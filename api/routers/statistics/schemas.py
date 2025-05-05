from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class RegistrationsStatistic(BaseModel):
    origin_users: int = 0
    referal_users: int = 0


class UsersStatistic(BaseModel):
    starts:         int = 0
    runs:           int = 0
    registrations:  int = 0
    activations:    int = 0


class TasksStatistic(BaseModel):
    started:    int = 0
    completed:  int = 0
    
    
class TicketsStatistic(BaseModel):
    received:   int = 0
    spent:      int = 0
    purshased:  int = 0


class GiveawaysStatistic(BaseModel):
    primary:    int = 0
    repeated:   int = 0


class DailyStatistic(BaseModel):
    registrations:  RegistrationsStatistic
    users:          UsersStatistic
    tasks:          TasksStatistic
    tickets:        TicketsStatistic
    giveaways:      GiveawaysStatistic
    

class StatisticData(BaseModel):
    data: dict[str, DailyStatistic] = Field(..., description='additionalProp* = Строка в формате "YYYY-MM-DD"')
    
    
class StatisticFilters(BaseModel):   
    # Баланс
    min_balance:        Optional[int] = None
    max_balance:        Optional[int] = None
    
    # Конкурс
    giveaway_id:         Optional[int] = None
    
    # Подписка
    gs_subscription:    Optional[Literal['FULL', 'PRO', 'LITE', 'UNSUBSCRIBED']] = None
    
    datetime_start:     Optional[str|datetime] = None
    datetime_end:       Optional[str|datetime] = None
