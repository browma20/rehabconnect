def test_generate_therapist_explanation_mentions_metrics_and_gaps(automation_service):
    explanation, risk_messages, data_gap_messages = automation_service.generate_therapist_explanation(
        therapist={'name': 'Alice Smith', 'discipline': 'PT'},
        scores={
            'availability_score': 85,
            'reliability_score': 92,
            'performance_score': 88,
            'caseload_balance_score': 70,
            'total_score': 86,
            'rank': 1,
        },
        risks=['low_reliability'],
        data_flags={
            'missing_availability': False,
            'missing_reliability': False,
            'missing_performance': True,
            'missing_caseload': False,
            'missing_timeoff': False,
        },
    )

    assert 'reliability 92.0' in explanation
    assert any('Reliability score is below preferred threshold' in item for item in risk_messages)
    assert any('Performance data is missing' in item for item in data_gap_messages)


def test_generate_summary_explanation_uses_high_confidence_language(automation_service):
    summary = automation_service.generate_summary_explanation(
        recommendations=[{'name': 'Alice Smith', 'score': 95.0}],
        confidence_components={
            'match_quality': 95.0,
            'candidate_spread': 85.0,
            'data_completeness': 100.0,
            'risk_adjustment': 100.0,
        },
        global_risks=[],
        data_flags={},
    )

    assert 'Confidence is high.' in summary
    assert 'High confidence due to strong match quality' in summary


def test_generate_summary_explanation_uses_cautious_language_and_mentions_risks(automation_service):
    summary = automation_service.generate_summary_explanation(
        recommendations=[{'name': 'Alice Smith', 'score': 52.0}],
        confidence_components={
            'match_quality': 40.0,
            'candidate_spread': 5.0,
            'data_completeness': 70.0,
            'risk_adjustment': 45.0,
        },
        global_risks=['Near weekly capacity'],
        data_flags={'missing_reliability': 20},
    )

    assert 'Confidence is low.' in summary
    assert 'manual decision is recommended' in summary
    assert 'Major risks: Near weekly capacity.' in summary
    assert 'Data gaps: Reliability data is missing.' in summary
