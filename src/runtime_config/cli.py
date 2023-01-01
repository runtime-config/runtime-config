import asyncio

import click
import uvicorn

from runtime_config.services.account.create_admin_cmd import (
    create_admin as create_admin_cmd,
)


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option('--host', default='0.0.0.0')
@click.option('--port', default=8080)
@click.option('--reload', default=False, is_flag=True)
@click.option('--workers', default=None, type=int)
@click.option('--access_log', default=True, type=bool)
def serve(host: str, port: int, reload: bool, workers: int | None, access_log: bool) -> None:
    uvicorn.run(
        'runtime_config.wsgi:app',
        host=host,
        port=port,
        reload=reload,
        workers=workers,
        log_config={'version': 1, 'disable_existing_loggers': False},
        access_log=access_log,
    )


@cli.command()
def create_admin() -> None:
    asyncio.run(create_admin_cmd())


if __name__ == '__main__':
    cli()
