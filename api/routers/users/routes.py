from datetime import datetime
import math
from fastapi import APIRouter, Depends, Query, HTTPException

from api.routers.auth.tools.auth import AuthTools
from api.routers.users.schemas import EditUserRequest, UserFilters, UserResponse, UsersData
from api.routers.users.tools.users import UsersTools
from config import FRONT_DATE_FORMAT, FRONT_TIME_FORMAT
from custom_types import PermissionsTags
from database.exceptions import CustomDBExceptions


router = APIRouter(
    tags=['Users'],
    prefix='/users',
    # dependencies=[Depends(AuthTools.check_permissions(PermissionsTags.USERS))]
)


@router.get('/')
async def get_all_users(
    page:       int = Query(default=1, gt=0),
    per_page:   int = Query(default=12, gt=0, max=20),
    filter:     UserFilters = Depends()
) -> UsersData:
    for field in ("created_at_end", "created_at_start"):
        attr = getattr(filter, field)
        if isinstance(attr, str):
            try:
                setattr(
                    filter,
                    field,
                    datetime.strptime(
                        attr,
                        f"{FRONT_DATE_FORMAT} {FRONT_TIME_FORMAT}"
                    )
                )
                
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f'time data "{attr}" does not match format "{FRONT_DATE_FORMAT} {FRONT_TIME_FORMAT}"'
                )
                
    users = await UsersTools.get_all(
        page=page,
        per_page=per_page,
        filter=filter,
    )
    
    total_items = await UsersTools.get_count(
        filter=filter
    )
    total_pages = math.ceil(total_items / per_page)
    return UsersData(
        total_pages=total_pages,
        total_items=total_items,
        per_page=per_page,
        current_page=page,
        items = users
    )


@router.get('/{user_id}')
async def get_user(user_id: int) -> UserResponse:
    try:
        return await UsersTools.get(user_id)
    except CustomDBExceptions as ex:
        raise HTTPException(status_code=400, detail=ex.message)


@router.patch('/{user_id}')
async def edit_user(
    user_id: int,
    user_data: EditUserRequest
) -> UserResponse:
    try:
        return await UsersTools.update(user_id, user_data)
    except CustomDBExceptions as ex:
        raise HTTPException(status_code=400, detail=ex.message)
    
# @router.delete('/{user_id}')
# async def delete_faq(
#     user_id: int
# ):
#     ...
    
    