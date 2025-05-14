from dataclasses import dataclass


@dataclass
class CustomDBExceptions(Exception):
    message: str
    

@dataclass
class RoleNotFound(CustomDBExceptions):
    message: str = "Role not found"


@dataclass
class PermissionsNotFound(CustomDBExceptions):
    message: str = "Permissions not found"   


@dataclass
class AdminNotFound(CustomDBExceptions):
    message: str = "Admin not found"   


@dataclass
class FAQNotFound(CustomDBExceptions):
    message: str = 'FAQ (id={faq_id}) not found'
    
    
@dataclass
class DocsNotFound(CustomDBExceptions):
    message: str = 'Docs (id={faq_id}) not found'
    

@dataclass
class UserNotFound(CustomDBExceptions):
    message: str = "User not found"   
    
    
@dataclass
class ForeignKeyError(CustomDBExceptions):
    message: str
    

@dataclass
class CampaignNotFoundException(CustomDBExceptions):
    message: str