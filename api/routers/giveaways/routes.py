from datetime import datetime
from typing import Literal, Optional, Union
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile

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


@router.post('/giveaway')
async def add_giveaway(
    name:           str = Form(),
    active:         bool = Form(True),
    start_date:     datetime = Form(),
    period_days:    int = Form(),
    price:          int = Form(),
    photo:          UploadFile = File()
):
    return await GiveawaysTools.add(
        name=name,
        active=active,
        start_date=start_date,
        period_days=int(period_days),
        price=int(price),
        photo=photo
    )
    

@router.patch('/{giveaway_id}')
async def add_giveaway(
    request:        Request,
    giveaway_id:    int,
    name:           Union[str, Literal['']] = Form(''),
    active:         Union[bool, Literal['']] = Form(''),
    start_date:     Union[datetime, Literal['']] = Form(''),
    period_days:    Union[int, Literal['']] = Form(''),
    price:          Union[int, Literal['']] = Form(''),
    photo:          Union[UploadFile, Literal['']] = File(None)
) -> Giveaway:
    return await GiveawaysTools.update(
        giveaway_id=giveaway_id,
        name=       name        if name not in (None, '') else None,
        active=     active      if active not in (None, '') else None,
        start_date= start_date  if start_date not in (None, '') else None,
        period_days=period_days if period_days not in (None, '') else None,
        price=      price       if price not in (None, '') else None,
        photo=      photo       if photo not in (None, '') else None
    )