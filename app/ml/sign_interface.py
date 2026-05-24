from __future__ import annotations

import json
import os
import pathlib
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import torch
import torch.nn.functional as F
import numpy as np

from .tcn_classifier import TCNClassifier

APP_DIR = Path(__file__).resolve().parents[1]
AI_DIR = APP_DIR / "ai"
LABELS_DIR = AI_DIR / "label"


@dataclass(frozen=True)
class TCNModelSpec:
    model_key: str
    name: str
    checkpoint_path: Path
    labels_path: Path | None = None


MODEL_REGISTRY: dict[str, TCNModelSpec] = {
    "hoa_de": TCNModelSpec(
        model_key="hoa_de",
        name="Hoa De",
        checkpoint_path=Path(
            os.getenv(
                "TCN_MODEL_HOADE_PATH",
                str(AI_DIR / "tcn_dialect-hoa-de_20260514_214512.pt"),
            )
        ),
        labels_path=Path(
            os.getenv(
                "TCN_LABELS_HOADE_PATH",
                str(LABELS_DIR / "tcn_dialect-hoa-de_labels.json"),
            )
        ),
    ),
}


def register_tcn_model(model_key: str, checkpoint_path: str | Path, labels_path: str | Path | None = None) -> None:
    """Runtime registration hook for future TCN models."""
    MODEL_REGISTRY[model_key] = TCNModelSpec(
        model_key=model_key,
        name=model_key,
        checkpoint_path=Path(checkpoint_path),
        labels_path=Path(labels_path) if labels_path is not None else None,
    )


def load_id2label(path: Path | None) -> dict[int, str]:
    if path is None or not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    if not raw:
        return {}

    _, sample_value = next(iter(raw.items()))
    if isinstance(sample_value, int):
        return {int(v): str(k) for k, v in raw.items()}

    if isinstance(sample_value, dict):
        out: dict[int, str] = {}
        for k, v in raw.items():
            if not isinstance(v, dict):
                continue
            label = (
                v.get("label_original")
                or v.get("label_slug")
                or v.get("label_key")
                or str(k)
            )
            out[int(k)] = str(label)
        return out

    return {int(k): str(v) for k, v in raw.items()}


def normalize_single_hand(hand: np.ndarray) -> np.ndarray:
    """
    Normalize ONE hand independently.

    hand shape: (21, 3)
    """
    h = hand.astype(np.float32).copy()

    # empty hand
    if not np.any(h):
        return h

    # wrist landmark
    wrist = h[0, :2].copy()

    # translate
    h[:, :2] = h[:, :2] - wrist

    # compute scale
    valid = np.linalg.norm(h[:, :2], axis=1) > 1e-6

    if valid.any():
        pts = h[valid, :2]

        span_x = pts[:, 0].max() - pts[:, 0].min()
        span_y = pts[:, 1].max() - pts[:, 1].min()

        scale = max(span_x, span_y)

        if scale > 1e-6:
            h[:, :2] = h[:, :2] / scale

    return h


def normalize_hands_vector_126(vec: np.ndarray) -> np.ndarray:
    if vec is None:
        return vec

    v = np.asarray(vec, dtype=np.float32)

    if v.size != 126:
        return v

    try:
        arr = v.reshape(2, 21, 3).astype(np.float32)
    except Exception:
        return v

    # preserve semantic hand identity
    left = arr[0]
    right = arr[1]

    # normalize independently
    left = normalize_single_hand(left)
    right = normalize_single_hand(right)

    out = np.concatenate(
        [
            left.reshape(-1),
            right.reshape(-1),
        ]
    ).astype(np.float32)

    return out


def preprocess_hands_vector_126(frame: List[float]) -> np.ndarray:
    arr = np.asarray(frame, dtype=np.float32).reshape(-1)
    if arr.size != 126:
        raise ValueError(f"Each frame must have exactly 126 features, got {arr.size}")

    arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
    return normalize_hands_vector_126(arr)


def preprocess_sequence_126(frames: List[List[float]], max_len: int = 60) -> torch.Tensor:
    if not isinstance(frames, list) or not frames:
        raise ValueError("frames must not be empty")

    if len(frames) < 12:
        raise ValueError("At least 12 frames are required for prediction")

    processed = [preprocess_hands_vector_126(frame) for frame in frames[-max_len:]]
    seq = np.stack(processed, axis=0).astype(np.float32)
    return torch.from_numpy(seq)


def _normalize_state_dict(ckpt: dict) -> tuple[dict, dict, int, int, dict[int, str] | None]:
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
    return state_dict, cfg, in_dim, num_classes, id2label


class TCNModelService:
    def __init__(self) -> None:
        self._models: dict[str, TCNClassifier] = {}
        self._id2labels: dict[str, dict[int, str]] = {}

    def resolve_spec(self, model_key: str) -> TCNModelSpec:
        try:
            return MODEL_REGISTRY[model_key]
        except KeyError as exc:
            raise KeyError(f"Unknown TCN model_key: {model_key}") from exc

    def list_models(self) -> list[dict[str, str | bool | None]]:
        items: list[dict[str, str | bool | None]] = []
        for spec in MODEL_REGISTRY.values():
            items.append(
                {
                    "model_key": spec.model_key,
                    "name": spec.name,
                    "checkpoint_path": str(spec.checkpoint_path),
                    "labels_path": str(spec.labels_path) if spec.labels_path else None,
                    "is_loaded": spec.model_key in self._models,
                }
            )
        return items

    def _load_ckpt(self, spec: TCNModelSpec, device: str) -> tuple[TCNClassifier, dict[int, str]]:
        ckpt_path = spec.checkpoint_path
        if not ckpt_path.exists():
            raise FileNotFoundError(f"TCN checkpoint not found: {ckpt_path}")

        orig_windows_path = pathlib.WindowsPath
        orig_posix_path = pathlib.PosixPath
        try:
            if os.name == "nt":
                pathlib.PosixPath = pathlib.WindowsPath  # type: ignore[assignment]
            else:
                pathlib.WindowsPath = pathlib.PosixPath  # type: ignore[assignment]

            ckpt = torch.load(str(ckpt_path), map_location=device, weights_only=False)
        finally:
            pathlib.WindowsPath = orig_windows_path
            pathlib.PosixPath = orig_posix_path

        state_dict, cfg, in_dim, num_classes, id2label = _normalize_state_dict(ckpt)

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

        labels = load_id2label(spec.labels_path)
        if not labels and isinstance(id2label, dict) and id2label:
            labels = {}
            for k, v in id2label.items():
                if isinstance(v, dict):
                    label = v.get("label_original") or v.get("label_slug") or v.get("label_key") or str(k)
                    labels[int(k)] = str(label)
                else:
                    labels[int(k)] = str(v)

        return model, labels

    def get(self, model_key: str, device: str | None = None) -> tuple[TCNClassifier, dict[int, str]]:
        device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        if model_key not in self._models:
            spec = self.resolve_spec(model_key)
            model, labels = self._load_ckpt(spec, device)
            self._models[model_key] = model
            self._id2labels[model_key] = labels
        return self._models[model_key], self._id2labels.get(model_key, {})


TCN_SERVICE = TCNModelService()


@torch.no_grad()
def predict_sign(frames: List[List[float]], model_key: str = "hoa_de") -> Tuple[str, float, List[float]]:
    model, id2label = TCN_SERVICE.get(model_key, DEVICE)
    x = preprocess_sequence_126(frames, max_len=60).to(DEVICE)
    t_len = x.shape[0]

    x = x.unsqueeze(0)
    lengths = torch.tensor([t_len], device=DEVICE)

    logits = model(x, lengths)
    probs = F.softmax(logits, dim=-1)[0]

    cls_id = int(probs.argmax())
    prob = float(probs[cls_id])

    return id2label.get(cls_id, "UNKNOWN"), prob, probs.tolist()


DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
