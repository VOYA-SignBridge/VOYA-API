import os
import json
import torch
import torch.nn as nn
from typing import Any, Dict


MODEL_PATH = os.path.join("app", "ai", "alphabets_model.pt")
LABELS_PATH = os.path.join("app", "ai", "alphabet_labels.json")
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

#  MODEL DEFINITION 
class ParallelCNNLSTMModel(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers, num_classes, per_video_output=True):
        super(ParallelCNNLSTMModel, self).__init__()
        self.cnn = nn.Sequential(
            nn.Conv1d(in_channels=input_size, out_channels=64, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.MaxPool1d(kernel_size=2, stride=2),
            nn.Conv1d(in_channels=64, out_channels=128, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.MaxPool1d(kernel_size=2, stride=2),
            nn.Flatten(),
            nn.LazyLinear(out_features=128),
            nn.ReLU()
        )
        self.lstm = nn.LSTM(input_size=input_size, hidden_size=hidden_size, num_layers=num_layers, batch_first=True)
        self.fc_lstm = nn.Linear(hidden_size, 128)
        self.fc = nn.Linear(128 * 2, num_classes)
        self.per_video_output = per_video_output

    def forward(self, x):
        if x.dim() == 4:
            b, f, s, d = x.shape
            x = x.reshape(b * f, s, d)
            is_video = True
        else:
            is_video = False
        x_cnn = x.permute(0, 2, 1)
        out_cnn = self.cnn(x_cnn)
        out_lstm, _ = self.lstm(x)
        out_lstm = self.fc_lstm(out_lstm[:, -1, :])
        out = torch.cat([out_cnn, out_lstm], dim=1)
        out = self.fc(out)
        if is_video:
            out = out.view(b, f, -1)
            if self.per_video_output:
                out = out.mean(dim=1)
        return out

#  MODEL LOADING
def load_model():
    try:
        # dùng tham số y như khi train
        model = ParallelCNNLSTMModel(input_size=3, hidden_size=128, num_layers=2, num_classes=23)
        state_dict = torch.load(MODEL_PATH, map_location=DEVICE)
        model.load_state_dict(state_dict, strict=True)
        model.eval().to(DEVICE)
        print(f"✅ Loaded alphabet model: {MODEL_PATH}")
        return model
    except Exception as e:
        print(f"❌ Failed to load alphabet model: {e}")
        return None

model = load_model()

# =============================
#  LABELS
# =============================
if os.path.exists(LABELS_PATH):
    with open(LABELS_PATH, "r", encoding="utf-8") as f:
        labels = json.load(f)
else:
    labels = {f"class_{i+1:04d}": chr(65 + i) for i in range(26)}  # A–Z fallback
    print("⚠️ Using fallback alphabet labels")

# =============================
#  PREDICT FUNCTION
# =============================
def predict_alphabet(frames: Any) -> Dict[str, Any]:
    """
    frames: list[list[list[float]]] - mảng (seq_len, 21, 3)
    """
    if model is None:
        return {"error": "Model not loaded"}

    try:
        tensor = torch.tensor(frames, dtype=torch.float32).unsqueeze(0).to(DEVICE)
        with torch.no_grad():
            outputs = model(tensor)
            probs = torch.softmax(outputs, dim=1)
            conf, idx = torch.max(probs, dim=1)
            conf = conf.item()
            idx = idx.item()

        label_key = f"class_{idx+1:04d}"
        return {
            "label": labels.get(label_key, f"Class {idx}"),
            "confidence": round(conf, 4)
        }

    except Exception as e:
        return {"error": str(e)}
