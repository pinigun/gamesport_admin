from api.routers.admins.schemas import RoleResponse, RoleRequest
from database import db

class RolesTools:
    async def get_all() -> list[RoleResponse]:
        return [
            RoleResponse.model_validate(role)
            for role in await db.admins.get_all_roles()
        ]
    
    
    async def add(role_data: RoleRequest) -> RoleResponse:
        return RoleResponse.model_validate(
            await db.admins.add_role(**role_data.model_dump())
        )
        
    
    async def edit(role_id: int, role_data: RoleRequest) -> RoleResponse:
        return RoleResponse.model_validate(
            await db.admins.edit_role(
                role_id=role_id,
                role_data=role_data.model_dump()
            )
        )