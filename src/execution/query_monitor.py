import time
from typing import Dict, List


class QueryMonitor:
    def __init__(self, slow_query_threshold: float = 5.0):
        self.slow_query_threshold = slow_query_threshold
        self.query_stats: Dict[str, Dict] = {}

    def record_query(self, sql: str, duration: float, success: bool):
        if sql not in self.query_stats:
            self.query_stats[sql] = {
                "count": 0,
                "total_duration": 0,
                "success_count": 0,
                "failure_count": 0
            }

        stats = self.query_stats[sql]
        stats["count"] += 1
        stats["total_duration"] += duration

        if success:
            stats["success_count"] += 1
        else:
            stats["failure_count"] += 1

        if duration > self.slow_query_threshold:
            stats["is_slow"] = True
            stats["slow_duration"] = duration

    def get_slow_queries(self) -> List[str]:
        return [
            sql for sql, stats in self.query_stats.items()
            if stats.get("is_slow")
        ]

    def get_query_stats(self, sql: str) -> Dict:
        return self.query_stats.get(sql, {})

    def get_all_stats(self) -> Dict[str, Dict]:
        return self.query_stats

    def clear_stats(self):
        self.query_stats = {}

    def get_success_rate(self, sql: str) -> float:
        stats = self.query_stats.get(sql, {})
        count = stats.get("count", 0)
        if count == 0:
            return 0.0
        success = stats.get("success_count", 0)
        return (success / count) * 100

    def get_average_duration(self, sql: str) -> float:
        stats = self.query_stats.get(sql, {})
        count = stats.get("count", 0)
        if count == 0:
            return 0.0
        total = stats.get("total_duration", 0)
        return total / count
