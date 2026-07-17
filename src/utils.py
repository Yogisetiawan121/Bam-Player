"""
Utility functions for the video player application.
Handles time formatting, file validation, path operations, and thumbnail generation.
"""
import os
import re
import json
import hashlib
from pathlib import Path
from typing import Optional, List

# Supported media formats
VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.ts', '.mpg', '.mpeg', '.3gp'}
SUBTITLE_EXTENSIONS = {'.srt', '.ass', '.ssa', '.vtt', '.sub', '.idx'}
PLAYLIST_EXTENSION = '.json'
AUDIO_EXTENSIONS = {'.mp3', '.flac', '.wav', '.aac', '.ogg', '.wma', '.m4a'}


def format_time(ms: int) -> str:
    """Format milliseconds to HH:MM:SS or MM:SS string."""
    if ms < 0:
        ms = 0
    total_seconds = ms // 1000
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    if hours > 0:
        return f"{hours:d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:d}:{seconds:02d}"


def format_time_precise(ms: int) -> str:
    """Format milliseconds to HH:MM:SS.mmm string."""
    if ms < 0:
        ms = 0
    total_seconds = ms // 1000
    millis = ms % 1000
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{millis:03d}"


def is_video_file(filepath: str) -> bool:
    """Check if a file is a supported video format."""
    return Path(filepath).suffix.lower() in VIDEO_EXTENSIONS


def is_subtitle_file(filepath: str) -> bool:
    """Check if a file is a supported subtitle format."""
    return Path(filepath).suffix.lower() in SUBTITLE_EXTENSIONS


def is_media_file(filepath: str) -> bool:
    """Check if a file is any supported media format."""
    ext = Path(filepath).suffix.lower()
    return ext in VIDEO_EXTENSIONS or ext in AUDIO_EXTENSIONS


def get_video_files_from_dir(directory: str) -> List[str]:
    """Recursively get all video files from a directory."""
    video_files = []
    for root, _, files in os.walk(directory):
        for f in files:
            filepath = os.path.join(root, f)
            if is_video_file(filepath):
                video_files.append(filepath)
    video_files.sort(key=lambda x: x.lower())
    return video_files


def find_subtitles_for_video(video_path: str) -> List[str]:
    """Find subtitle files matching the video filename in the same directory."""
    video_dir = os.path.dirname(video_path)
    video_stem = Path(video_path).stem.lower()
    subtitles = []

    if not os.path.isdir(video_dir):
        return subtitles

    for f in os.listdir(video_dir):
        f_path = os.path.join(video_dir, f)
        if is_subtitle_file(f_path):
            f_stem = Path(f).stem.lower()
            # Match "video.srt", "video.en.srt", etc.
            if f_stem == video_stem or f_stem.startswith(video_stem + '.'):
                subtitles.append(f_path)
    return sorted(subtitles)


def get_file_hash(filepath: str) -> str:
    """Get MD5 hash of first 64KB of file for quick identification."""
    hasher = hashlib.md5()
    try:
        with open(filepath, 'rb') as f:
            hasher.update(f.read(65536))
    except (IOError, OSError):
        return ""
    return hasher.hexdigest()


def get_pictures_folder() -> str:
    """Get the system Pictures folder path."""
    pictures = os.path.join(os.path.expanduser("~"), "Pictures", "Bam Player Screenshots")
    os.makedirs(pictures, exist_ok=True)
    return pictures


def sanitize_filename(name: str) -> str:
    """Remove invalid characters from a filename."""
    return re.sub(r'[<>:"/\\|?*]', '_', name)


def human_readable_size(size_bytes: int) -> str:
    """Convert bytes to human readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def clamp(value, min_val, max_val):
    """Clamp a value between min and max."""
    return max(min_val, min(max_val, value))


def parse_srt_time(time_str: str) -> int:
    """Parse SRT timestamp to milliseconds."""
    match = re.match(r'(\d{2}):(\d{2}):(\d{2})[,.](\d{3})', time_str.strip())
    if match:
        h, m, s, ms = map(int, match.groups())
        return h * 3600000 + m * 60000 + s * 1000 + ms
    return 0


def get_app_data_dir() -> str:
    """Get the application data directory for storing databases and configs."""
    app_data = os.path.join(os.getenv('APPDATA', os.path.expanduser('~')), 'BamPlayer')
    if not os.path.exists(app_data):
        os.makedirs(app_data)
    return app_data
