from __future__ import annotations
import json
from pathlib import Path
from typing import List, Tuple

import torch
import torch.nn.functional as F

from .tcn_classifier import TCNClassifier
import pathlib   # 👈 thêm dòng này

# đường dẫn tới checkpoint và json nhãn
CKPT_PATH = Path("app/ai/tcn_classifier.pt")
LABELS_PATH = Path("app/ai/tcn_labels.json")  


def load_id2label(path: Path):
    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    return {int(k): v for k, v in raw.items()}


ID2LABEL = load_id2label(LABELS_PATH)


def load_tcn_from_ckpt(device: str | None = None) -> TCNClassifier:
    """Load TCN checkpoint được train trên Windows nhưng chạy trên Linux."""
    device = device or ("cuda" if torch.cuda.is_available() else "cpu")

    # 👇 Trick: map WindowsPath -> PosixPath khi unpickle checkpoint
    has_windows_path = hasattr(pathlib, "WindowsPath")
    if has_windows_path:
        old_windows_path = pathlib.WindowsPath
        pathlib.WindowsPath = pathlib.PosixPath

    try:
        ckpt = torch.load(str(CKPT_PATH), map_location=device)
    finally:
        # trả lại class gốc để tránh side-effect về sau
        if has_windows_path:
            pathlib.WindowsPath = old_windows_path

    in_dim: int = ckpt["in_dim"]
    num_classes: int = ckpt["num_classes"]
    cfg: dict = ckpt["config"]

    model = TCNClassifier(
        in_dim=in_dim,
        num_classes=num_classes,
        channels=cfg["channels"],
        levels=cfg["levels"],
        kernel_size=cfg["kernel_size"],
        dropout=cfg["dropout"],
    )
    model.load_state_dict(ckpt["model_state"])
    model.to(device)
    model.eval()

    return model


DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# 👇 lazy-load model, tránh crash khi import module
_TCN_MODEL: TCNClassifier | None = None


def get_tcn_model() -> TCNClassifier:
    global _TCN_MODEL
    if _TCN_MODEL is None:
        _TCN_MODEL = load_tcn_from_ckpt(DEVICE)
    return _TCN_MODEL



@torch.no_grad()
def predict_sign(frames: List[List[float]]) -> Tuple[str, float, List[float]]:
    if not frames:
        raise ValueError("Empty sequence")

    model = get_tcn_model()   # 👈 dùng model lazy-load

    x = torch.tensor(frames, dtype=torch.float32, device=DEVICE)  # [T, D]
    T_len, _ = x.shape

    x = x.unsqueeze(0)  # [1, T, D]
    lengths = torch.tensor([T_len], dtype=torch.long, device=DEVICE)

    logits = model(x, lengths)           # [1, num_classes]
    probs = F.softmax(logits, dim=-1)[0] # [num_classes]

    cls_id = int(torch.argmax(probs).item())
    prob = float(probs[cls_id].item())
    label = ID2LABEL.get(cls_id, str(cls_id))

    return label, prob, probs.tolist()
