from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator

from config import BASE_ADMIN_URL, FRONT_DATE_FORMAT, FRONT_TIME_FORMAT


CHECK_TYPES_MAP = {
    'auto': 'Автоматический',
    'manual': 'Ручной',
    'gs': 'GameSport',
    'app': 'Драйвер',
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
    started:        int
    completed:      int
    description:    str | None
    check_type:     str | None
    is_active:      bool
    created_at:     str
    photo:          str | None

    model_config = ConfigDict(from_attributes=True)
    
    @field_validator("created_at", mode='before')
    def check_date(cls, value: str | datetime):
        if isinstance(value, datetime):
            return value.strftime(format=f"{FRONT_DATE_FORMAT} {FRONT_TIME_FORMAT}")
        return value
    
    @field_validator("check_type", mode='before')
    def validate_check_type(cls, value: str | None):
        if value is not None:
            value = CHECK_TYPES_MAP[value]
        return value
    
    
    @field_validator('photo', mode='before')
    def format_photo_url(cls, value):
        if value is not None:
            value = f'{BASE_ADMIN_URL}/{value}'
        return value


class TasksData(BaseModel):
    total_items:    int
    total_pages:    int
    per_page:       int
    current_page:   int
    
    items:          list[Task]