from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import os
import tempfile
import json
from pydantic import BaseModel

# Import our custom modules
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, project_root)

from src.inference import SanjeevaniClassifier
from src.api.explainability import GradCamGenerator
from src.api.semantic_search import SemanticSearchEngine

app = FastAPI(title="Sanjeevani Scan AI API", version="1.0.0")

# CORS for mobile/web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modern Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Server"] = "Protected-AI-Gateway"
    return response

# Global instances (lazy loaded on startup)
classifier = None
grad_cam = None
search_engine = None
db_path = os.path.join(project_root, "data", "processed", "sanjeevani_kb.db")
model_path = os.path.join(project_root, "data", "processed", "best_model_final.pth")

@app.on_event("startup")
async def startup_event():
    global classifier, grad_cam, search_engine
    print("Starting up Sanjeevani API...")
    
    # We initialize the classifier with our OOD logic parameters
    classifier = SanjeevaniClassifier(model_path=model_path, num_classes=66, confidence_threshold=0.20)
    
    # Initialize Grad-CAM with the loaded model
    grad_cam = GradCamGenerator(model=classifier.model)
    
    # Initialize Semantic Search Engine
    search_engine = SemanticSearchEngine(db_path)

def get_db():
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# Comprehensive mapping of all 66 model classes to botanical species
CLASS_TO_SPECIES = {
    # Aliases
    "HolyBasilVana": "Ocimum tenuiflorum",
    "Amruth": "Tinospora cordifolia",
    "Bringaraj": "Eclipta prostrata",
    "AloeVera": "Aloe barbadensis",
    # Standard class to botanical species
    "Neem": "Azadirachta indica",
    "Tulsi": "Ocimum tenuiflorum",
    "Ashwagandha": "Withania somnifera",
    "Brahmi": "Bacopa monnieri",
    "Turmeric": "Curcuma longa",
    "Amla": "Phyllanthus emblica",
    "Giloy": "Tinospora cordifolia",
    "Shatavari": "Asparagus racemosus",
    "Ginger": "Zingiber officinale",
    "Aparajita": "Clitoria ternatea",
    "Jamun": "Syzygium cumini",
    "Moringa": "Moringa oleifera",
    "Bael": "Aegle marmelos",
    "Adulsa": "Justicia adhatoda",
    "Bhringraj": "Eclipta prostrata",
    "Agathi": "Sesbania grandiflora",
    "Arjuna": "Terminalia arjuna",
    "Banyan": "Ficus benghalensis",
    "Betel": "Piper betle",
    "BetelNut": "Areca catechu",
    "BlackPepper": "Piper nigrum",
    "Castor": "Ricinus communis",
    "Chamomile": "Matricaria chamomilla",
    "Chitraka": "Plumbago zeylanica",
    "Clove": "Syzygium aromaticum",
    "Coriander": "Coriandrum sativum",
    "CurryLeaf": "Murraya koenigii",
    "Devadaru": "Cedrus deodara",
    "Fenugreek": "Trigonella foenum-graecum",
    "GotoKola": "Centella asiatica",
    "Guava": "Psidium guajava",
    "Gudmar": "Gymnema sylvestre",
    "Haritaki": "Terminalia chebula",
    "Hibiscus": "Hibiscus rosa-sinensis",
    "IndianBeech": "Pongamia pinnata",
    "IndianSarsaparilla": "Hemidesmus indicus",
    "InsulinPlant": "Costus igneus",
    "Kalmegh": "Andrographis paniculata",
    "Kanchnaar": "Bauhinia variegata",
    "Karela": "Momordica charantia",
    "Karpuravalli": "Plectranthus amboinicus",
    "Kutaja": "Holarrhena antidysenterica",
    "Lemon": "Citrus limon",
    "Lemongrass": "Cymbopogon citratus",
    "LongPepper": "Piper longum",
    "Mint": "Mentha spicata",
    "Mulethi": "Glycyrrhiza glabra",
    "Nirgundi": "Vitex negundo",
    "Palash": "Butea monosperma",
    "Papaya": "Carica papaya",
    "Patharchatta": "Bryophyllum pinnatum",
    "Peepal": "Ficus religiosa",
    "Pomegranate": "Punica granatum",
    "Punarnava": "Boerhavia diffusa",
    "Sarpagandha": "Rauvolfia serpentina",
    "Sesame": "Sesamum indicum",
    "Shyonaka": "Oroxylum indicum",
    "SnakePlant": "Dracaena trifasciata",
    "Vacha": "Acorus calamus",
    "Vetiver": "Chrysopogon zizanioides",
    "Vibhitaki": "Terminalia bellirica",
    "Yashad": "Yashada Mineralia",
}

@app.get("/")
def read_root():
    return {"message": "Welcome to Sanjeevani Scan AI API"}

@app.post("/predict")
async def predict_image(file: UploadFile = File(...)):
    """Classifies a leaf image and rejects non-plants."""
    if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG and PNG allowed.")
        
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_path = temp_file.name

    try:
        # Load class names dynamically from the test directory structure
        class_names = sorted(os.listdir(os.path.join(project_root, "data", "processed", "test")))
        result = classifier.predict(temp_path, class_names=class_names)
        
        if result.get("status") == "success":
            predicted_class = result["prediction"]
            species = CLASS_TO_SPECIES.get(predicted_class, predicted_class)
            
            result["plant_id"] = None
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT plant_id, common_name, common_names_json FROM plants WHERE species_name = ? OR common_name = ? OR common_name LIKE ?",
                (species, predicted_class, f"%{predicted_class}%")
            )
            row = cursor.fetchone()
            if row:
                result["plant_id"] = row["plant_id"]
                result["common_name"] = row["common_name"]
                if row["common_names_json"]:
                    try:
                        result["common_names"] = json.loads(row["common_names_json"])
                    except:
                        result["common_names"] = {}
            conn.close()

    finally:
        os.remove(temp_path)
        
    return result

@app.post("/explain")
async def explain_prediction(file: UploadFile = File(...)):
    """Returns a Grad-CAM heatmap base64 string for the image."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_path = temp_file.name

    try:
        base64_img = grad_cam.generate_heatmap_base64(temp_path)
        if not base64_img:
            raise HTTPException(status_code=500, detail="Failed to generate Grad-CAM heatmap.")
    finally:
        os.remove(temp_path)
        
    return {"status": "success", "heatmap_base64": base64_img}

@app.get("/plant/{plant_id}")
def get_plant_profile(plant_id: int):
    """Retrieves the full Ayurvedic knowledge profile for a plant."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get basic info
    cursor.execute("SELECT * FROM plants WHERE plant_id = ?", (plant_id,))
    plant = cursor.fetchone()
    if not plant:
        conn.close()
        raise HTTPException(status_code=404, detail="Plant not found")
        
    # Get profile
    cursor.execute("SELECT * FROM ayurvedic_profile WHERE plant_id = ?", (plant_id,))
    profile = cursor.fetchone()
    
    # Get uses
    cursor.execute("SELECT condition, use_description, classical_reference FROM therapeutic_uses WHERE plant_id = ?", (plant_id,))
    uses = cursor.fetchall()
    
    # Get phytochemicals
    cursor.execute("SELECT compound_name, activity FROM phytochemicals WHERE plant_id = ?", (plant_id,))
    phytochemicals = cursor.fetchall()
    
    # Get contraindications
    cursor.execute("SELECT condition, severity, notes FROM contraindications WHERE plant_id = ?", (plant_id,))
    contraindications = cursor.fetchall()
    
    conn.close()
    
    plant_dict = dict(plant)
    if plant_dict.get("common_names_json"):
        try:
            plant_dict["common_names"] = json.loads(plant_dict["common_names_json"])
        except:
            plant_dict["common_names"] = {}

    profile_dict = dict(profile) if profile else None
    
    return {
        "plant": plant_dict,
        "ayurvedic_profile": profile_dict,
        "profile": profile_dict,
        "therapeutic_uses": [dict(u) for u in uses],
        "phytochemicals": [dict(p) for p in phytochemicals],
        "contraindications": [dict(c) for c in contraindications]
    }

@app.get("/plants")
async def get_all_plants(lang: str = "en"):
    """Returns all plants in library with localized common names."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT plant_id, species_name, botanical_name, common_name, common_names_json, family FROM plants ORDER BY species_name ASC")
    plants = cursor.fetchall()
    conn.close()
    
    result = []
    for p in plants:
        common_json = {}
        if p["common_names_json"]:
            try:
                common_json = json.loads(p["common_names_json"])
            except:
                pass
        localized_common = common_json.get(lang) or p["common_name"] or p["species_name"]
        result.append({
            "plant_id": p["plant_id"],
            "species_name": p["species_name"],
            "botanical_name": p["botanical_name"],
            "common_names": localized_common,
            "common_names_dict": common_json,
            "family": p["family"]
        })
    return result

@app.get("/search")
def search_symptoms(query: str = Query(..., min_length=2)):
    """Semantic search to find plants based on symptoms or conditions."""
    results = []
    if search_engine:
        raw_results = search_engine.search(query, top_k=5)
        conn = get_db()
        cursor = conn.cursor()
        for r in raw_results:
            pid = r.get("plant_id")
            if pid:
                cursor.execute("SELECT * FROM plants WHERE plant_id = ?", (pid,))
                prow = cursor.fetchone()
                if prow:
                    plant_dict = dict(prow)
                    if plant_dict.get("common_names_json"):
                        try:
                            plant_dict["common_names"] = json.loads(plant_dict["common_names_json"])
                        except:
                            plant_dict["common_names"] = {}
                    cursor.execute("SELECT use_description FROM therapeutic_uses WHERE plant_id = ? AND condition = ?", (pid, r.get("condition_matched", "")))
                    use_row = cursor.fetchone()
                    results.append({
                        "plant": plant_dict,
                        "condition": r.get("condition_matched", ""),
                        "use_description": use_row["use_description"] if use_row else "Therapeutic herbal application",
                        "similarity_score": r.get("similarity_score", 0.0)
                    })
        conn.close()
    return {"query": query, "results": results}

if __name__ == "__main__":
    import uvicorn
    # Make sure to run this script from the project root or adjust paths accordingly
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
