import tensorflow as tf

def convert_to_quantized_tflite():
    saved_model_dir = r"d:\Sanjeevani Scan AI\data\processed\saved_model"
    output_path = r"d:\Sanjeevani Scan AI\data\processed\sanjeevani_quantized.tflite"
    
    print(f"Loading SavedModel from {saved_model_dir}")
    converter = tf.lite.TFLiteConverter.from_saved_model(saved_model_dir)
    
    # We will use post-training dynamic range quantization to reduce size 
    # to < 20MB without needing a representative dataset.
    print("Applying dynamic range quantization...")
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    
    # If we wanted FP16 quantization instead (larger but more precise):
    # converter.target_spec.supported_types = [tf.float16]
    
    print("Converting model...")
    tflite_quant_model = converter.convert()
    
    print(f"Saving quantized TFLite model to {output_path}")
    with open(output_path, "wb") as f:
        f.write(tflite_quant_model)
        
    print("Conversion complete.")
    
if __name__ == "__main__":
    convert_to_quantized_tflite()
