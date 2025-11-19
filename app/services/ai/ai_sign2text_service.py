import os
import json
import numpy as np
import tensorflow as tf

#  PATH FIX – absolute path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(CURRENT_DIR, "..", "..", "ai", "best_model_Simple_LSTM.h5")
LABELS_PATH = os.path.join(CURRENT_DIR, "..", "..", "ai", "labels_sign2text.json")

MODEL_PATH = os.path.normpath(MODEL_PATH)
LABELS_PATH = os.path.normpath(LABELS_PATH)

print("🔍 MODEL PATH =", MODEL_PATH)
print("🔍 LABEL PATH =", LABELS_PATH)

#  LOAD MODEL
def load_sign2text_model():
    try:
        model = tf.keras.models.load_model(MODEL_PATH, compile=False)
        print("✅ Model loaded successfully:", MODEL_PATH)
        print("➡ Input shape:", model.input_shape)
        print("➡ Output shape:", model.output_shape)
        return model
    except Exception as e:
        print("❌ Failed to load model:", e)
        return None

model = load_sign2text_model()

#  LOAD LABELS
if os.path.exists(LABELS_PATH):
    with open(LABELS_PATH, "r", encoding="utf-8") as f:
        LABELS = json.load(f)
    print("✅ Labels loaded:", LABELS)
else:
    LABELS = {"0": "Hello", "1": "Thank you"}
    print("⚠ No labels found → using fallback:", LABELS)

#  PREDICT FUNCTION

def predict_sign2text(frames):
    if model is None:
        return {"error": "Model not loaded"}

    # (phần predict giữ nguyên)
