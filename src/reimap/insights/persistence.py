"""Persist the most recent insights snapshot and daily reports.

Keeps a small on-disk trail so the UI can show the last computed insights
immediately after startup, before the first scan completes.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from ..app_dirs import data_dir
from ..logging_config import get_logger

log = get_logger("insights.persistence")


class InsightsPersistence:
    """Read/write the latest insights snapshot and archived daily reports."""

    def __init__(self) -> None:
        self._snapshot_path: Path = data_dir() / "insights_latest.json"
        self._reports_path: Path = data_dir() / "daily_reports.json"

    def save_snapshot(self, snapshot: dict) -> None:
        """Persist the latest insights snapshot."""
        try:
            self._snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")
        except OSError as exc:
            log.error("Could not persist insights snapshot: %s", exc)

    def load_snapshot(self) -> dict | None:
        """Load the last persisted insights snapshot, if any."""
        if not self._snapshot_path.exists():
            return None
        try:
            return json.loads(self._snapshot_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def archive_report(self, report: dict, keep: int = 30) -> None:
        """Append a daily report and trim the archive to ``keep`` entries."""
        archive = self.load_reports()
        archive.append({"archived_at": time.time(), "report": report})
        archive = archive[-keep:]
        try:
            self._reports_path.write_text(json.dumps(archive), encoding="utf-8")
        except OSError as exc:
            log.error("Could not archive daily report: %s", exc)

    def load_reports(self) -> list[dict]:
        """Return all archived daily reports (oldest first)."""
        if not self._reports_path.exists():
            return []
        try:
            data = json.loads(self._reports_path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except (OSError, json.JSONDecodeError):
            return []
