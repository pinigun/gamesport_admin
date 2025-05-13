from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Literal


@dataclass
class TriggerDTO:
    id:                 int
    name:               int
    cron_expression:    str
    trigger_params:     dict[str, Any]


@dataclass
class CampaignDTO:
    id:                 int
    name:               str
    type:               Literal['one_time', 'trigger']
    title:              str | None 
    text:               str
    button_text:        str | None
    button_url:         str | None
    photo:              str | None
    timer:              timedelta | None
    is_active:          bool
    shedulet_at:        datetime | None
    created_at:         datetime
    triggers:           list[TriggerDTO]