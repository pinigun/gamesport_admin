from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query

from api.routers.giveaways.schemas import Giveaway
from api.routers.giveaways.tools.giveaways import GiveawaysTools
from api.routers.statistics.schemas import StatisticData, StatisticFilters
from api.routers.statistics.tools.statistics import StatisticTools
from config import FRONT_DATE_FORMAT, FRONT_TIME_FORMAT


router = APIRouter(
    tags=['Giveaways'],
    prefix='/giveaways',
)


@router.get('/')
async def get_giveaways(
    page:       int = Query(1, gt=0),
    per_page:   int = Query(10, gt=0)
) -> list[Giveaway]:
    return await GiveawaysTools.get_all(page=page, per_page=per_page)