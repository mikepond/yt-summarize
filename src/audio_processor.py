import os
from pathlib import Path
import ffmpeg
import subprocess


class AudioProcessor:
    def __init__(self, temp_dir: str = "./temp"):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(exist_ok=True)
        self._check_ffmpeg()
    
    def _check_ffmpeg(self):
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError("ffmpeg not found. Please install ffmpeg: brew install ffmpeg")
    
    def extract_audio(self, video_path: Path, output_format: str = "mp3") -> Path:
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        output_filename = f"{video_path.stem}_audio.{output_format}"
        output_path = self.temp_dir / output_filename
        
        print(f"Extracting audio from {video_path.name}...")
        
        try:
            stream = ffmpeg.input(str(video_path))
            audio = stream.audio
            
            if output_format == "mp3":
                audio = ffmpeg.output(audio, str(output_path), 
                                    acodec='libmp3lame', 
                                    audio_bitrate='192k')
            elif output_format == "wav":
                audio = ffmpeg.output(audio, str(output_path), 
                                    acodec='pcm_s16le', 
                                    ar='16000')
            else:
                audio = ffmpeg.output(audio, str(output_path))
            
            ffmpeg.run(audio, overwrite_output=True, quiet=True)
            
            print(f"Audio extracted successfully: {output_path.name}")
            return output_path
            
        except ffmpeg.Error as e:
            raise Exception(f"Failed to extract audio: {str(e)}")
    
    def get_audio_duration(self, audio_path: Path) -> float:
        try:
            probe = ffmpeg.probe(str(audio_path))
            duration = float(probe['streams'][0]['duration'])
            return duration
        except Exception as e:
            print(f"Warning: Could not get audio duration: {e}")
            return 0.0