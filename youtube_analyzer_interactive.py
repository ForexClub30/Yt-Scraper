"""
YOUTUBE VIDEO ANALYZER PRO - DEEP ANALYSIS EDITION
Interactive | Bulk Support | Views, Likes, Duration, Country, Engagement

Author: Grok (xAI) | @YLdplayer85479 (Pakistan)
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional
import re
import requests

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
#           YOUTUBE ANALYZER PRO CLASS
# ========================================
class YouTubeAnalyzerPro:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ENTER API KEY")
        self.use_api = API_AVAILABLE and bool(self.api_key)
        self.youtube = None
        if self.use_api:
            try:
                self.youtube = build('youtube', 'v3', developerKey=self.api_key)
            except Exception as e:
                print(f"API init failed: {e}. Using yt-dlp fallback.")
                self.use_api = False

        # ReturnYouTubeDislike API
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
        """Convert ISO 8601 duration (PT1H2M3S) to HH:MM:SS"""
        if not iso_duration:
            return "N/A"
        duration = iso_duration.replace("PT", "")
        hours, minutes, seconds = 0, 0, 0
        if 'H' in duration:
            hours, duration = duration.split('H')
        if 'M' in duration:
            minutes, duration = duration.split('M')
        if 'S' in duration:
            seconds = duration.replace('S', '')
        try:
            return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
        except:
            return "N/A"

    def get_dislikes(self, video_id: str) -> int:
        try:
            resp = requests.get(self.rtd_api + video_id, timeout=5)
            if resp.status_code == 200:
                return resp.json().get("dislikes", 0)
        except:
            pass
        return 0

    def get_video_data_api(self, video_id: str) -> Optional[Dict]:
        try:
            req = self.youtube.videos().list(
                part='snippet,contentDetails,statistics,topicDetails',
                id=video_id
            )
            res = req.execute()
            if not res['items']:
                return None

            item = res['items'][0]
            sn = item['snippet']
            st = item['statistics']
            cd = item['contentDetails']

            # Duration
            duration = self.format_duration(cd.get('duration', ''))

            # Views, Likes
            views = int(st.get('viewCount', 0))
            likes = int(st.get('likeCount', 0))
            comments = int(st.get('commentCount', 0))
            dislikes = self.get_dislikes(video_id)

            # Engagement
            engagement = round((likes / views) * 100, 2) if views > 0 else 0

            # Performance Score (0-100)
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
                lang = sn['defaultLanguage']
                country = {
                    'en': 'US', 'es': 'ES', 'hi': 'IN', 'ar': 'SA',
                    'pt': 'BR', 'fr': 'FR', 'de': 'DE', 'ru': 'RU'
                }.get(lang[:2], 'Global')

            # Category
            cat_id = sn.get('categoryId', '')
            categories = {
                '1': 'Film & Animation', '2': 'Autos', '10': 'Music', '15': 'Pets',
                '17': 'Sports', '20': 'Gaming', '22': 'People & Blogs', '23': 'Comedy',
                '24': 'Entertainment', '25': 'News', '26': 'Howto', '27': 'Education',
                '28': 'Science & Tech'
            }
            category = categories.get(cat_id, 'Unknown')

            published_at = sn['publishedAt']
            dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))

            return {
                'video_id': video_id,
                'title': sn['title'],
                'upload_date': dt.date().isoformat(),
                'upload_time': dt.time().strftime('%H:%M:%S'),
                'upload_datetime': published_at,
                'duration': duration,
                'views': views,
                'likes': likes,
                'dislikes': dislikes,
                'comments': comments,
                'engagement_rate_%': engagement,
                'performance_score': score,
                'description': sn['description'],
                'channel_title': sn['channelTitle'],
                'channel_id': sn['channelId'],
                'country': country,
                'category': category,
                'hashtags': self.extract_hashtags(sn['description'] + ' ' + sn['title']),
                'thumbnail': f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
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
                    dt = datetime.strptime(upload_date, '%Y%m%d')
                    date_str = dt.date().isoformat()
                    time_str = '00:00:00'
                else:
                    date_str = time_str = 'N/A'

                duration = info.get('duration', 0)
                dur_str = f"{duration//3600:02d}:{(duration%3600)//60:02d}:{duration%60:02d}" if duration else "N/A"

                views = info.get('view_count', 0)
                likes = info.get('like_count', 0)
                dislikes = self.get_dislikes(video_id) if video_id else 0
                comments = info.get('comment_count', 0)

                return {
                    'video_id': video_id,
                    'title': info.get('title', 'N/A'),
                    'upload_date': date_str,
                    'upload_time': time_str,
                    'upload_datetime': upload_date or 'N/A',
                    'duration': dur_str,
                    'views': views,
                    'likes': likes,
                    'dislikes': dislikes,
                    'comments': comments,
                    'engagement_rate_%': round((likes/views)*100, 2) if views else 0,
                    'performance_score': 0,
                    'description': info.get('description', 'N/A'),
                    'channel_title': info.get('uploader', 'N/A'),
                    'channel_id': info.get('channel_id', 'N/A'),
                    'country': 'N/A',
                    'category': info.get('category', 'N/A'),
                    'hashtags': self.extract_hashtags(
                        info.get('description', '') + ' ' + info.get('title', '')
                    ),
                    'thumbnail': info.get('thumbnail', ''),
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
            print("   No valid URLs found.")
            return []

        print(f"\n   Analyzing {len(urls)} video(s)...")
        results = []
        for url in tqdm(urls, desc="   Progress", unit="vid", leave=False):
            data = self.analyze_single(url)
            if data:
                results.append(data)
            else:
                vid = self.extract_video_id(url) or 'N/A'
                results.append({
                    'video_id': vid, 'title': 'ERROR', 'upload_date': 'N/A', 'duration': 'N/A',
                    'views': 0, 'likes': 0, 'dislikes': 0, 'comments': 0,
                    'engagement_rate_%': 0, 'performance_score': 0,
                    'description': 'Failed', 'channel_title': 'N/A', 'country': 'N/A',
                    'hashtags': [], 'url': url
                })
        return results

    def print_table(self, data: List[Dict]):
        if not data:
            print("\n   No data.")
            return

        print("\n" + "="*160)
        print(f"{'#':<3} {'Title':<45} {'Views':<10} {'Likes':<8} {'Dur':<8} {'Country':<8} {'Score':<6} {'Eng%'}")
        print("="*160)
        for i, r in enumerate(data, 1):
            title = (r['title'][:42] + '...') if len(r['title']) > 45 else r['title']
            views = f"{r['views']//1000}K" if r['views'] >= 1000 else str(r['views'])
            likes = f"{r['likes']//1000}K" if r['likes'] >= 1000 else str(r['likes'])
            print(f"{i:<3} {title:<45} {views:<10} {likes:<8} {r['duration']:<8} {r['country']:<8} {r['performance_score']:<6} {r['engagement_rate_%']}")
        print("="*160 + "\n")

    def export_to_csv(self, data: List[Dict], filename: str):
        df = pd.DataFrame(data)
        df['hashtags'] = df['hashtags'].apply(lambda x: ', '.join(x))
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"   CSV → {filename}")

    def export_to_excel(self, data: List[Dict], filename: str):
        df = pd.DataFrame(data)
        df['hashtags'] = df['hashtags'].apply(lambda x: ', '.join(x))
        df.to_excel(filename, index=False)
        print(f"   Excel → {filename}")

    def export_to_json(self, data: List[Dict], filename: str):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"   JSON → {filename}")


# ========================================
#              INTERACTIVE MENU
# ========================================
def interactive_menu():
    print("\n" + "="*70)
    print("   YOUTUBE ANALYZER PRO - DEEP STATS EDITION")
    print("   Views | Likes | Duration | Country | Engagement | Score")
    print("   Created by Muhammad Yousuf(Pakistan)")
    print("="*70)

    # API Key
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        ch = input("\n   Enter YouTube API Key? (y/n): ").strip().lower()
        if ch == 'y':
            api_key = input("   API Key: ").strip()
        else:
            print("   Using yt-dlp (limited stats).")
    else:
        print("   API Key loaded.")

    analyzer = YouTubeAnalyzerPro(api_key=api_key)

    if analyzer.use_api:
        print("   Using YouTube API v3 (Full Stats)")
    else:
        if not YTDLP_AVAILABLE:
            print("   ERROR: Install yt-dlp → pip install yt-dlp")
            return
        print("   Using yt-dlp (No country/duration)")

    # Mode
    print("\n   1. Single Video")
    print("   2. Bulk from TXT File")
    mode = input("   Choose (1/2): ").strip()

    data = []
    if mode == '1':
        url = input("\n   YouTube URL: ").strip()
        if not url: return
        print("   Analyzing...")
        res = analyzer.analyze_single(url)
        if res:
            data = [res]
            print("   Done!")
        else:
            return
    elif mode == '2':
        path = input("\n   TXT File Path: ").strip()
        if not path: return
        data = analyzer.analyze_bulk_from_file(path)
        if not data: return
    else:
        print("   Invalid.")
        return

    # Show
    analyzer.print_table(data)

    # Export
    print("\n   Export:")
    csv = input("   CSV? (y/n): ").lower() == 'y'
    xlsx = input("   Excel? (y/n): ").lower() == 'y'
    json_exp = input("   JSON? (y/n): ").lower() == 'y'

    base = "youtube_analysis"
    if csv:
        f = input(f"   CSV name [{base}.csv]: ") or f"{base}.csv"
        analyzer.export_to_csv(data, f)
    if xlsx:
        f = input(f"   Excel name [{base}.xlsx]: ") or f"{base}.xlsx"
        analyzer.export_to_excel(data, f)
    if json_exp:
        f = input(f"   JSON name [{base}.json]: ") or f"{base}.json"
        analyzer.export_to_json(data, f)

    print("\n   All done! Follow @YLdplayer85479 for updates!\n")


# ========================================
#                  MAIN
# ========================================
if __name__ == '__main__':
    if not API_AVAILABLE and not YTDLP_AVAILABLE:
        print("Install: pip install google-api-python-client pandas yt-dlp tqdm openpyxl requests")
        sys.exit(1)

    try:
        interactive_menu()
    except KeyboardInterrupt:
        print("\n\n   Cancelled. Bye!")
    except Exception as e:
        print(f"\n   Error: {e}")
