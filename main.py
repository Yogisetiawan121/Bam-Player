import sys
import os

from PyQt6.QtWidgets import QApplication
from src.main_window import MainWindow

def main():
    # Setup App
    app = QApplication(sys.argv)
    app.setApplicationName("Bam Player")
    app.setApplicationVersion("1.3.0")
    
    # Ensure VLC plugins are found on Windows when running from source or pyinstaller
    if sys.platform == 'win32':
        vlc_plugin_path = os.environ.get('VLC_PLUGIN_PATH')
        if not vlc_plugin_path:
            # Common paths for VLC on windows
            common_paths = [
                r"C:\Program Files\VideoLAN\VLC\plugins",
                r"C:\Program Files (x86)\VideoLAN\VLC\plugins",
                # Also check relative to executable if bundled
                os.path.join(os.path.dirname(sys.executable), "plugins")
            ]
            for p in common_paths:
                if os.path.exists(p):
                    os.environ['VLC_PLUGIN_PATH'] = p
                    break

    window = MainWindow()
    
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        window.play_file(sys.argv[1])
        
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
