import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image
import io
import re
from config import Config
from gemini_helper import GeminiHelper

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Detect if running on HuggingFace Spaces
RUNNING_ON_HUGGINGFACE = Config.RUNNING_ON_HUGGINGFACE

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize Gemini Helper
gemini_helper = GeminiHelper(
    api_key=Config.GEMINI_API_KEY,
    model_name=Config.GEMINI_MODEL
)

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    allergens = db.relationship('UserAllergen', backref='user', lazy=True, cascade='all, delete-orphan')
    safe_products = db.relationship('SafeProduct', backref='user', lazy=True, cascade='all, delete-orphan')
    allergic_products = db.relationship('AllergicProduct', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class UserAllergen(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ingredient_name = db.Column(db.String(200), nullable=False)
    severity = db.Column(db.String(50), default='unknown')  # mild, moderate, severe, unknown

class SafeProduct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_name = db.Column(db.String(200), nullable=False)
    ingredients = db.Column(db.Text, nullable=False)
    scan_date = db.Column(db.DateTime, default=db.func.current_timestamp())

class AllergicProduct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_name = db.Column(db.String(200), nullable=False)
    ingredients = db.Column(db.Text, nullable=False)
    scan_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    reaction_severity = db.Column(db.String(50), default='unknown')  # mild, moderate, severe, unknown

class IngredientSynonym(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    primary_name = db.Column(db.String(200), nullable=False)
    synonym = db.Column(db.String(200), nullable=False)

class KnownAllergen(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    category = db.Column(db.String(100))
    description = db.Column(db.Text)

# Login manager user loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Helper functions
def normalize_ingredient(ingredient):
    """Normalize ingredient name for comparison"""
    return ingredient.lower().strip()

def find_ingredient_synonyms(ingredient):
    """Find all synonyms for an ingredient"""
    normalized = normalize_ingredient(ingredient)
    
    # Try to get synonyms from Gemini first if available
    if Config.USE_GEMINI_FOR_ALLERGEN_INFO and gemini_helper.is_available():
        try:
            gemini_synonyms = gemini_helper.find_ingredient_synonyms(ingredient)
            # Normalize all synonyms
            all_names = set([normalize_ingredient(syn) for syn in gemini_synonyms])
            return list(all_names)
        except Exception as e:
            print(f"Error getting Gemini synonyms, falling back to database: {e}")
    
    # Fallback to database synonyms
    synonyms = IngredientSynonym.query.filter(
        (db.func.lower(IngredientSynonym.primary_name) == normalized) |
        (db.func.lower(IngredientSynonym.synonym) == normalized)
    ).all()
    
    all_names = set([normalized])
    for syn in synonyms:
        all_names.add(normalize_ingredient(syn.primary_name))
        all_names.add(normalize_ingredient(syn.synonym))
    
    return list(all_names)

def parse_ingredients(text):
    """Parse ingredient text into individual ingredients"""
    # Common patterns for ingredient lists
    text = text.replace('\n', ' ').replace('\r', ' ')
    
    # Split by common separators
    ingredients = re.split(r'[,;]', text)
    
    # Clean up each ingredient
    cleaned = []
    for ing in ingredients:
        ing = ing.strip()
        # Remove common prefixes like numbers, bullets
        ing = re.sub(r'^[\d\.\-\*\•]+\s*', '', ing)
        if ing and len(ing) > 2:
            cleaned.append(ing)
    
    return cleaned

def detect_potential_allergens(user_id):
    """Cross-reference allergic and safe products to find potential allergens"""
    # Get all allergic and safe products for the user
    allergic_products = AllergicProduct.query.filter_by(user_id=user_id).all()
    safe_products = SafeProduct.query.filter_by(user_id=user_id).all()
    
    if not allergic_products or not safe_products:
        return []
    
    # Parse ingredients from all products
    allergic_ingredients = set()
    safe_ingredients = set()
    
    for product in allergic_products:
        ingredients = parse_ingredients(product.ingredients)
        for ing in ingredients:
            normalized = normalize_ingredient(ing)
            # Include synonyms
            synonyms = find_ingredient_synonyms(ing)
            allergic_ingredients.update(synonyms)
    
    for product in safe_products:
        ingredients = parse_ingredients(product.ingredients)
        for ing in ingredients:
            normalized = normalize_ingredient(ing)
            # Include synonyms
            synonyms = find_ingredient_synonyms(ing)
            safe_ingredients.update(synonyms)
    
    # Find ingredients that are ONLY in allergic products, not in safe products
    potential_allergens = allergic_ingredients - safe_ingredients
    
    # Get actual ingredient names (not just normalized)
    result = []
    for product in allergic_products:
        ingredients = parse_ingredients(product.ingredients)
        for ing in ingredients:
            synonyms = find_ingredient_synonyms(ing)
            if any(syn in potential_allergens for syn in synonyms):
                if ing not in [r['name'] for r in result]:
                    result.append({
                        'name': ing,
                        'count': sum(1 for p in allergic_products if ing.lower() in p.ingredients.lower())
                    })
    
    # Sort by frequency
    result.sort(key=lambda x: x['count'], reverse=True)
    return result

def analyze_ingredients(ingredients_list, user_id):
    """Analyze ingredients against user allergens and known allergen database"""
    user_allergens = UserAllergen.query.filter_by(user_id=user_id).all()
    user_allergen_names = set()
    
    # Collect all user allergen names and their synonyms
    for allergen in user_allergens:
        synonyms = find_ingredient_synonyms(allergen.ingredient_name)
        user_allergen_names.update(synonyms)
    
    results = {
        'allergens_found': [],
        'safe_ingredients': [],
        'unknown_ingredients': [],
        'warnings': [],
        'potential_allergens': [],
        'gemini_insights': []  # New field for Gemini-powered insights
    }
    
    # Try to use Gemini for comprehensive analysis if available
    if Config.USE_GEMINI_FOR_ALLERGEN_INFO and gemini_helper.is_available():
        try:
            user_allergen_list = [a.ingredient_name for a in user_allergens]
            gemini_analysis = gemini_helper.analyze_ingredient_list(ingredients_list, user_allergen_list)
            
            # Process Gemini analysis results
            if gemini_analysis:
                # Add user allergens found by Gemini
                for allergen_match in gemini_analysis.get('user_allergens_found', []):
                    # Find severity from user's allergen list
                    severity = 'unknown'
                    for ua in user_allergens:
                        if normalize_ingredient(ua.ingredient_name) == normalize_ingredient(allergen_match.get('matches_allergen', '')):
                            severity = ua.severity
                            break
                    
                    results['allergens_found'].append({
                        'name': allergen_match.get('ingredient', ''),
                        'severity': severity,
                        'gemini_explanation': allergen_match.get('explanation', '')
                    })
                
                # Add common allergens identified by Gemini
                for common_allergen in gemini_analysis.get('common_allergens', []):
                    results['warnings'].append({
                        'name': common_allergen.get('ingredient', ''),
                        'category': common_allergen.get('category', 'Unknown'),
                        'description': common_allergen.get('description', '')
                    })
                
                # Store Gemini insights
                results['gemini_insights'] = gemini_analysis
                
                # Mark remaining as safe
                identified_ingredients = set()
                for a in results['allergens_found']:
                    identified_ingredients.add(normalize_ingredient(a['name']))
                for w in results['warnings']:
                    identified_ingredients.add(normalize_ingredient(w['name']))
                
                for ing in ingredients_list:
                    if normalize_ingredient(ing) not in identified_ingredients:
                        results['safe_ingredients'].append(ing)
                
                # Get potential allergens from cross-referencing
                potential_allergens = detect_potential_allergens(user_id)
                for potential in potential_allergens[:5]:  # Limit to top 5
                    results['potential_allergens'].append({
                        'name': potential['name'],
                        'reason': f'Found in {potential["count"]} allergic products but not in safe products'
                    })
                
                return results
        except Exception as e:
            print(f"Error using Gemini for analysis, falling back to traditional method: {e}")
    
    # Fallback to traditional analysis
    # Get potential allergens from cross-referencing
    potential_allergens = detect_potential_allergens(user_id)
    potential_allergen_names = set([p['name'].lower() for p in potential_allergens])
    
    for ingredient in ingredients_list:
        normalized = normalize_ingredient(ingredient)
        synonyms = find_ingredient_synonyms(ingredient)
        
        # Check against user allergens
        found_allergen = False
        for syn in synonyms:
            if syn in user_allergen_names:
                # Find severity
                severity = 'unknown'
                for ua in user_allergens:
                    if normalize_ingredient(ua.ingredient_name) in synonyms:
                        severity = ua.severity
                        break
                
                results['allergens_found'].append({
                    'name': ingredient,
                    'severity': severity
                })
                found_allergen = True
                break
        
        if not found_allergen:
            # Check against potential allergens from cross-referencing
            if normalized in potential_allergen_names:
                results['potential_allergens'].append({
                    'name': ingredient,
                    'reason': 'Found in allergic products but not in safe products'
                })
                continue
            
            # Check against known allergen database
            known = KnownAllergen.query.filter(
                db.func.lower(KnownAllergen.name).in_(synonyms)
            ).first()
            
            if known:
                results['warnings'].append({
                    'name': ingredient,
                    'category': known.category,
                    'description': known.description
                })
            else:
                results['safe_ingredients'].append(ingredient)
    
    return results

# Routes
@app.context_processor
def inject_globals():
    """Make global variables available to all templates"""
    return {
        'running_on_huggingface': RUNNING_ON_HUGGINGFACE
    }

@app.before_request
def auto_login_on_huggingface():
    """Automatically log in demo user when running on HuggingFace Spaces"""
    if RUNNING_ON_HUGGINGFACE and not current_user.is_authenticated:
        # Skip auto-login for static files
        if request.endpoint and 'static' not in request.endpoint:
            # Get or create demo user
            demo_user = User.query.filter_by(username='demo_user').first()
            
            if not demo_user:
                # Create demo user if doesn't exist
                demo_user = User(username='demo_user', email='demo@derme-app.com')
                demo_user.set_password('demo123')
                db.session.add(demo_user)
                db.session.commit()
                
                # Add some sample allergens for demo
                sample_allergens = [
                    ('Fragrance', 'severe'),
                    ('Parabens', 'moderate'),
                    ('SLS', 'mild')
                ]
                
                for allergen_name, severity in sample_allergens:
                    allergen = UserAllergen(
                        user_id=demo_user.id,
                        ingredient_name=allergen_name,
                        severity=severity
                    )
                    db.session.add(allergen)
                
                db.session.commit()
            
            # Log in the demo user
            login_user(demo_user, remember=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/demo-login')
def demo_login():
    """Demo/test mode - automatically log in as demo user"""
    # Try to find existing demo user
    demo_user = User.query.filter_by(username='demo_user').first()
    
    if not demo_user:
        # Create demo user if doesn't exist
        demo_user = User(username='demo_user', email='demo@derme-app.com')
        demo_user.set_password('demo123')
        db.session.add(demo_user)
        db.session.commit()
        
        # Add some sample allergens for demo
        sample_allergens = [
            ('Fragrance', 'severe'),
            ('Parabens', 'moderate'),
            ('SLS', 'mild')
        ]
        
        for allergen_name, severity in sample_allergens:
            allergen = UserAllergen(
                user_id=demo_user.id,
                ingredient_name=allergen_name,
                severity=severity
            )
            db.session.add(allergen)
        
        db.session.commit()
    
    # Log in the demo user
    login_user(demo_user, remember=True)
    flash('Logged in as demo user for testing', 'info')
    return redirect(url_for('dashboard'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not username or not email or not password:
            flash('All fields are required', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('register.html')
        
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    allergens = UserAllergen.query.filter_by(user_id=current_user.id).all()
    safe_products = SafeProduct.query.filter_by(user_id=current_user.id).order_by(SafeProduct.scan_date.desc()).limit(5).all()
    allergic_products = AllergicProduct.query.filter_by(user_id=current_user.id).order_by(AllergicProduct.scan_date.desc()).limit(5).all()
    potential_allergens = detect_potential_allergens(current_user.id)[:5]  # Top 5
    
    return render_template('dashboard.html', 
                         allergens=allergens, 
                         safe_products=safe_products,
                         allergic_products=allergic_products,
                         potential_allergens=potential_allergens)

@app.route('/allergens', methods=['GET', 'POST'])
@login_required
def manage_allergens():
    if request.method == 'POST':
        ingredient_name = request.form.get('ingredient_name')
        severity = request.form.get('severity', 'unknown')
        
        if ingredient_name:
            allergen = UserAllergen(
                user_id=current_user.id,
                ingredient_name=ingredient_name,
                severity=severity
            )
            db.session.add(allergen)
            db.session.commit()
            flash('Allergen added successfully', 'success')
        
        return redirect(url_for('manage_allergens'))
    
    allergens = UserAllergen.query.filter_by(user_id=current_user.id).all()
    return render_template('allergens.html', allergens=allergens)

@app.route('/allergens/delete/<int:allergen_id>', methods=['POST'])
@login_required
def delete_allergen(allergen_id):
    allergen = UserAllergen.query.get_or_404(allergen_id)
    
    if allergen.user_id != current_user.id:
        flash('Unauthorized', 'error')
        return redirect(url_for('manage_allergens'))
    
    db.session.delete(allergen)
    db.session.commit()
    flash('Allergen removed', 'success')
    return redirect(url_for('manage_allergens'))

@app.route('/scan', methods=['GET', 'POST'])
@login_required
def scan():
    if request.method == 'POST':
        if 'image' not in request.files:
            flash('No image uploaded', 'error')
            return redirect(url_for('scan'))
        
        file = request.files['image']
        
        if file.filename == '':
            flash('No image selected', 'error')
            return redirect(url_for('scan'))
        
        if file:
            try:
                # Read image
                image = Image.open(file.stream)
                
                # Try Gemini first if enabled and available
                text = ""
                ingredients = []
                ocr_method = "tesseract"  # Default
                
                if Config.USE_GEMINI_FOR_OCR and gemini_helper.is_available():
                    try:
                        text, ingredients = gemini_helper.extract_ingredients_from_image(image)
                        if ingredients:
                            ocr_method = "gemini"
                        elif Config.FALLBACK_TO_TESSERACT:
                            # Fallback to Tesseract if Gemini didn't find ingredients
                            text = pytesseract.image_to_string(image)
                            ingredients = parse_ingredients(text)
                            ocr_method = "tesseract (fallback)"
                    except Exception as e:
                        print(f"Gemini OCR error: {e}")
                        if Config.FALLBACK_TO_TESSERACT:
                            # Fallback to Tesseract on error
                            text = pytesseract.image_to_string(image)
                            ingredients = parse_ingredients(text)
                            ocr_method = "tesseract (fallback)"
                else:
                    # Use Tesseract OCR
                    text = pytesseract.image_to_string(image)
                    ingredients = parse_ingredients(text)
                
                if not ingredients:
                    flash('No ingredients detected. Please try a clearer image.', 'warning')
                    return render_template('scan.html', ocr_text=text, ocr_method=ocr_method)
                
                # Analyze ingredients
                analysis = analyze_ingredients(ingredients, current_user.id)
                
                # Store in session for results page
                session['scan_results'] = {
                    'ocr_text': text,
                    'ingredients': ingredients,
                    'analysis': analysis,
                    'ocr_method': ocr_method
                }
                
                return redirect(url_for('scan_results'))
                
            except Exception as e:
                flash(f'Error processing image: {str(e)}', 'error')
                return redirect(url_for('scan'))
    
    return render_template('scan.html')

@app.route('/scan/results')
@login_required
def scan_results():
    results = session.get('scan_results')
    
    if not results:
        flash('No scan results available', 'warning')
        return redirect(url_for('scan'))
    
    return render_template('results.html', results=results)

@app.route('/api/allergen-info/<ingredient_name>')
@login_required
def get_allergen_info(ingredient_name):
    """API endpoint to get detailed allergen information using Gemini"""
    if Config.USE_GEMINI_FOR_ALLERGEN_INFO and gemini_helper.is_available():
        try:
            info = gemini_helper.get_allergen_information(ingredient_name)
            return jsonify({
                'success': True,
                'info': info,
                'source': 'gemini'
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e),
                'source': 'gemini'
            }), 500
    else:
        # Fallback to database lookup
        known = KnownAllergen.query.filter(
            db.func.lower(KnownAllergen.name) == ingredient_name.lower()
        ).first()
        
        if known:
            return jsonify({
                'success': True,
                'info': {
                    'ingredient': known.name,
                    'category': known.category,
                    'description': known.description
                },
                'source': 'database'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No information available',
                'source': 'database'
            }), 404

@app.route('/scan/save', methods=['POST'])
@login_required
def save_product():
    results = session.get('scan_results')
    
    if not results:
        return jsonify({'error': 'No scan results to save'}), 400
    
    product_name = request.form.get('product_name', 'Unknown Product')
    product_type = request.form.get('product_type', 'safe')  # 'safe' or 'allergic'
    
    if product_type == 'allergic':
        severity = request.form.get('reaction_severity', 'unknown')
        product = AllergicProduct(
            user_id=current_user.id,
            product_name=product_name,
            ingredients=', '.join(results['ingredients']),
            reaction_severity=severity
        )
        flash('Allergic product saved successfully', 'success')
    else:
        product = SafeProduct(
            user_id=current_user.id,
            product_name=product_name,
            ingredients=', '.join(results['ingredients'])
        )
        flash('Safe product saved successfully', 'success')
    
    db.session.add(product)
    db.session.commit()
    
    return redirect(url_for('dashboard'))

@app.route('/products/allergic')
@login_required
def allergic_products():
    products = AllergicProduct.query.filter_by(user_id=current_user.id).order_by(AllergicProduct.scan_date.desc()).all()
    return render_template('allergic_products.html', products=products)

@app.route('/products/allergic/delete/<int:product_id>', methods=['POST'])
@login_required
def delete_allergic_product(product_id):
    product = AllergicProduct.query.get_or_404(product_id)
    
    if product.user_id != current_user.id:
        flash('Unauthorized', 'error')
        return redirect(url_for('allergic_products'))
    
    db.session.delete(product)
    db.session.commit()
    flash('Allergic product removed', 'success')
    return redirect(url_for('allergic_products'))

@app.route('/potential-allergens')
@login_required
def potential_allergens_page():
    potential = detect_potential_allergens(current_user.id)
    return render_template('potential_allergens.html', potential_allergens=potential)

@app.route('/potential-allergens/ingredient/<ingredient_name>')
@login_required
def view_ingredient_products(ingredient_name):
    """View all allergic products that contain a specific ingredient"""
    allergic_products = AllergicProduct.query.filter_by(user_id=current_user.id).all()
    
    # Filter products that contain this ingredient
    products_with_ingredient = []
    for product in allergic_products:
        if ingredient_name.lower() in product.ingredients.lower():
            products_with_ingredient.append(product)
    
    return render_template('ingredient_products.html', 
                         ingredient_name=ingredient_name,
                         products=products_with_ingredient)

@app.route('/potential-allergens/edit/<ingredient_name>', methods=['POST'])
@login_required
def edit_potential_allergen(ingredient_name):
    """Edit/correct an ingredient name in all allergic products"""
    new_name = request.form.get('new_name')
    
    if not new_name:
        flash('New ingredient name is required', 'error')
        return redirect(url_for('potential_allergens_page'))
    
    # Find and update all allergic products containing this ingredient
    allergic_products = AllergicProduct.query.filter_by(user_id=current_user.id).all()
    updated_count = 0
    
    for product in allergic_products:
        ingredients = parse_ingredients(product.ingredients)
        updated_ingredients = []
        
        for ing in ingredients:
            if ing.lower() == ingredient_name.lower():
                updated_ingredients.append(new_name)
                updated_count += 1
            else:
                updated_ingredients.append(ing)
        
        if updated_count > 0:
            product.ingredients = ', '.join(updated_ingredients)
    
    if updated_count > 0:
        db.session.commit()
        flash(f'Updated "{ingredient_name}" to "{new_name}" in {updated_count} instance(s)', 'success')
    else:
        flash('No instances found to update', 'warning')
    
    return redirect(url_for('potential_allergens_page'))

@app.route('/potential-allergens/remove/<ingredient_name>', methods=['POST'])
@login_required
def remove_potential_allergen(ingredient_name):
    """Remove an ingredient from all allergic products"""
    allergic_products = AllergicProduct.query.filter_by(user_id=current_user.id).all()
    removed_count = 0
    
    for product in allergic_products:
        ingredients = parse_ingredients(product.ingredients)
        filtered_ingredients = [ing for ing in ingredients if ing.lower() != ingredient_name.lower()]
        
        if len(filtered_ingredients) < len(ingredients):
            product.ingredients = ', '.join(filtered_ingredients)
            removed_count += 1
    
    if removed_count > 0:
        db.session.commit()
        flash(f'Removed "{ingredient_name}" from {removed_count} product(s)', 'success')
    else:
        flash('No instances found to remove', 'warning')
    
    return redirect(url_for('potential_allergens_page'))


# Initialize database
def init_db():
    with app.app_context():
        db.create_all()
        
        # Add some common ingredient synonyms
        if IngredientSynonym.query.count() == 0:
            synonyms = [
                ('Tocopherol', 'Vitamin E'),
                ('Retinol', 'Vitamin A'),
                ('Ascorbic Acid', 'Vitamin C'),
                ('Sodium Lauryl Sulfate', 'SLS'),
                ('Sodium Laureth Sulfate', 'SLES'),
                ('Fragrance', 'Parfum'),
                ('Methylparaben', 'Paraben'),
                ('Propylparaben', 'Paraben'),
            ]
            
            for primary, synonym in synonyms:
                syn = IngredientSynonym(primary_name=primary, synonym=synonym)
                db.session.add(syn)
            
            db.session.commit()
        
        # Add common known allergens
        if KnownAllergen.query.count() == 0:
            allergens = [
                ('Fragrance', 'Sensitizer', 'Can cause allergic reactions and skin irritation'),
                ('Parfum', 'Sensitizer', 'Can cause allergic reactions and skin irritation'),
                ('Formaldehyde', 'Preservative', 'Known allergen and irritant'),
                ('Methylisothiazolinone', 'Preservative', 'Common cause of allergic contact dermatitis'),
                ('Methylchloroisothiazolinone', 'Preservative', 'Common cause of allergic contact dermatitis'),
                ('Paraphenylenediamine', 'Dye', 'Strong allergen found in hair dyes'),
                ('Lanolin', 'Moisturizer', 'Can cause allergic reactions in sensitive individuals'),
                ('Propylene Glycol', 'Solvent', 'May cause irritation in some individuals'),
            ]
            
            for name, category, description in allergens:
                allergen = KnownAllergen(name=name, category=category, description=description)
                db.session.add(allergen)
            
            db.session.commit()

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=7860, debug=True)
