# Derme Configuration Guide

## Overview

The Derme application now supports Google Gemini AI for enhanced allergen detection and ingredient analysis. This guide will help you configure the application to use Gemini's powerful vision and language models.

## Features Powered by Google Gemini

1. **Enhanced OCR**: Extract ingredient lists from product photos with better accuracy than traditional OCR
2. **Allergen Identification**: Automatically identify allergens and their alternative names
3. **Ingredient Analysis**: Get detailed information about ingredients, their potential risks, and common uses
4. **Smart Cross-referencing**: Match ingredients against your known allergens, even with different naming conventions

## Getting Your Gemini API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy your API key

**Note**: The Gemini API has a free tier that includes:
- 60 requests per minute
- 1,500 requests per day
- Perfect for personal use and testing

## Configuration

### Step 1: Set Up Environment Variables

Create a `.env` file in the project root (copy from `.env.example`):

```bash
cp .env.example .env
```

### Step 2: Configure Your Settings

Edit `.env` with your preferences:

```bash
# Required: Your Gemini API Key
GEMINI_API_KEY=your-api-key-here

# Optional: Choose Gemini Model (default: gemini-1.5-flash)
# Options: gemini-1.5-flash (faster, cheaper) or gemini-1.5-pro (more capable)
GEMINI_MODEL=gemini-1.5-flash

# Optional: Feature flags
USE_GEMINI_FOR_OCR=true              # Use Gemini for image-to-text extraction
USE_GEMINI_FOR_ALLERGEN_INFO=true    # Use Gemini for detailed allergen info
FALLBACK_TO_TESSERACT=true           # Use Tesseract if Gemini fails
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Run the Application

```bash
python app.py
```

## Configuration Options

### Flask Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key for sessions | `dev-secret-key-change-in-production` |
| `DATABASE_URL` | Database connection string | `sqlite:///derme.db` |

### Gemini API Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Your Google Gemini API key | (empty - required for Gemini features) |
| `GEMINI_MODEL` | Gemini model to use | `gemini-1.5-flash` |
| `USE_GEMINI_FOR_OCR` | Enable Gemini for OCR | `true` |
| `USE_GEMINI_FOR_ALLERGEN_INFO` | Enable Gemini for allergen details | `true` |
| `FALLBACK_TO_TESSERACT` | Use Tesseract if Gemini unavailable | `true` |

### Analysis Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `CONFIDENCE_THRESHOLD` | Minimum confidence for allergen matches | `0.6` |
| `MAX_ALLERGEN_SYNONYMS` | Maximum synonyms to fetch per ingredient | `10` |

## Usage Without Gemini

The application works perfectly fine without Gemini API key. It will automatically fall back to:
- **Tesseract OCR** for text extraction
- **Database lookup** for known allergens
- **Basic cross-referencing** for potential allergen detection

To run without Gemini, simply leave `GEMINI_API_KEY` empty or don't set it.

## Deployment

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set up configuration
cp .env.example .env
# Edit .env with your settings

# Run the app
python app.py
```

### HuggingFace Spaces

When deploying to HuggingFace Spaces:

1. Add your `GEMINI_API_KEY` in the Space's Settings → Repository secrets
2. The app will automatically detect HuggingFace environment
3. All other configuration can use defaults

### Production Deployment

For production:
1. **Always** set a secure `SECRET_KEY`
2. Consider using `gemini-1.5-pro` for better accuracy
3. Monitor your Gemini API usage in [Google AI Studio](https://makersuite.google.com/app/apikey)
4. Set appropriate rate limits if needed

## Troubleshooting

### Gemini API Not Working

**Problem**: Getting errors when scanning images

**Solutions**:
1. Verify your API key is correct
2. Check your API quota at [Google AI Studio](https://makersuite.google.com/app/apikey)
3. Ensure `FALLBACK_TO_TESSERACT=true` for automatic fallback
4. Check the console logs for specific error messages

### No Ingredients Detected

**Problem**: Scan completes but no ingredients found

**Solutions**:
1. Ensure image quality is good (clear, well-lit)
2. Make sure ingredient list is clearly visible
3. Try with `USE_GEMINI_FOR_OCR=true` for better accuracy
4. Verify Tesseract is installed if using fallback

### API Rate Limits

**Problem**: Hitting API rate limits

**Solutions**:
1. Free tier: 60 requests/minute, 1500/day
2. Add delays between scans if batch processing
3. Consider caching results for frequently scanned products
4. Upgrade to paid tier if needed for higher volume

## Advanced Configuration

### Custom Gemini Prompts

To customize how Gemini analyzes ingredients, edit the prompts in `gemini_helper.py`:

```python
# Example: Modify the allergen analysis prompt
prompt = """
Your custom prompt here...
"""
```

### Caching Results

For better performance, consider implementing caching:

```python
# Add to app.py
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_allergen_info(ingredient):
    return gemini_helper.get_allergen_information(ingredient)
```

## Support

For issues or questions:
- Check the [GitHub Issues](https://github.com/DrewThomasson/Derme---Cosmetic-Wellness-Platform/issues)
- Review [Google Gemini API Documentation](https://ai.google.dev/docs)
- Contact the development team

## Privacy & Security

- API keys are stored as environment variables, never in code
- Uploaded images are processed in memory, not permanently stored
- Gemini API calls are made over HTTPS
- User allergen data stays in your local database
- Review [Google's Privacy Policy](https://policies.google.com/privacy) for API usage

## Cost Considerations

### Free Tier
- **Perfect for**: Personal use, testing, small-scale applications
- **Limits**: 60 RPM, 1500 RPD
- **Cost**: $0

### Paid Usage
- **Gemini 1.5 Flash**: ~$0.075 per 1M input tokens
- **Gemini 1.5 Pro**: ~$3.50 per 1M input tokens
- Typical scan costs: <$0.01 per image with Flash model

## License

This project is licensed under the MIT License - see the LICENSE file for details.
