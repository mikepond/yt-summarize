import os
import re
from pathlib import Path
from typing import Optional, Union
import yt_dlp
from tqdm import tqdm


class VideoHandler:
    def __init__(self, output_dir: str = "./temp"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def is_youtube_url(self, url: str) -> bool:
        youtube_regex = r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
        return bool(re.match(youtube_regex, url))
    
    def download_youtube_video(self, url: str, output_filename: Optional[str] = None) -> Path:
        if not self.is_youtube_url(url):
            raise ValueError(f"Invalid YouTube URL: {url}")
        
        if not output_filename:
            output_filename = "%(title)s.%(ext)s"
        
        output_path = self.output_dir / output_filename
        
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': str(output_path),
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [self._progress_hook],
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                actual_filename = ydl.prepare_filename(info)
                if not actual_filename.endswith('.mp4'):
                    actual_filename += '.mp4'
                return Path(actual_filename)
        except Exception as e:
            raise Exception(f"Failed to download video: {str(e)}")
    
    def _progress_hook(self, d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)
            if total > 0:
                percentage = (downloaded / total) * 100
                print(f"\rDownloading: {percentage:.1f}%", end='', flush=True)
        elif d['status'] == 'finished':
            print("\nDownload completed!")
    
    def process_input(self, input_path: str) -> Path:
        if self.is_youtube_url(input_path):
            print(f"Detected YouTube URL: {input_path}")
            return self.download_youtube_video(input_path)
        elif Path(input_path).exists() and Path(input_path).is_file():
            print(f"Using local video file: {input_path}")
            return Path(input_path)
        else:
            raise ValueError(f"Invalid input: {input_path}. Must be a YouTube URL or valid file path.")