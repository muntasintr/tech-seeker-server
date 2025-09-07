from flask import Flask, request, jsonify
from yt_dlp import YoutubeDL
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# This single function will handle all requests to the root URL.
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods=['GET'])
def get_video_info(path):
    video_id = request.args.get('id')

    if not video_id:
        return jsonify({"error": "No YouTube video ID provided. Use ?id=VIDEO_ID"}), 400

    YDL_OPTIONS = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'noplaylist': True,
        'quiet': True
    }

    try:
        with YoutubeDL(YDL_OPTIONS) as ydl:
            logging.info(f"Fetching info for video ID: {video_id}")
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            logging.info("Successfully extracted info.")

            formats_to_return = []
            if 'formats' in info:
                for f in info['formats']:
                    # We are interested in formats that have both video and audio, or just video (for DASH)
                    if f.get('vcodec') != 'none' and f.get('url'):
                        resolution = f.get('resolution', 'N/A')
                        if f.get('height'):
                            resolution = f"{f['height']}p"
                        
                        formats_to_return.append({
                            'resolution': resolution,
                            'url': f['url'],
                            'has_audio': f.get('acodec') != 'none'
                        })
            
            # Remove duplicate resolutions, keeping the best quality (often the first one found)
            unique_formats = {f['resolution']: f for f in reversed(formats_to_return)}.values()


            return jsonify({
                "title": info.get("title", "No title"),
                "thumbnail": info.get("thumbnail", ""),
                "formats": sorted(list(unique_formats), key=lambda x: int(x['resolution'][:-1] or 0), reverse=True)
            })

    except Exception as e:
        logging.error(f"Error processing video ID {video_id}: {str(e)}")
        return jsonify({"error": "Could not process the video. It may be private, deleted, or region-locked."}), 500

if __name__ == '__main__':
    app.run(debug=True)

