from fastapi import APIRouter

router = APIRouter()

@router.get("/history")
async def get_history():
    return {"history": []}
