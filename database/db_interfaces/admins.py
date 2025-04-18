from database.db_interface import BaseInterface
from loguru import logger
from database.models import (
    Admin,
    AdminRole,
    AdminRoleLink,
    AdminRolePermissions,
    AdminRolePermissionLink,
)



class AdminsDBInterface(BaseInterface):
    def __init__(self, session_):
        super().__init__(session_ = session_)
   
   
    async def get_all_permissions(self):
        return await self.get_rows(AdminRolePermissions)
    
    
    async def add_admin(
        self
    ):
        pass
    
    
    async def get_all_admins(
        self
    ):
        pass
    
    
    