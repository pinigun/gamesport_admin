from datetime import datetime
from typing import Literal, Optional
from loguru import logger
from pydantic import BaseModel, ConfigDict, Field, field_validator, ValidationError, model_validator

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
    gs_id:              int | None = None
    created_at:         str | datetime
    days_in_project:    int
    tg_id:              str | None
    username:           str | None
    phone:              str | None
    email:              str | None
    balance:            float | None = None
    giveaways_count:    int
    gs_subscription:    Literal['FULL', 'PRO', 'LITE', 'UNSUBSCRIBED']
    completed_tasks:    int = 0
    referals_count:     int = 0
    deleted:            bool
    
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator("created_at")
    def validate_login(cls, value: str | datetime):
        if isinstance(value, datetime):
            return value.strftime(format=f"{FRONT_DATE_FORMAT} {FRONT_TIME_FORMAT}")
        return value
    
    @model_validator(mode='before')
    def model_validate(cls, values):
        created_at = values.get('created_at')
        
        # Преобразование created_at в datetime, если это строка
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        # Вычисление days_in_project
        days_in_project = (datetime.now() - created_at).days
        
        values['days_in_project'] = days_in_project
        
        return values
    
    
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
    