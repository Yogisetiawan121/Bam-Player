"""
Main application window integrating all components.
"""
import os
import sys
import vlc
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QFileDialog, QMessageBox, QSplitter)
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
from .utils import get_pictures_folder


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
        
        self._setup_ui()
        self._setup_vlc()
        self._connect_signals()
        setup_shortcuts(self)
        
        self._restore_state()
        
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
        self.control_bar.video_filters_requested.connect(self.show_video_filters)
        
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
        self.tray.quit_requested.connect(self.close)

    def _restore_state(self):
        geom = self.settings.load_window_geometry()
        if geom:
            self.restoreGeometry(geom)
            
        state = self.settings.load_window_state()
        if state:
            self.restoreState(state)
            
        if self.settings.load_always_on_top():
            self.toggle_always_on_top(True)

    # ── Playback Controls ─────────────────────────────────────────────
    def play_file(self, filepath: str):
        if not os.path.exists(filepath):
            QMessageBox.warning(self, "Error", f"File not found: {filepath}")
            return
            
        media = self.vlc_instance.media_new(filepath)
        self.player.set_media(media)
        
        # Try loading subtitle
        self.subtitle_manager.auto_load_subtitle(self.player, filepath)
        
        # Apply filters
        filters = self.settings.load_filter_values()
        apply_filters_to_player(self.player, filters)
        
        self.player.play()
        self.update_timer.start()
        
        title = os.path.basename(filepath)
        self.control_bar.set_title(title)
        self.setWindowTitle(f"Bam Player - {title}")
        
        self.settings.save_last_file(filepath)
        self.settings.add_recent_file(filepath)
        
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
        self.osd.show_state('stop')

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

    def seek_relative(self, delta_ms: int):
        current = self.player.get_time()
        dur = self.player.get_length()
        if current >= 0 and dur > 0:
            new_pos = max(0, min(current + delta_ms, dur))
            self.player.set_time(int(new_pos))
            # Update UI immediately for responsiveness
            self.control_bar.seek_bar.set_position(int(new_pos))
            self.osd.show_seek(self.control_bar.time_label.text().split(' / ')[0])

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

    # ── VLC Event Callbacks ───────────────────────────────────────────
    @vlc.callbackmethod
    def _on_media_end(self, event):
        # Handle looping/next based on mode
        loop_mode = self.settings.load_loop_mode()
        if loop_mode == 'single':
            # Restart current
            pass # Requires re-setting media in some VLC versions, or setting position to 0
        else:
            # Schedule next track safely using QTimer (VLC callbacks shouldn't block/call GUI)
            QTimer.singleShot(100, self.play_next)

    @vlc.callbackmethod
    def _on_playing(self, event):
        self.control_bar.set_playing_state(True)
        self.tray.update_play_state(True)

    @vlc.callbackmethod
    def _on_paused(self, event):
        self.control_bar.set_playing_state(False)
        self.tray.update_play_state(False)

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

    def show_video_filters(self):
        current = self.settings.load_filter_values()
        dialog = VideoFiltersDialog(self, current)
        dialog.filters_changed.connect(self._on_filters_changed)
        dialog.exec()
        
    def _on_filters_changed(self, filters: dict):
        self.settings.save_filter_values(filters)
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
        """Show control bar on mouse move over video."""
        self.control_bar.reset_hide_timer()
        self.setCursor(Qt.CursorShape.ArrowCursor)

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
            
        super().closeEvent(event)
