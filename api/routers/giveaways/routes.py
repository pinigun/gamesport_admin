from datetime import datetime
import math
from typing import Literal, Union
from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from loguru import logger

from api.routers.giveaways.schemas import Giveaway, GiveawaysData, GiveawaysHistoryData, GivewayParticipantsData, GivewayPrizesData, PrizesData
from api.routers.giveaways.tools.giveaways import GiveawaysTools
from api.routers.statistics.tools.statistics import StatisticTools
from config import DATE_FORMAT, FRONT_DATE_FORMAT, FRONT_TIME_FORMAT
from database.exceptions import CustomDBExceptions


router = APIRouter(
    prefix='/giveaways',
)


@router.get('/', tags=['Giveaways'])
async def get_giveaways(
    page:       int = Query(1, gt=0),
    per_page:   int = Query(10, gt=0)
) -> GiveawaysData:
    total_items = await GiveawaysTools.get_giveaways_count()
    total_pages = math.ceil(total_items / per_page)
    
    return GiveawaysData(
        total_pages=total_pages,
        total_items=total_items,
        per_page=per_page,
        current_page=page,
        items = await GiveawaysTools.get_all(page=page, per_page=per_page) if total_pages else []
    )
    
    
@router.post('/giveaway', tags=['Giveaways'])
async def add_giveaway(
    prizes_photos:  list[UploadFile],
    prizes_data:    str | list[PrizesData],
    name:           str = Form(),
    active:         bool = Form(True),
    start_date:     str = Form(..., description=f'YYYY-MM-DD hh:mm:ss'),
    period_days:    int = Form(),
    price:          int = Form(),
) -> Giveaway:
    '''Ручка добавления конкурсов, фото добав'''
    return await GiveawaysTools.add(
        name=name,
        active=active,
        start_date=start_date,
        period_days=period_days,
        price=price,
        prizes_data=prizes_data,
        prizes_photos=prizes_photos
    )
    

@router.patch('/{giveaway_id}', tags=['Giveaways'])
async def add_giveaway(
    giveaway_id:    int,
    name:           Union[str, Literal['']] = Form(''),
    active:         Union[bool, Literal['']] = Form(''),
    start_date:     Union[datetime, Literal['']] = Form(''),
    period_days:    Union[int, Literal['']] = Form(''),
    price:          Union[int, Literal['']] = Form(''),
    photo:          Union[UploadFile, Literal['']] = File(None)
) -> Giveaway:
    try:
        return await GiveawaysTools.update(
            giveaway_id=giveaway_id,
            name=       name        if name not in (None, '') else None,
            active=     active      if active not in (None, '') else None,
            start_date= start_date  if start_date not in (None, '') else None,
            period_days=period_days if period_days not in (None, '') else None,
            price=      price       if price not in (None, '') else None,
            photo=      photo       if photo not in (None, '') else None
        )
    except CustomDBExceptions as ex:
        raise HTTPException(status_code=400, detail=ex.message)


@router.get('/history', tags=['Giveaways.History'])
async def get_giveaways_history(
    page:       int = Query(1, gt=0),
    per_page:   int = Query(10, gt=0)
) -> GiveawaysHistoryData:
    total_admins = await GiveawaysTools.get_history_count()
    total_pages = math.ceil(total_admins / per_page)
    
    return GiveawaysHistoryData(
        total_pages=total_pages,
        total_items=total_admins,
        per_page=per_page,
        current_page=page,
        items = await GiveawaysTools.get_history(page=page, per_page=per_page) if total_pages else []
    )


@router.get('/{giveaway_id}', tags=['Giveaways'])
async def get_giveaway(
    giveaway_id: int
) -> Giveaway:
    try:
        return await GiveawaysTools.get(giveaway_id=giveaway_id)
    except CustomDBExceptions as ex:
        raise HTTPException(status_code=400, detail=ex.message)


@router.post('/prizes/{giveaway_id}', tags=['Giveaways.Prizes'])
async def add_prizes(
    giveaway_id: int,
    name:   list[str] = Form(),
    photo:  list[UploadFile] = File()
):
    try:
        return await GiveawaysTools.add_prize(giveaway_id, name, photo)
    except CustomDBExceptions as ex:
        raise HTTPException(status_code=400, detail=ex.message)


@router.get('/prizes/{giveaway_id}', tags=['Giveaways.Prizes'])
async def get_prizes(
    giveaway_id: int,
    page:       int = Query(1, gt=0),
    per_page:   int = Query(10, gt=0)
) -> GivewayPrizesData:
    try:
        total_admins = await GiveawaysTools.get_prizes_count(giveaway_id)
        total_pages = math.ceil(total_admins / per_page)
        
        return GivewayPrizesData(
            total_pages=total_pages,
            total_items=total_admins,
            per_page=per_page,
            current_page=page,
            items = await GiveawaysTools.get_prizes(giveaway_id=giveaway_id, page=page, per_page=per_page) if total_pages else []
        )
    except CustomDBExceptions as ex:
        raise HTTPException(status_code=400, detail=ex.message)


@router.get('/participants/{giveaway_id}', tags=['Giveaways.Participants'])
async def get_giveaway_participtants(
    giveaway_id: int,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    page:       int = Query(1, gt=0),
    per_page:   int = Query(10, gt=0)
) -> GivewayParticipantsData:
    if not any((start_date, end_date)): 
        raise HTTPException(400, detail='Bad request: Any data should been is not none')
    
    
    try:
        total_items = await GiveawaysTools.get_participants_count(
            giveaway_id,
            start_date,
            end_date
        )
        total_pages = math.ceil(total_items / per_page)
        
        return GivewayParticipantsData(
            total_pages=total_pages,
            total_items=total_items,
            per_page=per_page,
            current_page=page,
            items = await GiveawaysTools.get_participants(
                page=page, 
                per_page=per_page,
                start_date=start_date,
                end_date=end_date,
                giveaway_id=giveaway_id, 
                ) if total_pages else []
        )
    except CustomDBExceptions as ex:
        raise HTTPException(status_code=400, detail=ex.message)
   
   
@router.get('/participants/report/{giveaway_id}', tags=['Giveaways.Participants'])
async def get_giveaway_participtants_report(
    giveaway_id: int,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    page:       int = Query(1, gt=0),
    per_page:   int = Query(10, gt=0)
) -> GivewayParticipantsData:
    if not any((start_date, end_date)): 
        raise HTTPException(400, detail='Bad request: Any data should been is not none')
    try:
        participants = await GiveawaysTools.get_participants(
            page=page, 
            per_page=per_page,
            start_date=start_date,
            end_date=end_date,
            giveaway_id=giveaway_id, 
        )  
        output = await GiveawaysTools.get_participants_report(participants)
        headers = {
            'Content-Disposition': f'attachment; filename="giveaway{giveaway_id}.xlsx"'
        }
        return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers=headers)
    except CustomDBExceptions as ex:
        raise HTTPException(status_code=400, detail=ex.message)    
    
    
    
    
@router.post('/participants/winner', tags=['Giveaways.Participants'])
async def add_winner(
    giveaway_id:    int = Body(),
    winner_id:      int = Body(),
    prize_id:       int = Body()
) -> JSONResponse:
    try:
        await GiveawaysTools.add_winner(
            giveaway_id=giveaway_id,
            winner_id=winner_id,
            prize_id=prize_id
        )
        return JSONResponse(content={'detail': 'success'})
    except CustomDBExceptions as ex:
        raise HTTPException(status_code=400, detail=ex.message)