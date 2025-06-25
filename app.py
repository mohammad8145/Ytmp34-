import os
import json
import threading
import schedule
import time
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, send_from_directory
import yt_dlp

app = Flask(__name__)
DOWNLOAD_FOLDER = 'downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER

# --- File Cleanup Logic ---

def cleanup_old_files():
    """Deletes files in the download folder older than 24 hours."""
    print("Running cleanup job...")
    now = time.time()
    twenty_four_hours = 24 * 60 * 60
    
    for filename in os.listdir(app.config['DOWNLOAD_FOLDER']):
        file_path = os.path.join(app.config['DOWNLOAD_FOLDER'], filename)
        # Avoid deleting the .gitkeep file
        if filename == '.gitkeep':
            continue
        try:
            if os.path.isfile(file_path):
                file_age = now - os.path.getmtime(file_path)
                if file_age > twenty_four_hours:
                    os.remove(file_path)
                    print(f"Deleted old file: {filename}")
        except Exception as e:
    import traceback
    print("==== SERVER ERROR START ====")
    print(traceback.format_exc())  # Print the full error in Render logs
    print("==== SERVER ERROR END ====")
    return jsonify({'error': 'An internal server error occurred.'}), 500
# --- Scheduler Setup ---

def run_scheduler():
    """Sets up and runs the scheduled tasks in a separate thread."""
    # Schedule the cleanup job to run once every day
    schedule.every(1).day.at("04:00").do(cleanup_old_files)
    while True:
        schedule.run_pending()
        time.sleep(60) # check every minute

# Start the scheduler in a background thread
scheduler_thread = threading.Thread(target=run_scheduler)
scheduler_thread.daemon = True
scheduler_thread.start()

# --- Flask Routes ---

@app.route('/')
def index():
    """Renders the main homepage."""
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    """Handles the conversion request."""
    data = request.get_json()
    url = data.get('url')

    if not url:
        return jsonify({"error": "URL is required."}), 400

    try:
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
            info_dict = ydl.extract_info(url, download=True)
            video_id = info_dict.get('id', None)
            video_title = info_dict.get('title', None)
            thumbnail = info_dict.get('thumbnail', None)

            # Construct the filename yt-dlp would have created
            filename = f"{video_id}.mp3"
            
            # This is a safe check in case something unexpected happened
            if not os.path.exists(os.path.join(app.config['DOWNLOAD_FOLDER'], filename)):
                 return jsonify({"error": "Conversion failed on the server."}), 500


            return jsonify({
                "title": video_title,
                "thumbnail": thumbnail,
                "file": f"/download/{filename}"
            })

    except yt_dlp.utils.DownloadError as e:
        # This catches invalid URLs, private videos, etc.
        return jsonify({"error": "Invalid YouTube URL or video is unavailable."}), 400
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500


@app.route('/download/<filename>')
def download_file(filename):
    """Serves the converted MP3 file for download."""
    # Sanitize filename to prevent directory traversal
    if '..' in filename or filename.startswith('/'):
        return "Invalid filename", 400
    
    try:
        return send_from_directory(
            app.config['DOWNLOAD_FOLDER'], 
            filename, 
            as_attachment=True
        )
    except FileNotFoundError:
        return "File not found.", 404


if __name__ == '__main__':
    # Using Gunicorn is recommended for production, but this works for development
    app.run(debug=True, host='0.0.0.0', port=5000)
