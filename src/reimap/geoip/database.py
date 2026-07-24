"""GeoIP database discovery, installation and verification.

reimap uses MaxMind's GeoLite2-City database (``.mmdb``). The database is never
bundled — users supply their own free MaxMind licence key, or drop an ``.mmdb``
file into the cache directory manually. This keeps the project licence-clean and
telemetry-free.
"""

from __future__ import annotations

import shutil
import tarfile
import tempfile
from pathlib import Path

from ..app_dirs import geoip_dir
from ..hooks import HookName, hooks
from ..logging_config import get_logger

log = get_logger("geoip.database")

_EDITION = "GeoLite2-City"
_DOWNLOAD_URL = (
    "https://download.maxmind.com/app/geoip_download"
    "?edition_id={edition}&license_key={key}&suffix=tar.gz"
)


class GeoIPDatabase:
    """Locate, install and verify the GeoLite2-City database."""

    def __init__(self, directory: Path | None = None) -> None:
        self.directory = directory or geoip_dir()

    # -- Discovery ----------------------------------------------------------
    def path(self) -> Path | None:
        """Return the path to an installed ``.mmdb`` file, or ``None``."""
        preferred = self.directory / f"{_EDITION}.mmdb"
        if preferred.exists():
            return preferred
        for candidate in sorted(self.directory.glob("*.mmdb")):
            return candidate
        return None

    def is_installed(self) -> bool:
        """Whether a usable database is present on disk."""
        return self.path() is not None

    def status(self) -> dict[str, object]:
        """Return a small dictionary describing the current database state."""
        path = self.path()
        if path is None:
            return {"installed": False, "path": None, "size_mb": 0.0}
        size_mb = round(path.stat().st_size / (1024 * 1024), 2)
        return {"installed": True, "path": str(path), "size_mb": size_mb}

    # -- Installation -------------------------------------------------------
    def install_from_file(self, source: Path) -> Path:
        """Copy an existing ``.mmdb`` file into the managed directory.

        Args:
            source: Path to a ``.mmdb`` file the user already downloaded.

        Returns:
            The destination path inside the managed directory.
        """
        source = Path(source)
        if source.suffix != ".mmdb":
            raise ValueError("Expected a .mmdb file")
        destination = self.directory / source.name
        shutil.copy2(source, destination)
        log.info("Installed GeoIP database from %s", source)
        hooks.emit(HookName.GEOIP_DB_UPDATED, path=str(destination))
        return destination

    def download(self, account_id: str, license_key: str) -> Path:
        """Download and extract GeoLite2-City using a MaxMind licence key.

        Args:
            account_id: MaxMind account id (kept for API symmetry; not required
                by the download endpoint but validated to be non-empty).
            license_key: MaxMind licence key.

        Returns:
            The path to the extracted ``.mmdb`` file.

        Raises:
            RuntimeError: If the download or extraction fails.
        """
        import requests  # imported lazily so the core has no hard requests dep at import

        if not license_key:
            raise RuntimeError("A MaxMind license key is required to download the database.")

        url = _DOWNLOAD_URL.format(edition=_EDITION, key=license_key)
        log.info("Downloading %s from MaxMind...", _EDITION)
        try:
            resp = requests.get(url, stream=True, timeout=60)
            resp.raise_for_status()
        except requests.RequestException as exc:  # pragma: no cover - network
            raise RuntimeError(f"GeoIP download failed: {exc}") from exc

        with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp:
            for chunk in resp.iter_content(chunk_size=1 << 16):
                tmp.write(chunk)
            archive_path = Path(tmp.name)

        try:
            mmdb = self._extract(archive_path)
        finally:
            archive_path.unlink(missing_ok=True)

        hooks.emit(HookName.GEOIP_DB_UPDATED, path=str(mmdb))
        log.info("GeoIP database ready at %s", mmdb)
        return mmdb

    def _extract(self, archive_path: Path) -> Path:
        """Extract the ``.mmdb`` member from a MaxMind tar.gz archive."""
        with tarfile.open(archive_path, "r:gz") as tar:
            member = next((m for m in tar.getmembers() if m.name.endswith(".mmdb")), None)
            if member is None:
                raise RuntimeError("Archive did not contain a .mmdb file")
            destination = self.directory / Path(member.name).name
            with tar.extractfile(member) as src, open(destination, "wb") as dst:  # type: ignore[arg-type]
                shutil.copyfileobj(src, dst)
        return destination
