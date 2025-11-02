import os
import json
import numpy as np
import tensorflow as tf

# =========================
# 🔧 ĐƯỜNG DẪN MODEL & LABELS
# =========================
MODEL_PATH = os.path.join("app", "ai", "best_model_Simple_LSTM.h5")
LABELS_PATH = os.path.join("app", "ai", "labels_sign2text.json")

# =========================
# 🧠 HÀM LOAD MODEL
# =========================
def load_model():
    try:
        model = tf.keras.models.load_model(MODEL_PATH, compile=False)
        print(f"✅ Loaded sign2text model successfully: {MODEL_PATH}")
        print("📊 Model output shape:", model.output_shape)
        return model
    except Exception as e:
        print(f"❌ Failed to load sign2text model: {e}")
        return None

# Load model khi module được import
model = load_model()

# =========================
# 🏷️ LOAD LABELS
# =========================
if os.path.exists(LABELS_PATH):
    with open(LABELS_PATH, "r", encoding="utf-8") as f:
        labels = json.load(f)
    print(f"✅ Loaded labels from {LABELS_PATH}: {labels}")
else:
    labels = {"class_0001": "xin chào", "class_0002": "cảm ơn"}
    print("⚠️ Using fallback labels:", labels)

# =========================
# 🔍 HÀM DỰ ĐOÁN
# =========================
def predict_sign2text(frames: list[list[float]]):
    """
    frames: Danh sách 60 frame, mỗi frame có 226 float (keypoints)
    Trả về nhãn và độ tin cậy
    """
    if model is None:
        return {"error": "Model not loaded"}

    try:
        if len(frames) != 60:
            raise ValueError(f"Expected 60 frames, got {len(frames)}")
        if len(frames[0]) != 226:
            raise ValueError(f"Expected 226 features per frame, got {len(frames[0])}")

        # Chuẩn hóa dữ liệu đầu vào
        data = np.array(frames, dtype=np.float32).reshape(1, 60, 226)

        preds = model.predict(data, verbose=0)
        idx = int(np.argmax(preds))
        conf = float(np.max(preds))
        label_key = f"{idx}" 
        print(f"[DEBUG] Raw prediction probabilities: {preds[0]}")

        result = {
            "label": labels.get(label_key, f"Class {idx}"),
            "confidence": round(conf, 4),
        }

        print(f"[sign2text] ✅ Predict: {result['label']} ({result['confidence']*100:.2f}%)")
        return result

    except Exception as e:
        print(f"[sign2text] ❌ Error during prediction: {e}")
        return {"error": str(e)}


# =========================
# 🧪 TEST CỤC BỘ (CHẠY TRỰC TIẾP)
# =========================
if __name__ == "__main__":
    print("🚀 Testing sign2text model inference...\n")

    # Sinh dữ liệu giả để test
    dummy = np.random.rand(1, 60, 226).astype(np.float32)
    preds = model.predict(dummy)
    print("Predictions:", preds)
    print("Predicted class:", np.argmax(preds))

    # Gọi thử hàm predict_sign2text()
    frames = np.random.rand(60, 226).tolist()
    result = predict_sign2text(frames)
    print("🧠 Final Prediction:", result)
