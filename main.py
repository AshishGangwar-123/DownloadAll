from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from yt_dlp import YoutubeDL
from pydantic import BaseModel
import os

app = FastAPI()

# Enable CORS so the frontend can communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # Allow Content-Disposition to expose filename to frontend
    expose_headers=["Content-Disposition"]
)

# Pydantic model to match the incoming JSON request
class URL(BaseModel):
    url: str
    format: str  # Accepts: "best", "1080", "720", "480", "360", "144", or "mp3"

@app.post("/info")
def get_info(url: URL):
     # Setup basic options, download=False avoids downloading actual video file
     option = {}
     with YoutubeDL(option) as ydl:
         info = ydl.extract_info(url.url, download=False)
         
     formats = info.get("formats", [])
     video_sizes = {}
     best_audio_size = 0

     # Loop through all format streams to find matching resolutions
     for f in formats:
         filesize = f.get("filesize") or f.get("filesize_approx") or 0
         if filesize == 0:
             continue
         
         vcodec = f.get("vcodec", "none")
         acodec = f.get("acodec", "none")
         
         # 1. Identify audio-only stream size
         if vcodec == "none" and acodec != "none":
             if filesize > best_audio_size:
                 best_audio_size = filesize
         # 2. Identify video stream size by resolution height
         elif vcodec != "none":
             height = f.get("height")
             if height in [1080, 720, 480, 360, 144]:
                 if height not in video_sizes or filesize > video_sizes[height]:
                     video_sizes[height] = filesize

     # Calculate final size estimates in MB
     sizes_mb = {}
     if best_audio_size > 0:
         sizes_mb["mp3"] = f"{round(best_audio_size / (1024 * 1024), 1)} MB"
     else:
         sizes_mb["mp3"] = "Unknown"

     for h in [1080, 720, 480, 360, 144]:
         if h in video_sizes:
             # Estimated video + audio combined size
             total_bytes = video_sizes[h] + best_audio_size
             sizes_mb[str(h)] = f"{round(total_bytes / (1024 * 1024), 1)} MB"
         else:
             sizes_mb[str(h)] = "Unknown"

     return sizes_mb

# Background function to safely remove file from server storage
def remove_file(file_path: str):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Cleanup: Removed temporary file {file_path} from server disk.")
    except Exception as e:
        print(f"Error during cleanup of file {file_path}: {e}")

@app.post("/download")
def handle_download(url: URL, background_tasks: BackgroundTasks):
     # Set the corresponding yt-dlp format using basic if-elif checks
     if url.format == "mp3":
         download_format = "bestaudio/best"
     elif url.format == "1080":
         download_format = "bestvideo[height<=1080]+bestaudio/best"
     elif url.format == "720":
         download_format = "bestvideo[height<=720]+bestaudio/best"
     elif url.format == "480":
         download_format = "bestvideo[height<=480]+bestaudio/best"
     elif url.format == "360":
         download_format = "bestvideo[height<=360]+bestaudio/best"
     elif url.format == "144":
         download_format = "bestvideo[height<=144]+bestaudio/best"
     else:
         download_format = "best"

     # Create temporary downloads folder if not exists
     os.makedirs("./downloads", exist_ok=True)

     option = {
        "outtmpl": "./downloads/%(title)s.%(ext)s",
        "format": download_format
     }

     # Trigger the download and get filename details
     with YoutubeDL(option) as ydl:
         info = ydl.extract_info(url.url, download=True)
         filename = ydl.prepare_filename(info)
         
         # Check if video extension changed after downloading/merging (e.g. mkv/mp4)
         if not os.path.exists(filename):
             # Try checking if it exists with different extension or format
             basename, _ = os.path.splitext(filename)
             for ext in ['.mp4', '.mkv', '.webm', '.3gp', '.m4a']:
                 if os.path.exists(basename + ext):
                     filename = basename + ext
                     break

     # Add task to delete this downloaded file once response is sent
     background_tasks.add_task(remove_file, filename)

     # Send the file back to the browser
     return FileResponse(
         path=filename,
         filename=os.path.basename(filename),
         media_type="application/octet-stream"
     )