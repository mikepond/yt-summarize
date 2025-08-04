import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List
from openai import OpenAI


class OutputGenerator:
    def __init__(self, output_dir: str = "./output", api_key: Optional[str] = None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None
    
    def generate_markdown(self, 
                         video_title: str,
                         summary_data: Dict,
                         transcript_data: Dict,
                         video_url: Optional[str] = None,
                         include_transcript: bool = False,
                         chapters: Optional[List[Dict]] = None) -> Path:
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c for c in video_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"{safe_title}_{timestamp}.md"
        output_path = self.output_dir / filename
        
        content = self._build_markdown_content(
            video_title,
            summary_data,
            transcript_data,
            video_url,
            include_transcript,
            chapters
        )
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Markdown summary saved: {output_path}")
        return output_path
    
    def _build_markdown_content(self,
                               video_title: str,
                               summary_data: Dict,
                               transcript_data: Dict,
                               video_url: Optional[str],
                               include_transcript: bool,
                               chapters: Optional[List[Dict]]) -> str:
        
        lines = []
        
        # Header
        lines.append(f"# {video_title}")
        lines.append("")
        lines.append(f"**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if video_url:
            lines.append(f"**Source:** [{video_url}]({video_url})")
        
        if transcript_data.get("duration"):
            duration_min = int(transcript_data["duration"] / 60)
            lines.append(f"**Duration:** {duration_min} minutes")
        
        if transcript_data.get("language"):
            lines.append(f"**Language:** {transcript_data['language']}")
        
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Chapters if available
        if chapters:
            lines.append("## Table of Contents")
            lines.append("")
            for chapter in chapters:
                lines.append(f"- [{chapter['timestamp']}] **{chapter['title']}**")
                if chapter.get('description'):
                    lines.append(f"  - {chapter['description'].strip()}")
            lines.append("")
        
        # Summary sections
        if summary_data.get("style") == "detailed" and summary_data.get("sections"):
            sections = summary_data["sections"]
            
            if sections.get("overview"):
                lines.append("## Overview")
                lines.append("")
                lines.append(sections["overview"])
                lines.append("")
            
            if sections.get("key_points"):
                lines.append("## Key Points")
                lines.append("")
                lines.append(sections["key_points"])
                lines.append("")
            
            if sections.get("details"):
                lines.append("## Important Details")
                lines.append("")
                lines.append(sections["details"])
                lines.append("")
            
            if sections.get("conclusion"):
                lines.append("## Conclusion")
                lines.append("")
                lines.append(sections["conclusion"])
                lines.append("")
        else:
            lines.append("## Summary")
            lines.append("")
            lines.append(summary_data["summary"])
            lines.append("")
        
        # Statistics
        lines.append("## Statistics")
        lines.append("")
        lines.append(f"- **Summary word count:** {summary_data.get('word_count', 'N/A')}")
        lines.append(f"- **Transcript word count:** {len(transcript_data.get('text', '').split())}")
        lines.append("")
        
        # Full transcript if requested
        if include_transcript:
            lines.append("---")
            lines.append("")
            lines.append("## Full Transcript")
            lines.append("")
            
            if transcript_data.get("segments"):
                from .transcription import TranscriptionService
                service = TranscriptionService()
                formatted_transcript = service.format_transcript_with_timestamps(transcript_data)
                lines.append(formatted_transcript)
            else:
                lines.append(transcript_data.get("text", ""))
        
        return "\n".join(lines)
    
    def generate_audio_summary(self, 
                              summary_text: str,
                              video_title: str,
                              voice: str = "alloy",
                              speed: float = 1.0) -> Optional[Path]:
        
        if not self.client:
            print("Warning: OpenAI client not initialized. Skipping audio generation.")
            return None
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = "".join(c for c in video_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"{safe_title}_audio_{timestamp}.mp3"
            output_path = self.output_dir / filename
            
            print(f"Generating audio summary with voice '{voice}'...")
            
            response = self.client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=summary_text,
                speed=speed
            )
            
            response.stream_to_file(str(output_path))
            
            print(f"Audio summary saved: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"Warning: Audio generation failed: {str(e)}")
            return None
    
    def create_summary_text_for_audio(self, summary_data: Dict, video_title: str) -> str:
        """Create a version of the summary optimized for text-to-speech"""
        
        intro = f"This is a summary of the video titled: {video_title}. "
        
        if summary_data.get("style") == "detailed" and summary_data.get("sections"):
            sections = summary_data["sections"]
            
            parts = [intro]
            
            if sections.get("overview"):
                parts.append("Overview: " + sections["overview"])
            
            if sections.get("key_points"):
                parts.append("The key points are: " + sections["key_points"])
            
            if sections.get("conclusion"):
                parts.append("In conclusion: " + sections["conclusion"])
            
            return " ".join(parts)
        else:
            return intro + summary_data["summary"]