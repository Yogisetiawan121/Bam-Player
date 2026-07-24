"""
Main application window integrating all components.
"""
import os
import sys
import time
import subprocess
import webbrowser
import vlc
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QFileDialog, QMessageBox, QSplitter, QDialog)
from PyQt6.QtCore import Qt, QTimer, QUrl, QSize
from PyQt6.QtGui import QIcon, QDropEvent, QDragEnterEvent
import qtawesome as qta

from .settings_manager import SettingsManager
from .video_widget import VideoWidget
from .control_bar import ControlBar
from .playlist_panel import PlaylistPanel
from .osd import OSDWidget
from .system_tray import SystemTrayIntegration
from .subtitle_manager import SubtitleManager, SubtitleStyleDialog
from .video_filters import VideoFiltersDialog, apply_filters_to_player
from .styles import get_main_stylesheet
from .shortcuts import setup_shortcuts
from .utils import get_pictures_folder, get_video_files_from_dir
from .discord_rpc import DiscordRPC
from .update_checker import UpdateChecker, ReleaseInfo
from .update_dialog import (UpdateAvailableDialog, UpToDateDialog,
                                UpdateSettingsDialog, UpdateDownloadDialog)


class MainWindow(QMainWindow):
    """Main window of the Bam Player application."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bam Player")
        self.setMinimumSize(800, 600)
        self.setStyleSheet(get_main_stylesheet())
        self.setAcceptDrops(True)
        
        self.settings = SettingsManager()
        self.is_fullscreen = False
        self._current_filepath = None  # Track for restart/loop operations
        
        self._setup_ui()
        self._setup_vlc()
        self._connect_signals()
        setup_shortcuts(self)
        
        self._restore_state()
        
        # Cursor auto-hide timer (3s delay after last mouse move)
        self._cursor_hide_timer = QTimer(self)
        self._cursor_hide_timer.setSingleShot(True)
        self._cursor_hide_timer.timeout.connect(self._on_cursor_hide_timeout)

        # Discord Rich Presence (lazy-connects on first play)
        self.discord_rpc = DiscordRPC()

        # Auto-update checker (uses hardcoded default repo, no config needed)
        repo, _, _ = self.settings.load_update_settings()
        self.update_checker = UpdateChecker(repo)

        # Timer to update UI state during playback
        self.update_timer = QTimer(self)
        self.update_timer.setInterval(250)
        self.update_timer.timeout.connect(self._update_ui_state)
        
    def _setup_ui(self):
        # Central widget and layout
        self.setContentsMargins(0, 0, 0, 0)
        self.central_widget = QWidget()
        self.central_widget.setContentsMargins(0, 0, 0, 0)
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_layout.addWidget(self.splitter)
        
        # Video area container (for absolute positioning of OSD/Controls)
        self.video_container = QWidget()
        self.video_container.setMinimumWidth(550)
        self.video_container.setStyleSheet("background-color: black;")
        
        # We don't use a layout for the video container so we can overlay widgets
        self.video_widget = VideoWidget(self.video_container)
        
        self.osd = OSDWidget(self.video_container)
        self.control_bar = ControlBar(self.video_container)
        
        self.splitter.addWidget(self.video_container)
        
        # Playlist Panel
        self.playlist_panel = PlaylistPanel(self.settings)
        self.splitter.addWidget(self.playlist_panel)
        
        # Set splitter proportions (75% video, 25% playlist)
        self.splitter.setSizes([800, 250])
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 0)
        
        # Override video container resize event so it resizes overlays perfectly
        self.video_container.resizeEvent = self._on_video_container_resize
        
        # Hide playlist if saved as hidden
        if not self.settings.load_playlist_visible():
            self.playlist_panel.hide()
            
        # System Tray (if icon exists, else use qtawesome)
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'icon.ico')
        icon = QIcon(icon_path) if os.path.exists(icon_path) else qta.icon('mdi6.play-circle', color='#6c5ce7')
        self.setWindowIcon(icon)
        
        self.tray = SystemTrayIntegration(icon, self)
        self.tray.show()

        # ── Menu Bar (Help → Updates) ──
        self._setup_menu_bar()

    def _setup_menu_bar(self):
        """Create the application menu bar with update-related entries."""
        from PyQt6.QtWidgets import QMenuBar
        from PyQt6.QtGui import QAction
        from . import __app_name__

        self._menubar = self.menuBar()
        self._menubar.setNativeMenuBar(False)  # Ensure cross-platform consistency

        # Help menu
        help_menu = self._menubar.addMenu("&Help")

        self._action_check_updates = QAction(qta.icon('mdi6.update', color='#e8e8f0'), "Check for Updates…", self)
        self._action_check_updates.triggered.connect(self.check_for_updates_now)
        help_menu.addAction(self._action_check_updates)

        help_menu.addSeparator()

        self._action_update_settings = QAction(qta.icon('mdi6.cog-outline', color='#e8e8f0'), "Update Settings…", self)
        self._action_update_settings.triggered.connect(self.open_update_settings)
        help_menu.addAction(self._action_update_settings)

        help_menu.addSeparator()

        about_action = QAction(qta.icon('mdi6.information-outline', color='#e8e8f0'), f"About {__app_name__}", self)
        about_action.triggered.connect(self._show_about_dialog)
        help_menu.addAction(about_action)

    def _show_about_dialog(self):
        """Show a simple about dialog."""
        from . import __version__, __app_name__
        QMessageBox.about(
            self,
            f"About {__app_name__}",
            f"<h2>{__app_name__}</h2>"
            f"<p>Version {__version__}</p>"
            f"<p>A modern media player built with Python, PyQt6, and libVLC.</p>"
        )

    def _on_video_container_resize(self, event):
        """Handle resizing to keep overlays positioned correctly."""
        QWidget.resizeEvent(self.video_container, event)
        vc_size = event.size()
        self.video_widget.setGeometry(0, 0, vc_size.width(), vc_size.height())
        
        # Position control bar at bottom
        cb_height = self.control_bar.height()
        self.control_bar.setGeometry(0, vc_size.height() - cb_height, vc_size.width(), cb_height)

    def resizeEvent(self, event):
        super().resizeEvent(event)

    def _setup_vlc(self):
        self.player = self.video_widget.get_player()
        self.vlc_instance = self.video_widget.get_instance()
        
        self.subtitle_manager = SubtitleManager(self.settings)
        
        # Apply saved volume and speed
        vol = self.settings.load_volume()
        self.control_bar.volume_ctrl.set_volume(vol)
        self.player.audio_set_volume(vol)
        
        speed = self.settings.load_speed()
        self.control_bar.speed_ctrl.set_speed(speed)
        self.player.set_rate(speed)
        
        # Event manager for VLC
        self.vlc_events = self.player.event_manager()
        self.vlc_events.event_attach(vlc.EventType.MediaPlayerEndReached, self._on_media_end)
        self.vlc_events.event_attach(vlc.EventType.MediaPlayerPlaying, self._on_playing)
        self.vlc_events.event_attach(vlc.EventType.MediaPlayerPaused, self._on_paused)
        
    def _connect_signals(self):
        # Video Widget
        self.video_widget.mouse_moved.connect(self._on_mouse_moved)
        self.video_widget.double_clicked.connect(self.toggle_fullscreen)
        self.video_widget.clicked.connect(self.toggle_playback)
        
        # Control Bar - Playback
        self.control_bar.play_pause_requested.connect(self.toggle_playback)
        self.control_bar.stop_requested.connect(self.stop_playback)
        self.control_bar.next_requested.connect(self.play_next)
        self.control_bar.prev_requested.connect(self.play_prev)
        
        # Control Bar - Tools
        self.control_bar.open_requested.connect(self.open_file_dialog)
        self.control_bar.fullscreen_requested.connect(self.toggle_fullscreen)
        self.control_bar.playlist_toggle_requested.connect(self.toggle_playlist)
        self.control_bar.subtitle_settings_requested.connect(self.show_subtitle_settings)
        self.control_bar.subtitle_toggle_requested.connect(self.toggle_subtitles)
        self.control_bar.video_filters_requested.connect(self.show_video_filters)
        self.control_bar.enhancement_toggle_requested.connect(self.toggle_enhancement)
        
        # Seek Bar
        self.control_bar.seek_bar.seek_requested.connect(self.seek_absolute)
        
        # Volume
        self.control_bar.volume_ctrl.volume_changed.connect(self.set_volume)
        self.control_bar.volume_ctrl.mute_toggled.connect(self.set_mute)
        
        # Speed
        self.control_bar.speed_ctrl.speed_changed.connect(self.set_speed)
        
        # Playlist
        self.playlist_panel.item_activated.connect(self.play_file)
        
        # System Tray
        self.tray.restore_requested.connect(self.showNormal)
        self.tray.play_pause_requested.connect(self.toggle_playback)
        self.tray.next_requested.connect(self.play_next)
        self.tray.prev_requested.connect(self.play_prev)
        self.tray.check_updates_requested.connect(self.check_for_updates_now)
        self.tray.update_settings_requested.connect(self.open_update_settings)
        self.tray.quit_requested.connect(self.close)

        # Control Bar — mouse enter/leave for cursor auto-hide
        self.control_bar.mouse_entered.connect(self._pause_cursor_hide)
        self.control_bar.mouse_left.connect(self._resume_cursor_hide)

        # Schedule auto-update check on startup (delay to let window appear first)
        QTimer.singleShot(5000, self._auto_check_updates)

    def _restore_state(self):
        geom = self.settings.load_window_geometry()
        if geom:
            self.restoreGeometry(geom)
            
        state = self.settings.load_window_state()
        if state:
            self.restoreState(state)
            
        if self.settings.load_always_on_top():
            self.toggle_always_on_top(True)

        # Restore enhancement button state
        enhance_enabled, _ = self.settings.load_enhancement_settings()
        self.control_bar.set_enhancement_active(enhance_enabled)

    # ── Playback Controls ─────────────────────────────────────────────
    def play_file(self, filepath: str):
        if not os.path.exists(filepath):
            QMessageBox.warning(self, "Error", f"File not found: {filepath}")
            return
            
        media = self.vlc_instance.media_new(filepath)
        self.player.set_media(media)
        
        # Try loading subtitle
        self.subtitle_manager.auto_load_subtitle(self.player, filepath)
        
        self.player.play()
        self.update_timer.start()

        # Apply filters AFTER play() so the video pipeline is initialized
        self._apply_effective_filters()
        
        # Clear previous chapter markers and schedule extraction for new media
        self.control_bar.seek_bar.set_chapters([])
        QTimer.singleShot(800, self._extract_chapter_markers)
        
        title = os.path.basename(filepath)
        self.control_bar.set_title(title)
        self.setWindowTitle(f"Bam Player - {title}")
        
        self._current_filepath = filepath
        self.settings.save_last_file(filepath)
        self.settings.add_recent_file(filepath)

        # Update Discord Rich Presence (position is 0 — starts from beginning)
        duration = self.player.get_length()
        self.discord_rpc.set_playing(title, duration, position_ms=0)
        
    def toggle_playback(self):
        if self.player.get_state() == vlc.State.Playing:
            self.player.pause()
            self.osd.show_state('pause')
        else:
            if not self.player.get_media():
                # Try to play first item in playlist if no media
                first = self.playlist_panel.model.get_item(0)
                if first:
                    self.play_file(first.filepath)
                    return
            self.player.play()
            self.osd.show_state('play')

    def stop_playback(self):
        self.player.stop()
        self.update_timer.stop()
        self.control_bar.set_playing_state(False)
        self.control_bar.update_time(0, 0)
        self.control_bar.seek_bar.set_buffered(0)
        self.control_bar.seek_bar.set_chapters([])
        self.osd.show_state('stop')
        self.discord_rpc.clear_presence()

    def play_next(self):
        next_file = self.playlist_panel.get_next_item()
        if next_file:
            current_idx = self.playlist_panel.get_current_index()
            self.playlist_panel.set_current_index(current_idx + 1)
            self.play_file(next_file)

    def play_prev(self):
        prev_file = self.playlist_panel.get_prev_item()
        if prev_file:
            current_idx = self.playlist_panel.get_current_index()
            self.playlist_panel.set_current_index(current_idx - 1)
            self.play_file(prev_file)

    def seek_absolute(self, position_ms: int):
        self.player.set_time(position_ms)
        self.osd.show_seek(self.control_bar.time_label.text().split(' / ')[0])
        self._sync_discord_timer()

    def seek_relative(self, delta_ms: int):
        current = self.player.get_time()
        dur = self.player.get_length()
        if current >= 0 and dur > 0:
            new_pos = max(0, min(current + delta_ms, dur))
            self.player.set_time(int(new_pos))
            # Update UI immediately for responsiveness
            self.control_bar.seek_bar.set_position(int(new_pos))
            self.osd.show_seek(self.control_bar.time_label.text().split(' / ')[0])
            self._sync_discord_timer()

    def set_volume(self, volume: int):
        self.player.audio_set_volume(volume)
        self.settings.save_volume(volume)
        self.osd.show_volume(volume)

    def set_mute(self, muted: bool):
        self.player.audio_set_mute(muted)
        
    def set_speed(self, speed: float):
        self.player.set_rate(speed)
        self.settings.save_speed(speed)
        self.osd.show_speed(speed)

    def _extract_chapter_markers(self):
        """Extract chapter positions + names from the current media and populate seek bar.

        Uses a seek-and-record approach since libvlc doesn't expose chapter start times directly.
        Chapter names are sourced from libvlc media chapter descriptions if available.
        Pauses playback during scanning to avoid visual glitches, then restores state.
        """
        seek_bar = self.control_bar.seek_bar

        try:
            chapter_count = self.player.video_get_chapter_count()
        except Exception:
            chapter_count = 0

        # video_get_chapter_count returns -1 on error, 0 for no chapters, 1 for single default
        if chapter_count <= 1:
            seek_bar.set_chapters([])
            return

        # Save current state to restore after scanning
        saved_pos = self.player.get_time()
        saved_state = self.player.get_state()
        saved_chapter = max(self.player.video_get_chapter(), 0)
        was_playing = saved_state == vlc.State.Playing

        # Try to get chapter descriptions from the media (e.g. "Opening Credits", "Chapter 3")
        chapter_names = {}
        media = self.player.get_media()
        if media:
            try:
                media.parse()  # Ensure media metadata is fully parsed
                # python-vlc exposes libvlc_media_get_chapter_description as:
                #   media.get_chapter_description(title_index, chapter_index)
                # where -1 means "current title"
                for i in range(chapter_count):
                    try:
                        desc = media.get_chapter_description(-1, i)
                        if desc:
                            chapter_names[i] = desc.strip()
                    except Exception:
                        pass
            except Exception:
                pass

        # Pause during scanning to avoid visible seek artifacts
        if was_playing:
            self.player.set_pause(True)

        chapters = []
        try:
            # Skip chapter 0 (start of video at position 0)
            for i in range(1, chapter_count):
                self.player.video_set_chapter(i)
                pos = self.player.get_time()
                if pos > 10:  # Filter out spurious zero positions
                    name = chapter_names.get(i, f"Chapter {i}")
                    chapters.append((pos, name))
        except Exception:
            chapters = []

        # Restore playback state
        try:
            self.player.video_set_chapter(saved_chapter)
            if saved_pos > 0:
                self.player.set_time(saved_pos)
            if was_playing:
                self.player.play()
        except Exception:
            pass

        seek_bar.set_chapters(sorted(chapters))

    # ── VLC Event Callbacks ───────────────────────────────────────────
    @vlc.callbackmethod
    def _on_media_end(self, event):
        # Handle looping/next based on mode
        loop_mode = self.settings.load_loop_mode()
        if loop_mode == 'single':
            # Defer restart to main thread (VLC callbacks should not make libvlc calls)
            QTimer.singleShot(100, self._restart_current_media)
        else:
            # Schedule next track safely using QTimer (VLC callbacks shouldn't block/call GUI)
            QTimer.singleShot(100, self.play_next)

    def _restart_current_media(self):
        """Re-set the current media to restart playback (more reliable than set_time(0)).

        Re-loads subtitles and re-schedules chapter extraction since set_media()
        re-initializes the subtitle state internally.
        """
        current_media = self.player.get_media()
        if current_media:
            self.player.set_media(current_media)
            # Re-load subtitles (set_media re-initializes subtitle state)
            if self._current_filepath:
                self.subtitle_manager.auto_load_subtitle(self.player, self._current_filepath)
            # Clear and re-extract chapter markers
            self.control_bar.seek_bar.set_chapters([])
            QTimer.singleShot(800, self._extract_chapter_markers)
            self.player.play()

    def _reapply_filters(self):
        """Re-apply effective filters after pipeline is fully initialized."""
        self._apply_effective_filters()

    @vlc.callbackmethod
    def _on_playing(self, event):
        self.control_bar.set_playing_state(True)
        self.tray.update_play_state(True)
        # Re-apply filters once the video pipeline is fully initialized
        QTimer.singleShot(0, self._reapply_filters)
        # Update Discord presence on main thread (VLC callbacks run on libvlc thread)
        # Two-phase: first set_playing in play_file() may lack duration (media not parsed),
        # so this correction fires once VLC has the real length.
        if self._current_filepath:
            title = os.path.basename(self._current_filepath)
            duration = self.player.get_length()
            position = max(0, self.player.get_time())
            QTimer.singleShot(0, lambda t=title, d=duration, p=position: self.discord_rpc.set_playing(t, d, p))

    @vlc.callbackmethod
    def _on_paused(self, event):
        self.control_bar.set_playing_state(False)
        self.tray.update_play_state(False)
        # Update Discord on main thread to show paused state
        if self._current_filepath:
            title = os.path.basename(self._current_filepath)
            QTimer.singleShot(0, lambda t=title: self.discord_rpc.set_paused(t))

    def _sync_discord_timer(self):
        """Refresh the Discord Rich Presence timer to match current VLC position.

        Call this after seeking or any operation that changes playback position
        without triggering a new MediaPlayerPlaying event.
        """
        if not self._current_filepath or self.player.get_state() != vlc.State.Playing:
            return
        title = os.path.basename(self._current_filepath)
        duration = self.player.get_length()
        position = max(0, self.player.get_time())
        self.discord_rpc.set_playing(title, duration, position)

    def _update_ui_state(self):
        """Called periodically to update seek bar and time."""
        if self.player.get_state() in (vlc.State.Playing, vlc.State.Paused):
            time = self.player.get_time()
            length = self.player.get_length()
            if time >= 0 and length > 0:
                self.control_bar.update_time(time, length)
                
                # Approximate buffering based on position for local files
                # VLC python bindings don't expose fine-grained network buffering easily
                self.control_bar.seek_bar.set_buffered(length)

    # ── UI Actions ────────────────────────────────────────────────────
    def toggle_fullscreen(self):
        self.set_fullscreen(not self.is_fullscreen)

    def set_fullscreen(self, fullscreen: bool):
        self.is_fullscreen = fullscreen
        
        # Hide menu bar in fullscreen (no Help section cluttering the view)
        if hasattr(self, '_menubar'):
            self._menubar.setVisible(not fullscreen)
        
        # Windows 11 rounded corners fix
        import sys
        if sys.platform == "win32":
            import ctypes
            try:
                hwnd = int(self.winId())
                DWMWA_WINDOW_CORNER_PREFERENCE = 33
                val = ctypes.c_int(1 if fullscreen else 0) # 1 = DONOTROUND, 0 = DEFAULT
                ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_WINDOW_CORNER_PREFERENCE, ctypes.byref(val), ctypes.sizeof(val))
            except Exception:
                pass

        if fullscreen:
            self.showFullScreen()
        else:
            self.showNormal()

    def toggle_playlist(self):
        is_visible = not self.playlist_panel.isVisible()
        self.playlist_panel.setVisible(is_visible)
        self.settings.save_playlist_visible(is_visible)

    def toggle_always_on_top(self, force_state=None):
        flags = self.windowFlags()
        if force_state is not None:
            is_on_top = force_state
        else:
            is_on_top = not bool(flags & Qt.WindowType.WindowStaysOnTopHint)
            
        if is_on_top:
            self.setWindowFlags(flags | Qt.WindowType.WindowStaysOnTopHint)
            self.osd.show_message("Always on Top: ON")
        else:
            self.setWindowFlags(flags & ~Qt.WindowType.WindowStaysOnTopHint)
            self.osd.show_message("Always on Top: OFF")
            
        self.show() # Required after changing window flags
        self.settings.save_always_on_top(is_on_top)

    def show_subtitle_settings(self):
        dialog = SubtitleStyleDialog(self, self.subtitle_manager.prefs)
        dialog.prefs_changed.connect(self._on_subtitle_prefs_changed)
        dialog.exec()
        
    def _on_subtitle_prefs_changed(self, prefs: dict):
        self.settings.save_subtitle_prefs(prefs)
        self.subtitle_manager.prefs = prefs
        self.osd.show_message("Subtitle styles saved")

    def toggle_subtitles(self):
        """Real-time toggle of subtitle visibility (on/off)."""
        active = self.subtitle_manager.toggle_subtitles(self.player)
        self.control_bar.set_subtitle_active(active)
        if active:
            self.osd.show_message("Subtitles: ON")
        else:
            self.osd.show_message("Subtitles: OFF")

    def show_video_filters(self):
        current = self.settings.load_filter_values()
        enhance_enabled, enhance_sharpness = self.settings.load_enhancement_settings()
        dialog = VideoFiltersDialog(self, current, enhance_enabled, enhance_sharpness)
        dialog.filters_changed.connect(self._on_filters_changed)
        dialog.enhancement_changed.connect(self._on_enhancement_changed)
        dialog.exec()
        
    def _on_filters_changed(self, filters: dict):
        self.settings.save_filter_values(filters)
        self._apply_effective_filters()

    def _on_enhancement_changed(self, enabled: bool, sharpness: float):
        self.settings.save_enhancement_settings(enabled, sharpness)
        self.control_bar.set_enhancement_active(enabled)
        self._apply_effective_filters()

    def toggle_enhancement(self):
        """Quick-toggle enhancement on/off from control bar button."""
        enabled, sharpness = self.settings.load_enhancement_settings()
        new_enabled = not enabled
        if new_enabled and sharpness <= 0:
            # Default to 50% sharpness if turning on from zero
            sharpness = 50.0
        self.settings.save_enhancement_settings(new_enabled, sharpness)
        self.control_bar.set_enhancement_active(new_enabled)
        self._apply_effective_filters()
        if new_enabled:
            self.osd.show_message("Enhancement: ON")
        else:
            self.osd.show_message("Enhancement: OFF")

    def _apply_effective_filters(self):
        """Combine raw filter values with enhancement settings and apply to VLC."""
        filters = self.settings.load_filter_values()
        enhance_enabled, sharpness = self.settings.load_enhancement_settings()

        if enhance_enabled and sharpness > 0:
            # Apply enhancement on top of user's manual adjustments
            sharp_factor = sharpness / 100.0
            enhanced = filters.copy()
            enhanced['contrast'] = filters['contrast'] * (1.0 + sharp_factor * 0.4)
            enhanced['saturation'] = filters['saturation'] * (1.0 + sharp_factor * 0.3)
            enhanced['gamma'] = filters['gamma'] * (1.0 - sharp_factor * 0.1)
            # Clamp to valid VLC ranges
            enhanced['contrast'] = max(0.0, min(2.0, enhanced['contrast']))
            enhanced['saturation'] = max(0.0, min(3.0, enhanced['saturation']))
            enhanced['gamma'] = max(0.01, min(10.0, enhanced['gamma']))
            apply_filters_to_player(self.player, enhanced)
        else:
            apply_filters_to_player(self.player, filters)

    def open_file_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Open Media", "", 
            "Media Files (*.mp4 *.mkv *.avi *.mov *.wmv *.flv *.webm *.mp3 *.flac *.wav)"
        )
        if files:
            self.playlist_panel.model.add_items(files)
            if self.player.get_state() != vlc.State.Playing:
                # Play the first added file
                idx = self.playlist_panel.model.rowCount() - len(files)
                self.playlist_panel.set_current_index(idx)
                self.play_file(files[0])

    def open_folder_dialog(self):
        folder = QFileDialog.getExistingDirectory(self, "Open Folder")
        if folder:
            files = get_video_files_from_dir(folder)
            if files:
                self.playlist_panel.model.add_items(files)

    def take_screenshot(self):
        if self.player.get_state() in (vlc.State.Playing, vlc.State.Paused):
            folder = get_pictures_folder()
            # Simple timestamp filename
            import time
            filename = os.path.join(folder, f"bam_shot_{int(time.time())}.png")
            # In libvlc, snapshot is done async
            # For 0 width/height it uses original size
            if self.player.video_take_snapshot(0, filename, 0, 0) == 0:
                self.osd.show_screenshot(filename)

    def _on_mouse_moved(self):
        """Show control bar + cursor on mouse move over video."""
        self.control_bar.reset_hide_timer()
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self._reset_cursor_hide_timer()

    def _reset_cursor_hide_timer(self):
        """Restart the cursor auto-hide countdown (only when playing)."""
        if self.player.get_state() == vlc.State.Playing:
            self._cursor_hide_timer.start(3000)

    def _pause_cursor_hide(self):
        """Keep cursor visible when hovering the control bar."""
        self._cursor_hide_timer.stop()
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def _resume_cursor_hide(self):
        """Restart cursor hide countdown when leaving the control bar."""
        self._reset_cursor_hide_timer()

    def _on_cursor_hide_timeout(self):
        """Hide the cursor after inactivity."""
        self.setCursor(Qt.CursorShape.BlankCursor)

    # ── Drag and Drop ─────────────────────────────────────────────────
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        files = [url.toLocalFile() for url in urls if url.isLocalFile()]
        
        added = False
        for f in files:
            if os.path.isdir(f):
                dir_files = get_video_files_from_dir(f)
                if dir_files:
                    self.playlist_panel.model.add_items(dir_files)
                    added = True
            else:
                if self.playlist_panel.model.add_item(f):
                    added = True
                    
        if added and self.player.get_state() != vlc.State.Playing:
             # Play last added (or first if playlist was empty)
             self.play_file(self.playlist_panel.model.get_item(0).filepath)

    # ── Update Checking & Auto-Install ─────────────────────────────────
    def _auto_check_updates(self):
        """Run a silent update check on startup if auto-check is due."""
        if not self.update_checker:
            return

        auto_check, interval = self._get_auto_check_settings()
        if not auto_check:
            return

        last_check = self.settings.load_last_update_check()
        if last_check > 0 and (time.time() - last_check) < interval * 3600:
            return  # Not due yet

        self._run_update_check(silent=True)

    def _get_auto_check_settings(self) -> tuple:
        """Return (auto_check_enabled, interval_hours)."""
        _, enabled, interval = self.settings.load_update_settings()
        return enabled, interval

    def _run_update_check(self, silent: bool = False):
        """Check for updates. When silent, only notify if a new version is found."""
        if not self.update_checker.repo:
            return

        # Run the HTTP request in a background thread to avoid blocking the UI
        import threading

        def _check():
            try:
                release = self.update_checker.check_for_updates()
                # Mark this check as done regardless of result
                self.settings.save_last_update_check(time.time())

                if release:
                    # Check if the user already skipped this version
                    skipped = self.settings.load_skipped_version()
                    if silent and skipped == release.version:
                        return  # Only skip silently during auto-checks

                    def show_dialog():
                        dialog = UpdateAvailableDialog(release, self)
                        result = dialog.exec()
                        if result == QDialog.DialogCode.Rejected:
                            # User clicked "Remind Me Later" — skip this version
                            self.settings.save_skipped_version(release.version)
                        elif result == QDialog.DialogCode.Accepted:
                            # User clicked "Download & Install" — start auto-install
                            QTimer.singleShot(
                                0, lambda r=release: self._download_and_install_update(r)
                            )
                    QTimer.singleShot(0, show_dialog)
                    return
                elif not silent:
                    def show_uptodate():
                        UpToDateDialog(self).exec()
                    QTimer.singleShot(0, show_uptodate)
            except ConnectionError as exc:
                if not silent:
                    def show_error():
                        QMessageBox.warning(
                            self, "Update Check Failed",
                            f"Could not connect to GitHub to check for updates.\n\n"
                            f"Details: {exc}\n\n"
                            f"Please check your internet connection and try again."
                        )
                    QTimer.singleShot(0, show_error)
            except Exception:
                if not silent:
                    def show_error():
                        self.osd.show_message("Update check failed — check your connection")
                    QTimer.singleShot(0, show_error)

        thread = threading.Thread(target=_check, daemon=True)
        thread.start()

    def check_for_updates_now(self):
        """Called from menu/tray action — runs update check with full feedback."""
        self.osd.show_message("Checking for updates…")
        self._run_update_check(silent=False)

    def open_update_settings(self):
        """Open the update configuration dialog."""
        from .update_checker import DEFAULT_REPO
        dialog = UpdateSettingsDialog(self, self.settings)
        if dialog.exec():
            repo, auto_check, interval = dialog.get_values()
            self.settings.save_update_settings(repo, auto_check, interval)
            # Recreate the checker with the (possibly changed) repo
            self.update_checker = UpdateChecker(repo or DEFAULT_REPO)
            self.osd.show_message("Update settings saved")

    def _download_and_install_update(self, release: ReleaseInfo):
        """Download the installer, then open the folder in Explorer.

        If the download URL isn't an .exe (e.g. portable zip or source),
        fall back to opening it in the browser instead.
        """
        url = release.download_url
        if not url.lower().endswith(".exe"):
            webbrowser.open(url)
            self.osd.show_message(
                f"Download opened in your browser (v{release.version})"
            )
            return

        dialog = UpdateDownloadDialog(release, self)
        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted and dialog.installer_path:
            self._show_in_explorer(dialog.installer_path)

    def _show_in_explorer(self, path: str):
        """Open Windows Explorer with the given file selected."""
        if not os.path.exists(path):
            QMessageBox.critical(
                self,
                "File Not Found",
                "The downloaded file could not be found. Try downloading again.",
            )
            return

        try:
            # Opens Explorer with the file highlighted
            subprocess.Popen(["explorer", "/select,", os.path.normpath(path)])
        except Exception as e:
            # Fallback: just open the containing folder
            try:
                folder = os.path.dirname(path)
                os.startfile(folder)
            except Exception:
                QMessageBox.warning(
                    self, "Update",
                    f"File saved to:\n{path}\n\nPlease run it manually to install the update.",
                )

    # ── Shutdown ──────────────────────────────────────────────────────
    def closeEvent(self, event):
        try:
            self.stop_playback()
            self.settings.save_window_geometry(self.saveGeometry())
            self.settings.save_window_state(self.saveState())
            
            # Current file position saving
            if self.player.get_media():
                m = self.player.get_media()
                try:
                    m.parse()
                    uri = m.get_mrl()
                    if uri and uri.startswith('file:///'):
                        filepath = uri[8:]
                        time = self.player.get_time()
                        self.settings.save_last_file(filepath, time)
                except Exception:
                    pass
        except Exception as e:
            print("Error during shutdown:", e)
            
        try:
            self.tray.hide()
        except Exception:
            pass

        # Close Discord RPC connection
        try:
            self.discord_rpc.close()
        except Exception:
            pass
            
        super().closeEvent(event)
