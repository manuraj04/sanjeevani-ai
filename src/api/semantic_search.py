import os
import sqlite3
import numpy as np
try:
    import faiss
    from sentence_transformers import SentenceTransformer
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("Warning: FAISS or sentence-transformers not installed. Semantic search will be mocked.")

class SemanticSearchEngine:
    def __init__(self, db_path):
        self.db_path = db_path
        self.index = None
        self.plant_map = {} # Maps FAISS index ID to Plant Data
        
        if FAISS_AVAILABLE:
            print("Loading sentence transformer model (all-MiniLM-L6-v2)...")
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            self._build_index()
            
    def _get_db_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _build_index(self):
        """Extracts therapeutic uses from DB and builds the FAISS index."""
        print("Building semantic search index from database...")
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        # We join plants with therapeutic uses
        cursor.execute('''
            SELECT p.plant_id, p.species_name, t.condition, t.use_description
            FROM plants p
            JOIN therapeutic_uses t ON p.plant_id = t.plant_id
        ''')
        rows = cursor.fetchall()
        
        if not rows:
            print("No therapeutic uses found in database to index.")
            return

        texts_to_encode = []
        for i, row in enumerate(rows):
            # Combine condition and description into a single text for embedding
            text = f"{row['condition']}: {row['use_description']}"
            texts_to_encode.append(text)
            
            # Store mapping
            self.plant_map[i] = {
                "plant_id": row["plant_id"],
                "species_name": row["species_name"],
                "condition": row["condition"],
                "matched_text": text
            }
            
        print(f"Encoding {len(texts_to_encode)} therapeutic profiles...")
        embeddings = self.model.encode(texts_to_encode, convert_to_numpy=True)
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Create FAISS Index (Inner Product on normalized vectors = Cosine Similarity)
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(embeddings)
        print("FAISS Index built successfully.")
        conn.close()

    def search(self, query, top_k=3):
        """Searches for plants matching the symptom query."""
        if not FAISS_AVAILABLE or self.index is None:
            return [{"error": "Semantic search engine not initialized or dependencies missing."}]
            
        # Encode the query
        query_embedding = self.model.encode([query], convert_to_numpy=True)
        faiss.normalize_L2(query_embedding)
        
        # Search the index
        distances, indices = self.index.search(query_embedding, top_k)
        
        results = []
        for i in range(top_k):
            idx = indices[0][i]
            if idx != -1 and idx in self.plant_map:
                score = float(distances[0][i])
                plant_info = self.plant_map[idx]
                results.append({
                    "plant_id": plant_info["plant_id"],
                    "species_name": plant_info["species_name"],
                    "condition_matched": plant_info["condition"],
                    "similarity_score": score
                })
                
        return results

if __name__ == "__main__":
    project_root = os.path.join(os.path.dirname(__file__), "..", "..")
    db_path = os.path.join(project_root, "data", "processed", "sanjeevani_kb.db")
    
    engine = SemanticSearchEngine(db_path)
    if FAISS_AVAILABLE:
        print("\nTesting Semantic Search:")
        query = "skin rash and itching"
        print(f"Query: '{query}'")
        results = engine.search(query)
        for res in results:
            print(f" - {res['species_name']} (Score: {res['similarity_score']:.2f}) -> {res['condition_matched']}")
