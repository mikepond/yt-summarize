import os
from pathlib import Path
from typing import Optional, Dict
from openai import OpenAI
from pydub import AudioSegment
import math


class TranscriptionService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided. Set OPENAI_API_KEY environment variable.")
        
        self.client = OpenAI(api_key=self.api_key)
        self.max_file_size_mb = 25  # OpenAI Whisper limit
    
    def transcribe_audio(self, audio_path: Path, language: Optional[str] = None) -> Dict:
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        file_size_mb = audio_path.stat().st_size / (1024 * 1024)
        
        if file_size_mb <= self.max_file_size_mb:
            return self._transcribe_single_file(audio_path, language)
        else:
            print(f"Audio file is {file_size_mb:.1f}MB, splitting into chunks...")
            return self._transcribe_chunked(audio_path, language)
    
    def _transcribe_single_file(self, audio_path: Path, language: Optional[str] = None) -> Dict:
        print(f"Transcribing audio file: {audio_path.name}")
        
        try:
            with open(audio_path, "rb") as audio_file:
                params = {
                    "model": "whisper-1",
                    "file": audio_file,
                    "response_format": "verbose_json"
                }
                
                if language:
                    params["language"] = language
                
                response = self.client.audio.transcriptions.create(**params)
                
                return {
                    "text": response.text,
                    "segments": response.segments if hasattr(response, 'segments') else [],
                    "language": response.language if hasattr(response, 'language') else language,
                    "duration": response.duration if hasattr(response, 'duration') else None
                }
                
        except Exception as e:
            raise Exception(f"Transcription failed: {str(e)}")
    
    def _transcribe_chunked(self, audio_path: Path, language: Optional[str] = None) -> Dict:
        audio = AudioSegment.from_file(str(audio_path))
        chunk_length_ms = 10 * 60 * 1000  # 10 minutes
        chunks = []
        
        for i in range(0, len(audio), chunk_length_ms):
            chunk = audio[i:i + chunk_length_ms]
            chunk_path = audio_path.parent / f"chunk_{i//chunk_length_ms}.mp3"
            chunk.export(str(chunk_path), format="mp3")
            chunks.append(chunk_path)
        
        full_transcript = []
        all_segments = []
        
        try:
            for i, chunk_path in enumerate(chunks):
                print(f"Transcribing chunk {i+1}/{len(chunks)}...")
                result = self._transcribe_single_file(chunk_path, language)
                full_transcript.append(result["text"])
                
                if result.get("segments"):
                    time_offset = (i * chunk_length_ms) / 1000
                    for segment in result["segments"]:
                        segment["start"] += time_offset
                        segment["end"] += time_offset
                        all_segments.append(segment)
        finally:
            for chunk_path in chunks:
                if chunk_path.exists():
                    chunk_path.unlink()
        
        return {
            "text": " ".join(full_transcript),
            "segments": all_segments,
            "language": language,
            "duration": len(audio) / 1000
        }
    
    def format_transcript_with_timestamps(self, transcript_data: Dict) -> str:
        if not transcript_data.get("segments"):
            return transcript_data["text"]
        
        formatted_lines = []
        for segment in transcript_data["segments"]:
            timestamp = f"[{self._format_timestamp(segment['start'])} - {self._format_timestamp(segment['end'])}]"
            formatted_lines.append(f"{timestamp} {segment['text'].strip()}")
        
        return "\n".join(formatted_lines)
    
    def _format_timestamp(self, seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"