"""
Subtitle manager and style configuration.
Handles loading subtitle files into VLC and applying custom text styles.
"""
import os
import vlc
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QGroupBox, QComboBox, QColorDialog,
                             QSpinBox, QCheckBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFontDatabase
from .styles import get_subtitle_dialog_stylesheet
from .utils import find_subtitles_for_video


class SubtitleManager:
    """Manages subtitle files and styling for a VLC player instance."""
    
    def __init__(self, settings_manager):
        self.settings = settings_manager
        self.prefs = self.settings.load_subtitle_prefs()
        self.current_sub_path = None
        
    def auto_load_subtitle(self, player: vlc.MediaPlayer, video_path: str) -> bool:
        """Attempt to automatically find and load a matching subtitle file."""
        if not self.prefs.get('enabled', True):
            return False
            
        subs = find_subtitles_for_video(video_path)
        if subs:
            # Prefer SRT, then whatever is first
            best_sub = next((s for s in subs if s.endswith('.srt')), subs[0])
            return self.load_subtitle(player, best_sub)
        return False

    def load_subtitle(self, player: vlc.MediaPlayer, sub_path: str) -> bool:
        """Load a specific subtitle file into the player."""
        if not os.path.exists(sub_path):
            return False
            
        # VLC returns 1 on success, 0 on failure
        success = player.video_set_subtitle_file(sub_path)
        if success:
            self.current_sub_path = sub_path
            self.apply_styles(player)
            # Enable subtitle track if disabled
            if not self.prefs.get('enabled', True):
                player.video_set_spu(0) # Disable
            else:
                # Get track count, if > 0, set to the first track (or previously selected)
                # In VLC, track 0 is typically disabled, track 1 is first sub
                # We just let VLC handle track selection on load, but we ensure it's not explicitly disabled
                pass
            return True
        return False
        
    def apply_styles(self, player: vlc.MediaPlayer):
        """Apply current styling preferences to VLC."""
        # Unfortunately, python-vlc's libvlc API doesn't expose direct methods
        # to change subtitle font/color dynamically during playback for all formats.
        # It relies on freetype module settings passed during Instance creation.
        # However, we can update the config strings for the next playback or 
        # recreate the instance if really needed.
        
        # We can store the styles and provide args for the vlc.Instance creation
        pass
        
    def get_vlc_args(self) -> list:
        """Get VLC arguments for subtitle styling based on current prefs."""
        # Note: These apply to libvlc freetype text renderer
        color_hex = self.prefs.get('font_color', '#FFFFFF').lstrip('#')
        try:
            # Convert hex to decimal for VLC
            color_dec = int(color_hex, 16)
        except ValueError:
            color_dec = 16777215 # White
            
        args = [
            f'--freetype-font={self.prefs.get("font_family", "Arial")}',
            f'--freetype-fontsize={self.prefs.get("font_size", 24)}',
            f'--freetype-color={color_dec}',
            f'--freetype-background-opacity={self.prefs.get("bg_opacity", 128)}'
        ]
        return args


class SubtitleStyleDialog(QDialog):
    """Dialog for customizing subtitle appearance."""
    
    prefs_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None, current_prefs=None):
        super().__init__(parent)
        self.setWindowTitle("Subtitle Settings")
        self.setFixedSize(300, 350)
        self.setStyleSheet(get_subtitle_dialog_stylesheet())
        
        self.prefs = current_prefs or {
            'font_family': 'Arial',
            'font_size': 24,
            'font_color': '#FFFFFF',
            'bg_opacity': 128,
            'enabled': True
        }
        
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Enabled checkbox
        self.enabled_cb = QCheckBox("Enable Subtitles")
        self.enabled_cb.setChecked(self.prefs['enabled'])
        layout.addWidget(self.enabled_cb)
        
        group = QGroupBox("Appearance", self)
        group_layout = QVBoxLayout(group)
        
        # Font family
        font_layout = QHBoxLayout()
        font_layout.addWidget(QLabel("Font:"))
        self.font_combo = QComboBox()
        for font in QFontDatabase.families():
            self.font_combo.addItem(font)
        
        # Set current font
        idx = self.font_combo.findText(self.prefs['font_family'])
        if idx >= 0:
            self.font_combo.setCurrentIndex(idx)
        font_layout.addWidget(self.font_combo)
        group_layout.addLayout(font_layout)
        
        # Font size
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Size:"))
        self.size_spin = QSpinBox()
        self.size_spin.setRange(8, 72)
        self.size_spin.setValue(self.prefs['font_size'])
        size_layout.addWidget(self.size_spin)
        group_layout.addLayout(size_layout)
        
        # Font color
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Color:"))
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(60, 24)
        self._set_btn_color(self.prefs['font_color'])
        self.color_btn.clicked.connect(self._choose_color)
        color_layout.addWidget(self.color_btn)
        group_layout.addLayout(color_layout)
        
        # Background opacity
        bg_layout = QHBoxLayout()
        bg_layout.addWidget(QLabel("BG Opacity:"))
        self.bg_spin = QSpinBox()
        self.bg_spin.setRange(0, 255)
        self.bg_spin.setValue(self.prefs['bg_opacity'])
        self.bg_spin.setToolTip("0 = Transparent, 255 = Opaque")
        bg_layout.addWidget(self.bg_spin)
        group_layout.addLayout(bg_layout)
        
        layout.addWidget(group)
        
        # Warning label about restart
        warn_lbl = QLabel("Note: Styling changes require\nreloading the video to take effect.")
        warn_lbl.setStyleSheet("color: #8888a0; font-size: 11px;")
        layout.addWidget(warn_lbl)
        
        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save_and_close)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
    def _set_btn_color(self, hex_color: str):
        self.current_color = hex_color
        self.color_btn.setStyleSheet(f"background-color: {hex_color}; border: 1px solid #555;")
        
    def _choose_color(self):
        color = QColorDialog.getColor(QColor(self.current_color), self, "Select Subtitle Color")
        if color.isValid():
            self._set_btn_color(color.name())
            
    def _save_and_close(self):
        self.prefs = {
            'font_family': self.font_combo.currentText(),
            'font_size': self.size_spin.value(),
            'font_color': self.current_color,
            'bg_opacity': self.bg_spin.value(),
            'enabled': self.enabled_cb.isChecked()
        }
        self.prefs_changed.emit(self.prefs)
        self.accept()
