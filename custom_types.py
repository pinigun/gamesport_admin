from enum import Enum


class PermissionsTags(str, Enum):
    ADMINS = 'admins'
    USERS = 'users'
    

class AdminStatuses(str, Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'  