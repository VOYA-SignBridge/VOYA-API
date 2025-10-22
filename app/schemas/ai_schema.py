from pydantic import BaseModel
from typing import List

# ✅ Dành cho model sign2text (TensorFlow)
class Sign2TextInput(BaseModel):
    frames: List[List[float]]  # 60 frames × 226 features/frame

# ✅ Dành cho model alphabet (PyTorch)
class AlphabetInput(BaseModel):
    frames: List[List[List[float]]]  # seq_len × 21 keypoints × 3 coords
