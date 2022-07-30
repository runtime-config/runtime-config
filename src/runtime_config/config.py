from pathlib import Path

from pydantic import PostgresDsn as PostgresDsnOrig
from pydantic.env_settings import BaseSettings
from pydantic.fields import Field

_inst: dict[str, 'Config'] = {}


class PostgresDsn(PostgresDsnOrig):
    allowed_schemes = {
        *PostgresDsnOrig.allowed_schemes,
        'postgresql+aiopg',
    }


class Config(BaseSettings):
    project_dir: Path = Path(__file__).absolute().parent.parent.parent
    app_dir: Path = Path(__file__).absolute().parent
    current_env: str = Field(default='dev')

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
            scheme='postgresql+aiopg',
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
