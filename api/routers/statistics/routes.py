from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException

from api.routers.statistics.schemas import StatisticFilters
from api.routers.statistics.tools.statistics import StatisticTools
from config import FRONT_DATE_FORMAT, FRONT_TIME_FORMAT


router = APIRouter(
    tags=['Statistics'],
    prefix='/statistics',
)


@router.get('/')
async def get_statistics(
    filters: StatisticFilters = Depends()
):
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
    return await StatisticTools.get_all(filters)