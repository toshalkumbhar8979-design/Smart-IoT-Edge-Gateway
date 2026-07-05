"""
analytics.py
------------
Pure, testable logic for rolling aggregation and anomaly detection.
Deliberately decoupled from MQTT/network code so it can be unit tested
in isolation (see tests/test_edge_gateway.py).
"""

import statistics
from collections import deque
from dataclasses import dataclass, field


@dataclass
class RollingStats:
    """Maintains a fixed-size rolling window of readings for one sensor/metric
    and computes summary statistics + anomaly flags on the fly."""

    window_size: int
    values: deque = field(init=False)

    def __post_init__(self):
        self.values = deque(maxlen=self.window_size)

    def add(self, value: float) -> None:
        self.values.append(value)

    @property
    def mean(self) -> float:
        return statistics.fmean(self.values) if self.values else 0.0

    @property
    def stdev(self) -> float:
        return statistics.pstdev(self.values) if len(self.values) > 1 else 0.0

    def zscore(self, value: float) -> float:
        """How many standard deviations `value` is from the current rolling mean.
        Returns 0 if there isn't enough data yet or the window has no variance."""
        if len(self.values) < 2 or self.stdev == 0:
            return 0.0
        return (value - self.mean) / self.stdev

    def is_anomaly(self, value: float, threshold: float) -> bool:
        return abs(self.zscore(value)) >= threshold

    def summary(self) -> dict:
        return {
            "count": len(self.values),
            "mean": round(self.mean, 2),
            "stdev": round(self.stdev, 2),
            "min": round(min(self.values), 2) if self.values else None,
            "max": round(max(self.values), 2) if self.values else None,
        }
