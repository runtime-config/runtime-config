import copy

from aiopg.sa import SAConnection
from httpx import AsyncClient
from pytest_mock import MockerFixture

from runtime_config.enums.settings import ValueType
from tests.db_utils import count_settings, create_setting, get_all_settings


async def test_create_setting(mocker: MockerFixture, async_client: AsyncClient, db_conn: SAConnection, setting_data):
    # arrange
    url = '/setting/create'

    setting_data['value_type'] = setting_data['value_type'].value
    setting_data.pop('created_by_db_user')

    expected_setting = {**setting_data}

    # act
    resp = await async_client.post(url, json=setting_data)
    resp_data = resp.json()

    count_setting = await count_settings(db_conn)

    resp_second = await async_client.post(url, json=setting_data)
    resp_second_data = resp_second.json()

    # assert
    assert count_setting == 1
    assert resp.status_code == 200
    assert resp_data == {
        'id': mocker.ANY,
        'created_by_db_user': 'admin',
        'updated_at': mocker.ANY,
        **expected_setting,
    }
    assert resp_second.status_code == 400
    assert resp_second_data == {'status': 'error', 'message': 'Variable with the same name already exists'}


async def test_create_setting__raise_unexpected_exc__return_400(
    mocker: MockerFixture, async_client: AsyncClient, db_conn: SAConnection, setting_data
):
    # arrange
    url = '/setting/create'
    mocker.patch('runtime_config.web.views.db_repo.create_new_setting').return_value = None

    setting_data['value_type'] = setting_data['value_type'].value
    setting_data.pop('created_by_db_user')

    # act
    resp = await async_client.post(url, json=setting_data)
    resp_data = resp.json()

    # assert
    assert resp.status_code == 400
    assert resp_data == {'status': 'error', 'message': 'Failed to create new setting'}


async def test_delete_setting(async_client: AsyncClient, db_conn: SAConnection, setting_data):
    # arrange
    created = await create_setting(db_conn, setting_data)
    url = f'/setting/delete/{created["id"]}'

    # act
    resp = await async_client.get(url)
    resp_data = resp.json()

    # assert
    assert resp.status_code == 200
    assert resp_data == {'status': 'success'}
    assert len(await get_all_settings(db_conn)) == 0


async def test_delete_setting__setting_not_found__return_400(
    async_client: AsyncClient, db_conn: SAConnection, setting_data
):
    # arrange
    url = f'/setting/delete/{999}'

    # act
    resp = await async_client.get(url)
    resp_data = resp.json()

    # assert
    assert resp.status_code == 400
    assert resp_data == {'status': 'error', 'message': 'Could not find the setting with the specified id'}


async def test_edit_setting(mocker: MockerFixture, async_client: AsyncClient, db_conn: SAConnection, setting_data):
    # arrange
    url = '/setting/edit'
    created = await create_setting(db_conn, setting_data)
    new = {
        'id': created['id'],
        'value': '99',
    }

    # act
    resp = await async_client.post(url, json=new)
    resp_data = resp.json()

    # assert
    assert resp.status_code == 200
    assert resp_data == {
        **created,
        'id': mocker.ANY,
        'value': new['value'],
        'updated_at': mocker.ANY,
    }


async def test_edit_setting__setting_not_found__return_400(
    async_client: AsyncClient, db_conn: SAConnection, setting_data
):
    # arrange
    url = '/setting/edit'
    payload = {'id': 999, 'name': 'some_name'}

    # act
    resp = await async_client.post(url, json=payload)
    resp_data = resp.json()

    # assert
    assert resp.status_code == 400
    assert resp_data == {'status': 'error', 'message': 'Setting with the specified id was not found'}


async def test_get_setting(mocker: MockerFixture, async_client: AsyncClient, db_conn: SAConnection, setting_data):
    # arrange
    created = await create_setting(db_conn, setting_data)
    await async_client.post('/setting/edit', json={'id': created['id'], 'value': '444'})
    expected_resp_with_history = {
        'change_history': [
            {
                'created_by_db_user': 'admin',
                'deleted_by_db_user': None,
                'disabled': False,
                'id': mocker.ANY,
                'is_deleted': False,
                'name': 'timeout',
                'service_name': 'service-name',
                'updated_at': mocker.ANY,
                'value': '10',
                'value_type': 'int',
            }
        ],
        'setting': {
            'created_by_db_user': 'admin',
            'disabled': False,
            'id': mocker.ANY,
            'name': 'timeout',
            'service_name': 'service-name',
            'updated_at': mocker.ANY,
            'value': '444',
            'value_type': 'int',
        },
    }
    expected_resp = copy.deepcopy(expected_resp_with_history)
    expected_resp['change_history'] = None

    # act
    resp = await async_client.get(f'/setting/get/{created["id"]}')
    resp_data = resp.json()

    resp_with_history = await async_client.get(f'/setting/get/{created["id"]}?include_history=true')
    resp_data_with_history = resp_with_history.json()

    # assert
    assert resp.status_code == 200
    assert resp_data == expected_resp

    assert resp_with_history.status_code == 200
    assert resp_data_with_history == expected_resp_with_history


async def test_get_settings__getting_a_non_existent_setting__return_empty_resp(
    async_client: AsyncClient, db_conn: SAConnection, setting_data
):
    # act
    resp = await async_client.get('/setting/get/999')
    resp_data = resp.json()

    # assert
    assert resp.status_code == 200
    assert resp_data == {'change_history': None, 'setting': None}


async def test_search_settings(mocker: MockerFixture, async_client: AsyncClient, db_conn: SAConnection, setting_data):
    # arrange
    await create_setting(db_conn, setting_data)
    await create_setting(
        db_conn,
        {
            **setting_data,
            'name': 'name',
            'value': 'Dima',
            'value_type': ValueType.str,
        },
    )

    # act
    resp = await async_client.post('/setting/search', json={'search_params': {'name': 'timeou'}})
    resp_data = resp.json()

    # assert
    assert resp.status_code == 200
    assert resp_data == [
        {
            'id': mocker.ANY,
            'name': setting_data['name'],
            'value': setting_data['value'],
            'value_type': setting_data['value_type'].value,
            'service_name': setting_data['service_name'],
            'created_by_db_user': 'admin',
            'disabled': setting_data['disabled'],
            'updated_at': mocker.ANY,
        }
    ]


async def test_search_settings__search_for_settings_of_a_non_existing_service__return_empty_list(
    async_client: AsyncClient, db_conn: SAConnection, setting_data
):
    # arrange
    await create_setting(db_conn, setting_data)

    # act
    resp = await async_client.post('/setting/search', json={'search_params': {'service_name': 'other'}})
    resp_data = resp.json()

    # assert
    assert resp.status_code == 200
    assert resp_data == []


async def test_get_all_service_settings(
    mocker: MockerFixture, async_client: AsyncClient, db_conn: SAConnection, setting_data
):
    # arrange
    await create_setting(db_conn, setting_data)
    service_name = setting_data["service_name"]

    # act
    resp = await async_client.post(f'/setting/all/{service_name}', json={})
    resp_data = resp.json()

    # assert
    assert resp.status_code == 200
    assert resp_data == [
        {
            **setting_data,
            'id': mocker.ANY,
            'value_type': setting_data['value_type'].value,
            'updated_at': mocker.ANY,
        }
    ]


async def test_get_all_service_settings__use_custom_limit_and_offset(
    async_client: AsyncClient, db_conn: SAConnection, setting_data
):
    # arrange
    service_name = setting_data["service_name"]
    for name in ('timeout', 'timeout1', 'timeout2', 'timeout3'):
        await create_setting(db_conn, {**setting_data, 'name': name})

    # act
    resp = await async_client.post(f'/setting/all/{service_name}', json={'offset': 0, 'limit': 2})
    resp_data = resp.json()

    resp1 = await async_client.post(f'/setting/all/{service_name}', json={'offset': 2, 'limit': 2})
    resp1_data = resp1.json()

    # assert
    assert resp.status_code == 200
    assert [i['name'] for i in resp_data] == ['timeout', 'timeout1']

    assert resp1.status_code == 200
    assert [i['name'] for i in resp1_data] == ['timeout2', 'timeout3']


async def test_get_service_settings(async_client: AsyncClient, db_conn: SAConnection, setting_data):
    # arrange
    await create_setting(db_conn, setting_data)
    url = f'/get_settings/{setting_data["service_name"]}'

    # act
    resp = await async_client.get(url)
    resp_data = resp.json()

    # assert
    assert len(resp_data) == 1
    assert resp_data[0] == {
        'name': setting_data['name'],
        'value': setting_data['value'],
        'value_type': setting_data['value_type'].value,
        'disable': setting_data['disabled'],
    }


async def test_health_check(async_client, db, setting_data):
    # act
    resp = await async_client.get('/health-check')

    # assert
    assert resp.json() == {'status': 'ok'}
