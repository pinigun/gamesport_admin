from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger
from campaign_scheduler.campaign import Campaign
from campaign_scheduler.custom_types import CampaignDTO, TriggerDTO
from .db_interface import db

class CampaignScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()
        self.scheduler.add_job(
            self.sync_db,
            IntervalTrigger(minutes=1),
            id="sync_database",
            replace_existing=True
        )


    async def schedule_campaign(self, campaign: Campaign):
        job_id = f"{campaign.id}"
        trigger = CronTrigger.from_crontab(campaign.cron_expression) if campaign.type == 'trigger' else DateTrigger(campaign.shedulet_at if campaign.shedulet_at > datetime.now() + timedelta(minutes=1) else datetime.now() + timedelta(minutes=1))
        logger.debug('Запланировали таску')
        self.scheduler.add_job(
            campaign.run,
            trigger=trigger,
            id=job_id,
            replace_existing=True
        )
        
    
    async def sync_db(self):
        logger.debug('Запустили синхронизацию')
        campaigns = await db.get_all(is_active=True)
        current_jobs = self.scheduler.get_jobs()
        current_campaigns_ids = [str(dict(campaign)["id"]) for campaign in campaigns]
        for job in current_jobs:
            if job.id != 'sync_database':
                if job.id not in current_campaigns_ids:
                    self.scheduler.remove_job(str(job.id))
            
        logger.debug(campaigns)
        for campaign in campaigns:
            campaign = dict(campaign)
            triggers = campaign.pop('triggers')
            await self.schedule_campaign(
                Campaign(
                    campaign=CampaignDTO(
                        **campaign,
                        triggers=[
                            TriggerDTO(**trigger)
                            for trigger in triggers
                        ]
                    )
                )
            )
        
        
# class CampaignScheduler:
#     def __init__(self):
#         self.scheduler = AsyncIOScheduler()
#         self.scheduler.start()

#     async def schedule_campaign(self, campaign: Campaign):
#         job_id = f"campaign_{campaign.id}"
#         cron = CronTrigger.from_crontab(campaign.cron_expression)
#         logger.debug('Запланировали таску')
#         self.scheduler.add_job(
#             campaign.run,
#             cron,
#             id=job_id,
#             replace_existing=True
#         )

#     def remove_campaign(self, campaign_id: int):
#         job_id = f"campaign_{campaign_id}"
#         self.scheduler.remove_job(job_id)

