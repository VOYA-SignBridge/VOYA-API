from enum import Enum
from pydantic import BaseModel
from typing import List


class TCNModelKey(str, Enum):
    hoa_de = "hoa_de"

class Sign2TextInput(BaseModel):
    frames: List[List[float]]  # 60 frames × 226 features/frame

class AlphabetInput(BaseModel):
    frames: List[List[List[float]]]  # seq_len × 21 keypoints × 3 coords

class SignSequenceRequest(BaseModel):
    # mỗi frame là 1 vector float chiều D=in_dim
    frames: List[List[float]]
    model_key: TCNModelKey = TCNModelKey.hoa_de


class TCNModelRegisterRequest(BaseModel):
    model_key: str
    checkpoint_path: str
    labels_path: str | None = None


class TCNModelPredictionRequest(BaseModel):
    model_key: TCNModelKey = TCNModelKey.hoa_de
    frames: List[List[float]]


class TCNModelInfo(BaseModel):
    model_key: str
    name: str
    checkpoint_path: str
    labels_path: str | None = None
    is_loaded: bool = False


class SignPredictionResponse(BaseModel):
    label: str
    probability: float
    raw_probs: List[float]
