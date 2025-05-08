from datetime import datetime, timedelta
from enum import Enum
import os
from typing import Any

from sqlalchemy import CheckConstraint, ForeignKey, Interval, String, DateTime, Boolean, Integer, Float, True_
from sqlalchemy.dialects.postgresql import BYTEA, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from config import DATE_FORMAT
from custom_types import AdminStatuses, FAQStatuses

class TypeEnum(str, Enum):
    FLOAT = 'float'
    INTEGER = 'int'
    STRING = 'str'
    DATETIME = 'datetime'
    BOOLEAN = 'bool'
    TIME = 'time'


class Base(DeclarativeBase):
    pass


class UserTaskParticipant(Base):
    __tablename__ = 'user_tasks_participants'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer)
    task_template_id: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime)


class TaskTemplate(Base):
    __tablename__ = 'tasks_templates'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    target: Mapped[str] = mapped_column(String, nullable=True)
    check_type: Mapped[str] = mapped_column(String, nullable=True)
    title: Mapped[str] = mapped_column(String, nullable=True)
    small_descr: Mapped[str] = mapped_column(String, nullable=True)
    big_descr: Mapped[str] = mapped_column(String, nullable=True)
    tickets: Mapped[int] = mapped_column(Integer, nullable=True)
    complete_count: Mapped[int] = mapped_column(Integer, nullable=True)
    redirect_url: Mapped[str] = mapped_column(String, nullable=True)
    regular: Mapped[bool] = mapped_column(Boolean, default=False)
    grade: Mapped[int] = mapped_column(Integer, nullable=True)
    bookmaker_id: Mapped[int] = mapped_column(Integer, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=False)
    tg_chat_id: Mapped[str] = mapped_column(String, nullable=True)
    photo: Mapped[str] = mapped_column(String, nullable=True)
    postback_url: Mapped[str|None] = mapped_column(String, nullable=True)
    timer_value: Mapped[timedelta] = mapped_column(Interval, nullable=True)
    gift_giveaway_id: Mapped[int] = mapped_column(Integer, nullable=True)

    def get_data(self, complete_count=None):
        data = {
            'id': self.id,
            'target': self.target,
            'check_enable': bool(self.check_type) and self.check_type != 'auto',
            'title': self.title,
            'small_descr': self.small_descr,
            'big_descr': self.big_descr.replace('\n', '</br>') if self.big_descr else None,
            'tickets': self.tickets,
            # 'complete_count': self.complete_count,
            'redirect_url': self.redirect_url,
            # 'bookmaker_id': self.bookmaker_id,
        }
        if self.complete_count is not None and self.complete_count > 1:
            data.update(
                complete=complete_count or 0,
                expected=self.complete_count
            )
        return data

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    gs_id: Mapped[int] = mapped_column(Integer, nullable=True)

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
    vk_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=True)
    # vk_username: Mapped[str] = mapped_column(String, nullable=True)
    

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

    def get_login_data(self):
        data = {}
        if self.phone:
            data = {
                'login_type': 'phone',
                'login_value': self.phone
            }
        elif self.email:
            data = {
                'login_type': 'email',
                'login_value': self.email
            }
        elif self.tg_id:
            data = {
                'login_type': 'telegram_id',
                'login_value': int(self.tg_id)
            }
        return data

    def get_photo_path(self):
        photo_path = f'static/user_photos/{self.id}/photo'
        base_path = f'./{photo_path}'
        ext_list = ['jpg', 'jpeg', 'png']
        for ext in ext_list:
            path = f'{photo_path}.{ext}'
            if os.path.exists(path):
                return f'/api/{path}'



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
    type: Mapped[str] = mapped_column(String)
    reason: Mapped[str] = mapped_column(String)
    amount: Mapped[int] = mapped_column(Integer, nullable=True)
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
    name: Mapped[str] = mapped_column(String)
    photo: Mapped[str] = mapped_column(String, nullable=True)
    period_days: Mapped[int] = mapped_column(Integer, nullable=True)
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

    id:                 Mapped[int] = mapped_column(Integer, primary_key=True)
    name:               Mapped[str] = mapped_column(String, nullable=True)
    giveaway_id:        Mapped[int] = mapped_column(Integer)
    position:           Mapped[int] = mapped_column(Integer)
    border_color_hex:   Mapped[str] = mapped_column(String, nullable=True)
    photo:              Mapped[str] = mapped_column(String, nullable=True)
    
    
class Admin(Base):
    __tablename__ = 'admins'
    
    id:             Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name:     Mapped[str] = mapped_column(String, nullable=False)
    last_name:      Mapped[str] = mapped_column(String, nullable=False)
    middle_name:    Mapped[str] = mapped_column(String, nullable=True)
    email:          Mapped[str] = mapped_column(String, nullable=False)
    phone_number:   Mapped[str] = mapped_column(String, nullable=False)
    password:       Mapped[str] = mapped_column(String, nullable=False)
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

    admin_id:   Mapped[int] = mapped_column(ForeignKey("admins.id", ondelete='CASCADE'), primary_key=True)
    role_id:    Mapped[int] = mapped_column(ForeignKey("admin_roles.id", ondelete='CASCADE'), primary_key=True)


class AdminRolePermissions(Base):
    __tablename__ = 'admin_role_permissions'
    
    id:     Mapped[int] = mapped_column(Integer, primary_key=True)
    name:   Mapped[str] = mapped_column(String, nullable=False)
    tag:    Mapped[str] = mapped_column(String, nullable=False)

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


class FAQ(Base):
    __tablename__ = 'faq'
    
    id:         Mapped[int] = mapped_column(Integer, primary_key=True)
    question:   Mapped[str] = mapped_column(String, nullable=False)
    answer:     Mapped[str] = mapped_column(String, nullable=False)
    status:     Mapped[str] = mapped_column(String, nullable=True)
    position:   Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    
    __table_args__ = (
        CheckConstraint(
            f"status IN ({', '.join([f'\'{status.value}\'' for status in FAQStatuses])})",
            name='faq_status_check'
        ),
    )
    
    
class UsersStatistic(Base):
    __tablename__ = 'users_statistic'

    id:         Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id:    Mapped[int] = mapped_column(Integer, nullable=False)
    type:       Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class UserTaskComplete(Base):
    __tablename__ = 'user_tasks_complete'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer)
    task_template_id: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    
    
class BalanceReasons(str, Enum):
    welcome_bonus =             'Welcome bonus'
    welcome_bonus_gs =          'Welcome bonus GS'
    onboarding_complete_bonus = 'Onboarding complete bonus'
    everyday_reward =           'Everyday reward'
    everyday_reward_lite =      'Everyday reward (For Lite)'
    everyday_reward_pro =       'Everyday reward (For Pro)'
    wheel_spin =                'Wheel spin'
    wheel_spin_free =           'Wheel spin FREE'
    wheel_prize =               'Wheel prize'
    take_part_giveaway =        'Take part Giveaway'
    referrer_bonus_with_sub =   'Referrer Bonus (With subscription)'
    referral_bonus_with_sub =   'Referral Bonus (With subscription)'
    referrer_bonus =            'Referrer Bonus'
    referral_bonus =            'Referral Bonus'
    tickets_from_gs =           'Initiated by GS '
    task_was_completed =        'Completed Task'
        
        
class Campaign(Base):
    __tablename__ = 'campaigns'
    
    id:                 Mapped[int] = mapped_column(Integer, primary_key=True)
    name:               Mapped[str] = mapped_column(String, nullable=False)
    type:               Mapped[str] = mapped_column(String, nullable=False)
    title:              Mapped[str] = mapped_column(String, nullable=True)
    text:               Mapped[str] = mapped_column(String, nullable=False)
    button_text:        Mapped[str] = mapped_column(String, nullable=True)
    button_url:         Mapped[str] = mapped_column(String, nullable=True)
    timer:              Mapped[timedelta] = mapped_column(Interval, nullable=True)
    
    shedulet_at:        Mapped[datetime] = mapped_column(DateTime)
    
    # Связь с рассылками через промежуточную таблицу campaigns_triggers_link
    triggers: Mapped[list["CampaignTrigger"]] = relationship(
        "CampaignTrigger",
        secondary="campaigns_triggers_link",
        back_populates="campaigns"
    )


class CampaignTrigger(Base):
    __tablename__ = 'campaigns_triggers'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    params: Mapped[dict] = mapped_column(JSONB, nullable=True)
    
    # Связь с триггерами через промежуточную таблицу campaigns_triggers_link
    campaigns: Mapped[list["Campaign"]] = relationship(
        "Campaign",
        secondary="campaigns_triggers_link",
        back_populates="triggers"
    )
    
    
class CampaignTriggerLink(Base):
    __tablename__ = 'campaigns_triggers_link'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(Integer, ForeignKey("campaigns.id", ondelete='CASCADE'))
    trigger_id: Mapped[int] = mapped_column(Integer, ForeignKey("campaigns_triggers.id", ondelete='CASCADE'))
    
