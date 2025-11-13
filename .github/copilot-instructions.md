# Copilot Instructions for Derme - Cosmetic Wellness Platform

## Project Overview

Derme is a Flask-based web application that helps users with sensitive skin and allergies analyze ingredients in cosmetic products. The application allows users to scan product labels using OCR, identify potential allergens, track skin reactions, and receive personalized recommendations.

**Key Features:**
- Product ingredient scanning via OCR (Tesseract)
- Comprehensive allergen database (496+ known allergens with 14,000+ synonyms)
- User authentication and personal allergen tracking
- Severity-based allergen classification
- Product history tracking (safe and allergic products)
- Password recovery via security questions

**Important Notice:** This is for informational use only and NOT medical advice. Always consult a qualified health provider for medical concerns.

## Technology Stack

### Backend
- **Framework:** Flask 3.0.0
- **Database:** SQLite with Flask-SQLAlchemy 3.1.1
- **Authentication:** Flask-Login 0.6.3
- **Security:** Werkzeug 3.0.1 for password hashing
- **OCR:** Tesseract OCR with pytesseract 0.3.10
- **Image Processing:** Pillow 10.1.0
- **HTTP Requests:** requests 2.31.0

### Frontend
- **HTML5, CSS3, Vanilla JavaScript**
- Templates in `templates/` directory
- Static assets in `static/` directory

### System Dependencies
- Tesseract OCR (system package)
- Python 3.8 or higher (recommended: 3.10.18)

## Setup and Installation

### Prerequisites
```bash
# Install Tesseract OCR
# Ubuntu/Debian:
sudo apt-get install tesseract-ocr tesseract-ocr-eng libtesseract-dev

# macOS:
brew install tesseract
```

### Environment Setup
```bash
# Clone the repository
git clone https://github.com/DrewThomasson/Derme---Cosmetic-Wellness-Platform.git
cd Derme---Cosmetic-Wellness-Platform

# Create conda environment (recommended)
conda create -n derme python=3.10.18
conda activate derme

# Install Python dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

The application will:
- Initialize the SQLite database (`derme.db`)
- Load allergen data from `data/allergens.json` on first run
- Start the Flask development server on port 7860

### Environment Variables
- `SECRET_KEY`: Flask secret key (defaults to 'dev-secret-key-change-in-production')
- `SPACE_ID`: Set when running on HuggingFace Spaces

## Project Structure

```
Derme---Cosmetic-Wellness-Platform/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── packages.txt               # System dependencies (Tesseract)
├── data/
│   ├── allergens.json         # 496 allergens with synonyms
│   └── README.md              # Allergen database documentation
├── templates/                 # HTML templates
│   ├── base.html             # Base template with navigation
│   ├── index.html            # Landing page
│   ├── login.html            # Login page
│   ├── register.html         # Registration with security questions
│   ├── scan.html             # Product scanning interface
│   ├── results.html          # Scan results display
│   ├── allergens.html        # User allergen management
│   └── dashboard.html        # User dashboard
├── static/
│   ├── css/                  # Stylesheets
│   └── uploads/              # User-uploaded images (created at runtime)
├── test_forgot_password.py   # Test script for password recovery
└── demo_allergen_detection.py # Allergen detection demo

Documentation:
├── README.md                  # Main documentation
├── QUICKSTART.md             # Quick start guide
├── IMPLEMENTATION_SUMMARY.md # Allergen database integration details
├── README_DEPLOYMENT.md      # Deployment guide
└── MIGRATION_FIX.md          # Database migration notes
```

## Database Models

### User
- Authentication: username, email, password_hash
- Security questions (3) for password recovery
- Relationships: allergens, safe_products, allergic_products

### UserAllergen
- Personal allergens tracked per user
- Fields: name, severity (mild, moderate, severe)
- Foreign key to User

### KnownAllergen
- Comprehensive allergen database (496 allergens)
- Fields: name, where_found, product_categories, clinician_note, url
- Populated from `data/allergens.json`

### AllergenSynonym
- Maps 14,000+ ingredient name variations to allergens
- Enables matching across chemical names, trade names, abbreviations

### SafeProduct / AllergicProduct
- Product history tracking
- Fields: product_name, ingredients, scan_date, notes

## Coding Conventions

### Python Style
- Follow PEP 8 style guide
- Use 4 spaces for indentation
- Keep lines under 100 characters when possible
- Use meaningful variable and function names
- Add docstrings to functions that aren't self-explanatory

### Flask Patterns
- Use blueprints if adding major new features
- Keep route handlers focused and delegate to helper functions
- Use `flash()` for user feedback messages
- Always use `@login_required` decorator for protected routes
- Handle database sessions properly (commit or rollback)

### Database Operations
- Use SQLAlchemy ORM, not raw SQL
- Always handle potential database errors with try/except
- Use `db.session.commit()` explicitly after changes
- Clean up with `db.session.rollback()` on errors

### Security Best Practices
- Never commit secrets or API keys
- Use `generate_password_hash()` and `check_password_hash()` for passwords
- Validate and sanitize all user inputs
- Use `secure_filename()` for file uploads
- Set appropriate file size limits (16MB max)
- Implement CSRF protection for forms
- Use `@login_required` for authenticated endpoints

### Template Guidelines
- Extend `base.html` for consistent navigation
- Use Flask's `url_for()` for all internal links
- Escape user-generated content (Jinja2 does this by default)
- Keep JavaScript minimal and in templates (no separate JS files currently)
- Use Bootstrap classes for styling consistency

## Testing

### Current Test Infrastructure
- Basic test script: `test_forgot_password.py`
- Demonstrates database operations and user creation
- No comprehensive test suite currently

### Testing Approach
When adding tests:
- Use Flask's test client for route testing
- Create test fixtures with sample data
- Test both success and error paths
- Clean up test data after tests run
- Run tests with: `python test_forgot_password.py`

### Manual Testing
- Test OCR with various product images (good/bad lighting, angles)
- Verify allergen matching with different ingredient name formats
- Test password recovery flow completely
- Check edge cases (empty inputs, special characters, very long lists)

## Building and Running

### Development Mode
```bash
# Standard development run
python app.py

# Access at: http://localhost:7860
```

### Database Management
```bash
# Delete database to reset (will recreate on next run)
rm derme.db

# Database automatically initializes with allergen data from data/allergens.json
```

### OCR Testing
Use the demo script to test allergen detection:
```bash
python demo_allergen_detection.py
```

## Deployment Considerations

### HuggingFace Spaces
- Application detects `SPACE_ID` environment variable
- Uses port 7860 by default
- Ensure `packages.txt` includes Tesseract dependencies
- Database persists in the container

### General Deployment
- Set `SECRET_KEY` environment variable to a secure random value
- Use a production WSGI server (e.g., Gunicorn)
- Consider using PostgreSQL instead of SQLite for production
- Set up proper logging
- Configure static file serving
- Enable HTTPS

## Common Tasks

### Adding New Allergens
1. Update `data/allergens.json` with new allergen data
2. Delete existing database: `rm derme.db`
3. Restart application to rebuild database

### Updating Dependencies
```bash
# Update requirements.txt after adding packages
pip freeze > requirements.txt

# Always test after dependency updates
```

### Modifying Database Schema
1. Update model classes in `app.py`
2. Consider migration strategy (currently: delete and recreate)
3. Update `MIGRATION_FIX.md` with migration notes
4. Test with existing user data if possible

### Adding New Routes
1. Add route handler in `app.py`
2. Create corresponding template in `templates/`
3. Update navigation in `base.html` if needed
4. Add any required database queries
5. Test authentication and authorization

## Known Limitations

- SQLite database (not ideal for high concurrency)
- No automated test suite
- OCR quality depends on image quality
- File uploads stored locally (no cloud storage)
- Basic password recovery (security questions only)
- No email functionality
- No admin interface

## Important Files to Understand

1. **app.py**: Core application logic, routes, database models
2. **data/allergens.json**: Allergen database source
3. **templates/results.html**: Main results display with allergen information
4. **QUICKSTART.md**: User-facing quick start guide
5. **IMPLEMENTATION_SUMMARY.md**: Technical details of allergen database integration

## Common Pitfalls to Avoid

1. **Don't modify the allergen database schema** without updating the JSON loader
2. **Don't bypass authentication** on protected routes
3. **Don't expose database errors** to users (use generic error messages)
4. **Don't store sensitive data in plain text**
5. **Don't commit `derme.db`** or user-uploaded files
6. **Don't hardcode paths** - use Flask's built-in path helpers
7. **Don't skip input validation** - especially for file uploads

## Getting Help

- Review `QUICKSTART.md` for user-focused documentation
- Check `IMPLEMENTATION_SUMMARY.md` for allergen database details
- Run `demo_allergen_detection.py` to see allergen detection examples
- Read inline comments in `app.py` for specific implementation details

## Attribution

- Allergen data: Contact Dermatitis Institute (https://www.contactdermatitisinstitute.com)
- Course: Software Engineering Project - Fall 2025
- Team: Super Cool Guys (Group 8)
