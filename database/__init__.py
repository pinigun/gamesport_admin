import asyncio
from config import DB_URL
from .db_interface import BaseInterface
from .db_interfaces.users import UsersDBInterface
from .db_interfaces.admins import AdminsDBInterface


class DBInterface(BaseInterface):
    def __init__(self, db_url: str):
        super().__init__(db_url)
        self.users = UsersDBInterface(session_=self.async_ses)
        self.admins = AdminsDBInterface(session_=self.async_ses)
    
    
db = DBInterface(DB_URL)


async def main():
    await db.initial()


if __name__ == '__main__':
    asyncio.run(main())
