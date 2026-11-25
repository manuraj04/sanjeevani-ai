import { Asset } from 'expo-asset';
import * as ImageManipulator from 'expo-image-manipulator';
import { Buffer } from 'buffer';
import jpeg from 'jpeg-js';
import { loadTensorflowModel } from 'react-native-fast-tflite';
import { MODEL_CLASS_NAMES, SYNONYM_CLASS_MAP, CLASS_TO_SPECIES_MAP } from '../constants/classNames';

const MODEL_ASSET = require('../assets/sanjeevani_quantized.tflite');
const IMAGENET_MEAN = [0.485, 0.456, 0.406];
const IMAGENET_STD = [0.229, 0.224, 0.225];

let cachedTfliteModel = null;
let modelLoadPromise = null;

/**
 * Loads the bundled quantized INT8 TFLite EfficientNetV2-S model once and caches it in memory.
 * Uses expo-asset downloadAsync() so Android release APKs always resolve a valid file:// URL.
 */
export async function getOfflineVisionModel() {
  if (cachedTfliteModel) {
    return cachedTfliteModel;
  }
  if (!modelLoadPromise) {
    modelLoadPromise = (async () => {
      const asset = Asset.fromModule(MODEL_ASSET);
      if (!asset.localUri) {
        await asset.downloadAsync();
      }
      const modelUrl = asset.localUri || asset.uri;
      const model = await loadTensorflowModel({ url: modelUrl }, []);
      cachedTfliteModel = model;
      return model;
    })().catch((err) => {
      modelLoadPromise = null;
      throw err;
    });
  }
  return modelLoadPromise;
}

/**
 * Resizes and center-crops an image URI to 224x224, then normalizes RGB pixels into Float32Array [1,224,224,3].
 */
async function preprocessImageToTensor(imageUri) {
  // Match Python training/evaluation preprocessing: Resize(256, 256) -> CenterCrop(224, 224)
  const resized = await ImageManipulator.manipulateAsync(
    imageUri,
    [
      { resize: { width: 256, height: 256 } },
      { crop: { originX: 16, originY: 16, width: 224, height: 224 } }
    ],
    { format: ImageManipulator.SaveFormat.JPEG, compress: 1.0, base64: true }
  );

  if (!resized.base64) {
    throw new Error('Failed to encode manipulated image as base64.');
  }

  const rawBytes = Buffer.from(resized.base64, 'base64');
  const decoded = jpeg.decode(rawBytes, { useTArray: true });
  const rgba = decoded.data;

  const expectedPixels = 224 * 224;
  if (decoded.width !== 224 || decoded.height !== 224 || rgba.length < expectedPixels * 4) {
    throw new Error(`Unexpected decoded dimensions: ${decoded.width}x${decoded.height}`);
  }

  const inputFloat = new Float32Array(expectedPixels * 3);
  let outIdx = 0;
  for (let i = 0; i < expectedPixels * 4; i += 4) {
    inputFloat[outIdx++] = (rgba[i] / 255.0 - IMAGENET_MEAN[0]) / IMAGENET_STD[0];
    inputFloat[outIdx++] = (rgba[i + 1] / 255.0 - IMAGENET_MEAN[1]) / IMAGENET_STD[1];
    inputFloat[outIdx++] = (rgba[i + 2] / 255.0 - IMAGENET_MEAN[2]) / IMAGENET_STD[2];
  }
  return inputFloat;
}

function softmax(logits) {
  let maxLogit = -Infinity;
  for (let i = 0; i < logits.length; i++) {
    if (logits[i] > maxLogit) maxLogit = logits[i];
  }
  const exps = new Float32Array(logits.length);
  let sum = 0;
  for (let i = 0; i < logits.length; i++) {
    const e = Math.exp(logits[i] - maxLogit);
    exps[i] = e;
    sum += e;
  }
  for (let i = 0; i < exps.length; i++) {
    exps[i] /= sum;
  }
  return exps;
}

/**
 * Executes genuine on-device TensorFlow Lite leaf classification without internet connectivity.
 */
export async function runOfflineTFLiteInference(imageUri, confidenceThreshold = 0.20) {
  const model = await getOfflineVisionModel();
  const inputFloat = await preprocessImageToTensor(imageUri);

  // NitroModules expects ArrayBuffer[] inputs and returns ArrayBuffer[] outputs
  const inputBuffer = inputFloat.buffer.slice(
    inputFloat.byteOffset,
    inputFloat.byteOffset + inputFloat.byteLength
  );
  const outputs = await model.run([inputBuffer]);
  const logits = new Float32Array(outputs[0]);
  const probs = softmax(logits);

  // Merge synonymous training labels cleanly (e.g. Amruth + Giloy -> Giloy)
  const merged = {};
  for (let i = 0; i < Math.min(probs.length, MODEL_CLASS_NAMES.length); i++) {
    const rawName = MODEL_CLASS_NAMES[i];
    const canonical = SYNONYM_CLASS_MAP[rawName] || rawName;
    merged[canonical] = (merged[canonical] || 0) + probs[i];
  }

  let bestClass = 'Unknown';
  let bestConfidence = 0;
  for (const [cls, prob] of Object.entries(merged)) {
    if (prob > bestConfidence) {
      bestConfidence = prob;
      bestClass = cls;
    }
  }

  if (bestConfidence < confidenceThreshold) {
    return {
      status: 'rejected',
      reason: 'low_confidence',
      message: `On-device edge confidence too low (${(bestConfidence * 100).toFixed(1)}%). Please center a clear medicinal leaf in good lighting.`,
      confidence: String(bestConfidence),
      is_offline_edge: true
    };
  }

  return {
    status: 'success',
    prediction: bestClass,
    common_name: bestClass,
    botanical_name: CLASS_TO_SPECIES_MAP[bestClass] || bestClass,
    confidence: String(bestConfidence),
    is_offline_edge: true,
    engine: 'TensorFlow Lite INT8 (On-Device)'
  };
}
