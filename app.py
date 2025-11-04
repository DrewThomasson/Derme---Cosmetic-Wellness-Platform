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
from datetime import datetime

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
    # Security questions for password recovery
    security_question_1 = db.Column(db.String(200))
    security_answer_1_hash = db.Column(db.String(200))
    security_question_2 = db.Column(db.String(200))
    security_answer_2_hash = db.Column(db.String(200))
    security_question_3 = db.Column(db.String(200))
    security_answer_3_hash = db.Column(db.String(200))
    allergens = db.relationship('UserAllergen', backref='user', lazy=True, cascade='all, delete-orphan')
    safe_products = db.relationship('SafeProduct', backref='user', lazy=True, cascade='all, delete-orphan')
    allergic_products = db.relationship('AllergicProduct', backref='user', lazy=True, cascade='all, delete-orphan')
    epipens = db.relationship('EpiPen', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def set_security_answer(self, question_num, answer):
        """Set a security answer (hashed)"""
        answer_hash = generate_password_hash(answer.lower().strip())
        setattr(self, f'security_answer_{question_num}_hash', answer_hash)
    
    def check_security_answer(self, question_num, answer):
        """Check if security answer matches"""
        answer_hash = getattr(self, f'security_answer_{question_num}_hash')
        if not answer_hash:
            return False
        return check_password_hash(answer_hash, answer.lower().strip())

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
    where_found = db.Column(db.Text)
    product_categories = db.Column(db.Text)  # JSON array stored as text
    clinician_note = db.Column(db.Text)
    url = db.Column(db.String(500))
    # Legacy fields for backward compatibility
    category = db.Column(db.String(100))
    description = db.Column(db.Text)

class EpiPen(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)  # e.g., "EpiPen Jr", "EpiPen", "Auvi-Q"
    location = db.Column(db.String(200))  # Where it's stored (e.g., "Bedroom drawer", "Purse")
    expiration_date = db.Column(db.Date, nullable=False)
    lot_number = db.Column(db.String(100))
    notes = db.Column(db.Text)
    added_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    def days_until_expiration(self):
        """Calculate days until expiration"""
        from datetime import date
        delta = self.expiration_date - date.today()
        return delta.days
    
    def is_expired(self):
        """Check if EpiPen is expired"""
        return self.days_until_expiration() < 0
    
    def needs_reminder(self, days_threshold=30):
        """Check if EpiPen needs expiration reminder"""
        days = self.days_until_expiration()
        return 0 <= days <= days_threshold

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
                # Parse product categories from JSON string
                import json
                product_categories = []
                try:
                    product_categories = json.loads(known.product_categories) if known.product_categories else []
                except:
                    product_categories = []
                
                results['warnings'].append({
                    'name': ingredient,
                    'allergen_name': known.name,
                    'category': known.category,
                    'description': known.description or known.where_found,
                    'where_found': known.where_found,
                    'product_categories': product_categories,
                    'clinician_note': known.clinician_note,
                    'url': known.url
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
        
        # Get security questions and answers
        security_question_1 = request.form.get('security_question_1')
        security_answer_1 = request.form.get('security_answer_1')
        security_question_2 = request.form.get('security_question_2')
        security_answer_2 = request.form.get('security_answer_2')
        security_question_3 = request.form.get('security_question_3')
        security_answer_3 = request.form.get('security_answer_3')
        
        if not username or not email or not password:
            flash('All fields are required', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')
        
        # Validate security questions
        if not security_question_1 or not security_answer_1:
            flash('Please set up at least one security question', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('register.html')
        
        # Print before state
        print("\n" + "="*60)
        print("USER REGISTRATION - BEFORE STATE")
        print("="*60)
        user_count_before = User.query.count()
        print(f"Total users in database: {user_count_before}")
        if user_count_before > 0:
            print(f"Existing users registered: {user_count_before} user(s)")
        else:
            print("No existing users in database")
        print("="*60)
        
        # Create and add new user
        user = User(username=username, email=email)
        user.set_password(password)
        
        # Set security questions and answers
        if security_question_1 and security_answer_1:
            user.security_question_1 = security_question_1
            user.set_security_answer(1, security_answer_1)
        if security_question_2 and security_answer_2:
            user.security_question_2 = security_question_2
            user.set_security_answer(2, security_answer_2)
        if security_question_3 and security_answer_3:
            user.security_question_3 = security_question_3
            user.set_security_answer(3, security_answer_3)
        
        db.session.add(user)
        db.session.commit()
        
        # Print after state and confirmation
        print("\n" + "="*60)
        print("USER REGISTRATION - SUCCESSFUL")
        print("="*60)
        print(f"New user registered:")
        print(f"  - ID: {user.id}")
        print(f"  - Username: {user.username}")
        print(f"  - Registration time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        user_count_after = User.query.count()
        print(f"\nTotal users in database: {user_count_after}")
        print("✓ User successfully added to database")
        print("="*60 + "\n")
        
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
            # Print login success
            print("\n" + "="*60)
            print("USER LOGIN - SUCCESSFUL")
            print("="*60)
            print(f"User logged in:")
            print(f"  - ID: {user.id}")
            print(f"  - Username: {user.username}")
            print(f"  - Login time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Get user's allergen count
            allergen_count = UserAllergen.query.filter_by(user_id=user.id).count()
            safe_product_count = SafeProduct.query.filter_by(user_id=user.id).count()
            allergic_product_count = AllergicProduct.query.filter_by(user_id=user.id).count()
            
            print(f"\nUser profile summary:")
            print(f"  - Tracked allergens: {allergen_count}")
            print(f"  - Safe products: {safe_product_count}")
            print(f"  - Allergic products: {allergic_product_count}")
            print("="*60 + "\n")
            
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('dashboard'))
        else:
            # Print login failure
            print("\n" + "="*60)
            print("USER LOGIN - FAILED")
            print("="*60)
            print(f"Failed login attempt at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            if username:
                print(f"Attempted username: {username[:3]}***")
            print("="*60 + "\n")
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """First step: Enter username or email"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        identifier = request.form.get('identifier')  # username or email
        
        if not identifier:
            flash('Please enter your username or email', 'error')
            return render_template('forgot_password.html')
        
        # Find user by username or email
        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier)
        ).first()
        
        if not user:
            flash('No account found with that username or email', 'error')
            return render_template('forgot_password.html')
        
        # Check if user has security questions set up
        if not user.security_question_1:
            flash('This account does not have security questions set up. Please contact support.', 'error')
            return render_template('forgot_password.html')
        
        # Store user ID in session for security questions page
        session['reset_user_id'] = user.id
        return redirect(url_for('verify_security_questions'))
    
    return render_template('forgot_password.html')

@app.route('/verify-security-questions', methods=['GET', 'POST'])
def verify_security_questions():
    """Second step: Answer security questions"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    user_id = session.get('reset_user_id')
    if not user_id:
        flash('Session expired. Please start over.', 'error')
        return redirect(url_for('forgot_password'))
    
    user = User.query.get(user_id)
    if not user:
        flash('User not found', 'error')
        session.pop('reset_user_id', None)
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        # Get submitted answers
        answer_1 = request.form.get('answer_1', '')
        answer_2 = request.form.get('answer_2', '')
        answer_3 = request.form.get('answer_3', '')
        
        # Verify at least the first answer (required)
        if not user.check_security_answer(1, answer_1):
            flash('Incorrect answer to security question', 'error')
            return render_template('verify_security_questions.html', user=user)
        
        # Verify second answer if question exists
        if user.security_question_2 and answer_2:
            if not user.check_security_answer(2, answer_2):
                flash('Incorrect answer to security question', 'error')
                return render_template('verify_security_questions.html', user=user)
        
        # Verify third answer if question exists
        if user.security_question_3 and answer_3:
            if not user.check_security_answer(3, answer_3):
                flash('Incorrect answer to security question', 'error')
                return render_template('verify_security_questions.html', user=user)
        
        # All answers correct, proceed to password reset
        session['verified_user_id'] = user.id
        session.pop('reset_user_id', None)
        return redirect(url_for('reset_password'))
    
    return render_template('verify_security_questions.html', user=user)

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """Third step: Set new password"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    user_id = session.get('verified_user_id')
    if not user_id:
        flash('Session expired or verification incomplete. Please start over.', 'error')
        return redirect(url_for('forgot_password'))
    
    user = User.query.get(user_id)
    if not user:
        flash('User not found', 'error')
        session.pop('verified_user_id', None)
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not new_password or not confirm_password:
            flash('Both password fields are required', 'error')
            return render_template('reset_password.html')
        
        if len(new_password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return render_template('reset_password.html')
        
        if new_password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('reset_password.html')
        
        # Update password
        user.set_password(new_password)
        db.session.commit()
        
        # Clear session
        session.pop('verified_user_id', None)
        
        print("\n" + "="*60)
        print("PASSWORD RESET - SUCCESSFUL")
        print("="*60)
        print(f"User {user.username} reset their password at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60 + "\n")
        
        flash('Password successfully reset! You can now login with your new password.', 'success')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html')

@app.route('/dashboard')
@login_required
def dashboard():
    allergens = UserAllergen.query.filter_by(user_id=current_user.id).all()
    safe_products = SafeProduct.query.filter_by(user_id=current_user.id).order_by(SafeProduct.scan_date.desc()).limit(5).all()
    allergic_products = AllergicProduct.query.filter_by(user_id=current_user.id).order_by(AllergicProduct.scan_date.desc()).limit(5).all()
    potential_allergens = detect_potential_allergens(current_user.id)[:5]  # Top 5
    
    # Get EpiPen information
    epipens = EpiPen.query.filter_by(user_id=current_user.id).order_by(EpiPen.expiration_date.asc()).all()
    
    # Categorize epipens for dashboard warnings
    expired_epipens = [e for e in epipens if e.is_expired()]
    expiring_soon_epipens = [e for e in epipens if e.needs_reminder(30) and not e.is_expired()]
    
    return render_template('dashboard.html', 
                         allergens=allergens, 
                         safe_products=safe_products,
                         allergic_products=allergic_products,
                         potential_allergens=potential_allergens,
                         epipens=epipens,
                         expired_epipens=expired_epipens,
                         expiring_soon_epipens=expiring_soon_epipens)

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

@app.route('/epipens')
@login_required
def manage_epipens():
    """View and manage EpiPens"""
    from datetime import date
    epipens = EpiPen.query.filter_by(user_id=current_user.id).order_by(EpiPen.expiration_date.asc()).all()
    
    # Categorize epipens
    expired = []
    expiring_soon = []
    current = []
    
    for epipen in epipens:
        if epipen.is_expired():
            expired.append(epipen)
        elif epipen.needs_reminder(30):  # 30 days threshold
            expiring_soon.append(epipen)
        else:
            current.append(epipen)
    
    return render_template('epipens.html', 
                         expired=expired,
                         expiring_soon=expiring_soon,
                         current=current)

@app.route('/epipens/add', methods=['POST'])
@login_required
def add_epipen():
    """Add a new EpiPen"""
    from datetime import datetime
    
    name = request.form.get('name')
    location = request.form.get('location')
    expiration_date_str = request.form.get('expiration_date')
    lot_number = request.form.get('lot_number')
    notes = request.form.get('notes')
    
    if not name or not expiration_date_str:
        flash('EpiPen name and expiration date are required', 'error')
        return redirect(url_for('manage_epipens'))
    
    try:
        expiration_date = datetime.strptime(expiration_date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid expiration date format', 'error')
        return redirect(url_for('manage_epipens'))
    
    epipen = EpiPen(
        user_id=current_user.id,
        name=name,
        location=location,
        expiration_date=expiration_date,
        lot_number=lot_number,
        notes=notes
    )
    
    db.session.add(epipen)
    db.session.commit()
    flash('EpiPen added successfully', 'success')
    return redirect(url_for('manage_epipens'))

@app.route('/epipens/edit/<int:epipen_id>', methods=['POST'])
@login_required
def edit_epipen(epipen_id):
    """Edit an existing EpiPen"""
    from datetime import datetime
    
    epipen = EpiPen.query.get_or_404(epipen_id)
    
    if epipen.user_id != current_user.id:
        flash('Unauthorized', 'error')
        return redirect(url_for('manage_epipens'))
    
    name = request.form.get('name')
    location = request.form.get('location')
    expiration_date_str = request.form.get('expiration_date')
    lot_number = request.form.get('lot_number')
    notes = request.form.get('notes')
    
    if name:
        epipen.name = name
    if location is not None:
        epipen.location = location
    if expiration_date_str:
        try:
            epipen.expiration_date = datetime.strptime(expiration_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid expiration date format', 'error')
            return redirect(url_for('manage_epipens'))
    if lot_number is not None:
        epipen.lot_number = lot_number
    if notes is not None:
        epipen.notes = notes
    
    db.session.commit()
    flash('EpiPen updated successfully', 'success')
    return redirect(url_for('manage_epipens'))

@app.route('/epipens/delete/<int:epipen_id>', methods=['POST'])
@login_required
def delete_epipen(epipen_id):
    """Delete an EpiPen"""
    epipen = EpiPen.query.get_or_404(epipen_id)
    
    if epipen.user_id != current_user.id:
        flash('Unauthorized', 'error')
        return redirect(url_for('manage_epipens'))
    
    db.session.delete(epipen)
    db.session.commit()
    flash('EpiPen removed', 'success')
    return redirect(url_for('manage_epipens'))


def load_allergens_from_json():
    """Load allergens from the allergens.json file into the database"""
    import json
    
    json_path = os.path.join(os.path.dirname(__file__), 'data', 'allergens.json')
    
    if not os.path.exists(json_path):
        print(f"Warning: allergens.json not found at {json_path}")
        return
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            allergens_data = json.load(f)
        
        print(f"Loading {len(allergens_data)} allergens from Contact Dermatitis Institute database...")
        
        loaded_count = 0
        synonym_count = 0
        
        for allergen_data in allergens_data:
            allergen_name = allergen_data.get('allergen_name', '').strip()
            
            if not allergen_name:
                continue
            
            # Check if allergen already exists
            existing = KnownAllergen.query.filter_by(name=allergen_name).first()
            
            if not existing:
                # Create new allergen entry
                allergen = KnownAllergen(
                    name=allergen_name,
                    where_found=allergen_data.get('where_found', ''),
                    product_categories=json.dumps(allergen_data.get('product_categories', [])),
                    clinician_note=allergen_data.get('clinician_note', ''),
                    url=allergen_data.get('url', ''),
                    category='Contact Dermatitis Allergen',
                    description=allergen_data.get('where_found', '')
                )
                db.session.add(allergen)
                loaded_count += 1
            
            # Add synonyms from other_names
            other_names = allergen_data.get('other_names', [])
            for other_name in other_names:
                if other_name and other_name.strip():
                    other_name = other_name.strip()
                    
                    # Check if synonym already exists
                    existing_syn = IngredientSynonym.query.filter(
                        (db.func.lower(IngredientSynonym.primary_name) == allergen_name.lower()) &
                        (db.func.lower(IngredientSynonym.synonym) == other_name.lower())
                    ).first()
                    
                    if not existing_syn:
                        synonym = IngredientSynonym(
                            primary_name=allergen_name,
                            synonym=other_name
                        )
                        db.session.add(synonym)
                        synonym_count += 1
        
        db.session.commit()
        print(f"Successfully loaded {loaded_count} new allergens and {synonym_count} synonyms")
        
    except Exception as e:
        print(f"Error loading allergens from JSON: {str(e)}")
        db.session.rollback()

def migrate_database():
    """Migrate existing database schema to add new columns"""
    try:
        print("Checking for database migrations...")
        
        # Add new columns to known_allergen table using raw SQL
        with db.engine.connect() as conn:
            # Check each column and add if it doesn't exist for known_allergen table
            try:
                conn.execute(db.text("ALTER TABLE known_allergen ADD COLUMN where_found TEXT"))
                print("  Added column: where_found")
            except:
                pass
            
            try:
                conn.execute(db.text("ALTER TABLE known_allergen ADD COLUMN product_categories TEXT"))
                print("  Added column: product_categories")
            except:
                pass
            
            try:
                conn.execute(db.text("ALTER TABLE known_allergen ADD COLUMN clinician_note TEXT"))
                print("  Added column: clinician_note")
            except:
                pass
            
            try:
                conn.execute(db.text("ALTER TABLE known_allergen ADD COLUMN url VARCHAR(500)"))
                print("  Added column: url")
            except:
                pass
            
            # Add security question columns to user table
            try:
                conn.execute(db.text("ALTER TABLE user ADD COLUMN security_question_1 VARCHAR(200)"))
                print("  Added column: security_question_1")
            except:
                pass
            
            try:
                conn.execute(db.text("ALTER TABLE user ADD COLUMN security_answer_1_hash VARCHAR(200)"))
                print("  Added column: security_answer_1_hash")
            except:
                pass
            
            try:
                conn.execute(db.text("ALTER TABLE user ADD COLUMN security_question_2 VARCHAR(200)"))
                print("  Added column: security_question_2")
            except:
                pass
            
            try:
                conn.execute(db.text("ALTER TABLE user ADD COLUMN security_answer_2_hash VARCHAR(200)"))
                print("  Added column: security_answer_2_hash")
            except:
                pass
            
            try:
                conn.execute(db.text("ALTER TABLE user ADD COLUMN security_question_3 VARCHAR(200)"))
                print("  Added column: security_question_3")
            except:
                pass
            
            try:
                conn.execute(db.text("ALTER TABLE user ADD COLUMN security_answer_3_hash VARCHAR(200)"))
                print("  Added column: security_answer_3_hash")
            except:
                pass
            
            conn.commit()
        
        print("Database migration completed successfully")
        
    except Exception as e:
        print(f"Migration note: {str(e)}")

# Initialize database
def init_db():
    with app.app_context():
        db.create_all()
        
        # Migrate existing database if needed
        migrate_database()
        
        # Load allergens from JSON file
        if KnownAllergen.query.count() == 0:
            load_allergens_from_json()
        else:
            # If database exists but allergens.json has more entries, add new ones
            json_path = os.path.join(os.path.dirname(__file__), 'data', 'allergens.json')
            if os.path.exists(json_path):
                load_allergens_from_json()
        
        # Add some common ingredient synonyms if none exist
        # Note: allergens.json loading will add many more synonyms automatically
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

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=7860, debug=True)
