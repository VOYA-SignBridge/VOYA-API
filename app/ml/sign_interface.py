from __future__ import annotations
import json
from pathlib import Path
from typing import List, Tuple

import torch
import torch.nn.functional as F

from .tcn_classifier import TCNClassifier

# đường dẫn tới checkpoint và json nhãn
CKPT_PATH = Path("app/ai/tcn_classifier.pt")
LABELS_PATH = Path("app/ai/tcn_labels.json")  


def load_id2label(path: Path):
    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    # "0": "abc" -> {0: "abc"}
    return {int(k): v for k, v in raw.items()}


ID2LABEL = load_id2label(LABELS_PATH)


def load_tcn_from_ckpt(device: str | None = None) -> TCNClassifier:
    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    ckpt = torch.load(CKPT_PATH, map_location=device)

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
MODEL = load_tcn_from_ckpt(DEVICE)


@torch.no_grad()
def predict_sign(frames: List[List[float]]) -> Tuple[str, float, List[float]]:
    """
    frames: list length T, mỗi phần tử là vector [D]
    return: (label, prob, probs)
    """
    if not frames:
        raise ValueError("Empty sequence")

    x = torch.tensor(frames, dtype=torch.float32, device=DEVICE)  # [T, D]
    T_len, _ = x.shape

    x = x.unsqueeze(0)  # [1, T, D]
    lengths = torch.tensor([T_len], dtype=torch.long, device=DEVICE)

    logits = MODEL(x, lengths)            # [1, num_classes]
    probs = F.softmax(logits, dim=-1)[0]  # [num_classes]

    cls_id = int(torch.argmax(probs).item())
    prob = float(probs[cls_id].item())
    label = ID2LABEL.get(cls_id, str(cls_id))

    return label, prob, probs.tolist()
