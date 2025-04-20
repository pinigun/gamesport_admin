from fastapi import APIRouter


router = APIRouter(
    prefix='/dashboards',
    tags=['Dashboards']
)


@router.get('/')
async def get_general_stats():
    ...
    
    
