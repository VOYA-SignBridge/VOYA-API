from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["AUTHENTICATION SERVICE"])



@router.get("/me")
def get_me():
    """Return a placeholder profile now that authentication is disabled."""

    return {
        "id": None,
        "supabase_id": None,
        "email": None,
        "full_name": "Guest",
        "authenticated": False,
    }

