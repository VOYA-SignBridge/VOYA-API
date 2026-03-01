# app/ai/embedding_text.py

from FlagEmbedding import FlagModel
import numpy as np
from sqlalchemy.orm import Session
from app.models.sign import Sign

# Load model đúng chuẩn
_model = FlagModel(
    "BAAI/bge-m3",
    query_instruction_for_retrieval="",
    device="cpu"
)

_sign_vectors = {}

def build_sign_embeddings(db: Session):
    global _sign_vectors
    _sign_vectors = {}

    signs = db.query(Sign).all()

    texts = []
    keys = []

    for s in signs:
        text = s.description or s.key
        texts.append(text)
        keys.append(s.key)

    if not texts:
        return

    result = _model.encode(texts)
    dense_vecs = result["dense_vecs"]  # list[np.ndarray]

    for key, vec in zip(keys, dense_vecs):
        _sign_vectors[key] = np.array(vec)

    print("Built embeddings:", len(_sign_vectors))


def get_sign_vectors():
    return _sign_vectors


def embed_text(text: str):
    result = _model.encode([text])
    return np.array(result["dense_vecs"][0])
