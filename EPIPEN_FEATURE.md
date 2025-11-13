# EpiPen Management Feature

## Overview
This feature adds comprehensive EpiPen tracking with expiration dates and automatic reminders to the Derme application. Users can now track their EpiPens, receive warnings when they are about to expire, and get urgent notifications for expired EpiPens.

## Features

### 1. EpiPen Tracking
- **Name**: Type of EpiPen (e.g., "EpiPen", "EpiPen Jr", "Auvi-Q")
- **Location**: Where the EpiPen is stored (e.g., "Bedroom drawer", "Purse", "Car")
- **Expiration Date**: When the EpiPen expires
- **Lot Number**: Manufacturing lot number for tracking
- **Notes**: Additional information about the EpiPen

### 2. Automatic Expiration Detection
The system automatically categorizes EpiPens into three groups:
- **Expired**: EpiPens that have passed their expiration date
- **Expiring Soon**: EpiPens that will expire within 30 days
- **Current**: EpiPens that are still valid and not expiring soon

### 3. Dashboard Warnings
The dashboard displays urgent warnings for:
- **Expired EpiPens**: Red alert banner prompting immediate replacement
- **Expiring Soon**: Yellow warning banner for EpiPens expiring within 30 days
- **Status Summary**: Quick overview of total, expired, and expiring EpiPens

### 4. EpiPen Management Page
A dedicated page at `/epipens` provides:
- Visual warnings for expired and expiring EpiPens
- List of all EpiPens with detailed information
- Add new EpiPen form
- Inline editing for existing EpiPens
- Delete functionality with confirmation
- Color-coded status indicators
- Important safety information

## Usage

### Adding an EpiPen
1. Navigate to "EpiPens" in the navigation menu
2. Fill out the "Add New EpiPen" form:
   - EpiPen Type (required)
   - Location (optional but recommended)
   - Expiration Date (required)
   - Lot Number (optional)
   - Notes (optional)
3. Click "Add EpiPen"

### Editing an EpiPen
1. Go to the EpiPens management page
2. Click "Edit" on the EpiPen you want to modify
3. Update the fields in the inline form
4. Click "Save Changes"

### Deleting an EpiPen
1. Go to the EpiPens management page
2. Click "Delete" on the EpiPen you want to remove
3. Confirm the deletion in the prompt

## Technical Details

### Database Model
```python
class EpiPen(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(200))
    expiration_date = db.Column(db.Date, nullable=False)
    lot_number = db.Column(db.String(100))
    notes = db.Column(db.Text)
    added_date = db.Column(db.DateTime, default=db.func.current_timestamp())
```

### Methods
- `days_until_expiration()`: Returns the number of days until expiration (negative if expired)
- `is_expired()`: Returns True if the EpiPen has expired
- `needs_reminder(days_threshold=30)`: Returns True if the EpiPen will expire within the threshold

### Routes
- `GET /epipens`: View all EpiPens
- `POST /epipens/add`: Add a new EpiPen
- `POST /epipens/edit/<id>`: Update an existing EpiPen
- `POST /epipens/delete/<id>`: Delete an EpiPen

## Safety Information

The EpiPen management page includes important safety information:
- EpiPens should be replaced before their expiration date
- Store at room temperature (59°F to 86°F or 15°C to 30°C)
- Avoid extreme heat or cold
- Check the solution regularly - it should be clear and colorless
- Always carry your EpiPen if you have severe allergies
- In case of emergency, call 911 immediately after using an EpiPen

## Testing

Run the EpiPen test suite:
```bash
python test_epipen.py
```

The test suite covers:
- EpiPen creation and database persistence
- Expiration detection logic
- Categorization (expired, expiring soon, current)
- CRUD operations (Create, Read, Update, Delete)
- Days until expiration calculation
- Reminder threshold logic

## Future Enhancements

Potential improvements for future versions:
- Email/SMS reminders for expiring EpiPens
- Multiple reminder thresholds (60 days, 30 days, 7 days)
- QR code generation for quick access to EpiPen information
- Integration with emergency services
- Export EpiPen information as PDF
- Calendar integration for expiration reminders

## Support

For issues or questions about the EpiPen feature, please refer to:
- User documentation in README.md
- Test file: test_epipen.py
- Code implementation: app.py (EpiPen model and routes)
- Templates: templates/epipens.html, templates/dashboard.html

---

**Note**: This is a tracking and reminder tool. It does not replace medical advice. Always consult with healthcare professionals about proper EpiPen usage and storage.
