"""
Pytest configuration and fixtures for Derme tests
"""
import pytest
import sys
import os

# Add parent directory to path to import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app as flask_app, db, User, UserAllergen, SafeProduct, AllergicProduct, KnownAllergen, IngredientSynonym


@pytest.fixture
def app():
    """Create and configure a test Flask application"""
    flask_app.config['TESTING'] = True
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    flask_app.config['WTF_CSRF_ENABLED'] = False
    flask_app.config['SECRET_KEY'] = 'test-secret-key'
    
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client for the Flask application"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a test CLI runner for the Flask application"""
    return app.test_cli_runner()


@pytest.fixture
def test_user(app):
    """Create a test user in the database"""
    with app.app_context():
        user = User(username='testuser', email='test@example.com')
        user.set_password('testpassword123')
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def authenticated_client(client, test_user):
    """Create an authenticated test client"""
    client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    }, follow_redirects=True)
    return client


@pytest.fixture
def test_user_with_allergen(app, test_user):
    """Create a test user with a known allergen"""
    with app.app_context():
        user = User.query.filter_by(username='testuser').first()
        allergen = UserAllergen(
            user_id=user.id,
            ingredient_name='Fragrance',
            severity='severe'
        )
        db.session.add(allergen)
        db.session.commit()
        return user


@pytest.fixture
def known_allergen_db(app):
    """Populate database with some known allergens"""
    with app.app_context():
        allergens = [
            KnownAllergen(
                name='Methylisothiazolinone',
                where_found='Preservative in cosmetics and personal care products',
                product_categories='["shampoo", "lotion", "makeup"]',
                category='Preservative',
                description='Common preservative that can cause contact dermatitis'
            ),
            KnownAllergen(
                name='Fragrance',
                where_found='Perfumes, cosmetics, household products',
                product_categories='["perfume", "lotion", "soap"]',
                category='Fragrance',
                description='Common allergen in fragranced products'
            ),
            KnownAllergen(
                name='Formaldehyde',
                where_found='Preservative, disinfectant, construction materials',
                product_categories='["nail polish", "shampoo", "makeup"]',
                category='Preservative',
                description='Known contact allergen and sensitizer'
            )
        ]
        
        for allergen in allergens:
            db.session.add(allergen)
        
        # Add some synonyms
        synonyms = [
            IngredientSynonym(primary_name='Fragrance', synonym='Parfum'),
            IngredientSynonym(primary_name='Fragrance', synonym='Perfume'),
            IngredientSynonym(primary_name='Methylisothiazolinone', synonym='MIT'),
        ]
        
        for synonym in synonyms:
            db.session.add(synonym)
        
        db.session.commit()
