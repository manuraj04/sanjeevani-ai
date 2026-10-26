import sqlite3
import os
import sys

def create_connection(db_file):
    """Create a database connection to the SQLite database specified by db_file."""
    try:
        conn = sqlite3.connect(db_file)
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def validate_data(conn):
    """Run validation tests on the database."""
    cursor = conn.cursor()
    errors = []
    
    print("Running validation tests...")
    
    # 1. Check if plants exist
    cursor.execute("SELECT COUNT(*) FROM plants")
    plant_count = cursor.fetchone()[0]
    print(f"Total plants in DB: {plant_count}")
    if plant_count == 0:
        errors.append("Validation Failed: No plants found in database.")
        
    # 2. Check if every plant has a profile
    cursor.execute("""
        SELECT p.species_name 
        FROM plants p 
        LEFT JOIN ayurvedic_profile ap ON p.plant_id = ap.plant_id 
        WHERE ap.profile_id IS NULL
    """)
    missing_profiles = cursor.fetchall()
    if missing_profiles:
        for p in missing_profiles:
            errors.append(f"Validation Failed: Plant '{p[0]}' missing ayurvedic profile.")
            
    # 3. Check for phytochemicals
    cursor.execute("SELECT COUNT(*) FROM phytochemicals")
    phyto_count = cursor.fetchone()[0]
    print(f"Total phytochemicals in DB: {phyto_count}")
    if phyto_count == 0:
        errors.append("Validation Warning: No phytochemicals found in database.")

    # 4. Check for therapeutic uses
    cursor.execute("SELECT COUNT(*) FROM therapeutic_uses")
    uses_count = cursor.fetchone()[0]
    print(f"Total therapeutic uses in DB: {uses_count}")
    if uses_count == 0:
        errors.append("Validation Warning: No therapeutic uses found in database.")

    # Summarize results
    if errors:
        print("\n--- Validation Errors ---")
        for err in errors:
            print(err)
        return False
    else:
        print("\nAll validation tests passed successfully!")
        return True

if __name__ == '__main__':
    project_root = os.path.join(os.path.dirname(__file__), "..", "..")
    db_path = os.path.join(project_root, "data", "processed", "sanjeevani_kb.db")
    
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        sys.exit(1)
        
    conn = create_connection(db_path)
    if conn:
        success = validate_data(conn)
        conn.close()
        if not success:
            sys.exit(1)
    else:
        sys.exit(1)
