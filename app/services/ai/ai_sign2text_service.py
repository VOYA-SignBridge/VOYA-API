# import os
# import json
# import numpy as np
# import tensorflow as tf

# CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# MODEL_PATH = os.path.normpath(os.path.join(CURRENT_DIR, "..", "..", "ai", "best_model_Simple_LSTM.h5"))
# LABELS_PATH = os.path.normpath(os.path.join(CURRENT_DIR, "..", "..", "ai", "sign2text_labels.json"))

# print("🔍 MODEL PATH =", MODEL_PATH)
# print("🔍 LABEL PATH =", LABELS_PATH)

# _SIGN2TEXT_MODEL: tf.keras.Model | None = None


# def load_sign2text_model():
#     try:
#         model = tf.keras.models.load_model(MODEL_PATH, compile=False)
#         print("✅ Sign2Text model loaded:", MODEL_PATH)
#         print("➡ Input shape:", model.input_shape)
#         print("➡ Output shape:", model.output_shape)
#         return model
#     except Exception as e:
#         print("❌ Failed to load Sign2Text model:", e)
#         return None


# def get_sign2text_model():
#     global _SIGN2TEXT_MODEL
#     if _SIGN2TEXT_MODEL is None:
#         _SIGN2TEXT_MODEL = load_sign2text_model()
#     return _SIGN2TEXT_MODEL


# # Labels
# if os.path.exists(LABELS_PATH):
#     with open(LABELS_PATH, "r", encoding="utf-8") as f:
#         LABELS = json.load(f)
#     print("✅ Labels loaded:", LABELS)
# else:
#     LABELS = {"0": "Hello", "1": "Thank you"}
#     print("⚠ No labels found → using fallback:", LABELS)


# def predict_sign2text(frames):
#     model = get_sign2text_model()
#     if model is None:
#         return {"error": "Model not loaded"}

#     try:
#         arr = np.array(frames, dtype=np.float32)
#         # TODO: reshape/normalize đúng như lúc train
#         arr = np.expand_dims(arr, axis=0)  # [1, T, D] chẳng hạn
#         preds = model(arr)
#         probs = tf.nn.softmax(preds, axis=-1).numpy()[0]
#         idx = int(np.argmax(probs))
#         label = LABELS.get(str(idx), f"class_{idx}")
#         conf = float(probs[idx])
#         return {"label": label, "confidence": round(conf, 4)}
#     except Exception as e:
#         return {"error": str(e)}
