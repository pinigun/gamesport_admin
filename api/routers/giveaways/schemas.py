from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator
from database.models import Giveaway as GivewayDBModel

from config import BASE_ADMIN_URL


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
    photo:              Optional[str] = None

    @model_validator(mode='before')
    def format_start_date(cls, values):
        if isinstance(values, GivewayDBModel):
            start_date = values.start_date
            if start_date:
                try:
                    # Форматируем в новый формат
                    values.start_date = datetime.strftime(start_date, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    raise ValueError(f"Invalid start_date format: {start_date}")
            if values.photo is not None:
                values.photo = f'{BASE_ADMIN_URL}/{values.photo}'
        elif 'start_date' in values:
            start_date = values['start_date']
            if start_date:
                try:
                    # Форматируем в новый формат
                    values['start_date'] = datetime.strftime(start_date, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    raise ValueError(f"Invalid start_date format: {start_date}")
            photo = values.get('photo')
            if photo is not None:
                values['photo'] = f'{BASE_ADMIN_URL}/{photo}'
        return values
    

    model_config = ConfigDict(from_attributes=True)


class GiveawaysData(BaseModel):
    total_items:    int
    total_pages:    int
    per_page:       int
    current_page:   int
    
    items:          list[Giveaway]
    

