"""
Overlay control bar with auto-hide behavior.
Contains play/pause, seek, volume, speed, and other playback controls.
"""
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QSizePolicy, QMenu
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QSize
from PyQt6.QtGui import QAction
import qtawesome as qta
from .styles import get_control_bar_stylesheet
from .seek_bar import SeekBar
from .volume_control import VolumeControl
from .speed_control import SpeedControl
from .utils import format_time


class ControlBar(QWidget):
    """Bottom overlay control bar for video playback."""
    
    play_pause_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    next_requested = pyqtSignal()
    prev_requested = pyqtSignal()
    fullscreen_requested = pyqtSignal()
    playlist_toggle_requested = pyqtSignal()
    open_requested = pyqtSignal()
    subtitle_settings_requested = pyqtSignal()
    subtitle_toggle_requested = pyqtSignal()
    video_filters_requested = pyqtSignal()
    enhancement_toggle_requested = pyqtSignal()
    mouse_entered = pyqtSignal()
    mouse_left = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("controlBar")
        self.setStyleSheet(get_control_bar_stylesheet())
        
        # Ensure it stays at the bottom and spans the width
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(85)
        
        self.is_playing = False
        self._setup_ui()
        
        # Auto-hide setup
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.hide)
        
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 5, 10, 5)
        main_layout.setSpacing(0)
        
        # Top row: Seek Bar
        self.seek_bar = SeekBar()
        main_layout.addWidget(self.seek_bar)
        
        # Bottom row: Controls
        ctrl_layout = QHBoxLayout()
        ctrl_layout.setSpacing(5)
        
        # Playback buttons
        self.btn_prev = QPushButton()
        self.btn_prev.setIcon(qta.icon('mdi6.skip-previous', color='#e8e8f0'))
        self.btn_prev.setIconSize(QSize(22, 22))
        self.btn_prev.setFixedSize(32, 32)
        self.btn_prev.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_prev.setObjectName("controlButton")
        self.btn_prev.setToolTip("Previous")
        self.btn_prev.clicked.connect(self.prev_requested.emit)
        ctrl_layout.addWidget(self.btn_prev)
        
        self.btn_play = QPushButton()
        self.btn_play.setIcon(qta.icon('mdi6.play', color='white'))
        self.btn_play.setIconSize(QSize(28, 28))
        self.btn_play.setFixedSize(40, 40)
        self.btn_play.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_play.setObjectName("playButton")
        self.btn_play.setToolTip("Play/Pause (Space)")
        self.btn_play.clicked.connect(self.play_pause_requested.emit)
        ctrl_layout.addWidget(self.btn_play)
        
        self.btn_stop = QPushButton()
        self.btn_stop.setIcon(qta.icon('mdi6.stop', color='#e8e8f0'))
        self.btn_stop.setIconSize(QSize(22, 22))
        self.btn_stop.setFixedSize(32, 32)
        self.btn_stop.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_stop.setObjectName("controlButton")
        self.btn_stop.setToolTip("Stop")
        self.btn_stop.clicked.connect(self.stop_requested.emit)
        ctrl_layout.addWidget(self.btn_stop)
        
        self.btn_next = QPushButton()
        self.btn_next.setIcon(qta.icon('mdi6.skip-next', color='#e8e8f0'))
        self.btn_next.setIconSize(QSize(22, 22))
        self.btn_next.setFixedSize(32, 32)
        self.btn_next.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_next.setObjectName("controlButton")
        self.btn_next.setToolTip("Next")
        self.btn_next.clicked.connect(self.next_requested.emit)
        ctrl_layout.addWidget(self.btn_next)
        
        # Time Label
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setObjectName("timeLabel")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setMinimumWidth(100)
        ctrl_layout.addWidget(self.time_label)
        
        # Title label (stretches)
        self.title_label = QLabel("")
        self.title_label.setObjectName("titleLabel")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Elide text if too long
        font_metrics = self.title_label.fontMetrics()
        self.title_label.setMinimumWidth(100)
        ctrl_layout.addWidget(self.title_label, 1)
        
        # Volume
        self.volume_ctrl = VolumeControl()
        self.volume_ctrl.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        ctrl_layout.addWidget(self.volume_ctrl)
        
        # Speed
        self.speed_ctrl = SpeedControl()
        self.speed_ctrl.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        ctrl_layout.addWidget(self.speed_ctrl)
        
        # Tools
        self.btn_open = QPushButton()
        self.btn_open.setIcon(qta.icon('mdi6.folder-open', color='#e8e8f0'))
        self.btn_open.setIconSize(QSize(20, 20))
        self.btn_open.setFixedSize(32, 32)
        self.btn_open.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_open.setObjectName("controlButton")
        self.btn_open.setToolTip("Open File")
        self.btn_open.clicked.connect(self.open_requested.emit)
        ctrl_layout.addWidget(self.btn_open)
        
        self.btn_sub = QPushButton()
        self.btn_sub.setIcon(qta.icon('mdi6.subtitles-outline', color='#e8e8f0'))
        self.btn_sub.setIconSize(QSize(20, 20))
        self.btn_sub.setFixedSize(32, 32)
        self.btn_sub.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_sub.setObjectName("subtitleButton")
        self.btn_sub.setToolTip("Toggle Subtitles (Ctrl+D) — Right-click for settings")
        self.btn_sub.clicked.connect(self.subtitle_toggle_requested.emit)
        self.btn_sub.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.btn_sub.customContextMenuRequested.connect(self._show_subtitle_context_menu)
        ctrl_layout.addWidget(self.btn_sub)

        self._subtitles_active = True
        
        self.btn_filter = QPushButton()
        self.btn_filter.setIcon(qta.icon('mdi6.tune', color='#e8e8f0'))
        self.btn_filter.setIconSize(QSize(20, 20))
        self.btn_filter.setFixedSize(32, 32)
        self.btn_filter.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_filter.setObjectName("controlButton")
        self.btn_filter.setToolTip("Video Filters")
        self.btn_filter.clicked.connect(self.video_filters_requested.emit)
        ctrl_layout.addWidget(self.btn_filter)

        self.btn_enhance = QPushButton()
        self.btn_enhance.setIcon(qta.icon('mdi6.magic-staff', color='#8888a0'))
        self.btn_enhance.setIconSize(QSize(20, 20))
        self.btn_enhance.setFixedSize(32, 32)
        self.btn_enhance.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_enhance.setObjectName("enhanceButton")
        self.btn_enhance.setToolTip("Toggle Real-time Enhancement (Ctrl+E)")
        self.btn_enhance.clicked.connect(self.enhancement_toggle_requested.emit)
        ctrl_layout.addWidget(self.btn_enhance)
        
        self._enhancement_active = False
        
        self.btn_playlist = QPushButton()
        self.btn_playlist.setIcon(qta.icon('mdi6.playlist-music', color='#e8e8f0'))
        self.btn_playlist.setIconSize(QSize(20, 20))
        self.btn_playlist.setFixedSize(32, 32)
        self.btn_playlist.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_playlist.setObjectName("controlButton")
        self.btn_playlist.setToolTip("Toggle Playlist")
        self.btn_playlist.clicked.connect(self.playlist_toggle_requested.emit)
        ctrl_layout.addWidget(self.btn_playlist)
        
        self.btn_fullscreen = QPushButton()
        self.btn_fullscreen.setIcon(qta.icon('mdi6.fullscreen', color='#e8e8f0'))
        self.btn_fullscreen.setIconSize(QSize(20, 20))
        self.btn_fullscreen.setFixedSize(32, 32)
        self.btn_fullscreen.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_fullscreen.setObjectName("controlButton")
        self.btn_fullscreen.setToolTip("Fullscreen (F11)")
        self.btn_fullscreen.clicked.connect(self.fullscreen_requested.emit)
        ctrl_layout.addWidget(self.btn_fullscreen)
        
        main_layout.addLayout(ctrl_layout)

    def set_enhancement_active(self, active: bool):
        """Update the enhancement button appearance to reflect its state."""
        self._enhancement_active = active
        icon_color = '#a29bfe' if active else '#8888a0'
        self.btn_enhance.setIcon(qta.icon('mdi6.magic-staff', color=icon_color))
        self.btn_enhance.setToolTip(
            "Disable Enhancement (Ctrl+E)" if active else "Enable Enhancement (Ctrl+E)"
        )
        if active:
            self.btn_enhance.setProperty("active", "true")
        else:
            self.btn_enhance.setProperty("active", "false")
        self.btn_enhance.style().unpolish(self.btn_enhance)
        self.btn_enhance.style().polish(self.btn_enhance)

    def set_subtitle_active(self, active: bool):
        """Update the subtitle button appearance to reflect subtitle visibility."""
        self._subtitles_active = active
        icon_color = '#e8e8f0' if active else '#8888a0'
        self.btn_sub.setIcon(qta.icon('mdi6.subtitles-outline', color=icon_color))
        self.btn_sub.setProperty("active", "true" if active else "false")
        self.btn_sub.style().unpolish(self.btn_sub)
        self.btn_sub.style().polish(self.btn_sub)

    def _show_subtitle_context_menu(self, pos):
        """Show context menu for subtitle button (settings access)."""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1e1e2e;
                color: #e8e8f0;
                border: 1px solid #3a3a4e;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #6c5ce7;
            }
        """)
        toggle_action = QAction("Toggle Subtitles", self)
        toggle_action.triggered.connect(self.subtitle_toggle_requested.emit)
        menu.addAction(toggle_action)
        menu.addSeparator()
        settings_action = QAction("Subtitle Settings…", self)
        settings_action.triggered.connect(self.subtitle_settings_requested.emit)
        menu.addAction(settings_action)
        menu.exec(self.btn_sub.mapToGlobal(pos))

    def set_playing_state(self, playing: bool):
        self.is_playing = playing
        icon_name = 'mdi6.pause' if playing else 'mdi6.play'
        self.btn_play.setIcon(qta.icon(icon_name, color='white'))

    def update_time(self, pos_ms: int, dur_ms: int):
        self.seek_bar.set_position(pos_ms)
        self.seek_bar.set_duration(dur_ms)
        self.time_label.setText(f"{format_time(pos_ms)} / {format_time(dur_ms)}")
        
    def set_title(self, title: str):
        metrics = self.title_label.fontMetrics()
        elided = metrics.elidedText(title, Qt.TextElideMode.ElideRight, 300)
        self.title_label.setText(elided)
        self.title_label.setToolTip(title)

    # ── Visibility ───────────────────────────────────────────────────
    def reset_hide_timer(self, timeout=3000):
        """Reset the auto-hide timer."""
        self.show()
        if self.is_playing:
            self._hide_timer.start(timeout)
        
    def enterEvent(self, event):
        """Stop hiding when mouse enters."""
        self._hide_timer.stop()
        self.mouse_entered.emit()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """Resume hiding when mouse leaves."""
        if self.is_playing:
            self._hide_timer.start(3000)
        self.mouse_left.emit()
        super().leaveEvent(event)
