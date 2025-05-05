from datetime import datetime, timedelta
from pydantic import BaseModel, ConfigDict, field_validator

from config import BASE_ADMIN_URL, FRONT_DATE_FORMAT, FRONT_TIME_FORMAT


CHECK_TYPES_MAP = {
    'auto': 'Автоматический',
    'manual': 'Ручной',
    'gs': 'GameSport',
    'app': 'Драйвер',
    'timer': 'Таймер'
}   


class TaskParticipant(BaseModel):
    task_id:            int
    user_id:            int
    completed:          bool
    completed_tasks:    int
    email:              str | None
    phone:              str | None
    tg_username:        str | None
    tg_id:              str | None
    
    model_config = ConfigDict(from_attributes=True)


class Task(BaseModel):
    id:             int
    title:          str
    reward:         int
    giveaway_id:    int | None
    started:        int
    completed:      int
    description:    str | None
    redirect_url:   str | None
    is_active:      bool
    check_type:     str | None
    timer:          str | None
    postback_url:   str | None
    created_at:     str
    photo:          str | None
    
    
    @field_validator("created_at", mode='before')
    def check_date(cls, value: str | datetime):
        if isinstance(value, datetime):
            return value.strftime(format=f"{FRONT_DATE_FORMAT} {FRONT_TIME_FORMAT}")
        return value
    
    
    @field_validator('photo', mode='before')
    def format_photo_url(cls, value):
        if value is not None:
            value = f'{BASE_ADMIN_URL}/{value}'
        return value
    
    
    @field_validator('timer', mode='before')
    def format_timer(cls, value):
        if isinstance(value, timedelta):
            total_seconds = int(value.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours:02}:{minutes:02}:{seconds:02}"
        return value


class TasksData(BaseModel):
    total_items:    int
    total_pages:    int
    per_page:       int
    current_page:   int
    
    items:          list[Task]
    
    
class SupportedGiveaway(BaseModel):
    id: int
    name: str
    
    model_config = ConfigDict(from_attributes=True)