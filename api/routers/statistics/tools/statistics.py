from loguru import logger
from api.routers.statistics.schemas import DailyStatistic, StatisticData, StatisticFilters
from database import db


class StatisticTools:
    async def get_all(filters: StatisticFilters):
        statistics = await db.statistics.get_all_stats(**filters.model_dump())
        logger.debug(list(statistics.items())[:2])
        return StatisticData(
            data={
                date: DailyStatistic(**statistics[date])
                for date in statistics
            }
        )