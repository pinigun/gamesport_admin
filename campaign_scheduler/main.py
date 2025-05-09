import asyncio

from loguru import logger
from campaign_scheduler.campaign_sheduler import CampaignScheduler
logger.debug('Теееееест12')


async def main():
    campaign_sheduler = CampaignScheduler()
    logger.info('Запустили шедулер')
    await campaign_sheduler.sync_db()
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())