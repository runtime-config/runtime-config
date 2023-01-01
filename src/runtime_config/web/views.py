import psycopg2.errors
from aiopg.sa import SAConnection
from fastapi import APIRouter, HTTPException, Query, Request, status

from runtime_config.enums.status import ResponseStatus
from runtime_config.repositories.db import repo as db_repo
from runtime_config.repositories.db.entities import SettingData, SettingHistoryData
from runtime_config.repositories.db.repo import delete_user_refresh_token
from runtime_config.services.account.security import JwtTokenService, authenticate_user
from runtime_config.services_web.security import only_authorized_user
from runtime_config.web.entities import (
    CreateNewSettingRequest,
    EditSettingRequest,
    GetSettingResponse,
    HttpExceptionResponse,
    OAuth2PasswordRequest,
    OAuth2RefreshTokenRequest,
    OperationStatusResponse,
    TokenResponse,
)

router = APIRouter()


@router.post(
    '/token',
    response_model=TokenResponse,
    responses={401: {'model': HttpExceptionResponse}},
)
async def get_pair_tokens(
    request: Request,
    payload: OAuth2PasswordRequest,
) -> dict[str, str]:
    db_conn: SAConnection = request.state.db_conn
    jwt_token_service: JwtTokenService = request.app.state.jwt_token_service
    user = await authenticate_user(db_conn=db_conn, username=payload.username, password=payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect username or password',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    access_token, refresh_token = await jwt_token_service.create_token_pair(db_conn=db_conn, user=user)
    return {'access_token': access_token, 'refresh_token': refresh_token, 'token_type': 'bearer'}


@router.post(
    '/refresh-token',
    response_model=TokenResponse,
    responses={401: {'model': HttpExceptionResponse}},
)
async def update_tokens(
    request: Request,
    payload: OAuth2RefreshTokenRequest,
) -> dict[str, str]:
    db_conn: SAConnection = request.state.db_conn
    jwt_token_service: JwtTokenService = request.app.state.jwt_token_service

    access_token, refresh_token = await jwt_token_service.refresh_token_pair(
        db_conn=db_conn, refresh_token=payload.refresh_token
    )
    if access_token is None or refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Not valid refresh token',
        )

    return {'access_token': access_token, 'refresh_token': refresh_token, 'token_type': 'bearer'}


@router.get(
    '/logout',
    response_model=OperationStatusResponse,
    responses={401: {'model': HttpExceptionResponse}},
)
@only_authorized_user
async def logout(request: Request) -> OperationStatusResponse:
    await delete_user_refresh_token(conn=request.state.db_conn, user_id=request.state.user.id)
    return {'status': ResponseStatus.success}


@router.post(
    '/setting/create',
    response_model=SettingData,
    responses={400: {'model': HttpExceptionResponse}, 401: {'model': HttpExceptionResponse}},
)
@only_authorized_user
async def create_setting(
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


@router.get(
    '/setting/delete/{setting_id}',
    response_model=OperationStatusResponse,
    responses={400: {'model': HttpExceptionResponse}, 401: {'model': HttpExceptionResponse}},
)
@only_authorized_user
async def delete_setting(
    request: Request,
    setting_id: int,
) -> OperationStatusResponse:
    db_conn: SAConnection = request.state.db_conn
    if not await db_repo.delete_setting(conn=db_conn, setting_id=setting_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Could not find the setting with the specified id',
        )

    return {'status': ResponseStatus.success}


@router.post(
    '/setting/edit',
    response_model=SettingData,
    responses={400: {'model': HttpExceptionResponse}, 401: {'model': HttpExceptionResponse}},
)
@only_authorized_user
async def edit_setting(
    request: Request,
    payload: EditSettingRequest,
) -> SettingData:
    db_conn: SAConnection = request.state.db_conn
    edited_setting = await db_repo.edit_setting(
        conn=db_conn, setting_id=payload.id, values=payload.dict(exclude={'id'}, exclude_unset=True)
    )
    if not edited_setting:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Setting with the specified id was not found',
        )

    return edited_setting


@router.get(
    '/setting/get/{setting_id}', response_model=GetSettingResponse, responses={401: {'model': HttpExceptionResponse}}
)
@only_authorized_user
async def get_setting(
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


@router.get('/setting/search', response_model=list[SettingData], responses={401: {'model': HttpExceptionResponse}})
@only_authorized_user
async def search_settings(
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


@router.get(
    '/setting/all/{service_name}', response_model=list[SettingData], responses={401: {'model': HttpExceptionResponse}}
)
@only_authorized_user
async def get_all_service_settings(
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


@router.get('/health-check')
def health_check() -> dict[str, str]:
    return {'status': 'ok'}
