import typing as t
from datetime import datetime, timedelta

from aiopg.sa import SAConnection
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import ValidationError
from structlog import get_logger

from runtime_config.entities.auth import TokenData
from runtime_config.repositories.db.entities import User
from runtime_config.repositories.db.repo import (
    get_user,
    get_user_refresh_token,
    update_refresh_token,
)

logger = get_logger(__name__)
crypt_context = CryptContext(schemes=["argon2"], deprecated="auto")


class JwtTokenService:
    def __init__(
        self, secret_key: str, access_token_expire_time: int, refresh_token_expire_time: int, algorithm: str = 'HS256'
    ) -> None:
        self._secret_key: str = secret_key
        self.access_token_expire_time: timedelta = timedelta(minutes=access_token_expire_time)
        self.refresh_token_expire_time: timedelta = timedelta(minutes=refresh_token_expire_time)
        self.algorithm = algorithm

    async def refresh_token_pair(self, db_conn: SAConnection, refresh_token: str) -> tuple[str | None, str | None]:
        new_access_token, new_refresh_token = None, None

        _, decoded_token = self._decode_token(refresh_token)
        if not decoded_token:
            return new_access_token, new_refresh_token

        user = await get_user(conn=db_conn, username=decoded_token.username)
        if not user:
            logger.info('User not found from refresh token')
            return new_access_token, new_refresh_token

        found_token = await get_user_refresh_token(conn=db_conn, refresh_token=refresh_token, user_id=user.id)
        if not found_token:
            logger.info('Refresh token not found in database')
            return new_access_token, new_refresh_token

        new_access_token, new_refresh_token = await self.create_token_pair(db_conn=db_conn, user=user)
        return new_access_token, new_refresh_token

    async def create_token_pair(self, db_conn: SAConnection, user: User) -> tuple[str, str]:
        access = self._create_access_token(user)
        refresh = self._create_refresh_token(user)
        await update_refresh_token(conn=db_conn, new_token=refresh, user_id=user.id)
        return access, refresh

    def _create_access_token(self, user: User) -> str:
        token_payload = {'sub': user.username, 'exp': datetime.utcnow() + self.access_token_expire_time}
        token = jwt.encode(token_payload, key=self._secret_key, algorithm=self.algorithm)
        return token

    def _create_refresh_token(self, user: User) -> str:
        token_payload = {
            'sub': user.username,
            'exp': datetime.utcnow() + self.refresh_token_expire_time,
            'type': 'refresh',
        }
        token = jwt.encode(token_payload, key=self._secret_key, algorithm=self.algorithm)
        return token

    async def get_user_from_access_token(self, db_conn: SAConnection, token: str) -> User | None:
        user = None
        _, decoded_token = self._decode_token(token)
        if decoded_token:
            user = await get_user(conn=db_conn, username=decoded_token.username)

        return user

    def _decode_token(self, token: str) -> tuple[dict[str, t.Any] | None, TokenData | None]:
        payload, token_data = None, None
        try:
            payload = jwt.decode(token, self._secret_key, algorithms=[self.algorithm])
            token_data = TokenData(**payload)
        except (JWTError, ValidationError):
            logger.info('Decode jwt token fail', exc_info=True)

        return payload, token_data


async def authenticate_user(db_conn: SAConnection, username: str, password: str) -> User | None:
    user = await get_user(conn=db_conn, username=username)
    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    return user


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return crypt_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return crypt_context.hash(password)
