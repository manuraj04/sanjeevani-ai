import urllib.request
import json
import os
import requests

API_URL = "http://127.0.0.1:8000"

def test_api():
    print("=== DEEP RUN TEST SUITE ===")
    
    # 1. Health check
    print("\n1. Testing Root endpoint...")
    res = requests.get(f"{API_URL}/")
    assert res.status_code == 200, f"Root failed: {res.status_code}"
    print("PASS: Root status OK")

    # 2. Library Plants in English and Hindi
    print("\n2. Testing /plants in English & Hindi...")
    res_en = requests.get(f"{API_URL}/plants?lang=en")
    assert res_en.status_code == 200, f"Plants EN failed: {res_en.status_code}"
    plants_en = res_en.json()
    print(f"PASS: Found {len(plants_en)} plants in EN library. First: {plants_en[0]['species_name']} -> {plants_en[0]['common_names']}")

    res_hi = requests.get(f"{API_URL}/plants?lang=hi")
    assert res_hi.status_code == 200, f"Plants HI failed: {res_hi.status_code}"
    plants_hi = res_hi.json()
    print(f"PASS: Found {len(plants_hi)} plants in HI library.")

    # 3. Plant Profile for Giloy (plant_id 12) and Aloe Vera (plant_id 5)
    print("\n3. Testing /plant/12 (Giloy) & /plant/5 (Aloe Vera)...")
    res_giloy = requests.get(f"{API_URL}/plant/12")
    assert res_giloy.status_code == 200, f"Giloy failed: {res_giloy.status_code}"
    giloy_data = res_giloy.json()
    assert giloy_data.get("ayurvedic_profile") is not None, "Giloy ayurvedic_profile is None"
    assert giloy_data.get("profile") is not None, "Giloy profile alias is None"
    print("PASS: Giloy profile loaded successfully:")
    print("  - Dosha:", giloy_data["ayurvedic_profile"]["dosha_effect"])
    print("  - Rasa:", giloy_data["ayurvedic_profile"]["rasa"])
    print("  - Prabhava:", giloy_data["ayurvedic_profile"]["prabhava"])

    res_aloe = requests.get(f"{API_URL}/plant/5")
    assert res_aloe.status_code == 200, f"Aloe failed: {res_aloe.status_code}"
    aloe_data = res_aloe.json()
    assert aloe_data.get("ayurvedic_profile") is not None, "Aloe ayurvedic_profile is None"
    print("PASS: Aloe Vera profile loaded successfully:")
    print("  - Dosha:", aloe_data["ayurvedic_profile"]["dosha_effect"])
    print("  - Guna:", aloe_data["ayurvedic_profile"]["guna"])

    # 4. Search endpoint
    print("\n4. Testing /search with 'fever'...")
    res_search = requests.get(f"{API_URL}/search?query=fever")
    assert res_search.status_code == 200, f"Search failed: {res_search.status_code}"
    search_data = res_search.json()
    print(f"PASS: Search returned {len(search_data.get('results', []))} results.")
    for r in search_data.get('results', [])[:2]:
        p = r.get('plant', {})
        print(f"  - Matched: {p.get('species_name')} ({p.get('common_name')}) for {r.get('condition')}")

    # 5. Predict and Explain endpoint with a real test leaf image if available
    test_dir = os.path.join("data", "processed", "test")
    if os.path.exists(test_dir):
        # find first image in test folder
        sample_img = None
        for root, dirs, files in os.walk(test_dir):
            for f in files:
                if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                    sample_img = os.path.join(root, f)
                    break
            if sample_img:
                break
        
        if sample_img:
            print(f"\n5. Testing /predict with sample leaf: {sample_img}...")
            with open(sample_img, 'rb') as f:
                res_predict = requests.post(f"{API_URL}/predict", files={"file": ("leaf.jpg", f, "image/jpeg")})
            assert res_predict.status_code == 200, f"Predict failed: {res_predict.status_code}"
            pred_data = res_predict.json()
            print("PASS: Predict result:", pred_data.get("prediction"), "Status:", pred_data.get("status"), "Plant ID:", pred_data.get("plant_id"))

            print("\n6. Testing /explain with sample leaf...")
            with open(sample_img, 'rb') as f:
                res_explain = requests.post(f"{API_URL}/explain", files={"file": ("leaf.jpg", f, "image/jpeg")})
            assert res_explain.status_code == 200, f"Explain failed: {res_explain.status_code}"
            exp_data = res_explain.json()
            assert exp_data.get("heatmap_base64") is not None, "Heatmap missing"
            print("PASS: Grad-CAM heatmap generated successfully (len base64:", len(exp_data["heatmap_base64"]), ")")

    print("\n=== ALL DEEP RUN TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    test_api()
