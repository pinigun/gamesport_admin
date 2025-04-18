import math
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from api.routers.admins.schemas import AdminRequest, AdminResponse, AdminsData, EditAdminRequest, RolePermissionResponse, RoleRequest
from api.routers.admins.tools.admins import AdminsTools
from api.routers.admins.tools.permissions import PermissionsTools
from api.routers.admins.tools.roles import RolesTools
from database.exceptions import CustomDBExceptions


router = APIRouter(
    prefix='/admins',
)


@router.post('/auth', tags=['Admins'])
async def admin_auth():
    pass


@router.get('/', tags=['Admins'])
async def get_all_admins(
    page: int = 1,
    per_page: int = 12,
):
    total_admins = await AdminsTools.get_count()
    total_pages = math.ceil((total_admins - 1) / per_page)
    
    return AdminsData(
        total_pages=total_pages,
        total_admins=total_admins,
        per_page=per_page,
        current_page=page,
        admins = await AdminsTools.get_all(page, per_page) if total_pages else []
    )


@router.post('/admin', tags=['Admins'])
async def add_admin(
    admin_data: AdminRequest
):
    try:
        return await AdminsTools.add(admin_data)
    except CustomDBExceptions as ex:
        raise HTTPException(status_code=400, detail=ex.message)


@router.patch('/admin/{admin_id}', tags=['Admins'])
async def edit_admin(
    admin_id: int,
    admin_data: EditAdminRequest
):
    try:
        return await AdminsTools.edit(
            admin_id=admin_id,
            admin_data=admin_data
        )
    except CustomDBExceptions as ex:
        raise HTTPException(status_code=400, detail=ex.message)


@router.delete('/admin/{admin_id}', tags=['Admins'])
async def delete_admin(
    admin_id: int
):
    try:
        await AdminsTools.delete(admin_id)
        return JSONResponse(content={'detail': 'success'})
    except CustomDBExceptions as ex:
        raise HTTPException(status_code=400, detail=ex.message)
 

@router.get('/roles/', tags=['Admins.Roles'])
async def get_all_roles():
    return await RolesTools.get_all()


@router.get('/roles/permissions', tags=['Admins.Roles'])
async def get_all_permissions() -> list[RolePermissionResponse]:
    return await PermissionsTools.get_all()
       

@router.post('/roles/role', tags=['Admins.Roles'])
async def add_role(
    role_data: RoleRequest
):
    try:
        return await RolesTools.add(role_data)
    except CustomDBExceptions as ex:
        raise HTTPException(status_code=400, detail=ex.message)


@router.patch('/roles/{role_id}', tags=['Admins.Roles'])
async def edit_role(
    role_id: int,
    new_role_data: RoleRequest
):
    try:
        return await RolesTools.edit(
            role_id=role_id, 
            role_data=new_role_data
        )
    except CustomDBExceptions as ex:
        raise HTTPException(status_code=400, detail=ex.message)
