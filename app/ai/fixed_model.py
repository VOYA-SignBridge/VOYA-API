import tensorflow as tf
import h5py
import os

OLD_PATH = "app/ai/best_model_Simple_LSTM.h5"
NEW_PATH = "app/ai/best_model_Simple_LSTM_2class_fixed.h5"

print("🚀 Fixing 2-class LSTM model for TF 2.15+\n")

# ===== 1️⃣ Rebuild architecture (identical to old) =====
print("🧱 Rebuilding architecture manually...")
model = tf.keras.Sequential([
    tf.keras.layers.Input(shape=(60, 226), name="input_layer"),
    tf.keras.layers.LSTM(32, name="lstm"),
    tf.keras.layers.Dropout(0.5, name="dropout"),
    tf.keras.layers.Dense(16, activation='relu', name="dense"),
    tf.keras.layers.Dropout(0.3, name="dropout_1"),
    tf.keras.layers.Dense(2, activation='softmax', name="dense_1")
])
print("✅ Architecture built successfully")

# ===== 2️⃣ Helper: recursively extract datasets =====
def extract_datasets(group):
    """Đệ quy đọc toàn bộ dataset trong group"""
    weights = []
    def recurse(g):
        for key, item in g.items():
            if isinstance(item, h5py.Dataset):
                weights.append(item[()])
            elif isinstance(item, h5py.Group):
                recurse(item)
    recurse(group)
    return weights

# ===== 3️⃣ Load weights from old .h5 =====
print("\n📥 Loading weights from old file...")
with h5py.File(OLD_PATH, 'r') as f:
    if "model_weights" not in f:
        raise ValueError("❌ 'model_weights' not found in old file.")
    
    groups = list(f["model_weights"].keys())
    print("📦 Available groups:", groups)

    for layer in model.layers:
        lname = layer.name
        if lname in f["model_weights"]:
            g = f["model_weights"][lname]
            weights = extract_datasets(g)
            if weights:
                try:
                    layer.set_weights(weights)
                    print(f"✅ Weights loaded for layer: {lname} ({len(weights)} tensors)")
                except Exception as e:
                    print(f"⚠️ Shape mismatch at {lname}: {e}")
            else:
                print(f"⚠️ No datasets found for layer: {lname}")
        else:
            print(f"⚠️ No weights found for layer: {lname}")

# ===== 4️⃣ Save new compatible model =====
os.makedirs(os.path.dirname(NEW_PATH), exist_ok=True)
model.save(NEW_PATH)
print(f"\n💾 Model saved successfully → {NEW_PATH}")
