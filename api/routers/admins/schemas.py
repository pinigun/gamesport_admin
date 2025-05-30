from typing import Literal
from custom_types import AdminStatuses
from pydantic import BaseModel, ConfigDict


class RolePermissionResponse(BaseModel):
    id:     int
    name:   str
    
    model_config = ConfigDict(from_attributes=True)
    
    
class Role(BaseModel):
    id:             int
    name:           str
    
    model_config = ConfigDict(from_attributes=True)
  
  
class RoleResponse(Role):
    permissions:    list[RolePermissionResponse]
    

class RolePermissionAction(BaseModel):
    permission_id:  int
    action:         Literal['add', 'delete']
  
    
class RoleRequest(BaseModel):
    name:               str
    permission_ids:    list[int]
    

class AdminRequest(BaseModel):
    first_name:     str
    last_name:      str
    middle_name:    str | None = None
    email:          str
    phone_number:   str
    password:       str
    role_ids:       list[int]   
    status:         AdminStatuses
    
    
class EditAdminRequest(BaseModel):
    first_name:     str | None = None
    last_name:      str | None = None
    middle_name:    str | None = None
    email:          str | None = None
    phone_number:   str | None = None
    password:       str | None = None
    role_ids:       list[int]
    status:         AdminStatuses
    

class AdminResponse(BaseModel):
    id: int
    first_name:     str
    last_name:      str
    middle_name:    str | None = None
    email:          str
    phone_number:   str
    status:         Literal['active', 'inactive']
    roles:          list[Role]
    
    model_config = ConfigDict(from_attributes=True)
    

class AdminsData(BaseModel):
    total_items:    int
    total_pages:    int
    per_page:       int
    current_page:   int
    
    items:          list[AdminResponse]