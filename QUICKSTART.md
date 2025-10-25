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

2. **Explore the Allergen Database** (NEW!)
   - The app includes a comprehensive database of 496 known allergens
   - Over 14,000 ingredient synonyms for accurate matching
   - Data sourced from the Contact Dermatitis Institute

3. **Add Your Personal Allergens**
   - Go to "My Allergens"
   - Add ingredients you're allergic to
   - Set severity levels (mild, moderate, severe)

4. **Scan a Product**
   - Go to "Scan Product"
   - Upload a clear photo of the ingredient list
   - View the analysis results with detailed allergen information

## What's New: Comprehensive Allergen Database

The app now includes the **Contact Dermatitis Institute Allergen Database**:

- **496 Known Allergens**: Comprehensive list of contact dermatitis allergens
- **14,000+ Synonyms**: Matches ingredients even when listed under different names
- **Detailed Information**: Each allergen includes:
  - Where it's commonly found
  - Product categories that may contain it
  - Clinical notes for medical professionals
  - Links to more detailed information

### Example Detection

When you scan a product, the app will now detect:
- **Your Personal Allergens**: Ingredients you've marked as causing reactions
- **Known Database Allergens**: Ingredients known to cause contact dermatitis
- **Safe Ingredients**: Ingredients with no known allergen issues

The app matches ingredients across all known names. For example:
- "Parfum" → Matches "Fragrance"
- "MIT" → Matches "Methylisothiazolinone"
- "Kathon CG" → Matches preservative allergens

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
