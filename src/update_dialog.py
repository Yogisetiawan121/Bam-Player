"""
Update notification dialog.
Shows available release info with release notes, version diff, and a download button.
"""
import webbrowser
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextBrowser, QWidget, QSizePolicy, QSpacerItem,
    QCheckBox, QSpinBox,
)
from PyQt6.QtCore import Qt, QSize
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

        download_btn = QPushButton("⬇  Download Update")
        download_btn.setObjectName("downloadBtn")
        download_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        download_btn.clicked.connect(self._on_download)
        btn_row.addWidget(download_btn)

        layout.addLayout(btn_row)

    def _on_download(self):
        """Open the download URL in the default browser, then close."""
        if self._release.download_url:
            webbrowser.open(self._release.download_url)
        self.accept()


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
