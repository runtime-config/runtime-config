FROM python:3.10-slim-buster

ENV POETRY_VERSION=1.2.2

WORKDIR /opt/app/

RUN apt update && apt install -y gcc libpq-dev
RUN pip install poetry==$POETRY_VERSION \
    && poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock /opt/app/

RUN poetry export --only=main --without-hashes -o requirements.txt \
    && psycopg2_pkg=$(cat requirements.txt | perl -n -e '/(^psycopg2==.*)\s;/ && print $1') \
    && pip wheel $psycopg2_pkg


FROM python:3.10-slim-buster

WORKDIR /opt/app/

RUN groupadd app_user \
    && useradd --gid app_user --shell /bin/bash --create-home app_user \
    && apt update \
    && apt install -y libpq-dev \
    && apt autoremove -y \
    && apt autoclean -y \
    && rm -fr /var/lib/apt/lists /var/lib/cache/* /var/log/*

COPY --from=0 /opt/app/pyproject.toml /opt/app/requirements.txt /opt/app/psycopg2-*.whl ./
RUN pip install psycopg2-*.whl \
    && pip install -r requirements.txt \
    && pip install --force-reinstall psycopg2-*.whl \
    && rm -rf /root/.cache/pip \
    && rm /opt/app/psycopg2-*.whl

COPY src/ /opt/app/src
COPY migrations/ /opt/app/migrations
COPY alembic.ini/ /opt/app/

RUN pip install . && rm -rf /root/.cache/pip

USER app_user

ENTRYPOINT ["runtime-config"]
