from typing import TypedDict
from database.db_interface import BaseInterface
from database.exceptions import FAQNotFound
from database.models import FAQ, Giveaway
from sqlalchemy import select, text, update


class GiveawaysDBInterface(BaseInterface):
    def __init__(self, session_):
        super().__init__(session_ = session_)
        

    async def get_ids(self):
        return await self.get_rows(
            Giveaway.id
        )