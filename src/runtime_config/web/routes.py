from fastapi import FastAPI

from runtime_config.services.account.security import JwtTokenService


def init_routes(app: FastAPI, jwt_token_service: JwtTokenService) -> None:
    from runtime_config.web.views import (
        account_views,
        common_router,
        setting_views,
        user_views,
    )

    account_views.init_deps(jwt_token_service)

    app.include_router(account_views.router)
    app.include_router(user_views.router)
    app.include_router(setting_views.router)
    app.include_router(common_router)
