from loguru import logger
from api.routers.campaign.schemas import CampaignResponse, Trigger
from database import db
from tools.photos import PhotoTools


class CampaignTools:
    async def delete(campaign_id: int):
        await db.campaigns.delete(campaign_id)
    
    
    async def get_count():
        return await db.campaigns.get_count()
    
    
    async def get_all(
        page: int,
        per_page: int,
        order_by: str,
        order_direction: str,
        **filters
    ) -> list[CampaignResponse]:
        return [
            CampaignResponse.model_validate(campaign)
            for campaign in await db.campaigns.get_all(
                page=page,
                per_page=per_page,
                order_by=order_by,
                order_direction=order_direction,
                **filters
            )
        ]
        
    
    async def get_triggers() -> list[Trigger]:
        return [
            Trigger.model_validate(trigger)
            for trigger in await db.campaigns.get_triggers()
        ]
        
        
    async def add(**campaign_data):
        photo = campaign_data.pop('photo')
        new_campaign = await db.campaigns.add(campaign_data)
        logger.debug(new_campaign)
        if photo:
            campaign_data['photo'] = await PhotoTools.save_photo(
                path=f"static/campaigns/{new_campaign.id}",
                photo=photo
            )
            new_campaign = await db.campaigns.update(
                campaign_id=new_campaign.id,
                photo=campaign_data.get('photo'),
                triggers=new_campaign.triggers,
            )
        return CampaignResponse.model_validate(new_campaign)
    
    
    async def update(campaign_id: int, **campaign_data):
        campaign_data = {key: value for key, value in campaign_data.items() if value is not None and value != ''}
        photo = campaign_data.pop('photo', None)
        if photo:
            campaign_data['photo'] = await PhotoTools.save_photo(
                path=f"static/campaigns/{campaign_id}",
                photo=photo
            )
        campaign = await db.campaigns.update(
            campaign_id=campaign_id,
            **campaign_data
        )
        return CampaignResponse.model_validate(campaign)
        