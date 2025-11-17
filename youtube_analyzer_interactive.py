"""
YouTube Video Analyzer - FULLY INTERACTIVE (User Input Based)
No command-line arguments needed. Everything is asked step-by-step.

Features:
- Single or Bulk (from .txt file) YouTube video analysis
- Input via interactive prompts
- Uses YouTube API v3 (accurate date/time) or yt-dlp fallback
- Outputs: Console Table + CSV + Optional JSON

Author:@YLdplayer85479 (Pakistan)
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional
import re

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

from tqdm import tqdm


# ========================================
#           YOUTUBE ANALYZER CLASS
# ========================================
class YouTubeAnalyzer:
    def __init__(self, api_key: Optional[str] = None, use_api: bool = True):
        self.api_key = api_key or os.getenv("YOUTUBE_API_KEY")
        self.use_api = use_api and API_AVAILABLE and bool(self.api_key)
        self.youtube = None
        if self.use_api:
            try:
                self.youtube = build('youtube', 'v3', developerKey=self.api_key)
            except Exception as e:
                print(f"Warning: API build failed: {e}. Falling back to yt-dlp.")
                self.use_api = False

    def extract_video_id(self, url: str) -> Optional[str]:
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'(?:embed\/)([0-9A-Za-z_-]{11})',
            r'(?:shorts\/)([0-9A-Za-z_-]{11})',
            r'youtu\.be\/([0-9A-Za-z_-]{11})',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def extract_hashtags(self, text: str) -> List[str]:
        return list(set(re.findall(r'#\w+', text)))

    def get_video_data_api(self, video_id: str) -> Optional[Dict]:
        try:
            request = self.youtube.videos().list(
                part='snippet,contentDetails,statistics',
                id=video_id
            )
            response = request.execute()
            if not response['items']:
                return None

            item = response['items'][0]['snippet']
            published_at = item['publishedAt']

            dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            return {
                'video_id': video_id,
                'title': item['title'],
                'upload_date': dt.date().isoformat(),
                'upload_time': dt.time().strftime('%H:%M:%S'),
                'upload_datetime': published_at,
                'description': item['description'],
                'channel_title': item['channelTitle'],
                'hashtags': self.extract_hashtags(item['description'] + ' ' + item['title']),
                'url': f'https://www.youtube.com/watch?v={video_id}'
            }
        except Exception as e:
            print(f"   API Error: {e}")
            return None

    def get_video_data_ytdlp(self, url: str) -> Optional[Dict]:
        if not YTDLP_AVAILABLE:
            return None
        ydl_opts = {'quiet': True, 'no_warnings': True}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    return None

                video_id = info.get('id')
                upload_date = info.get('upload_date')
                if upload_date:
                    date_obj = datetime.strptime(upload_date, '%Y%m%d')
                    upload_date_str = date_obj.date().isoformat()
                    upload_time_str = '00:00:00'
                else:
                    upload_date_str = upload_time_str = 'N/A'

                return {
                    'video_id': video_id,
                    'title': info.get('title', 'N/A'),
                    'upload_date': upload_date_str,
                    'upload_time': upload_time_str,
                    'upload_datetime': info.get('upload_date', 'N/A'),
                    'description': info.get('description', 'N/A'),
                    'channel_title': info.get('uploader', 'N/A'),
                    'hashtags': self.extract_hashtags(
                        info.get('description', '') + ' ' + info.get('title', '')
                    ),
                    'url': url
                }
        except Exception as e:
            print(f"   yt-dlp Error: {e}")
            return None

    def analyze_single(self, url: str) -> Optional[Dict]:
        video_id = self.extract_video_id(url)
        if not video_id:
            print("   Invalid YouTube URL!")
            return None

        if self.use_api:
            return self.get_video_data_api(video_id)
        else:
            return self.get_video_data_ytdlp(url)

    def analyze_bulk_from_file(self, file_path: str) -> List[Dict]:
        if not os.path.exists(file_path):
            print(f"   File not found: {file_path}")
            return []

        with open(file_path, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip() and ('youtube.com' in line or 'youtu.be' in line)]

        if not urls:
            print("   No valid YouTube URLs found in file.")
            return []

        print(f"\n   Analyzing {len(urls)} video(s)...")
        results = []
        for url in tqdm(urls, desc="   Progress", unit="video", leave=False):
            data = self.analyze_single(url)
            if data:
                results.append(data)
            else:
                vid = self.extract_video_id(url) or 'N/A'
                results.append({
                    'video_id': vid,
                    'title': 'ERROR',
                    'upload_date': 'N/A',
                    'upload_time': 'N/A',
                    'description': 'Failed to fetch',
                    'channel_title': 'N/A',
                    'hashtags': [],
                    'url': url
                })
        return results

    def print_table(self, data: List[Dict]):
        if not data:
            print("\n   No data to display.")
            return

        print("\n" + "="*130)
        print(f"{'#':<3} {'Title':<50} {'Date':<12} {'Time':<8} {'Hashtags':<35} {'Channel':<20}")
        print("="*130)
        for i, row in enumerate(data, 1):
            title = (row['title'][:47] + '...') if len(row['title']) > 50 else row['title']
            hashtags = ', '.join(row['hashtags']) if row['hashtags'] else 'None'
            hashtags = (hashtags[:32] + '...') if len(hashtags) > 35 else hashtags
            channel = (row['channel_title'][:17] + '...') if len(row['channel_title']) > 20 else row['channel_title']
            print(f"{i:<3} {title:<50} {row['upload_date']:<12} {row['upload_time']:<8} {hashtags:<35} {channel}")
        print("="*130 + "\n")

    def export_to_csv(self, data: List[Dict], filename: str):
        df = pd.DataFrame(data)
        df['hashtags'] = df['hashtags'].apply(lambda x: ', '.join(x) if isinstance(x, list) else '')
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"   CSV saved: {filename}")

    def export_to_json(self, data: List[Dict], filename: str):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"   JSON saved: {filename}")


# ========================================
#              INTERACTIVE MENU
# ========================================
def interactive_menu():
    print("\n" + "="*60)
    print("   YOUTUBE VIDEO ANALYZER (Interactive Mode)")
    print("   Created by Grok (xAI) | @YLdplayer85479 (Pakistan)")
    print("="*60)

    # --- API Key Input ---
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        print("\n   YouTube API Key not found in environment.")
        choice = input("   Do you want to enter API key now? (y/n): ").strip().lower()
        if choice == 'y':
            api_key = input("   Enter your YouTube Data API v3 Key: ").strip()
        else:
            print("   Proceeding without API key (using yt-dlp fallback).")
            api_key = None
    else:
        print(f"   API Key loaded from environment.")

    analyzer = YouTubeAnalyzer(api_key=api_key, use_api=True)

    if analyzer.use_api:
        print("   Using YouTube Data API v3 (Accurate Date & Time)")
    else:
        if not YTDLP_AVAILABLE:
            print("   ERROR: yt-dlp not installed!")
            print("   Install: pip install yt-dlp")
            return
        print("   Using yt-dlp (Upload time may show 00:00:00)")

    # --- Mode Selection ---
    print("\n   Choose analysis mode:")
    print("   1. Single Video")
    print("   2. Bulk from TXT File")
    mode = input("   Enter 1 or 2: ").strip()

    data = []

    if mode == '1':
        url = input("\n   Enter YouTube URL: ").strip()
        if not url:
            print("   No URL entered.")
            return
        print("   Analyzing...")
        result = analyzer.analyze_single(url)
        if result:
            data = [result]
            print("   Success!")
        else:
            print("   Failed to analyze video.")
            return

    elif mode == '2':
        file_path = input("\n   Enter path to TXT file (one URL per line): ").strip()
        if not file_path:
            print("   No file path entered.")
            return
        data = analyzer.analyze_bulk_from_file(file_path)
        if not data:
            return

    else:
        print("   Invalid choice.")
        return

    # --- Show Results ---
    analyzer.print_table(data)

    # --- Export Options ---
    print("   Export options:")
    export_csv = input("   Save as CSV? (y/n): ").strip().lower() == 'y'
    csv_file = "youtube_analysis.csv"
    if export_csv:
        csv_file = input(f"   CSV filename [default: {csv_file}]: ").strip() or csv_file

    export_json = input("   Save as JSON? (y/n): ").strip().lower() == 'y'
    json_file = "youtube_analysis.json"
    if export_json:
        json_file = input(f"   JSON filename [default: {json_file}]: ").strip() or json_file

    # --- Save Files ---
    if export_csv and data:
        analyzer.export_to_csv(data, csv_file)
    if export_json and data:
        analyzer.export_to_json(data, json_file)

    print("\n   Analysis complete! Thank you for using the tool.")
    print("   Follow @YLdplayer85479 for updates!\n")


# ========================================
#                  MAIN
# ========================================
if __name__ == '__main__':
    if not API_AVAILABLE and not YTDLP_AVAILABLE:
        print("Please install required packages:")
        print("pip install google-api-python-client pandas yt-dlp tqdm")
        sys.exit(1)

    try:
        interactive_menu()
    except KeyboardInterrupt:
        print("\n\n   Operation cancelled by user. Goodbye!")
    except Exception as e:
        print(f"\n   Unexpected error: {e}")
