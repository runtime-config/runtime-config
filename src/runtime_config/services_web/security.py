import typing as t
from functools import wraps

from fastapi import HTTPException, Request, status

from runtime_config.enums.user import UserRole
from runtime_config.repositories.db.entities import User

T = t.TypeVar('T')
P = t.ParamSpec('P')


def only_authorized_user(func: t.Callable[P, t.Awaitable[T]]) -> t.Callable[P, t.Awaitable[T]]:
    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        request: Request = t.cast(Request, kwargs.get('request'))
        assert isinstance(request, Request)

        user: User | None = request.state.user
        exception_params: dict[str, t.Any] = {
            'status_code': status.HTTP_401_UNAUTHORIZED,
            'headers': {'WWW-Authenticate': 'Bearer'},
        }
        if user is None:
            raise HTTPException(
                detail=(
                    'Authorization required. Please check that you have passed the token in '
                    'the request headers and that it is not out of date.'
                ),
                **exception_params,
            )
        if not user.is_active:
            raise HTTPException(
                detail=(
                    'This user is not active. Please activate user or contact with '
                    'your administrator.'
                ),
                **exception_params,
            )
        return await func(*args, **kwargs)

    return wrapper


def only_admin_user(func: t.Callable[P, t.Awaitable[T]]) -> t.Callable[P, t.Awaitable[T]]:
    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        request: Request = t.cast(Request, kwargs.get('request'))
        assert isinstance(request, Request)

        user: User = request.state.user
        if not user.role == UserRole.admin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Administrator user required',
                headers={'WWW-Authenticate': 'Bearer'},
            )
        return await func(*args, **kwargs)

    return wrapper
