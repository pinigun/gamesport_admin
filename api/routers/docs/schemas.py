from pydantic import BaseModel, ConfigDict

from custom_types import DocsStatuses


class DocsRequest(BaseModel):
    name:       str
    text:       str
    status:     DocsStatuses


class DocsResponse(BaseModel):
    id:         int
    name:       str
    text:       str
    status:     DocsStatuses
    position:   int
    
    model_config = ConfigDict(from_attributes=True)


class DocsData(BaseModel):
    total_items:    int
    total_pages:    int
    per_page:       int
    current_page:   int
    
    items:          list[DocsResponse]
    
    
class SwapDocsRequest(BaseModel):    
    first_doc_id:   int
    second_doc_id:  int