import logging
from logging.config import dictConfig

import structlog
from structlog.dev import ConsoleRenderer
from structlog.processors import JSONRenderer
from structlog.types import Processor

from runtime_config.config import LogLevel

processors: list[Processor] = [
    structlog.processors.TimeStamper(fmt='iso'),
    structlog.stdlib.add_log_level,
    structlog.stdlib.add_logger_name,
    structlog.stdlib.PositionalArgumentsFormatter(),
    structlog.processors.StackInfoRenderer(),
    structlog.processors.UnicodeDecoder(),
    structlog.processors.format_exc_info,
]

json_renderer = JSONRenderer(ensure_ascii=False)
simple_renderer = ConsoleRenderer(colors=True)


def _init_structlog(log_level: int, processors: list[Processor]) -> None:
    structlog.configure(
        cache_logger_on_first_use=True,
        processors=[*processors, structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(min_level=log_level),
    )


def _init_logging(log_level: int, processors: list[Processor], renderer: ConsoleRenderer | JSONRenderer) -> None:
    dictConfig(
        {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'default': {
                    '()': structlog.stdlib.ProcessorFormatter,
                    'processors': [
                        structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                        renderer,
                    ],
                    'foreign_pre_chain': processors,
                },
            },
            'handlers': {
                'default': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'default',
                },
            },
            'loggers': {
                '': {
                    'handlers': ['default'],
                    'level': log_level,
                }
            },
        }
    )


def init_logger(log_mode: str, log_level: LogLevel = LogLevel.info) -> None:
    level = getattr(logging, log_level.value.upper())
    renderer: ConsoleRenderer | JSONRenderer = json_renderer if log_mode == 'json' else simple_renderer

    _init_logging(level, processors, renderer)
    _init_structlog(level, processors)
