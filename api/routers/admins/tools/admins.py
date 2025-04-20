import hashlib
from database import db
from api.routers.admins.schemas import AdminRequest, AdminResponse


class AdminsTools:
    def _hashpw(password: str) -> str:
        return hashlib.md5(password.encode()).hexdigest()
    
    
    async def delete(admin_id: int):
        return await db.admins.delete(admin_id) 
                
    
    async def get_count():
        return await db.admins.get_count()
    
    
    async def edit(
        admin_id:   int,
        admin_data: AdminRequest,
    ) -> AdminResponse:
        return AdminResponse.model_validate(
            await db.admins.edit(
                admin_id=admin_id,
                admin_data=admin_data.model_dump()
            )
        )
    
    
    async def get_all(
        page:       int,
        per_page:   int
    ) -> list[AdminResponse]:
        return [
            AdminResponse.model_validate(admin)
            for admin in await db.admins.get_all(
                page=page,
                per_page=per_page
            )
        ]
    
    
    async def add(admin_data: AdminRequest):
        admin_dict = admin_data.model_dump()
        admin_dict['status'] = admin_dict['status'].value
        admin_dict['password'] = AdminsTools._hashpw(password=admin_dict['password'])
        
        return AdminResponse.model_validate(
            await db.admins.add_admin(
                admin_dict
            )
        )
        