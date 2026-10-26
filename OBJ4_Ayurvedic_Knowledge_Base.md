# Objective 4 — Ayurvedic Knowledge Base Construction
## Sanjeevani Scan | Medicinal Plant Identification System

> **Goal:** Design and construct a structured, relational Ayurvedic Knowledge Base that links every classified plant species to its medicinal properties, Dosha profile, therapeutic uses, and phytochemicals.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Database Schema Design](#2-database-schema-design)
3. [Data Sources (IMPPAT & TKDL)](#3-data-sources-imppat--tkdl)
4. [Implementation & Population Scripts](#4-implementation--population-scripts)
5. [Symptom-to-Plant Semantic Search](#5-symptom-to-plant-semantic-search)
6. [Progress Tracker](#6-progress-tracker)

---

## 1. Overview

Identifying a plant is only the first step. To make Sanjeevani Scan a complete clinical and educational tool, we must provide context. When the AI model (from Objective 3) classifies a leaf as *Ocimum tenuiflorum* (Tulsi), the application needs to query an offline database to instantly retrieve its Ayurvedic profile.

We chose **SQLite** for this architecture because it is lightweight, requires no background server process, and can be easily bundled directly within a React Native mobile application for 100% offline access.

---

## 2. Database Schema Design

The knowledge base is highly relational, mapped out in `src/db/schema.sql`. It centers around a core `plants` table with one-to-many relationships for complex attributes.

### Core Tables:
- **`plants`**: `plant_id`, `species_name`, `botanical_name`, `family`, `region`, `habitat`.
- **`ayurvedic_profile`**: Links to `plant_id`. Contains `dosha_effect` (Vata/Pitta/Kapha), `rasa` (Taste), `guna` (Properties), `virya` (Potency), `vipaka` (Post-digestive effect), and `prabhava` (Special effect).
- **`therapeutic_uses`**: Links to `plant_id`. Contains the health `condition`, `use_description`, and the `classical_reference` (e.g., Charaka Samhita).
- **`phytochemicals`**: Links to `plant_id`. Tracks `compound_name`, `pubchem_id`, and `activity` (e.g., Anti-inflammatory).
- **`contraindications`**: Links to `plant_id`. Contains safety warnings, `severity`, and `notes` (e.g., avoid during pregnancy).

---

## 3. Data Sources (IMPPAT & TKDL)

The data for this knowledge base is curated from highly reputable, peer-reviewed traditional medicine databases:

1. **IMPPAT (Indian Medicinal Plants, Phytochemistry And Therapeutics)**: We extract the verified phytochemical compounds and their known pharmacological activities.
2. **TKDL (Traditional Knowledge Digital Library)**: Used to cross-reference classical Ayurvedic properties (Dosha, Rasa, Guna) and therapeutic uses to ensure traditional authenticity.

---

## 4. Implementation & Population Scripts

The database construction is managed by a suite of scripts in the `src/db/` directory:

1. **`schema.sql`**: Defines the SQL `CREATE TABLE` statements with strict foreign-key constraints to maintain data integrity.
2. **`extract_imppat.py`**: A data engineering script that formats raw curated data (currently utilizing a mock/bootstrap dataset structure) into a structured JSON format (`mock_ayurvedic_knowledge.json`).
3. **`populate_db.py`**: Connects to the local SQLite database (`data/processed/sanjeevani_kb.db`), drops existing tables, rebuilds the schema, and securely iterates through the JSON file to `INSERT` records.
4. **`validate_db.py`**: Runs sanity checks (e.g., counts total plants, verifies foreign key links, checks for null crucial fields) to ensure the DB is perfectly healthy before we ship it to the mobile app.

---

## 5. Symptom-to-Plant Semantic Search

*Advanced Feature Pipeline*

Because the database uses relational text for `therapeutic_uses`, we plan to implement a reverse-lookup feature in the API/App. 
By generating vector embeddings for the `condition` and `use_description` columns using a Sentence-Transformer model (`all-MiniLM-L6-v2`), users will be able to search for a symptom (e.g., *"dry cough and fever"*) and the system will query the database semantically to return the top 5 Ayurvedic plants best suited for that condition.

---

## 6. Progress Tracker

- [x] Define SQL relational schema (`schema.sql`)
- [x] Create Python extraction script for base data (`extract_imppat.py`)
- [x] Create automated database population script (`populate_db.py`)
- [x] Build validation script to check DB integrity (`validate_db.py`)
- [x] Generate initial bootstrapped SQLite database (`sanjeevani_kb.db`)
- [ ] Expand mock data to full 67-80 species database (Pending Data Entry)
- [ ] Implement Semantic Search Embeddings (Objective 5)

**Next Steps (Objective 5):** System Integration! Connecting the trained TFLite model and this SQLite database into a FastApi Backend and React Native Mobile Application.
