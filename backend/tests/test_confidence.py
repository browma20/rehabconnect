def test_compute_confidence_is_high_when_all_inputs_are_strong(automation_service):
    payload = automation_service.compute_confidence(
        top_score=96.0,
        second_score=8.0,
        data_flags={},
        risk_flags={},
    )

    assert payload['confidence'] >= 0.9
    assert payload['components']['match_quality'] == 96.0
    assert payload['components']['data_completeness'] == 100.0
    assert payload['components']['risk_adjustment'] == 100.0


def test_compute_confidence_is_low_with_weak_match_and_high_risk(automation_service):
    payload = automation_service.compute_confidence(
        top_score=30.0,
        second_score=25.0,
        data_flags={},
        risk_flags={
            'overload_risk': 20,
            'predictive_alert': 25,
            'timeoff_proximity': 15,
            'high_cancellation_risk': 20,
            'marketplace_failures': 10,
        },
    )

    assert payload['components']['risk_adjustment'] == 10.0
    assert payload['confidence'] == 0.35


def test_missing_data_reduces_data_completeness_and_confidence(automation_service):
    no_penalty = automation_service.compute_confidence(
        top_score=88.0,
        second_score=44.0,
        data_flags={},
        risk_flags={},
    )
    with_penalty = automation_service.compute_confidence(
        top_score=88.0,
        second_score=44.0,
        data_flags={
            'missing_availability': 20,
            'missing_reliability': 20,
        },
        risk_flags={},
    )

    assert with_penalty['components']['data_completeness'] == 60.0
    assert with_penalty['confidence'] < no_penalty['confidence']
