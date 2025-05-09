import asyncio
from datetime import datetime
from typing import Literal, NamedTuple
from campaign_scheduler.campaign_sheduler import CronTrigger
from campaign_scheduler.custom_types import CampaignDTO, TriggerDTO
from campaign_scheduler.triggers import CampaignTrigger, TelegramUserID, TriggersMap
from loguru import logger
from tools.telegram import TelegramTools, TelegramButton
from .db_interface import db


class CampaignMessage(NamedTuple):
    text: str
    photo: str | None
    button: TelegramButton
    

class Campaign:
    def __init__(self, campaign: CampaignDTO):
        if not isinstance(campaign, CampaignDTO):
            raise TypeError("Type should been is 'CampaignDTO'")
        
        self.id:                int = campaign.id
        self.type:              Literal['one_time', 'trigger'] = campaign.type
        self.shedulet_at:       datetime = campaign.shedulet_at
        self.triggers:          list[TriggerDTO] = self.get_triggers(campaign.triggers)
        self.message:           CampaignMessage = self.prepare_message(campaign)
        self.cron_expression:   str = self.get_min_trigger_cron_expression()
        
    
    def get_triggers(
        self,
        triggers: list[TriggerDTO]
    ) -> list[CampaignTrigger]:
        return [
            TriggersMap[trigger.id](
                id=trigger.id,
                name=trigger.name,
                trigger_params=trigger.trigger_params,
                cron_expression=trigger.cron_expression
            )
            for trigger in triggers
        ] 
        
        
    async def run(self) -> None:
        logger.info(f'[CAMPAIGN:{self.id}] Получаем пул юзеров для отправки рассылки')
        users_pool: set[TelegramUserID] = set()
        users_pool: set[TelegramUserID] = await self.triggers[0].get_users_pull()
        for trigger in self.triggers[1:]:
            if self.type == 'trigger':
                users_pool.update(await trigger.get_users_pull())
            elif self.type == 'one_time':
                users_pool = users_pool.intersection(await trigger.get_users_pull())    
        logger.info(f'[CAMPAIGN:{self.id}] Получили пул юзеров {len(users_pool)=}')
        
        logger.info(f'[CAMPAIGN:{self.id}] Запускаем отправку сообщений')
        campaign_results = await asyncio.gather(
            *[
                self.send_message(
                    chat_id=int(user_id),
                    
                )
                for user_id in users_pool
            ]
        )
        logger.info(f'[CAMPAIGN:{self.id}] Отправлено сообщений: {sum(campaign_results)} из {len(users_pool)}')
        if self.type == 'one_time':
            await db.update(campaign_id=self.id, is_active=False)
    
    def prepare_message(self, campaign: CampaignDTO) -> CampaignMessage:
        return CampaignMessage(
            text=f"{f'<b>{campaign.title}</b>\n' if campaign.title else ''}{campaign.text}",
            button=TelegramButton(
                text=campaign.button_text,
                url=campaign.button_url
            ) if campaign.button_text and campaign.button_url else None,
            # photo=campaign.photo
            photo="https://app.gamesport.com/api/static/giveaways/44/56.webp"
        )
        

    async def send_message(self, chat_id: int):
        return await TelegramTools.send_message(
            chat_id=chat_id,
            text=self.message.text,
            photo_url=self.message.photo,
            button=self.message.button
        )
        
    
    def get_min_trigger_cron_expression(self):
        """
        Возвращает cron-выражение и ближайшее время его срабатывания.

        :param crons: список cron-выражений
        :param now: текущее время (по умолчанию — datetime.now())
        :return: (cron-выражение, ближайшее время запуска)
        """
        now = datetime.now()

        fire_times = [
            (trigger.cron_expression, CronTrigger.from_crontab(trigger.cron_expression).get_next_fire_time(None, now))
            for trigger in self.triggers
        ]

        return min(fire_times, key=lambda x: x[1])[0]