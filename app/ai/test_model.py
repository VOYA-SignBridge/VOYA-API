import torch
import torch.nn as nn
import json
import numpy as np
import os

MODEL_PATH = os.path.join("app", "ai", "alphabets_model.pt")
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 🔹 Dự đoán cấu trúc mạng — bạn có thể chỉnh lại nếu nhớ thông số training
class AlphabetLSTM(nn.Module):
    def __init__(self, input_size=226, hidden_size=128, num_layers=2, num_classes=29):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, num_classes)
        self.softmax = nn.Softmax(dim=1)

    def forward(self, x):
        out, _ = self.lstm(x)
        out = out[:, -1, :]  # lấy timestep cuối
        out = self.fc(out)
        return self.softmax(out)

def load_alphabet_model():
    model = AlphabetLSTM()
    try:
        state_dict = torch.load(MODEL_PATH, map_location=DEVICE)
        if isinstance(state_dict, dict):
            model.load_state_dict(state_dict)
            print("✅ Loaded state_dict successfully")
        else:
            print("⚠️ File không phải state_dict, đang cố load trực tiếp...")
            model = state_dict
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
    model.eval()
    return model.to(DEVICE)

model = load_alphabet_model()

# 🔹 Nếu không có label file — tạo mặc định A–Z
LABELS_PATH = os.path.join("app", "ai", "alphabet_labels.json")
if os.path.exists(LABELS_PATH):
    with open(LABELS_PATH, "r", encoding="utf-8") as f:
        labels = json.load(f)
else:
    print("⚠️ No label file found → using default A–Z labels")
    labels = {f"class_{i+1:04d}": chr(65+i) for i in range(26)}  # A–Z fallback

def predict_alphabet(frames: list[list[float]]):
    try:
        data = torch.tensor(frames, dtype=torch.float32).unsqueeze(0).to(DEVICE)
        preds = model(data)
        idx = int(torch.argmax(preds, dim=1))
        conf = float(torch.max(preds))
        return {
            "label": labels.get(f"class_{idx+1:04d}", f"Class {idx}"),
            "confidence": round(conf, 4)
        }
    except Exception as e:
        return {"error": str(e)}
