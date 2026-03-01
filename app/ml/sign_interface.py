from __future__ import annotations
import json
from pathlib import Path
from typing import List, Tuple
import os
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
    """Load TCN checkpoint bất kể train trên Windows hay Linux."""
    device = device or ("cuda" if torch.cuda.is_available() else "cpu")

    # Lưu lại class gốc để restore
    orig_windows_path = pathlib.WindowsPath
    orig_posix_path = pathlib.PosixPath

    try:
        if os.name == "nt":
            # 🟢 ĐANG CHẠY TRÊN WINDOWS
            # Nếu checkpoint được save trên Linux → trong pickle có PosixPath
            # → map PosixPath sang WindowsPath để unpickle được
            pathlib.PosixPath = pathlib.WindowsPath  # type: ignore
        else:
            # 🟢 ĐANG CHẠY TRÊN LINUX/MAC
            # Nếu checkpoint được save trên Windows → trong pickle có WindowsPath
            # → map WindowsPath sang PosixPath
            pathlib.WindowsPath = pathlib.PosixPath  # type: ignore

        ckpt = torch.load(str(CKPT_PATH), map_location=device)

    finally:
        # Restore lại tránh side-effect cho chỗ khác
        pathlib.WindowsPath = orig_windows_path
        pathlib.PosixPath = orig_posix_path

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
