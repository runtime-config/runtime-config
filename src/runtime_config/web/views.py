import typing as t

from fastapi import APIRouter

from runtime_config.repositories.db.repo import get_service_settings
from runtime_config.web.entities import GetSettingsResponse

router = APIRouter()


@router.get('/get_settings/{service_name}', response_model=list[GetSettingsResponse])
async def get_settings(service_name: str) -> list[dict[str, t.Any]]:
    return [setting async for setting in get_service_settings(service_name)]


@router.get('/health-check')
def health_check() -> dict[str, str]:
    return {'status': 'ok'}
