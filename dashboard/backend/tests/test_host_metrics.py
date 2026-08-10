"""Unit tests for host metrics collection (stdlib fallbacks + optional psutil)."""

from dashboard.backend import host_metrics


def test_collect_host_metrics_shape():
    data = host_metrics.collect_host_metrics()
    assert isinstance(data["platform"], str)
    assert "ram" in data and "disk" in data
    assert set(data["ram"]) >= {"used_bytes", "total_bytes", "percent"}
    assert set(data["disk"]) >= {"used_bytes", "total_bytes", "percent", "path"}
    assert data["disk"]["total_bytes"] is None or data["disk"]["total_bytes"] > 0
    assert "process" in data
    assert data["process"]["pid"] > 0
    assert isinstance(data["collected_at"], float)


def test_pct_helper():
    assert host_metrics._pct(50, 100) == 50.0
    assert host_metrics._pct(None, 100) is None
    assert host_metrics._pct(10, 0) is None
