import typing as t

import psycopg2.errors
from aiopg.sa import SAConnection
from fastapi import APIRouter, HTTPException, Query, Request, status

from runtime_config.enums.status import ResponseStatus
from runtime_config.enums.user import UserRole
from runtime_config.repositories.db import repo as db_repo
from runtime_config.repositories.db.entities import (
    SettingData,
    SettingHistoryData,
    User,
)
from runtime_config.repositories.db.repo import delete_user_refresh_token
from runtime_config.services.account.security import JwtTokenService, authenticate_user
from runtime_config.services.account.user import create_new_user, create_simple_user
from runtime_config.services_web.security import only_admin_user, only_authorized_user
from runtime_config.web.entities import (
    CreateNewSettingRequest,
    CreateUserRequest,
    DeleteItemsResponse,
    EditSettingRequest,
    EditUserRequest,
    GetSettingResponse,
    HttpExceptionResponse,
    OAuth2PasswordRequest,
    OAuth2RefreshTokenRequest,
    OperationStatusResponse,
    SignUpRequest,
    TokenResponse,
    UserResponse,
)

common_router = APIRouter()


class AccountViews:
    router = APIRouter()
    jwt_token_service: JwtTokenService

    def __init__(self) -> None:
        self.router.add_api_route(
            '/account/sign-up',
            endpoint=self.sign_up,
            methods=['POST'],
            response_model=OperationStatusResponse,
            responses={400: {'model': HttpExceptionResponse}},
            tags=['account'],
        )
        self.router.add_api_route(
            '/account/token',
            endpoint=self.get_pair_tokens,
            methods=['POST'],
            response_model=TokenResponse,
            responses={401: {'model': HttpExceptionResponse}},
            tags=['account'],
        )
        self.router.add_api_route(
            '/account/refresh-token',
            endpoint=self.update_tokens,
            methods=['POST'],
            response_model=TokenResponse,
            responses={401: {'model': HttpExceptionResponse}},
            tags=['account'],
        )
        self.router.add_api_route(
            '/account/logout',
            endpoint=self.logout,
            methods=['GET'],
            response_model=OperationStatusResponse,
            responses={401: {'model': HttpExceptionResponse}},
            tags=['account'],
        )

    def init_deps(self, jwt_token_service: JwtTokenService) -> None:
        self.jwt_token_service = jwt_token_service

    async def sign_up(
        self,
        request: Request,
        payload: SignUpRequest,
    ) -> dict[str, t.Any]:
        db_conn: SAConnection = request.state.db_conn
        try:
            await create_simple_user(conn=db_conn, values=payload.dict())
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            )
        return {'status': ResponseStatus.success}

    async def get_pair_tokens(
        self,
        request: Request,
        payload: OAuth2PasswordRequest,
    ) -> dict[str, str]:
        db_conn: SAConnection = request.state.db_conn
        user = await authenticate_user(
            db_conn=db_conn, username=payload.username, password=payload.password
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Incorrect username or password',
                headers={'WWW-Authenticate': 'Bearer'},
            )
        access_token, refresh_token = await self.jwt_token_service.create_token_pair(
            db_conn=db_conn, user=user
        )
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'bearer',
        }

    async def update_tokens(
        self,
        request: Request,
        payload: OAuth2RefreshTokenRequest,
    ) -> dict[str, str]:
        db_conn: SAConnection = request.state.db_conn

        access_token, refresh_token = await self.jwt_token_service.refresh_token_pair(
            db_conn=db_conn, refresh_token=payload.refresh_token
        )
        if access_token is None or refresh_token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Not valid refresh token',
            )

        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'bearer',
        }

    @only_authorized_user
    async def logout(self, request: Request) -> OperationStatusResponse:
        await delete_user_refresh_token(conn=request.state.db_conn, user_id=request.state.user.id)
        return {'status': ResponseStatus.success}


class UserViews:
    router = APIRouter()

    def __init__(self) -> None:
        self.router.add_api_route(
            '/user/create',
            endpoint=self.create_user,
            response_model=UserResponse,
            methods=['POST'],
            responses={
                400: {'model': HttpExceptionResponse},
                401: {'model': HttpExceptionResponse},
            },
            tags=['user'],
        )
        self.router.add_api_route(
            '/user/delete',
            endpoint=self.delete_users,
            response_model=DeleteItemsResponse,
            methods=['GET'],
            responses={
                401: {'model': HttpExceptionResponse},
            },
            tags=['user'],
        )
        self.router.add_api_route(
            '/user/edit',
            endpoint=self.edit_user,
            response_model=UserResponse,
            methods=['POST'],
            responses={
                400: {'model': HttpExceptionResponse},
                401: {'model': HttpExceptionResponse},
            },
            tags=['user'],
        )
        self.router.add_api_route(
            '/user/get',
            endpoint=self.get_users,
            response_model=list[UserResponse],
            methods=['GET'],
            responses={401: {'model': HttpExceptionResponse}},
            tags=['user'],
        )
        self.router.add_api_route(
            '/user/search',
            endpoint=self.search_user,
            response_model=list[UserResponse],
            methods=['GET'],
            responses={401: {'model': HttpExceptionResponse}},
            tags=['user'],
        )
        self.router.add_api_route(
            '/user/all',
            endpoint=self.get_all_users,
            response_model=list[UserResponse],
            methods=['GET'],
            responses={401: {'model': HttpExceptionResponse}},
            tags=['user'],
        )

    @only_authorized_user
    @only_admin_user
    async def create_user(
        self,
        request: Request,
        payload: CreateUserRequest,
    ) -> User:
        db_conn: SAConnection = request.state.db_conn
        try:
            created_user = await create_new_user(conn=db_conn, values=payload.dict())
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            )

        return created_user

    @only_authorized_user
    @only_admin_user
    async def delete_users(
        self, request: Request, user_ids: list[int] = Query(alias='user_id')
    ) -> DeleteItemsResponse:
        db_conn: SAConnection = request.state.db_conn
        deleted_rows_id = await db_repo.delete_users(conn=db_conn, user_ids=user_ids)
        return DeleteItemsResponse(ids=deleted_rows_id)

    @only_authorized_user
    @only_admin_user
    async def edit_user(
        self,
        request: Request,
        payload: EditUserRequest,
    ) -> User:
        db_conn: SAConnection = request.state.db_conn
        edited_user = await db_repo.edit_user(
            conn=db_conn,
            user_id=payload.id,
            values=payload.dict(exclude={'id'}, exclude_unset=True),
        )
        if not edited_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='User with the specified id was not found',
            )

        return edited_user

    @only_authorized_user
    @only_admin_user
    async def get_users(
        self,
        request: Request,
        user_ids: list[int] = Query(alias='user_id'),
    ) -> list[User]:
        db_conn: SAConnection = request.state.db_conn
        found_users = await db_repo.get_users(conn=db_conn, user_ids=user_ids)
        return found_users

    @only_authorized_user
    @only_admin_user
    async def search_user(
        self,
        request: Request,
        username: str | None = None,
        full_name: str | None = None,
        email: str | None = None,
        role: UserRole | None = None,
        is_active: bool | None = None,
        offset: int = Query(default=0, gt=-1),
        limit: int = Query(default=30, gt=0, le=30),
    ) -> list[User]:
        db_conn: SAConnection = request.state.db_conn
        return [
            usr
            async for usr in db_repo.search_user(
                conn=db_conn,
                values={
                    'username': username,
                    'full_name': full_name,
                    'email': email,
                    'role': role,
                    'is_active': is_active,
                },
                offset=offset,
                limit=limit,
            )
        ]

    @only_authorized_user
    @only_admin_user
    async def get_all_users(
        self,
        request: Request,
        offset: int = Query(default=0, gt=-1),
        limit: int = Query(default=30, gt=0, le=30),
    ) -> list[User]:
        db_conn: SAConnection = request.state.db_conn
        return [
            user async for user in db_repo.get_all_users(conn=db_conn, offset=offset, limit=limit)
        ]


class SettingViews:
    router = APIRouter()

    def __init__(self) -> None:
        self.router.add_api_route(
            '/setting/create',
            endpoint=self.create_setting,
            response_model=SettingData,
            methods=['POST'],
            responses={
                400: {'model': HttpExceptionResponse},
                401: {'model': HttpExceptionResponse},
            },
            tags=['setting'],
        )

        self.router.add_api_route(
            '/setting/delete',
            endpoint=self.delete_settings,
            response_model=DeleteItemsResponse,
            methods=['GET'],
            responses={401: {'model': HttpExceptionResponse}},
            tags=['setting'],
        )
        self.router.add_api_route(
            '/setting/edit',
            endpoint=self.edit_setting,
            response_model=SettingData,
            methods=['POST'],
            responses={
                400: {'model': HttpExceptionResponse},
                401: {'model': HttpExceptionResponse},
            },
            tags=['setting'],
        )
        self.router.add_api_route(
            '/setting/get/{setting_id}',
            endpoint=self.get_setting,
            response_model=GetSettingResponse,
            methods=['GET'],
            responses={401: {'model': HttpExceptionResponse}},
            tags=['setting'],
        )
        self.router.add_api_route(
            '/setting/search',
            endpoint=self.search_settings,
            response_model=list[SettingData],
            methods=['GET'],
            responses={401: {'model': HttpExceptionResponse}},
            tags=['setting'],
        )
        self.router.add_api_route(
            '/setting/all/{service_name}',
            endpoint=self.get_service_setting,
            response_model=list[SettingData],
            methods=['GET'],
            responses={401: {'model': HttpExceptionResponse}},
            tags=['setting'],
        )

    @only_authorized_user
    async def create_setting(
        self,
        request: Request,
        payload: CreateNewSettingRequest,
    ) -> SettingData:
        db_conn: SAConnection = request.state.db_conn
        try:
            created_setting = await db_repo.create_new_setting(conn=db_conn, values=payload.dict())
        except psycopg2.errors.UniqueViolation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Variable with the same name already exists',
            )

        if not created_setting:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Failed to create new setting',
            )

        return created_setting

    @only_authorized_user
    async def delete_settings(
        self, request: Request, setting_ids: list[int] = Query(alias='setting_id')
    ) -> DeleteItemsResponse:
        db_conn: SAConnection = request.state.db_conn
        deleted_rows_id = await db_repo.delete_settings(conn=db_conn, setting_ids=setting_ids)
        return DeleteItemsResponse(ids=deleted_rows_id)

    @only_authorized_user
    async def edit_setting(
        self,
        request: Request,
        payload: EditSettingRequest,
    ) -> SettingData:
        db_conn: SAConnection = request.state.db_conn
        edited_setting = await db_repo.edit_setting(
            conn=db_conn,
            setting_id=payload.id,
            values=payload.dict(exclude={'id'}, exclude_unset=True),
        )
        if not edited_setting:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Setting with the specified id was not found',
            )

        return edited_setting

    @only_authorized_user
    async def get_setting(
        self,
        request: Request,
        setting_id: int,
        include_history: bool = False,
    ) -> GetSettingResponse:
        db_conn: SAConnection = request.state.db_conn
        change_history: list[SettingHistoryData] | None
        found_setting, change_history = await db_repo.get_setting(
            conn=db_conn, setting_id=setting_id, include_history=include_history
        )
        if not include_history:
            change_history = None
        return GetSettingResponse(setting=found_setting, change_history=change_history)

    @only_authorized_user
    async def search_settings(
        self,
        request: Request,
        name: str | None = None,
        service_name: str | None = None,
        offset: int = Query(default=0, gt=-1),
        limit: int = Query(default=30, gt=0, le=30),
    ) -> list[SettingData]:
        db_conn: SAConnection = request.state.db_conn
        return [
            setting
            async for setting in db_repo.search_settings(
                conn=db_conn, name=name, service_name=service_name, offset=offset, limit=limit
            )
        ]

    @only_authorized_user
    async def get_service_setting(
        self,
        request: Request,
        service_name: str,
        offset: int = Query(default=0, gt=-1),
        limit: int = Query(default=30, gt=0, le=30),
    ) -> list[SettingData]:
        db_conn: SAConnection = request.state.db_conn
        return [
            setting
            async for setting in db_repo.get_service_settings(
                conn=db_conn,
                service_name=service_name,
                offset=offset,
                limit=limit,
            )
        ]


@common_router.get('/health-check')
def health_check() -> dict[str, str]:
    return {'status': 'ok'}


account_views = AccountViews()
user_views = UserViews()
setting_views = SettingViews()
