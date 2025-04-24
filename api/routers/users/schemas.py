from datetime import datetime
from typing import Literal, Optional
from loguru import logger
from pydantic import BaseModel, ConfigDict, Field, field_validator, ValidationError

from config import FRONT_DATE_FORMAT, FRONT_TIME_FORMAT


class EditUserRequest(BaseModel):
    tg_id:              str | None = None
    phone:              str | None = None
    email:              str | None = None
    balance:            float | None = None
    deleted:            bool | None = None
    password:           str | None = None


class UserResponse(BaseModel):
    id: int
    created_at:         str | datetime
    tg_id:              str | None
    phone:              str | None
    email:              str | None
    balance:            float | None = None
    giveaways_count:    int
    gs_subscription:    Literal['FULL', 'PRO', 'LITE', 'UNSUBSCRIBED']
    
    # Unsupported
    gs_id:              int | None = None
    completed_tasks:    int | None = None
    referals_count:     int = 0
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator("created_at")
    def validate_login(cls, value: str | datetime):
        if isinstance(value, datetime):
            return value.strftime(format=f"{FRONT_DATE_FORMAT} {FRONT_TIME_FORMAT}")
        return value
    
    
class UsersData(BaseModel):
    total_items:    int
    total_pages:    int
    per_page:       int
    current_page:   int
    
    items:          list[UserResponse]
    

class UserFilters(BaseModel):
    # Поиск
    tg_id:              Optional[str] = None
    email:              Optional[str] = None
    phone:              Optional[str] = None
    
    # Баланс
    min_balance:        Optional[int] = None
    max_balance:        Optional[int] = None
    
    # Конкурс
    giveway_id:         Optional[int] = None
    
    # Подписка
    gs_subscription:       Optional[Literal['FULL', 'PRO', 'LITE', 'UNSUBSCRIBED']] = None
    
    created_at_start:   Optional[str|datetime] = None
    created_at_end:     Optional[str|datetime] = None
    