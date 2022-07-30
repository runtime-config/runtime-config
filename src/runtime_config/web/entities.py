from pydantic.main import BaseModel

from runtime_config.enums.settings import ValueType


class GetSettingsResponse(BaseModel):
    name: str
    value: str
    value_type: ValueType
    disable: bool
