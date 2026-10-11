from app.index.confidence import (
    data_quality_score,
    direction_probabilities,
    model_performance_score,
    overall_confidence,
    stability_score,
)


def test_direction_probabilities_sum_to_100():
    probs = direction_probabilities([2.0, 2.5, 3.0, -1.0, 0.0])
    total = sum(probs.values())
    assert abs(total - 100.0) < 0.02
    assert probs["Increase"] > 0


def test_direction_probabilities_empty_fallback():
    probs = direction_probabilities([])
    assert abs(sum(probs.values()) - 100.0) < 0.02


def test_confidence_scores_in_bounds():
    assert 0.0 <= data_quality_score([]) <= 100.0
    assert 0.0 <= model_performance_score(None, None) <= 100.0
    assert 0.0 <= stability_score([], None, 2200.0) <= 100.0
    assert 0.0 <= overall_confidence(90.0, 85.0, 80.0) <= 100.0


def test_direction_probabilities_direction_map():
    probs = direction_probabilities([10.0, 10.0, 10.0])
    assert probs["Increase"] == 100.0
    assert probs["No Change"] == 0.0
    assert probs["Decrease"] == 0.0
