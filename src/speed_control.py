"""
Speed control widget with preset speeds and custom selector.
Supports 0.25x to 4x playback speed.
"""
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QMenu
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction


class SpeedControl(QWidget):
    """Playback speed selector with presets from 0.25x to 4x."""

    speed_changed = pyqtSignal(float)

    PRESETS = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 4.0]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._speed = 1.0
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._btn = QPushButton("1.0x")
        self._btn.setObjectName("controlButton")
        self._btn.setFixedSize(50, 32)
        self._btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn.setToolTip("Playback Speed")
        self._btn.clicked.connect(self._show_menu)
        layout.addWidget(self._btn)

    def _show_menu(self):
        menu = QMenu(self)
        for speed in self.PRESETS:
            action = QAction(f"{speed:.2f}x", menu)
            action.setCheckable(True)
            action.setChecked(abs(speed - self._speed) < 0.01)
            action.triggered.connect(lambda checked, s=speed: self.set_speed(s))
            menu.addAction(action)

        # Show menu above the button
        pos = self._btn.mapToGlobal(self._btn.rect().topLeft())
        pos.setY(pos.y() - menu.sizeHint().height())
        menu.exec(pos)

    def set_speed(self, speed: float):
        """Set playback speed."""
        speed = max(0.25, min(4.0, speed))
        self._speed = speed
        self._btn.setText(f"{speed:.2g}x")
        self.speed_changed.emit(speed)

    def get_speed(self) -> float:
        return self._speed

    def increase_speed(self):
        """Jump to next preset speed."""
        for s in self.PRESETS:
            if s > self._speed + 0.01:
                self.set_speed(s)
                return
        self.set_speed(self.PRESETS[-1])

    def decrease_speed(self):
        """Jump to previous preset speed."""
        for s in reversed(self.PRESETS):
            if s < self._speed - 0.01:
                self.set_speed(s)
                return
        self.set_speed(self.PRESETS[0])

    def reset_speed(self):
        """Reset to 1.0x."""
        self.set_speed(1.0)
