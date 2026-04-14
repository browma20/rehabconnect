from flask import Flask

from backend.app.routes import automation_routes
from backend.app.routes.automation_routes import automation_bp
from backend.app.services.automation_suggestion_service import AutomationSuggestionService


class DummyDb:
    def close(self):
        return None


def create_test_client(monkeypatch):
    monkeypatch.setattr(automation_routes, 'SessionLocal', lambda: DummyDb())
    app = Flask(__name__)
    app.register_blueprint(automation_bp, url_prefix='/api')
    return app.test_client()


def test_suggest_assignment_api_contract_success(monkeypatch):
    monkeypatch.setattr(
        AutomationSuggestionService,
        'suggest_assignment',
        lambda self, session_id, performed_by=None: {
            'success': True,
            'session_id': session_id,
            'recommendations': [
                {
                    'therapist_id': 'THER001',
                    'score': 91.5,
                    'explanation': 'Top recommendation: Alice Smith scored 91.5.',
                    'risks': ['Near weekly capacity'],
                    'data_gaps': ['Reliability data is missing'],
                }
            ],
            'confidence': 0.86,
            'confidence_components': {
                'match_quality': 91.5,
                'candidate_spread': 70.0,
                'data_completeness': 80.0,
                'risk_adjustment': 90.0,
            },
            'summary_explanation': 'Confidence is high.',
            'global_risks': ['Near weekly capacity'],
        },
    )

    client = create_test_client(monkeypatch)
    response = client.post('/api/automation/suggest-assignment', json={'session_id': 'SCHED001'})
    payload = response.get_json()

    assert response.status_code == 200
    assert payload['success'] is True
    assert payload['data']['session_id'] == 'SCHED001'
    assert 'recommendations' in payload['data']
    assert 'confidence' in payload['data']
    assert 'confidence_components' in payload['data']
    assert 'summary_explanation' in payload['data']
    assert 'global_risks' in payload['data']
    assert {'therapist_id', 'score', 'explanation', 'risks', 'data_gaps'} <= set(payload['data']['recommendations'][0].keys())


def test_suggest_reschedule_api_contract_success(monkeypatch):
    monkeypatch.setattr(
        AutomationSuggestionService,
        'suggest_reschedule',
        lambda self, session_id, performed_by=None: {
            'success': True,
            'session_id': session_id,
            'current_time': '2026-04-06T10:00:00Z',
            'recommendations': [
                {
                    'start_time': '10:00:00',
                    'end_time': '11:00:00',
                    'score': 88.0,
                    'explanation': 'Top recommendation: Alice Smith scored 88.0.',
                    'risks': ['Near weekly capacity'],
                    'data_gaps': ['Time-off data is missing'],
                }
            ],
            'confidence': 0.74,
            'confidence_components': {
                'match_quality': 88.0,
                'candidate_spread': 35.0,
                'data_completeness': 90.0,
                'risk_adjustment': 85.0,
            },
            'summary_explanation': 'Confidence is medium.',
            'global_risks': ['Near weekly capacity'],
        },
    )

    client = create_test_client(monkeypatch)
    response = client.post('/api/automation/suggest-reschedule', json={'session_id': 'SCHED001'})
    payload = response.get_json()

    assert response.status_code == 200
    assert payload['success'] is True
    assert payload['data']['session_id'] == 'SCHED001'
    assert 'current_time' in payload['data']
    assert 'recommendations' in payload['data']
    assert 'confidence' in payload['data']
    assert 'confidence_components' in payload['data']
    assert 'summary_explanation' in payload['data']
    assert 'global_risks' in payload['data']
    assert {'start_time', 'end_time', 'score', 'explanation', 'risks', 'data_gaps'} <= set(payload['data']['recommendations'][0].keys())


def test_automation_routes_return_safe_error_payloads(monkeypatch):
    monkeypatch.setattr(
        AutomationSuggestionService,
        'suggest_assignment',
        lambda self, session_id, performed_by=None: {'success': False, 'error': 'Session not found'},
    )

    client = create_test_client(monkeypatch)
    response = client.post('/api/automation/suggest-assignment', json={'session_id': 'UNKNOWN'})
    payload = response.get_json()

    assert response.status_code == 404
    assert payload['success'] is False
    assert 'error' in payload


def test_automation_routes_validate_missing_session_id(monkeypatch):
    client = create_test_client(monkeypatch)
    response = client.post('/api/automation/suggest-reschedule', json={})
    payload = response.get_json()

    assert response.status_code == 400
    assert payload == {'success': False, 'error': 'session_id is required'}