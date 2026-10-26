import os
import requests
import time
from tqdm import tqdm
from PIL import Image
from io import BytesIO

def download_random_images(output_dir, num_images=100, image_size=(256, 256)):
    """Downloads random non-plant images from picsum.photos for the OOD class."""
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Downloading {num_images} random images to {output_dir}...")
    url = f"https://picsum.photos/{image_size[0]}/{image_size[1]}"
    
    count = 0
    with tqdm(total=num_images) as pbar:
        while count < num_images:
            try:
                # Add a random seed to get different images
                req_url = f"{url}?random={count}"
                response = requests.get(req_url, timeout=5)
                if response.status_code == 200:
                    img = Image.open(BytesIO(response.content))
                    
                    # Basic check to ensure it's a valid RGB image
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                        
                    img_path = os.path.join(output_dir, f"non_plant_{count:04d}.jpg")
                    img.save(img_path)
                    count += 1
                    pbar.update(1)
            except Exception as e:
                print(f"Error downloading image: {e}")
                time.sleep(1)

if __name__ == "__main__":
    project_root = os.path.join(os.path.dirname(__file__), "..", "..")
    
    # Download 200 for train, 50 for val
    train_dir = os.path.join(project_root, "data", "processed", "train", "Non_Plant")
    val_dir = os.path.join(project_root, "data", "processed", "val", "Non_Plant")
    
    download_random_images(train_dir, num_images=200)
    download_random_images(val_dir, num_images=50)
    
    print("\nNon-plant OOD dataset collection complete.")
