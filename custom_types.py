from enum import Enum


class PermissionsTags(str, Enum):
    ADMINS = 'admins'
    USERS = 'users'
    FAQ = 'faq'
    

class AdminStatuses(str, Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'  
    
    
class FAQStatuses(str, Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive' 
    
class DocsStatuses(str, Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive' 