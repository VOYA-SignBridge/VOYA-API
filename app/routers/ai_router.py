from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import HTTPBearer
from app.ml.sign_interface import TCN_SERVICE, predict_sign, register_tcn_model
# from app.services.ai.ai_sign2text_service import predict_sign2text
from app.services.ai.ai_alphabet_service import predict_alphabet
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
