#!/usr/bin/env python3
"""
Video Tracker - TV Show Video Player
A feature-rich local app for watching TV series with progress tracking.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import vlc
import os
import json
from pathlib import Path
import platform
import time
from datetime import datetime

# Constants
APP_NAME = "Video Tracker"
CONFIG_DIR = Path.home() / ".video_tracker"
CONFIG_DIR.mkdir(exist_ok=True)
PROGRESS_FILE = CONFIG_DIR / "progress.json"
SERIES_FILE = CONFIG_DIR / "series.json"
DEFAULT_INTRO_SKIP = 30  # seconds

VIDEO_EXTS = {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm"}


class VideoTracker:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.geometry("1024x768")
        
        # Borderless fullscreen by default
        self.root.overrideredirect(True)
        self.root.attributes("-fullscreen", True)
        self.is_fullscreen = True
        
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.configure_dark_theme()
        
        # VLC setup
        args = ["--no-xlib"] if platform.system() == "Linux" else []
        self.vlc_instance = vlc.Instance(*args)
        self.player = self.vlc_instance.media_player_new()
        
        # State
        self.series_list = self.load_series()
        self.progress = self.load_progress()
        self.current_series = None
        self.episodes = []
        self.current_index = 0
        self.hud_visible = False
        self.hud_timer = None
        self.intro_skip_seconds = DEFAULT_INTRO_SKIP
        self.volume = 80
        self.booster = 100  # 100%
        
        # Build UI
        self.build_home_ui()
        
        # Global bindings
        self.root.bind("<Escape>", self.toggle_fullscreen)
        self.root.bind("<KeyPress>", self.handle_keypress)
        self.root.bind("<Motion>", self.on_mouse_activity)
        
        # Event for end of media
        self.player.event_manager().event_attach(
            vlc.EventType.MediaPlayerEndReached, self.on_media_end
        )
        
        self.root.mainloop()
    
    def configure_dark_theme(self):
        bg = "#1e1e1e"
        fg = "#ffffff"
        self.root.configure(bg=bg)
        self.style.configure(".", background=bg, foreground=fg, font=("Segoe UI", 10))
        self.style.configure("TButton", background="#2d2d2d", foreground=fg, padding=10)
        self.style.configure("TScale", background=bg, troughcolor="#3a3a3a")
        self.style.map("TButton", background=[("active", "#3a3a3a")])
    
    def load_series(self):
        if SERIES_FILE.exists():
            try:
                return json.loads(SERIES_FILE.read_text())
            except:
                pass
        return []
    
    def save_series(self):
        SERIES_FILE.write_text(json.dumps(self.series_list, indent=2))
    
    def load_progress(self):
        if PROGRESS_FILE.exists():
            try:
                return json.loads(PROGRESS_FILE.read_text())
            except:
                pass
        return {}
    
    def save_progress(self):
        PROGRESS_FILE.write_text(json.dumps(self.progress, indent=2))
    
    def build_home_ui(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Top bar with burger
        top_bar = tk.Frame(self.root, bg="#1e1e1e", height=50)
        top_bar.pack(fill="x", side="top")
        top_bar.pack_propagate(False)
        
        burger_btn = tk.Button(top_bar, text="☰", font=("Segoe UI", 18), bg="#1e1e1e", fg="white",
                               bd=0, activebackground="#2d2d2d", command=self.show_burger_menu)
        burger_btn.pack(side="left", padx=15, pady=5)
        
        title_label = tk.Label(top_bar, text=APP_NAME, font=("Segoe UI", 16, "bold"), bg="#1e1e1e", fg="white")
        title_label.pack(side="left", padx=20)
        
        # Center content
        center_frame = tk.Frame(self.root, bg="#1e1e1e")
        center_frame.pack(expand=True, fill="both")
        
        # Big play button
        play_btn = ttk.Button(center_frame, text="▶ Play Last Episode", 
                              command=self.play_last_episode, style="TButton")
        play_btn.pack(pady=30)
        
        add_btn = ttk.Button(center_frame, text="➕ Add New Series", 
                             command=self.add_series, style="TButton")
        add_btn.pack(pady=10)
        
        info_label = tk.Label(center_frame, text="Select a series from the menu (☰) to browse episodes",
                              bg="#1e1e1e", fg="#888888", font=("Segoe UI", 11))
        info_label.pack(pady=20)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status = tk.Label(self.root, textvariable=self.status_var, bg="#252525", fg="#aaaaaa",
                          anchor="w", padx=10)
        status.pack(fill="x", side="bottom")
    
    def show_burger_menu(self):
        menu = tk.Menu(self.root, tearoff=0, bg="#2d2d2d", fg="white",
                       activebackground="#3a3a3a", activeforeground="white")
        
        if self.series_list:
            for idx, series in enumerate(self.series_list):
                menu.add_command(label=f"📺 {series['name']}", 
                                 command=lambda i=idx: self.select_series(i))
            menu.add_separator()
        
        menu.add_command(label="➕ Add New Series", command=self.add_series)
        menu.add_command(label="⚙ Settings", command=self.show_settings)
        menu.add_separator()
        menu.add_command(label="Exit", command=self.root.quit)
        
        try:
            x = self.root.winfo_rootx() + 10
            y = self.root.winfo_rooty() + 50
            menu.tk_popup(x, y)
        except:
            menu.tk_popup(50, 50)
    
    def add_series(self):
        name = simpledialog.askstring("Series Name", "Enter series name (e.g. Breaking Bad):", parent=self.root)
        if not name:
            return
        
        root_path = filedialog.askdirectory(title="Select series root folder (containing seasons or episodes)")
        if not root_path:
            return
        
        episodes = self.scan_episodes(root_path)
        if not episodes:
            messagebox.showwarning("No Videos", "No video files found in the selected folder.")
            return
        
        series = {
            "name": name,
            "root": root_path,
            "added": datetime.now().isoformat()
        }
        self.series_list.append(series)
        self.save_series()
        
        messagebox.showinfo("Success", f"Added '{name}' with {len(episodes)} episodes.")
        self.select_series(len(self.series_list) - 1)
    
    def scan_episodes(self, root_path):
        videos = []
        for ext in VIDEO_EXTS:
            videos.extend(Path(root_path).rglob(f"*{ext}"))
        videos.sort(key=lambda p: (p.parent.name.lower(), p.name.lower()))
        return [str(p) for p in videos]
    
    def select_series(self, index):
        self.current_series = self.series_list[index]
        self.episodes = self.scan_episodes(self.current_series["root"])
        
        if not self.episodes:
            messagebox.showerror("Error", "No episodes found!")
            return
        
        self.show_episode_browser()
    
    def show_episode_browser(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        top_bar = tk.Frame(self.root, bg="#1e1e1e", height=50)
        top_bar.pack(fill="x")
        top_bar.pack_propagate(False)
        
        back_btn = tk.Button(top_bar, text="← Back", bg="#1e1e1e", fg="white", bd=0,
                             font=("Segoe UI", 12), command=self.build_home_ui)
        back_btn.pack(side="left", padx=15)
        
        title = tk.Label(top_bar, text=self.current_series["name"], font=("Segoe UI", 14, "bold"),
                         bg="#1e1e1e", fg="white")
        title.pack(side="left", padx=10)
        
        list_frame = tk.Frame(self.root, bg="#1e1e1e")
        list_frame.pack(expand=True, fill="both", padx=20, pady=10)
        
        canvas = tk.Canvas(list_frame, bg="#1e1e1e", highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#1e1e1e")
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        for i, ep_path in enumerate(self.episodes):
            ep_name = Path(ep_path).name
            key = ep_path
            prog = self.progress.get(key, {})
            pos = prog.get("position", 0)
            dur = prog.get("duration", 0)
            watched = "✓ " if pos > 0 and dur > 0 and pos >= dur * 0.9 else ""
            
            btn_text = f"{watched}{ep_name}"
            btn = ttk.Button(scrollable_frame, text=btn_text, 
                             command=lambda idx=i: self.play_episode(idx))
            btn.pack(fill="x", pady=2, padx=5)
        
        resume_btn = ttk.Button(self.root, text="▶ Resume Last Watched", 
                                command=self.play_last_in_series)
        resume_btn.pack(pady=10)
    
    def play_last_in_series(self):
        last_idx = 0
        for i, ep in enumerate(self.episodes):
            key = ep
            if key in self.progress and self.progress[key].get("position", 0) > 0:
                last_idx = i
        self.play_episode(last_idx)
    
    def play_episode(self, index):
        if index < 0 or index >= len(self.episodes):
            return
        self.current_index = index
        ep_path = self.episodes[index]
        self.create_player_window(ep_path)
    
    def create_player_window(self, media_path):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.root.title(f"{APP_NAME} - {Path(media_path).name}")
        
        self.video_frame = tk.Frame(self.root, bg="black")
        self.video_frame.pack(fill="both", expand=True)
        
        if platform.system() == "Windows":
            self.player.set_hwnd(self.video_frame.winfo_id())
        elif platform.system() == "Linux":
            self.player.set_xwindow(self.video_frame.winfo_id())
        else:
            self.player.set_nsobject(self.video_frame.winfo_id())
        
        media = self.vlc_instance.media_new(media_path)
        self.player.set_media(media)
        self.player.play()
        
        key = media_path
        if key in self.progress:
            pos = self.progress[key].get("position", 0)
            if pos > 0:
                self.root.after(800, lambda: self.player.set_time(pos))
        
        self.create_hud()
        
        self.save_position_periodically(media_path)
        
        self.video_frame.bind("<Motion>", self.on_mouse_activity)
        self.video_frame.bind("<Button-1>", self.toggle_play_pause)
        
        self.show_hud()
        self.root.after(3000, self.hide_hud)
    
    def create_hud(self):
        self.hud_frame = tk.Frame(self.root, bg="#1a1a1a", height=80)
        self.hud_frame.pack(fill="x", side="bottom")
        self.hud_frame.pack_propagate(False)
        
        timeline_row = tk.Frame(self.hud_frame, bg="#1a1a1a")
        timeline_row.pack(fill="x", padx=10, pady=5)
        
        self.time_label = tk.Label(timeline_row, text="00:00 / 00:00", bg="#1a1a1a", fg="white", width=18)
        self.time_label.pack(side="left")
        
        self.timeline = ttk.Scale(timeline_row, from_=0, to=1000, orient="horizontal",
                                  command=self.on_timeline_change)
        self.timeline.pack(side="left", fill="x", expand=True, padx=10)
        self.timeline.bind("<ButtonRelease-1>", self.seek_video)
        
        controls = tk.Frame(self.hud_frame, bg="#1a1a1a")
        controls.pack(fill="x", padx=10)
        
        self.play_btn = tk.Button(controls, text="⏸", font=("Segoe UI", 14), bg="#1a1a1a", fg="white",
                                  bd=0, command=self.toggle_play_pause)
        self.play_btn.pack(side="left", padx=5)
        
        skip_back = tk.Button(controls, text="⏪ 10s", bg="#1a1a1a", fg="white", bd=0,
                              command=lambda: self.skip_seconds(-10))
        skip_back.pack(side="left", padx=5)
        
        skip_fwd = tk.Button(controls, text="10s ⏩", bg="#1a1a1a", fg="white", bd=0,
                             command=lambda: self.skip_seconds(10))
        skip_fwd.pack(side="left", padx=5)
        
        self.skip_intro_btn = tk.Button(controls, text=f"Skip Intro ({self.intro_skip_seconds}s)", 
                                        bg="#2d2d2d", fg="#ffaa00", bd=0, font=("Segoe UI", 9),
                                        command=self.skip_intro)
        self.skip_intro_btn.pack(side="left", padx=10)
        self.skip_intro_btn.bind("<Button-3>", self.set_intro_skip)
        
        vol_frame = tk.Frame(controls, bg="#1a1a1a")
        vol_frame.pack(side="right", padx=5)
        
        tk.Label(vol_frame, text="Vol", bg="#1a1a1a", fg="white", font=("Segoe UI", 8)).pack(side="left")
        self.vol_scale = ttk.Scale(vol_frame, from_=0, to=100, orient="horizontal", length=80,
                                   command=self.update_volume)
        self.vol_scale.set(self.volume)
        self.vol_scale.pack(side="left", padx=2)
        
        tk.Label(vol_frame, text="Boost", bg="#1a1a1a", fg="#ffaa00", font=("Segoe UI", 8)).pack(side="left", padx=(10,0))
        self.boost_scale = ttk.Scale(vol_frame, from_=0, to=600, orient="horizontal", length=80,
                                     command=self.update_volume)
        self.boost_scale.set(self.booster)
        self.boost_scale.pack(side="left", padx=2)
        
        self.update_timeline()
    
    def update_timeline(self):
        if not hasattr(self, "player") or not self.player.is_playing():
            if hasattr(self, "hud_frame"):
                self.root.after(500, self.update_timeline)
            return
        
        try:
            length = self.player.get_length()
            if length > 0:
                pos = self.player.get_time()
                percent = (pos / length) * 1000
                self.timeline.set(percent)
                
                pos_str = self.format_time(pos)
                len_str = self.format_time(length)
                self.time_label.config(text=f"{pos_str} / {len_str}")
        except:
            pass
        
        if hasattr(self, "hud_frame"):
            self.root.after(500, self.update_timeline)
    
    def format_time(self, ms):
        if ms < 0:
            ms = 0
        s = int(ms / 1000)
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"
    
    def on_timeline_change(self, val):
        pass
    
    def seek_video(self, event=None):
        if not hasattr(self, "player"):
            return
        val = self.timeline.get()
        length = self.player.get_length()
        if length > 0:
            new_time = int((val / 1000) * length)
            self.player.set_time(new_time)
    
    def update_volume(self, val=None):
        vol = self.vol_scale.get()
        boost = self.boost_scale.get()
        self.volume = vol
        self.booster = boost
        
        effective = int(vol * (boost / 100.0))
        vlc_vol = min(200, effective)
        self.player.audio_set_volume(vlc_vol)
    
    def skip_seconds(self, secs):
        if not hasattr(self, "player"):
            return
        current = self.player.get_time()
        new_time = max(0, current + secs * 1000)
        self.player.set_time(new_time)
        self.show_hud()
    
    def skip_intro(self):
        self.skip_seconds(self.intro_skip_seconds)
    
    def set_intro_skip(self, event):
        new_val = simpledialog.askinteger("Intro Skip", "Set intro skip seconds:",
                                          initialvalue=self.intro_skip_seconds, minvalue=0, maxvalue=300)
        if new_val is not None:
            self.intro_skip_seconds = new_val
            if hasattr(self, "skip_intro_btn"):
                self.skip_intro_btn.config(text=f"Skip Intro ({self.intro_skip_seconds}s)")
    
    def toggle_play_pause(self, event=None):
        if not hasattr(self, "player"):
            return
        if self.player.is_playing():
            self.player.pause()
            self.play_btn.config(text="▶")
        else:
            self.player.play()
            self.play_btn.config(text="⏸")
        self.show_hud()
    
    def show_hud(self):
        if hasattr(self, "hud_frame"):
            self.hud_frame.pack(fill="x", side="bottom")
            self.hud_visible = True
            if self.hud_timer:
                self.root.after_cancel(self.hud_timer)
            self.hud_timer = self.root.after(3000, self.hide_hud)
    
    def hide_hud(self):
        if hasattr(self, "hud_frame") and self.hud_visible:
            self.hud_frame.pack_forget()
            self.hud_visible = False
    
    def on_mouse_activity(self, event=None):
        self.show_hud()
    
    def handle_keypress(self, event):
        if not hasattr(self, "player"):
            return
        
        key = event.keysym.lower()
        if key in ("space", "k"):
            self.toggle_play_pause()
        elif key == "left":
            self.skip_seconds(-5)
        elif key == "right":
            self.skip_seconds(5)
        elif key == "j":
            self.skip_seconds(-10)
        elif key == "l":
            self.skip_seconds(10)
        elif key == "f":
            self.toggle_fullscreen()
        elif key == "escape":
            self.toggle_fullscreen()
    
    def toggle_fullscreen(self, event=None):
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes("-fullscreen", self.is_fullscreen)
        if not self.is_fullscreen:
            self.root.overrideredirect(False)
            self.root.geometry("1024x768")
        else:
            self.root.overrideredirect(True)
    
    def on_media_end(self, event):
        if self.current_index + 1 < len(self.episodes):
            next_idx = self.current_index + 1
            self.root.after(1000, lambda: self.play_episode(next_idx))
        else:
            self.root.after(1000, self.build_home_ui)
    
    def save_position_periodically(self, media_path):
        def saver():
            if hasattr(self, "player") and self.player.get_media():
                try:
                    pos = self.player.get_time()
                    dur = self.player.get_length()
                    if pos > 0 and dur > 0:
                        if media_path not in self.progress:
                            self.progress[media_path] = {}
                        self.progress[media_path]["position"] = pos
                        self.progress[media_path]["duration"] = dur
                        self.progress[media_path]["last_watched"] = datetime.now().isoformat()
                        self.save_progress()
                except:
                    pass
            if hasattr(self, "player") and self.player.get_media():
                self.root.after(5000, saver)
        
        self.root.after(5000, saver)
    
    def play_last_episode(self):
        latest = None
        latest_time = ""
        for series in self.series_list:
            eps = self.scan_episodes(series["root"])
            for ep in eps:
                if ep in self.progress:
                    t = self.progress[ep].get("last_watched", "")
                    if t > latest_time:
                        latest_time = t
                        latest = (series, ep, eps.index(ep) if ep in eps else 0)
        
        if latest:
            series, ep_path, idx = latest
            self.current_series = series
            self.episodes = self.scan_episodes(series["root"])
            self.play_episode(idx)
        else:
            if self.series_list:
                self.select_series(0)
            else:
                messagebox.showinfo("No Series", "Add a series first using the menu!")
    
    def show_settings(self):
        win = tk.Toplevel(self.root)
        win.title("Settings")
        win.geometry("400x300")
        win.configure(bg="#1e1e1e")
        
        tk.Label(win, text="Intro Skip Default (seconds)", bg="#1e1e1e", fg="white").pack(pady=10)
        skip_var = tk.IntVar(value=self.intro_skip_seconds)
        ttk.Scale(win, from_=0, to=120, variable=skip_var, orient="horizontal").pack(fill="x", padx=20)
        
        def save():
            self.intro_skip_seconds = skip_var.get()
            if hasattr(self, "skip_intro_btn"):
                self.skip_intro_btn.config(text=f"Skip Intro ({self.intro_skip_seconds}s)")
            win.destroy()
        
        ttk.Button(win, text="Save", command=save).pack(pady=20)
        
        tk.Label(win, text="Volume Booster maxes effective volume at 200% (VLC limit).\nSystem volume can be used for more.", 
                 bg="#1e1e1e", fg="#888888", wraplength=350).pack(pady=10)


if __name__ == "__main__":
    VideoTracker()
