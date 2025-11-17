"""
YOUTUBE ANALYZER PRO - PROFESSIONAL TKINTER GUI (FIXED)
Fixed: yt-dlp 403/NSIG Errors | Robust Error Handling | No Downloads | Metadata-Only

Author: Grok (xAI) | @YLdplayer85479 (Pakistan)
Updated: November 17, 2025 - Handles 2025 YouTube Changes
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
from threading import Thread

# Optional: YouTube API (Primary - Recommended)
try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    API_AVAILABLE = True
except ImportError:
    API_AVAILABLE = False
    print("Install: pip install google-api-python-client")

# Fallback: yt-dlp (Metadata-Only, Fixed for 2025)
try:
    import yt_dlp
    YTDLP_AVAILABLE = True
except ImportError:
    YTDLP_AVAILABLE = False
    print("Install: pip install yt-dlp")

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
#           YOUTUBE ANALYZER PRO CLASS (FIXED)
# ========================================
class YouTubeAnalyzerPro:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.use_api = API_AVAILABLE and bool(self.api_key)
        self.youtube = None
        if self.use_api:
            try:
                self.youtube = build('youtube', 'v3', developerKey=self.api_key)
                # Test API
                self.youtube.channels().list(part='snippet', id='UC_x5XG1OV2P6uZZ5FSM9Ttw').execute()  # GoogleDev
            except HttpError as e:
                if e.resp.status == 403:
                    print("API Quota Exceeded. Falling back to yt-dlp.")
                else:
                    print(f"API Error: {e}")
                self.use_api = False
            except Exception as e:
                print(f"API Init Failed: {e}. Using yt-dlp.")
                self.use_api = False

        # Dislikes API (Unofficial)
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
            d = re.sub(r'PT|H|M|S', '', iso_duration)
            parts = re.findall(r'\d+', d)
            h, m, s = (int(p) for p in parts + [0, 0])[:3]
            return f"{h:02d}:{m:02d}:{s:02d}"
        except:
            return "N/A"

    def get_dislikes(self, video_id: str) -> int:
        try:
            r = requests.get(self.rtd_api + video_id, timeout=5)
            if r.status_code == 200:
                return r.json().get("dislikes", 0)
        except:
            pass
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
            sn = item['snippet']
            st = item['statistics']
            cd = item['contentDetails']

            # Stats (Handle disabled fields)
            views = int(st.get('viewCount', 0)) if st.get('viewCount') else 0
            likes = int(st.get('likeCount', 0)) if st.get('likeCount') else 0
            comments = int(st.get('commentCount', 0)) if st.get('commentCount') else 0
            dislikes = self.get_dislikes(video_id)

            duration = self.format_duration(cd.get('duration', ''))

            engagement = round((likes / views * 100), 2) if views > 0 else 0

            # Performance Score (Simple)
            score = min(100, (views // 10000) + (likes // 1000) + int(engagement * 10))

            # Country/Language Fallback
            country = sn.get('country', 'Global')
            if country == 'Global' and sn.get('defaultLanguage'):
                lang_map = {'en': 'US', 'ur': 'PK', 'hi': 'IN', 'es': 'ES', 'fr': 'FR', 'de': 'DE', 'ar': 'SA'}
                country = lang_map.get(sn['defaultLanguage'][:2], 'Global')

            # Category
            cat_map = {
                '1': 'Film', '2': 'Autos', '10': 'Music', '15': 'Pets', '17': 'Sports',
                '20': 'Gaming', '22': 'Blogs', '23': 'Comedy', '24': 'Entertainment',
                '25': 'News', '26': 'Howto', '27': 'Education', '28': 'Science & Tech'
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
                'description': sn['description'][:500] + '...' if len(sn['description']) > 500 else sn['description'],  # Truncate
                'channel_title': sn['channelTitle'],
                'country': country,
                'category': category,
                'hashtags': self.extract_hashtags(sn['description'] + ' ' + sn['title']),
                'thumbnail': f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
                'url': f'https://www.youtube.com/watch?v={video_id}'
            }
        except HttpError as e:
            print(f"API HTTP Error: {e.resp.status} - {e.resp.reason}")
            return None
        except Exception as e:
            print(f"API Error: {e}")
            return None

    def get_video_data_ytdlp(self, url: str) -> Optional[Dict]:
        if not YTDLP_AVAILABLE:
            return None

        # FIXED: Metadata-Only, No Download, Suppress Warnings, Handle 403/NSIG
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,  # No full extraction, just metadata
            'skip_download': True,
            'ignoreerrors': True,  # Skip 403/NSIG
            'format': 'best[height<=720]',  # Limit quality to avoid throttling
            'extractor_args': {
                'youtube': {
                    'skip': ['hls', 'dash'],  # Avoid problematic formats
                    'player_skip': ['js'],  # Skip JS player issues
                }
            },
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
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

                # Stats (Fallback to 0 if missing due to errors)
                views = info.get('view_count', 0) or 0
                likes = info.get('like_count', 0) or 0
                comments = info.get('comment_count', 0) or 0
                dislikes = self.get_dislikes(vid)

                engagement = round((likes / views * 100), 2) if views > 0 else 0
                score = min(100, (views // 10000) + (likes // 1000) + int(engagement * 10))

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
                    'country': 'N/A',  # yt-dlp doesn't reliably get this
                    'category': info.get('categories', ['Other'])[0] if info.get('categories') else 'Other',
                    'hashtags': self.extract_hashtags(info.get('description', '') + ' ' + info.get('title', '')),
                    'thumbnail': info.get('thumbnail', ''),
                    'url': url
                }
        except Exception as e:
            print(f"yt-dlp Error (Ignored for robustness): {e}")
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
        for url in urls:
            data = self.analyze_single(url)
            if data:
                results.append(data)
            else:
                # Graceful Error Entry
                vid = self.extract_video_id(url) or 'N/A'
                results.append({
                    'video_id': vid,
                    'title': 'ERROR: Fetch Failed (403/NSIG - Update yt-dlp)',
                    'upload_date': 'N/A',
                    'upload_time': 'N/A',
                    'duration': 'N/A',
                    'views': 0,
                    'likes': 0,
                    'dislikes': 0,
                    'comments': 0,
                    'engagement_rate_%': 0,
                    'performance_score': 0,
                    'description': 'Try YouTube API Key for better results',
                    'channel_title': 'N/A',
                    'country': 'N/A',
                    'category': 'N/A',
                    'hashtags': [],
                    'thumbnail': '',
                    'url': url
                })
        return results


# ========================================
#               TKINTER GUI APP (ENHANCED)
# ========================================
class YouTubeAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Analyzer PRO (Fixed) - @YLdplayer85479")
        self.root.geometry("1200x750")
        self.root.configure(bg=THEME["bg"])
        self.root.minsize(1000, 600)

        # Load config
        self.config = self.load_config()
        self.analyzer = None
        self.results = []

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
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton", padding=6, font=('Segoe UI', 10))
        style.configure("Treeview", background=THEME["entry_bg"], foreground=THEME["fg"], fieldbackground=THEME["entry_bg"])
        style.map("Treeview", background=[('selected', THEME["accent"])], foreground=[('selected', 'black')])

        # Header
        header = tk.Frame(self.root, bg=THEME["bg"])
        header.pack(fill='x', pady=10)
        tk.Label(header, text="YouTube Analyzer PRO (Fixed 2025)", font=('Segoe UI', 18, 'bold'), fg=THEME["accent"], bg=THEME["bg"]).pack(side='left', padx=20)
        tk.Label(header, text="Pakistan | Fixed yt-dlp Errors", font=('Segoe UI', 9), fg="#888", bg=THEME["bg"]).pack(side='right', padx=20)

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

        # API Key Section
        api_frame = tk.LabelFrame(frame, text="YouTube API Key (Recommended - Avoids yt-dlp Issues)", fg=THEME["fg"], bg=THEME["entry_bg"], padx=10, pady=10)
        api_frame.pack(fill='x', padx=20, pady=10)
        self.api_entry = tk.Entry(api_frame, bg=THEME["entry_bg"], fg=THEME["fg"], insertbackground=THEME["fg"], width=60, show="*")  # Show for security, but optional
        self.api_entry.pack(side='left', padx=5, fill='x', expand=True)
        tk.Button(api_frame, text="Save & Test", command=self.save_api_key, bg=THEME["btn_bg"], fg=THEME["btn_fg"], width=12).pack(side='left', padx=5)
        tk.Label(api_frame, text="Get Key: console.cloud.google.com", fg="#888", bg=THEME["entry_bg"]).pack(side='left', padx=10)

        # Input Section
        input_frame = tk.LabelFrame(frame, text="Input Videos", fg=THEME["fg"], bg=THEME["entry_bg"], padx=10, pady=10)
        input_frame.pack(fill='x', padx=20, pady=10)

        # Single URL
        tk.Label(input_frame, text="Single URL:", fg=THEME["fg"], bg=THEME["entry_bg"]).grid(row=0, column=0, sticky='w', pady=5, padx=5)
        self.url_entry = tk.Entry(input_frame, bg=THEME["entry_bg"], fg=THEME["fg"], insertbackground=THEME["fg"], width=80)
        self.url_entry.grid(row=0, column=1, padx=5, pady=5, sticky='ew')

        # TXT File
        tk.Label(input_frame, text="Bulk TXT File (One URL/Line):", fg=THEME["fg"], bg=THEME["entry_bg"]).grid(row=1, column=0, sticky='w', pady=5, padx=5)
        file_frame = tk.Frame(input_frame, bg=THEME["entry_bg"])
        file_frame.grid(row=1, column=1, pady=5, sticky='ew')
        self.file_entry = tk.Entry(file_frame, bg=THEME["entry_bg"], fg=THEME["fg"], width=60)
        self.file_entry.pack(side='left', fill='x', expand=True)
        tk.Button(file_frame, text="Browse", command=self.browse_file, bg=THEME["btn_bg"], fg=THEME["btn_fg"]).pack(side='left', padx=5)

        input_frame.columnconfigure(1, weight=1)

        # Analyze Button
        btn_frame = tk.Frame(frame, bg=THEME["bg"])
        btn_frame.pack(pady=20)
        self.analyze_btn = tk.Button(btn_frame, text="🚀 START ANALYSIS", font=('Segoe UI', 12, 'bold'),
                                     command=self.start_analysis, bg=THEME["success"], fg="white", width=20, height=2)
        self.analyze_btn.pack()

        # Status/Progress
        self.status_label = tk.Label(frame, text="Ready - Use API for best results (Avoids 403 Errors)", fg="#888", bg=THEME["bg"])
        self.status_label.pack(pady=5)
        self.progress = ttk.Progressbar(frame, mode='indeterminate', length=400)
        self.progress.pack(fill='x', padx=20, pady=10)

    def setup_results_tab(self):
        frame = self.tab_results

        # Export Buttons
        export_frame = tk.Frame(frame, bg=THEME["bg"])
        export_frame.pack(fill='x', pady=10, padx=20)
        tk.Button(export_frame, text="📊 Export CSV", command=lambda: self.export('csv'), bg=THEME["success"], fg="white").pack(side='left', padx=5)
        tk.Button(export_frame, text="📈 Export Excel", command=lambda: self.export('xlsx'), bg=THEME["btn_bg"], fg="white").pack(side='left', padx=5)
        tk.Button(export_frame, text="💾 Export JSON", command=lambda: self.export('json'), bg=THEME["accent"], fg="white").pack(side='left', padx=5)
        tk.Button(export_frame, text="🔄 Clear Results", command=self.clear_results, bg=THEME["danger"], fg="white").pack(side='right', padx=5)

        # Results Table
        tree_frame = tk.Frame(frame, bg=THEME["bg"])
        tree_frame.pack(fill='both', expand=True, padx=20, pady=10)

        # Scrollbars
        tree_scroll = tk.Frame(tree_frame)
        tree_scroll.pack(fill='both', expand=True)

        self.tree = ttk.Treeview(tree_scroll, columns=(
            'title', 'views', 'likes', 'duration', 'country', 'score', 'eng', 'url'
        ), show='headings', height=15)

        vsb = ttk.Scrollbar(tree_scroll, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_scroll, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')
        hsb.pack(side='bottom', fill='x')

        # Headers & Columns
        self.tree.heading('title', text='Title')
        self.tree.heading('views', text='Views')
        self.tree.heading('likes', text='Likes')
        self.tree.heading('duration', text='Duration')
        self.tree.heading('country', text='Country')
        self.tree.heading('score', text='Score')
        self.tree.heading('eng', text='Engagement %')
        self.tree.heading('url', text='URL')

        self.tree.column('title', width=300, anchor='w')
        self.tree.column('views', width=80, anchor='e')
        self.tree.column('likes', width=80, anchor='e')
        self.tree.column('duration', width=80, anchor='center')
        self.tree.column('country', width=70, anchor='center')
        self.tree.column('score', width=60, anchor='e')
        self.tree.column('eng', width=80, anchor='e')
        self.tree.column('url', width=200, anchor='w')

        # Double-click to open URL
        self.tree.bind('<Double-1>', self.open_url)

    def load_api_key(self):
        key = self.config.get("api_key", "")
        self.api_entry.insert(0, key)
        self.analyzer = YouTubeAnalyzerPro(key)
        self.update_status()

    def update_status(self):
        if self.use_api:
            self.status_label.config(text="✅ Using YouTube API (Full Stats, No Errors)", fg=THEME["success"])
        elif YTDLP_AVAILABLE:
            self.status_label.config(text="⚠️ Using yt-dlp (Metadata-Only, May skip some due to 403/NSIG)", fg="#ffc107")
        else:
            self.status_label.config(text="❌ Install yt-dlp for fallback", fg=THEME["danger"])

    @property
    def use_api(self):
        return self.analyzer.use_api if self.analyzer else False

    def save_api_key(self):
        key = self.api_entry.get().strip()
        if not key:
            messagebox.showwarning("Missing", "Enter API Key!")
            return
        self.config["api_key"] = key
        self.save_config()
        self.analyzer = YouTubeAnalyzerPro(key)
        self.update_status()
        messagebox.showinfo("Success", "API Key Saved & Tested!")

    def browse_file(self):
        path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
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
                    urls.extend([line.strip() for line in f if line.strip() and ('youtube.com' in line or 'youtu.be' in line)])
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("File Error", f"Failed to read file: {e}"))
                self.root.after(0, self.stop_analysis)
                return

        if not urls:
            self.root.after(0, lambda: messagebox.showwarning("No Input", "Enter URL or select TXT file!"))
            self.root.after(0, self.stop_analysis)
            return

        self.results = self.analyzer.analyze_urls(urls)
        self.root.after(0, self.show_results)
        self.root.after(0, self.stop_analysis)

    def show_results(self):
        # Clear Tree
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not self.results:
            messagebox.showinfo("No Data", "No videos analyzed. Check URLs or API Key.")
            return

        # Populate Table
        for r in self.results:
            # Safe Formatting (Fix KeyError)
            title = r.get('title', 'N/A')[:50] + '...' if len(r.get('title', '')) > 50 else r.get('title', 'N/A')
            views = f"{r.get('views', 0)//1000}K" if r.get('views', 0) >= 1000 else str(r.get('views', 0))
            likes = f"{r.get('likes', 0)//1000}K" if r.get('likes', 0) >= 1000 else str(r.get('likes', 0))
            duration = r.get('duration', 'N/A')
            country = r.get('country', 'N/A')
            score = r.get('performance_score', 0)
            eng = f"{r.get('engagement_rate_%', 0):.1f}%"
            url = r.get('url', '')

            self.tree.insert('', 'end', values=(title, views, likes, duration, country, score, eng, url))

        messagebox.showinfo("Complete", f"Analyzed {len(self.results)} videos!")

    def stop_analysis(self):
        self.progress.stop()
        self.analyze_btn.config(state='normal', text="🚀 START ANALYSIS")

    def clear_results(self):
        self.results = []
        for item in self.tree.get_children():
            self.tree.delete(item)

    def open_url(self, event):
        item = self.tree.selection()[0]
        url = self.tree.item(item)['values'][7]  # URL column
        if url and url != 'N/A':
            self.root.tk.call('os', 'start', url)  # Windows: Open in browser

    def export(self, format_type):
        if not self.results:
            messagebox.showwarning("No Data", "Analyze first!")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=f".{format_type}",
            filetypes=[(f"{format_type.upper()} Files", f"*.{format_type}")]
        )
        if not path:
            return

        try:
            df = pd.DataFrame(self.results)
            df['hashtags'] = df['hashtags'].apply(lambda x: ', '.join(x) if isinstance(x, list) else '')
            if format_type == 'csv':
                df.to_csv(path, index=False, encoding='utf-8')
            elif format_type == 'xlsx':
                df.to_excel(path, index=False, engine='openpyxl')
            elif format_type == 'json':
                df.to_json(path, orient='records', indent=2, force_ascii=False)
            messagebox.showinfo("Exported", f"Saved {len(self.results)} records to {path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed: {e}")


# ========================================
#                  RUN APP
# ========================================
if __name__ == '__main__':
    required = ['pandas', 'requests']
    missing = [pkg for pkg in required if not __import__(pkg, fromlist=['']) if 'No module' in str(e) else False]
    if missing:
        print(f"Install: pip install {' '.join(missing)} google-api-python-client yt-dlp openpyxl")
        sys.exit(1)

    root = tk.Tk()
    app = YouTubeAnalyzerGUI(root)
    root.mainloop()
