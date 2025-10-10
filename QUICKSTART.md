# Quick Start Guide

## 🐳 Docker (Fastest & Easiest)

**Recommended for most users:**

```bash
# 1. Clone the repository
git clone https://github.com/DrewThomasson/Derme---Cosmetic-Wellness-Platform.git
cd Derme---Cosmetic-Wellness-Platform

# 2. Start with Docker
docker compose up -d

# 3. Open your browser at: http://localhost:7860
# 4. Click "Try Demo" for instant access
```

**With AI features:**
```bash
# Add your Gemini API key
echo "GEMINI_API_KEY=your-key-here" > .env

# Restart
docker compose restart
```

**See [DOCKER_README.md](DOCKER_README.md) for complete Docker documentation.**

---

## 🚀 Running Locally (Manual Setup)

### Option 1: Without AI Features (Fastest)

```bash
# 1. Install Tesseract OCR (for image text extraction)
# Ubuntu/Debian:
sudo apt-get install tesseract-ocr

# macOS:
brew install tesseract

# 2. Clone and setup
git clone https://github.com/DrewThomasson/Derme---Cosmetic-Wellness-Platform.git
cd Derme---Cosmetic-Wellness-Platform
pip install -r requirements.txt

# 3. Run the application
python app.py

# 4. Open your browser at: http://localhost:7860
```

### Option 2: With AI Features (Recommended)

```bash
# Follow steps above, then:

# Get your FREE Gemini API key from:
# https://makersuite.google.com/app/apikey

# Create configuration file
cp .env.example .env

# Edit .env and add your API key:
# GEMINI_API_KEY=your-key-here

# Run the application
python app.py
```

**With Gemini AI you get:**
- 🔍 Better OCR accuracy for ingredient extraction
- 🧠 Smart allergen identification with alternative names
- 📚 Detailed ingredient information on demand
- ⚡ AI-powered explanations for detected allergens

## 🎯 First Time Setup

1. **Try Demo Mode** (Fastest!)
   - Click "🧪 Try Demo" on the home page
   - Pre-loaded with sample allergens
   - No registration needed

2. **Or Register Your Account**
   - Click "Register" in the navigation
   - Create your username and password

3. **Add Your Allergens**
   - Go to "My Allergens"
   - Add ingredients you're allergic to
   - Set severity levels (mild, moderate, severe)

4. **Scan Your First Product**
   - Go to "Scan Product"
   - Upload a clear photo of the ingredient list
   - View the AI-powered analysis results
   - Click "ℹ️ More Info" for detailed allergen information

## 🧪 Sample Allergens to Test

Try adding these common cosmetic allergens:
- **Fragrance** (also called Parfum) - Severe
- **Parabens** (Methylparaben, Propylparaben) - Moderate
- **Sodium Lauryl Sulfate** (SLS) - Mild
- **Formaldehyde** - Severe
- **Lanolin** - Moderate
- **Propylene Glycol** - Mild

## 💡 Tips for Best Results

### For Scanning:
- Use good lighting when photographing labels
- Keep the camera steady and focused
- Ensure text is in focus and readable
- Capture the entire ingredient list
- Avoid glare and shadows
- Use a flat surface

### For Better Allergen Detection:
- Scan both safe AND allergic products
- The more products you scan, the better the pattern detection
- Check the "Potential Allergens" section on dashboard
- Use AI features for comprehensive ingredient info

## 🆘 Troubleshooting

**"Tesseract not found" error:**
- Make sure Tesseract is installed and in your PATH
- On Windows, you may need to set the path in app.py

**Gemini API not working:**
- Check your API key in `.env` file
- Verify quota at [Google AI Studio](https://makersuite.google.com/app/apikey)
- App automatically falls back to Tesseract if Gemini unavailable

**Database errors:**
- Delete `instance/derme.db` and restart to recreate

**Upload not working:**
- Check that `static/uploads/` directory exists
- Verify file is an image (JPG, PNG, JPEG)
- File size must be under 16MB

**No ingredients detected:**
- Try a clearer, better-lit photo
- Enable Gemini for better OCR accuracy
- Check that ingredient text is visible in the image

## 📚 Learn More

- **Full Configuration**: See [CONFIG_README.md](CONFIG_README.md)
- **Deployment Guide**: See [README_DEPLOYMENT.md](README_DEPLOYMENT.md)
- **Main Documentation**: See [README.md](README.md)

## 🛠️ Tech Stack

- **Backend**: Flask (Python)
- **Database**: SQLite
- **OCR**: Tesseract + Google Gemini Vision (optional)
- **AI Analysis**: Google Gemini 1.5 Flash (optional)
- **Authentication**: Flask-Login
- **Image Processing**: Pillow (PIL)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript

## 🌟 What Makes This Special?

- **🤖 AI-Powered**: Optional Google Gemini integration for enhanced accuracy
- **🔄 Smart Fallback**: Works perfectly without API keys
- **📊 Pattern Detection**: Compares safe vs allergic products to find hidden triggers
- **🎯 User-Friendly**: Demo mode for instant testing
- **🔒 Privacy-First**: All data stored locally in your SQLite database
