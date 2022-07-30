FROM python:3.10-slim-buster

ARG CURRENT_ENV=prod
ENV POETRY_VERSION=1.1.13

WORKDIR /opt/app/

RUN groupadd app_user \
    && useradd --gid app_user --shell /bin/bash --create-home app_user \
    && apt update \
    && apt upgrade -y \
    && apt install -y wget gcc libpq-dev python3-dev \
    && ln -s /root/.poetry/bin/poetry /usr/bin/poetry \
    && wget https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py \
    && python ./get-poetry.py --version $POETRY_VERSION \
    && poetry config virtualenvs.create false \
    && rm ./get-poetry.py \
    && apt purge -y wget \
    && apt autoremove -y \
    && apt autoclean -y \
    && rm -fr /var/lib/apt/lists /var/lib/cache/* /var/log/*

COPY pyproject.toml poetry.lock /opt/app/

COPY src/ /opt/app/src
COPY migrations/ /opt/app/migrations
COPY alembic.ini/ /opt/app/

RUN /bin/bash -c 'poetry install $(test "$CURRENT_ENV" == prod && echo "--no-dev") --no-interaction --no-ansi'

USER app_user

ENTRYPOINT ["runtime-config"]
