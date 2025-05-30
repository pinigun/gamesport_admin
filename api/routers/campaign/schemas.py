from datetime import datetime, timedelta
import json
from typing import Literal
from loguru import logger
from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from config import BASE_ADMIN_URL, FRONT_DATE_FORMAT, FRONT_TIME_FORMAT


class Trigger(BaseModel):
    id: int
    name: str
    trigger_params: dict | None
    
    model_config = ConfigDict(from_attributes=True)
    
    
class TriggerWithParams(Trigger):
    trigger_params: dict | None
    
   
class TriggerRequest(BaseModel):
    id: int
    trigger_params: dict | None
    
    
class TriggersData(BaseModel):
    triggers: list[TriggerRequest]    
    
    @model_validator(mode='before')
    def validation(cls, values):
        if isinstance(values, str):
            values = json.loads(values)
            for key, value in values.items():
                values[key] = None if value == None or not value or value =='null' else value
            logger.debug(type(values))
        return values
    
    
class CampaignResponse(BaseModel):
    id:                 int
    name:               str
    type:               Literal['one_time', 'trigger']
    title:              str | None 
    text:               str
    button_text:        str | None
    button_url:         str | None
    photo:              str | None
    timer:              timedelta | None
    sent:               int = 0
    received:           int = 0
    is_active:          bool
    shedulet_at:        datetime | None
    created_at:         datetime | None
    triggers:           list[TriggerWithParams]
    
    model_config = ConfigDict(from_attributes=True)
    
    
    @field_validator('photo', mode='before')
    def format_photo_url(cls, value):
        if value is not None:
            value = f'{BASE_ADMIN_URL}/{value}'
        return value
    
    
    @field_validator("created_at", mode='before')
    def check_date(cls, value: str | datetime):
        if isinstance(value, datetime):
            return value.strftime(format=f"{FRONT_DATE_FORMAT} {FRONT_TIME_FORMAT}")
        return value
    
    
class CampaignsData(BaseModel):
    total_items:    int
    total_pages:    int
    per_page:       int
    current_page:   int
    
    items:          list[CampaignResponse]
    
    
class ButtonData(BaseModel):
    text:    str | None
    url:     str | None