from runtime_config.config import get_config
from runtime_config.main import app_factory

app = app_factory(config=get_config())
