"""Compute insights from live connections and rolling history.

The engine turns raw data into the human-facing signals shown in the Insights
panel and the Daily Report: newly seen endpoints, frequent talkers, provider and
country concentration, and per-application breakdowns. Results pass through the
``FILTER_INSIGHTS`` hook so plugins can augment or redact them.
"""

from __future__ import annotations

import time
from collections import Counter
from dataclasses import dataclass, field

from ..hooks import HookName, hooks
from ..model import ConnectionKind
from ..state import HistoryStore, LiveStore


@dataclass
class InsightsSnapshot:
    """A point-in-time summary of network activity."""

    generated_at: float
    total_connections: int = 0
    mapped_connections: int = 0
    new_endpoints: list[str] = field(default_factory=list)
    frequent_endpoints: list[dict] = field(default_factory=list)
    top_countries: list[tuple[str, int]] = field(default_factory=list)
    top_processes: list[tuple[str, int]] = field(default_factory=list)
    unmapped_count: int = 0
    listening_count: int = 0

    def as_dict(self) -> dict:
        """Return a JSON-serialisable representation."""
        return {
            "generated_at": self.generated_at,
            "total_connections": self.total_connections,
            "mapped_connections": self.mapped_connections,
            "new_endpoints": self.new_endpoints,
            "frequent_endpoints": self.frequent_endpoints,
            "top_countries": self.top_countries,
            "top_processes": self.top_processes,
            "unmapped_count": self.unmapped_count,
            "listening_count": self.listening_count,
        }


class InsightsEngine:
    """Derive :class:`InsightsSnapshot` values from live + historical state."""

    def __init__(
        self,
        store: LiveStore,
        history: HistoryStore,
        frequent_threshold: int = 5,
    ) -> None:
        self._store = store
        self._history = history
        self.frequent_threshold = frequent_threshold

    def compute(self) -> InsightsSnapshot:
        """Compute a fresh snapshot and emit the insights hooks."""
        connections = self._store.all()
        now = time.time()

        new_endpoints = [
            c.remote_ip
            for c in connections
            if c.kind is ConnectionKind.REMOTE and self._history.is_new(c.remote_ip)
        ]

        frequent = [
            {
                "ip": e.ip,
                "hits": e.hits,
                "country": e.country,
                "city": e.city,
                "processes": e.processes,
            }
            for e in self._history.frequent(self.frequent_threshold)[:20]
        ]

        country_counter: Counter[str] = Counter()
        process_counter: Counter[str] = Counter()
        for c in connections:
            if c.location and c.location.country:
                country_counter[c.location.country] += 1
            if c.process:
                process_counter[c.process] += 1

        snapshot = InsightsSnapshot(
            generated_at=now,
            total_connections=len(connections),
            mapped_connections=sum(1 for c in connections if c.is_mapped),
            new_endpoints=sorted(set(new_endpoints)),
            frequent_endpoints=frequent,
            top_countries=country_counter.most_common(10),
            top_processes=process_counter.most_common(10),
            unmapped_count=len(self._store.unmapped()),
            listening_count=len(self._store.listening_ports()),
        )

        hooks.emit(HookName.INSIGHTS_UPDATED, insights=snapshot)
        filtered = hooks.filter(HookName.FILTER_INSIGHTS, snapshot)
        return filtered if isinstance(filtered, InsightsSnapshot) else snapshot

    def daily_report(self) -> dict:
        """Produce a compact daily report from rolling history."""
        entries = self._history.all_entries()
        country_totals = self._history.country_totals()
        process_counter: Counter[str] = Counter()
        for entry in entries:
            for proc in entry.processes:
                process_counter[proc] += entry.hits

        report = {
            "generated_at": time.time(),
            "distinct_endpoints": len(entries),
            "total_hits": sum(e.hits for e in entries),
            "countries": list(country_totals.items())[:15],
            "top_applications": process_counter.most_common(15),
            "busiest_endpoints": [
                {"ip": e.ip, "hits": e.hits, "country": e.country}
                for e in sorted(entries, key=lambda x: x.hits, reverse=True)[:15]
            ],
        }
        hooks.emit(HookName.DAILY_REPORT_GENERATED, report=report)
        return report
