"""
Video rendering surface using python-vlc.
Handles hardware acceleration, embedding the VLC window, and emitting playback events.
"""
import sys
import vlc
from PyQt6.QtWidgets import QFrame
from PyQt6.QtCore import Qt, pyqtSignal


class VideoWidget(QFrame):
    """VLC video rendering widget with hardware acceleration support."""

    # Signals
    mouse_moved = pyqtSignal()
    double_clicked = pyqtSignal()
    clicked = pyqtSignal()
    right_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet("background-color: black; border: none;")
        self.setMouseTracking(True)
        self.setAcceptDrops(True)

        # Create VLC instance with hardware acceleration and optimal caching
        vlc_args = [
            '--no-xlib',
            '--drop-late-frames',
            '--skip-frames',
            '--avcodec-hw=any',
            '--avcodec-threads=0',
            '--network-caching=1000',
            '--file-caching=500',
        ]
        self.instance = vlc.Instance(vlc_args)
        self.media_player = self.instance.media_player_new()

        # Disable VLC's default mouse and keyboard handling so Qt can handle it
        self.media_player.video_set_mouse_input(False)
        self.media_player.video_set_key_input(False)

        # Set the window id where to render VLC's video output
        self._set_window_id()

    def _set_window_id(self):
        """Pass the window id to libvlc."""
        if sys.platform.startswith('linux'):
            self.media_player.set_xwindow(self.winId())
        elif sys.platform == "win32":
            self.media_player.set_hwnd(self.winId())
        elif sys.platform == "darwin":
            try:
                self.media_player.set_nsobject(int(self.winId()))
            except Exception:
                self.media_player.set_nsobject(self.winId())

    def get_player(self) -> vlc.MediaPlayer:
        return self.media_player

    def get_instance(self) -> vlc.Instance:
        return self.instance

    # ── Mouse Events ──────────────────────────────────────────────────
    def mouseMoveEvent(self, event):
        self.mouse_moved.emit()
        super().mouseMoveEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit()
        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        elif event.button() == Qt.MouseButton.RightButton:
            self.right_clicked.emit()
        super().mousePressEvent(event)
