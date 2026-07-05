"""
Unit tests for the core analytics logic (analytics.py).
These run without any MQTT broker or network dependency, since the logic
being tested is deliberately decoupled from the transport layer.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from analytics import RollingStats


def test_rolling_window_respects_max_size():
    stats = RollingStats(window_size=3)
    for v in [1, 2, 3, 4, 5]:
        stats.add(v)
    assert len(stats.values) == 3
    assert list(stats.values) == [3, 4, 5]


def test_mean_and_stdev_basic():
    stats = RollingStats(window_size=5)
    for v in [10, 10, 10, 10]:
        stats.add(v)
    assert stats.mean == 10
    assert stats.stdev == 0


def test_zscore_zero_with_insufficient_data():
    stats = RollingStats(window_size=5)
    stats.add(10)
    assert stats.zscore(999) == 0.0


def test_zscore_detects_outlier():
    stats = RollingStats(window_size=10)
    for v in [20, 21, 19, 20, 21, 19, 20]:
        stats.add(v)
    # value far from the stable baseline should have a large |z-score|
    z = stats.zscore(50)
    assert abs(z) > 3


def test_is_anomaly_flags_extreme_value():
    stats = RollingStats(window_size=10)
    for v in [20, 21, 19, 20, 21, 19, 20]:
        stats.add(v)
    assert stats.is_anomaly(50, threshold=2.5) is True
    assert stats.is_anomaly(20.5, threshold=2.5) is False


def test_summary_reports_expected_fields():
    stats = RollingStats(window_size=5)
    for v in [1, 2, 3]:
        stats.add(v)
    summary = stats.summary()
    assert summary["count"] == 3
    assert summary["min"] == 1
    assert summary["max"] == 3
