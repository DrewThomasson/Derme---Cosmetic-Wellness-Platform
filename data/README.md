# Allergen Database

This directory contains the Contact Dermatitis Institute allergen database used by the Derme application.

## allergens.json

This file contains a comprehensive database of 496 known allergens that commonly cause contact dermatitis. The data is sourced from the Contact Dermatitis Institute website (https://www.contactdermatitisinstitute.com).

### Data Structure

Each allergen entry includes:

- **allergen_name**: The primary name of the allergen
- **where_found**: Description of where the allergen is commonly found or used
- **other_names**: Array of alternative names, chemical names, and trade names for the allergen
- **product_categories**: Array of product types where this allergen is typically found
- **clinician_note**: Additional notes for medical professionals (may be empty)
- **url**: Link to more detailed information on the Contact Dermatitis Institute website

### Example Entry

```json
{
  "allergen_name": "Methylisothiazolinone",
  "where_found": "This substance is a preservative used in personal hygiene products...",
  "other_names": [
    "2-Methyl-4-isothiazolin-3-one",
    "MIT",
    "MI"
  ],
  "product_categories": [
    "Body Washes/Hand Soaps/Moisturizers",
    "Cleaners",
    "Hair Products"
  ],
  "clinician_note": "",
  "url": "https://www.contactdermatitisinstitute.com/methylisothiazolinone.php"
}
```

### Database Loading

The allergen database is automatically loaded into the SQLite database on application startup:

1. The `load_allergens_from_json()` function reads the allergens.json file
2. Each allergen is stored in the `KnownAllergen` table
3. All alternative names are stored in the `IngredientSynonym` table for comprehensive matching
4. This enables the app to detect allergens even when they're listed under different names

### Statistics

- **Total Allergens**: 496
- **Total Synonyms**: 14,000+
- **Source**: Contact Dermatitis Institute (https://www.contactdermatitisinstitute.com)

### Updates

To update the allergen database, replace the `allergens.json` file with a new version and delete the `instance/derme.db` file. The database will be recreated with the new data on next startup.

## Attribution

This database was created by scraping the Contact Dermatitis Institute website. All data is provided for informational and educational purposes only. Please refer to the original source for the most up-to-date information.

**Important**: This information is not medical advice. Always consult with a qualified healthcare provider for medical advice regarding allergies and skin conditions.
