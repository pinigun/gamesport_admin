from fastapi import APIRouter
from fastapi.responses import JSONResponse

from api.routers.auth.schemas import LogInModel
from api.routers.auth.tools.auth import AuthData, AuthTools
from database.exceptions import CustomDBExceptions
from fastapi import HTTPException


router = APIRouter()


@router.post('/auth', tags=['Auth'])
async def auth(
    auth_request: LogInModel
):
    try:
        auth_data: AuthData = await AuthTools.auth(auth_request)
        return JSONResponse(
            status_code=200,
            content=auth_data.admin_data,
            headers={
                'Authorization': f'Bearer {auth_data.jwt_token}'
            }
        )
    except CustomDBExceptions as ex:
        raise HTTPException(status_code=400, detail=ex.message)
    