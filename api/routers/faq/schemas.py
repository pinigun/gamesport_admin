from pydantic import BaseModel, ConfigDict

from custom_types import FAQStatuses


class FAQRequest(BaseModel):
    question:   str
    answer:     str
    status:     FAQStatuses


class FAQResponse(BaseModel):
    id:         int
    question:   str
    answer:     str
    status:     FAQStatuses
    position:   int
    
    model_config = ConfigDict(from_attributes=True)


class FAQData(BaseModel):
    total_items:    int
    total_pages:    int
    per_page:       int
    current_page:   int
    
    items:          list[FAQResponse]
    
    
class SwapFAQRequest(BaseModel):    
    first_faq_id:   int
    second_faq_id:  int