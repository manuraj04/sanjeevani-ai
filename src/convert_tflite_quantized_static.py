import tensorflow as tf

def convert_to_quantized_tflite():
    saved_model_dir = r"d:\Sanjeevani Scan AI\data\processed\saved_model"
    output_path = r"d:\Sanjeevani Scan AI\data\processed\sanjeevani_quantized.tflite"
    
    print(f"Loading SavedModel from {saved_model_dir}")
    model = tf.saved_model.load(saved_model_dir)
    
    # The default signature is usually 'serving_default'
    concrete_func = model.signatures[tf.saved_model.DEFAULT_SERVING_SIGNATURE_DEF_KEY]
    
    # Force the input shape to be static [1, 3, 224, 224] to avoid TFLite quantization MLIR errors
    # Find the input tensor
    input_tensor = concrete_func.inputs[0]
    print(f"Original input shape: {input_tensor.shape}")
    input_tensor.set_shape([1, 224, 224, 3])
    print(f"Static input shape forced to: {input_tensor.shape}")
    
    print("Setting up TFLite Converter with INT8 Dynamic Range Quantization...")
    converter = tf.lite.TFLiteConverter.from_concrete_functions([concrete_func])
    
    # Enable dynamic range quantization (weights to 8-bit precision)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS, tf.lite.OpsSet.SELECT_TF_OPS]
    
    print("Converting model...")
    tflite_quant_model = converter.convert()
    
    print(f"Saving quantized TFLite model to {output_path}")
    with open(output_path, "wb") as f:
        f.write(tflite_quant_model)
        
    print(f"Conversion complete! File size: {len(tflite_quant_model) / (1024*1024):.2f} MB")
    
if __name__ == "__main__":
    convert_to_quantized_tflite()
