import typing as t

import psycopg2.errors
from aiopg.sa import SAConnection
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from runtime_config.enums.status import ResponseStatus
from runtime_config.lib.db import get_db_conn
from runtime_config.repositories.db import repo as db_repo
from runtime_config.repositories.db.entities import SettingData, SettingHistoryData
from runtime_config.web.entities import (
    CreateNewSettingRequest,
    EditSettingRequest,
    GetAllSettingsRequest,
    GetServiceSettingsLegacyResponse,
    GetSettingResponse,
    OperationStatusResponse,
    SettingSearchRequest,
)

router = APIRouter()


@router.post('/setting/create', response_model=SettingData, responses={400: {'model': OperationStatusResponse}})
async def create_setting(
    payload: CreateNewSettingRequest, db_conn: SAConnection = Depends(get_db_conn)
) -> SettingData | JSONResponse:
    response: SettingData | JSONResponse
    try:
        created_setting = await db_repo.create_new_setting(conn=db_conn, values=payload.dict())
    except psycopg2.errors.UniqueViolation:
        response = JSONResponse(
            content={'status': ResponseStatus.error.value, 'message': 'Variable with the same name already exists'},
            status_code=400,
        )
    else:
        if created_setting:
            response = created_setting
        else:
            response = JSONResponse(
                content={'status': ResponseStatus.error.value, 'message': 'Failed to create new setting'},
                status_code=400,
            )

    return response


@router.get(
    '/setting/delete/{setting_id}',
    response_model=OperationStatusResponse,
    responses={400: {'model': OperationStatusResponse}},
)
async def delete_setting(
    setting_id: int, db_conn: SAConnection = Depends(get_db_conn)
) -> OperationStatusResponse | JSONResponse:
    if await db_repo.delete_setting(conn=db_conn, setting_id=setting_id):
        return {'status': ResponseStatus.success}
    else:
        return JSONResponse(
            content={
                'status': ResponseStatus.error.value,
                'message': 'Could not find the setting with the specified id',
            },
            status_code=400,
        )


@router.post('/setting/edit', response_model=SettingData, responses={400: {'model': OperationStatusResponse}})
async def edit_setting(
    payload: EditSettingRequest, db_conn: SAConnection = Depends(get_db_conn)
) -> SettingData | JSONResponse:
    response: SettingData | JSONResponse
    edited_setting = await db_repo.edit_setting(
        conn=db_conn, setting_id=payload.id, values=payload.dict(exclude={'id'}, exclude_unset=True)
    )
    if edited_setting:
        response = edited_setting
    else:
        response = JSONResponse(
            content={'status': ResponseStatus.error.value, 'message': 'Setting with the specified id was not found'},
            status_code=400,
        )

    return response


@router.get('/setting/get/{setting_id}', response_model=GetSettingResponse)
async def get_setting(
    setting_id: int, include_history: bool = False, db_conn: SAConnection = Depends(get_db_conn)
) -> GetSettingResponse:
    change_history: list[SettingHistoryData] | None
    found_setting, change_history = await db_repo.get_setting(
        conn=db_conn, setting_id=setting_id, include_history=include_history
    )
    if not include_history:
        change_history = None
    return GetSettingResponse(setting=found_setting, change_history=change_history)


@router.post('/setting/search', response_model=list[SettingData])
async def search_settings(
    payload: SettingSearchRequest, db_conn: SAConnection = Depends(get_db_conn)
) -> list[SettingData]:
    return [
        setting
        async for setting in db_repo.search_settings(
            conn=db_conn, search_params=payload.search_params, offset=payload.offset, limit=payload.limit
        )
    ]


@router.post('/setting/all/{service_name}', response_model=list[SettingData])
async def get_all_service_settings(
    service_name: str, payload: GetAllSettingsRequest, db_conn: SAConnection = Depends(get_db_conn)
) -> list[SettingData]:
    return [
        setting
        async for setting in db_repo.get_service_settings(
            conn=db_conn,
            service_name=service_name,
            offset=payload.offset,
            limit=payload.limit,
        )
    ]


@router.get('/get_settings/{service_name}', response_model=list[GetServiceSettingsLegacyResponse], deprecated=True)
async def get_service_settings(
    service_name: str, db_conn: SAConnection = Depends(get_db_conn)
) -> list[dict[str, t.Any]]:
    # not removed for backwards compatibility with client library
    def rename_fields(setting_data: SettingData) -> dict[str, t.Any]:
        data = setting_data.dict()
        data['disable'] = data.pop('disabled')
        return data

    return [
        rename_fields(setting)
        async for setting in db_repo.get_service_settings(conn=db_conn, service_name=service_name)
    ]


@router.get('/health-check')
def health_check() -> dict[str, str]:
    return {'status': 'ok'}
