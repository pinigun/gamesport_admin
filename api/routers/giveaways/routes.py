from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException

from api.routers.giveaways.tools.giveaways import GiveawaysTools
from api.routers.statistics.schemas import StatisticData, StatisticFilters
from api.routers.statistics.tools.statistics import StatisticTools
from config import FRONT_DATE_FORMAT, FRONT_TIME_FORMAT


router = APIRouter(
    tags=['Giveaways'],
    prefix='/giveaways',
)


@router.get('/')
async def get_giveaways() -> list[int]:
    return await GiveawaysTools.get_ids()