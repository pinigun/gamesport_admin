import bcrypt
from api.routers.admins.schemas import AdminRequest, AdminResponse
from database import db


class AdminsTools:
    def _checkpw(
        input_password: str,
        db_password: str
    ):
        return bcrypt.checkpw(input_password, db_password)
        
        
    def _hashpw(password: str):
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    
    
    async def edit(
        admin_id: int,
        admin_data: AdminRequest,
    ) -> AdminResponse:
        return AdminResponse.model_validate(
            await db.admins.edit(
                admin_id=admin_id,
                admin_data=admin_data.model_dump()
            )
        )
    
    
    async def get_all(page: int, per_page: int):
        return [
            AdminResponse.model_validate(admin)
            for admin in await db.admins.get_all(
                page=page,
                per_page=per_page
            )
        ]
                
    
    async def get_count():
        return await db.admins.get_count()
    
    
    async def add(admin_data: AdminRequest):
        admin_dict = admin_data.model_dump()
        admin_dict['status'] = admin_dict['status'].value
        admin_dict['password'] = AdminsTools._hashpw(password=admin_dict['password'])
        
        return AdminResponse.model_validate(
            await db.admins.add_admin(
                admin_dict
            )
        )
        
    async def delete(admin_id: int):
        return await db.admins.delete(admin_id) 