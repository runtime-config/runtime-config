from fastapi import FastAPI


def init_routes(app: FastAPI) -> None:
    from runtime_config.web.views import router

    app.include_router(router)
