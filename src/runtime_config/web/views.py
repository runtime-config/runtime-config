import psycopg2.errors
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from runtime_config.enums.status import ResponseStatus
from runtime_config.repositories.db import repo as db_repo
from runtime_config.repositories.db.entities import SettingData
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
async def create_setting(payload: CreateNewSettingRequest) -> SettingData | JSONResponse:
    response: SettingData | JSONResponse
    try:
        created_setting = await db_repo.create_new_setting(payload.dict())
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
async def delete_setting(setting_id: int) -> OperationStatusResponse | JSONResponse:
    if await db_repo.delete_setting(setting_id):
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
async def edit_setting(payload: EditSettingRequest) -> SettingData | JSONResponse:
    response: SettingData | JSONResponse
    edited_setting = await db_repo.edit_setting(
        setting_id=payload.id, values=payload.dict(exclude={'id'}, exclude_unset=True)
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
async def get_setting(setting_id: int, include_history: bool = False) -> GetSettingResponse:
    found_setting, change_history = await db_repo.get_setting(setting_id=setting_id, include_history=include_history)
    return GetSettingResponse(setting=found_setting, change_history=change_history)


@router.post('/setting/search', response_model=list[SettingData])
async def search_settings(payload: SettingSearchRequest) -> list[SettingData]:
    return [
        setting
        async for setting in db_repo.search_settings(
            search_params=payload.search_params, offset=payload.offset, limit=payload.limit
        )
    ]


@router.post('/setting/all/{service_name}', response_model=list[SettingData])
async def get_all_service_settings(service_name: str, payload: GetAllSettingsRequest) -> list[SettingData]:
    return [
        setting
        async for setting in db_repo.get_service_settings(
            service_name=service_name,
            offset=payload.offset,
            limit=payload.limit,
        )
    ]


@router.get('/get_settings/{service_name}', response_model=list[GetServiceSettingsLegacyResponse], deprecated=True)
async def get_service_settings(service_name: str) -> list[SettingData]:
    # not removed for backwards compatibility with client library
    return [setting async for setting in db_repo.get_service_settings(service_name)]


@router.get('/health-check')
def health_check() -> dict[str, str]:
    return {'status': 'ok'}
