![license](https://img.shields.io/github/license/aleksey925/runtime-config?style=for-the-badge) [![version](https://img.shields.io/github/v/release/aleksey925/runtime-config?display_name=tag&style=for-the-badge)](https://github.com/aleksey925/runtime-config/pkgs/container/runtime-config) ![coverage](https://img.shields.io/codecov/c/github/aleksey925/runtime-config/master?style=for-the-badge) [![tests status](https://img.shields.io/github/workflow/status/aleksey925/runtime-config/Tests/master?style=for-the-badge)](https://github.com/aleksey925/runtime-config/actions?query=branch%3Amaster)

runtime-config
==============

Server for storing service settings. Together with the [client](https://github.com/aleksey925/runtime-config-py), it
allows you to change application settings at runtime.

Table of contents:

- [Overview](#overview)
- [Usage](#usage)
- [Deploy](#deploy)
- [Build docker image](#build-docker-image)
- [Development](#development)
  - [Setting up a local development environment on macOS with Apple Silicone](#setting-up-a-local-development-environment-on-macos-with-apple-silicone)
  - [Start service locally](#start-service-locally)
  - [Start service in docker](#start-service-in-docker)
  - [Work with migrations](#work-with-migrations)


# Overview

This application is responsible for storing settings and providing an API for the client library. If you want to see
the api of this service, follow the [link](http://0.0.0.0:8080/docs) after starting the service. Swagger will be
available there.

It's very important for understanding who created / changed some settings when a team has the ability to change
application settings in real time. Therefore, the database implements logging of all changes to the setting table.
You can see them in the setting_history table. The logs contain information about users who made changes and when
changes were made.

# Usage

At the moment, WEB UI is not implemented, so now you need to edit the description of variables directly in the service
database. You can do this in the settings table.

An example of a request to create a variable that will be used in `some-service-name` service:

```sql
INSERT INTO setting(name, value, value_type, service_name)
VALUES ('timeout', '1', 'int', 'some-service-name');
```

With the help of the [client](https://github.com/aleksey925/runtime-config-py), this variable can be get like this:

```python
source = ConfigServerSrc(host='http://127.0.0.1:8080', service_name='some-service-name')
config = await RuntimeConfig.create(init_settings={}, source=source)
print(config.get('timeout'))
```

If you want to change the value of a nested variable, then use the following query:

```sql
INSERT INTO setting(name, value, value_type, service_name)
VALUES ('db__timeout', '1', 'int', 'some-service-name');
```

With the help of the [client](https://github.com/aleksey925/runtime-config-py), this variable can be get like this:

```python
source = ConfigServerSrc(host='http://127.0.0.1:8080', service_name='some-service-name')
config = await RuntimeConfig.create(init_settings={'db': {'timeout': 10}}, source=source)
print(config.db['timeout'])
```

Available variable types:

- str
- int
- bool
- null
- json

# Deploy

**docker-compose**

1. Create a `.env` file with the necessary environment variables. An example of an `.env` file can be found in
`.env.example`.

2. Copy docker-compose.yml.

3. Start the service and its dependencies.

   ```
   docker compose up
   ```

**Other**

1. Define all environment variables necessary for the service to work. You can find them in `.env.example`.

2. Select a docker image with the latest version of the application. You can find docker images
[here](https://github.com/aleksey925/runtime-config/pkgs/container/runtime-config).

3. Deploy postgres.

4. Apply all migrations to postgres. Run the following `alembic upgrade head` command inside the docker image.

5. Run the selected docker image. When starting, you need to pass the `serve` argument, which means that the web
application will be launched to process requests from client libraries.

# Build docker image

An example command for building a docker image with an application of version 0.1.0

```
ver=0.1.0 make build-img
```


# Development

## Setting up a local development environment on macOS with Apple Silicone

1. Install brew.

    ```
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    ```

2. Add to `~/.zshrc` and reopen console.

   ```
   # brew
   eval "$(/opt/homebrew/bin/brew shellenv)"

   # poetry
   export PATH="$HOME/.poetry/bin:$PATH"

   # pyenv
   eval "$(pyenv init --path)"

   # direnv
   eval "$(direnv hook zsh)"

   # Generates flags necessary for building from source C libraries
   export LDFLAGS=""
   export CPPFLAGS=""
   export PKG_CONFIG_PATH=""

   pkgs=(curl readline sqlite)
   for pkg in $pkgs; do
       pkg_dir="$HOMEBREW_PREFIX/opt/$pkg"

       lib_dir="$pkg_dir/lib"

       if [ -d "$lib_dir" ]; then
           export LDFLAGS="$LDFLAGS -L$lib_dir"
       fi

       include_dir="$pkg_dir/include"
       if [ -d "$include_dir" ]; then
           export CPPFLAGS="$CPPFLAGS -I$include_dir"
       fi

       pkg_config_dir="$lib_dir/pkgconfig"
       if [ -d "$pkg_config_dir" ]; then
           if [ "x$PKG_CONFIG_PATH" = "x" ]; then
               export PKG_CONFIG_PATH="$pkg_config_dir"
           else
               export PKG_CONFIG_PATH="PKG_CONFIG_PATH:$pkg_config_dir"
           fi
       fi
   done
   ```

3. Install required software.

    ```
    brew install wget direnv pyenv postgresql openssl
    ```

    ```
    brew install --cask docker
    ```

    ```
    wget https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py
    /usr/bin/python3 ./get-poetry.py
    poetry config virtualenvs.create false
    ```

    ```
    pyenv install 3.10.4
    ```

4. Disable background postgres service.

   ```
   /opt/homebrew/opt/postgresql/bin/postgres -D /opt/homebrew/var/postgres
   ```

5. Create configuration files. After creating the .env file, set the variables in it to the values you need.

    ```
    cp ./env.example ./.env
    cp ./envrc.example ./.envrc
    ```

6. Reopen console and run `direnv allow`. After executing this command, a virtual environment for python will be
created.

7. Install requirements.

    ```
    poetry install
    ```

8. Run tests to make sure the environment has been set up correctly.

    ```
    make tests
    ```

## Start service locally

1. Start postgres

   ```
   docker compose -f docker-compose.dev.yml up db
   ```

2. Run migrations

    ```
    make migrate
    ```

3. Start the service

   ```
   python ./src/runtime_config/cli.py serve --reload
   ```

## Start service in docker

```
make up
```

## Work with migrations

The automatic generation of the migration is done by the following command (you need to be careful and check what was
generated):

```
alembic revision --autogenerate -m <description>
```

Applying all migrations:

```
alembic upgrade head
```

Downgrade last migration:

```
alembic downgrade -1
```
