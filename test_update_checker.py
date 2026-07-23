"""Quick validation of the update checker module."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# 1. Test version comparison
from src.update_checker import UpdateChecker

checker = UpdateChecker("test/repo")

tests = [
    ("1.1.0", "1.0.0", True, "minor bump"),
    ("2.0.0", "1.9.9", True, "major bump"),
    ("1.0.1", "1.0.0", True, "patch bump"),
    ("1.0.0", "1.0.0", False, "same version"),
    ("1.0.0", "1.0.1", False, "older remote"),
    ("0.9.0", "1.0.0", False, "older major"),
    ("1.0.0-beta", "1.0.0-alpha", True, "pre-release newer"),
    ("1.0.0", "1.0.0-beta", True, "release > pre-release"),
    ("v1.0.0", "1.0.0", False, "v prefix stripped"),
    ("1.10.0", "1.9.0", True, "two-digit minor"),
    ("1.0.0+sha1234", "1.0.0", False, "build metadata ignored"),
]

all_pass = True
for remote, current, expected, label in tests:
    result = UpdateChecker._is_newer(remote, current)
    if result != expected:
        print(f"FAIL: '{remote}' vs '{current}' ({label}) — expected {expected}, got {result}")
        all_pass = False
    else:
        print(f"PASS: '{remote}' vs '{current}' ({label})")

# 2. Test asset picking
from src.update_checker import UpdateChecker
import sys

# Mock sys.platform for testing
original_platform = sys.platform

# Test Windows asset picking
sys.platform = "win32"
win_checker = UpdateChecker("test/repo")
assets = [
    {"name": "player-1.0.0.tar.gz", "browser_download_url": "https://example.com/tar.gz"},
    {"name": "player-1.0.0.exe", "browser_download_url": "https://example.com/exe"},
    {"name": "player-1.0.0.zip", "browser_download_url": "https://example.com/zip"},
]
url = win_checker._pick_asset(assets)
assert url == "https://example.com/exe", f"Expected exe, got {url}"
print(f"PASS: Windows picks .exe first: {url}")

# Test Linux
sys.platform = "linux"
linux_checker = UpdateChecker("test/repo")
url = linux_checker._pick_asset(assets)
assert url == "https://example.com/tar.gz", f"Expected tar.gz, got {url}"
print(f"PASS: Linux picks .tar.gz first: {url}")

sys.platform = original_platform
print("\nAll tests passed!" if all_pass else "\nSome tests FAILED!")
