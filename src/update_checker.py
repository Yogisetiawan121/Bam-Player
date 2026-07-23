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
        self.repo = repo.strip("/ ")
        self._latest_release: Optional[ReleaseInfo] = None

    def check_for_updates(self, timeout: int = 10) -> Optional[ReleaseInfo]:
        """Query GitHub releases and return a ReleaseInfo if a newer version exists."""
        if not self.repo:
            return None

        url = f"https://api.github.com/repos/{self.repo}/releases/latest"

        try:
            ctx = ssl.create_default_context()
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
            return None

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

    def _pick_asset(self, assets: list) -> str:
        """Return the browser_download_url of the most suitable asset for this OS."""
        if sys.platform == "win32":
            preferences = [".exe", ".msi", ".zip", ".7z"]
        elif sys.platform == "darwin":
            preferences = [".dmg", ".app.tar.gz", ".zip"]
        else:
            preferences = [".AppImage", ".tar.gz", ".tar.xz", ".deb", ".rpm"]

        scored: list[tuple[int, str]] = []
        for asset in assets:
            name = (asset.get("name") or "").lower()
            url = asset.get("browser_download_url") or ""
            for i, ext in enumerate(preferences):
                if name.endswith(ext):
                    scored.append((i, url))
                    break
        scored.sort(key=lambda x: x[0])
        return scored[0][1] if scored else ""

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
