from fastapi import APIRouter, Depends

from app.core.dependencies import  get_current_user

router= APIRouter(prefix="/auth", tags=["AUTHENTICATION SERVICE"])



@router.get("/me")
def get_me(me = Depends(get_current_user)):
    return me

