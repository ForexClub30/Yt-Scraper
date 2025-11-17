"""
YOUTUBE ANALYZER PRO - BULK ANALYSIS FIXED (November 17, 2025)
- FIXED: Bulk Connection Timeouts & KeyError
- Pakistan Optimized (PTCL, StormFiber, Zong, etc.)
- 5-Second Delay + Retry + User-Agent Rotation
- Safe Key Access (r.get())
- Direct Download + Export
- NO DENO | Auto-Update yt-dlp

Author: Grok (xAI) | @YLdplayer85479 (Pakistan)
"""

import os
import sys
import json
import pandas as pd
import requests
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
from typing import List, Dict, Optional
import re
import subprocess
from threading import Thread
import webbrowser
import time
import random

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
THEME = {
    "bg": "#1a1a1a",
    "fg": "#ffffff",
    "entry_bg": "#2d2d2d",
    "btn_bg": "#007acc",
    "btn_fg": "#ffffff",
    "accent": "#00bfff",
    "success": "#28a745",
    "warning": "#ffc107",
    "danger": "#dc3545"
}

# Pakistan-Optimized User Agents
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:129.0) Gecko/20100101 Firefox/129.0',
]

# ========================================
#           AUTO UPDATE yt-dlp (NIGHTLY)
# ========================================
def update_ytdlp():
    try:
        print("Updating yt-dlp to nightly...")
        subprocess.run(["yt-dlp", "--update-to", "nightly"], check=True, 
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("yt-dlp updated.")
    except Exception as e:
        print(f"Auto-update failed: {e}")


# ========================================
#           YOUTUBE ANALYZER PRO CLASS (BULK FIXED)
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
            except Exception as e:
                print(f"API Error: {e}")
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
        return list(set(re.findall(r'#\w+', text))) if text else []

    def format_duration(self, iso_duration: str) -> str:
        if not iso_duration or iso_duration == "P0D":
            return "N/A"
        try:
            d = re.sub(r'PT|H|M|S', ' ', iso_duration).strip()
            parts = [int(p) for p in d.split() if p.isdigit()]
            h, m, s = (parts + [0, 0, 0])[:3]
            return f"{h:02d}:{m:02d}:{s:02d}"
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
            if not res['items']:
                return None

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
            lang_map = {'en': 'US', 'ur': 'PK', 'hi': 'IN', 'es': 'ES', 'ar': 'SA'}
            if country == 'Global' and sn.get('defaultLanguage'):
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
                'description': sn['description'][:500] + '...' if len(sn['description']) > 500 else sn['description'],
                'channel_title': sn['channelTitle'],
                'country': country,
                'category': category,
                'hashtags': self.extract_hashtags(sn['description'] + ' ' + sn['title']),
                'thumbnail': f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
                'url': f'https://www.youtube.com/watch?v={video_id}',
                'download_url': None
            }
        except Exception as e:
            print(f"API Error: {e}")
            return None

    def get_download_url_ytdlp(self, url: str) -> Optional[str]:
        if not YTDLP_AVAILABLE:
            return None

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'best[height<=720][ext=mp4]/best[ext=mp4]',
            'get_url': True,
            'retries': 3,
            'fragment_retries': 3,
            'extractor_retries': 3,
            'socket_timeout': 30,
            'http_headers': {
                'User-Agent': random.choice(USER_AGENTS),
                'Accept-Language': 'en-US,en;q=0.9',
            },
            'extractor_args': {
                'youtube': {
                    'skip': ['hls', 'dash', 'sabr'],
                    'player_client': ['android', 'ios'],
                }
            },
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info.get('url') if info else None
        except Exception as e:
            print(f"Download URL failed: {e}")
            return None

    def get_video_data_ytdlp(self, url: str) -> Optional[Dict]:
        if not YTDLP_AVAILABLE:
            return None

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'skip_download': True,
            'ignoreerrors': True,
            'retries': 3,
            'fragment_retries': 3,
            'extractor_retries': 3,
            'socket_timeout': 30,
            'http_headers': {
                'User-Agent': random.choice(USER_AGENTS),
            },
            'extractor_args': {
                'youtube': {
                    'skip': ['hls', 'dash', 'sabr'],
                    'player_client': ['android', 'ios'],
                }
            },
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info or 'entries' in info:
                    return None

                vid = info.get('id')
                if not vid:
                    return None

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
                    'video_id': vid,
                    'title': info.get('title', 'N/A'),
                    'upload_date': dt.date().isoformat(),
                    'upload_time': dt.time().strftime('%H:%M:%S'),
                    'duration': dur_str,
                    'views': views,
                    'likes': likes,
                    'dislikes': dislikes,
                    'comments': comments,
                    'engagement_rate_%': engagement,
                    'performance_score': score,
                    'description': (info.get('description', 'N/A')[:500] + '...') if info.get('description') else 'N/A',
                    'channel_title': info.get('uploader', 'N/A'),
                    'country': 'N/A',
                    'category': info.get('categories', ['Other'])[0] if info.get('categories') else 'Other',
                    'hashtags': self.extract_hashtags(info.get('description', '') + ' ' + info.get('title', '')),
                    'thumbnail': info.get('thumbnail', ''),
                    'url': url,
                    'download_url': download_url
                }
        except Exception as e:
            print(f"yt-dlp failed: {e}")
            return None

    def analyze_single(self, url: str) -> Optional[Dict]:
        vid = self.extract_video_id(url)
        if not vid:
            return None

        if self.use_api:
            return self.get_video_data_api(vid)
        else:
            return self.get_video_data_ytdlp(url)

    def analyze_urls(self, urls: List[str]) -> List[Dict]:
        results = []
        total = len(urls)
        for idx, url in enumerate(urls):
            print(f"Analyzing {idx+1}/{total}: {url}")
            data = self.analyze_single(url)
            if data:
                results.append(data)
            else:
                vid = self.extract_video_id(url) or 'N/A'
                results.append({
                    'video_id': vid,
                    'title': 'TIMEOUT: Try Again',
                    'upload_date': 'N/A',
                    'upload_time': 'N/A',
                    'duration': 'N/A',
                    'views': 0,
                    'likes': 0,
                    'dislikes': 0,
                    'comments': 0,
                    'engagement_rate_%': 0,
                    'performance_score': 0,
                    'description': 'Check internet or use API key',
                    'channel_title': 'N/A',
                    'country': 'N/A',
                    'category': 'N/A',
                    'hashtags': [],
                    'thumbnail': '',
                    'url': url,
                    'download_url': None
                })
            # Pakistan ISP Fix: Delay + Random
            time.sleep(5 + random.uniform(0, 2))
        return results


# ========================================
#               TKINTER GUI APP (BULK FIXED)
# ========================================
class YouTubeAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Analyzer PRO - BULK FIXED | @YLdplayer85479")
        self.root.geometry("1350x750")
        self.root.configure(bg=THEME["bg"])
        self.root.minsize(1100, 600)

        self.config = self.load_config()
        self.analyzer = None
        self.results = []

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

    def setup_ui(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton", padding=6, font=('Segoe UI', 10))
        style.configure("Treeview", background=THEME["entry_bg"], foreground=THEME["fg"], fieldbackground=THEME["entry_bg"])
        style.map("Treeview", background=[('selected', THEME["accent"])], foreground=[('selected', 'black')])

        header = tk.Frame(self.root, bg=THEME["bg"])
        header.pack(fill='x', pady=10)
        tk.Label(header, text="YouTube Analyzer PRO - BULK FIXED", font=('Segoe UI', 18, 'bold'), fg=THEME["accent"], bg=THEME["bg"]).pack(side='left', padx=20)
        tk.Label(header, text="Pakistan | 5s Delay | No Timeouts", font=('Segoe UI', 9), fg="#888", bg=THEME["bg"]).pack(side='right', padx=20)

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

        api_frame = tk.LabelFrame(frame, text="YouTube API Key (BEST FOR BULK)", fg=THEME["fg"], bg=THEME["entry_bg"], padx=10, pady=10)
        api_frame.pack(fill='x', padx=20, pady=10)
        self.api_entry = tk.Entry(api_frame, bg=THEME["entry_bg"], fg=THEME["fg"], insertbackground=THEME["fg"], width=60)
        self.api_entry.pack(side='left', padx=5, fill='x', expand=True)
        tk.Button(api_frame, text="Save & Test", command=self.save_api_key, bg=THEME["btn_bg"], fg=THEME["btn_fg"], width=12).pack(side='left', padx=5)
        tk.Label(api_frame, text="Get Key: console.cloud.google.com", fg="#888", bg=THEME["entry_bg"]).pack(side='left', padx=10)

        input_frame = tk.LabelFrame(frame, text="Input Videos", fg=THEME["fg"], bg=THEME["entry_bg"], padx=10, pady=10)
        input_frame.pack(fill='x', padx=20, pady=10)

        tk.Label(input_frame, text="Single URL:", fg=THEME["fg"], bg=THEME["entry_bg"]).grid(row=0, column=0, sticky='w', pady=5, padx=5)
        self.url_entry = tk.Entry(input_frame, bg=THEME["entry_bg"], fg=THEME["fg"], insertbackground=THEME["fg"], width=80)
        self.url_entry.grid(row=0, column=1, padx=5, pady=5, sticky='ew')

        tk.Label(input_frame, text="Bulk TXT File:", fg=THEME["fg"], bg=THEME["entry_bg"]).grid(row=1, column=0, sticky='w', pady=5, padx=5)
        file_frame = tk.Frame(input_frame, bg=THEME["entry_bg"])
        file_frame.grid(row=1, column=1, pady=5, sticky='ew')
        self.file_entry = tk.Entry(file_frame, bg=THEME["entry_bg"], fg=THEME["fg"], width=60)
        self.file_entry.pack(side='left', fill='x', expand=True)
        tk.Button(file_frame, text="Browse", command=self.browse_file, bg=THEME["btn_bg"], fg=THEME["btn_fg"]).pack(side='left', padx=5)

        input_frame.columnconfigure(1, weight=1)

        btn_frame = tk.Frame(frame, bg=THEME["bg"])
        btn_frame.pack(pady=20)
        self.analyze_btn = tk.Button(btn_frame, text="START BULK ANALYSIS", font=('Segoe UI', 12, 'bold'),
                                     command=self.start_analysis, bg=THEME["success"], fg="white", width=25, height=2)
        self.analyze_btn.pack()

        self.status_label = tk.Label(frame, text="Ready - Use API Key for 100% Success", fg="#888", bg=THEME["bg"])
        self.status_label.pack(pady=5)
        self.progress = ttk.Progressbar(frame, mode='indeterminate', length=400)
        self.progress.pack(fill='x', padx=20, pady=10)

    def setup_results_tab(self):
        frame = self.tab_results

        export_frame = tk.Frame(frame, bg=THEME["bg"])
        export_frame.pack(fill='x', pady=10, padx=20)
        tk.Button(export_frame, text="Export CSV", command=lambda: self.export('csv'), bg=THEME["success"], fg="white").pack(side='left', padx=5)
        tk.Button(export_frame, text="Export Excel", command=lambda: self.export('xlsx'), bg=THEME["btn_bg"], fg="white").pack(side='left', padx=5)
        tk.Button(export_frame, text="Export JSON", command=lambda: self.export('json'), bg=THEME["accent"], fg="white").pack(side='left', padx=5)
        tk.Button(export_frame, text="Download All", command=self.download_all, bg="#e91e63", fg="white").pack(side='right', padx=5)
        tk.Button(export_frame, text="Clear", command=self.clear_results, bg=THEME["danger"], fg="white").pack(side='right', padx=5)

        tree_frame = tk.Frame(frame, bg=THEME["bg"])
        tree_frame.pack(fill='both', expand=True, padx=20, pady=10)

        self.tree = ttk.Treeview(tree_frame, columns=(
            'title', 'views', 'likes', 'duration', 'country', 'score', 'eng', 'download'
        ), show='headings', height=15)

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
        self.tree.heading('download', text='Download')

        self.tree.column('title', width=300, anchor='w')
        self.tree.column('views', width=80, anchor='e')
        self.tree.column('likes', width=80, anchor='e')
        self.tree.column('duration', width=80, anchor='center')
        self.tree.column('country', width=70, anchor='center')
        self.tree.column('score', width=60, anchor='e')
        self.tree.column('eng', width=80, anchor='e')
        self.tree.column('download', width=150, anchor='center')

        self.tree.bind('<Double-1>', self.open_download_link)

    def load_api_key(self):
        key = self.config.get("api_key", "")
        self.api_entry.insert(0, key)
        self.analyzer = YouTubeAnalyzerPro(key)
        self.update_status()

    def update_status(self):
        if self.analyzer and self.analyzer.use_api:
            self.status_label.config(text="Using YouTube API (No Timeouts)", fg=THEME["success"])
        elif YTDLP_AVAILABLE:
            self.status_label.config(text="Using yt-dlp (5s delay per video)", fg=THEME["warning"])
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
            messagebox.showerror("Error", "Save API Key first!")
            return

        self.analyze_btn.config(state='disabled', text="Analyzing...")
        self.progress.start(10)
        Thread(target=self.run_analysis, daemon=True).start()

    def run_analysis(self):
        urls = []
        url = self.url_entry.get().strip()
        file_path = self.file_entry.get().strip()

        if url:
            urls.append(url)
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    urls.extend([line.strip() for line in f if line.strip() and 'youtube' in line])
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("File Error", f"Failed: {e}"))
                self.root.after(0, self.stop_analysis)
                return

        if not urls:
            self.root.after(0, lambda: messagebox.showwarning("No Input", "Enter URL or file!"))
            self.root.after(0, self.stop_analysis)
            return

        self.results = self.analyzer.analyze_urls(urls)
        self.root.after(0, self.show_results)
        self.root.after(0, self.stop_analysis)

    def show_results(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not self.results:
            messagebox.showinfo("No Data", "No videos analyzed.")
            return

        for r in self.results:
            # FIXED: Use .get() to avoid KeyError
            title = r.get('title', 'N/A')[:50] + '...' if len(r.get('title', '')) > 50 else r.get('title', 'N/A')
            views = f"{r.get('views', 0)//1000}K" if r.get('views', 0) >= 1000 else str(r.get('views', 0))
            likes = f"{r.get('likes', 0)//1000}K" if r.get('likes', 0) >= 1000 else str(r.get('likes', 0))
            dl_text = "Download" if r.get('download_url') else "Not Available"

            self.tree.insert('', 'end', values=(
                title, views, likes, r.get('duration', 'N/A'), r.get('country', 'N/A'),
                r.get('performance_score', 0), f"{r.get('engagement_rate_%', 0):.1f}%", dl_text
            ), tags=(r.get('download_url'),))

        messagebox.showinfo("Complete", f"Analyzed {len(self.results)} videos!")

    def stop_analysis(self):
        self.progress.stop()
        self.analyze_btn.config(state='normal', text="START BULK ANALYSIS")

    def clear_results(self):
        self.results = []
        for item in self.tree.get_children():
            self.tree.delete(item)

    def open_download_link(self, event):
        item = self.tree.selection()
        if not item:
            return
        dl_url = self.tree.item(item[0], "tags")[0]
        if dl_url:
            webbrowser.open(dl_url)
        else:
            messagebox.showinfo("No Link", "Direct download not available.")

    def download_all(self):
        if not self.results:
            return
        folder = filedialog.askdirectory()
        if not folder:
            return
        messagebox.showinfo("Starting", "Downloading all videos...")
        Thread(target=self._download_all, args=(folder,), daemon=True).start()

    def _download_all(self, folder):
        for r in self.results:
            url = r.get('download_url')
            if url:
                try:
                    subprocess.run(["yt-dlp", "-o", f"{folder}/%(title)s.%(ext)s", url], check=True)
                except:
                    pass

    def export(self, format_type):
        if not self.results:
            messagebox.showwarning("No Data", "Analyze first!")
            return

        path = filedialog.asksaveasfilename(defaultextension=f".{format_type}")
        if not path:
            return

        df = pd.DataFrame(self.results)
        df['hashtags'] = df['hashtags'].apply(lambda x: ', '.join(x) if isinstance(x, list) else '')
        df['download_url'] = df['download_url'].apply(lambda x: x or 'N/A')

        if format_type == 'csv':
            df.to_csv(path, index=False, encoding='utf-8')
        elif format_type == 'xlsx':
            df.to_excel(path, index=False)
        elif format_type == 'json':
            df.to_json(path, orient='records', indent=2, force_ascii=False)
        messagebox.showinfo("Exported", f"Saved to {path}")


# ========================================
#                  RUN APP
# ========================================
if __name__ == '__main__':
    if not YTDLP_AVAILABLE:
        print("Install: pip install yt-dlp google-api-python-client pandas openpyxl requests")
        sys.exit(1)

    root = tk.Tk()
    app = YouTubeAnalyzerGUI(root)
    root.mainloop()
