from pydantic import BaseModel, Field


class NewAdminUser(BaseModel):
    username: str = Field(min_length=3)
    full_name: str | None
    email: str = Field(regex='.*@.*')
    password: str = Field(min_length=3, max_length=40)
