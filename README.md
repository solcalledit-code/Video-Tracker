# Video Tracker

A powerful local Python desktop app for binge-watching TV shows. Features automatic episode detection & ordering, persistent watch progress across sessions, a beautiful borderless fullscreen interface, custom HUD controls, volume booster, and keyboard shortcuts.

## ✨ Features

- **Auto Episode Ordering**: Scans your series folder and sorts episodes naturally (supports Season/Episode structures).
- **Progress Tracking**: Saves exact playback position per episode. Resumes exactly where you left off, even across app restarts.
- **Multiple Series Support**: Add unlimited series. Switch instantly via the burger menu (top-left ☰).
- **Borderless Fullscreen**: Launches in immersive fullscreen by default. Press **ESC** (or **F**) to toggle windowed mode.
- **Smart Video HUD**: Timeline scrubber, time display, play/pause, skip controls that auto-hide after 3 seconds of inactivity. Move your mouse to reveal.
- **Volume + Booster**: Standard volume (0-100%) + dedicated booster (0-600%). Effective gain applied to VLC (capped at 200% internally; pair with system volume for louder output).
- **Intro Skip**: One-click button on HUD (default 30s). **Right-click** the button to customize per session.
- **Intuitive Controls**:
  - Left/Right Arrow: ±5 seconds
  - **J** / **L**: ±10 seconds
  - **Space** or **K** or **Click**: Pause / Unpause
  - Auto-plays next episode when one finishes.
- **Keyboard Friendly**: Full shortcut support.

## 🚀 Quick Start

### Prerequisites
1. Install [VLC Media Player](https://www.videolan.org/vlc/) (required for playback).
2. `pip install python-vlc`

### Run the App
```bash
python main.py
```

### First Use
1. Click **➕ Add New Series** or use the burger menu (☰ top-left).
2. Give your series a name (e.g. "The Office").
3. Select the root folder containing your video files (seasons subfolders or flat episodes work).
4. Episodes are auto-detected and sorted.
5. Click any episode to play — it will resume from your last position!

Use the burger menu anytime to switch series or access Settings (change default intro skip time).

## 📁 File Structure Example
Your series folder can look like:
```
My Series/
├── Season 01/
│   ├── S01E01.mkv
│   ├── S01E02.mkv
│   └── ...
└── Season 02/
    ├── ...
```
Or flat episode files — the app handles both.

## 🔧 Technical Details
- Built with **Tkinter** (no extra GUI deps) + **python-vlc** for robust cross-platform playback.
- Progress & series data stored in `~/.video_tracker/` (JSON).
- Works on Windows, Linux, macOS.

## 👍 Contributing
Pull requests welcome! This is a personal project but open to improvements (e.g. better volume handling >200%, theming, subtitles).

**Created with Grok** — enjoy your watch parties! 🎬