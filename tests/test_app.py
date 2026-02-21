from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'


def test_profile_primary_script_and_coaching():
    payload = {
        'avoidance': [10, 10, 10, 10],
        'worship': [2, 2, 2, 2],
        'status': [2, 2, 2, 2],
        'vigilance': [3, 3, 3, 3],
    }
    response = client.post('/api/profile', json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data['primary_script'] == 'money_avoidance'
    assert data['risk_bands']['avoidance'] == 'active_risk'


def test_scenario_has_affordability_flag():
    payload = {
        'city': 'Izmir',
        'gross_monthly_income': 70000,
        'rent': 13156,
        'utilities': 2100,
        'transportation': 1500,
        'groceries': 10500,
        'discretionary': 6000,
        'target_savings_rate': 0.2,
    }
    response = client.post('/api/scenario', json=payload)
    assert response.status_code == 200
    data = response.json()
    assert 'projected_savings_rate' in data
    assert isinstance(data['affordable'], bool)


def test_cancel_requires_consent():
    payload = {
        'service_name': 'Gym',
        'monthly_cost': 20,
        'cancellation_reason': 'Not used',
        'user_consent': False,
    }
    response = client.post('/api/subscription/cancel-script', json=payload)
    assert response.status_code == 400


def test_index_alias_and_frontend_fallback_are_served():
    root = client.get('/')
    index = client.get('/index.html')
    random_path = client.get('/v1')

    assert root.status_code == 200
    assert index.status_code == 200
    assert random_path.status_code == 200
    assert 'Financial Therapy Coach' in random_path.text


def test_api_fallback_stays_404():
    response = client.get('/api/does-not-exist')
    assert response.status_code == 404
