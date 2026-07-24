"""Demo data seeding for reimap.

``reimap --demo`` seeds the live store with a curated, static set of realistic
connections spread across the globe instead of scanning real sockets. It exists
for two reasons: to let anyone evaluate the UI without installing a GeoIP database
or generating traffic, and to produce the screenshots in the documentation.

No real network activity is observed in demo mode.
"""

from __future__ import annotations

import time

from .model import Connection, ConnectionKind, GeoLocation
from .state import HistoryStore, LiveStore

# (ip, port, process, city, country, cc, lat, lon)
_SAMPLE = [
    ("140.82.121.4", 443, "code", "Ashburn", "United States", "US", 39.04, -77.49),
    ("151.101.1.140", 443, "firefox", "San Francisco", "United States", "US", 37.77, -122.42),
    ("104.16.132.229", 443, "firefox", "London", "United Kingdom", "GB", 51.51, -0.13),
    ("13.107.42.14", 443, "Teams", "Amsterdam", "Netherlands", "NL", 52.37, 4.90),
    ("142.250.185.78", 443, "chrome", "Frankfurt", "Germany", "DE", 50.11, 8.68),
    ("52.96.7.130", 443, "Outlook", "Dublin", "Ireland", "IE", 53.33, -6.25),
    ("35.190.247.1", 443, "python", "Mumbai", "India", "IN", 19.08, 72.88),
    ("203.0.113.9", 443, "slack", "Singapore", "Singapore", "SG", 1.35, 103.82),
    ("13.230.4.20", 443, "spotify", "Tokyo", "Japan", "JP", 35.68, 139.69),
    ("18.229.10.5", 443, "aws-cli", "São Paulo", "Brazil", "BR", -23.55, -46.63),
    ("54.153.10.7", 443, "docker", "Sydney", "Australia", "AU", -33.87, 151.21),
    ("185.199.108.153", 443, "git", "Toronto", "Canada", "CA", 43.65, -79.38),
    ("162.159.135.234", 443, "discord", "Paris", "France", "FR", 48.86, 2.35),
    ("104.244.42.1", 443, "app", "Madrid", "Spain", "ES", 40.42, -3.70),
    ("31.13.72.36", 443, "app", "Stockholm", "Sweden", "SE", 59.33, 18.06),
    ("77.88.55.60", 443, "browser", "Moscow", "Russia", "RU", 55.75, 37.62),
    ("119.75.217.3", 443, "browser", "Beijing", "China", "CN", 39.90, 116.40),
    ("196.10.52.1", 443, "curl", "Cape Town", "South Africa", "ZA", -33.92, 18.42),
    ("200.55.10.2", 443, "app", "Buenos Aires", "Argentina", "AR", -34.60, -58.38),
    ("41.203.72.1", 443, "app", "Nairobi", "Kenya", "KE", -1.29, 36.82),
    ("212.58.244.20", 443, "podcast", "Manchester", "United Kingdom", "GB", 53.48, -2.24),
    ("157.240.22.35", 443, "app", "Singapore", "Singapore", "SG", 1.35, 103.82),
    ("172.217.16.142", 443, "chrome", "Zurich", "Switzerland", "CH", 47.37, 8.54),
    ("52.84.150.10", 443, "cdn", "Seoul", "South Korea", "KR", 37.57, 126.98),
    ("34.117.59.81", 443, "backend", "Los Angeles", "United States", "US", 34.05, -118.24),
    ("91.198.174.192", 443, "wiki", "Vienna", "Austria", "AT", 48.21, 16.37),
    ("5.9.10.20", 443, "server", "Helsinki", "Finland", "FI", 60.17, 24.94),
    ("103.21.244.0", 443, "app", "Jakarta", "Indonesia", "ID", -6.21, 106.85),
    ("190.93.240.1", 443, "app", "Mexico City", "Mexico", "MX", 19.43, -99.13),
    ("45.60.10.5", 443, "api", "Dubai", "United Arab Emirates", "AE", 25.20, 55.27),
]

# Listening ports to populate the Open Ports panel.
_LISTEN = [
    (5432, "postgres", "127.0.0.1"),
    (6379, "redis-server", "127.0.0.1"),
    (8050, "reimap", "127.0.0.1"),
    (3000, "node", "0.0.0.0"),
    (22, "sshd", "0.0.0.0"),
]

# LAN peers for the LAN/Local panel.
_LAN = [
    ("192.168.1.1", 53, "systemd-resolve"),
    ("192.168.1.42", 445, "smbd"),
    ("192.168.1.10", 631, "cupsd"),
]


def build_demo_connections() -> list[Connection]:
    """Return the curated demo connection set with locations attached."""
    now = time.time()
    conns: list[Connection] = []

    for ip, port, proc, city, country, cc, lat, lon in _SAMPLE:
        conns.append(
            Connection(
                remote_ip=ip,
                remote_port=port,
                local_port=50000 + (port % 1000),
                protocol="tcp",
                status="ESTABLISHED",
                process=proc,
                kind=ConnectionKind.REMOTE,
                location=GeoLocation(
                    latitude=lat, longitude=lon, city=city, country=country, country_code=cc
                ),
                first_seen=now,
                last_seen=now,
            )
        )

    for port, proc, bind in _LISTEN:
        conns.append(
            Connection(
                remote_ip=bind,
                remote_port=0,
                local_port=port,
                protocol="tcp",
                status="LISTEN",
                process=proc,
                kind=ConnectionKind.LISTEN,
                first_seen=now,
                last_seen=now,
            )
        )

    for ip, port, proc in _LAN:
        conns.append(
            Connection(
                remote_ip=ip,
                remote_port=port,
                local_port=51000 + (port % 1000),
                protocol="tcp",
                status="ESTABLISHED",
                process=proc,
                kind=ConnectionKind.LAN,
                first_seen=now,
                last_seen=now,
            )
        )

    return conns


def seed(store: LiveStore, history: HistoryStore, *, weight: int = 6) -> None:
    """Seed the live store and history with demo data.

    Args:
        store: The live store to populate.
        history: The history store to populate (so Insights/Report look real).
        weight: How many times to fold the data into history, to create a
            plausible spread of "frequent" endpoints.
    """
    conns = build_demo_connections()
    store.update(conns, duration=0.004)
    for _ in range(weight):
        history.record(conns)
