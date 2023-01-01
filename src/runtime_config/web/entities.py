import typing as t

from pydantic.fields import Field
from pydantic.main import BaseModel

from runtime_config.enums.settings import ValueType
from runtime_config.enums.status import ResponseStatus
from runtime_config.repositories.db.entities import SettingData, SettingHistoryData


class OAuth2PasswordRequest(BaseModel):
    username: str
    password: str


class OAuth2RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class HttpExceptionResponse(BaseModel):
    detail: str


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
