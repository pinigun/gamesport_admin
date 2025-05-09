from api.routers.campaign.schemas import CampaignResponse, Trigger
from database import db
from tools.photos import PhotoTools


class CampaignTools:
    async def get_count():
        return await db.campaigns.get_count()
    
    
    async def get_all(page: int, per_page: int) -> list[CampaignResponse]:
        return [
            CampaignResponse.model_validate(campaign)
            for campaign in await db.campaigns.get_all(page, per_page)
        ]
        
    
    async def get_triggers() -> list[Trigger]:
        return [
            Trigger.model_validate(trigger)
            for trigger in await db.campaigns.get_triggers()
        ]
        
    async def add(**campaign_data):
        photo = campaign_data.pop('photo')
        new_campaign = await db.campaigns.add(campaign_data)
        if photo:
            campaign_data['photo'] = await PhotoTools.save_photo(
                path="static/campaigns/",
                photo=photo
            )
            new_campaign = await db.campaigns.update(
                campaign_id=new_campaign.id,
                photo=campaign_data.get('photo')
            )
        return CampaignResponse.model_validate(new_campaign)