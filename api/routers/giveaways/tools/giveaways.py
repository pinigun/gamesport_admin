from loguru import logger
from api.routers.statistics.schemas import DailyStatistic, StatisticData, StatisticFilters
from database import db


class GiveawaysTools:
    async def get_ids() -> list[int]:
        return await db.giveaways.get_ids()