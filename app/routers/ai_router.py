from fastapi import APIRouter, Depends, HTTPException
from app.services.ai.ai_sign2text_service import predict_sign2text
from app.services.ai.ai_alphabet_service import predict_alphabet
from app.schemas.ai_schema import Sign2TextInput, AlphabetInput
from app.core.dependencies import get_current_user as get
from app.models.user import User
from app.db.database import get_db
router = APIRouter(prefix="/ai", tags=["AI SERVICE"])


@router.post("/sign2text")
def sign_to_text(sign_input: Sign2TextInput , current_user: User= Depends(get)):
    result = predict_sign2text(sign_input.frames)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.post("/alphabet")
def alphabet_recognition(sign_input: AlphabetInput, current_user: User= Depends(get_db)):
    result = predict_alphabet(sign_input.frames)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result