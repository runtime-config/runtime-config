import datetime
import typing as t

from pydantic.main import BaseModel

from runtime_config.enums.settings import ValueType
from runtime_config.enums.token import TokenType
from runtime_config.enums.user import UserRole


class SettingData(BaseModel):
    id: int
    name: str
    value: t.Any
    value_type: ValueType
    is_disabled: bool
    service_name: str
    created_by_db_user: str
    updated_at: datetime.datetime


class SettingHistoryData(SettingData):
    is_deleted: bool
    deleted_by_db_user: str | None


class User(BaseModel):
    id: int
    username: str
    full_name: str | None
    email: str
    password: str
    role: UserRole
    is_active: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime


class Token(BaseModel):
    id: int
    user_id: int
    token: str
    type: TokenType
