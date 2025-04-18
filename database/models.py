from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import CheckConstraint, ForeignKey, String, DateTime, Boolean, Integer, Float
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from config import DATE_FORMAT

class TypeEnum(str, Enum):
    FLOAT = 'float'
    INTEGER = 'int'
    STRING = 'str'
    DATETIME = 'datetime'
    BOOLEAN = 'bool'
    TIME = 'time'


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)

    tg_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=True)
    username: Mapped[str] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str] = mapped_column(String(255), nullable=True)

    is_admin: Mapped[bool] = mapped_column(default=False)
    deleted: Mapped[bool] = mapped_column(default=False)
    timezone: Mapped[int] = mapped_column(nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)

    email: Mapped[str] = mapped_column(String, nullable=True)
    phone: Mapped[str] = mapped_column(String, nullable=True)

    hashed_password: Mapped[str] = mapped_column(String, nullable=True)
    otp_code: Mapped[str] = mapped_column(String, nullable=True)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    referrer_id: Mapped[int] = mapped_column(Integer, nullable=True)
    identity: Mapped[str] = mapped_column(String, nullable=True)
    from_gs: Mapped[bool] = mapped_column(default=False)
    complete_education: Mapped[bool] = mapped_column(default=False)

    streak: Mapped[int] = mapped_column(Integer, default=1)
    last_claimed: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    streamname: Mapped[str] = mapped_column(String, nullable=True, default='default')
    last_login: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    free_wheels: Mapped[int] = mapped_column(Integer, default=0)



    def get_data(self):
        return {
            'id': self.id,
            'tg_id': self.tg_id,
            'username': self.username,
            'is_admin': self.is_admin,
            'deleted': self.deleted,
            'timezone': self.timezone,
            'created_at': self.created_at.strftime('%d-%m-%Y'),
            'email': self.email,
            'phone': self.phone,
        }

    def get_profile_username(self):
        if self.username:
            return self.username
        elif self.email:
            return self.email
        elif self.phone:
            return self.phone
        else:
            name = []
            if self.first_name:
                name.append(self.first_name)
            if self.last_name:
                name.append(self.last_name)
            if name:
                return ' '.join(name)
            return 'No name'


class UserSubscription(Base):
    __tablename__ = 'users_subscriptions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer)
    lite: Mapped[bool] = mapped_column(Boolean, default=False)
    lite_expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    pro: Mapped[bool] = mapped_column(Boolean, default=False)
    pro_expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    def get_data(self):
        return {
            'lite': self.lite,
            'lite_expires_at': self.lite_expires_at.strftime('%d.%m.%Y') if self.lite_expires_at else None,
            'pro': self.pro,
            'pro_expires_at': self.pro_expires_at.strftime('%d.%m.%Y') if self.pro_expires_at else None,
        }


class TempOTPStorage(Base):
    __tablename__ = "temp_otp_storage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    login: Mapped[str] = mapped_column(String)
    otp_code: Mapped[str] = mapped_column(String, nullable=True)
    confirmed: Mapped[bool] = mapped_column(default=False)


class UserBalanceHistory(Base):
    __tablename__ = "users_balances_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer)
    # referral_id: Mapped[int] = mapped_column(Integer, nullable=True)
    # order_id: Mapped[int] = mapped_column(Integer, nullable=True)
    type: Mapped[str] = mapped_column(String)
    reason: Mapped[str] = mapped_column(String)
    amount: Mapped[int] = mapped_column(Integer, nullable=True)
    # referral_lvl: Mapped[int] = mapped_column(Integer, nullable=True)
    # referral_percent: Mapped[int] = mapped_column(Integer, nullable=True)
    # status: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime)


class PrizeCarousel(Base):
    __tablename__ = "prize_carousels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    streamname: Mapped[str] = mapped_column(String, default='default')
    active: Mapped[bool] = mapped_column(default=True)


class AppConfig(Base):
    __tablename__ = "app_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    unique_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    value: Mapped[str] = mapped_column(String, nullable=True)
    description: Mapped[str] = mapped_column(String, nullable=True)
    description_en: Mapped[str] = mapped_column(String, nullable=True)
    type_: Mapped[TypeEnum] = mapped_column(String(16), nullable=True)
    sub_data: Mapped[str] = mapped_column(String(64), nullable=True)

    def get_value(self) -> Any:
        if self.type_ == 'str':
            return self.value
        if self.type_ == 'int':
            return int(self.value)
        if self.type_ == 'float':
            return float(self.value)
        if self.type_ == 'datetime':
            return datetime.datetime.strptime(self.value, self.sub_data)
        if self.type_ == 'time':
            return datetime.datetime.strptime(self.value, self.sub_data).time()
        if self.type_ == 'bool':
            return bool(self.value)
        return None


class Bookmaker(Base):
    __tablename__ = "bookmakers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    tickets: Mapped[int] = mapped_column(Integer, nullable=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(default=True)

    def get_data(self):
        return {
            'name': self.name,
            'image': f'/api/static/bookmakers/{self.name}.svg',
            'tickets': self.tickets,
            'amount': self.amount
        }


class Wheel(Base):
    __tablename__ = "wheel"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tickets: Mapped[int] = mapped_column(Integer, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    chance: Mapped[float] = mapped_column(Float, default=0)

    def get_data(self):
        return {
            'id': self.id,
            'tickets': self.tickets,
        }


class Giveaway(Base):
    __tablename__ = 'giveaways'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    streamname: Mapped[str] = mapped_column(String, nullable=True)
    price: Mapped[int] = mapped_column(Integer)
    start_date: Mapped[datetime] = mapped_column(DateTime)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    def get_data(self):
        return {
            'id': self.id,
            'streamname': self.streamname,
            'price': self.price,
            'start_date': self.start_date.strftime(DATE_FORMAT),
        }


class GiveawayParticipant(Base):
    __tablename__ = 'giveaways_participant'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer)
    giveaway_id: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime)


class GiveawayEnded(Base):
    __tablename__ = 'giveaways_ended'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    giveaway_id: Mapped[int] = mapped_column(Integer)
    end_date: Mapped[datetime] = mapped_column(DateTime)
    winner_id: Mapped[int] = mapped_column(Integer)
    prize_id: Mapped[int] = mapped_column(Integer)


class GiveawayPrize(Base):
    __tablename__ = 'giveaways_prizes'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=True)
    giveaway_id: Mapped[int] = mapped_column(Integer)
    
    
class AdminStatuses(str, Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'    
    
    
class Admin(Base):
    __tablename__ = 'admins'
    
    id:             Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name:     Mapped[str] = mapped_column(String, nullable=False)
    last_name:      Mapped[str] = mapped_column(String, nullable=False)
    middle_name:    Mapped[str] = mapped_column(String, nullable=True)
    email:          Mapped[str] = mapped_column(String, nullable=False)
    phone_number:   Mapped[str] = mapped_column(String, nullable=False)
    password:       Mapped[bytes] = mapped_column(BYTEA, nullable=False)
    status:         Mapped[str] = mapped_column(String, nullable=False)
    
    # Связь с ролями через промежуточную таблицу admin_roles_link
    roles: Mapped[list["AdminRole"]] = relationship(
        "AdminRole",
        secondary="admin_roles_link",
        back_populates="admins"
    )
    __table_args__ = (
        CheckConstraint(
            f"status IN ({', '.join([f'\'{status.value}\'' for status in AdminStatuses])})",
            name='admin_status_check'
        ),
    )
    
    

class AdminRole(Base):
    __tablename__ = "admin_roles"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)

    # Связь с админами через промежуточную таблицу admin_roles_link
    admins: Mapped[list["Admin"]] = relationship(
        "Admin",
        secondary="admin_roles_link",
        back_populates="roles"
    )

    # Связь с разрешениями через промежуточную таблицу admin_role_permissions_link
    permissions: Mapped[list["AdminRolePermissions"]] = relationship(
        "AdminRolePermissions",
        secondary="admin_role_permissions_link",
        back_populates="roles"
    )


class AdminRoleLink(Base):
    '''
    Промежуточная таблица для связывания many-to-many таблиц admins и admin_roles
    '''
    __tablename__ = "admin_roles_link"

    admin_id: Mapped[int] = mapped_column(ForeignKey("admins.id", ondelete='CASCADE'), primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("admin_roles.id", ondelete='CASCADE'), primary_key=True)


class AdminRolePermissions(Base):
    __tablename__ = 'admin_role_permissions'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str]

    # Связь с ролями через промежуточную таблицу admin_role_permissions_link
    roles: Mapped[list["AdminRole"]] = relationship(
        "AdminRole",
        secondary="admin_role_permissions_link",
        back_populates="permissions"
    )


class AdminRolePermissionLink(Base):
    '''
    Промежуточная таблица для связывания many-to-many таблиц admin_roles и admin_role_permissions
    '''
    __tablename__ = "admin_role_permissions_link"

    role_id: Mapped[int] = mapped_column(ForeignKey("admin_roles.id", ondelete='CASCADE'), primary_key=True)
    permission_id: Mapped[int] = mapped_column(ForeignKey("admin_role_permissions.id", ondelete='CASCADE'), primary_key=True)
