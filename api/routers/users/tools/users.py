from loguru import logger
from dataclasses import field
from api.routers.users.schemas import EditUserRequest, UserFilters, UserResponse
from database import db
from database.exceptions import UserNotFound


class UsersTools:
    async def update(user_id: int, user_data: EditUserRequest) -> UserResponse:
        updated_user = await db.users.update_user(
            user_id,
            user_data.model_dump(exclude_none=True)
        )
        logger.debug(updated_user)
        return UserResponse.model_validate(updated_user)
    
    
    async def get_count(filter: UserFilters) -> int:
        searching_fields = ("email", "phone", "tg_id")
        searching_filter = {}
        for searching_field in searching_fields:
            if getattr(filter, searching_field):
                searching_filter[searching_field] = getattr(filter, searching_field)
                
        return await db.users.get_filtered_count(
            **filter.model_dump(exclude=['tg_id', "email", 'phone']),
            **searching_filter
        ) 
        
    
    async def get_all(
        page: int,
        per_page: int,
        filter: UserFilters,
        task_id: int | None = None
    ) -> list[UserResponse]:
        searching_fields = ("email", "phone", "tg_id")
        searching_filter = {}
        for searching_field in searching_fields:
            if getattr(filter, searching_field):
                searching_filter[searching_field] = getattr(filter, searching_field)
        
        return [
            UserResponse.model_validate(user)
            for user in await db.users.get_all(
                page=page,
                per_page=per_page,
                task_id=task_id,
                **filter.model_dump(exclude=['tg_id', "email", 'phone']),
                **searching_filter,
            )
        ]
        
    
    async def get(user_id) -> UserResponse:
        result = await db.users.get_all(page=1, per_page=1, id=user_id)
        if not result:
            raise UserNotFound
        return UserResponse.model_validate(result[0])