from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
from yt_dlp import YoutubeDL
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        # Parse query parameters
        query_components = parse_qs(urlparse(self.path).query)
        video_id = query_components.get('id', [None])[0]

        if not video_id:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "No YouTube video ID provided. Use ?id=VIDEO_ID"}).encode('utf-8'))
            return

        YDL_OPTIONS = {
            'noplaylist': True,
            'quiet': True,
            'format': 'best[ext=mp4]/best' # Simplified format selection
        }

        try:
            with YoutubeDL(YDL_OPTIONS) as ydl:
                logging.info(f"Fetching info for video ID: {video_id}")
                info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                logging.info("Successfully extracted info.")

                formats_to_return = []
                if 'formats' in info:
                    for f in info.get('formats', []):
                        # Ensure we have a URL and it's a progressive format (video+audio) or just video
                        if f.get('url') and (f.get('vcodec') != 'none'):
                            height = f.get('height')
                            if height:
                                formats_to_return.append({
                                    'quality': f"{height}p",
                                    'url': f['url']
                                })
                
                # Filter for unique heights, keeping the first one found (yt-dlp usually lists best first)
                unique_formats = []
                seen_qualities = set()
                for f in formats_to_return:
                    if f['quality'] not in seen_qualities:
                        unique_formats.append(f)
                        seen_qualities.add(f['quality'])
                
                response_data = {
                    "title": info.get("title", "No title"),
                    "thumbnail": info.get("thumbnail", ""),
                    "formats": sorted(unique_formats, key=lambda x: int(x['quality'][:-1]), reverse=True)
                }

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode('utf-8'))

        except Exception as e:
            logging.error(f"Error processing video ID {video_id}: {str(e)}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Could not process the video. It may be private, deleted, or region-locked."}).encode('utf-8'))
            
        return
