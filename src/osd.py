"""
On-Screen Display (OSD) overlay widget.
Shows animated notifications for volume, speed, seek, and other state changes.
"""
from PyQt6.QtWidgets import QLabel, QWidget, QGraphicsOpacityEffect, QHBoxLayout
from PyQt6.QtCore import QTimer, QPropertyAnimation, QEasingCurve, Qt, pyqtProperty
from PyQt6.QtGui import QFont
from .styles import get_osd_stylesheet


class OSDWidget(QWidget):
    """Animated on-screen display overlay for player notifications."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(get_osd_stylesheet())

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._label = QLabel(self)
        self._label.setObjectName("osdLabel")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont("Segoe UI", 16, QFont.Weight.DemiBold)
        self._label.setFont(font)
        layout.addWidget(self._label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Opacity effect for fade animation
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(0.0)
        self.setGraphicsEffect(self._opacity_effect)

        # Fade animation
        self._fade_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Auto-hide timer
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._fade_out)

        self._display_duration = 1500  # ms before fade starts
        self._fade_duration = 400  # ms for fade animation

        self.hide()

    def show_message(self, text: str, duration: int = 1500, icon: str = ""):
        """Display an OSD message with optional icon prefix."""
        display_text = f"{icon}  {text}" if icon else text
        self._label.setText(display_text)

        # Stop any running animations
        self._fade_anim.stop()
        self._hide_timer.stop()

        # Position at top-center of parent
        self._reposition()

        # Fade in
        self._opacity_effect.setOpacity(0.0)
        self.show()
        self.raise_()

        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.setDuration(200)
        self._fade_anim.start()

        # Schedule fade out
        self._display_duration = duration
        self._hide_timer.start(self._display_duration)

    def show_volume(self, volume: int):
        """Show volume change notification."""
        bar = self._make_bar(volume, 150)
        self.show_message(f"{bar}  {volume}%")

    def show_speed(self, speed: float):
        """Show speed change notification."""
        self.show_message(f"{speed:.2f}x")

    def show_seek(self, time_str: str):
        """Show seek position notification."""
        self.show_message(time_str, duration=1000)

    def show_state(self, state: str):
        """Show play state notification."""
        self.show_message(state.replace('_', ' ').title(), duration=1000)

    def show_screenshot(self, path: str):
        """Show screenshot saved notification."""
        self.show_message(f"Screenshot saved", duration=2000)

    def _make_bar(self, value: int, max_val: int) -> str:
        """Create a text-based progress bar."""
        filled = int((value / max_val) * 15)
        return "█" * filled + "░" * (15 - filled)

    def _fade_out(self):
        """Start fade-out animation."""
        # Disconnect any existing connections to prevent handler accumulation
        try:
            self._fade_anim.finished.disconnect(self._on_fade_out_done)
        except TypeError:
            pass
        self._fade_anim.setStartValue(self._opacity_effect.opacity())
        self._fade_anim.setEndValue(0.0)
        self._fade_anim.setDuration(self._fade_duration)
        self._fade_anim.finished.connect(self._on_fade_out_done)
        self._fade_anim.start()

    def _on_fade_out_done(self):
        """Hide widget after fade completes."""
        try:
            self._fade_anim.finished.disconnect(self._on_fade_out_done)
        except TypeError:
            pass
        self.hide()

    def _reposition(self):
        """Position the OSD at the top-center of the parent widget."""
        if self.parent():
            parent = self.parent()
            self.adjustSize()
            w = max(self._label.sizeHint().width() + 60, 200)
            h = self._label.sizeHint().height() + 20
            x = (parent.width() - w) // 2
            y = int(parent.height() * 0.08)
            self.setGeometry(x, y, w, h)

    def showEvent(self, event):
        super().showEvent(event)
        self._reposition()
