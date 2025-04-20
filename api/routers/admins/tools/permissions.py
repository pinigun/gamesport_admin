from api.routers.admins.schemas import RolePermissionResponse
from database import db


class PermissionsTools:
    async def get_all(roles_ids: list[int]) -> list[RolePermissionResponse]:
        return [
            RolePermissionResponse.model_validate(role_permission)
            for role_permission in await db.admins.get_all_permissions(roles_ids)
        ]