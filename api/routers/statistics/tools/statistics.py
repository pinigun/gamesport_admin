import math
from loguru import logger
from api.routers.statistics.schemas import DailyStatistic, StatisticData, StatisticFilters
from database import db


class StatisticTools:
    async def get_all(page: int, per_page: int, filters: StatisticFilters) -> StatisticData:
        statistics, total_items = await db.statistics.get_all_stats(page=page, per_page=per_page,**filters.model_dump())
        logger.debug(list(statistics.items())[:2])
        return StatisticData(
            total_items=total_items,
            total_pages=math.ceil(total_items/per_page),
            per_page=per_page,
            current_page=page,
            data={
                date: DailyStatistic(**statistics[date])
                for date in statistics
            }
        )