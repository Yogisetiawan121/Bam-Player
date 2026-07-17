"""
Volume control widget with slider and mute toggle.
Supports 0-150% volume with visual boost indicator.
"""
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QSlider, QToolTip
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QSize
from PyQt6.QtGui import QWheelEvent
import qtawesome as qta
from .utils import clamp


class VolumeControl(QWidget):
    """Volume slider with mute button and 0-150% range."""

    volume_changed = pyqtSignal(int)  # 0-150
    mute_toggled = pyqtSignal(bool)

    VOLUME_ICONS = {
        'muted': 'mdi6.volume-off',
        'low': 'mdi6.volume-low',
        'medium': 'mdi6.volume-medium',
        'high': 'mdi6.volume-high',
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._volume = 80
        self._muted = False
        self._pre_mute_volume = 80
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Mute button
        self._mute_btn = QPushButton()
        self._mute_btn.setIcon(qta.icon(self.VOLUME_ICONS['high'], color='#e8e8f0'))
        self._mute_btn.setIconSize(QSize(20, 20))
        self._mute_btn.setObjectName("controlButton")
        self._mute_btn.setFixedSize(32, 32)
        self._mute_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._mute_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._mute_btn.setToolTip("Mute/Unmute (M)")
        self._mute_btn.clicked.connect(self.toggle_mute)
        layout.addWidget(self._mute_btn)

        # Volume slider
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._slider.setRange(0, 150)
        self._slider.setValue(80)
        self._slider.setFixedWidth(100)
        self._slider.setCursor(Qt.CursorShape.PointingHandCursor)
        self._slider.setToolTip("Volume: 80%")
        self._slider.valueChanged.connect(self._on_slider_changed)
        layout.addWidget(self._slider)

    def _on_slider_changed(self, value: int):
        self._volume = value
        self._muted = value == 0
        self._update_icon()
        self._slider.setToolTip(f"Volume: {value}%")
        self.volume_changed.emit(value)

    def _update_icon(self):
        if self._muted or self._volume == 0:
            icon_name = self.VOLUME_ICONS['muted']
            color = '#ff6b6b'
        elif self._volume < 40:
            icon_name = self.VOLUME_ICONS['low']
            color = '#e8e8f0'
        elif self._volume < 80:
            icon_name = self.VOLUME_ICONS['medium']
            color = '#e8e8f0'
        else:
            icon_name = self.VOLUME_ICONS['high']
            color = '#51cf66' if self._volume > 100 else '#e8e8f0'
            
        self._mute_btn.setIcon(qta.icon(icon_name, color=color))

        # Indicate boost with tooltip
        if self._volume > 100:
            self._mute_btn.setToolTip(f"Volume BOOST: {self._volume}% (M)")
        else:
            self._mute_btn.setToolTip(f"Toggle Mute (M)")

    def toggle_mute(self):
        if self._muted:
            self._muted = False
            self._slider.setValue(self._pre_mute_volume if self._pre_mute_volume > 0 else 80)
        else:
            self._pre_mute_volume = self._volume
            self._muted = True
            self._slider.setValue(0)
        self.mute_toggled.emit(self._muted)

    def set_volume(self, volume: int):
        """Set volume programmatically (0-150)."""
        volume = clamp(volume, 0, 150)
        self._slider.setValue(volume)

    def get_volume(self) -> int:
        return self._volume

    def adjust_volume(self, delta: int):
        """Adjust volume by delta amount."""
        new_vol = clamp(self._volume + delta, 0, 150)
        self.set_volume(new_vol)

    def is_muted(self) -> bool:
        return self._muted

    def wheelEvent(self, event: QWheelEvent):
        delta = 5 if event.angleDelta().y() > 0 else -5
        self.adjust_volume(delta)
        event.accept()
