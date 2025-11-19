from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import HTTPBearer
from app.ml.sign_interface import predict_sign
from app.services.ai.ai_sign2text_service import predict_sign2text
from app.services.ai.ai_alphabet_service import predict_alphabet
from app.schemas.ai_schema import Sign2TextInput, AlphabetInput, SignPredictionResponse, SignSequenceRequest
# from app.core.dependencies import get_current_user 
from app.models.user import User
from app.db.database import get_db
security = HTTPBearer()

router = APIRouter(prefix="/ai", tags=["AI SERVICE"])


@router.post("/sign2text")
def sign_to_text(sign_input: Sign2TextInput ):
    result = predict_sign2text(sign_input.frames)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.post("/alphabet")
def alphabet_recognition(sign_input: AlphabetInput):
    result = predict_alphabet(sign_input.frames)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.post("/tcn-recognize", response_model=SignPredictionResponse)
def recognize_sign(
    req: SignSequenceRequest,
    
):
    if not req.frames:
        raise HTTPException(status_code=400, detail="frames must not be empty")

    try:
        label, prob, probs = predict_sign(req.frames)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return SignPredictionResponse(
        label=label,
        probability=prob,
        raw_probs=probs,
    )