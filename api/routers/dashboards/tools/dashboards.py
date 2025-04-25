from datetime import datetime, timedelta
from tracemalloc import start
from typing import Literal, TypedDict

from loguru import logger
from api.routers.dashboards.schemas import GeneralStats
from database import db


class TrendData(TypedDict):
    trend_value: str
    trend_direction: bool


class DashboardsTools:
    def _get_stat_trend(
        new_value: int | float,
        old_value: int | float
    ) -> TrendData:
        if old_value == 0:
            return TrendData(
                trend_value="0.00 %" if new_value == old_value else "∞ %",
                trend_direction=True
            )
            
        trend_value = round(((new_value - old_value) / old_value)*100, 2)
        
        if trend_value < 0:
            return TrendData(
                trend_value=f'{trend_value} %',
                trend_direction=False
            )
        else:
            return TrendData(
                trend_value=f'{trend_value} %',
                trend_direction=True
            )

    
    async def get_general_stats(period: Literal['today', 'yesterday']):
        match period:
            # Так как нам надо возвращать тренд роста, мы берем статы по двум дням и считаем прирост
            case 'today':
                start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            case 'yesterday':
                start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)             
        end_date = start_date + timedelta(days=1) - timedelta(milliseconds=1)
        
        prev_start_date = start_date - timedelta(days=1)
        prev_end_date = end_date - timedelta(days=1)
        
        logger.debug(
            f"{start_date=}"
            f"{end_date=}"
            f"{prev_start_date=}"
            f"{prev_end_date=}"
        )
        result = await db.dashboards.get_general_stats(
            start_date=start_date,
            end_date=end_date,
            
            prev_start_date=prev_start_date,
            prev_end_date=prev_end_date,           
        )        
        logger.debug(result)
        period = result.period
        for section_key, section in period.items():
            if section:
                for section_value_key, value in section.items():
                    # Получаем значение этого же параметра из предыдущего периода
                    prev_value = result.prev_period[section_key][section_value_key]
                    period[section_key][section_value_key] = {
                        "value": value,
                        'trend': DashboardsTools._get_stat_trend(value, prev_value)
                    }
                
        return GeneralStats(**period)
        
        