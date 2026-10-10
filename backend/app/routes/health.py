from fastapi import APIRouter

router = APIRouter()


@router.get("/api/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "user-authentication-system"}
