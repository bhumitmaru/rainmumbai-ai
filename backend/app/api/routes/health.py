from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "app": "RainMumbai AI", "version": "1.0.0"}
