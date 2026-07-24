import sys
import os

from PyQt6.QtWidgets import QApplication
from src.main_window import MainWindow

def main():
    # Setup App
    app = QApplication(sys.argv)
    app.setApplicationName("Bam Player")
    app.setApplicationVersion("1.7.0")

    window = MainWindow()
    
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        window.play_file(sys.argv[1])
        
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
