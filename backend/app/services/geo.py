"""Geographic helpers for travel-distance matching (US miles)."""

from __future__ import annotations

import json
import math
import re
import threading
import urllib.error
import urllib.parse
import urllib.request
from abc import ABC, abstractmethod

_EARTH_RADIUS_MILES = 3958.7613
_US_ZIP_RE = re.compile(r"^(\d{5})")


def haversine_miles(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """Great-circle distance between two WGS84 points, in miles."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return 2 * _EARTH_RADIUS_MILES * math.asin(math.sqrt(a))


def normalize_us_zip(postal_code: str | None) -> str | None:
    if not postal_code:
        return None
    match = _US_ZIP_RE.match(postal_code.strip())
    return match.group(1) if match else None


class ZipGeocoder(ABC):
    @abstractmethod
    def geocode(self, postal_code: str) -> tuple[float, float] | None:
        """Return (latitude, longitude) for a US ZIP, or None if unknown."""


class StaticZipGeocoder(ZipGeocoder):
    """Deterministic lookup table — used in tests and as Nominatim cache seed."""

    def __init__(self, mapping: dict[str, tuple[float, float]] | None = None):
        self._mapping = {
            normalize_us_zip(zip_code) or zip_code: coords
            for zip_code, coords in (mapping or {}).items()
        }

    def geocode(self, postal_code: str) -> tuple[float, float] | None:
        zip_code = normalize_us_zip(postal_code)
        if zip_code is None:
            return None
        return self._mapping.get(zip_code)


class NominatimZipGeocoder(ZipGeocoder):
    """Resolve US ZIP centroids via OpenStreetMap Nominatim (cached in-process)."""

    def __init__(self, *, user_agent: str = "clinical-trial-tracker/0.1"):
        self._user_agent = user_agent
        self._lock = threading.Lock()
        self._cache: dict[str, tuple[float, float] | None] = {}

    def geocode(self, postal_code: str) -> tuple[float, float] | None:
        zip_code = normalize_us_zip(postal_code)
        if zip_code is None:
            return None

        with self._lock:
            if zip_code in self._cache:
                return self._cache[zip_code]

        coords = self._fetch(zip_code)
        with self._lock:
            self._cache[zip_code] = coords
        return coords

    def _fetch(self, zip_code: str) -> tuple[float, float] | None:
        query = urllib.parse.urlencode(
            {
                "postalcode": zip_code,
                "country": "US",
                "format": "json",
                "limit": 1,
            }
        )
        request = urllib.request.Request(
            f"https://nominatim.openstreetmap.org/search?{query}",
            headers={"User-Agent": self._user_agent},
        )
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError):
            return None

        if not payload:
            return None
        try:
            return float(payload[0]["lat"]), float(payload[0]["lon"])
        except (KeyError, TypeError, ValueError):
            return None


_geocoder_lock = threading.Lock()
_default_geocoder: ZipGeocoder | None = None


def get_zip_geocoder() -> ZipGeocoder:
    global _default_geocoder
    with _geocoder_lock:
        if _default_geocoder is None:
            _default_geocoder = NominatimZipGeocoder()
        return _default_geocoder


def set_zip_geocoder(geocoder: ZipGeocoder | None) -> None:
    """Override the process geocoder (tests). Pass None to restore default."""
    global _default_geocoder
    with _geocoder_lock:
        _default_geocoder = geocoder


def nearest_site_distance_miles(
    origin: tuple[float, float],
    locations: list[tuple[float, float]],
) -> float | None:
    if not locations:
        return None
    lat0, lon0 = origin
    return min(haversine_miles(lat0, lon0, lat, lon) for lat, lon in locations)
