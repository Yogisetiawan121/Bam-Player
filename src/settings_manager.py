"""
Settings manager using QSettings for persistent configuration.
Handles window geometry, playback state, recent files, and preferences.
"""
from PyQt6.QtCore import QSettings, QByteArray, QPoint, QSize
from typing import Optional, List, Dict, Any


class SettingsManager:
    """Manages application settings persistence using QSettings."""

    def __init__(self):
        self._settings = QSettings('BamPlayer', 'BamPlayer')

    # ── Window State ──────────────────────────────────────────────────
    def save_window_geometry(self, geometry: QByteArray):
        self._settings.setValue('window/geometry', geometry)

    def load_window_geometry(self) -> Optional[QByteArray]:
        val = self._settings.value('window/geometry')
        return val if isinstance(val, QByteArray) else None

    def save_window_state(self, state: QByteArray):
        self._settings.setValue('window/state', state)

    def load_window_state(self) -> Optional[QByteArray]:
        val = self._settings.value('window/state')
        return val if isinstance(val, QByteArray) else None

    def save_window_position(self, pos: QPoint):
        self._settings.setValue('window/x', pos.x())
        self._settings.setValue('window/y', pos.y())

    def load_window_position(self) -> Optional[QPoint]:
        x = self._settings.value('window/x', type=int)
        y = self._settings.value('window/y', type=int)
        if x is not None and y is not None:
            return QPoint(x, y)
        return None

    def save_window_size(self, size: QSize):
        self._settings.setValue('window/width', size.width())
        self._settings.setValue('window/height', size.height())

    def load_window_size(self) -> Optional[QSize]:
        w = self._settings.value('window/width', type=int)
        h = self._settings.value('window/height', type=int)
        if w is not None and h is not None:
            return QSize(w, h)
        return None

    # ── Playback State ────────────────────────────────────────────────
    def save_last_file(self, filepath: str, position_ms: int = 0):
        self._settings.setValue('playback/last_file', filepath)
        self._settings.setValue('playback/last_position', position_ms)

    def load_last_file(self) -> tuple:
        filepath = self._settings.value('playback/last_file', '', type=str)
        position = self._settings.value('playback/last_position', 0, type=int)
        return filepath, position

    def save_volume(self, volume: int):
        self._settings.setValue('playback/volume', volume)

    def load_volume(self) -> int:
        return self._settings.value('playback/volume', 80, type=int)

    def save_speed(self, speed: float):
        self._settings.setValue('playback/speed', speed)

    def load_speed(self) -> float:
        return self._settings.value('playback/speed', 1.0, type=float)

    def save_loop_mode(self, mode: str):
        """Save loop mode: 'none', 'single', 'playlist'"""
        self._settings.setValue('playback/loop_mode', mode)

    def load_loop_mode(self) -> str:
        return self._settings.value('playback/loop_mode', 'none', type=str)

    def save_shuffle(self, enabled: bool):
        self._settings.setValue('playback/shuffle', enabled)

    def load_shuffle(self) -> bool:
        return self._settings.value('playback/shuffle', False, type=bool)

    # ── Recent Files ──────────────────────────────────────────────────
    def save_recent_files(self, files: List[str]):
        self._settings.setValue('recent/files', files[:15])

    def load_recent_files(self) -> List[str]:
        val = self._settings.value('recent/files', [])
        if isinstance(val, list):
            return val
        elif isinstance(val, str):
            return [val] if val else []
        return []

    def add_recent_file(self, filepath: str):
        recent = self.load_recent_files()
        if filepath in recent:
            recent.remove(filepath)
        recent.insert(0, filepath)
        self.save_recent_files(recent[:15])

    # ── Playlist ──────────────────────────────────────────────────────
    def save_playlist_visible(self, visible: bool):
        self._settings.setValue('ui/playlist_visible', visible)

    def load_playlist_visible(self) -> bool:
        return self._settings.value('ui/playlist_visible', True, type=bool)

    def save_last_playlist(self, filepath: str):
        self._settings.setValue('playlist/last_file', filepath)

    def load_last_playlist(self) -> str:
        return self._settings.value('playlist/last_file', '', type=str)

    # ── Subtitle Preferences ─────────────────────────────────────────
    def save_subtitle_prefs(self, prefs: Dict[str, Any]):
        self._settings.beginGroup('subtitle')
        for key, value in prefs.items():
            self._settings.setValue(key, value)
        self._settings.endGroup()

    def load_subtitle_prefs(self) -> Dict[str, Any]:
        self._settings.beginGroup('subtitle')
        prefs = {
            'font_family': self._settings.value('font_family', 'Arial', type=str),
            'font_size': self._settings.value('font_size', 24, type=int),
            'font_color': self._settings.value('font_color', '#FFFFFF', type=str),
            'bg_opacity': self._settings.value('bg_opacity', 128, type=int),
            'enabled': self._settings.value('enabled', True, type=bool),
        }
        self._settings.endGroup()
        return prefs

    # ── Video Filters ─────────────────────────────────────────────────
    def save_filter_values(self, filters: Dict[str, float]):
        self._settings.beginGroup('filters')
        for key, value in filters.items():
            self._settings.setValue(key, value)
        self._settings.endGroup()

    def load_filter_values(self) -> Dict[str, float]:
        self._settings.beginGroup('filters')
        filters = {
            'brightness': self._settings.value('brightness', 1.0, type=float),
            'contrast': self._settings.value('contrast', 1.0, type=float),
            'saturation': self._settings.value('saturation', 1.0, type=float),
            'hue': self._settings.value('hue', 0, type=int),
            'gamma': self._settings.value('gamma', 1.0, type=float),
        }
        self._settings.endGroup()
        return filters

    # ── Always on Top ─────────────────────────────────────────────────
    def save_always_on_top(self, enabled: bool):
        self._settings.setValue('ui/always_on_top', enabled)

    def load_always_on_top(self) -> bool:
        return self._settings.value('ui/always_on_top', False, type=bool)

    # ── Enhancement Settings ────────────────────────────────────────────
    def save_enhancement_settings(self, enabled: bool, sharpness: float):
        self._settings.setValue('enhancement/enabled', enabled)
        self._settings.setValue('enhancement/sharpness', sharpness)

    def load_enhancement_settings(self) -> tuple:
        enabled = self._settings.value('enhancement/enabled', False, type=bool)
        sharpness = self._settings.value('enhancement/sharpness', 0.0, type=float)
        return enabled, sharpness

    # ── Update Settings ─────────────────────────────────────────────
    def save_update_settings(self, repo: str, auto_check: bool, interval_hours: int):
        """Save auto-update preferences."""
        self._settings.setValue('update/repo', repo)
        self._settings.setValue('update/auto_check', auto_check)
        self._settings.setValue('update/interval_hours', interval_hours)

    def load_update_settings(self) -> tuple:
        """Return (repo, auto_check, interval_hours)."""
        repo = self._settings.value('update/repo', '', type=str)
        auto_check = self._settings.value('update/auto_check', True, type=bool)
        interval = self._settings.value('update/interval_hours', 24, type=int)
        return repo, auto_check, interval

    def save_last_update_check(self, timestamp: float):
        self._settings.setValue('update/last_check', timestamp)

    def load_last_update_check(self) -> float:
        return self._settings.value('update/last_check', 0.0, type=float)

    def save_skipped_version(self, version: str):
        """Save a version the user chose to skip."""
        self._settings.setValue('update/skipped_version', version)

    def load_skipped_version(self) -> str:
        return self._settings.value('update/skipped_version', '', type=str)

    # ── Generic ───────────────────────────────────────────────────────
    def set_value(self, key: str, value):
        self._settings.setValue(key, value)

    def get_value(self, key: str, default=None, value_type=None):
        if value_type:
            return self._settings.value(key, default, type=value_type)
        return self._settings.value(key, default)

    def sync(self):
        self._settings.sync()
