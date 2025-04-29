from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator

from config import FRONT_DATE_FORMAT, FRONT_TIME_FORMAT


class Task(BaseModel):
    id: int
    title: str
    reward: int
    started: int
    completed: int
    check_type: str | None
    is_active: bool
    created_at: str

    model_config = ConfigDict(from_attributes=True)
    
    @field_validator("created_at", mode='before')
    def validate_login(cls, value: str | datetime):
        if isinstance(value, datetime):
            return value.strftime(format=f"{FRONT_DATE_FORMAT} {FRONT_TIME_FORMAT}")
        return value


class TasksData(BaseModel):
    total_items:    int
    total_pages:    int
    per_page:       int
    current_page:   int
    
    items:          list[Task]