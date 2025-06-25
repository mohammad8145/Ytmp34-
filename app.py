import os
import schedule
import threading
import time
from flask import Flask, request, jsonify, send_from_directory, render_template
import yt_dlp

# --- Basic Flask App Setup ---
app = Flask(__name__, template_folder='templates', static_folder='static')

# --- Configuration ---
DOWNLOADS_FOLDER = 'downloads'
app.config['DOWNLOADS_FOLDER'] = DOWNLOADS_FOLDER
os.makedirs(DOWNLOADS_FOLDER, exist_ok=True)

# --- File Cleanup Scheduler ---
def cleanup_old_files():
    """Deletes files in the downloads folder older than 24 hours."""
    print("Running scheduled cleanup...")
    now = time.time()
    for filename in os.listdir(DOWNLOADS_FOLDER):
        file_path = os.path.join(DOWNLOADS_FOLDER, filename)
        if os.path.isfile(file_path):
            file_mod_time = os.path.getmtime(file_path)
            if (now - file_mod_time) > 86400:  # 24 hours
                try:
                    os.remove(file_path)
                    print(f"Deleted old file: {filename}")
                except Exception as e:
                    print(f"Error deleting file {filename}: {e}")

# Run cleanup every day at 3 AM.
schedule.every().day.at("03:00").do(cleanup_old_files)

def run_scheduler():
    """Runs the scheduler in a separate thread."""
    while True:
        schedule.run_pending()
        time.sleep(60)

# --- Flask Routes ---

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert_video():
    """API endpoint to convert YouTube video to MP3."""
    data = request.get_json()
    url = data.get('url')

    if not url:
        return jsonify({'error': 'URL is required'}), 400

    try:
        # yt-dlp options
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': os.path.join(app.config['DOWNLOADS_FOLDER'], '%(id)s.%(ext)s'),
            'noplaylist': True,
            'quiet': True,
            'geo_bypass': True,
            'nocheckcertificate': True,
            'ignoreerrors': True,
            'force_generic_extractor': False,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            video_id = info_dict.get('id', None)
            video_title = info_dict.get('title', 'Unknown Title')
            thumbnail_url = info_dict.get('thumbnail', None)

            ydl.download([url])

            mp3_filename = f"{video_id}.mp3"
            download_path = f"/download/{mp3_filename}"

            response_data = {
                'title': video_title,
                'thumbnail': thumbnail_url,
                'file': download_path
            }
            return jsonify(response_data)

    except Exception as e:
        import traceback
        print("==== SERVER ERROR START ====")
        print(traceback.format_exc())
        print("==== SERVER ERROR END ====")
        return jsonify({'error': 'An internal server error occurred.'}), 500

@app.route('/download/<filename>')
def download_file(filename):
    """Serve the converted MP3 file for download."""
    try:
        return send_from_directory(
            app.config['DOWNLOADS_FOLDER'],
            filename,
            as_attachment=True
        )
    except FileNotFoundError:
        return jsonify({'error': 'File not found.'}), 404

# --- Main Execution ---
if __name__ == '__main__':
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    app.run(host='0.0.0.0', port=5000, debug=True)
