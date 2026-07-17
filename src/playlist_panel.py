"""
Playlist UI panel with list view and control buttons.
"""
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QListView, QMenu, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, QModelIndex, QUrl
from PyQt6.QtGui import QAction, QDropEvent, QDragEnterEvent
from typing import Optional
import qtawesome as qta
from .playlist_model import PlaylistModel
from .styles import get_playlist_stylesheet
from .utils import get_video_files_from_dir


class PlaylistPanel(QWidget):
    """Sidebar panel for playlist management."""
    
    item_activated = pyqtSignal(str)  # filepath
    
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setObjectName("playlistPanel")
        self.setStyleSheet(get_playlist_stylesheet())
        self.setMinimumWidth(250)
        self.setMaximumWidth(400)
        
        self.model = PlaylistModel(self)
        self._setup_ui()
        
        # Load last playlist if exists
        last_pl = self.settings.load_last_playlist()
        if last_pl and os.path.exists(last_pl):
            self.model.load_from_file(last_pl)
            
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 8, 0)
        
        title = QLabel("Playlist")
        title.setObjectName("playlistHeader")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Toolbar buttons
        self.btn_add = QPushButton()
        self.btn_add.setIcon(qta.icon('mdi6.plus', color='#8888a0'))
        self.btn_add.setObjectName("playlistButton")
        self.btn_add.setToolTip("Add Files")
        self.btn_add.clicked.connect(self._add_files)
        header_layout.addWidget(self.btn_add)
        
        self.btn_save = QPushButton()
        self.btn_save.setIcon(qta.icon('mdi6.content-save', color='#8888a0'))
        self.btn_save.setObjectName("playlistButton")
        self.btn_save.setToolTip("Save Playlist")
        self.btn_save.clicked.connect(self._save_playlist)
        header_layout.addWidget(self.btn_save)
        
        self.btn_clear = QPushButton()
        self.btn_clear.setIcon(qta.icon('mdi6.trash-can-outline', color='#8888a0'))
        self.btn_clear.setObjectName("playlistButton")
        self.btn_clear.setToolTip("Clear Playlist")
        self.btn_clear.clicked.connect(self.model.clear)
        header_layout.addWidget(self.btn_clear)
        
        layout.addLayout(header_layout)
        
        # List View
        self.list_view = QListView()
        self.list_view.setModel(self.model)
        self.list_view.setSelectionMode(QListView.SelectionMode.ExtendedSelection)
        self.list_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_view.setAcceptDrops(True)
        self.list_view.setDragEnabled(True)
        self.list_view.setDragDropMode(QListView.DragDropMode.InternalMove)
        self.list_view.setAlternatingRowColors(True)
        
        self.list_view.doubleClicked.connect(self._on_item_double_clicked)
        self.list_view.customContextMenuRequested.connect(self._show_context_menu)
        
        layout.addWidget(self.list_view)
        
    def _on_item_double_clicked(self, index: QModelIndex):
        item = self.model.get_item(index.row())
        if item:
            self.item_activated.emit(item.filepath)
            
    def _show_context_menu(self, pos):
        indexes = self.list_view.selectedIndexes()
        if not indexes:
            return
            
        menu = QMenu(self)
        
        action_play = QAction("Play", self)
        action_play.triggered.connect(lambda: self._on_item_double_clicked(indexes[0]))
        menu.addAction(action_play)
        
        action_remove = QAction("Remove", self)
        action_remove.triggered.connect(self._remove_selected)
        menu.addAction(action_remove)
        
        menu.addSeparator()
        
        action_reveal = QAction("Open File Location", self)
        action_reveal.triggered.connect(lambda: self._reveal_in_explorer(indexes[0]))
        menu.addAction(action_reveal)
        
        menu.exec(self.list_view.mapToGlobal(pos))
        
    def _remove_selected(self):
        # Remove in reverse order to keep indices valid
        indexes = sorted([idx.row() for idx in self.list_view.selectedIndexes()], reverse=True)
        for idx in indexes:
            self.model.remove_item(idx)
            
    def _reveal_in_explorer(self, index: QModelIndex):
        item = self.model.get_item(index.row())
        if item and os.path.exists(item.filepath):
            # Windows specific explorer selection
            if os.name == 'nt':
                os.system(f'explorer /select,"{item.filepath}"')
                
    def _add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Add Media Files", "",
            "Media Files (*.mp4 *.mkv *.avi *.mov *.wmv *.flv *.webm *.mp3 *.flac *.wav)"
        )
        if files:
            self.model.add_items(files)
            
    def _save_playlist(self):
        if self.model.rowCount() == 0:
            return
            
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Playlist", "", "Playlist Files (*.json)"
        )
        if path:
            if not path.endswith('.json'):
                path += '.json'
            if self.model.save_to_file(path):
                self.settings.save_last_playlist(path)
                QMessageBox.information(self, "Success", "Playlist saved successfully.")
            else:
                QMessageBox.critical(self, "Error", "Failed to save playlist.")

    def get_current_index(self) -> int:
        idx = self.list_view.currentIndex()
        return idx.row() if idx.isValid() else -1

    def set_current_index(self, row: int):
        if 0 <= row < self.model.rowCount():
            idx = self.model.index(row, 0)
            self.list_view.setCurrentIndex(idx)
            
    def get_next_item(self) -> Optional[str]:
        current = self.get_current_index()
        if current >= 0 and current < self.model.rowCount() - 1:
            item = self.model.get_item(current + 1)
            return item.filepath if item else None
        return None
        
    def get_prev_item(self) -> Optional[str]:
        current = self.get_current_index()
        if current > 0:
            item = self.model.get_item(current - 1)
            return item.filepath if item else None
        return None
