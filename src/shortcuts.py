"""
Keyboard shortcuts mapping for the main window.
"""
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtCore import Qt


def setup_shortcuts(window):
    """Setup global keyboard shortcuts for the main window."""
    
    # Play / Pause
    QShortcut(QKeySequence(Qt.Key.Key_Space), window).activated.connect(window.toggle_playback)
    
    # Fullscreen
    QShortcut(QKeySequence(Qt.Key.Key_F11), window).activated.connect(window.toggle_fullscreen)
    QShortcut(QKeySequence(Qt.Key.Key_Escape), window).activated.connect(
        lambda: window.set_fullscreen(False) if window.is_fullscreen else None
    )
    
    # Volume control
    QShortcut(QKeySequence(Qt.Key.Key_Up), window).activated.connect(
        lambda: window.control_bar.volume_ctrl.adjust_volume(5)
    )
    QShortcut(QKeySequence(Qt.Key.Key_Down), window).activated.connect(
        lambda: window.control_bar.volume_ctrl.adjust_volume(-5)
    )
    QShortcut(QKeySequence(Qt.Key.Key_M), window).activated.connect(
        window.control_bar.volume_ctrl.toggle_mute
    )
    
    # Seeking
    QShortcut(QKeySequence(Qt.Key.Key_Right), window).activated.connect(
        lambda: window.seek_relative(5000) # +5s
    )
    QShortcut(QKeySequence(Qt.Key.Key_Left), window).activated.connect(
        lambda: window.seek_relative(-5000) # -5s
    )
    QShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_Right), window).activated.connect(
        lambda: window.seek_relative(30000) # +30s
    )
    QShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_Left), window).activated.connect(
        lambda: window.seek_relative(-30000) # -30s
    )
    
    # Frame stepping (using , and .)
    QShortcut(QKeySequence(Qt.Key.Key_Comma), window).activated.connect(
        lambda: window.seek_relative(-1000/24) # Approximate 1 frame backward at 24fps
    )
    QShortcut(QKeySequence(Qt.Key.Key_Period), window).activated.connect(
        lambda: window.seek_relative(1000/24) # Approximate 1 frame forward
    )
    
    # Speed control
    QShortcut(QKeySequence(Qt.Key.Key_BracketRight), window).activated.connect(
        window.control_bar.speed_ctrl.increase_speed
    )
    QShortcut(QKeySequence(Qt.Key.Key_BracketLeft), window).activated.connect(
        window.control_bar.speed_ctrl.decrease_speed
    )
    QShortcut(QKeySequence(Qt.Key.Key_Backslash), window).activated.connect(
        window.control_bar.speed_ctrl.reset_speed
    )
    
    # Files
    QShortcut(QKeySequence("Ctrl+O"), window).activated.connect(window.open_file_dialog)
    QShortcut(QKeySequence("Ctrl+Shift+O"), window).activated.connect(window.open_folder_dialog)
    
    # Screenshot
    QShortcut(QKeySequence("Ctrl+S"), window).activated.connect(window.take_screenshot)
    
    # Always on Top
    QShortcut(QKeySequence("Ctrl+T"), window).activated.connect(window.toggle_always_on_top)
    
    # Playlist toggle
    QShortcut(QKeySequence("Ctrl+P"), window).activated.connect(window.toggle_playlist)
