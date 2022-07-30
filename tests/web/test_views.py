from tests.db_utils import create_setting


async def test_get_settings(async_client, db, setting_data):
    # arrange
    await create_setting(db, setting_data)
    url = f'/get_settings/{setting_data["service_name"]}'

    # act
    resp = await async_client.get(url)

    # assert
    assert resp.json() == [
        {
            'name': setting_data['name'],
            'value': setting_data['value'],
            'value_type': setting_data['value_type'].value,
            'disable': setting_data['disable'],
        }
    ]


async def test_health_check(async_client, db, setting_data):
    # act
    resp = await async_client.get('/health-check')

    # assert
    assert resp.json() == {'status': 'ok'}
