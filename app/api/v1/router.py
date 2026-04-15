from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["API"])


@router.get("/test")
async def test():
    return {"Hello": "World!"}
