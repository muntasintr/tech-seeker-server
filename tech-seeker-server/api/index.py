from http.server import BaseHTTPRequestHandler
import json
from yt_dlp import YoutubeDL
from urllib.parse import urlparse, parse_qs

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        query_components = parse_qs(urlparse(self.path).query)
        video_id = query_components.get('id', [None])[0]

        if not video_id:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Video ID is required. Use ?id=VIDEO_ID"}).encode())
            return

        YDL_OPTS = {
            'quiet': True,
            'noplaylist': True,
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        }

        try:
            with YoutubeDL(YDL_OPTS) as ydl:
                info = ydl.extract_info(f"[https://www.youtube.com/watch?v=](https://www.youtube.com/watch?v=){video_id}", download=False)
                
                formats_to_return = []
                if 'formats' in info:
                    seen_resolutions = set()
                    for f in info.get('formats', []):
                        # We need formats with a URL and a video codec.
                        if f.get('url') and f.get('vcodec') != 'none':
                            height = f.get('height')
                            if height and f'{height}p' not in seen_resolutions:
                                formats_to_return.append({
                                    'quality': f'{height}p',
                                    'url': f.get('url')
                                })
                                seen_resolutions.add(f'{height}p')
                
                # Sort by height numerically (e.g., 1080p, 720p, ...)
                formats_to_return.sort(key=lambda x: int(x['quality'][:-1]), reverse=True)

                response_data = {
                    "title": info.get("title", "No title"),
                    "thumbnail": info.get("thumbnail", ""),
                    "formats": formats_to_return
                }
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*') # Added for cross-origin requests
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
