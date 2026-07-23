"""
Dark glassmorphism theme for the video player.
Complete QSS stylesheet with styled widgets, animations, and modern aesthetics.
"""

COLORS = {
    'bg_primary': '#0a0a0f',
    'bg_secondary': '#12121a',
    'bg_tertiary': '#1a1a2e',
    'bg_glass': 'rgba(18, 18, 30, 0.85)',
    'bg_glass_light': 'rgba(30, 30, 50, 0.75)',
    'bg_hover': 'rgba(255, 255, 255, 0.08)',
    'bg_pressed': 'rgba(255, 255, 255, 0.12)',
    'accent': '#6c5ce7',
    'accent_light': '#a29bfe',
    'accent_dark': '#4834d4',
    'accent_glow': 'rgba(108, 92, 231, 0.3)',
    'text_primary': '#e8e8f0',
    'text_secondary': '#8888a0',
    'text_muted': '#555570',
    'border': 'rgba(255, 255, 255, 0.06)',
    'border_light': 'rgba(255, 255, 255, 0.1)',
    'danger': '#ff6b6b',
    'success': '#51cf66',
    'warning': '#ffd43b',
    'seek_bg': 'rgba(255, 255, 255, 0.12)',
    'seek_buffered': 'rgba(108, 92, 231, 0.3)',
    'seek_progress': '#6c5ce7',
    'volume_bg': 'rgba(255, 255, 255, 0.12)',
    'volume_fill': '#51cf66',
}


def get_main_stylesheet() -> str:
    """Return the complete application stylesheet."""
    return f"""
    /* ===== Global ===== */
    QMainWindow {{
        background-color: {COLORS['bg_primary']};
        color: {COLORS['text_primary']};
        border: none;
        margin: 0px;
        padding: 0px;
    }}

    QWidget {{
        color: {COLORS['text_primary']};
        font-family: 'Segoe UI', 'Inter', sans-serif;
        font-size: 13px;
    }}

    /* ===== Menu Bar ===== */
    QMenuBar {{
        background-color: {COLORS['bg_secondary']};
        color: {COLORS['text_primary']};
        border-bottom: 1px solid {COLORS['border']};
        padding: 2px 0px;
        font-size: 12px;
    }}

    QMenuBar::item {{
        padding: 6px 12px;
        border-radius: 4px;
        margin: 2px 1px;
    }}

    QMenuBar::item:selected {{
        background-color: {COLORS['bg_hover']};
    }}

    QMenuBar::item:pressed {{
        background-color: {COLORS['accent']};
    }}

    /* ===== Menus ===== */
    QMenu {{
        background-color: {COLORS['bg_secondary']};
        border: 1px solid {COLORS['border_light']};
        border-radius: 8px;
        padding: 6px;
    }}

    QMenu::item {{
        padding: 8px 32px 8px 16px;
        border-radius: 4px;
        margin: 1px 4px;
    }}

    QMenu::item:selected {{
        background-color: {COLORS['accent']};
        color: white;
    }}

    QMenu::item:disabled {{
        color: {COLORS['text_muted']};
    }}

    QMenu::separator {{
        height: 1px;
        background-color: {COLORS['border']};
        margin: 4px 12px;
    }}

    QMenu::indicator {{
        width: 16px;
        height: 16px;
        margin-left: 6px;
    }}

    /* ===== Scroll Bars ===== */
    QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        margin: 0;
    }}

    QScrollBar::handle:vertical {{
        background: {COLORS['text_muted']};
        border-radius: 4px;
        min-height: 30px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: {COLORS['text_secondary']};
    }}

    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0;
    }}

    QScrollBar::add-page:vertical,
    QScrollBar::sub-page:vertical {{
        background: transparent;
    }}

    QScrollBar:horizontal {{
        background: transparent;
        height: 8px;
        margin: 0;
    }}

    QScrollBar::handle:horizontal {{
        background: {COLORS['text_muted']};
        border-radius: 4px;
        min-width: 30px;
    }}

    QScrollBar::handle:horizontal:hover {{
        background: {COLORS['text_secondary']};
    }}

    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {{
        width: 0;
    }}

    /* ===== Tooltips ===== */
    QToolTip {{
        background-color: {COLORS['bg_tertiary']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border_light']};
        border-radius: 6px;
        padding: 6px 10px;
        font-size: 12px;
    }}

    /* ===== Push Buttons ===== */
    QPushButton {{
        background-color: {COLORS['bg_tertiary']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: 500;
    }}

    QPushButton:hover {{
        background-color: {COLORS['bg_hover']};
        border-color: {COLORS['border_light']};
    }}

    QPushButton:pressed {{
        background-color: {COLORS['bg_pressed']};
    }}

    QPushButton:disabled {{
        color: {COLORS['text_muted']};
        background-color: {COLORS['bg_secondary']};
    }}

    /* ===== Combo Box ===== */
    QComboBox {{
        background-color: {COLORS['bg_tertiary']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        border-radius: 6px;
        padding: 6px 12px;
        min-width: 70px;
    }}

    QComboBox:hover {{
        border-color: {COLORS['border_light']};
    }}

    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}

    QComboBox QAbstractItemView {{
        background-color: {COLORS['bg_secondary']};
        border: 1px solid {COLORS['border_light']};
        border-radius: 6px;
        selection-background-color: {COLORS['accent']};
        padding: 4px;
    }}

    /* ===== Sliders ===== */
    QSlider::groove:horizontal {{
        height: 4px;
        background: {COLORS['seek_bg']};
        border-radius: 2px;
    }}

    QSlider::handle:horizontal {{
        background: {COLORS['accent']};
        width: 14px;
        height: 14px;
        margin: -5px 0;
        border-radius: 7px;
    }}

    QSlider::handle:horizontal:hover {{
        background: {COLORS['accent_light']};
        width: 16px;
        height: 16px;
        margin: -6px 0;
        border-radius: 8px;
    }}

    QSlider::sub-page:horizontal {{
        background: {COLORS['accent']};
        border-radius: 2px;
    }}

    QSlider::groove:vertical {{
        width: 4px;
        background: {COLORS['seek_bg']};
        border-radius: 2px;
    }}

    QSlider::handle:vertical {{
        background: {COLORS['accent']};
        width: 14px;
        height: 14px;
        margin: 0 -5px;
        border-radius: 7px;
    }}

    QSlider::sub-page:vertical {{
        background: {COLORS['seek_bg']};
        border-radius: 2px;
    }}

    QSlider::add-page:vertical {{
        background: {COLORS['accent']};
        border-radius: 2px;
    }}

    /* ===== Spin Box ===== */
    QSpinBox, QDoubleSpinBox {{
        background-color: {COLORS['bg_tertiary']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        border-radius: 6px;
        padding: 4px 8px;
    }}

    /* ===== Labels ===== */
    QLabel {{
        color: {COLORS['text_primary']};
    }}

    /* ===== Group Box ===== */
    QGroupBox {{
        border: 1px solid {COLORS['border']};
        border-radius: 8px;
        margin-top: 8px;
        padding-top: 16px;
        font-weight: 600;
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        padding: 0 8px;
        color: {COLORS['accent_light']};
    }}

    /* ===== Tab Widget ===== */
    QTabWidget::pane {{
        border: 1px solid {COLORS['border']};
        border-radius: 8px;
        background-color: {COLORS['bg_secondary']};
    }}

    QTabBar::tab {{
        background-color: {COLORS['bg_tertiary']};
        color: {COLORS['text_secondary']};
        padding: 8px 16px;
        margin-right: 2px;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
    }}

    QTabBar::tab:selected {{
        background-color: {COLORS['bg_secondary']};
        color: {COLORS['text_primary']};
        border-bottom: 2px solid {COLORS['accent']};
    }}

    QTabBar::tab:hover:!selected {{
        background-color: {COLORS['bg_hover']};
    }}

    /* ===== Dialog ===== */
    QDialog {{
        background-color: {COLORS['bg_primary']};
    }}

    /* ===== File Dialog / List Views ===== */
    QListWidget, QListView, QTreeView, QTableView {{
        background-color: {COLORS['bg_secondary']};
        border: 1px solid {COLORS['border']};
        border-radius: 6px;
        alternate-background-color: {COLORS['bg_tertiary']};
        outline: none;
    }}

    QListWidget::item, QListView::item {{
        padding: 6px 8px;
        border-radius: 4px;
        margin: 1px 4px;
    }}

    QListWidget::item:selected, QListView::item:selected {{
        background-color: {COLORS['accent']};
        color: white;
    }}

    QListWidget::item:hover:!selected, QListView::item:hover:!selected {{
        background-color: {COLORS['bg_hover']};
    }}

    /* ===== Status Bar ===== */
    QStatusBar {{
        background-color: {COLORS['bg_secondary']};
        color: {COLORS['text_secondary']};
        border-top: 1px solid {COLORS['border']};
        font-size: 11px;
    }}

    /* ===== Line Edit ===== */
    QLineEdit {{
        background-color: {COLORS['bg_tertiary']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        border-radius: 6px;
        padding: 6px 12px;
    }}

    QLineEdit:focus {{
        border-color: {COLORS['accent']};
    }}

    /* ===== Check Box ===== */
    QCheckBox {{
        spacing: 8px;
    }}

    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border-radius: 4px;
        border: 1px solid {COLORS['border_light']};
        background-color: {COLORS['bg_tertiary']};
    }}

    QCheckBox::indicator:checked {{
        background-color: {COLORS['accent']};
        border-color: {COLORS['accent']};
    }}
    """


def get_control_bar_stylesheet() -> str:
    """Return stylesheet for the overlay control bar."""
    return f"""
    QWidget#controlBar {{
        background-color: {COLORS['bg_glass']};
        border-top: 1px solid {COLORS['border']};
    }}

    QPushButton#controlButton {{
        background-color: transparent;
        border: none;
        color: {COLORS['text_primary']};
        border-radius: 8px;
    }}

    QPushButton#controlButton:hover {{
        background-color: {COLORS['bg_hover']};
    }}

    QPushButton#controlButton:pressed {{
        background-color: {COLORS['bg_pressed']};
    }}

    QPushButton#playButton {{
        background-color: {COLORS['accent']};
        border: none;
        color: white;
        border-radius: 20px;
    }}

    QPushButton#playButton:hover {{
        background-color: {COLORS['accent_light']};
    }}

    QPushButton#playButton:pressed {{
        background-color: {COLORS['accent_dark']};
    }}

    QLabel#timeLabel {{
        color: {COLORS['text_secondary']};
        font-size: 12px;
        font-family: 'Consolas', 'Courier New', monospace;
        padding: 0 4px;
    }}

    QLabel#titleLabel {{
        color: {COLORS['text_primary']};
        font-size: 12px;
        font-weight: 500;
        padding: 4px 8px;
    }}

    QPushButton#enhanceButton {{
        background-color: transparent;
        border: none;
        border-radius: 8px;
        color: {COLORS['text_primary']};
    }}

    QPushButton#enhanceButton:hover {{
        background-color: {COLORS['bg_hover']};
    }}

    QPushButton#enhanceButton[active="true"] {{
        background-color: rgba(108, 92, 231, 0.25);
        border: 1px solid {COLORS['accent_glow']};
    }}

    QPushButton#enhanceButton[active="true"]:hover {{
        background-color: rgba(108, 92, 231, 0.35);
    }}
    """


def get_playlist_stylesheet() -> str:
    """Return stylesheet for the playlist panel."""
    return f"""
    QWidget#playlistPanel {{
        background-color: {COLORS['bg_secondary']};
        border-left: 1px solid {COLORS['border']};
    }}

    QLabel#playlistHeader {{
        color: {COLORS['text_primary']};
        font-size: 14px;
        font-weight: 600;
        padding: 12px 16px 8px 16px;
    }}

    QPushButton#playlistButton {{
        background-color: transparent;
        border: none;
        color: {COLORS['text_secondary']};
        padding: 6px;
        border-radius: 4px;
    }}

    QPushButton#playlistButton:hover {{
        background-color: {COLORS['bg_hover']};
        color: {COLORS['text_primary']};
    }}
    """


def get_osd_stylesheet() -> str:
    """Return stylesheet for on-screen display."""
    return f"""
    QLabel#osdLabel {{
        background-color: rgba(0, 0, 0, 0.75);
        color: white;
        font-size: 18px;
        font-weight: 600;
        padding: 12px 24px;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }}
    """


def get_seek_bar_stylesheet() -> str:
    """Return stylesheet for the custom seek bar."""
    return f"""
    QWidget#seekBarContainer {{
        background: transparent;
    }}
    """


def get_filter_dialog_stylesheet() -> str:
    """Return stylesheet for the video filters dialog."""
    return f"""
    QDialog {{
        background-color: {COLORS['bg_primary']};
    }}

    QSlider::groove:horizontal {{
        height: 4px;
        background: {COLORS['seek_bg']};
        border-radius: 2px;
    }}

    QSlider::handle:horizontal {{
        background: {COLORS['accent']};
        width: 14px;
        height: 14px;
        margin: -5px 0;
        border-radius: 7px;
    }}

    QSlider::sub-page:horizontal {{
        background: {COLORS['accent']};
        border-radius: 2px;
    }}

    QLabel {{
        font-size: 12px;
    }}

    QLabel#filterValue {{
        color: {COLORS['accent_light']};
        font-family: 'Consolas', monospace;
        min-width: 40px;
    }}

    QGroupBox#enhanceGroup {{
        border: 1px solid {COLORS['accent_glow']};
        background-color: rgba(108, 92, 231, 0.05);
    }}

    QLabel#enhanceDesc {{
        color: {COLORS['text_secondary']};
        font-size: 11px;
        font-style: italic;
        padding: 4px;
    }}

    QCheckBox {{
        color: {COLORS['accent_light']};
        font-weight: 600;
    }}
    """


def get_subtitle_dialog_stylesheet() -> str:
    """Return stylesheet for subtitle settings dialog."""
    return get_filter_dialog_stylesheet()
