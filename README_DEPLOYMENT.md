# Derme - Deployment Guide

## Important: Auto-Login Behavior

### HuggingFace Spaces Deployment
When deployed to HuggingFace Spaces, the application automatically logs in users with a demo account. **No login page will be shown** - users are taken directly to the dashboard for immediate testing.

- ✅ **Auto-login enabled**: Detects HuggingFace environment via `SPACE_ID` environment variable
- 🔒 **Login/Register hidden**: Authentication pages and buttons are not displayed
- 👤 **Demo user**: Automatically logged in as `demo_user` with pre-populated sample allergens
- 🚫 **No logout**: Logout button is hidden to maintain demo experience

### Local Development
When running locally, the full authentication system is available:

- 📝 **Registration & Login**: Users can create accounts and log in normally
- 🧪 **Demo Button**: A "Try Demo" button provides quick access to test features
- 🔓 **Logout Available**: Users can log out and switch accounts

## Running Locally

### Prerequisites
- Python 3.8 or higher
- Tesseract OCR installed on your system

### Installation Steps

1. **Install Tesseract OCR**
   
   - **Ubuntu/Debian:**
     ```bash
     sudo apt-get update
     sudo apt-get install tesseract-ocr
     ```
   
   - **macOS:**
     ```bash
     brew install tesseract
     ```
   
   - **Windows:**
     Download and install from: https://github.com/UB-Mannheim/tesseract/wiki

2. **Install Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application**
   ```bash
   python app.py
   ```

4. **Access the Application**
   Open your browser and navigate to: `http://localhost:7860`

## Deploying to HuggingFace Spaces

### Prerequisites
- A HuggingFace account
- Git installed on your system

### Deployment Steps

1. **Create a new Space on HuggingFace**
   - Go to https://huggingface.co/spaces
   - Click "Create new Space"
   - Choose a name for your Space
   - Select "Gradio" as the SDK (or "Streamlit", but the app uses Flask which works with custom spaces)
   - Set visibility to Public or Private

2. **Configure Space**
   
   Create a file named `packages.txt` in the root directory:
   ```
   tesseract-ocr
   tesseract-ocr-eng
   ```

3. **Push Code to HuggingFace Space**
   ```bash
   git remote add space https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME
   git push space main
   ```

4. **Space Configuration**
   The app.py is already configured to run on port 7860, which is the default port for HuggingFace Spaces.
   
   **Note**: Once deployed, the application will automatically detect it's running on HuggingFace Spaces and enable auto-login mode. Users will be taken directly to the dashboard without seeing any login pages.

### Environment Variables (Optional)

You can set environment variables in HuggingFace Spaces settings:
- `SECRET_KEY`: A secure secret key for Flask sessions (recommended for production)

## Application Structure

```
Derme---Cosmetic-Wellness-Platform/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── packages.txt          # System packages for HuggingFace
├── templates/            # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── allergens.html
│   ├── scan.html
│   └── results.html
├── static/               # Static files
│   └── css/
│       └── style.css
└── derme.db             # SQLite database (created on first run)
```

## Features

1. **User Authentication**
   - User registration and login
   - Secure password hashing
   - Session management

2. **Allergen Management**
   - Add personal allergens
   - Set severity levels (mild, moderate, severe)
   - Remove allergens

3. **Product Scanning**
   - Upload images of ingredient labels
   - OCR text extraction using Tesseract
   - Automatic ingredient parsing

4. **Ingredient Analysis**
   - Cross-reference with user's allergen list
   - Check against known allergen database
   - Identify ingredient synonyms

5. **Product Tracking**
   - Save safe products
   - View scan history
   - Dashboard overview

## Database Schema

The application uses SQLite with the following tables:

- **User**: Stores user accounts
- **UserAllergen**: Stores user's personal allergens
- **SafeProduct**: Stores scanned safe products
- **IngredientSynonym**: Maps ingredient synonyms
- **KnownAllergen**: Database of common allergens

## Security Notes

- Passwords are hashed using Werkzeug's security utilities
- Flask sessions are used for authentication
- Remember to set a secure SECRET_KEY in production

## Troubleshooting

### Tesseract Not Found Error
If you get an error about Tesseract not being found:
- Make sure Tesseract is installed
- On Windows, you may need to add Tesseract to PATH or specify the path in app.py:
  ```python
  pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
  ```

### Database Errors
If you encounter database errors:
- Delete `derme.db` and restart the application to recreate the database

### Upload Issues
- Ensure the `static/uploads` directory exists and is writable
- Check file size limits (default: 16MB)

## Future Enhancements

- Integration with external allergen databases
- Barcode scanning support
- Mobile app version
- Export/import user data
- Advanced ingredient analysis
- Symptom tracking journal
