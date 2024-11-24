import yt_dlp
import whisper
import os
from moviepy.editor import VideoFileClip
from tqdm import tqdm
import warnings
import shutil

# Suppress yt-dlp warnings
warnings.filterwarnings('ignore', category=UserWarning, module='yt_dlp')

class VideoTranscriber:
    def __init__(self, language='en'):
        try:
            self.model = whisper.load_model("base")
            self.language = language
            print(f"✓ Whisper model loaded successfully for language: {language}")
        except Exception as e:
            print(f"Error loading Whisper model: {e}")
            exit(1)
    
    def validate_url(self, url):
        """Validate URL format"""
        return url.startswith(('http://', 'https://')) and any(
            domain in url.lower() for domain in ['youtube.com', 'youtu.be', 'instagram.com']
        )

    def download_video(self, url, temp_dir="temp"):
        os.makedirs(temp_dir, exist_ok=True)
        ydl_opts = {
            'format': 'best',
            'outtmpl': f'{temp_dir}/%(id)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [self._download_progress_hook]
        }
        
        print("Downloading video...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=True)
                return os.path.join(temp_dir, f"{info['id']}.{info['ext']}")
            except Exception as e:
                raise Exception(f"Download failed: {str(e)}")

    def _download_progress_hook(self, d):
        if d['status'] == 'downloading':
            if 'total_bytes' in d:
                progress = (d['downloaded_bytes'] / d['total_bytes']) * 100
                print(f"Download progress: {progress:.1f}%", end='')

    def extract_audio(self, video_path, temp_dir="temp"):
        print("Extracting audio...")
        video = VideoFileClip(video_path)
        audio_path = os.path.join(temp_dir, "audio.mp3")
        video.audio.write_audiofile(audio_path, verbose=False, logger=None)
        video.close()
        return audio_path

    def transcribe(self, file_path):
        print("Transcribing audio... This may take a few minutes.")
        result = self.model.transcribe(file_path, language=self.language)
        return result["text"]

    def process_url(self, url):
        if not self.validate_url(url):
            raise ValueError("Invalid URL format or unsupported platform")
            
        video_path = self.download_video(url)
        audio_path = self.extract_audio(video_path)
        transcript = self.transcribe(audio_path)
        
        # Cleanup
        for path in [video_path, audio_path]:
            if os.path.exists(path):
                os.remove(path)
        
        return transcript

    def process_local_file(self, file_path):
        if not os.path.exists(file_path):
            raise FileNotFoundError("Video file not found")
            
        audio_path = self.extract_audio(file_path)
        transcript = self.transcribe(audio_path)
        
        if os.path.exists(audio_path):
            os.remove(audio_path)
            
        return transcript

    def clean_temp_dir(self, temp_dir):
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)