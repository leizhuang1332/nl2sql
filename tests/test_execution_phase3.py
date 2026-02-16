import pytest
from src.execution.query_monitor import QueryMonitor


def test_query_monitor_init():
    monitor = QueryMonitor()
    assert monitor.slow_query_threshold == 5.0
    assert monitor.query_stats == {}


def test_query_monitor_custom_threshold():
    monitor = QueryMonitor(slow_query_threshold=2.0)
    assert monitor.slow_query_threshold == 2.0


def test_query_monitor_record_query():
    monitor = QueryMonitor()
    monitor.record_query("SELECT * FROM users", 0.5, True)

    stats = monitor.get_query_stats("SELECT * FROM users")
    assert stats["count"] == 1
    assert stats["total_duration"] == 0.5
    assert stats["success_count"] == 1
    assert stats["failure_count"] == 0


def test_query_monitor_record_failure():
    monitor = QueryMonitor()
    monitor.record_query("SELECT * FROM users", 0.5, False)

    stats = monitor.get_query_stats("SELECT * FROM users")
    assert stats["count"] == 1
    assert stats["failure_count"] == 1


def test_query_monitor_multiple_queries():
    monitor = QueryMonitor()
    monitor.record_query("SELECT * FROM users", 0.5, True)
    monitor.record_query("SELECT * FROM users", 1.0, True)
    monitor.record_query("SELECT * FROM users", 0.3, False)

    stats = monitor.get_query_stats("SELECT * FROM users")
    assert stats["count"] == 3
    assert stats["total_duration"] == 1.8
    assert stats["success_count"] == 2
    assert stats["failure_count"] == 1


def test_query_monitor_slow_query_detection():
    monitor = QueryMonitor(slow_query_threshold=2.0)
    monitor.record_query("SELECT * FROM users", 3.0, True)

    stats = monitor.get_query_stats("SELECT * FROM users")
    assert stats["is_slow"] is True
    assert stats["slow_duration"] == 3.0


def test_query_monitor_fast_query_not_slow():
    monitor = QueryMonitor(slow_query_threshold=2.0)
    monitor.record_query("SELECT * FROM users", 1.0, True)

    stats = monitor.get_query_stats("SELECT * FROM users")
    assert stats.get("is_slow") is None


def test_query_monitor_get_slow_queries():
    monitor = QueryMonitor(slow_query_threshold=2.0)
    monitor.record_query("SELECT * FROM users", 3.0, True)
    monitor.record_query("SELECT * FROM orders", 1.0, True)

    slow_queries = monitor.get_slow_queries()
    assert len(slow_queries) == 1
    assert "SELECT * FROM users" in slow_queries


def test_query_monitor_get_all_stats():
    monitor = QueryMonitor()
    monitor.record_query("SELECT * FROM users", 0.5, True)
    monitor.record_query("SELECT * FROM orders", 1.0, True)

    all_stats = monitor.get_all_stats()
    assert len(all_stats) == 2


def test_query_monitor_clear_stats():
    monitor = QueryMonitor()
    monitor.record_query("SELECT * FROM users", 0.5, True)
    monitor.clear_stats()

    assert monitor.query_stats == {}


def test_query_monitor_success_rate():
    monitor = QueryMonitor()
    monitor.record_query("SELECT * FROM users", 0.5, True)
    monitor.record_query("SELECT * FROM users", 0.5, True)
    monitor.record_query("SELECT * FROM users", 0.5, False)
    monitor.record_query("SELECT * FROM users", 0.5, False)

    rate = monitor.get_success_rate("SELECT * FROM users")
    assert rate == 50.0


def test_query_monitor_success_rate_no_queries():
    monitor = QueryMonitor()
    rate = monitor.get_success_rate("SELECT * FROM users")
    assert rate == 0.0


def test_query_monitor_average_duration():
    monitor = QueryMonitor()
    monitor.record_query("SELECT * FROM users", 1.0, True)
    monitor.record_query("SELECT * FROM users", 3.0, True)
    monitor.record_query("SELECT * FROM users", 2.0, True)

    avg = monitor.get_average_duration("SELECT * FROM users")
    assert avg == 2.0


def test_query_monitor_average_duration_no_queries():
    monitor = QueryMonitor()
    avg = monitor.get_average_duration("SELECT * FROM users")
    assert avg == 0.0
