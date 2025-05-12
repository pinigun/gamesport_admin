from datetime import datetime
import math
from typing import Literal
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from loguru import logger

from api.routers.campaign.schemas import CampaignsData, Trigger, TriggerRequest, TriggersData
from api.routers.campaign.tools.campaign import CampaignTools
from api.routers.dashboards.schemas import GeneralStats, GiveawaysGraphStats, GraphStats, TasksGraphStats
from api.routers.dashboards.tools.dashboards import DashboardsTools
from api.routers.tasks.schemas import TasksData
from database.exceptions import CustomDBExceptions


router = APIRouter(
    prefix='/campaigns',
    tags=['Campaigns']
)


@router.get('/')
async def get_campaigns(
    page: int = 1,
    per_page: int = 12,
    campaign_id: int | None = None,
    name: str | None = None,
    is_active: bool | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    order_by: Literal['id'] = "id",
    order_direction: Literal['desc', 'asc'] = 'desc'
) -> CampaignsData:
    total_items = await CampaignTools.get_count()
    total_pages = math.ceil(total_items / per_page)
    
    return CampaignsData(
        total_pages=total_pages,
        total_items=total_items,
        per_page=per_page,
        current_page=page,
        items = await CampaignTools.get_all(
            page=page,
            per_page=per_page,
            order_by=order_by,
            order_direction=order_direction,
            campaign_id=campaign_id,
            start_date=start_date,
            end_date=end_date,
            is_active=is_active,
            name=name,
        ) if total_pages else []
    )

    
@router.post('/campaign')
async def add_campaign(
    name: str = Form(...),
    text: str = Form(...),
    photo: UploadFile | Literal[''] = File(''),
    type: Literal['one_time', 'trigger'] = Form(...),
    title: str | Literal[''] = Form('') ,
    button_text: str | Literal[''] = Form(''),
    button_url: str | Literal[''] = Form(''),
    is_active: bool = Form(True),
    triggers: TriggersData = Form(...),
    shedulet_at: datetime | Literal[''] = Form('')
):
    logger.debug(triggers)
    if type == 'one_time':
        if not shedulet_at:
            raise HTTPException(400, detail='Bad request: If set type is "one_time" field shedulet_at is required')
    return await CampaignTools.add(
        name=name,
        text=text,
        photo=photo if photo else None,
        type=type,
        title=title if title else None,
        is_active=is_active,
        button_text=button_text if button_text else None,
        button_url=button_url if button_url else None,
        triggers=triggers.model_dump()['triggers'],
        shedulet_at=shedulet_at if shedulet_at else None
    )
    
    
@router.patch('/{campaign_id}')
async def edit_campaign(
    campaign_id: int,
    name: str = Form(''),
    text: str = Form(''),
    photo: UploadFile | Literal[''] = File(''),
    type: Literal['one_time', 'trigger'] = Form(...),
    title: str | Literal[''] = Form('') ,
    button_text: str | Literal[''] = Form(''),
    button_url: str | Literal[''] = Form(''),
    triggers: TriggersData = Form(...),
    is_active: bool = Form(True),
    shedulet_at: datetime | Literal[''] = Form('')
):
    logger.debug(triggers)
    if type == 'one_time':
        if not shedulet_at:
            raise HTTPException(400, detail='Bad request: If set type is "one_time" field shedulet_at is required')
    try:
        return await CampaignTools.update(
            campaign_id=campaign_id,
            name=name if name else None,
            text=text if text else None,
            photo=photo if photo else None,
            type=type,
            is_active=is_active,
            title=title if title else None,
            button_text=button_text if button_text else None,
            button_url=button_url if button_url else None,
            triggers=triggers.model_dump()['triggers'],
            shedulet_at=shedulet_at if shedulet_at else None
        )
    except CustomDBExceptions as ex:
        raise HTTPException(400, detail=ex.message)


@router.delete('/{campaign_id}')
async def delete_campaign(campaign_id: int):
    try:
        await CampaignTools.delete(campaign_id)
        return JSONResponse(content={'detail': 'success'})
    except CustomDBExceptions as ex:
        raise HTTPException(400, detail=ex.message)


@router.get('/triggers')
async def get_triggers() -> list[Trigger]:
    return await CampaignTools.get_triggers()