import os
import time
import numpy as np
import tensorflow as tf
from PIL import Image
from tqdm import tqdm

def preprocess_image(image_path):
    img = Image.open(image_path).convert('RGB')
    # Resize to 256 then center crop to 224 as per PyTorch transforms
    img = img.resize((256, 256), Image.BILINEAR)
    
    # Center crop
    width, height = img.size
    left = (width - 224) / 2
    top = (height - 224) / 2
    right = (width + 224) / 2
    bottom = (height + 224) / 2
    img = img.crop((left, top, right, bottom))
    
    # Convert to float32 and scale to [0, 1]
    img_array = np.array(img).astype(np.float32) / 255.0
    
    # Normalize with ImageNet mean and std
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    img_array = (img_array - mean) / std
    
    # Add batch dimension -> [1, 224, 224, 3]
    return np.expand_dims(img_array, axis=0)

def main():
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    test_dir = os.path.join(project_root, "data", "processed", "test")
    model_path = os.path.join(project_root, "data", "processed", "sanjeevani_quantized.tflite")
    
    if not os.path.exists(test_dir):
        print(f"Error: Test directory {test_dir} not found.")
        return
        
    print(f"Loading TFLite model: {model_path}")
    interpreter = tf.lite.Interpreter(model_path=model_path)
    interpreter.allocate_tensors()
    
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    input_index = input_details[0]['index']
    output_index = output_details[0]['index']
    
    classes = sorted(os.listdir(test_dir))
    class_to_idx = {cls_name: i for i, cls_name in enumerate(classes)}
    
    total = 0
    correct_top1 = 0
    correct_top5 = 0
    
    start_time = time.time()
    
    for cls_name in tqdm(classes, desc="Evaluating classes"):
        cls_dir = os.path.join(test_dir, cls_name)
        if not os.path.isdir(cls_dir):
            continue
            
        true_idx = class_to_idx[cls_name]
        
        for img_name in os.listdir(cls_dir):
            if not img_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue
                
            img_path = os.path.join(cls_dir, img_name)
            
            try:
                input_data = preprocess_image(img_path)
            except Exception as e:
                print(f"Error reading {img_path}: {e}")
                continue
                
            interpreter.set_tensor(input_index, input_data)
            interpreter.invoke()
            output_data = interpreter.get_tensor(output_index)[0]
            
            # Top-1
            pred_idx = np.argmax(output_data)
            if pred_idx == true_idx:
                correct_top1 += 1
                
            # Top-5
            top5_indices = np.argsort(output_data)[-5:][::-1]
            if true_idx in top5_indices:
                correct_top5 += 1
                
            total += 1
            
    end_time = time.time()
    
    print("\n--- Evaluation Results ---")
    print(f"Total Images: {total}")
    print(f"Top-1 Accuracy: {correct_top1 / total * 100:.2f}%")
    print(f"Top-5 Accuracy: {correct_top5 / total * 100:.2f}%")
    print(f"Average inference time per image (including load): {(end_time - start_time) / total * 1000:.2f} ms")

if __name__ == "__main__":
    main()
