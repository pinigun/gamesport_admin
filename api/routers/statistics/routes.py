from datetime import datetime
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query

from api.routers.statistics.schemas import StatisticData, StatisticFilters
from api.routers.statistics.tools.statistics import StatisticTools
from config import FRONT_DATE_FORMAT, FRONT_TIME_FORMAT


router = APIRouter(
    tags=['Statistics'],
    prefix='/statistics',
)


@router.get('/')
async def get_statistics(
    page:               int = Query(1, gt=0),
    per_page:           int = Query(10, gt=0),
    order_by:           Literal['date'] = 'date',
    order_direction:    Literal['desc', 'asc'] = 'desc',
    filters:            StatisticFilters = Depends()
) -> StatisticData:
    for field in ("datetime_end", "datetime_start"):
        attr = getattr(filters, field)
        if isinstance(attr, str):
            try:
                setattr(
                    filters,
                    field,
                    datetime.strptime(
                        attr,
                        f"{FRONT_DATE_FORMAT} {FRONT_TIME_FORMAT}"
                    )
                )
                
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f'time data "{attr}" does not match format "{FRONT_DATE_FORMAT} {FRONT_TIME_FORMAT}"'
                )
    return await StatisticTools.get_all(
        page=page,
        per_page=per_page,
        order_by=order_by,
        order_direction=order_direction,
        filters=filters
    )