import jwt
from fastapi import Depends, HTTPException
from typing import NamedTuple
from custom_types import PermissionsTags
from database.exceptions import AdminNotFound
from api.routers.admins.tools.admins import db
from api.routers.auth.schemas import LogInModel
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# from config import HASH_SECRET_KEY
HASH_SECRET_KEY = "PT1bj08S0YAe"
JWTToken = str


security = HTTPBearer(auto_error=False)


class AuthData(NamedTuple):
    admin_data:   int
    jwt_token:  JWTToken


class JWTTools:
    @staticmethod
    def generate_jwt(data: dict):
        return jwt.encode(data, HASH_SECRET_KEY, algorithm="HS256")

    
    @staticmethod
    def decode_jwt(token: str | bytes):
        return jwt.decode(token, HASH_SECRET_KEY, algorithms=["HS256"])


class AuthTools:   
    async def auth(auth_data: LogInModel) -> AuthData:
        admin = await db.admins.get_admin(
            **auth_data.get_filter_data()
        )

        if not admin:
            raise AdminNotFound(message='Invalid login or password')
        
        token_data = {
            'admin': {
                'id': admin.id
            }
        }
        return AuthData(
            admin_data=token_data,
            jwt_token=JWTTools.generate_jwt(
                data=token_data
            )
        )
    
    
    def check_permissions(permission_tag: PermissionsTags):
        async def wrapper(
            credentials: HTTPAuthorizationCredentials = Depends(security)
        ):
            try:
                token_data = JWTTools.decode_jwt(token=credentials.credentials)
            except:
                raise HTTPException(403, detail='Invalid token')
            admin = await db.admins.get_admin(
                load_roles=True,
                id=token_data['admin']['id']
            )
            
            permissions = await db.admins.get_all_permissions(
                roles_ids=[role.id for role in admin.roles],
                tag=permission_tag.value
            )
            if not permissions:
                raise HTTPException(
                    status_code=403, 
                    detail=f"Access denied to section '{permission_tag.value}'"
                )
        return wrapper
        
        
        
        
    
        
def main():
    token = JWTTools.generate_jwt(
        {
            "user": {
                'id': 1,
                'roles': [1, 2],
            }     
        }
    )
    
    print(JWTTools.decode_jwt(token))
    

if __name__ == '__main__':
    main()