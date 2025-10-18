import os
import csv
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, Response
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
    medications = db.relationship('Medication', backref='user', lazy=True, cascade='all, delete-orphan')
    epipens = db.relationship('EpiPen', backref='user', lazy=True, cascade='all, delete-orphan')
    symptoms = db.relationship('SymptomLog', backref='user', lazy=True, cascade='all, delete-orphan')
    emergency_contacts = db.relationship('EmergencyContact', backref='user', lazy=True, cascade='all, delete-orphan')

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

class Medication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    dosage = db.Column(db.String(100))
    frequency = db.Column(db.String(100))  # e.g., "Daily", "Twice daily", "As needed"
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)  # Optional, for courses of medication
    notes = db.Column(db.Text)
    active = db.Column(db.Boolean, default=True)

class EpiPen(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    brand = db.Column(db.String(100))
    dosage = db.Column(db.String(50))  # e.g., "0.3mg", "0.15mg"
    expiry_date = db.Column(db.Date, nullable=False)
    location = db.Column(db.String(200))  # Where it's stored
    lot_number = db.Column(db.String(100))

class SymptomLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    symptoms = db.Column(db.Text, nullable=False)  # Description of symptoms
    severity = db.Column(db.String(50), default='mild')  # mild, moderate, severe
    suspected_trigger = db.Column(db.String(200))  # Product or ingredient suspected
    notes = db.Column(db.Text)

class EmergencyContact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    relationship = db.Column(db.String(100))  # e.g., "Spouse", "Parent", "Doctor"
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120))
    is_primary = db.Column(db.Boolean, default=False)

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

# Health Management Routes
@app.route('/health')
@login_required
def health_dashboard():
    """Health management dashboard"""
    # Get active medications
    medications = Medication.query.filter_by(user_id=current_user.id, active=True).all()
    
    # Get EpiPens with expiry warnings
    epipens = EpiPen.query.filter_by(user_id=current_user.id).all()
    expiring_soon = []
    for epipen in epipens:
        days_until_expiry = (epipen.expiry_date - datetime.now().date()).days
        if days_until_expiry <= 90:  # Warning if expires within 90 days
            expiring_soon.append((epipen, days_until_expiry))
    
    # Get recent symptoms
    recent_symptoms = SymptomLog.query.filter_by(user_id=current_user.id).order_by(SymptomLog.date.desc()).limit(5).all()
    
    # Get emergency contacts
    contacts = EmergencyContact.query.filter_by(user_id=current_user.id).all()
    
    return render_template('health_dashboard.html',
                         medications=medications,
                         epipens=epipens,
                         expiring_soon=expiring_soon,
                         recent_symptoms=recent_symptoms,
                         contacts=contacts)

@app.route('/medications')
@login_required
def medications_page():
    """View and manage medications"""
    active_meds = Medication.query.filter_by(user_id=current_user.id, active=True).order_by(Medication.start_date.desc()).all()
    inactive_meds = Medication.query.filter_by(user_id=current_user.id, active=False).order_by(Medication.start_date.desc()).all()
    return render_template('medications.html', active_medications=active_meds, inactive_medications=inactive_meds)

@app.route('/medications/add', methods=['POST'])
@login_required
def add_medication():
    """Add a new medication"""
    name = request.form.get('name')
    dosage = request.form.get('dosage')
    frequency = request.form.get('frequency')
    start_date_str = request.form.get('start_date')
    end_date_str = request.form.get('end_date')
    notes = request.form.get('notes')
    
    if not name or not start_date_str:
        flash('Medication name and start date are required', 'error')
        return redirect(url_for('medications_page'))
    
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None
        
        medication = Medication(
            user_id=current_user.id,
            name=name,
            dosage=dosage,
            frequency=frequency,
            start_date=start_date,
            end_date=end_date,
            notes=notes,
            active=True
        )
        
        db.session.add(medication)
        db.session.commit()
        flash(f'Medication "{name}" added successfully', 'success')
    except ValueError:
        flash('Invalid date format', 'error')
    
    return redirect(url_for('medications_page'))

@app.route('/medications/toggle/<int:med_id>', methods=['POST'])
@login_required
def toggle_medication(med_id):
    """Mark medication as active or inactive"""
    medication = Medication.query.get_or_404(med_id)
    
    if medication.user_id != current_user.id:
        flash('Unauthorized', 'error')
        return redirect(url_for('medications_page'))
    
    medication.active = not medication.active
    db.session.commit()
    
    status = 'active' if medication.active else 'inactive'
    flash(f'Medication marked as {status}', 'success')
    return redirect(url_for('medications_page'))

@app.route('/medications/delete/<int:med_id>', methods=['POST'])
@login_required
def delete_medication(med_id):
    """Delete a medication"""
    medication = Medication.query.get_or_404(med_id)
    
    if medication.user_id != current_user.id:
        flash('Unauthorized', 'error')
        return redirect(url_for('medications_page'))
    
    db.session.delete(medication)
    db.session.commit()
    flash('Medication deleted', 'success')
    return redirect(url_for('medications_page'))

@app.route('/epipens')
@login_required
def epipens_page():
    """View and manage EpiPens"""
    epipens = EpiPen.query.filter_by(user_id=current_user.id).order_by(EpiPen.expiry_date).all()
    
    # Calculate days until expiry and warnings
    epipens_with_warnings = []
    for epipen in epipens:
        days_until_expiry = (epipen.expiry_date - datetime.now().date()).days
        warning_level = 'danger' if days_until_expiry <= 30 else ('warning' if days_until_expiry <= 90 else 'success')
        epipens_with_warnings.append({
            'epipen': epipen,
            'days_until_expiry': days_until_expiry,
            'warning_level': warning_level
        })
    
    return render_template('epipens.html', epipens_data=epipens_with_warnings)

@app.route('/epipens/add', methods=['POST'])
@login_required
def add_epipen():
    """Add a new EpiPen"""
    brand = request.form.get('brand')
    dosage = request.form.get('dosage')
    expiry_date_str = request.form.get('expiry_date')
    location = request.form.get('location')
    lot_number = request.form.get('lot_number')
    
    if not expiry_date_str:
        flash('Expiry date is required', 'error')
        return redirect(url_for('epipens_page'))
    
    try:
        expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
        
        epipen = EpiPen(
            user_id=current_user.id,
            brand=brand,
            dosage=dosage,
            expiry_date=expiry_date,
            location=location,
            lot_number=lot_number
        )
        
        db.session.add(epipen)
        db.session.commit()
        flash('EpiPen added successfully', 'success')
    except ValueError:
        flash('Invalid date format', 'error')
    
    return redirect(url_for('epipens_page'))

@app.route('/epipens/delete/<int:epipen_id>', methods=['POST'])
@login_required
def delete_epipen(epipen_id):
    """Delete an EpiPen"""
    epipen = EpiPen.query.get_or_404(epipen_id)
    
    if epipen.user_id != current_user.id:
        flash('Unauthorized', 'error')
        return redirect(url_for('epipens_page'))
    
    db.session.delete(epipen)
    db.session.commit()
    flash('EpiPen deleted', 'success')
    return redirect(url_for('epipens_page'))

@app.route('/symptoms')
@login_required
def symptoms_page():
    """View and manage symptom logs"""
    symptoms = SymptomLog.query.filter_by(user_id=current_user.id).order_by(SymptomLog.date.desc()).all()
    return render_template('symptoms.html', symptoms=symptoms)

@app.route('/symptoms/add', methods=['POST'])
@login_required
def add_symptom():
    """Add a new symptom log"""
    date_str = request.form.get('date')
    symptoms_text = request.form.get('symptoms')
    severity = request.form.get('severity', 'mild')
    suspected_trigger = request.form.get('suspected_trigger')
    notes = request.form.get('notes')
    
    if not symptoms_text:
        flash('Symptom description is required', 'error')
        return redirect(url_for('symptoms_page'))
    
    try:
        log_date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M') if date_str else datetime.now()
        
        symptom = SymptomLog(
            user_id=current_user.id,
            date=log_date,
            symptoms=symptoms_text,
            severity=severity,
            suspected_trigger=suspected_trigger,
            notes=notes
        )
        
        db.session.add(symptom)
        db.session.commit()
        flash('Symptom logged successfully', 'success')
    except ValueError:
        flash('Invalid date format', 'error')
    
    return redirect(url_for('symptoms_page'))

@app.route('/symptoms/delete/<int:symptom_id>', methods=['POST'])
@login_required
def delete_symptom(symptom_id):
    """Delete a symptom log"""
    symptom = SymptomLog.query.get_or_404(symptom_id)
    
    if symptom.user_id != current_user.id:
        flash('Unauthorized', 'error')
        return redirect(url_for('symptoms_page'))
    
    db.session.delete(symptom)
    db.session.commit()
    flash('Symptom log deleted', 'success')
    return redirect(url_for('symptoms_page'))

@app.route('/emergency-card')
@login_required
def emergency_card():
    """View emergency information card"""
    allergens = UserAllergen.query.filter_by(user_id=current_user.id).all()
    medications = Medication.query.filter_by(user_id=current_user.id, active=True).all()
    contacts = EmergencyContact.query.filter_by(user_id=current_user.id).order_by(EmergencyContact.is_primary.desc()).all()
    epipens = EpiPen.query.filter_by(user_id=current_user.id).all()
    
    return render_template('emergency_card.html',
                         allergens=allergens,
                         medications=medications,
                         contacts=contacts,
                         epipens=epipens)

@app.route('/emergency-contacts')
@login_required
def emergency_contacts_page():
    """Manage emergency contacts"""
    contacts = EmergencyContact.query.filter_by(user_id=current_user.id).order_by(EmergencyContact.is_primary.desc()).all()
    return render_template('emergency_contacts.html', contacts=contacts)

@app.route('/emergency-contacts/add', methods=['POST'])
@login_required
def add_emergency_contact():
    """Add a new emergency contact"""
    name = request.form.get('name')
    relationship = request.form.get('relationship')
    phone = request.form.get('phone')
    email = request.form.get('email')
    is_primary = request.form.get('is_primary') == 'on'
    
    if not name or not phone:
        flash('Name and phone are required', 'error')
        return redirect(url_for('emergency_contacts_page'))
    
    contact = EmergencyContact(
        user_id=current_user.id,
        name=name,
        relationship=relationship,
        phone=phone,
        email=email,
        is_primary=is_primary
    )
    
    db.session.add(contact)
    db.session.commit()
    flash('Emergency contact added', 'success')
    return redirect(url_for('emergency_contacts_page'))

@app.route('/emergency-contacts/delete/<int:contact_id>', methods=['POST'])
@login_required
def delete_emergency_contact(contact_id):
    """Delete an emergency contact"""
    contact = EmergencyContact.query.get_or_404(contact_id)
    
    if contact.user_id != current_user.id:
        flash('Unauthorized', 'error')
        return redirect(url_for('emergency_contacts_page'))
    
    db.session.delete(contact)
    db.session.commit()
    flash('Emergency contact deleted', 'success')
    return redirect(url_for('emergency_contacts_page'))

@app.route('/export-data')
@login_required
def export_data():
    """Export all user data as CSV"""
    output = io.StringIO()
    
    # Export allergens
    output.write("=== YOUR ALLERGENS ===\n")
    output.write("Ingredient,Severity\n")
    allergens = UserAllergen.query.filter_by(user_id=current_user.id).all()
    for allergen in allergens:
        output.write(f'"{allergen.ingredient_name}","{allergen.severity}"\n')
    
    output.write("\n=== SAFE PRODUCTS ===\n")
    output.write("Product Name,Ingredients,Scan Date\n")
    safe_products = SafeProduct.query.filter_by(user_id=current_user.id).all()
    for product in safe_products:
        output.write(f'"{product.product_name}","{product.ingredients}","{product.scan_date}"\n')
    
    output.write("\n=== ALLERGIC PRODUCTS ===\n")
    output.write("Product Name,Ingredients,Severity,Scan Date\n")
    allergic_products = AllergicProduct.query.filter_by(user_id=current_user.id).all()
    for product in allergic_products:
        output.write(f'"{product.product_name}","{product.ingredients}","{product.reaction_severity}","{product.scan_date}"\n')
    
    output.write("\n=== MEDICATIONS ===\n")
    output.write("Name,Dosage,Frequency,Start Date,End Date,Notes,Active\n")
    medications = Medication.query.filter_by(user_id=current_user.id).all()
    for med in medications:
        output.write(f'"{med.name}","{med.dosage}","{med.frequency}","{med.start_date}","{med.end_date or ''}","{med.notes or ''}","{med.active}"\n')
    
    output.write("\n=== SYMPTOM LOGS ===\n")
    output.write("Date,Symptoms,Severity,Suspected Trigger,Notes\n")
    symptoms = SymptomLog.query.filter_by(user_id=current_user.id).order_by(SymptomLog.date.desc()).all()
    for symptom in symptoms:
        output.write(f'"{symptom.date}","{symptom.symptoms}","{symptom.severity}","{symptom.suspected_trigger or ''}","{symptom.notes or ''}"\n')
    
    output.write("\n=== EMERGENCY CONTACTS ===\n")
    output.write("Name,Relationship,Phone,Email,Primary\n")
    contacts = EmergencyContact.query.filter_by(user_id=current_user.id).all()
    for contact in contacts:
        output.write(f'"{contact.name}","{contact.relationship or ''}","{contact.phone}","{contact.email or ''}","{contact.is_primary}"\n')
    
    # Create response
    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers['Content-Disposition'] = f'attachment; filename=derme_data_{current_user.username}_{datetime.now().strftime("%Y%m%d")}.csv'
    
    return response

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
