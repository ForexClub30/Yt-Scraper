"""
YOUTUBE ANALYZER PRO - PROFESSIONAL TKINTER GUI
Deep Analysis | Views, Likes, Duration, Country, Engagement
Modern UI | Drag & Drop | Export | Auto-Save API Key

Author: Grok (xAI) | @YLdplayer85479 (Pakistan)
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
from threading import Thread
from tkinterdnd2 import DND_FILES, TkinterDnD

# Optional: YouTube API
try:
    from googleapiclient.discovery import build
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
THEME = {
    "bg": "#1e1e1e",
    "fg": "#ffffff",
    "entry_bg": "#2d2d2d",
    "btn_bg": "#007acc",
    "btn_fg": "#ffffff",
    "accent": "#00bfff",
    "success": "#28a745",
    "danger": "#dc3545"
}


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
            except:
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
            if m:
                return m.group(1)
        return None

    def extract_hashtags(self, text: str) -> List[str]:
        return list(set(re.findall(r'#\w+', text)))

    def format_duration(self, iso_duration: str) -> str:
        if not iso_duration or iso_duration == "P0D":
            return "N/A"
        d = iso_duration.replace("PT", "")
        h, m, s = 0, 0, 0
        if 'H' in d: h, d = d.split('H')
        if 'M' in d: m, d = d.split('M')
        if 'S' in d: s = d.replace('S', '')
        try:
            return f"{int(h):02d}:{int(m):02d}:{int(s):02d}"
        except:
            return "N/A"

    def get_dislikes(self, video_id: str) -> int:
        try:
            r = requests.get(self.rtd_api + video_id, timeout=5)
            return r.json().get("dislikes", 0) if r.status_code == 200 else 0
        except:
            return 0

    def get_video_data_api(self, video_id: str) -> Optional[Dict]:
        try:
            req = self.youtube.videos().list(
                part='snippet,contentDetails,statistics',
                id=video_id
            )
            res = req.execute()
            if not res['items']: return None
            item = res['items'][0]
            sn, st, cd = item['snippet'], item['statistics'], item['contentDetails']

            views = int(st.get('viewCount', 0))
            likes = int(st.get('likeCount', 0))
            comments = int(st.get('commentCount', 0))
            dislikes = self.get_dislikes(video_id)
            duration = self.format_duration(cd.get('duration', ''))
            engagement = round((likes / views) * 100, 2) if views > 0 else 0

            # Performance Score
            score = 0
            if views > 1_000_000: score += 30
            elif views > 100_000: score += 20
            elif views > 10_000: score += 10
            if engagement > 5: score += 20
            elif engagement > 2: score += 10
            if likes > 10_000: score += 20
            score = min(score, 100)

            # Country
            country = sn.get('country', 'N/A')
            if country == 'N/A' and sn.get('defaultLanguage'):
                lang_map = {'en': 'US', 'ur': 'PK', 'hi': 'IN', 'ar': 'SA', 'es': 'ES'}
                country = lang_map.get(sn['defaultLanguage'][:2], 'Global')

            cat_map = {
                '10': 'Music', '17': 'Sports', '20': 'Gaming', '22': 'Blogs',
                '24': 'Entertainment', '25': 'News', '27': 'Education', '28': 'Tech'
            }
            category = cat_map.get(sn.get('categoryId', ''), 'Other')

            dt = datetime.fromisoformat(sn['publishedAt'].replace('Z', '+00:00'))

            return {
                'video_id': video_id,
                'title': sn['title'],
                'upload_date': dt.date().isoformat(),
                'upload_time': dt.time().strftime('%H:%M:%S'),
                'duration': duration,
                'views': views,
                'likes': likes,
                'dislikes': dislikes,
                'comments': comments,
                'engagement_rate_%': engagement,
                'performance_score': score,
                'description': sn['description'],
                'channel_title': sn['channelTitle'],
                'country': country,
                'category': category,
                'hashtags': self.extract_hashtags(sn['description'] + ' ' + sn['title']),
                'thumbnail': f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
                'url': f'https://www.youtube.com/watch?v={video_id}'
            }
        except Exception as e:
            return None

    def get_video_data_ytdlp(self, url: str) -> Optional[Dict]:
        if not YTDLP_AVAILABLE: return None
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info: return None
                vid = info.get('id')
                upload = info.get('upload_date')
                dt = datetime.strptime(upload, '%Y%m%d') if upload else None
                dur = info.get('duration', 0)
                dur_str = f"{dur//3600:02d}:{(dur%3600)//60:02d}:{dur%60:02d}" if dur else "N/A"
                views = info.get('view_count', 0)
                likes = info.get('like_count', 0)
                dislikes = self.get_dislikes(vid) if vid else 0
                return {
                    'video_id': vid,
                    'title': info.get('title', 'N/A'),
                    'upload_date': dt.date().isoformat() if dt else 'N/A',
                    'upload_time': '00:00:00',
                    'duration': dur_str,
                    'views': views,
                    'likes': likes,
                    'dislikes': dislikes,
                    'comments': info.get('comment_count', 0),
                    'engagement_rate_%': round((likes/views)*100, 2) if views else 0,
                    'performance_score': 0,
                    'description': info.get('description', 'N/A'),
                    'channel_title': info.get('uploader', 'N/A'),
                    'country': 'N/A',
                    'category': info.get('category', 'N/A'),
                    'hashtags': self.extract_hashtags(info.get('description', '') + ' ' + info.get('title', '')),
                    'thumbnail': info.get('thumbnail', ''),
                    'url': url
                }
        except:
            return None

    def analyze_single(self, url: str) -> Optional[Dict]:
        vid = self.extract_video_id(url)
        if not vid: return None
        return self.get_video_data_api(vid) if self.use_api else self.get_video_data_ytdlp(url)

    def analyze_urls(self, urls: List[str]) -> List[Dict]:
        results = []
        for url in urls:
            data = self.analyze_single(url)
            if data:
                results.append(data)
            else:
                vid = self.extract_video_id(url) or 'N/A'
                results.append({'video_id': vid, 'title': 'ERROR', 'url': url, 'views': 0})
        return results


# ========================================
#               TKINTER GUI APP
# ========================================
class YouTubeAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Analyzer PRO - @YLdplayer85479")
        self.root.geometry("1200x700")
        self.root.configure(bg=THEME["bg"])
        self.root.minsize(1000, 600)

        # Load config
        self.config = self.load_config()
        self.analyzer = None

        self.setup_ui()
        self.load_api_key()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        return {}

    def save_config(self):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=2)

    def setup_ui(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton", padding=6, font=('Segoe UI', 10))
        style.configure("Treeview", background=THEME["entry_bg"], foreground="white", fieldbackground=THEME["entry_bg"])
        style.map('Treeview', background=[('selected', THEME["accent"])])

        # Header
        header = tk.Frame(self.root, bg=THEME["bg"])
        header.pack(fill='x', pady=10)
        tk.Label(header, text="YouTube Analyzer PRO", font=('Segoe UI', 18, 'bold'), fg=THEME["accent"], bg=THEME["bg"]).pack(side='left', padx=20)
        tk.Label(header, text="Pakistan", font=('Segoe UI', 10), fg="#888", bg=THEME["bg"]).pack(side='right', padx=20)

        # Tabs
        tab_control = ttk.Notebook(self.root)
        self.tab_analyze = ttk.Frame(tab_control)
        self.tab_results = ttk.Frame(tab_control)
        tab_control.add(self.tab_analyze, text='Analyze')
        tab_control.add(self.tab_results, text='Results')
        tab_control.pack(expand=1, fill='both', padx=20, pady=10)

        self.setup_analyze_tab()
        self.setup_results_tab()

    def setup_analyze_tab(self):
        frame = self.tab_analyze

        # API Key
        api_frame = tk.LabelFrame(frame, text="API Key (Recommended)", fg=THEME["fg"], bg=THEME["bg"], padx=10, pady=10)
        api_frame.pack(fill='x', padx=20, pady=10)
        self.api_entry = tk.Entry(api_frame, bg=THEME["entry_bg"], fg=THEME["fg"], insertbackground=THEME["fg"], width=50)
        self.api_entry.pack(side='left', padx=5)
        tk.Button(api_frame, text="Save", command=self.save_api_key, bg=THEME["btn_bg"], fg=THEME["btn_fg"]).pack(side='left', padx=5)
        tk.Label(api_frame, text="Get Free Key: console.cloud.google.com", fg="#888", bg=THEME["bg"]).pack(side='left', padx=10)

        # Input
        input_frame = tk.LabelFrame(frame, text="Input", fg=THEME["fg"], bg=THEME["bg"], padx=10, pady=10)
        input_frame.pack(fill='x', padx=20, pady=10)

        tk.Label(input_frame, text="Single URL:", fg=THEME["fg"], bg=THEME["bg"]).grid(row=0, column=0, sticky='w', pady=5)
        self.url_entry = tk.Entry(input_frame, bg=THEME["entry_bg"], fg=THEME["fg"], insertbackground=THEME["fg"], width=70)
        self.url_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(input_frame, text="Or TXT File:", fg=THEME["fg"], bg=THEME["bg"]).grid(row=1, column=0, sticky='w', pady=5)
        self.file_entry = tk.Entry(input_frame, bg=THEME["entry_bg"], fg=THEME["fg"], width=50)
        self.file_entry.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        tk.Button(input_frame, text="Browse", command=self.browse_file).grid(row=1, column=1, padx=(420, 5), pady=5)
        self.file_entry.drop_target_register(DND_FILES)
        self.file_entry.dnd_bind('<<Drop>>', self.drop_file)

        # Analyze Button
        btn_frame = tk.Frame(frame, bg=THEME["bg"])
        btn_frame.pack(pady=20)
        self.analyze_btn = tk.Button(btn_frame, text="START ANALYSIS", font=('Segoe UI', 12, 'bold'),
                                     command=self.start_analysis, bg=THEME["success"], fg="white", width=20)
        self.analyze_btn.pack()

        # Progress
        self.progress = ttk.Progressbar(frame, mode='indeterminate')
        self.progress.pack(fill='x', padx=20, pady=10)

    def setup_results_tab(self):
        frame = self.tab_results

        # Export Buttons
        export_frame = tk.Frame(frame, bg=THEME["bg"])
        export_frame.pack(fill='x', pady=10)
        tk.Button(export_frame, text="Export CSV", command=lambda: self.export('csv')).pack(side='left', padx=10)
        tk.Button(export_frame, text="Export Excel", command=lambda: self.export('xlsx')).pack(side='left', padx=5)
        tk.Button(export_frame, text="Export JSON", command=lambda: self.export('json')).pack(side='left', padx=5)

        # Table
        tree_frame = tk.Frame(frame)
        tree_frame.pack(fill='both', expand=True, padx=20, pady=10)
        self.tree = ttk.Treeview(tree_frame, columns=(
            'title', 'views', 'likes', 'duration', 'country', 'score', 'eng'
        ), show='headings')
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')
        hsb.pack(side='bottom', fill='x')

        self.tree.heading('title', text='Title')
        self.tree.heading('views', text='Views')
        self.tree.heading('likes', text='Likes')
        self.tree.heading('duration', text='Duration')
        self.tree.heading('country', text='Country')
        self.tree.heading('score', text='Score')
        self.tree.heading('eng', text='Eng %')

        self.tree.column('title', width=400)
        self.tree.column('views', width=100, anchor='e')
        self.tree.column('likes', width=80, anchor='e')
        self.tree.column('duration', width=80)
        self.tree.column('country', width=80)
        self.tree.column('score', width=60, anchor='e')
        self.tree.column('eng', width=60, anchor='e')

        self.results = []

    def load_api_key(self):
        key = self.config.get("api_key", "")
        self.api_entry.insert(0, key)
        self.analyzer = YouTubeAnalyzerPro(key)

    def save_api_key(self):
        key = self.api_entry.get().strip()
        self.config["api_key"] = key
        self.save_config()
        self.analyzer = YouTubeAnalyzerPro(key)
        messagebox.showinfo("Success", "API Key Saved!")

    def browse_file(self):
        path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if path:
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, path)

    def drop_file(self, event):
        path = event.data.strip('{}')
        if path.endswith('.txt'):
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, path)

    def start_analysis(self):
        self.analyze_btn.config(state='disabled')
        self.progress.start()
        Thread(target=self.run_analysis, daemon=True).start()

    def run_analysis(self):
        urls = []
        url = self.url_entry.get().strip()
        file_path = self.file_entry.get().strip()

        if url:
            urls.append(url)
        if file_path and os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                urls.extend([line.strip() for line in f if line.strip() and 'youtube' in line])

        if not urls:
            self.root.after(0, lambda: messagebox.showwarning("Input Error", "Enter URL or TXT file!"))
            self.root.after(0, self.stop_analysis)
            return

        self.results = self.analyzer.analyze_urls(urls)
        self.root.after(0, self.show_results)
        self.root.after(0, self.stop_analysis)

    def show_results(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for r in self.results:
            views = f"{r['views']//1000}K" if r['views'] >= 1000 else str(r['views'])
            likes = f"{r['likes']//1000}K" if r['likes'] >= 1000 else str(r['likes'])
            self.tree.insert('', 'end', values=(
                r['title'][:60] + '...' if len(r['title']) > 60 else r['title'],
                views, likes, r['duration'], r['country'], r['performance_score'], r['engagement_rate_%']
            ))

    def stop_analysis(self):
        self.progress.stop()
        self.analyze_btn.config(state='normal')

    def export(self, format_type):
        if not self.results:
            messagebox.showwarning("No Data", "Analyze videos first!")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=f".{format_type}",
            filetypes=[(f"{format_type.upper()} Files", f"*.{format_type}")]
        )
        if not path: return

        df = pd.DataFrame(self.results)
        df['hashtags'] = df['hashtags'].apply(lambda x: ', '.join(x))
        if format_type == 'csv':
            df.to_csv(path, index=False)
        elif format_type == 'xlsx':
            df.to_excel(path, index=False)
        elif format_type == 'json':
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
        messagebox.showinfo("Exported", f"Saved to {path}")


# ========================================
#                  RUN APP
# ========================================
if __name__ == '__main__':
    if not API_AVAILABLE and not YTDLP_AVAILABLE:
        messagebox.showerror("Missing", "Install: pip install google-api-python-client yt-dlp pandas openpyxl requests tkinterdnd2")
        sys.exit(1)

    root = TkinterDnD.Tk()
    app = YouTubeAnalyzerGUI(root)
    root.mainloop()
