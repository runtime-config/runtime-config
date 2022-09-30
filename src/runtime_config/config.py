from __future__ import annotations

from enum import Enum
from pathlib import Path

from pydantic import PostgresDsn
from pydantic.env_settings import BaseSettings
from pydantic.fields import Field

_inst: dict[str, Config] = {}


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
    project_dir: Path = Path(__file__).absolute().parent.parent.parent
    app_dir: Path = Path(__file__).absolute().parent
    current_env: str = Field(default='dev')

    log_mode: LogMode = LogMode.simple
    log_level: LogLevel = LogLevel.info

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

    class Config:
        project_dir: Path = Path(__file__).absolute().parent.parent.parent
        env_file = project_dir / '.env'


def get_config() -> Config:
    try:
        config = _inst['conf']
    except KeyError:
        config = Config()
        _inst['conf'] = config

    return config
