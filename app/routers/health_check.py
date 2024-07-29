from fastapi import APIRouter

router = APIRouter(prefix="/healthcheck", tags=["General"])


@router.get("/")
async def root():
    return {"status_code": 200, "detail": "ok", "result": "working"}
