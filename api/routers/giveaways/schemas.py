from datetime import date, datetime
from enum import Enum
from typing import Any, Literal, Optional
from loguru import logger
from pydantic import BaseModel, ConfigDict, Field, model_validator
from database.models import Giveaway as GivewayDBModel
import json
from config import BASE_ADMIN_URL


class GiveawayPrize(BaseModel):
    id: int
    name: str | None
    photo: str | None
    position: int | None
    
    model_config = ConfigDict(from_attributes=True)


class GiveawayParticiptant(BaseModel):
    id:         int
    email:      str | None
    phone:      str | None
    tg_id:      str | None
    vk_id:      str | None
    prize_id:   int | None
    prize_name: str | None
    
    model_config = ConfigDict(from_attributes=True)


# class GiveawayWinner(GiveawayParticiptant):
#     id: int
#     email: str | None
#     phone: str | None
#     tg_id: int | None
#     prize_id: int
#     prize_name: str | None


class GiveawaysRecordsTypes(str, Enum):
    RUNNING = 'Идет'
    PENDING = 'Ожидается'
    FINISHED = 'Завершен'
    

class GiveawayHistoryRecord(BaseModel):
    id:                 int
    start_date:         str | None
    end_date:           str | None
    number:             int
    status:             GiveawaysRecordsTypes
    participants_count: int = 0
    price:              int
    spent_tickets:      int = 0
    winners:            list[GiveawayParticiptant] | None
   
    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode='before')
    def validation(cls, values):
        if isinstance(values, dict):
            start_date: datetime = values.get('start_date')
            end_date: datetime = values.get("end_date")
            if end_date is None:
                if start_date.replace(tzinfo=None) > datetime.now().replace(tzinfo=None):
                    values['status'] = GiveawaysRecordsTypes.PENDING
                else:
                    values['status'] = GiveawaysRecordsTypes.RUNNING
            else:
                values['status'] = GiveawaysRecordsTypes.FINISHED
                 
            if start_date:
                try:
                    # Форматируем в новый формат
                    values['start_date'] = datetime.strftime(start_date, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    raise ValueError(f"Invalid start_date format: {start_date}")
            if end_date:
                try:
                    # Форматируем в новый формат
                    values['end_date'] = datetime.strftime(end_date, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    raise ValueError(f"Invalid end_date format: {end_date}")
        return values


class Giveaway(BaseModel):
    id:                 int
    start_date:         str
    number:             int
    period_days:        Optional[int] = None
    name:               str
    price:              int
    active:             bool
    winner_id:          Optional[int] = None
    participants_count: int = 0
    spent_tickets:      int = 0
    
    model_config = ConfigDict(from_attributes=True, extra='allow')

    @model_validator(mode='before')
    def validation(cls, values):
        if isinstance(values, GivewayDBModel):
            start_date = values.start_date
            if start_date:
                try:
                    # Форматируем в новый формат
                    values.start_date = datetime.strftime(start_date, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    raise ValueError(f"Invalid start_date format: {start_date}")
        elif isinstance(values, dict):
            start_date = values.get('start_date')
            end_date = values.get("end_date")
            if start_date:
                try:
                    # Форматируем в новый формат
                    values['start_date'] = datetime.strftime(start_date, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    raise ValueError(f"Invalid start_date format: {start_date}")
            if end_date:
                try:
                    # Форматируем в новый формат
                    values['end_date'] = datetime.strftime(start_date, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    raise ValueError(f"Invalid end_date format: {end_date}")
        return values


class Prize(BaseModel):
    id:         int | None = None
    name:       str
    position:   int = Field(gt=0, description="Start from 1")


class PrizesData(BaseModel):
    prizes: list[Prize]
    
    @model_validator(mode='before')
    def validation(cls, values):
        if isinstance(values, str):
            values = json.loads(values)
            logger.debug(type(values))
        return values


class GivewayPrizesData(BaseModel):
    total_items:    int
    total_pages:    int
    per_page:       int
    current_page:   int
    
    items:          list[GiveawayPrize]


class GiveawaysData(BaseModel):
    total_items:    int
    total_pages:    int
    per_page:       int
    current_page:   int
    
    items:          list[Giveaway]
    

class GiveawaysHistoryData(BaseModel):
    total_items:    int
    total_pages:    int
    per_page:       int
    current_page:   int
    
    items:          list[GiveawayHistoryRecord]
    
    
class GivewayParticipantsData(BaseModel):
    total_items:    int
    total_pages:    int
    per_page:       int
    current_page:   int
    
    items:          list[GiveawayParticiptant]


class GiveawayRequest(BaseModel):
    name:           str
    active:         bool
    start_date:     date = Field(..., description='YYYY-MM-DD')
    period_days:    int = Field(..., ge=0)
    price:          int = Field(..., ge=0)


class PrizeRequest(BaseModel):
    name:       str
    photo:      str 
    position:   str = Field(..., gt=0)
