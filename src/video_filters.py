"""
Video filters dialog and VLC integration.
Adjust brightness, contrast, saturation, hue, and gamma in real-time.
Includes a real-time Enhancement section with sharpness simulation.
"""
import vlc
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QSlider, QPushButton, QGroupBox, QCheckBox)
from PyQt6.QtCore import Qt, pyqtSignal
from .styles import get_filter_dialog_stylesheet


class VideoFiltersDialog(QDialog):
    """Dialog for adjusting video color filters and enhancement."""

    filters_changed = pyqtSignal(dict)
    enhancement_changed = pyqtSignal(bool, float)  # enabled, sharpness
    
    def __init__(self, parent=None, current_filters=None, 
                 enhancement_enabled=False, enhancement_sharpness=0.0):
        super().__init__(parent)
        self.setWindowTitle("Video Filters & Enhancement")
        self.setFixedSize(380, 560)
        self.setStyleSheet(get_filter_dialog_stylesheet())
        
        self.current_filters = current_filters or {
            'brightness': 1.0,
            'contrast': 1.0,
            'saturation': 1.0,
            'hue': 0,
            'gamma': 1.0
        }
        self._enhancement_enabled = enhancement_enabled
        self._enhancement_sharpness = enhancement_sharpness
        
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # ── Basic Adjustments ──────────────────────────────────────────
        group = QGroupBox("Adjustments", self)
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(16)
        
        # Brightness (0.0 to 2.0, default 1.0)
        self.bright_slider, self.bright_val = self._create_slider(
            "Brightness", 0, 200, int(self.current_filters['brightness'] * 100), group_layout
        )
        
        # Contrast (0.0 to 2.0, default 1.0)
        self.contrast_slider, self.contrast_val = self._create_slider(
            "Contrast", 0, 200, int(self.current_filters['contrast'] * 100), group_layout
        )
        
        # Saturation (0.0 to 3.0, default 1.0)
        self.sat_slider, self.sat_val = self._create_slider(
            "Saturation", 0, 300, int(self.current_filters['saturation'] * 100), group_layout
        )
        
        # Hue (-180 to 180, default 0)
        self.hue_slider, self.hue_val = self._create_slider(
            "Hue", -180, 180, self.current_filters['hue'], group_layout, is_hue=True
        )
        
        # Gamma (0.01 to 10.0, default 1.0) - scale 1-1000
        self.gamma_slider, self.gamma_val = self._create_slider(
            "Gamma", 1, 1000, int(self.current_filters['gamma'] * 100), group_layout
        )
        
        layout.addWidget(group)
        
        # ── Real-time Enhancement ──────────────────────────────────────
        enhance_group = QGroupBox("Real-time Enhancement", self)
        enhance_group.setObjectName("enhanceGroup")
        enhance_layout = QVBoxLayout(enhance_group)
        enhance_layout.setSpacing(12)
        
        # Master toggle
        toggle_row = QHBoxLayout()
        self.enhance_check = QCheckBox("Enable Enhancement")
        self.enhance_check.setChecked(self._enhancement_enabled)
        self.enhance_check.toggled.connect(self._on_enhancement_toggled)
        toggle_row.addWidget(self.enhance_check)
        toggle_row.addStretch()
        enhance_layout.addLayout(toggle_row)
        
        # Sharpness slider (built manually so it doesn't trigger _on_filter_changed)
        sharp_row = QHBoxLayout()
        sharp_label = QLabel("Sharpness")
        sharp_label.setFixedWidth(80)
        self.enhance_slider = QSlider(Qt.Orientation.Horizontal)
        self.enhance_slider.setRange(0, 100)
        self.enhance_slider.setValue(int(self._enhancement_sharpness))
        self.enhance_slider.setEnabled(self._enhancement_enabled)
        self.enhance_val = QLabel()
        self.enhance_val.setObjectName("filterValue")
        self.enhance_val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.enhance_val.setText(f"{int(self._enhancement_sharpness)}%")
        
        def _on_enhance_slider_changed(val):
            self.enhance_val.setText(f"{val}%")
            self._emit_enhancement()
        
        self.enhance_slider.valueChanged.connect(_on_enhance_slider_changed)
        
        sharp_row.addWidget(sharp_label)
        sharp_row.addWidget(self.enhance_slider)
        sharp_row.addWidget(self.enhance_val)
        enhance_layout.addLayout(sharp_row)
        
        # Description label
        desc = QLabel(
            "Enhances visual clarity by intelligently boosting \n"
            "contrast, saturation, and gamma in real-time.\n"
            "Works alongside your manual adjustments above."
        )
        desc.setObjectName("enhanceDesc")
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        enhance_layout.addWidget(desc)
        
        layout.addWidget(enhance_group)
        
        # ── Buttons ────────────────────────────────────────────────────
        btn_layout = QHBoxLayout()
        reset_btn = QPushButton("Reset Defaults")
        reset_btn.clicked.connect(self._reset_filters)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(reset_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)

    def _create_slider(self, name, min_val, max_val, current, layout, 
                       is_hue=False):
        row = QHBoxLayout()
        
        label = QLabel(name)
        label.setFixedWidth(80)
        
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(current)
        
        val_label = QLabel()
        val_label.setObjectName("filterValue")
        val_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        def update_val(val):
            if is_hue:
                val_label.setText(f"{val}°")
            else:
                val_label.setText(f"{val/100.0:.2f}")
            if hasattr(self, 'gamma_slider'):
                self._on_filter_changed()
            
        slider.valueChanged.connect(update_val)
        # Initialize text without triggering filter updates yet
        if is_hue:
            val_label.setText(f"{current}°")
        else:
            val_label.setText(f"{current/100.0:.2f}")
        
        row.addWidget(label)
        row.addWidget(slider)
        row.addWidget(val_label)
        
        layout.addLayout(row)
        return slider, val_label

    def _on_enhancement_toggled(self, enabled: bool):
        self.enhance_slider.setEnabled(enabled)
        self._emit_enhancement()

    def _emit_enhancement(self):
        enabled = self.enhance_check.isChecked()
        sharpness = self.enhance_slider.value()
        self._enhancement_enabled = enabled
        self._enhancement_sharpness = sharpness
        self.enhancement_changed.emit(enabled, sharpness)

    def _reset_filters(self):
        self.bright_slider.setValue(100)
        self.contrast_slider.setValue(100)
        self.sat_slider.setValue(100)
        self.hue_slider.setValue(0)
        self.gamma_slider.setValue(100)
        self.enhance_check.setChecked(False)
        self.enhance_slider.setValue(50)

    def _on_filter_changed(self):
        self.current_filters = {
            'brightness': self.bright_slider.value() / 100.0,
            'contrast': self.contrast_slider.value() / 100.0,
            'saturation': self.sat_slider.value() / 100.0,
            'hue': self.hue_slider.value(),
            'gamma': self.gamma_slider.value() / 100.0
        }
        self.filters_changed.emit(self.current_filters)
        # Also emit enhancement since sharpness slider may have changed
        self._emit_enhancement()


def apply_filters_to_player(player: vlc.MediaPlayer, filters: dict):
    """Apply filter dictionary to VLC player instance."""
    # Enable adjust filter if any filter is non-default
    defaults = {
        'brightness': 1.0, 'contrast': 1.0, 
        'saturation': 1.0, 'hue': 0, 'gamma': 1.0
    }
    
    needs_adjust = any(abs(filters[k] - defaults[k]) > 0.01 for k in defaults)
    
    # 1 is adjust, 0 is disable
    player.video_set_adjust_int(vlc.VideoAdjustOption.Enable, 1 if needs_adjust else 0)
    
    if needs_adjust:
        player.video_set_adjust_float(vlc.VideoAdjustOption.Brightness, filters['brightness'])
        player.video_set_adjust_float(vlc.VideoAdjustOption.Contrast, filters['contrast'])
        player.video_set_adjust_float(vlc.VideoAdjustOption.Saturation, filters['saturation'])
        player.video_set_adjust_int(vlc.VideoAdjustOption.Hue, filters['hue'])
        player.video_set_adjust_float(vlc.VideoAdjustOption.Gamma, filters['gamma'])
