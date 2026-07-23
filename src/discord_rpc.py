"""
Discord Rich Presence integration for Bam Player.

Updates your Discord status with the currently playing video title,
so your friends can see what you're watching in real time.

Features:
  - Smart show-name extraction from video filenames (like Crunchyroll)
  - Auto-generates asset keys from show names for Discord Rich Presence images
  - FILENAME_OVERRIDES: exact filename → show name mapping (for non-standard names)
  - SHOW_ASSET_MAP: show name → Discord asset key mapping (for custom artwork keys)
  - Falls back to generic "play"/"pause" icons when no show is detected

Usage:
    from .discord_rpc import DiscordRPC

    rpc = DiscordRPC(client_id="your_client_id_here")
    rpc.connect()

    rpc.set_playing("Attack on Titan S01E01.mkv", duration_ms=600000)
    rpc.set_paused("Attack on Titan S01E01.mkv")
    rpc.clear_presence()
    rpc.close()
"""
import re
import time
import logging
from typing import Optional, Dict

try:
    from pypresence import Presence
    from pypresence.exceptions import DiscordNotFound, PipeClosed
    PYPYRESENCE_AVAILABLE = True
except ImportError:
    PYPYRESENCE_AVAILABLE = False

logger = logging.getLogger(__name__)


# ── Public API ──────────────────────────────────────────────────────────


class DiscordRPC:
    """Manages Discord Rich Presence for the video player.

    Automatically extracts show names from filenames and generates
    asset keys so your Discord profile shows matching artwork for
    each video — just like Crunchyroll.

    Connects lazily (on first use) so the player isn't slowed down at startup.
    All failures are logged but never raised — the player works perfectly
    whether or not Discord is running.
    """

    # Create your own app at https://discord.com/developers/applications
    # and paste its Client ID here (or pass it to the constructor).
    DEFAULT_CLIENT_ID = "1529520230018060391"

    # ── Filename overrides ───────────────────────────────────────────
    # Map exact filenames (without extension, case-insensitive) to show names.
    # This is checked FIRST, before any regex pattern matching.
    # Use this for files whose names don't follow standard naming conventions.
    #
    # Example:
    #   FILENAME_OVERRIDES = {
    #       "kuroshitsuji s2": "Kuroshitsuji Season 2",
    #       "my weird file name 2024": "My Custom Show",
    #   }
    FILENAME_OVERRIDES: Dict[str, str] = {
        # ── Kuroshitsuji (Black Butler) ─────────────────────────
        # Prefix matching is used: "kuroshitsuji s2" will match any filename
        # starting with those words, e.g. "Kuroshitsuji S2E01.mkv".
        "kuroshitsuji s2":                        "Kuroshitsuji Season 2",
        "kuroshitsuji book of circus":             "Kuroshitsuji Book of Circus",
        "kuroshitsuji book of murder":             "Kuroshitsuji Book of Murder",
        "kuroshitsuji movie book of the atlantic": "Kuroshitsuji Movie: Book of the Atlantic",
        "kuroshitsuji s4":                        "Kuroshitsuji Season 4",
        "kuroshitsuji midori":                    "Kuroshitsuji Midori (Emerald Witch Arc)",
        # ── Yani Neko ──────────────────────────────────────────
        "yani neko":                                "Yani Neko",
        # ── Kimetsu No Yaiba ──────────────────────────────────────────
        "kimetsu no yaiba":                         "Kimetsu No Yaiba",
        # ── Other shows ────────────────────────────────────────
        "nippon sangoku":                          "Nippon Sangoku",
    }

    # ── Show-to-asset key mapping ────────────────────────────────────
    # Map detected show names to the exact asset keys you uploaded
    # in the Discord Developer Portal (Rich Presence → Art Assets).
    #
    # If a show is NOT listed here, the key is auto-generated from the
    # show name (lowercase, spaces → underscores, max 32 chars).
    #
    # Example:
    #   SHOW_ASSET_MAP = {
    #       "Attack on Titan": "aot_cover",
    #       "Spider-Man: Into the Spider-Verse": "spiderverse_poster",
    #   }
    SHOW_ASSET_MAP: Dict[str, str] = {
        # ── Kuroshitsuji (Black Butler) ─────────────────────────
        "Kuroshitsuji Season 2":                  "kuroshitsuji_s2",
        "Kuroshitsuji Book of Circus":             "kuroshitsuji_book_of_circus",
        "Kuroshitsuji Book of Murder":             "kuroshitsuji_book_of_murder",
        "Kuroshitsuji Movie: Book of the Atlantic": "kuroshitsuji_book_of_atlantic",
        "Kuroshitsuji Season 4":                   "kuroshitsuji_s4",
        "Kuroshitsuji Midori (Emerald Witch Arc)":     "kuroshitsuji_midori",
        # ── Yani Neko ──────────────────────────────────────────
        "Yani Neko":                                "yani_neko",
        # ── Kimetsu No Yaiba ──────────────────────────────────────────
        "Kimetsu No Yaiba":                          "kimetsu_no_yaiba",
        # ── Other shows ────────────────────────────────────────
        "Nippon Sangoku":                          "nippon_sangoku"
    }

    def __init__(self, client_id: Optional[str] = None):
        self._client_id = client_id or self.DEFAULT_CLIENT_ID
        self._rpc: Optional[Presence] = None
        self._connected = False
        self._start_time: Optional[int] = None
        self._current_title: Optional[str] = None
        self._current_show: Optional[str] = None

    # ── Connection ────────────────────────────────────────────────────

    def connect(self) -> bool:
        """Open a connection to Discord's local RPC pipe.

        Returns True if connected (or already connected), False if Discord
        isn't running or the pipe is unavailable.
        """
        if not PYPYRESENCE_AVAILABLE:
            logger.info("pypresence not installed — Discord Rich Presence disabled")
            return False
        if self._connected and self._rpc:
            return True
        try:
            self._rpc = Presence(self._client_id)
            self._rpc.connect()
            self._connected = True
            logger.info("Connected to Discord Rich Presence")
            return True
        except DiscordNotFound:
            logger.info("Discord client not found — Rich Presence unavailable")
            return False
        except Exception as exc:
            logger.warning("Failed to connect to Discord RPC: %s", exc)
            return False

    def close(self) -> None:
        """Clear presence and tear down the RPC connection."""
        self._clear()
        if self._rpc:
            try:
                self._rpc.close()
            except Exception:
                pass
        self._rpc = None
        self._connected = False
        self._start_time = None
        self._current_title = None
        self._current_show = None

    # ── Presence Updates ──────────────────────────────────────────────

    def set_playing(self, title: str, duration_ms: int = 0,
                     position_ms: int = 0) -> bool:
        """Show 'Watching {show}' in the user's Discord profile.

        Automatically detects the show name from the filename and uses
        it as the *large_image* asset key, so Discord shows your uploaded
        artwork.
        Season/episode info (e.g. "S2 E01") is shown in the details field
        when detected from the filename.

        The count-up elapsed timer is based on *position_ms* — pass the
        current video position so the timer continues correctly after
        pause/resume or seeking.

        Parameters
        ----------
        title : str
            Full filename (e.g. "Attack on Titan S01E01.mkv").
        duration_ms : int
            Total duration of the video in milliseconds. Pass 0 to omit
            the end-timer (shows only elapsed time).
        position_ms : int
            Current playback position in milliseconds. Pass 0 to start
            the timer from now (fresh start).
        """
        if not self._ensure_connected():
            return False
        self._current_title = title

        # Calculate start timestamp so the count-up reflects actual position
        now = int(time.time())
        if position_ms > 0:
            self._start_time = now - (position_ms // 1000)
        else:
            self._start_time = now

        end_time: Optional[int] = None
        if duration_ms > 0:
            end_time = self._start_time + (duration_ms // 1000)

        # Extract show name and episode info
        show_name = self._parse_show_name(title)
        self._current_show = show_name
        episode_str = self._format_episode(title)

        if show_name:
            large_image = self._resolve_asset_key(show_name)
            large_text = show_name
            state = f"Watching {show_name}"
            details = episode_str if episode_str else show_name
        else:
            large_image = "play"
            large_text = "Watching Video"
            state = "Watching Video"
            if episode_str:
                details = episode_str
            else:
                details = title  # Fall back to full filename

        return self._update(
            state=state,
            details=details,
            large_image=large_image,
            large_text=large_text,
            small_image="play",
            small_text="Playing",
            end=end_time,
        )

    def set_paused(self, title: str) -> bool:
        """Show a paused indicator in Discord (with show artwork + episode)."""
        if not self._ensure_connected():
            return False
        self._current_title = title
        self._start_time = None

        show_name = self._parse_show_name(title)
        episode_str = self._format_episode(title)

        if show_name:
            large_image = self._resolve_asset_key(show_name)
            large_text = show_name
            if episode_str:
                details = f"{show_name} {episode_str}"
            else:
                details = show_name
        else:
            large_image = "pause"
            large_text = "Paused"
            details = title

        return self._update(
            state="⏸ Paused",
            details=details,
            large_image=large_image,
            large_text=large_text,
            small_image="pause",
            small_text="Paused",
        )

    def clear_presence(self) -> bool:
        """Remove the Rich Presence activity entirely."""
        self._current_title = None
        self._current_show = None
        self._start_time = None
        return self._clear()

    # ── Show Name Parsing ─────────────────────────────────────────────
    #
    # Extracts a clean show name from common naming conventions:
    #
    #   "Show.Name.S01E01.1080p.mkv"           →  "Show Name"
    #   "Show Name - Episode 01.mkv"           →  "Show Name"
    #   "Show.Name.2023.1080p.BluRay.mkv"      →  "Show Name"
    #   "[SubGroup] Show Name - 01 [1080p]"     →  "Show Name"
    #   "Show Name (2023).mkv"                 →  "Show Name"
    #   "Show Name S01E01.mkv"                 →  "Show Name"
    #   "Show_Name_Ep01.mkv"                   →  "Show Name"
    #   "Kuroshitsuji Book of Circus.mkv"      →  "Kuroshitsuji Book of Circus"  (via override)
    #   "random_video.mp4"                     →  None   (generic fallback)

    @classmethod
    def _parse_show_name(cls, filename: str) -> Optional[str]:
        """Extract a human-readable show name from a video filename.

        Returns None when no structured show-name pattern is detected
        (the generic *play* / *pause* fallback icons will be used instead).
        """
        # Strip extension
        name = filename.rsplit('.', 1)[0]

        # ── Check filename overrides first (case-insensitive, prefix match) ──
        # Exact match takes priority; then prefix match (so "kuroshitsuji s2"
        # matches both the bare file "Kuroshitsuji S2.mkv" AND per-episode files
        # like "Kuroshitsuji S2E01.mkv").
        #
        # The prefix check uses a "next char is not a digit" guard to prevent
        # "s2" from matching "s20" while allowing "s2e01", "s2-01", "s2 01", etc.
        needle = name.lower().strip()
        best_match = None
        best_len = 0
        for ovr_key, ovr_value in cls.FILENAME_OVERRIDES.items():
            if needle == ovr_key:
                best_match = ovr_value
                break  # exact match is always best
            if needle.startswith(ovr_key) and len(needle) > len(ovr_key):
                # Next char after the prefix must NOT be a digit (avoids "s2" → "s20")
                next_char = needle[len(ovr_key)]
                if not next_char.isdigit() and len(ovr_key) > best_len:
                    best_match = ovr_value
                    best_len = len(ovr_key)
        if best_match:
            return best_match

        # Strip leading [Group] tags so patterns below don't capture them
        # e.g. "[SubsPlease] Attack.on.Titan.S01E01.mkv" → "Attack.on.Titan.S01E01"
        name = re.sub(r'^\[[^\]]*\]\s*', '', name)

        # ── Pattern 1: Show Name - Episode Number ────────────────────
        # e.g. "Attack on Titan - 01 [1080p].mkv"
        m = re.match(r'^(.+?)\s*-\s*\d+', name)
        if m:
            result = _clean_name(m.group(1))
            if result and len(result) > 2:
                return result

        # ── Pattern 2: Show.Name.S01E01 (dot before S) ──────────────
        # e.g. "Breaking.Bad.S01E01.1080p.mkv"
        m = re.search(r'^(.+?)\.S\d{1,2}E\d{1,2}', name, re.IGNORECASE)
        if m:
            result = _clean_name(m.group(1))
            if result and len(result) > 2:
                return result

        # ── Pattern 3: Show Name - Episode 01 (dash, optional "Episode") ──
        # e.g. "Attack on Titan - Episode 01.mkv"
        m = re.match(r'^(.+?)\s*-\s*(?:Episode\s*)?\d+', name, re.IGNORECASE)
        if m:
            result = _clean_name(m.group(1))
            if result and len(result) > 2:
                return result

        # ── Pattern 4: Show.Name.2023 (movie with year, dot separator) ──
        # e.g. "Spider-Man.No.Way.Home.2021.1080p.mkv"
        m = re.match(r'^(.+?)\.(19\d{2}|20\d{2})', name)
        if m:
            result = _clean_name(m.group(1))
            if result and len(result) > 2:
                return result

        # ── Pattern 5: Show Name (Year) ──────────────────────────────
        # e.g. "Interstellar (2014).mkv"
        m = re.match(r'^(.+?)\s*\((19\d{2}|20\d{2})\)', name)
        if m:
            result = m.group(1).strip()
            if result and len(result) > 2:
                return result

        # ── Pattern 6: Show_Name_Ep01 (underscore) ──────────────────
        # e.g. "Game_of_Thrones_Ep01.mkv"
        m = re.match(r'^(.+?)_(?:Ep(?:isode)?|E)\d+', name, re.IGNORECASE)
        if m:
            result = m.group(1).replace('_', ' ').strip()
            if result and len(result) > 2:
                return result

        # ── Pattern 7: Show Name S01E01 (space before S, no dot) ────
        # e.g. "Kuroshitsuji S2E01.mkv"
        m = re.match(r'^(.+?)\s+S\d{1,2}E\d{1,2}', name, re.IGNORECASE)
        if m:
            result = _clean_name(m.group(1))
            if result and len(result) > 2:
                return result

        # ── No structured pattern detected ───────────────────────────
        # This is probably a generic filename like "random_video.mp4"
        return None

    @staticmethod
    def _make_asset_key(show_name: str) -> str:
        """Convert a show name into a Discord asset key.

        - Lowercases everything
        - Replaces spaces, dots, dashes, and special chars with underscores
        - Truncates to 32 characters (Discord's limit for asset keys)
        """
        key = show_name.lower().strip()
        key = re.sub(r'[^a-z0-9]+', '_', key)
        key = key.strip('_')
        return key[:32]

    def _resolve_asset_key(self, show_name: str) -> str:
        """Return the asset key for a show, checking the custom map first.

        Looks up *show_name* in SHOW_ASSET_MAP first (for custom overrides).
        Falls back to auto-generated key from _make_asset_key().
        """
        if show_name in self.SHOW_ASSET_MAP:
            return self.SHOW_ASSET_MAP[show_name]
        return self._make_asset_key(show_name)

    @staticmethod
    def _format_episode(filename: str) -> Optional[str]:
        """Extract a human-readable season/episode string from a filename.

        Scans the original filename (before any override or pattern processing)
        for common season/episode markers and returns a clean label like
        "S2 E01", "Episode 1", or None if nothing is found.

        Examples:
          "Kuroshitsuji S2E01.mkv"       →  "S2 E01"
          "Show.S01E01.1080p.mkv"        →  "S1 E01"
          "Show - Episode 01.mkv"        →  "Episode 1"
          "Show - 01.mkv"                →  "E01"
          "Show_Ep01.mkv"                →  "E01"
          "Interstellar (2014).mkv"      →  None
        """
        # Strip extension so we don't match digits in ".mkv" etc.
        # We search the full string (not just the start) so episode
        # markers can appear anywhere in the filename.
        name = filename.rsplit('.', 1)[0]

        # ── Pattern: S01E01 or S2E01 ──────────────────────────────
        m = re.search(r'S(\d{1,2})[\s._-]*E(\d{1,2})', name, re.IGNORECASE)
        if m:
            season = int(m.group(1))
            episode = int(m.group(2))
            return f"S{season} E{episode:02d}"

        # ── Pattern: - Episode 01 / - Ep 01 (dash + word) ─────────
        m = re.search(r'-\s*(?:Ep(?:isode)?)\s*(\d+)', name, re.IGNORECASE)
        if m:
            return f"Episode {int(m.group(1))}"

        # ── Pattern: - 01 (dash + bare number, but NOT a year like -2021)
        m = re.search(r'-(\d{1,3})(?:\.|\s|$)', name)
        if m:
            ep = int(m.group(1))
            if 1 <= ep <= 999:  # Only treat 1-999 as episode numbers
                return f"E{ep:02d}"

        # ── Pattern: _Ep01 / _E01 (underscore prefix) ─────────────
        m = re.search(r'_(?:Ep(?:isode)?|E)(\d+)', name, re.IGNORECASE)
        if m:
            return f"E{int(m.group(1)):02d}"

        return None

    # ── Internal helpers ──────────────────────────────────────────────

    def _ensure_connected(self) -> bool:
        if self._connected and self._rpc:
            return True
        return self.connect()

    def _update(self, **kwargs) -> bool:
        if not self._rpc:
            return False
        try:
            self._rpc.update(**kwargs)
            return True
        except PipeClosed:
            self._connected = False
            logger.info("Discord RPC pipe closed — reconnecting…")
            if self._ensure_connected():
                try:
                    self._rpc.update(**kwargs)
                    return True
                except Exception:
                    pass
            return False
        except Exception as exc:
            logger.warning("Discord RPC update failed: %s", exc)
            return False

    def _clear(self) -> bool:
        if not self._rpc or not self._connected:
            return True
        try:
            self._rpc.clear()
            return True
        except Exception:
            pass
        return True


# ── Module-level helper ──────────────────────────────────────────────────


def _clean_name(raw: str) -> str:
    """Normalise a raw name fragment: replace dots/spaces and strip junk."""
    cleaned = re.sub(r'[.\s_]+', ' ', raw).strip()
    # Strip trailing release-group tags like "[1080p]", "[HEVC]" (possibly multiple)
    cleaned = re.sub(r'(?:\s*\[[^\]]*\])+$', '', cleaned).strip()
    return cleaned
