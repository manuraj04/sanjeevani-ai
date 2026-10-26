import numpy as np
import shutil
import os

import numpy as np
import onnx2tf.onnx2tf

# Mock download_test_image_data in the exact module it is used
def mock_download_test_image_data():
    return np.random.rand(1, 3, 224, 224).astype(np.float32)
onnx2tf.onnx2tf.download_test_image_data = mock_download_test_image_data

from onnx2tf import convert

def main():
    print("Running onnx2tf conversion with static ONNX model...")
    convert(
        input_onnx_file_path=r"d:\Sanjeevani Scan AI\data\processed\sanjeevani.onnx",
        output_folder_path=r"d:\Sanjeevani Scan AI\data\processed\saved_model_static",
        output_dynamic_range_quantized_tflite=True,
        replace_to_pseudo_operators=['GeLU', 'Erf'],
    )
    
    # Copy the resulting float32 or dynamic range tflite to our target path
    src = r"d:\Sanjeevani Scan AI\data\processed\saved_model_static\sanjeevani_dynamic_range_quant.tflite"
    dst = r"d:\Sanjeevani Scan AI\data\processed\sanjeevani_quantized.tflite"
    
    if os.path.exists(src):
        shutil.copy2(src, dst)
        print(f"Quantized model generated: {dst}")
        print(f"File size: {os.path.getsize(dst) / (1024*1024):.2f} MB")
    else:
        print(f"Error: Could not find output {src}")
    
    print("Conversion finished.")

if __name__ == "__main__":
    main()
