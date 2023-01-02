from pydantic import BaseModel, Field


class NewUserForm(BaseModel):
    username: str = Field(min_length=3)
    full_name: str | None
    email: str = Field(regex='.*@.*', example='user@mail.com')
    password: str = Field(min_length=3, max_length=40)
