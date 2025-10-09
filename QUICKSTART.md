# Quick Start Guide

## Running Locally (Quick Method)

```bash
# 1. Install Tesseract OCR
# Ubuntu/Debian:
sudo apt-get install tesseract-ocr

# macOS:
brew install tesseract

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Run the application
python app.py

# 4. Open your browser
# Navigate to: http://localhost:7860
```

## First Time Setup

1. **Register an Account**
   - Click "Register" in the navigation
   - Create your username and password

2. **Add Your Allergens**
   - Go to "My Allergens"
   - Add ingredients you're allergic to
   - Set severity levels (mild, moderate, severe)

3. **Scan a Product**
   - Go to "Scan Product"
   - Upload a clear photo of the ingredient list
   - View the analysis results

## Sample Allergens to Test

Try adding these common cosmetic allergens:
- Fragrance (Parfum)
- Parabens (Methylparaben, Propylparaben)
- Sodium Lauryl Sulfate (SLS)
- Formaldehyde
- Lanolin
- Propylene Glycol

## Tips for Best Results

- Use good lighting when photographing labels
- Keep the camera steady
- Ensure text is in focus and readable
- Capture the entire ingredient list
- Avoid glare and shadows

## Troubleshooting

**"Tesseract not found" error:**
- Make sure Tesseract is installed and in your PATH
- On Windows, you may need to set the path in app.py

**Database errors:**
- Delete `derme.db` and restart to recreate

**Upload not working:**
- Check that `static/uploads/` directory exists
- Verify file is an image (JPG, PNG, JPEG)
- File size must be under 16MB

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: SQLite
- **OCR**: Tesseract
- **Authentication**: Flask-Login
- **Image Processing**: Pillow (PIL)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
