from datetime import datetime
from typing import Literal
from fastapi import APIRouter

from api.routers.dashboards.schemas import GraphStats, TasksGraphStats
from api.routers.dashboards.tools.dashboards import DashboardsTools
from api.routers.tasks.schemas import TasksData


router = APIRouter(
    prefix='/dashboards',
    tags=['Dashboards']
)


@router.get('/general_stats')
async def get_general_stats(
    period: Literal['today', 'yesterday']
):
    return await DashboardsTools.get_general_stats(period)
    
    
@router.get("/graphs/users")
async def get_users_graph():
    ...

    
@router.get("/graphs/tickets")
async def get_tickets_graph(
    start:  datetime,
    end:    datetime,
    preset: Literal['received', 'spent']
) -> GraphStats:
    return GraphStats(
        data=await DashboardsTools.get_tickets_graph(
            start=start,
            end=end,
            preset=preset
        )
    )
    
    
@router.get("/graphs/tasks")
async def get_tasks_graph(
    start: datetime,
    end: datetime
) -> list[TasksGraphStats]:
    return await DashboardsTools.get_tasks_graph(start, end)
    
    
@router.get("/graphs/giveaways")
async def get_giveaways_graph():
    ...
    

@router.get("/graphs/referals")
async def get_referals_graph(
    start: datetime,
    end: datetime
) -> GraphStats:
    return GraphStats(data=await DashboardsTools.get_referals_graph(start, end))
    
    
@router.get("/graphs/wheel_spins")
async def get_wheel_spins_graph(
    start: datetime,
    end: datetime    
) -> GraphStats:
    return GraphStats(data=await DashboardsTools.get_wheel_spins_graph(start, end))
    