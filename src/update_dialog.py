"""
Update notification dialog.
Shows available release info with release notes, version diff, and a download button.
"""
import os
import ssl
import tempfile
import urllib.request
import urllib.error

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextBrowser, QWidget, QSizePolicy, QSpacerItem,
    QCheckBox, QSpinBox, QProgressBar, QMessageBox,
)
from PyQt6.QtCore import Qt, QSize, QThread, QObject, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QFont, QPixmap, QIcon
import qtawesome as qta

from . import __version__, __app_name__
from .update_checker import ReleaseInfo, DEFAULT_REPO
from .settings_manager import SettingsManager


class UpdateAvailableDialog(QDialog):
    """Modal dialog shown when a new version is available."""

    def __init__(self, release: ReleaseInfo, parent=None):
        super().__init__(parent)
        self._release = release
        self.setWindowTitle(f"Update Available — {__app_name__}")
        self.setFixedSize(520, 480)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #0a0a0f;
                border: 1px solid #1e1e2e;
                border-radius: 12px;
            }
            QLabel#headerLabel {
                color: #e8e8f0;
                font-size: 18px;
                font-weight: 700;
            }
            QLabel#versionLabel {
                color: #a29bfe;
                font-size: 14px;
                font-weight: 600;
            }
            QLabel#infoLabel {
                color: #8888a0;
                font-size: 12px;
            }
            QTextBrowser {
                background-color: #12121a;
                color: #d0d0e0;
                border: 1px solid #1e1e2e;
                border-radius: 8px;
                padding: 12px;
                font-size: 13px;
            }
            QPushButton#downloadBtn {
                background-color: #6c5ce7;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 28px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton#downloadBtn:hover {
                background-color: #a29bfe;
            }
            QPushButton#downloadBtn:pressed {
                background-color: #4834d4;
            }
            QPushButton#laterBtn {
                background-color: transparent;
                color: #8888a0;
                border: 1px solid #1e1e2e;
                border-radius: 8px;
                padding: 10px 28px;
                font-size: 13px;
            }
            QPushButton#laterBtn:hover {
                background-color: rgba(255,255,255,0.05);
                color: #e8e8f0;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)

        # ── Header row: icon + title ──
        header_row = QHBoxLayout()
        header_row.setSpacing(12)

        icon_label = QLabel()
        icon_label.setPixmap(qta.icon('mdi6.update', color='#a29bfe').pixmap(32, 32))
        header_row.addWidget(icon_label)

        header_label = QLabel("An Update is Available!")
        header_label.setObjectName("headerLabel")
        header_row.addWidget(header_label)
        header_row.addStretch()
        layout.addLayout(header_row)

        # ── Version info ──
        version_text = f"{__version__}  →  {self._release.version}"
        version_label = QLabel(version_text)
        version_label.setObjectName("versionLabel")
        layout.addWidget(version_label)

        # Release date
        date_label = QLabel(f"Released: {self._release.published_at[:10]}")
        date_label.setObjectName("infoLabel")
        layout.addWidget(date_label)

        if self._release.is_prerelease:
            pre_label = QLabel("⚠ This is a pre-release version")
            pre_label.setStyleSheet("color: #ffd43b; font-size: 11px; font-weight: 600;")
            layout.addWidget(pre_label)

        layout.addSpacing(8)

        # ── Release notes ──
        notes_label = QLabel("Release Notes:")
        notes_label.setStyleSheet("color: #8888a0; font-size: 12px; font-weight: 600;")
        layout.addWidget(notes_label)

        notes_browser = QTextBrowser()
        notes_browser.setOpenExternalLinks(True)
        notes_browser.setPlainText(self._release.release_notes)
        layout.addWidget(notes_browser)

        layout.addSpacing(8)

        # ── Action buttons ──
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        later_btn = QPushButton("Remind Me Later")
        later_btn.setObjectName("laterBtn")
        later_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        later_btn.clicked.connect(self.reject)
        btn_row.addWidget(later_btn)

        btn_row.addStretch()

        download_btn = QPushButton("⬇  Download & Install")
        download_btn.setObjectName("downloadBtn")
        download_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        download_btn.clicked.connect(lambda: self.accept())
        btn_row.addWidget(download_btn)

        layout.addLayout(btn_row)


# ── Background Download Worker ──────────────────────────────────────

class DownloadWorker(QObject):
    """Downloads a file in a background thread, emitting progress signals."""

    progress = pyqtSignal(int, int)   # bytes_downloaded, total_bytes
    finished = pyqtSignal(str)        # file_path
    error = pyqtSignal(str)           # error_message

    def __init__(self, url: str, dest_path: str):
        super().__init__()
        self.url = url
        self.dest_path = dest_path
        self._cancelled = False

    def cancel(self):
        """Signal the download to stop at the next chunk."""
        self._cancelled = True

    def run(self):
        """Perform the download (call from a QThread)."""
        try:
            ctx = ssl.create_default_context()
            req = urllib.request.Request(
                self.url,
                headers={
                    "User-Agent": f"{__app_name__}-Updater/{__version__}",
                },
            )
            with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
                total = int(resp.headers.get("Content-Length", 0))
                downloaded = 0
                chunk_size = 65536
                with open(self.dest_path, "wb") as f:
                    while True:
                        if self._cancelled:
                            self._cleanup()
                            return
                        chunk = resp.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        self.progress.emit(downloaded, total)

            if not self._cancelled:
                self.finished.emit(self.dest_path)
        except urllib.error.HTTPError as e:
            self.error.emit(f"Server error: {e.code} {e.reason}")
        except urllib.error.URLError as e:
            self.error.emit(f"Connection failed: {e.reason}")
        except OSError as e:
            self.error.emit(f"File error: {e.strerror}")
        except Exception as e:
            self.error.emit(str(e))

    def _cleanup(self):
        """Remove partially-downloaded file on cancellation."""
        try:
            if os.path.exists(self.dest_path):
                os.remove(self.dest_path)
        except Exception:
            pass


# ── Download Progress Dialog ─────────────────────────────────────────

class UpdateDownloadDialog(QDialog):
    """Modal dialog that downloads the installer with a progress bar.

    After download completes, the user can click "Install Now" to
    launch the installer and close the app.
    """

    def __init__(self, release: ReleaseInfo, parent=None):
        super().__init__(parent)
        self._release = release
        self.installer_path: str = ""
        self._worker: DownloadWorker = None
        self._thread: QThread = None
        self._download_complete = False
        self.setWindowTitle(f"Downloading Update — {__app_name__}")
        self.setFixedSize(440, 200)
        self.setWindowFlags(
            self.windowFlags()
            & ~Qt.WindowType.WindowContextHelpButtonHint
            & ~Qt.WindowType.WindowCloseButtonHint  # prevent accidental close
        )
        self.setModal(True)
        self._setup_ui()
        self._start_download()

    def _setup_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #0a0a0f;
                border: 1px solid #1e1e2e;
                border-radius: 12px;
            }
            QLabel#headerLabel {
                color: #e8e8f0;
                font-size: 16px;
                font-weight: 700;
            }
            QLabel#infoLabel {
                color: #8888a0;
                font-size: 12px;
            }
            QProgressBar {
                background-color: #12121a;
                border: 1px solid #1e1e2e;
                border-radius: 6px;
                text-align: center;
                color: #e8e8f0;
                font-size: 12px;
                height: 22px;
            }
            QProgressBar::chunk {
                background-color: #6c5ce7;
                border-radius: 5px;
            }
            QProgressBar#completeBar::chunk {
                background-color: #51cf66;
                border-radius: 5px;
            }
            QPushButton#actionBtn {
                background-color: #6c5ce7;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 24px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton#actionBtn:hover {
                background-color: #a29bfe;
            }
            QPushButton#actionBtn:pressed {
                background-color: #4834d4;
            }
            QPushButton#installBtn {
                background-color: #51cf66;
                color: #0a0a0f;
                border: none;
                border-radius: 8px;
                padding: 8px 24px;
                font-size: 14px;
                font-weight: 700;
            }
            QPushButton#installBtn:hover {
                background-color: #69db7c;
            }
            QPushButton#installBtn:pressed {
                background-color: #40c057;
            }
            QPushButton#cancelBtn {
                background-color: transparent;
                color: #8888a0;
                border: 1px solid #1e1e2e;
                border-radius: 8px;
                padding: 8px 20px;
                font-size: 13px;
            }
            QPushButton#cancelBtn:hover {
                color: #e8e8f0;
                background-color: rgba(255,255,255,0.05);
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 20, 28, 20)
        layout.setSpacing(12)

        # ── Header ──
        header_row = QHBoxLayout()
        header_row.setSpacing(10)

        self._icon_label = QLabel()
        self._icon_label.setPixmap(
            qta.icon("mdi6.download", color="#6c5ce7").pixmap(28, 28)
        )
        header_row.addWidget(self._icon_label)

        self._header_label = QLabel("Downloading update…")
        self._header_label.setObjectName("headerLabel")
        header_row.addWidget(self._header_label)
        header_row.addStretch()
        layout.addLayout(header_row)

        # ── Version info ──
        self._version_label = QLabel(
            f"Version {self._release.version}"
        )
        self._version_label.setObjectName("infoLabel")
        layout.addWidget(self._version_label)

        # ── Progress bar ──
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(True)
        self._progress_bar.setFixedHeight(24)
        layout.addWidget(self._progress_bar)

        # ── Size label ──
        self._size_label = QLabel("Preparing download…")
        self._size_label.setObjectName("infoLabel")
        layout.addWidget(self._size_label)

        layout.addStretch()

        # ── Buttons ──
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        btn_row.addStretch()

        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.setObjectName("cancelBtn")
        self._cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._cancel_btn.clicked.connect(self._on_cancel)
        btn_row.addWidget(self._cancel_btn)

        self._action_btn = QPushButton("Downloading…")
        self._action_btn.setObjectName("actionBtn")
        self._action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._action_btn.setEnabled(False)
        self._action_btn.setVisible(True)
        self._action_btn.clicked.connect(self._on_install)
        btn_row.addWidget(self._action_btn)

        layout.addLayout(btn_row)

    # ── Download lifecycle ───────────────────────────────────────────

    def _start_download(self):
        """Build the temp path and kick off the background download thread."""
        dest_dir = tempfile.gettempdir()
        exe_name = f"BamPlayer-{self._release.version}-Setup.exe"
        dest_path = os.path.join(dest_dir, exe_name)
        self.installer_path = dest_path

        self._worker = DownloadWorker(self._release.download_url, dest_path)
        self._thread = QThread(self)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_download_finished)
        self._worker.error.connect(self._on_download_error)
        self._thread.finished.connect(self._worker.deleteLater)

        self._thread.start()

    @pyqtSlot(int, int)
    def _on_progress(self, downloaded: int, total: int):
        """Update progress bar and size label."""
        if total > 0:
            pct = int(downloaded * 100 / total)
            self._progress_bar.setValue(pct)
            self._size_label.setText(
                f"{self._format_size(downloaded)} / {self._format_size(total)}"
            )
        else:
            # Unknown total size — show indeterminate progress
            self._progress_bar.setRange(0, 0)
            self._size_label.setText(f"{self._format_size(downloaded)} downloaded")

    @pyqtSlot(str)
    def _on_download_finished(self, path: str):
        """Download complete — switch to install-ready UI."""
        self._download_complete = True
        self._progress_bar.setValue(100)
        self._progress_bar.setObjectName("completeBar")
        self._progress_bar.style().unpolish(self._progress_bar)
        self._progress_bar.style().polish(self._progress_bar)

        self._icon_label.setPixmap(
            qta.icon("mdi6.check-circle", color="#51cf66").pixmap(28, 28)
        )
        self._header_label.setText("Update Ready!")

        size_info = self._size_label.text()
        self._size_label.setText(f"{size_info}  —  Ready to install")

        self._cancel_btn.setText("Later")
        self._cancel_btn.setObjectName("cancelBtn")  # keep same style

        self._action_btn.setText("🚀  Install Now")
        self._action_btn.setObjectName("installBtn")
        self._action_btn.style().unpolish(self._action_btn)
        self._action_btn.style().polish(self._action_btn)
        self._action_btn.setEnabled(True)

        self._thread.quit()

    @pyqtSlot(str)
    def _on_download_error(self, error_msg: str):
        """Download failed — show error and offer retry."""
        self._thread.quit()
        self._icon_label.setPixmap(
            qta.icon("mdi6.alert-circle", color="#ff6b6b").pixmap(28, 28)
        )
        self._header_label.setText("Download Failed")
        self._size_label.setText(error_msg)

        self._cancel_btn.setText("Close")
        self._action_btn.setText("🔄  Retry")
        self._action_btn.setObjectName("actionBtn")
        self._action_btn.style().unpolish(self._action_btn)
        self._action_btn.style().polish(self._action_btn)
        self._action_btn.setEnabled(True)
        self._action_btn.clicked.disconnect()
        self._action_btn.clicked.connect(self._retry_download)

    def _retry_download(self):
        """Reset UI and start download again."""
        self._progress_bar.setValue(0)
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setObjectName("")
        self._progress_bar.style().unpolish(self._progress_bar)
        self._progress_bar.style().polish(self._progress_bar)

        self._icon_label.setPixmap(
            qta.icon("mdi6.download", color="#6c5ce7").pixmap(28, 28)
        )
        self._header_label.setText("Downloading update…")
        self._size_label.setText("Preparing download…")

        self._cancel_btn.setText("Cancel")
        self._action_btn.setText("Downloading…")
        self._action_btn.setObjectName("actionBtn")
        self._action_btn.style().unpolish(self._action_btn)
        self._action_btn.style().polish(self._action_btn)
        self._action_btn.setEnabled(False)
        self._action_btn.clicked.disconnect()
        self._action_btn.clicked.connect(self._on_install)

        self._start_download()

    def _on_cancel(self):
        """Cancel download or close dialog."""
        if not self._download_complete and self._worker:
            self._worker.cancel()
        if self._thread and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait(2000)
        self.reject()

    def _on_install(self):
        """User clicked Install Now — accept the dialog."""
        if self._download_complete:
            self.accept()

    # ── Helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _format_size(bytes_val: int) -> str:
        """Return a human-readable size string (e.g. "12.3 MB")."""
        if bytes_val < 1024:
            return f"{bytes_val} B"
        elif bytes_val < 1024 * 1024:
            return f"{bytes_val / 1024:.1f} KB"
        elif bytes_val < 1024 * 1024 * 1024:
            return f"{bytes_val / (1024 * 1024):.1f} MB"
        else:
            return f"{bytes_val / (1024 * 1024 * 1024):.1f} GB"

    def closeEvent(self, event):
        """Clean up the background thread on close."""
        if self._worker and not self._download_complete:
            self._worker.cancel()
        if self._thread and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait(2000)
        super().closeEvent(event)


class UpToDateDialog(QDialog):
    """Small confirmation dialog when the user manually checks and is up to date."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{__app_name__} — Up to Date")
        self.setFixedSize(340, 160)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #0a0a0f;
                border: 1px solid #1e1e2e;
                border-radius: 12px;
            }
            QLabel#uptodateIcon {
                font-size: 32px;
            }
            QLabel#uptodateTitle {
                color: #51cf66;
                font-size: 16px;
                font-weight: 700;
            }
            QLabel#uptodateSub {
                color: #8888a0;
                font-size: 12px;
            }
            QPushButton {
                background-color: #6c5ce7;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 24px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #a29bfe;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(6)

        icon_label = QLabel()
        icon_label.setPixmap(qta.icon('mdi6.check-circle', color='#51cf66').pixmap(40, 40))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        title = QLabel(f"{__app_name__} is up to date")
        title.setObjectName("uptodateTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        sub = QLabel(f"Version {__version__} — the latest release.")
        sub.setObjectName("uptodateSub")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sub)

        layout.addSpacing(8)

        ok_btn = QPushButton("OK")
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.clicked.connect(self.accept)
        layout.addWidget(ok_btn, alignment=Qt.AlignmentFlag.AlignCenter)


class UpdateSettingsDialog(QDialog):
    """Settings dialog for configuring auto-update preferences.

    The GitHub repo is hardcoded as DEFAULT_REPO — no input needed.
    """

    def __init__(self, parent, settings: SettingsManager):
        super().__init__(parent)
        self.setWindowTitle(f"Update Settings — {__app_name__}")
        self.setFixedSize(420, 260)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        _, self._auto_check, self._interval = settings.load_update_settings()
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #0a0a0f;
                border: 1px solid #1e1e2e;
                border-radius: 12px;
            }
            QLabel {
                color: #e8e8f0;
                font-size: 13px;
            }
            QLabel#infoLabel {
                color: #8888a0;
                font-size: 11px;
            }
            QCheckBox {
                color: #e8e8f0;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid #3a3a4e;
                background-color: #12121a;
            }
            QCheckBox::indicator:checked {
                background-color: #6c5ce7;
                border-color: #6c5ce7;
            }
            QSpinBox {
                background-color: #12121a;
                color: #e8e8f0;
                border: 1px solid #1e1e2e;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
            }
            QSpinBox:focus {
                border-color: #6c5ce7;
            }
            QPushButton {
                background-color: #6c5ce7;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #a29bfe;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 20, 28, 20)
        layout.setSpacing(12)

        # Title
        title = QLabel("Update Preferences")
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #a29bfe;")
        layout.addWidget(title)

        # Description + repo info
        desc = QLabel(
            "Checking for updates on:"
        )
        desc.setStyleSheet("color: #8888a0; font-size: 12px;")
        layout.addWidget(desc)

        repo_label = QLabel(DEFAULT_REPO)
        repo_label.setObjectName("infoLabel")
        repo_label.setStyleSheet("color: #a29bfe; font-size: 12px; font-weight: 600;")
        layout.addWidget(repo_label)

        layout.addSpacing(8)

        # Auto-check toggle
        self._auto_check_cb = QCheckBox("Check for updates automatically")
        self._auto_check_cb.setChecked(self._auto_check)
        layout.addWidget(self._auto_check_cb)

        # Interval
        interval_row = QHBoxLayout()
        interval_row.setSpacing(8)
        interval_label = QLabel("Check every:")
        interval_label.setStyleSheet("color: #8888a0;")
        interval_row.addWidget(interval_label)

        self._interval_spin = QSpinBox()
        self._interval_spin.setRange(1, 168)
        self._interval_spin.setValue(self._interval)
        self._interval_spin.setSuffix(" hours")
        self._interval_spin.setFixedWidth(120)
        self._interval_spin.setEnabled(self._auto_check)
        self._auto_check_cb.toggled.connect(self._interval_spin.setEnabled)
        interval_row.addWidget(self._interval_spin)
        interval_row.addStretch()
        layout.addLayout(interval_row)

        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #8888a0;
                border: 1px solid #1e1e2e;
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 13px;
            }
            QPushButton:hover {
                color: #e8e8f0;
                background-color: rgba(255,255,255,0.05);
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def get_values(self) -> tuple:
        """Return (repo, auto_check, interval_hours)."""
        return (
            DEFAULT_REPO,
            self._auto_check_cb.isChecked(),
            self._interval_spin.value(),
        )

    def get_repo(self) -> str:
        return DEFAULT_REPO

    def is_auto_check_enabled(self) -> bool:
        return self._auto_check_cb.isChecked()

    def get_interval(self) -> int:
        return self._interval_spin.value()
