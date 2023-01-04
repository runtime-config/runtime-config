import datetime
import typing as t

from pydantic.fields import Field
from pydantic.main import BaseModel

from runtime_config.entities.user import NewUserForm
from runtime_config.enums.settings import ValueType
from runtime_config.enums.status import ResponseStatus
from runtime_config.enums.user import UserRole
from runtime_config.repositories.db.entities import SettingData, SettingHistoryData


class SignUpRequest(NewUserForm):
    pass


class OAuth2PasswordRequest(BaseModel):
    username: str
    password: str


class OAuth2RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class UserResponse(BaseModel):
    id: int
    username: str
    full_name: str | None
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime


class CreateUserRequest(NewUserForm):
    role: UserRole
    is_active: bool


class EditUserRequest(BaseModel):
    id: int
    username: str | None
    full_name: str | None
    email: str | None
    password: str | None
    role: UserRole | None
    is_active: bool | None


class HttpExceptionResponse(BaseModel):
    detail: str


class DeleteItemsResponse(t.TypedDict, total=False):
    ids: list[int]


class GetSettingResponse(BaseModel):
    setting: SettingData | None
    change_history: list[SettingHistoryData] | None


class EditSettingRequest(BaseModel):
    id: int
    name: str | None
    value: str | None
    value_type: ValueType | None
    is_disabled: bool | None
    service_name: str | None


class CreateNewSettingRequest(BaseModel):
    name: str
    value: str
    value_type: ValueType
    is_disabled: bool = Field(default=False)
    service_name: str


class OperationStatusResponse(t.TypedDict, total=False):
    status: ResponseStatus
    message: str


class GetServiceSettingsLegacyResponse(BaseModel):
    name: str
    value: t.Any
    value_type: ValueType
    disable: bool
