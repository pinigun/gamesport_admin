from datetime import datetime, timedelta
from typing import Literal, TypedDict

from loguru import logger
from api.routers.dashboards.schemas import GeneralStats, GiveawaysGraphStats, StatsParam, TasksGraphStats, TasksStats, TicketsStats, Trend
from api.routers.tasks.schemas import TasksData
from database import db
import json

class TrendData(TypedDict):
    trend_value: str
    trend_direction: bool


class DashboardsTools:
    def _get_stat_trend(
        new_value: int | float,
        old_value: int | float
    ) -> TrendData:
        decimal_places = 2
        if old_value == 0:
            return TrendData(
                trend_value=f"+{0.0:.{decimal_places}f} %",
                trend_direction=True
            )
            
        trend_value = round(((new_value - old_value) / old_value)*100, 3)
        if trend_value < 0:
            return TrendData(
                trend_value=f'{trend_value:.{decimal_places}f} %',
                trend_direction=False
            )
        else:
            return TrendData(
                trend_value=f'+{trend_value:.{decimal_places}f} %',
                trend_direction=True
            )


        
    
    async def get_general_stats(period: Literal['today', 'yesterday']) -> GeneralStats:
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
                    # Считаем тренд
                    period[section_key][section_value_key] = {
                        "value": value,
                        'trend': DashboardsTools._get_stat_trend(float(value), float(prev_value))
                    }
                
        return GeneralStats(**period)
    
    
    async def get_giveaways_graph(
        start: datetime,
        end: datetime,
    ) -> list[GiveawaysGraphStats]:
        curr_giveaways = [dict(record) for record in await db.dashboards.get_giveaways_graph(start, end)]
        prev_giveaways = [dict(record) for record in await db.dashboards.get_giveaways_graph(start=None, end=start-timedelta(seconds=1))]
        return [
            GiveawaysGraphStats(
                id=curr_giveaway['id'],
                name=curr_giveaway['name'],
                users_count=StatsParam(
                    value=curr_giveaway['participants_count'],
                    trend=DashboardsTools._get_stat_trend(
                        new_value=curr_giveaway['participants_count'],
                        old_value=prev_giveaway['participants_count']
                    )
                )
            )
            for curr_giveaway, prev_giveaway in zip(curr_giveaways, prev_giveaways) 
        ]
    
    
    async def get_users_graph(
        start: datetime,
        end: datetime,
        preset: Literal['ALL', 'NEW', 'REPEATED']
    ):
        users_graph = await db.dashboards.get_users_graph(
            start=start,
            end=end,
            preset=preset
        )
        logger.debug(users_graph)
        result = dict()
        if users_graph:
            result[users_graph[0]['day']] = StatsParam(
                value=users_graph[0]['users_count'],
            )
            result.update(**{
                    str(users_graph[i]['day']): StatsParam(
                        value=  int(users_graph[i]['users_count']),
                        trend=DashboardsTools._get_stat_trend(
                            new_value=int(users_graph[i]['users_count']),
                            old_value=int(users_graph[i-1]['users_count'])
                        )
                    )
                    for i in range(1, len(users_graph))
                }
            )
        return result
    
    
    
    async def get_wheel_spins_graph(start: datetime, end: datetime):
        wheel_spins_graph = await db.dashboards.get_wheel_spins_graph(
            start=start,
            end=end
        )
        
        result = dict()
        if wheel_spins_graph:
            result[wheel_spins_graph[0]['day']] = StatsParam(
                value=wheel_spins_graph[0]['wheel_spins_count'],
            )
            result.update(**{
                    str(wheel_spins_graph[i]['day']): StatsParam(
                        value=  int(wheel_spins_graph[i]['wheel_spins_count']),
                        trend=DashboardsTools._get_stat_trend(
                            new_value=int(wheel_spins_graph[i]['wheel_spins_count']),
                            old_value=int(wheel_spins_graph[i-1]['wheel_spins_count'])
                        )
                    )
                    for i in range(1, len(wheel_spins_graph))
                }
            )
        return result
    
    
    
    async def get_referals_graph(start: datetime, end: datetime):
        referals_graph = await db.dashboards.get_referals_graph(
            start=start,
            end=end
        )
        
        result = dict()
        if referals_graph:
            result[referals_graph[0]['day']] = StatsParam(
                value=referals_graph[0]['referals_count'],
            )
            result.update(**{
                    str(referals_graph[i]['day']): StatsParam(
                        value=  int(referals_graph[i]['referals_count']),
                        trend=DashboardsTools._get_stat_trend(
                            new_value=int(referals_graph[i]['referals_count']),
                            old_value=int(referals_graph[i-1]['referals_count'])
                        )
                    )
                    for i in range(1, len(referals_graph))
                }
            )
        return result
    
    
    async def get_tasks_graph(start: datetime, end: datetime) -> list[TasksGraphStats]:
        graph_data = [dict(record) for record in await db.dashboards.get_graph_tasks(start, end)]
        prev_graph_data = [dict(record) for record in await db.dashboards.get_graph_tasks(start=None, end=start-timedelta(seconds=1))]
        return [
            TasksGraphStats(
                id=curr_data['id'],
                title=curr_data['title'],
                started=StatsParam(
                    value=curr_data['started'],
                    trend=DashboardsTools._get_stat_trend(curr_data['started'], prev_data['started'])
                ),
                completed=StatsParam(
                    value=curr_data['completed'],
                    trend=DashboardsTools._get_stat_trend(curr_data['completed'], prev_data['completed'])
                )
            )
            for curr_data, prev_data in zip(graph_data, prev_graph_data)
        ]
        
        
    async def get_tickets_graph(
        start:  datetime,
        end:    datetime,
        preset: Literal['RECEIVED', 'SPENT']
    ):
        tickets_graph = await db.dashboards.get_graph_tickets(
            start=start,
            end=end,
            preset='IN' if preset == 'RECEIVED' else 'OUT'
        )
        result = dict()
        if tickets_graph:
            result[tickets_graph[0]['day']] = StatsParam(
                value=tickets_graph[0]['total'],
            )
            result.update(**{
                    str(tickets_graph[i]['day']): StatsParam(
                        value=int(tickets_graph[i]['total']),
                        trend=DashboardsTools._get_stat_trend(
                            new_value=int(tickets_graph[i]['total']),
                            old_value=int(tickets_graph[i-1]['total'])
                        )
                    )
                    for i in range(1, len(tickets_graph))
                }
            )
        return result