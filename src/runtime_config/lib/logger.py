import logging
import typing as t


def root_logger_cleaner() -> t.Generator[None, None, None]:
    """
    Resets the root logger to the settings it had when the coroutine was initialized
    """
    root = logging.getLogger()
    default_settings = {
        'level': root.level,
        'disabled': root.disabled,
        'propagate': root.propagate,
        'filters': root.filters[:],
        'handlers': root.handlers[:],
    }
    yield

    while True:
        for attr, attr_value in default_settings.items():
            setattr(root, attr, attr_value)
        yield
