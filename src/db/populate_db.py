import sqlite3
import json
import os

def create_connection(db_file):
    """Create a database connection to the SQLite database specified by db_file."""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
    return conn

def execute_sql_file(conn, sql_file):
    """Execute SQL commands from a file."""
    try:
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_commands = f.read()
        conn.executescript(sql_commands)
        print("Schema loaded successfully.")
    except Exception as e:
        print(f"Error executing SQL file: {e}")

def populate_database(conn, data_file):
    """Populate database from JSON data file."""
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            plants_data = json.load(f)
            
        cursor = conn.cursor()
        
        for plant in plants_data:
            # Insert plant
            common_names_dict = plant.get('common_names', {})
            common_name = plant.get('common_name') or common_names_dict.get('en', plant.get('species_name'))
            common_names_json = json.dumps(common_names_dict, ensure_ascii=False) if common_names_dict else None
            
            cursor.execute('''
                INSERT INTO plants(species_name, botanical_name, common_name, common_names_json, family, region, habitat)
                VALUES(?,?,?,?,?,?,?)
            ''', (plant.get('species_name'), plant.get('botanical_name'), common_name, common_names_json, plant.get('family'), plant.get('region'), plant.get('habitat')))
            
            plant_id = cursor.lastrowid
            print(f"Inserted plant: {plant.get('species_name')} ({common_name}) with ID {plant_id}")
            
            # Insert profile
            profile = plant.get('profile', {})
            cursor.execute('''
                INSERT INTO ayurvedic_profile(plant_id, dosha_effect, rasa, guna, virya, vipaka, prabhava)
                VALUES(?,?,?,?,?,?,?)
            ''', (plant_id, profile.get('dosha_effect'), profile.get('rasa'), profile.get('guna'), profile.get('virya'), profile.get('vipaka'), profile.get('prabhava')))
            
            # Insert uses
            for use in plant.get('uses', []):
                cursor.execute('''
                    INSERT INTO therapeutic_uses(plant_id, condition, use_description, classical_reference)
                    VALUES(?,?,?,?)
                ''', (plant_id, use.get('condition'), use.get('use_description'), use.get('classical_reference')))
                
            # Insert phytochemicals
            for phyto in plant.get('phytochemicals', []):
                cursor.execute('''
                    INSERT INTO phytochemicals(plant_id, compound_name, compound_class, pubchem_id, activity)
                    VALUES(?,?,?,?,?)
                ''', (plant_id, phyto.get('compound_name'), phyto.get('compound_class'), phyto.get('pubchem_id'), phyto.get('activity')))
                
            # Insert contraindications
            for contra in plant.get('contraindications', []):
                cursor.execute('''
                    INSERT INTO contraindications(plant_id, condition, severity, notes)
                    VALUES(?,?,?,?)
                ''', (plant_id, contra.get('condition'), contra.get('severity'), contra.get('notes')))
                
        conn.commit()
        print("Database populated successfully.")
        
    except Exception as e:
        print(f"Error populating database: {e}")
        conn.rollback()

if __name__ == '__main__':
    project_root = os.path.join(os.path.dirname(__file__), "..", "..")
    db_path = os.path.join(project_root, "data", "processed", "sanjeevani_kb.db")
    schema_path = os.path.join(project_root, "src", "db", "schema.sql")
    data_path = os.path.join(project_root, "data", "processed", "ayurvedic_knowledge.json")
    
    # Ensure processed directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print("Removed old database file for fresh recreation.")
        except Exception as e:
            print(f"Notice: Could not remove old db file: {e}")
    
    # Connect and process
    conn = create_connection(db_path)
    if conn is not None:
        print("Creating tables...")
        execute_sql_file(conn, schema_path)
        
        print(f"Populating data from {data_path}...")
        populate_database(conn, data_path)
        
        conn.close()
    else:
        print("Error! cannot create the database connection.")
