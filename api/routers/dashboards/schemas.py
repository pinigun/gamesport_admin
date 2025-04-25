from pydantic import BaseModel


class UserStats(BaseModel):
    total:      int = 0
    repeated:   int = 0
    new:        int = 0
    
    
class RegistrationsStats(BaseModel):
    origin:     int = 0
    referals:   int = 0


class TicketsStats(BaseModel):
    received:   int = 0
    spent:      int = 0
    

class TasksStats(BaseModel):
    started:   int = 0
    completed:      int = 0


class GeneralStats(BaseModel):
    users:          UserStats
    registrations:  RegistrationsStats
    tasks:          TasksStats
    tickets:        TicketsStats