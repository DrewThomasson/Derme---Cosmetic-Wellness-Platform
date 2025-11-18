import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image
import io
import re

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///derme.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Detect if running on HuggingFace Spaces
RUNNING_ON_HUGGINGFACE = os.environ.get('SPACE_ID') is not None

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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
        'potential_allergens': []
    }
    
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

# -------------------------------------------------------------------
# UC-9 & UC-14 helpers and mock data
# -------------------------------------------------------------------

def parse_date(date_str):
    """Helper to safely parse YYYY-MM-DD strings into datetime objects."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except Exception:
        return None

# Mock environmental data for pollen / air quality (UC-9).
# In a real system this would come from external APIs.
MOCK_ENVIRONMENT_DATA = [
    {"date": "2025-09-01", "pollen_index": 8.2, "aqi": 65},
    {"date": "2025-09-03", "pollen_index": 5.0, "aqi": 90},
    {"date": "2025-09-10", "pollen_index": 9.1, "aqi": 55},
    {"date": "2025-10-01", "pollen_index": 3.5, "aqi": 40},
]

# Mock dermatologist directory (UC-14).
# In a real system this would be populated from a Maps / provider API.
MOCK_DERMATOLOGISTS = [
    {
        "name": "Downtown Skin Care Clinic",
        "address": "123 Peachtree St, Atlanta, GA",
        "distance_km": 2.1,
        "rating": 4.7,
        "insurance": ["Aetna", "BlueCross", "Self-pay"],
        "phone": "+1-404-555-0101",
        "telederm": True
    },
    {
        "name": "Midtown Allergy & Derm",
        "address": "456 Midtown Ave, Atlanta, GA",
        "distance_km": 5.4,
        "rating": 4.3,
        "insurance": ["United", "Kaiser"],
        "phone": "+1-404-555-0112",
        "telederm": False
    },
    {
        "name": "Peachtree Dermatology Group",
        "address": "789 Ponce de Leon, Atlanta, GA",
        "distance_km": 8.0,
        "rating": 4.9,
        "insurance": ["Aetna", "United", "Self-pay"],
        "phone": "+1-404-555-0199",
        "telederm": True
    },
]

def severity_to_score(severity):
    """Map textual reaction severity to numeric score for charts."""
    if not severity:
        return 2
    s = severity.lower()
    if s == "mild":
        return 2
    if s == "moderate":
        return 3
    if s == "severe":
        return 5
    return 2  # default / unknown

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

# -------------------------------------------------------------------
# UC-9: View Seasonal Timeline & Heatmaps
# -------------------------------------------------------------------
@app.route('/analytics', methods=['GET'])
@login_required
def analytics():
    """
    UC-9: User views graphs comparing flare-ups vs. pollen/air quality;
    can filter by product/time. Environmental data is currently mocked.
    """
    # Filters from query string
    selected_product = request.args.get("product", "").strip() or None
    start_date_str = request.args.get("start_date", "").strip() or None
    end_date_str = request.args.get("end_date", "").strip() or None

    start_date = parse_date(start_date_str) if start_date_str else None
    end_date = parse_date(end_date_str) if end_date_str else None

    # Use allergic products as "flare-ups" (symptom history)
    allergic_products = AllergicProduct.query.filter_by(user_id=current_user.id).order_by(AllergicProduct.scan_date.asc()).all()

    # Join with environment data by date
    env_by_date = {e["date"]: e for e in MOCK_ENVIRONMENT_DATA}
    merged_records = []

    for p in allergic_products:
        if not p.scan_date:
            continue
        date_str = p.scan_date.date().strftime("%Y-%m-%d")
        date_obj = parse_date(date_str)
        if not date_obj:
            continue

        # Filter by date range
        if start_date and date_obj < start_date:
            continue
        if end_date and date_obj > end_date:
            continue

        # Filter by product name
        if selected_product and selected_product.lower() not in p.product_name.lower():
            continue

        env = env_by_date.get(date_str)
        if env:
            merged_records.append({
                "date": date_str,
                "product": p.product_name,
                "severity": severity_to_score(p.reaction_severity),
                "pollen_index": env["pollen_index"],
                "aqi": env["aqi"],
            })
        else:
            # Exception path: Missing environmental data
            merged_records.append({
                "date": date_str,
                "product": p.product_name,
                "severity": severity_to_score(p.reaction_severity),
                "pollen_index": None,
                "aqi": None,
            })

    # Build distinct product list for simple filter dropdown
    distinct_products = sorted({p.product_name for p in allergic_products})

    return render_template(
        'analytics.html',
        records=merged_records,
        products=distinct_products,
        selected_product=selected_product or "",
        start_date=start_date_str or "",
        end_date=end_date_str or "",
    )

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
                
                # Perform OCR
                text = pytesseract.image_to_string(image)
                
                # Parse ingredients
                ingredients = parse_ingredients(text)
                
                if not ingredients:
                    flash('No ingredients detected. Please try a clearer image.', 'warning')
                    return render_template('scan.html', ocr_text=text)
                
                # Analyze ingredients
                analysis = analyze_ingredients(ingredients, current_user.id)
                
                # Store in session for results page
                session['scan_results'] = {
                    'ocr_text': text,
                    'ingredients': ingredients,
                    'analysis': analysis
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

# -------------------------------------------------------------------
# UC-14: Find Dermatologist
# -------------------------------------------------------------------
@app.route('/find-dermatologist', methods=['GET'])
@login_required
def find_dermatologist():
    """
    UC-14: The user searches nearby dermatologists; filters by insurance,
    rating, distance; launches directions or calls. Tele-derm link if available.
    """
    location_query = request.args.get("location", "").strip()

    insurance_filter = request.args.get("insurance", "").strip()
    min_rating = request.args.get("min_rating", "").strip()
    max_distance = request.args.get("max_distance", "").strip()
    telederm_only = request.args.get("telederm_only", "") == "on"

    try:
        min_rating = float(min_rating) if min_rating else None
    except ValueError:
        min_rating = None

    try:
        max_distance = float(max_distance) if max_distance else None
    except ValueError:
        max_distance = None

    # Apply filters over mock directory
    results = []
    for d in MOCK_DERMATOLOGISTS:
        if insurance_filter and insurance_filter not in d["insurance"]:
            continue
        if min_rating is not None and d["rating"] < min_rating:
            continue
        if max_distance is not None and d["distance_km"] > max_distance:
            continue
        if telederm_only and not d["telederm"]:
            continue
        results.append(d)

    # Exception path: location permission / not provided
    location_warning = None
    if not location_query:
        location_warning = "Location is not set. Results are based on sample data near Atlanta."

    all_insurances = sorted({ins for d in MOCK_DERMATOLOGISTS for ins in d["insurance"]})

    return render_template(
        'find_dermatologist.html',
        location_query=location_query,
        location_warning=location_warning,
        providers=results,
        insurance_options=all_insurances,
        insurance_filter=insurance_filter,
        min_rating_value=min_rating if min_rating is not None else "",
        max_distance_value=max_distance if max_distance is not None else "",
        telederm_only=telederm_only,
    )

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
