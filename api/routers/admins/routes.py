from fastapi import APIRouter

from api.routers.admins.schemas import RolePermissionResponse
from api.routers.admins.tools.permissions import PermissionsTools


router = APIRouter(
    prefix='/admins',
    tags=['Admins']
)


@router.post('/auth')
async def admin_auth():
    pass
 

@router.get('/roles/permissions')
async def get_all_permissions() -> list[RolePermissionResponse]:
    return await PermissionsTools.get_all_permissions()
   

@router.get('/roles/{role_id}/permissons')
async def get_role_permission(
    role_id: int
):
    pass
    

@router.post('/roles/role')
async def add_role():
    pass


@router.patch('/roles/{role_id}')
async def edit_role(
    role_id: int,
):
    pass


@router.get('/')
async def get_all_admins():
    pass


@router.post('/admin')
async def create_admin():
    pass


@router.patch('/admin/{admin_id}')
async def edit_admin(
    admin_id: int
):
    pass


@router.delete('/admin/{admin_id}')
async def delete_admin(
    admin_id: int
):
    pass