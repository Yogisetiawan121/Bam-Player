"""
System tray integration.
Handles minimizing to tray, background playback, and tray menu controls.
"""
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import pyqtSignal


import qtawesome as qta


class SystemTrayIntegration(QSystemTrayIcon):
    """System tray icon and context menu."""
    
    restore_requested = pyqtSignal()
    play_pause_requested = pyqtSignal()
    next_requested = pyqtSignal()
    prev_requested = pyqtSignal()
    quit_requested = pyqtSignal()
    
    def __init__(self, icon: QIcon, parent=None):
        super().__init__(icon, parent)
        self.setToolTip("Bam Player")
        
        self.menu = QMenu()
        
        self.action_restore = QAction(qta.icon('mdi6.window-restore', color='#e8e8f0'), "Restore", self.menu)
        self.action_restore.triggered.connect(self.restore_requested.emit)
        self.menu.addAction(self.action_restore)
        
        self.menu.addSeparator()
        
        self.action_play = QAction(qta.icon('mdi6.play-pause', color='#e8e8f0'), "Play/Pause", self.menu)
        self.action_play.triggered.connect(self.play_pause_requested.emit)
        self.menu.addAction(self.action_play)
        
        self.action_prev = QAction(qta.icon('mdi6.skip-previous', color='#e8e8f0'), "Previous", self.menu)
        self.action_prev.triggered.connect(self.prev_requested.emit)
        self.menu.addAction(self.action_prev)
        
        self.action_next = QAction(qta.icon('mdi6.skip-next', color='#e8e8f0'), "Next", self.menu)
        self.action_next.triggered.connect(self.next_requested.emit)
        self.menu.addAction(self.action_next)
        
        self.menu.addSeparator()
        
        self.action_quit = QAction(qta.icon('mdi6.power', color='#ff6b6b'), "Quit", self.menu)
        self.action_quit.triggered.connect(self.quit_requested.emit)
        self.menu.addAction(self.action_quit)
        
        self.setContextMenu(self.menu)
        self.activated.connect(self._on_activated)
        
    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.restore_requested.emit()
            
    def update_play_state(self, playing: bool):
        # We could update the icon here to reflect playing state if desired
        pass
