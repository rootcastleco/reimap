"""Geographic location model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GeoLocation:
    """A resolved geographic location for an IP address.

    Attributes:
        latitude: Decimal degrees, north positive.
        longitude: Decimal degrees, east positive.
        city: Best-effort city name, may be empty.
        country: Human readable country name, may be empty.
        country_code: ISO-3166 alpha-2 code, may be empty.
        accuracy_km: Radius (km) MaxMind reports for the estimate, if any.
    """

    latitude: float
    longitude: float
    city: str = ""
    country: str = ""
    country_code: str = ""
    accuracy_km: int | None = None

    @property
    def label(self) -> str:
        """A short human readable ``City, Country`` label."""
        parts = [p for p in (self.city, self.country) if p]
        return ", ".join(parts) if parts else "Unknown location"
