import asyncio
import json
import time
import uuid
from collections import Counter, deque
from typing import Deque

import numpy as np
import torch
import torch.nn.functional as F
from fastapi import APIRouter, Depends, HTTPException, Query, Security, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer
from app.ml.sign_interface import (
    TCN_SERVICE,
    DEVICE,
    normalize_hands_vector_126,
    predict_sign,
    register_tcn_model,
)
# from app.services.ai.ai_sign2text_service import predict_sign2text
from app.services.ai.ai_alphabet_service import predict_alphabet
from app.core.dependencies import verify_supabase_jwt
from app.schemas.ai_schema import (
    Sign2TextInput,
    AlphabetInput,
    SignPredictionResponse,
    SignSequenceRequest,
    TCNModelRegisterRequest,
    TCNModelInfo,
)
from app.core.dependencies import get_current_user
security = HTTPBearer()

router = APIRouter(prefix="/ai", tags=["AI SERVICE"])

STREAM_SESSIONS: dict[str, dict] = {}
STREAM_SESSION_LOCK = asyncio.Lock()
STREAM_MAX_LEN = 60
STREAM_MIN_FRAMES = 12
STREAM_EMA_ALPHA = 0.7
STREAM_VOTE_WINDOW = 5
STREAM_MIN_CONFIDENCE = 0.55
STREAM_CONFIDENCE_THRESHOLD = 0.6
STREAM_STABLE_FRAMES = 3
STREAM_HOLD_FRAMES = 15


def _softmax_np(x: np.ndarray) -> np.ndarray:
    x = x - x.max(axis=-1, keepdims=True)
    e = np.exp(x)
    return e / np.clip(e.sum(axis=-1, keepdims=True), 1e-9, None)


def _init_stream_state(model_key: str, mode: str, session_id: str) -> dict:
    return {
        "session_id": session_id,
        "model_key": model_key,
        "mode": mode,
        "buffer": deque(maxlen=STREAM_MAX_LEN),
        "ema_logits": None,
        "vote_labels": deque(maxlen=STREAM_VOTE_WINDOW),
        "vote_confs": deque(maxlen=STREAM_VOTE_WINDOW),
        "display_label": "",
        "display_conf": 0.0,
        "candidate_label": "",
        "candidate_count": 0,
        "hold_counter": 0,
        "last_commit_label": "",
        "frame_index": 0,
    }


def _is_empty_frame(frame: list[float]) -> bool:
    try:
        arr = np.asarray(frame, dtype=np.float32).reshape(-1)
        return arr.size == 126 and not np.any(arr)
    except Exception:
        return False


async def _send_json_safe(websocket: WebSocket, payload: dict) -> None:
    try:
        await websocket.send_text(json.dumps(payload, ensure_ascii=False))
    except Exception:
        pass


def _run_stream_inference(state: dict) -> tuple[str, float, list[float], bool]:
    model, id2label = TCN_SERVICE.get(state["model_key"], DEVICE)
    buffer = state["buffer"]
    if len(buffer) < STREAM_MIN_FRAMES:
        return "", 0.0, [], False

    seq = np.stack(list(buffer), axis=0).astype(np.float32)
    x = torch.from_numpy(seq).to(DEVICE).unsqueeze(0)
    lengths = torch.tensor([x.shape[1]], device=DEVICE)

    with torch.no_grad():
        logits = model(x, lengths)[0]
        logits_np = logits.detach().cpu().numpy()
        if state["ema_logits"] is None:
            state["ema_logits"] = logits_np
        else:
            state["ema_logits"] = STREAM_EMA_ALPHA * state["ema_logits"] + (1.0 - STREAM_EMA_ALPHA) * logits_np

        probs = _softmax_np(state["ema_logits"])
        cls_id = int(np.argmax(probs))
        pred_label = id2label.get(cls_id, "UNKNOWN")
        pred_conf = float(probs[cls_id])

    if pred_label and pred_conf >= STREAM_MIN_CONFIDENCE:
        state["vote_labels"].append(pred_label)
        state["vote_confs"].append(pred_conf)

    if state["vote_labels"]:
        counts = Counter(state["vote_labels"])
        vote_label = counts.most_common(1)[0][0]
        confs = [c for l, c in zip(state["vote_labels"], state["vote_confs"]) if l == vote_label]
        if confs:
            pred_label = vote_label
            pred_conf = float(sum(confs) / len(confs))

    stable = False
    if pred_label and pred_conf >= STREAM_CONFIDENCE_THRESHOLD:
        if pred_label == state["display_label"]:
            state["display_conf"] = pred_conf
            state["hold_counter"] = STREAM_HOLD_FRAMES
            state["candidate_label"] = ""
            state["candidate_count"] = 0
            stable = True
        elif pred_label == state["candidate_label"]:
            state["candidate_count"] += 1
            if state["candidate_count"] >= STREAM_STABLE_FRAMES:
                state["display_label"] = pred_label
                state["display_conf"] = pred_conf
                state["hold_counter"] = STREAM_HOLD_FRAMES
                state["candidate_label"] = ""
                state["candidate_count"] = 0
                stable = True
        else:
            state["candidate_label"] = pred_label
            state["candidate_count"] = 1
    else:
        if state["hold_counter"] > 0:
            state["hold_counter"] -= 1
        else:
            state["display_label"] = ""
            state["display_conf"] = 0.0
            state["candidate_label"] = ""
            state["candidate_count"] = 0

    return pred_label, pred_conf, probs.tolist(), stable



@router.post("/alphabet")
def alphabet_recognition(sign_input: AlphabetInput, me = Depends(get_current_user)):
    result = predict_alphabet(sign_input.frames)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.post("/tcn-recognize", response_model=SignPredictionResponse, dependencies=[Depends(get_current_user)])
def recognize_sign(
    req: SignSequenceRequest
):
    if not req.frames:
        raise HTTPException(status_code=400, detail="frames must not be empty")

    try:
        label, prob, probs = predict_sign(req.frames, model_key=req.model_key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return SignPredictionResponse(
        label=label,
        probability=prob,
        raw_probs=probs,
    )


@router.post("/tcn-register", dependencies=[Depends(get_current_user)])
def register_tcn_model_api(req: TCNModelRegisterRequest):
    try:
        register_tcn_model(
            model_key=req.model_key,
            checkpoint_path=req.checkpoint_path,
            labels_path=req.labels_path,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "message": "TCN model registered",
        "model_key": req.model_key,
    }


@router.get("/tcn-models", response_model=list[TCNModelInfo])
def list_tcn_models():
    return TCN_SERVICE.list_models()


@router.websocket("/tcn-stream")
async def tcn_stream_websocket(
    websocket: WebSocket,
    model_key: str = Query("hoa_de"),
    mode: str = Query("translated"),
    session_id: str | None = Query(None),
    token: str | None = Query(None),
):
    if not token:
        await websocket.close(code=4403, reason="Missing token")
        return

    try:
        payload = verify_supabase_jwt(token)
    except Exception:
        await websocket.close(code=4403, reason="Invalid token")
        return

    _ = payload
    session_id = session_id or str(uuid.uuid4())
    mode = mode if mode in {"translated", "chat"} else "translated"

    try:
        TCN_SERVICE.resolve_spec(model_key)
    except KeyError as exc:
        await websocket.accept()
        await _send_json_safe(
            websocket,
            {
                "type": "error",
                "session_id": session_id,
                "code": "UNKNOWN_MODEL_KEY",
                "message": str(exc),
            },
        )
        await websocket.close(code=4400)
        return

    state = _init_stream_state(model_key=model_key, mode=mode, session_id=session_id)
    async with STREAM_SESSION_LOCK:
        STREAM_SESSIONS[session_id] = state

    await websocket.accept()
    await _send_json_safe(
        websocket,
        {
            "type": "session.started",
            "session_id": session_id,
            "model_key": model_key,
            "mode": mode,
        },
    )

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await _send_json_safe(
                    websocket,
                    {
                        "type": "error",
                        "session_id": session_id,
                        "code": "INVALID_JSON",
                        "message": "WebSocket payload must be JSON",
                    },
                )
                continue

            msg_type = msg.get("type")

            if msg_type == "session.end":
                await _send_json_safe(
                    websocket,
                    {
                        "type": "session.ended",
                        "session_id": session_id,
                    },
                )
                await websocket.close()
                break

            if msg_type == "session.start":
                await _send_json_safe(
                    websocket,
                    {
                        "type": "buffer_status",
                        "session_id": session_id,
                        "buffer_size": len(state["buffer"]),
                        "required_size": STREAM_MAX_LEN,
                        "has_hand": False,
                    },
                )
                continue

            if msg_type != "frame":
                continue

            frame = msg.get("frame")
            if not isinstance(frame, list):
                await _send_json_safe(
                    websocket,
                    {
                        "type": "error",
                        "session_id": session_id,
                        "code": "INVALID_FRAME",
                        "message": "frame must be a list",
                    },
                )
                continue

            if _is_empty_frame(frame):
                state["buffer"].clear()
                state["ema_logits"] = None
                state["vote_labels"].clear()
                state["vote_confs"].clear()
                state["display_label"] = ""
                state["display_conf"] = 0.0
                state["candidate_label"] = ""
                state["candidate_count"] = 0
                state["hold_counter"] = 0
                await _send_json_safe(
                    websocket,
                    {
                        "type": "no_hand",
                        "session_id": session_id,
                        "buffer_cleared": True,
                    },
                )
                continue

            try:
                normalized = normalize_hands_vector_126(frame)
                if normalized.size != 126:
                    raise ValueError(f"Each frame must have exactly 126 features, got {normalized.size}")
            except Exception as exc:
                await _send_json_safe(
                    websocket,
                    {
                        "type": "error",
                        "session_id": session_id,
                        "code": "INVALID_FRAME_SHAPE",
                        "message": str(exc),
                    },
                )
                continue

            state["frame_index"] += 1
            state["buffer"].append(normalized.astype(np.float32))

            await _send_json_safe(
                websocket,
                {
                    "type": "buffer_status",
                    "session_id": session_id,
                    "buffer_size": len(state["buffer"]),
                    "required_size": STREAM_MAX_LEN,
                    "has_hand": True,
                },
            )

            pred_label, pred_conf, raw_probs, stable = _run_stream_inference(state)
            if not pred_label:
                continue

            live_payload = {
                "type": "live_prediction",
                "session_id": session_id,
                "model_key": model_key,
                "label": pred_label,
                "label_key": pred_label,
                "probability": pred_conf,
                "raw_probs": raw_probs,
                "stable": stable,
                "source": "ema_vote",
                "timestamp": int(time.time() * 1000),
            }
            await _send_json_safe(websocket, live_payload)

            if mode == "chat" and stable and pred_label != state["last_commit_label"]:
                state["last_commit_label"] = pred_label
                await _send_json_safe(
                    websocket,
                    {
                        "type": "final_text",
                        "session_id": session_id,
                        "model_key": model_key,
                        "text": pred_label,
                        "label_key": pred_label,
                        "probability": pred_conf,
                        "commit_id": str(uuid.uuid4()),
                        "timestamp": int(time.time() * 1000),
                    },
                )

    except WebSocketDisconnect:
        pass
    finally:
        async with STREAM_SESSION_LOCK:
            STREAM_SESSIONS.pop(session_id, None)
