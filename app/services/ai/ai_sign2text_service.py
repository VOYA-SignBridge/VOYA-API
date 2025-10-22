import os
import json
import numpy as np
import tensorflow as tf

MODEL_PATH = os.path.join("app", "ai", "best_model_Simple_LSTM_2class_fixed.h5")
LABELS_PATH = os.path.join("app", "ai", "labels_sign2text.json")

# ====== Load Model ======
def load_model():
    try:
        model = tf.keras.models.load_model(MODEL_PATH, compile=False)
        print(f"✅ Loaded sign2text model: {MODEL_PATH}")
        return model
    except Exception as e:
        print(f"❌ Failed to load sign2text model: {e}")
        return None

model = load_model()

# ====== Load Labels ======
if os.path.exists(LABELS_PATH):
    with open(LABELS_PATH, "r", encoding="utf-8") as f:
        labels = json.load(f)
else:
    labels = {"class_0001": "xin chào", "class_0002": "cảm ơn"}
    print("⚠️ Using fallback labels for sign2text")

# ====== Prediction ======
def predict_sign2text(frames: list[list[float]]):
    if model is None:
        return {"error": "Model not loaded"}

    try:
        if len(frames) != 60:
            raise ValueError(f"Expected 60 frames, got {len(frames)}")
        if len(frames[0]) != 226:
            raise ValueError(f"Expected 226 features per frame, got {len(frames[0])}")

        data = np.array(frames, dtype=np.float32).reshape(1, 60, 226)
        preds = model.predict(data, verbose=0)
        idx = int(np.argmax(preds))
        conf = float(np.max(preds))
        label_key = f"class_{idx+1:04d}"

        return {
            "label": labels.get(label_key, f"Class {idx}"),
            "confidence": round(conf, 4),
        }
    except Exception as e:
        return {"error": str(e)}
