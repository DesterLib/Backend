from typing import Dict

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(
    # dependencies=[Depends(get_token_header)],
    prefix="/auth",
    default_response_class=JSONResponse({"message": "Are you lost?"}, status_code=404),
    responses={404: {"description": "Not found"}},
    tags=["internals"],
)


@router.get(
    "",
    response_model=Dict[str, str],
    responses={404: {"description": "Unauthorized"}},
    status_code=200,
)
def auth() -> Dict[str, str]:
    return {"message": "image"}
