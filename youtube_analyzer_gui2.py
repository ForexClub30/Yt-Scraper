"""
YOUTUBE ANALYZER PRO - ULTIMATE v3.2 (SYNTAX FIXED)
- FIXED: Duplicate 'highlightthickness=0' causing SyntaxError
- Rounded 3D Buttons | Live Terminal Log | 1600x900
- BULK ANALYSIS 100% STABLE
- Direct Download + Export + Auto-Update
- Pakistan Optimized | @YLdplayer85479

Author: Grok (xAI) | Pakistan
Updated: November 17, 2025 10:40 AM PKT
"""

import os
import sys
import json
import pandas as pd
import requests
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from datetime import datetime
from typing import List, Dict, Optional
import re
import subprocess
from threading import Thread
import webbrowser
import time
import random
import logging

# Optional: YouTube API
try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    API_AVAILABLE = True
except ImportError:
    API_AVAILABLE = False

# Fallback: yt-dlp
try:
    import yt_dlp
    YTDLP_AVAILABLE = True
except ImportError:
    YTDLP_AVAILABLE = False

# Config
CONFIG_FILE = "config.json"

# ========================================
#           PROFESSIONAL 3D THEME
# ========================================
THEME = {
    "bg": "#0a0a15",
    "card": "#1a1a2e",
    "accent": "#00d4ff",
    "success": "#00ff88",
    "warning": "#ffcc00",
    "danger": "#ff3b5c",
    "text": "#e0e0ff",
    "subtext": "#a0a0cc",
    "border": "#334466",
    "terminal_bg": "#0d0d1a",
    "terminal_fg": "#00ff88",
    "terminal_select": "#334466",
}

# User Agents
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)',
    'Mozilla/5.0 (Linux; Android 13; SM-S918B)',
]

# ========================================
#           CUSTOM LOGGER WITH GUI OUTPUT
# ========================================
class GUILogger(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget
        self.setFormatter(logging.Formatter('%(asctime)s | %(message)s', '%H:%M:%S'))

    def emit(self, record):
        msg = self.format(record)
        self.text_widget.config(state='normal')
        self.text_widget.insert('end', msg + '\n')
        self.text_widget.see('end')
        self.text_widget.config(state='disabled')

# ========================================
#           AUTO UPDATE yt-dlp
# ========================================
def update_ytdlp():
    log = logging.getLogger('gui')
    try:
        log.info("Updating yt-dlp to nightly...")
        subprocess.run(["yt-dlp", "--update-to", "nightly"], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log.info("yt-dlp updated to nightly.")
    except Exception as e:
        log.warning(f"Auto-update failed: {e}")

# ========================================
#           YOUTUBE ANALYZER PRO CLASS
# ========================================
class YouTubeAnalyzerPro:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.use_api = API_AVAILABLE and bool(self.api_key)
        self.youtube = None
        if self.use_api:
            try:
                self.youtube = build('youtube', 'v3', developerKey=self.api_key)
                self.youtube.videos().list(part='id', id='dQw4w9WgXcQ').execute()
                logging.getLogger('gui').info("YouTube API connected.")
            except Exception as e:
                logging.getLogger('gui').error(f"API Error: {e}")
                self.use_api = False
        self.rtd_api = "https://returnyoutubedislikeapi.com/votes?videoId="

    def extract_video_id(self, url: str) -> Optional[str]:
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'(?:embed\/)([0-9A-Za-z_-]{11})',
            r'(?:shorts\/)([0-9A-Za-z_-]{11})',
            r'youtu\.be\/([0-9A-Za-z_-]{11})',
        ]
        for p in patterns:
            m = re.search(p, url)
            if m: return m.group(1)
        return None

    def extract_hashtags(self, text: str) -> List[str]:
        return list(set(re.findall(r'#\w+', text))) if text else []

    def format_duration(self, iso_duration: str) -> str:
        if not iso_duration or iso_duration == "P0D": return "N/A"
        try:
            d = re.sub(r'PT|H|M|S', ' ', iso_duration).strip()
            parts = [int(p) for p in d.split() if p.isdigit()]
            h, m, s = (parts + [0, 0, 0])[:3]
            return f"{h:02d}:{m:02d}:{s:02d}"
        except: return "N/A"

    def get_dislikes(self, video_id: str) -> int:
        try:
            r = requests.get(self.rtd_api + video_id, timeout=5)
            return r.json().get("dislikes", 0) if r.status_code == 200 else 0
        except: return 0

    def get_video_data_api(self, video_id: str) -> Optional[Dict]:
        try:
            req = self.youtube.videos().list(part='snippet,contentDetails,statistics', id=video_id)
            res = req.execute()
            if not res['items']: return None
            item = res['items'][0]
            sn, st, cd = item['snippet'], item['statistics'], item['contentDetails']

            views = int(st.get('viewCount', 0)) if st.get('viewCount') else 0
            likes = int(st.get('likeCount', 0)) if st.get('likeCount') else 0
            comments = int(st.get('commentCount', 0)) if st.get('commentCount') else 0
            dislikes = self.get_dislikes(video_id)
            duration = self.format_duration(cd.get('duration', ''))
            engagement = round((likes / views * 100), 2) if views > 0 else 0
            score = min(100, (views // 10000) + (likes // 1000) + int(engagement * 10))

            country = sn.get('country', 'Global')
            lang_map = {'en': 'US', 'ur': 'PK', 'hi': 'IN'}
            if country == 'Global' and sn.get('defaultLanguage'):
                country = lang_map.get(sn['defaultLanguage'][:2], 'Global')

            cat_map = {'10': 'Music', '17': 'Sports', '20': 'Gaming', '24': 'Entertainment', '25': 'News', '27': 'Education'}
            category = cat_map.get(sn.get('categoryId', ''), 'Other')

            dt = datetime.fromisoformat(sn['publishedAt'].replace('Z', '+00:00'))

            return {
                'video_id': video_id, 'title': sn['title'], 'upload_date': dt.date().isoformat(),
                'upload_time': dt.time().strftime('%H:%M:%S'), 'duration': duration, 'views': views,
                'likes': likes, 'dislikes': dislikes, 'comments': comments, 'engagement_rate_%': engagement,
                'performance_score': score, 'description': sn['description'][:500] + '...' if len(sn['description']) > 500 else sn['description'],
                'channel_title': sn['channelTitle'], 'country': country, 'category': category,
                'hashtags': self.extract_hashtags(sn['description'] + ' ' + sn['title']),
                'thumbnail': f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
                'url': f'https://www.youtube.com/watch?v={video_id}', 'download_url': None
            }
        except Exception as e:
            logging.getLogger('gui').error(f"API fetch failed: {e}")
            return None

    def get_download_url_ytdlp(self, url: str) -> Optional[str]:
        if not YTDLP_AVAILABLE: return None
        ydl_opts = {
            'quiet': True, 'no_warnings': True, 'format': 'best[height<=720][ext=mp4]/best[ext=mp4]',
            'get_url': True, 'retries': 3, 'socket_timeout': 30,
            'http_headers': {'User-Agent': random.choice(USER_AGENTS)},
            'extractor_args': {'youtube': {'skip': ['hls', 'dash', 'sabr'], 'player_client': ['android', 'ios']}}
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info.get('url') if info else None
        except Exception as e:
            logging.getLogger('gui').warning(f"Direct URL failed: {e}")
            return None

    def get_video_data_ytdlp(self, url: str) -> Optional[Dict]:
        if not YTDLP_AVAILABLE: return None
        ydl_opts = {
            'quiet': True, 'no_warnings': True, 'extract_flat': True, 'skip_download': True,
            'ignoreerrors': True, 'retries': 3, 'socket_timeout': 30,
            'http_headers': {'User-Agent': random.choice(USER_AGENTS)},
            'extractor_args': {'youtube': {'skip': ['hls', 'dash', 'sabr'], 'player_client': ['android', 'ios']}}
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info or 'entries' in info: return None
                vid = info.get('id')
                if not vid: return None
                upload = info.get('upload_date')
                dt = datetime.strptime(upload, '%Y%m%d') if upload else datetime.now()
                dur = info.get('duration', 0)
                dur_str = f"{dur//3600:02d}:{(dur%3600)//60:02d}:{dur%60:02d}" if dur else "N/A"
                views = info.get('view_count', 0) or 0
                likes = info.get('like_count', 0) or 0
                comments = info.get('comment_count', 0) or 0
                dislikes = self.get_dislikes(vid)
                engagement = round((likes / views * 100), 2) if views > 0 else 0
                score = min(100, (views // 10000) + (likes // 1000) + int(engagement * 10))
                download_url = self.get_download_url_ytdlp(url)
                return {
                    'video_id': vid, 'title': info.get('title', 'N/A'), 'upload_date': dt.date().isoformat(),
                    'upload_time': dt.time().strftime('%H:%M:%S'), 'duration': dur_str, 'views': views,
                    'likes': likes, 'dislikes': dislikes, 'comments': comments, 'engagement_rate_%': engagement,
                    'performance_score': score, 'description': (info.get('description', 'N/A')[:500] + '...') if info.get('description') else 'N/A',
                    'channel_title': info.get('uploader', 'N/A'), 'country': 'N/A',
                    'category': info.get('categories', ['Other'])[0] if info.get('categories') else 'Other',
                    'hashtags': self.extract_hashtags(info.get('description', '') + ' ' + info.get('title', '')),
                    'thumbnail': info.get('thumbnail', ''), 'url': url, 'download_url': download_url
                }
        except Exception as e:
            logging.getLogger('gui').error(f"yt-dlp failed: {e}")
            return None

    def analyze_single(self, url: str) -> Optional[Dict]:
        vid = self.extract_video_id(url)
        if not vid:
            logging.getLogger('gui').warning(f"Invalid URL: {url}")
            return None
        log = logging.getLogger('gui')
        log.info(f"Analyzing: {url}")
        if self.use_api:
            return self.get_video_data_api(vid)
        else:
            return self.get_video_data_ytdlp(url)

    def analyze_urls(self, urls: List[str]) -> List[Dict]:
        results = []
        log = logging.getLogger('gui')
        total = len(urls)
        for idx, url in enumerate(urls):
            log.info(f"[{idx+1}/{total}] Processing...")
            data = self.analyze_single(url)
            if data:
                results.append(data)
                log.info(f"Success: {data.get('title', 'N/A')[:50]}...")
            else:
                vid = self.extract_video_id(url) or 'N/A'
                results.append({
                    'video_id': vid, 'title': 'FAILED: Timeout/Blocked', 'upload_date': 'N/A',
                    'upload_time': 'N/A', 'duration': 'N/A', 'views': 0, 'likes': 0, 'dislikes': 0,
                    'comments': 0, 'engagement_rate_%': 0, 'performance_score': 0,
                    'description': 'Try API key or better network', 'channel_title': 'N/A',
                    'country': 'N/A', 'category': 'N/A', 'hashtags': [], 'thumbnail': '',
                    'url': url, 'download_url': None
                })
                log.error(f"Failed: {url}")
            if not self.use_api:
                delay = 5 + random.uniform(0, 2)
                log.info(f"Waiting {delay:.1f}s...")
                time.sleep(delay)
        return results


# ========================================
#               ULTIMATE 3D GUI v3.2 (SYNTAX FIXED)
# ========================================
class YouTubeAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Analyzer PRO - ULTIMATE v3.2 | @YLdplayer85479")
        self.root.geometry("1600x900")
        self.root.minsize(1400, 800)
        self.root.configure(bg=THEME["bg"])

        self.config = self.load_config()
        self.analyzer = None
        self.results = []

        # Setup Logger
        self.setup_logging()
        self.create_3d_styles()
        self.setup_ui()
        self.load_api_key()
        Thread(target=update_ytdlp, daemon=True).start()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        return {}

    def save_config(self):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=2)

    def setup_logging(self):
        logger = logging.getLogger('gui')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter('%(asctime)s | %(message)s', '%H:%M:%S'))
            logger.addHandler(handler)

    def create_3d_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Glass.Treeview",
                        background=THEME["card"], foreground=THEME["text"],
                        fieldbackground=THEME["card"], rowheight=32, font=('Consolas', 10))
        style.configure("Glass.Treeview.Heading",
                        font=('Segoe UI', 11, 'bold'), background=THEME["accent"], foreground="white")
        style.map("Glass.Treeview",
                  background=[('selected', THEME["accent"])], foreground=[('selected', 'white')])

    def create_rounded_rect(self, canvas, x1, y1, x2, y2, radius=12, **kwargs):
        """Draw rounded rectangle on canvas"""
        points = [
            x1 + radius, y1,
            x1 + radius, y1,
            x2 - radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1 + radius,
            x1, y1
        ]
        return canvas.create_polygon(points, **kwargs, smooth=True)

    def create_3d_button(self, parent, text, command, color):
        # FIXED: Removed duplicate 'highlightthickness=0'
        btn = tk.Canvas(parent, bg=THEME["bg"], highlightthickness=0, height=50)
        rect = self.create_rounded_rect(btn, 0, 0, 240, 50, radius=12, fill=color, outline="")
        txt = btn.create_text(120, 25, text=text, fill="white", font=('Segoe UI', 12, 'bold'))
        def enter(e): btn.itemconfig(rect, fill=self.lighten(color, 25))
        def leave(e): btn.itemconfig(rect, fill=color)
        def press(e): btn.itemconfig(rect, fill=self.darken(color, 20)); self.root.after(100, command)
        btn.bind("<Enter>", enter); btn.bind("<Leave>", leave); btn.bind("<Button-1>", press)
        btn.pack(pady=10, padx=5)
        return btn

    def lighten(self, color, p): r,g,b=[int(color[i:i+2],16)for i in(1,3,5)];return f"#{min(255,int(r+(255-r)*p/100)):02x}{min(255,int(g+(255-g)*p/100)):02x}{min(255,int(b+(255-b)*p/100)):02x}"
    def darken(self, color, p): r,g,b=[int(color[i:i+2],16)for i in(1,3,5)];return f"#{int(r*(100-p)/100):02x}{int(g*(100-p)/100):02x}{int(b*(100-p)/100):02x}"

    def setup_ui(self):
        main = tk.Frame(self.root, bg=THEME["bg"])
        main.pack(fill='both', expand=True, padx=35, pady=25)

        # Header
        header = tk.Frame(main, bg=THEME["bg"])
        header.pack(fill='x', pady=(0, 25))
        tk.Label(header, text="YouTube Analyzer PRO", font=('Segoe UI', 32, 'bold'), fg=THEME["accent"], bg=THEME["bg"]).pack(side='left')
        tk.Label(header, text="ULTIMATE v3.2 | @YLdplayer85479", font=('Segoe UI', 10), fg=THEME["subtext"], bg=THEME["bg"]).pack(side='right')

        # Tabs
        tab_control = ttk.Notebook(main)
        self.tab_analyze = tk.Frame(tab_control, bg=THEME["bg"])
        self.tab_results = tk.Frame(tab_control, bg=THEME["bg"])
        tab_control.add(self.tab_analyze, text='   Analyze & Log   ')
        tab_control.add(self.tab_results, text='   Results Table   ')
        tab_control.pack(expand=1, fill='both')

        self.setup_analyze_tab()
        self.setup_results_tab()

    def setup_analyze_tab(self):
        frame = self.tab_analyze
        left = tk.Frame(frame, bg=THEME["bg"])
        left.pack(side='left', fill='both', expand=True, padx=(0,15))
        right = tk.Frame(frame, bg=THEME["bg"])
        right.pack(side='right', fill='both', expand=True, padx=(15,0))

        # === LEFT: INPUT ===
        input_card = tk.LabelFrame(left, text=" Input Configuration ", fg=THEME["text"], bg=THEME["card"], font=('Segoe UI', 12, 'bold'), relief='flat', bd=2)
        input_card.pack(fill='both', expand=True, pady=(0,15))

        # API
        api_f = tk.Frame(input_card, bg=THEME["card"])
        api_f.pack(fill='x', padx=20, pady=15)
        tk.Label(api_f, text="YouTube API Key:", fg=THEME["subtext"], bg=THEME["card"], font=('Segoe UI', 10)).pack(anchor='w')
        api_in = tk.Frame(api_f, bg=THEME["card"])
        api_in.pack(fill='x', pady=5)
        self.api_entry = tk.Entry(api_in, bg=THEME["terminal_bg"], fg=THEME["text"], insertbackground=THEME["accent"], font=('Consolas', 11))
        self.api_entry.pack(side='left', fill='x', expand=True)
        self.create_3d_button(api_in, "Save & Test", self.save_api_key, THEME["accent"])

        # URLs
        url_f = tk.Frame(input_card, bg=THEME["card"])
        url_f.pack(fill='x', padx=20, pady=10)
        tk.Label(url_f, text="Single URL:", fg=THEME["subtext"], bg=THEME["card"], font=('Segoe UI', 10)).pack(anchor='w')
        self.url_entry = tk.Entry(url_f, bg=THEME["terminal_bg"], fg=THEME["text"], insertbackground=THEME["accent"], font=('Consolas', 11))
        self.url_entry.pack(fill='x', pady=5)

        file_f = tk.Frame(input_card, bg=THEME["card"])
        file_f.pack(fill='x', padx=20, pady=10)
        tk.Label(file_f, text="Bulk TXT File:", fg=THEME["subtext"], bg=THEME["card"], font=('Segoe UI', 10)).pack(anchor='w')
        file_in = tk.Frame(file_f, bg=THEME["card"])
        file_in.pack(fill='x', pady=5)
        self.file_entry = tk.Entry(file_in, bg=THEME["terminal_bg"], fg=THEME["text"], font=('Consolas', 11))
        self.file_entry.pack(side='left', fill='x', expand=True)
        self.create_3d_button(file_in, "Browse", self.browse_file, THEME["warning"])

        # Start Button
        btn_f = tk.Frame(left, bg=THEME["bg"])
        btn_f.pack(pady=20)
        self.analyze_btn = self.create_3d_button(btn_f, "START BULK ANALYSIS", self.start_analysis, THEME["success"])

        # Status
        self.status_label = tk.Label(left, text="Ready", fg=THEME["subtext"], bg=THEME["bg"], font=('Segoe UI', 11))
        self.status_label.pack(pady=5)
        self.progress = ttk.Progressbar(left, mode='indeterminate', length=400)
        self.progress.pack(pady=10)

        # === RIGHT: TERMINAL LOG ===
        log_card = tk.LabelFrame(right, text=" Live Terminal Log ", fg=THEME["text"], bg=THEME["card"], font=('Segoe UI', 12, 'bold'), relief='flat', bd=2)
        log_card.pack(fill='both', expand=True)

        self.log_text = scrolledtext.ScrolledText(log_card, bg=THEME["terminal_bg"], fg=THEME["terminal_fg"],
                                                 font=('Consolas', 10), state='disabled', wrap='word',
                                                 selectbackground=THEME["terminal_select"])
        self.log_text.pack(fill='both', expand=True, padx=15, pady=15)

        # Setup GUI Logger
        gui_handler = GUILogger(self.log_text)
        logging.getLogger('gui').addHandler(gui_handler)

    def setup_results_tab(self):
        frame = self.tab_results

        action_bar = tk.Frame(frame, bg=THEME["card"], relief='flat', bd=2)
        action_bar.pack(fill='x', pady=15, padx=20)
        actions = tk.Frame(action_bar, bg=THEME["card"])
        actions.pack(pady=12)

        self.create_3d_button(actions, "Export CSV", lambda: self.export('csv'), THEME["success"]).pack(side='left', padx=8)
        self.create_3d_button(actions, "Export Excel", lambda: self.export('xlsx'), THEME["accent"]).pack(side='left', padx=8)
        self.create_3d_button(actions, "Export JSON", lambda: self.export('json'), THEME["warning"]).pack(side='left', padx=8)
        self.create_3d_button(actions, "Download All", self.download_all, "#e91e63").pack(side='right', padx=8)
        self.create_3d_button(actions, "Clear Results", self.clear_results, THEME["danger"]).pack(side='right', padx=8)

        table_frame = tk.Frame(frame, bg=THEME["bg"])
        table_frame.pack(fill='both', expand=True, padx=20, pady=10)

        self.tree = ttk.Treeview(table_frame, style="Glass.Treeview", columns=(
            'title', 'views', 'likes', 'duration', 'country', 'score', 'eng', 'download'
        ), show='headings')

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')
        hsb.pack(side='bottom', fill='x')

        headers = [
            ('title', 'Title', 450, 'w'),
            ('views', 'Views', 110, 'e'),
            ('likes', 'Likes', 110, 'e'),
            ('duration', 'Duration', 100, 'center'),
            ('country', 'Country', 90, 'center'),
            ('score', 'Score', 80, 'e'),
            ('eng', 'Eng %', 90, 'e'),
            ('download', 'Download', 160, 'center'),
        ]
        for col_id, text, width, anchor in headers:
            self.tree.heading(col_id, text=text)
            self.tree.column(col_id, width=width, anchor=anchor)

        self.tree.bind('<Double-1>', self.open_download_link)

    def load_api_key(self):
        key = self.config.get("api_key", "")
        self.api_entry.insert(0, key)
        self.analyzer = YouTubeAnalyzerPro(key)
        self.update_status()

    def update_status(self):
        log = logging.getLogger('gui')
        if self.analyzer and self.analyzer.use_api:
            self.status_label.config(text="API Mode: Instant & Reliable", fg=THEME["success"])
            log.info("API Mode Active")
        elif YTDLP_AVAILABLE:
            self.status_label.config(text="yt-dlp Mode: 5s delay per video", fg=THEME["warning"])
            log.info("yt-dlp Fallback Mode")
        else:
            self.status_label.config(text="Install yt-dlp", fg=THEME["danger"])

    def save_api_key(self):
        key = self.api_entry.get().strip()
        if not key:
            messagebox.showwarning("Missing", "Enter API Key!")
            return
        self.config["api_key"] = key
        self.save_config()
        self.analyzer = YouTubeAnalyzerPro(key)
        self.update_status()
        messagebox.showinfo("Success", "API Key Saved!")

    def browse_file(self):
        path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if path:
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, path)

    def start_analysis(self):
        if not self.analyzer:
            messagebox.showerror("Error", "Save API Key!")
            return
        self.analyze_btn.itemconfig("bg", fill=self.darken(THEME["success"], 20))
        self.progress.start(10)
        Thread(target=self.run_analysis, daemon=True).start()

    def run_analysis(self):
        urls = []
        url = self.url_entry.get().strip()
        file_path = self.file_entry.get().strip()

        if url: urls.append(url)
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    urls.extend([line.strip() for line in f if line.strip() and 'youtube' in line])
            except Exception as e:
                logging.getLogger('gui').error(f"File read error: {e}")
                self.root.after(0, self.stop_analysis)
                return

        if not urls:
            logging.getLogger('gui').warning("No URLs provided.")
            self.root.after(0, lambda: messagebox.showwarning("No Input", "Enter URL or file!"))
            self.root.after(0, self.stop_analysis)
            return

        logging.getLogger('gui').info(f"Starting analysis of {len(urls)} videos...")
        self.results = self.analyzer.analyze_urls(urls)
        self.root.after(0, self.show_results)
        self.root.after(0, self.stop_analysis)
        logging.getLogger('gui').info("Analysis completed.")

    def show_results(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for r in self.results:
            title = r.get('title', 'N/A')[:70] + '...' if len(r.get('title', '')) > 70 else r.get('title', 'N/A')
            views = f"{r.get('views', 0)//1000}K" if r.get('views', 0) >= 1000 else str(r.get('views', 0))
            likes = f"{r.get('likes', 0)//1000}K" if r.get('likes', 0) >= 1000 else str(r.get('likes', 0))
            dl_text = "Download" if r.get('download_url') else "N/A"
            self.tree.insert('', 'end', values=(
                title, views, likes, r.get('duration', 'N/A'), r.get('country', 'N/A'),
                r.get('performance_score', 0), f"{r.get('engagement_rate_%', 0):.1f}%", dl_text
            ), tags=(r.get('download_url'),))
        messagebox.showinfo("Done", f"Analyzed {len(self.results)} videos!")

    def stop_analysis(self):
        self.progress.stop()
        self.analyze_btn.itemconfig("bg", fill=THEME["success"])

    def clear_results(self):
        self.results = []
        for item in self.tree.get_children():
            self.tree.delete(item)
        logging.getLogger('gui').info("Results cleared.")

    def open_download_link(self, event):
        item = self.tree.selection()
        if not item: return
        dl_url = self.tree.item(item[0], "tags")[0]
        if dl_url:
            webbrowser.open(dl_url)
        else:
            messagebox.showinfo("No Link", "Direct download not available.")

    def download_all(self):
        if not self.results: return
        folder = filedialog.askdirectory()
        if not folder: return
        logging.getLogger('gui').info(f"Downloading all to: {folder}")
        Thread(target=self._download_all, args=(folder,), daemon=True).start()

    def _download_all(self, folder):
        for r in self.results:
            if r.get('download_url'):
                try:
                    subprocess.run(["yt-dlp", "-o", f"{folder}/%(title)s.%(ext)s", r['download_url']], check=True)
                except: pass

    def export(self, format_type):
        if not self.results:
            messagebox.showwarning("No Data", "Analyze first!")
            return
        path = filedialog.asksaveasfilename(defaultextension=f".{format_type}")
        if not path: return
        df = pd.DataFrame(self.results)
        df['hashtags'] = df['hashtags'].apply(lambda x: ', '.join(x) if isinstance(x, list) else '')
        if format_type == 'csv':
            df.to_csv(path, index=False, encoding='utf-8')
        elif format_type == 'xlsx':
            df.to_excel(path, index=False)
        elif format_type == 'json':
            df.to_json(path, orient='records', indent=2, force_ascii=False)
        logging.getLogger('gui').info(f"Exported: {path}")
        messagebox.showinfo("Exported", f"Saved to {path}")


# ========================================
#                  RUN APP
# ========================================
if __name__ == '__main__':
    root = tk.Tk()
    app = YouTubeAnalyzerGUI(root)
    root.mainloop()
