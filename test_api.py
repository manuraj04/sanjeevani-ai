import requests
import os
import base64
import json

API_URL = "http://localhost:8000"
IMAGE_PATH = r"d:\Sanjeevani Scan AI\data\processed\test\Neem\inat_101080370.jpg"

def test_predict():
    print(f"\n--- Testing /predict with {os.path.basename(IMAGE_PATH)} ---")
    with open(IMAGE_PATH, "rb") as f:
        files = {"file": (os.path.basename(IMAGE_PATH), f, "image/jpeg")}
        response = requests.post(f"{API_URL}/predict", files=files)
        
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2))
    else:
        print("Error:", response.text)

def test_explain():
    print(f"\n--- Testing /explain with {os.path.basename(IMAGE_PATH)} ---")
    with open(IMAGE_PATH, "rb") as f:
        files = {"file": (os.path.basename(IMAGE_PATH), f, "image/jpeg")}
        response = requests.post(f"{API_URL}/explain", files=files)
        
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Status: {data.get('status')}")
        
        base64_str = data.get("heatmap_base64")
        if base64_str:
            output_path = "gradcam_output.jpg"
            with open(output_path, "wb") as out_f:
                out_f.write(base64.b64decode(base64_str))
            print(f"Successfully saved Grad-CAM heatmap to: {output_path}")
    else:
        print("Error:", response.text)

if __name__ == "__main__":
    if not os.path.exists(IMAGE_PATH):
        print(f"Image not found at {IMAGE_PATH}")
    else:
        test_predict()
        test_explain()
