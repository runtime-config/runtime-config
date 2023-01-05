from __future__ import annotations

from enum import Enum
from pathlib import Path

from pydantic import PostgresDsn
from pydantic.env_settings import BaseSettings
from pydantic.fields import Field

_inst: dict[str, Config] = {}
project_dir: Path = Path(__file__).absolute().parent.parent.parent


class LogMode(Enum):
    json = 'json'
    simple = 'simple'


class LogLevel(Enum):
    critical = 'critical'
    error = 'error'
    warning = 'warning'
    info = 'info'
    debug = 'debug'
    notset = 'notset'


class Config(BaseSettings):
    project_dir: Path = project_dir
    app_dir: Path = Path(__file__).absolute().parent

    secret_key: str = Field(min_length=50)
    log_mode: LogMode = LogMode.simple
    log_level: LogLevel = LogLevel.info

    jwt_token_algorithm: str = Field(default='HS256')
    jwt_access_token_expire_time: int = Field(default=5)
    jwt_refresh_token_expire_time: int = Field(default=14400)

    # db
    db_host: str = Field(default='db')
    db_port: str = Field(default='5432')
    db_user: str
    db_password: str
    db_name: str

    @property
    def db_dsn(self) -> PostgresDsn:
        return PostgresDsn(
            url=None,
            scheme='postgresql',
            user=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            path=f'/{self.db_name}',
        )


def get_config(env_file: Path = project_dir / '.env') -> Config:
    try:
        config = _inst['conf']
    except KeyError:
        config = Config(_env_file=env_file)
        _inst['conf'] = config

    return config
