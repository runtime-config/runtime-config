import datetime
import typing as t

from pydantic.main import BaseModel

from runtime_config.enums.settings import ValueType


class SettingData(BaseModel):
    id: int
    name: str
    value: t.Any
    value_type: ValueType
    disabled: bool
    service_name: str
    created_by_db_user: str
    updated_at: datetime.datetime


class SettingHistoryData(SettingData):
    is_deleted: bool
    deleted_by_db_user: str | None


class SearchParams(t.TypedDict, total=False):
    name: str | None
    service_name: str | None
