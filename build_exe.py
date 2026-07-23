import os
import sys
import subprocess
import platform

def main():
    if platform.system() != 'Windows':
        print("This script is intended for Windows. Use it in a Windows environment or Wine.")
        sys.exit(1)

    # PyInstaller command
    # -y : Noconfirm (overwrite output)
    # -w : Windowed (no console)
    # -F : Onefile mode (optional, let's use directory mode for faster startup & DLLs)
    # --icon: Add app icon
    # --add-data: Include assets if any
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "-y",
        "-w",
        "--name", "BamPlayer",
        "--icon", "assets/icon.ico",
        "--clean",
        "main.py"
    ]
    
    # Run PyInstaller
    print("Running PyInstaller...")
    try:
        subprocess.run(cmd, check=True)
        print("\nBuild successful! Executable is in the 'dist/BamPlayer' directory.")
        
        # Note: python-vlc depends on libvlc.dll and plugins folder. 
        # A full standalone exe would need those copied or bundled.
        print("Note: To run standalone on a PC without VLC, you must copy VLC 'plugins' folder and libvlc.dll/libvlccore.dll to the dist/BamPlayer folder.")
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
