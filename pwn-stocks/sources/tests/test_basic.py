# Start via `make test-debug` or `make test-release`
async def test_add_game(service_client):
    response = await service_client.post('/add_game', json={
        'description': 'Test Description',
        'field': [[0] * 10] * 10
    })
    assert response.status == 200
