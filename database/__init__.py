import asyncio
from config import DB_URL
from .db_interface import BaseInterface
from .db_interfaces.faq import FAQDBInterface
from .db_interfaces.docs import DocsDBInterface
from .db_interfaces.users import UsersDBInterface
from .db_interfaces.tasks import TasksDBInterface
from .db_interfaces.admins import AdminsDBInterface
from .db_interfaces.giveaways import GiveawaysDBInterface
from .db_interfaces.campaigns import CampaignsDBInterface 
from .db_interfaces.dashboars import DashboardsDBInterface
from .db_interfaces.statistics import StatisticsDBInterface


class DBInterface(BaseInterface):
    def __init__(self, db_url: str):
        super().__init__(db_url)
        self.faq = FAQDBInterface(session_=self.async_ses)
        self.docs = DocsDBInterface(session_=self.async_ses)
        self.users = UsersDBInterface(session_=self.async_ses)
        self.tasks = TasksDBInterface(session_=self.async_ses)
        self.admins = AdminsDBInterface(session_=self.async_ses)
        self.giveaways = GiveawaysDBInterface(session_=self.async_ses)
        self.campaigns = CampaignsDBInterface(session_=self.async_ses)
        self.dashboards = DashboardsDBInterface(session_=self.async_ses)
        self.statistics = StatisticsDBInterface(session_=self.async_ses)
    
    
db = DBInterface(DB_URL)


async def main():
    await db.initial()


if __name__ == '__main__':
    asyncio.run(main())
