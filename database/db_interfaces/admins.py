from dataclasses import dataclass
from typing import Literal

from database.exceptions import AdminNotFound, PermissionsNotFound, RoleNotFound
from database.db_interface import BaseInterface
from sqlalchemy import and_, select
from sqlalchemy.orm import joinedload, selectinload
from database.models import (
    Admin,
    AdminRole,
    AdminRoleLink,
    AdminRolePermissions,
    AdminRolePermissionLink,
)


class AdminsDBInterface(BaseInterface):
    def __init__(self, session_):
        super().__init__(session_ = session_)
   
    
    async def get_admin(
        self, 
        load_roles: bool = False,
        **filter
    ) -> Admin:
        return await self.get_row(
            Admin,
            load_relations=[Admin.roles] if load_roles else None,
            **filter
        )
    
    
    async def edit(self, admin_id: int, admin_data: dict):
        async with self.async_ses() as session:
            # Получаем роль и её текущие доступы
            result = await session.execute(
                select(Admin)
                .where(Admin.id == admin_id)
                .options(selectinload(Admin.roles))  # загружаем связанные доступы
            )
            admin = result.unique().scalar_one_or_none()
            if not admin:
                raise AdminNotFound

            role_ids = admin_data.pop('role_ids')            
            
            # Обновляем поля
            for key, value in admin_data.items():
                setattr(admin, key, value)

            # Получаем новые объекты Permission по их ID
            result = await session.execute(
                select(AdminRole)
                .where(
                    AdminRole.id.in_(role_ids)
                )
            )
            new_roles = result.scalars().all()

            # Обновляем связи
            admin.roles.clear()  # удаляем все старые связи
            admin.roles.extend(new_roles)  # добавляем новые

            await session.commit()
            return admin
    
    
    async def delete(self, admin_id: int) -> Literal[True]:
        return await self.delete_rows(
            Admin,
            id=admin_id
        )
   
   
    async def get_all(self, page: int, per_page: int):
        return await self.get_rows(
            Admin,
            offset=(page - 1) * per_page,
            limit=per_page,
            load_relations=[Admin.roles]
        )

    
    async def get_count(self):
        return await self.get_rows_count(Admin)
   
   
    async def get_all_permissions(self, roles_ids: list[int], **filter):
        if not roles_ids:
            return await self.get_rows(
                AdminRolePermissions,
                **filter
            )
        
        async with self.async_ses() as session:
            permissions_ids = await session.execute(
                select(AdminRolePermissionLink.permission_id)
                .where(AdminRolePermissionLink.role_id.in_(roles_ids))
            )
            permissions_ids = permissions_ids.scalars().all()
            
            result = await session.execute(
                select(AdminRolePermissions)
                .where(AdminRolePermissions.id.in_(permissions_ids))
                .filter_by(**filter)
            )
            return result.scalars().all()
            
    
    async def get_all_roles(self):
        return await self.get_rows(
            AdminRole,
            load_relations=(AdminRole.permissions,),
        )
    
    
    async def add_role(self, name: str, permission_ids: list[int]):
        async with self.async_ses() as session:
            linked_permissions = await session.execute(
                select(AdminRolePermissions).where(AdminRolePermissions.id.in_(permission_ids))
            )
            linked_permissions = linked_permissions.scalars().all()
            if not linked_permissions:
                raise PermissionsNotFound
            new_role = AdminRole(
                name=name,
                permissions=linked_permissions
            )
            
            session.add(new_role)
            await session.commit()
            await session.refresh(new_role)
            result = await session.execute(
                select(AdminRole)
                .options(joinedload(AdminRole.permissions))
                .where(AdminRole.id == new_role.id)
            )
            new_role = result.unique().scalar_one()
            return new_role
    
    
    async def edit_role(self, role_id: int, role_data: dict):
        async with self.async_ses() as session:
            # Получаем роль и её текущие доступы
            result = await session.execute(
                select(AdminRole)
                .where(AdminRole.id == role_id)
                .options(selectinload(AdminRole.permissions))  # загружаем связанные доступы
            )
            role = result.unique().scalar_one_or_none()
            if not role:
                raise RoleNotFound

            # Обновляем название
            role.name = role_data['name']

            # Получаем новые объекты Permission по их ID
            result = await session.execute(
                select(AdminRolePermissions)
                .where(
                    AdminRolePermissions.id.in_(role_data["permission_ids"])
                )
            )
            new_permissions = result.scalars().all()

            # Обновляем связи
            role.permissions.clear()  # удаляем все старые связи
            role.permissions.extend(new_permissions)  # добавляем новые

            await session.commit()
            return role
    
    
    async def add_admin(
        self,
        admin_data: dict
    ):
        async with self.async_ses() as session:
            role_ids = admin_data.pop('role_ids')
            roles = await session.execute(
                select(AdminRole)
                .where(
                    AdminRole.id.in_(role_ids)
                )
            )
            roles = roles.scalars().all()
            if not roles:
                raise RoleNotFound
            
            new_admin = Admin(
                **admin_data,
                roles=roles
            )
            
            session.add(new_admin)
            await session.commit()
            await session.refresh(new_admin)
            result = await session.execute(
                select(Admin)
                .options(joinedload(Admin.roles))
                .where(Admin.id == new_admin.id)
            )
            new_admin = result.unique().scalar_one()
            return new_admin
        
    
    