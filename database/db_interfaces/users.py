from database.db_interface import BaseInterface
from loguru import logger


class UsersDBInterface(BaseInterface):
    def __init__(self, session_):
        super().__init__(session_ = session_)
   
    
    async def get_users(
        self,
        **filters
    ):
        pass