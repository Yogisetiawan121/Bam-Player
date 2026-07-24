"""
Build script for the Bam Player application using PyInstaller.

Usage:
  python build_exe.py              # just PyInstaller (directory mode)
  python build_exe.py --portable   # PyInstaller + VLC bundle + zip
  python build_exe.py --installer  # PyInstaller + VLC bundle + Inno Setup installer
  python build_exe.py --all        # all three: raw exe + portable zip + installer
"""
import os
import re
import sys
import subprocess
import platform
import shutil
import zipfile

APP_NAME = "BamPlayer"


def find_vlc() -> str:
    """Locate the VLC installation directory containing libvlc.dll."""
    candidates = [
        r"C:\Program Files\VideoLAN\VLC",
        r"C:\Program Files (x86)\VideoLAN\VLC",
        os.path.join(os.environ.get("ProgramData", "C:\\ProgramData"),
                     "chocolatey", "lib", "vlc", "tools"),
    ]
    for p in candidates:
        if os.path.isfile(os.path.join(p, "libvlc.dll")):
            return p
    # Fallback: search PATH
    for p in os.environ.get("PATH", "").split(os.pathsep):
        if os.path.isfile(os.path.join(p, "libvlc.dll")):
            return p
    return ""


def bundle_vlc(dist_dir: str):
    """Copy VLC runtime DLLs and plugins into the dist directory."""
    vlc_dir = find_vlc()
    if not vlc_dir:
        print("WARNING: VLC not found — skipping VLC bundle. "
              "The exe needs VLC installed system-wide.")
        return False

    print(f"Bundling VLC runtime from {vlc_dir}...")
    for dll in ["libvlc.dll", "libvlccore.dll"]:
        shutil.copy2(os.path.join(vlc_dir, dll), os.path.join(dist_dir, dll))

    # Copy all plugins, then strip heavy GUI parts
    plugin_src = os.path.join(vlc_dir, "plugins")
    plugin_dst = os.path.join(dist_dir, "plugins")
    if os.path.isdir(plugin_src):
        if os.path.isdir(plugin_dst):
            shutil.rmtree(plugin_dst)
        shutil.copytree(plugin_src, plugin_dst)
        # Remove heavy GUI plugins (not needed for our embedded player)
        for strip_dir in ["qt", "gui"]:
            path = os.path.join(plugin_dst, strip_dir)
            if os.path.isdir(path):
                shutil.rmtree(path)
        # Remove plugin cache (not needed at runtime)
        cache_file = os.path.join(plugin_dst, "plugins.dat")
        if os.path.isfile(cache_file):
            os.remove(cache_file)

    size = sum(f.stat().st_size for f in os.scandir(dist_dir) if f.is_file())
    print(f"VLC bundled. Dist size: {size / 1_048_576:.1f} MB")
    return True


def create_portable_zip(version: str):
    """Create a portable .zip of the bundled dist directory."""
    dist_dir = os.path.join("dist", APP_NAME)
    zip_name = f"{APP_NAME}-{version}.zip"
    zip_path = os.path.join("dist", zip_name)

    print(f"Creating portable archive: {zip_path}")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(dist_dir):
            for f in files:
                file_path = os.path.join(root, f)
                arcname = os.path.relpath(file_path, os.path.join("dist", APP_NAME))
                zf.write(file_path, arcname)
    size = os.path.getsize(zip_path)
    print(f"Portable archive: {zip_path} ({size / 1_048_576:.1f} MB)")
    return zip_path


def build_installer(version: str):
    """Run Inno Setup to build the installer .exe."""
    # Stamp version into the .iss script
    iss_path = "installer.iss"
    with open(iss_path, "r", encoding="utf-8") as f:
        content = f.read()
    content = re.sub(
        r'#define MyAppVersion "[^"]*"',
        f'#define MyAppVersion "{version}"',
        content,
    )
    with open(iss_path, "w", encoding="utf-8") as f:
        f.write(content)

    # Find ISCC.exe
    candidates = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
    ]
    iscc = ""
    for c in candidates:
        if os.path.isfile(c):
            iscc = c
            break
    if not iscc:
        print("WARNING: Inno Setup not found — skipping installer build.")
        return None

    print(f"Running Inno Setup compiler ({iscc})...")
    result = subprocess.run([iscc, iss_path], capture_output=True, text=True)
    if len(result.stdout) > 500:
        print(result.stdout[-500:])
    else:
        print(result.stdout)
    if result.returncode != 0:
        print(f"Inno Setup failed:\n{result.stderr}")
        return None

    installer_name = f"{APP_NAME}-{version}-Setup.exe"
    installer_path = os.path.join("dist", installer_name)
    if os.path.isfile(installer_path):
        size = os.path.getsize(installer_path)
        print(f"Installer built: {installer_path} ({size / 1_048_576:.1f} MB)")
        return installer_path
    print("WARNING: Installer not found at expected path.")
    return None


def main():
    if platform.system() != 'Windows':
        print("This script is intended for Windows. Use it in a Windows environment.")
        sys.exit(1)

    args = set(a.lower() for a in sys.argv[1:])
    do_pyinstaller = True
    do_vlc_bundle = "--portable" in args or "--installer" in args or "--all" in args
    do_portable_zip = "--portable" in args or "--all" in args
    do_installer = "--installer" in args or "--all" in args

    # Step 1: PyInstaller
    print("=" * 60)
    print("Step 1: Building with PyInstaller...")
    print("=" * 60)
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "-y", "-w",
        "--name", APP_NAME,
        "--icon", "assets/icon.ico",
        "--clean",
        "--add-data", "assets/icon.ico;assets",
        "--hidden-import", "certifi",
        "--collect-data", "certifi",
        "main.py",
    ]
    subprocess.run(cmd, check=True)
    print("PyInstaller build complete.")

    dist_dir = os.path.join("dist", APP_NAME)
    if not os.path.isdir(dist_dir):
        print(f"ERROR: Expected output directory not found: {dist_dir}")
        sys.exit(1)

    # Get version from the source
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from src import __version__
    version = __version__

    # Step 2: Bundle VLC DLLs
    if do_vlc_bundle:
        print()
        print("=" * 60)
        print("Step 2: Bundling VLC runtime DLLs...")
        print("=" * 60)
        bundle_vlc(dist_dir)

    # Step 3: Create portable zip
    if do_portable_zip:
        print()
        print("=" * 60)
        print("Step 3: Creating portable archive...")
        print("=" * 60)
        create_portable_zip(version)

    # Step 4: Build installer
    if do_installer:
        print()
        print("=" * 60)
        print("Step 4: Building installer...")
        print("=" * 60)
        if not do_vlc_bundle:
            bundle_vlc(dist_dir)
        build_installer(version)

    print()
    print("All done!")
    print(f"  Raw exe:   {dist_dir}\\{APP_NAME}.exe")
    if do_portable_zip:
        print(f"  Portable:  dist/{APP_NAME}-{version}.zip")
    if do_installer:
        print(f"  Installer: dist/{APP_NAME}-{version}-Setup.exe")


if __name__ == "__main__":
    main()
