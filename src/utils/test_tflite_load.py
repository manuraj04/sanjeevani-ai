import tensorflow as tf

def main():
    model_path = r"d:\Sanjeevani Scan AI\data\processed\sanjeevani_quantized.tflite"
    print("Loading TFLite model...")
    # Try normal interpreter loading, which might automatically load FlexOps
    interpreter = tf.lite.Interpreter(model_path=model_path)
    # Actually BUILTIN_WITHOUT_DEFAULT_DELEGATES might remove Flex. Let's just try normal first.
    # We will see if it fails.
    interpreter.allocate_tensors()
    print("Input:", interpreter.get_input_details()[0]['shape'])

if __name__ == "__main__":
    main()
