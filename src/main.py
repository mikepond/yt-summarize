#!/usr/bin/env python3
import os
import sys
from pathlib import Path
import click
from dotenv import load_dotenv
from typing import Optional

from video_handler import VideoHandler
from audio_processor import AudioProcessor
from transcription import TranscriptionService
from summarizer import Summarizer
from output_generator import OutputGenerator


# Load environment variables
load_dotenv()


class VideoSummarizer:
    def __init__(self):
        self.video_handler = VideoHandler()
        self.audio_processor = AudioProcessor()
        self.transcription_service = TranscriptionService()
        self.summarizer = Summarizer()
        self.output_generator = OutputGenerator()
        
    def process(self, 
                input_path: str,
                summary_style: str = "detailed",
                include_transcript: bool = False,
                generate_audio: bool = True,
                voice: str = "alloy",
                language: Optional[str] = None):
        
        try:
            # Step 1: Handle video input
            print("\n🎬 Processing video input...")
            video_path = self.video_handler.process_input(input_path)
            video_title = video_path.stem
            
            # Step 2: Extract audio
            print("\n🎵 Extracting audio...")
            audio_path = self.audio_processor.extract_audio(video_path)
            
            # Step 3: Transcribe audio
            print("\n📝 Transcribing audio...")
            transcript_data = self.transcription_service.transcribe_audio(audio_path, language)
            
            # Step 4: Generate summary
            print("\n🤖 Generating summary...")
            summary_data = self.summarizer.summarize_transcript(
                transcript_data["text"], 
                style=summary_style
            )
            
            # Step 5: Generate chapters (optional) - currently disabled as segments are not available
            chapters = None
            # Note: Chapter generation is currently disabled as the API no longer provides segments
            
            # Step 6: Generate markdown output
            print("\n📄 Creating markdown summary...")
            markdown_path = self.output_generator.generate_markdown(
                video_title,
                summary_data,
                transcript_data,
                video_url=input_path if self.video_handler.is_youtube_url(input_path) else None,
                include_transcript=include_transcript,
                chapters=chapters
            )
            
            # Step 7: Generate audio summary (optional)
            audio_summary_path = None
            if generate_audio:
                print("\n🔊 Generating audio summary...")
                audio_text = self.output_generator.create_summary_text_for_audio(summary_data, video_title)
                audio_summary_path = self.output_generator.generate_audio_summary(
                    audio_text,
                    video_title,
                    voice=voice
                )
            
            # Cleanup temporary files
            self._cleanup_temp_files(video_path, audio_path, input_path)
            
            print("\n✅ Summary generation complete!")
            print(f"\n📁 Output files:")
            print(f"   - Markdown: {markdown_path}")
            if audio_summary_path:
                print(f"   - Audio: {audio_summary_path}")
            
            return {
                "markdown_path": markdown_path,
                "audio_path": audio_summary_path,
                "summary": summary_data
            }
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            raise
    
    def _cleanup_temp_files(self, video_path: Path, audio_path: Path, original_input: str):
        """Clean up temporary files, but keep original video if it was a local file"""
        if self.video_handler.is_youtube_url(original_input):
            # Delete downloaded video
            if video_path.exists():
                video_path.unlink()
        
        # Always delete extracted audio
        if audio_path.exists():
            audio_path.unlink()


@click.command()
@click.argument('input_path', type=str)
@click.option('--style', '-s', 
              type=click.Choice(['brief', 'detailed', 'bullet']), 
              default='detailed',
              help='Summary style')
@click.option('--include-transcript', '-t', 
              is_flag=True,
              help='Include full transcript in markdown')
@click.option('--no-audio', 
              is_flag=True,
              help='Skip audio summary generation')
@click.option('--voice', '-v',
              type=click.Choice(['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer']),
              default='alloy',
              help='Voice for audio summary')
@click.option('--language', '-l',
              type=str,
              default=None,
              help='Language code for transcription (e.g., en, es, fr)')
def main(input_path: str, 
         style: str, 
         include_transcript: bool, 
         no_audio: bool,
         voice: str,
         language: Optional[str]):
    """
    Summarize YouTube videos or local video files.
    
    INPUT_PATH can be either a YouTube URL or a path to a local video file.
    
    Examples:
    
        # Summarize a YouTube video
        python main.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        
        # Summarize a local video with brief summary
        python main.py /path/to/video.mp4 --style brief
        
        # Include full transcript and skip audio generation
        python main.py "https://youtu.be/..." --include-transcript --no-audio
    """
    
    print("🎥 YouTube Video Summarizer")
    print("=" * 50)
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("\n❌ Error: OPENAI_API_KEY not found in environment variables.")
        print("Please set your OpenAI API key:")
        print("  export OPENAI_API_KEY='your-api-key-here'")
        print("\nOr create a .env file with:")
        print("  OPENAI_API_KEY=your-api-key-here")
        sys.exit(1)
    
    # Process the video
    summarizer = VideoSummarizer()
    summarizer.process(
        input_path,
        summary_style=style,
        include_transcript=include_transcript,
        generate_audio=not no_audio,
        voice=voice,
        language=language
    )


if __name__ == "__main__":
    main()