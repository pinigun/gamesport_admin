from pydantic import BaseModel, ConfigDict


class Task(BaseModel):
    id: int
    name: str
    reward: int
    started: int
    completed: int
    check_type: str
    active: bool

    model_config = ConfigDict(from_attributes=True)


class TasksData(BaseModel):
    total_items:    int
    total_pages:    int
    per_page:       int
    current_page:   int
    
    items:          list[Task]