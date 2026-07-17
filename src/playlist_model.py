"""
Playlist data model and serialization.
Handles storing, ordering, and saving/loading playlist items to JSON.
"""
import os
import json
import uuid
from typing import List, Dict, Optional
from PyQt6.QtCore import QAbstractListModel, Qt, QModelIndex, pyqtSignal
from .utils import is_media_file, sanitize_filename


class PlaylistItem:
    def __init__(self, filepath: str, title: str = None):
        self.id = str(uuid.uuid4())
        self.filepath = filepath
        self.title = title or os.path.basename(filepath)
        self.duration_ms = 0
        self.thumbnail = None  # Could hold a QPixmap later

    def to_dict(self) -> dict:
        return {
            'filepath': self.filepath,
            'title': self.title,
            'duration_ms': self.duration_ms
        }

    @classmethod
    def from_dict(cls, data: dict):
        item = cls(data.get('filepath', ''), data.get('title'))
        item.duration_ms = data.get('duration_ms', 0)
        return item


class PlaylistModel(QAbstractListModel):
    """Data model for the playlist view."""

    items_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.items: List[PlaylistItem] = []

    # ── Qt Model Interface ────────────────────────────────────────────
    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self.items)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self.items)):
            return None

        item = self.items[index.row()]
        
        if role == Qt.ItemDataRole.DisplayRole:
            return item.title
        elif role == Qt.ItemDataRole.UserRole:
            return item
        elif role == Qt.ItemDataRole.ToolTipRole:
            return item.filepath

        return None

    def supportedDropActions(self):
        return Qt.DropAction.MoveAction | Qt.DropAction.CopyAction

    # ── Item Management ───────────────────────────────────────────────
    def add_item(self, filepath: str) -> bool:
        if not is_media_file(filepath) or not os.path.exists(filepath):
            return False
            
        # Avoid exact duplicates
        if any(i.filepath == filepath for i in self.items):
            return False

        self.beginInsertRows(QModelIndex(), len(self.items), len(self.items))
        self.items.append(PlaylistItem(filepath))
        self.endInsertRows()
        self.items_changed.emit()
        return True

    def add_items(self, filepaths: List[str]):
        valid_paths = [p for p in filepaths if is_media_file(p) and os.path.exists(p)]
        # Filter duplicates
        existing = {i.filepath for i in self.items}
        valid_paths = [p for p in valid_paths if p not in existing]
        
        if not valid_paths:
            return

        self.beginInsertRows(QModelIndex(), len(self.items), len(self.items) + len(valid_paths) - 1)
        for p in valid_paths:
            self.items.append(PlaylistItem(p))
        self.endInsertRows()
        self.items_changed.emit()

    def remove_item(self, index: int):
        if 0 <= index < len(self.items):
            self.beginRemoveRows(QModelIndex(), index, index)
            self.items.pop(index)
            self.endRemoveRows()
            self.items_changed.emit()

    def clear(self):
        if self.items:
            self.beginResetModel()
            self.items.clear()
            self.endResetModel()
            self.items_changed.emit()

    def get_item(self, index: int) -> Optional[PlaylistItem]:
        if 0 <= index < len(self.items):
            return self.items[index]
        return None

    def move_item(self, from_idx: int, to_idx: int):
        if from_idx == to_idx or not (0 <= from_idx < len(self.items)) or not (0 <= to_idx < len(self.items)):
            return
            
        # For Qt's drag and drop, beginMoveRows requires specific index handling
        dest_idx = to_idx + 1 if to_idx > from_idx else to_idx
        self.beginMoveRows(QModelIndex(), from_idx, from_idx, QModelIndex(), dest_idx)
        item = self.items.pop(from_idx)
        self.items.insert(to_idx, item)
        self.endMoveRows()
        self.items_changed.emit()

    # ── Serialization ─────────────────────────────────────────────────
    def save_to_file(self, filepath: str) -> bool:
        try:
            data = {
                'version': 1,
                'items': [item.to_dict() for item in self.items]
            }
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Failed to save playlist: {e}")
            return False

    def load_from_file(self, filepath: str) -> bool:
        if not os.path.exists(filepath):
            return False
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if 'items' not in data:
                return False
                
            self.clear()
            
            self.beginInsertRows(QModelIndex(), 0, len(data['items']) - 1)
            for item_data in data['items']:
                self.items.append(PlaylistItem.from_dict(item_data))
            self.endInsertRows()
            
            self.items_changed.emit()
            return True
        except Exception as e:
            print(f"Failed to load playlist: {e}")
            return False
