# Bam Player

A feature-rich desktop video player built with Python, PyQt6, and the VLC media engine. 

Features a modern dark glassmorphism UI, comprehensive playlist management, subtitle support, video filters, and hardware-accelerated playback.

## Features
- **Wide Format Support**: MP4, MKV, AVI, MOV, FLV, WEBM, and more.
- **Hardware Acceleration**: Utilizes VLC's hardware decoding where available.
- **Modern UI**: Dark theme with translucent overlay controls that auto-hide.
- **Playlist Management**: Drag-and-drop support, JSON playlist saving/loading.
- **Subtitles**: Load `.srt`, `.ass`, `.vtt` with customizable font, size, and color.
- **Video Adjustments**: Real-time Brightness, Contrast, Saturation, Hue, and Gamma.
- **Shortcuts**: Full keyboard navigation (Space to play, F11 for fullscreen, arrows for seeking).
- **On-Screen Display**: Animated overlays for volume, speed, and seek changes.
- **Persistence**: Remembers window position, size, recent files, and volume.

## Requirements
- Python 3.10+
- VLC Media Player installed on your system (for local development).


## Keyboard Shortcuts
- `Space`: Play / Pause
- `F11` or `Double-Click`: Toggle Fullscreen
- `Right` / `Left`: Seek Forward / Backward (5s)
- `Ctrl + Right/Left`: Seek Forward / Backward (30s)
- `Up` / `Down`: Volume Up / Down
- `M`: Toggle Mute
- `[` / `]`: Decrease / Increase Playback Speed
- `\`: Reset Speed to 1.0x
- `,` / `.`: Frame Step Backward / Forward
- `Ctrl+O`: Open File
- `Ctrl+Shift+O`: Open Folder
- `Ctrl+P`: Toggle Playlist
- `Ctrl+S`: Take Screenshot
- `Ctrl+T`: Toggle Always on Top
