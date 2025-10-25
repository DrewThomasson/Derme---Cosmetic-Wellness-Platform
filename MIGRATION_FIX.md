# Database Migration Fix

## Problem

Users with existing databases were getting this error when trying to start the app:

```
sqlite3.OperationalError: no such column: known_allergen.where_found
```

This occurred because:
1. The PR added new columns to the `KnownAllergen` model (`where_found`, `product_categories`, `clinician_note`, `url`)
2. SQLAlchemy's `db.create_all()` only creates new tables, it doesn't alter existing tables
3. Users with existing databases had the old schema (4 columns) but the code expected the new schema (8 columns)

## Solution

Added automatic database migration in `app.py`:

### New Function: `migrate_database()`

```python
def migrate_database():
    """Migrate existing database schema to add new columns"""
    try:
        # Check if migration is needed
        try:
            KnownAllergen.query.with_entities(KnownAllergen.where_found).first()
            return  # Migration not needed
        except:
            pass  # Column doesn't exist, need to migrate
        
        print("Migrating database schema...")
        
        # Add new columns using raw SQL
        with db.engine.connect() as conn:
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
            
            conn.commit()
        
        print("Database migration completed successfully")
        
    except Exception as e:
        print(f"Migration note: {str(e)}")
```

### Updated `init_db()`

```python
def init_db():
    with app.app_context():
        db.create_all()
        
        # NEW: Migrate existing database if needed
        migrate_database()
        
        # Load allergens from JSON file
        # ... rest of initialization
```

## How It Works

1. **Detection**: Tries to query a new column (`where_found`)
   - If successful → Migration not needed
   - If fails → Triggers migration

2. **Migration**: Uses raw SQL `ALTER TABLE` statements to add new columns
   - Wrapped in try/except to handle columns that already exist
   - Safe to run multiple times (idempotent)

3. **Preservation**: All existing data is preserved
   - No data loss
   - No need to delete the database

## User Experience

### Before Fix
```bash
$ python app.py
Traceback (most recent call last):
  ...
sqlite3.OperationalError: no such column: known_allergen.where_found
```

### After Fix
```bash
$ python app.py
Migrating database schema...
  Added column: where_found
  Added column: product_categories
  Added column: clinician_note
  Added column: url
Database migration completed successfully
Loading 496 allergens from Contact Dermatitis Institute database...
Successfully loaded 492 new allergens and 14134 synonyms
 * Running on http://0.0.0.0:7860
```

## Testing

Tested with:
1. **Old database (4 columns)** → Successfully migrated to 8 columns ✅
2. **Fresh database** → Works normally ✅
3. **Already migrated database** → Skips migration gracefully ✅

## Benefits

- ✅ No manual intervention required
- ✅ Preserves all existing data
- ✅ Safe to run multiple times
- ✅ Automatic on app startup
- ✅ Clear feedback to user
- ✅ No breaking changes

## Commit

Fixed in commit: `c0b55be` - "Add automatic database migration to handle schema changes for existing databases"
