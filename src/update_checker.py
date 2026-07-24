"""
Automatic update checker for Bam Player.
Checks GitHub releases for newer versions and provides download links.
Uses only stdlib — no additional dependencies required.
"""
import json
import os
import re
import sys
import ssl
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Optional, List

from . import __version__, __app_name__

# Default GitHub repository — change this if you fork the project.
DEFAULT_REPO = "Yogisetiawan121/bam-player"


def normalize_repo(raw: str) -> str:
    """Normalize a repo string — strip full URLs and return just owner/name.

    Handles:
      - "https://api.github.com/repos/owner/name/releases/latest"
      - "https://github.com/owner/name"
      - "github.com/owner/name"
      - "owner/name"
    """
    raw = raw.strip("/ ")
    # Strip common prefixes
    for prefix in ["https://api.github.com/repos/", "http://api.github.com/repos/",
                    "https://github.com/", "http://github.com/",
                    "api.github.com/repos/", "github.com/"]:
        if raw.startswith(prefix):
            raw = raw[len(prefix):]
    # Strip trailing path segments like /releases/latest
    raw = raw.split("/releases")[0] if "/releases" in raw else raw
    # Strip trailing /releases, /tags, etc.
    raw = raw.rstrip("/")
    return raw


@dataclass
class ReleaseInfo:
    """Information about an available release update."""
    version: str
    download_url: str
    release_notes: str
    published_at: str
    is_prerelease: bool = False


class UpdateChecker:
    """
    Checks for application updates by querying the GitHub releases API.
    
    Usage:
        checker = UpdateChecker("yourname/bam-player")
        release = checker.check_for_updates()
        if release:
            print(f"Update available: {release.version}")
    """

    def __init__(self, repo: str = ""):
        self.repo = normalize_repo(repo)
        self._latest_release: Optional[ReleaseInfo] = None

    def check_for_updates(self, timeout: int = 10) -> Optional[ReleaseInfo]:
        """Query GitHub releases and return a ReleaseInfo if a newer version exists.

        Raises ConnectionError on network / API failures so callers can
        distinguish "up-to-date" (returns None) from "check failed" (raises).
        """
        if not self.repo:
            return None

        url = f"https://api.github.com/repos/{self.repo}/releases/latest"

        try:
            # Try to build an SSL context that works in frozen (PyInstaller) builds
            ctx = self._make_ssl_context()
            req = urllib.request.Request(
                url,
                headers={
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": f"{__app_name__}-Updater/{__version__}",
                },
            )
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError,
                json.JSONDecodeError, OSError, ssl.SSLError) as exc:
            raise ConnectionError(f"Update check failed: {exc}") from exc

        # Parse tag as version  e.g. "v1.1.0" or "1.1.0"
        tag = data.get("tag_name", "")
        version = tag.lstrip("v")

        if not self._is_newer(version, __version__):
            return None

        # Pick the best download asset for the current platform
        download_url = self._pick_asset(data.get("assets", []))
        if not download_url:
            download_url = data.get("zipball_url", "") or data.get("html_url", "")

        release_notes = (data.get("body") or "No release notes available.")[:3000]

        self._latest_release = ReleaseInfo(
            version=version,
            download_url=download_url,
            release_notes=release_notes,
            published_at=data.get("published_at", "Unknown"),
            is_prerelease=data.get("prerelease", False),
        )
        return self._latest_release

    # ── helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _make_ssl_context() -> ssl.SSLContext:
        """Create an SSL context that works in both normal and frozen (PyInstaller) builds.

        PyInstaller bundles often can't find system CA certificates, causing
        ssl.create_default_context() to fail or produce a context with no CAs.
        We try multiple fallback strategies.
        """
        # Strategy 1: Use certifi if available (PyInstaller often bundles it)
        try:
            import certifi
            ctx = ssl.create_default_context(cafile=certifi.where())
            return ctx
        except (ImportError, OSError):
            pass

        # Strategy 2: Normal default context (works outside PyInstaller)
        try:
            ctx = ssl.create_default_context()
            return ctx
        except (OSError, ssl.SSLError):
            pass

        # Strategy 3: Unverified context as last resort (still encrypted, just no cert check)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

    def _pick_asset(self, assets: list) -> str:
        """Return the browser_download_url of the most suitable asset for this OS.

        Priority order (Windows):
          1. Installer .exe (e.g. BamPlayer-1.1.0-Setup.exe)
          2. Portable .zip
          3. Raw .exe (requires VLC installed system-wide)
          4. .msi / .7z
        """
        def score(asset) -> int:
            """Lower score = better match."""
            name = (asset.get("name") or "").lower()
            if sys.platform == "win32":
                if name.endswith("-setup.exe") or name.endswith("-installer.exe"):
                    return 0  # installer — best for most users
                if name.endswith(".zip"):
                    return 10  # portable zip
                if name.endswith(".exe"):
                    return 20  # raw exe (needs VLC)
                if name.endswith(".msi"):
                    return 30
                if name.endswith(".7z"):
                    return 40
            elif sys.platform == "darwin":
                if name.endswith(".dmg"):
                    return 0
                if name.endswith(".app.tar.gz") or name.endswith(".app.zip"):
                    return 10
                if name.endswith(".zip"):
                    return 20
            else:
                if name.endswith(".appimage"):
                    return 0
                if name.endswith(".tar.gz") or name.endswith(".tar.xz"):
                    return 10
                if name.endswith(".deb"):
                    return 20
                if name.endswith(".rpm"):
                    return 30
                if name.endswith(".zip"):
                    return 40
            return 999  # no match

        scored = [(score(a), a.get("browser_download_url") or "") for a in assets]
        scored.sort(key=lambda x: x[0])
        return scored[0][1] if scored and scored[0][0] < 999 else ""

    @staticmethod
    def _is_newer(remote: str, current: str) -> bool:
        """Return True if the remote version string is newer than current."""
        def parse(v: str):
            parts = re.split(r"[.\-+_]", v)
            nums = []
            for p in parts:
                try:
                    nums.append(int(p))
                except ValueError:
                    nums.append(0)
            return nums

        r_parts = parse(remote)
        c_parts = parse(current)

        for r, c in zip(r_parts, c_parts):
            if r > c:
                return True
            if r < c:
                return False
        return len(r_parts) > len(c_parts)

    @property
    def latest_release(self) -> Optional[ReleaseInfo]:
        return self._latest_release


# ── Convenience helpers ───────────────────────────────────────────────

def format_last_checked(timestamp: float) -> str:
    """Format a Unix timestamp into a human-friendly relative string."""
    elapsed = time.time() - timestamp
    if elapsed < 60:
        return "just now"
    if elapsed < 3600:
        m = int(elapsed // 60)
        return f"{m} minute{'s' if m != 1 else ''} ago"
    if elapsed < 86400:
        h = int(elapsed // 3600)
        return f"{h} hour{'s' if h != 1 else ''} ago"
    d = int(elapsed // 86400)
    return f"{d} day{'s' if d != 1 else ''} ago"
