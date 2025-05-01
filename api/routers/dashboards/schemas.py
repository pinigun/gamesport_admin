from datetime import date
from pydantic import BaseModel, Field


class Trend(BaseModel):
    trend_value:        str = "0.00 %"
    trend_direction:    bool = True
    

class StatsParam(BaseModel):
    value: int = 0
    trend: Trend = Trend()


class UserStats(BaseModel):
    total:      StatsParam
    repeated:   StatsParam
    new:        StatsParam
    
    
class RegistrationsStats(BaseModel):
    origin:     StatsParam
    referals:   StatsParam


class TicketsStats(BaseModel):
    received:   StatsParam
    spent:      StatsParam
    

class TasksStats(BaseModel):
    started:    StatsParam = Field(default_factory=StatsParam)
    completed:  StatsParam = Field(default_factory=StatsParam)


class GeneralStats(BaseModel):
    users:          UserStats
    registrations:  RegistrationsStats
    tasks:          TasksStats
    tickets:        TicketsStats
    

class TasksGraphStats(BaseModel):
    id:         int
    title:      str
    started:    StatsParam = Field(default_factory=StatsParam)
    completed:  StatsParam = Field(default_factory=StatsParam)
        
    
class GiveawaysGraphStats(BaseModel):
    id: int
    name: str
    users_count: StatsParam = Field(default_factory=StatsParam)    
    
    
class GraphStats(BaseModel):
    data: dict[date, StatsParam]