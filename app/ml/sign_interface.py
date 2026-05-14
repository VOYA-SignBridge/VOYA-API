from __future__ import annotations

import json
import os
import pathlib
from pathlib import Path
from typing import List, Tuple

import torch
import torch.nn.functional as F

from .tcn_classifier import TCNClassifier

APP_DIR = Path(__file__).resolve().parents[1]
AI_DIR = APP_DIR / "ai"

# Prefer the user-provided 6-class checkpoint, but fall back to compatible files.
_CKPT_CANDIDATES = [
    Path(os.getenv("TCN_MODEL_PATH", "")) if os.getenv("TCN_MODEL_PATH") else None,
    AI_DIR / "tcn_dialect-hoa-de_20260514_214512.pt",
]
LABELS_PATH = Path(
    os.getenv("TCN_LABELS_PATH", str(AI_DIR / "tcn_dialect-hoa-de_labels.json"))
)


def load_id2label(path: Path) -> dict[int, str]:
    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    if not raw:
        return {}

    _, sample_value = next(iter(raw.items()))
    if isinstance(sample_value, int):
        return {int(v): str(k) for k, v in raw.items()}

    return {int(k): str(v) for k, v in raw.items()}


ID2LABEL = load_id2label(LABELS_PATH)


def resolve_ckpt_path() -> Path:
    for candidate in _CKPT_CANDIDATES:
        if candidate and candidate.exists():
            return candidate
    raise FileNotFoundError(
        "No TCN checkpoint found. Checked: "
        + ", ".join(str(p) for p in _CKPT_CANDIDATES if p is not None)
    )


def load_tcn_from_ckpt(device: str | None = None) -> TCNClassifier:
    """Load the configured TCN checkpoint on Windows or Linux."""
    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    ckpt_path = resolve_ckpt_path()

    orig_windows_path = pathlib.WindowsPath
    orig_posix_path = pathlib.PosixPath

    try:
        if os.name == "nt":
            pathlib.PosixPath = pathlib.WindowsPath  # type: ignore[assignment]
        else:
            pathlib.WindowsPath = pathlib.PosixPath  # type: ignore[assignment]

        ckpt = torch.load(str(ckpt_path), map_location=device)
    finally:
        pathlib.WindowsPath = orig_windows_path
        pathlib.PosixPath = orig_posix_path

    if "model_state_dict" in ckpt:
        state_dict = ckpt["model_state_dict"]
        cfg: dict = ckpt["model_config"]
        in_dim: int = ckpt["feature_dim"]
        num_classes: int = ckpt["num_classes"]
        id2label = ckpt.get("idx_to_label")
    else:
        state_dict = ckpt["model_state"]
        cfg: dict = ckpt["config"]
        in_dim: int = ckpt["in_dim"]
        num_classes: int = ckpt["num_classes"]
        id2label = ckpt.get("idx_to_label")

    model = TCNClassifier(
        in_dim=in_dim,
        num_classes=num_classes,
        channels=cfg["channels"],
        levels=cfg["levels"],
        kernel_size=cfg["kernel_size"],
        dropout=cfg["dropout"],
    )
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()

    # Prefer labels bundled with the checkpoint, otherwise keep the file-based fallback.
    if isinstance(id2label, dict) and id2label:
        global ID2LABEL
        ID2LABEL = {int(k): str(v) for k, v in id2label.items()}

    return model


DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

_TCN_MODEL: TCNClassifier | None = None


def get_tcn_model() -> TCNClassifier:
    global _TCN_MODEL
    if _TCN_MODEL is None:
        _TCN_MODEL = load_tcn_from_ckpt(DEVICE)
    return _TCN_MODEL


@torch.no_grad()
def predict_sign(frames: List[List[float]]) -> Tuple[str, float, List[float]]:
    if len(frames) < 12:
        return "WAITING", 0.0, []

    model = get_tcn_model()
    x = torch.tensor(frames, dtype=torch.float32, device=DEVICE)[-60:]
    t_len = x.shape[0]

    x = x.unsqueeze(0)
    lengths = torch.tensor([t_len], device=DEVICE)

    logits = model(x, lengths)
    probs = F.softmax(logits, dim=-1)[0]

    cls_id = int(probs.argmax())
    prob = float(probs[cls_id])

    return ID2LABEL.get(cls_id, "UNKNOWN"), prob, probs.tolist()
