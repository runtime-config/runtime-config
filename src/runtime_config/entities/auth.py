from pydantic.fields import Field
from pydantic.main import BaseModel


class TokenData(BaseModel):
    username: str = Field(alias='sub')
    type: str | None
