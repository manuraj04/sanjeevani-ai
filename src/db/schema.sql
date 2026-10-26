-- Sanjeevani Scan Knowledge Base Schema

CREATE TABLE IF NOT EXISTS plants (
    plant_id INTEGER PRIMARY KEY AUTOINCREMENT,
    species_name TEXT NOT NULL UNIQUE,
    botanical_name TEXT NOT NULL,
    common_name TEXT,
    common_names_json TEXT,
    family TEXT,
    region TEXT,
    habitat TEXT
);

CREATE TABLE IF NOT EXISTS ayurvedic_profile (
    profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
    plant_id INTEGER NOT NULL UNIQUE,
    dosha_effect TEXT,
    rasa TEXT,
    guna TEXT,
    virya TEXT,
    vipaka TEXT,
    prabhava TEXT,
    FOREIGN KEY(plant_id) REFERENCES plants(plant_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS therapeutic_uses (
    use_id INTEGER PRIMARY KEY AUTOINCREMENT,
    plant_id INTEGER NOT NULL,
    condition TEXT NOT NULL,
    use_description TEXT,
    classical_reference TEXT,
    FOREIGN KEY(plant_id) REFERENCES plants(plant_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS phytochemicals (
    phytochemical_id INTEGER PRIMARY KEY AUTOINCREMENT,
    plant_id INTEGER NOT NULL,
    compound_name TEXT NOT NULL,
    compound_class TEXT,
    pubchem_id TEXT,
    activity TEXT,
    FOREIGN KEY(plant_id) REFERENCES plants(plant_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS contraindications (
    contraindication_id INTEGER PRIMARY KEY AUTOINCREMENT,
    plant_id INTEGER NOT NULL,
    condition TEXT NOT NULL,
    severity TEXT,
    notes TEXT,
    FOREIGN KEY(plant_id) REFERENCES plants(plant_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS plant_images (
    image_id INTEGER PRIMARY KEY AUTOINCREMENT,
    plant_id INTEGER NOT NULL,
    image_path TEXT NOT NULL,
    source TEXT,
    split TEXT,
    verified BOOLEAN DEFAULT 0,
    FOREIGN KEY(plant_id) REFERENCES plants(plant_id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_plants_species ON plants(species_name);
CREATE INDEX IF NOT EXISTS idx_plants_common ON plants(common_name);
CREATE INDEX IF NOT EXISTS idx_therapeutic_condition ON therapeutic_uses(condition);
CREATE INDEX IF NOT EXISTS idx_phytochemicals_compound ON phytochemicals(compound_name);
CREATE INDEX IF NOT EXISTS idx_images_plant_id ON plant_images(plant_id);
