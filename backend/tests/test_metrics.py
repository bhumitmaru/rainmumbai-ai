import math

from app.services.metrics import direction_accuracy, direction_f1, mae, rmse


def test_mae():
    assert mae([(2.0, 0.0), (4.0, 0.0)]) == 3.0
    assert mae([]) is None


def test_rmse():
    assert rmse([(3.0, 0.0), (4.0, 0.0)]) == round(math.sqrt(12.5), 4)
    assert rmse([]) is None


def test_direction_accuracy():
    assert direction_accuracy([("Increase", "Increase"), ("Decrease", "No Change")]) == 0.5
    assert direction_accuracy([]) is None


def test_direction_f1():
    perfect = [("Increase", "Increase"), ("No Change", "No Change"), ("Decrease", "Decrease")]
    assert direction_f1(perfect) == 1.0
    assert direction_f1([]) is None
