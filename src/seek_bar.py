"""
Custom seek bar widget with hover preview, buffered progress, and click-to-seek.
Renders a modern translucent progress bar with time tooltip on hover.
"""
from PyQt6.QtWidgets import QWidget, QToolTip
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QPoint, QSize
from PyQt6.QtGui import QPainter, QColor, QLinearGradient, QBrush, QPen, QMouseEvent, QFont
from .styles import COLORS
from .utils import format_time


class SeekBar(QWidget):
    """Custom seek bar with hover preview and smooth interaction."""

    # Signals
    seek_requested = pyqtSignal(int)   # position in ms
    hover_position = pyqtSignal(int)   # position in ms (for preview)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(28)
        self.setMaximumHeight(28)

        self._duration = 0       # total duration in ms
        self._position = 0       # current position in ms
        self._buffered = 0       # buffered position in ms
        self._hover_pos = -1     # hover x position (-1 = not hovering)
        self._is_dragging = False
        self._chapters = []      # list of chapter positions in ms

        # Visual dimensions
        self._bar_height = 4
        self._bar_height_hover = 6
        self._handle_radius = 7
        self._current_bar_height = self._bar_height

        # Colors
        self._bg_color = QColor(255, 255, 255, 30)
        self._buffered_color = QColor(108, 92, 231, 77)
        self._progress_color = QColor(108, 92, 231)
        self._progress_glow = QColor(108, 92, 231, 100)
        self._handle_color = QColor(108, 92, 231)
        self._handle_hover_color = QColor(162, 155, 254)
        self._chapter_color = QColor(255, 255, 255, 120)
        self._hover_line_color = QColor(255, 255, 255, 60)

    # ── Properties ────────────────────────────────────────────────────
    def set_duration(self, duration_ms: int):
        self._duration = max(0, duration_ms)
        self.update()

    def set_position(self, position_ms: int):
        if not self._is_dragging:
            self._position = max(0, min(position_ms, self._duration))
            self.update()

    def set_buffered(self, buffered_ms: int):
        self._buffered = max(0, min(buffered_ms, self._duration))
        self.update()

    def set_chapters(self, chapters: list):
        """Set chapter markers (list of positions in ms)."""
        self._chapters = chapters
        self.update()

    def get_position(self) -> int:
        return self._position

    # ── Coordinate Helpers ────────────────────────────────────────────
    def _bar_rect(self) -> QRect:
        """Get the rectangle for the progress bar track."""
        margin = self._handle_radius + 2
        h = self._current_bar_height
        y = (self.height() - h) // 2
        return QRect(margin, y, self.width() - 2 * margin, h)

    def _pos_to_x(self, position_ms: int) -> float:
        """Convert time position to x coordinate."""
        bar = self._bar_rect()
        if self._duration <= 0:
            return float(bar.left())
        ratio = position_ms / self._duration
        return bar.left() + ratio * bar.width()

    def _x_to_pos(self, x: int) -> int:
        """Convert x coordinate to time position."""
        bar = self._bar_rect()
        if bar.width() <= 0:
            return 0
        ratio = (x - bar.left()) / bar.width()
        ratio = max(0.0, min(1.0, ratio))
        return int(ratio * self._duration)

    # ── Paint ─────────────────────────────────────────────────────────
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        bar = self._bar_rect()
        radius = self._current_bar_height / 2

        # Background track
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(self._bg_color))
        painter.drawRoundedRect(bar, radius, radius)

        # Buffered progress
        if self._buffered > 0 and self._duration > 0:
            buf_width = int(bar.width() * (self._buffered / self._duration))
            buf_rect = QRect(bar.left(), bar.top(), buf_width, bar.height())
            painter.setBrush(QBrush(self._buffered_color))
            painter.drawRoundedRect(buf_rect, radius, radius)

        # Progress fill with gradient
        if self._position > 0 and self._duration > 0:
            prog_width = int(bar.width() * (self._position / self._duration))
            prog_rect = QRect(bar.left(), bar.top(), prog_width, bar.height())

            gradient = QLinearGradient(bar.left(), 0, bar.right(), 0)
            gradient.setColorAt(0, QColor(108, 92, 231))
            gradient.setColorAt(1, QColor(162, 155, 254))
            painter.setBrush(QBrush(gradient))
            painter.drawRoundedRect(prog_rect, radius, radius)

        # Chapter markers
        for chapter_ms in self._chapters:
            cx = self._pos_to_x(chapter_ms)
            painter.setPen(QPen(self._chapter_color, 2))
            painter.drawLine(int(cx), bar.top() - 1, int(cx), bar.bottom() + 1)

        # Hover line
        if self._hover_pos >= 0 and not self._is_dragging:
            painter.setPen(QPen(self._hover_line_color, 1))
            hy = bar.top() - 3
            painter.drawLine(self._hover_pos, hy, self._hover_pos, bar.bottom() + 3)

        # Handle (thumb)
        if self._duration > 0:
            handle_x = self._pos_to_x(self._position)
            handle_y = self.height() / 2
            r = self._handle_radius

            is_hovered = self._hover_pos >= 0 or self._is_dragging

            if is_hovered:
                # Glow
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(self._progress_glow))
                painter.drawEllipse(
                    int(handle_x - r - 3), int(handle_y - r - 3),
                    int((r + 3) * 2), int((r + 3) * 2)
                )
                # Handle
                painter.setBrush(QBrush(self._handle_hover_color))
                painter.drawEllipse(
                    int(handle_x - r), int(handle_y - r),
                    r * 2, r * 2
                )
            else:
                # Smaller handle when not hovered
                sr = r - 2
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(self._handle_color))
                painter.drawEllipse(
                    int(handle_x - sr), int(handle_y - sr),
                    sr * 2, sr * 2
                )

        painter.end()

    # ── Mouse Events ──────────────────────────────────────────────────
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self._duration > 0:
            self._is_dragging = True
            pos = self._x_to_pos(int(event.position().x()))
            self._position = pos
            self.update()

    def mouseMoveEvent(self, event: QMouseEvent):
        x = int(event.position().x())
        bar = self._bar_rect()

        if self._is_dragging and self._duration > 0:
            pos = self._x_to_pos(x)
            self._position = pos
            self.update()
        elif bar.left() <= x <= bar.right():
            self._hover_pos = x
            self._current_bar_height = self._bar_height_hover

            # Show time tooltip
            hover_ms = self._x_to_pos(x)
            time_str = format_time(hover_ms)
            QToolTip.showText(
                self.mapToGlobal(QPoint(x, -30)),
                time_str, self
            )
            self.hover_position.emit(hover_ms)
            self.update()
        else:
            self._hover_pos = -1
            self._current_bar_height = self._bar_height
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self._is_dragging:
            self._is_dragging = False
            pos = self._x_to_pos(int(event.position().x()))
            self._position = pos
            self.seek_requested.emit(pos)
            self.update()

    def leaveEvent(self, event):
        self._hover_pos = -1
        self._current_bar_height = self._bar_height
        self.update()
        super().leaveEvent(event)

    def sizeHint(self) -> QSize:
        return QSize(200, 28)
