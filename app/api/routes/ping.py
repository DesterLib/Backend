from fastapi import APIRouter


router = APIRouter(
    prefix="/ping",
    tags=["misc"],
)


@router.get("", response_model=dict, status_code=200)
def ping() -> dict:
    return {"ok": True, "message": "Pong!"}
