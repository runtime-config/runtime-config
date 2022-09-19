import typing as t

from pydantic.fields import Field
from pydantic.main import BaseModel

from runtime_config.enums.settings import ValueType
from runtime_config.enums.status import ResponseStatus
from runtime_config.repositories.db.entities import (
    SearchParams,
    SettingData,
    SettingHistoryData,
)


class SettingSearchRequest(BaseModel):
    offset: int = Field(gt=-1, default=0)
    limit: int = Field(gt=0, le=30, default=30)
    search_params: SearchParams


class GetAllSettingsRequest(BaseModel):
    offset: int = Field(gt=-1, default=0)
    limit: int = Field(gt=0, le=30, default=30)


class GetSettingResponse(BaseModel):
    setting: SettingData | None
    change_history: list[SettingHistoryData] = Field(default_factory=list)


class EditSettingRequest(BaseModel):
    id: int
    name: str | None
    value: str | None
    value_type: ValueType | None
    disable: bool | None
    service_name: str | None


class CreateNewSettingRequest(BaseModel):
    name: str
    value: str
    value_type: ValueType
    disable: bool = Field(default=False)
    service_name: str


class OperationStatusResponse(t.TypedDict, total=False):
    status: ResponseStatus
    message: str


class DeleteSettingResponse(OperationStatusResponse):
    pass


class GetServiceSettingsLegacyResponse(BaseModel):
    name: str
    value: t.Any
    value_type: ValueType
    disable: bool
