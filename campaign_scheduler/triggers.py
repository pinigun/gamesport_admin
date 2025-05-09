from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
from .db_interface import db
from loguru import logger


TelegramUserID = int


@dataclass
class CampaignTrigger(ABC):
    id:                 int
    name:               str
    trigger_params:     dict[str, Any] | None
    cron_expression:    str
    
    @abstractmethod
    async def get_users_pull() -> list[TelegramUserID]:
        ...
        

class EverydayRewardTrigger(CampaignTrigger):
    '''Не забрал ежедневную награду'''
    async def get_users_pull(self) -> list[TelegramUserID]:
        users_pool = await db.get_evryday_reward_users_pool()
        logger.debug(f'EverydayRewardTrigger: {users_pool=}')
        
        # FIXME моковые данные
        users_pool = ['350352378']       
        users_pool = list(map(int, users_pool))
        return users_pool
    
    
class FirstPredictTrigger(CampaignTrigger):
    '''Получил первый прогноз'''
    ...
    
    
class UserInactivityTrigger(CampaignTrigger):
    '''Не заходил N дней'''
    async def get_users_pull(self) -> list[TelegramUserID]:
        users_pool = await db.get_users_inactive(inactive_days=self.trigger_params['inactive_days'])
        logger.debug(f'UserInactivityTrigger: {users_pool=}')
        
        # FIXME моковые данные
        users_pool = ['350352378']       
        users_pool = list(map(int, users_pool))
        return users_pool
    
    
class UserUncompleteTaskTrigger(CampaignTrigger):
    '''Не выполнил задачу'''
    async def get_users_pull(self):
        users_pool = await db.get_uncomplete_task_users_pool(task_id=self.trigger_params['task_id'])
        logger.debug(f'UserUncompleteTaskTrigger: {users_pool=}')
        
        # FIXME моковые данные
        users_pool = ['350352378']       
        users_pool = list(map(int, users_pool))
        return users_pool
    
    
class GiveawayEndingSoonTrigger(CampaignTrigger):
    '''Конкурс закночится через ...'''
    ...
    
    
class NotParticipationInGiveawayTrigger(CampaignTrigger):
    '''Не учавствовал в конкурсе'''
    ...
    
    
TriggersMap = {
    1: EverydayRewardTrigger,
    2: FirstPredictTrigger,
    3: UserInactivityTrigger,
    4: UserUncompleteTaskTrigger,
    5: GiveawayEndingSoonTrigger,
    6: NotParticipationInGiveawayTrigger
}
    
    
