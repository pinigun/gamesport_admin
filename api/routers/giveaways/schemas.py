from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Giveaway(BaseModel):
    id:             int
    start_date:     str
    number:         int
    period_days:    Optional[int] = None
    name:           str
    price:          int
    active:         bool
    winner_id:      Optional[int] = None
    coalesce:       int
    spent_tickets:  int
    photo:          Optional[str] = None

    @model_validator(mode='before')
    def format_start_date(cls, values):
        if 'start_date' in values:
            start_date = values['start_date']
            try:
                # Форматируем в новый формат
                values['start_date'] = datetime.strftime(start_date, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                raise ValueError(f"Invalid start_date format: {start_date}")
        return values


class GiveawaysData(BaseModel):
    total_items:    int
    total_pages:    int
    per_page:       int
    current_page:   int
    
    items:          list[Giveaway]