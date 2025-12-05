import sqlite3
import os
from app import app, migrate_database, db

DB_PATH = 'instance/derme.db'

def create_old_schema_db():
    """Creates a database with the old schema (missing columns)"""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
    # Ensure instance dir exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create known_allergen table with OLD schema (missing where_found, etc.)
    cursor.execute('''
        CREATE TABLE known_allergen (
            id INTEGER PRIMARY KEY,
            name VARCHAR(200) NOT NULL UNIQUE,
            category VARCHAR(100),
            description TEXT
        )
    ''')
    
    # Insert some dummy data
    cursor.execute("INSERT INTO known_allergen (name, category, description) VALUES ('TestAllergen', 'TestCat', 'TestDesc')")
    
    conn.commit()
    conn.close()
    print("Created old schema database.")

def verify_columns_exist():
    """Checks if new columns exist in the table"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(known_allergen)")
    columns = [info[1] for info in cursor.fetchall()]
    conn.close()
    
    required_columns = ['where_found', 'product_categories', 'clinician_note', 'url']
    missing = [col for col in required_columns if col not in columns]
    
    if missing:
        print(f"FAILED: Missing columns: {missing}")
        return False
    else:
        print("SUCCESS: All new columns found.")
        return True

def run_test():
    print("=== TC-001: Database Migration Verification ===")
    
    # 1. Setup old DB
    create_old_schema_db()
    
    # 2. Run Migration
    print("Running migration...")
    with app.app_context():
        migrate_database()
    
    # 3. Verify
    if verify_columns_exist():
        print("TC-001 PASSED")
    else:
        print("TC-001 FAILED")
        exit(1)

if __name__ == "__main__":
    run_test()
