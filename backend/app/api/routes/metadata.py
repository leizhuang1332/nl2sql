from fastapi import APIRouter

router = APIRouter()

@router.get("/tables")
async def get_tables():
    return {"tables": []}
