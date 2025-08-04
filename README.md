# YouTube Video Summarizer

A powerful Python application that downloads YouTube videos (or processes local video files), transcribes them, and generates both text and audio summaries using OpenAI's APIs.

## Features

- 🎬 **YouTube Video Download**: Automatically downloads videos from YouTube URLs
- 📁 **Local Video Support**: Process local video files directly
- 🎵 **Audio Extraction**: Extracts audio from video files using FFmpeg
- 📝 **Automatic Transcription**: Transcribes audio using OpenAI's Whisper API
- 🤖 **Smart Summarization**: Generates intelligent summaries using GPT-4
- 📚 **Chapter Detection**: Automatically identifies logical sections in long videos
- 📄 **Markdown Output**: Creates well-formatted markdown summaries
- 🔊 **Audio Summaries**: Generates spoken summaries using OpenAI's TTS API
- 🌍 **Multi-language Support**: Transcribe and summarize videos in multiple languages

## Prerequisites

- Python 3.8 or higher
- FFmpeg installed on your system
- OpenAI API key

### Installing FFmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
Download from [FFmpeg official website](https://ffmpeg.org/download.html)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd yt-summarize
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up your OpenAI API key:
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

## Usage

### Basic Usage

Summarize a YouTube video:
```bash
python src/main.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

Summarize a local video file:
```bash
python src/main.py /path/to/video.mp4
```

### Command Line Options

- `--style, -s`: Summary style (choices: brief, detailed, bullet; default: detailed)
- `--include-transcript, -t`: Include full transcript in markdown output
- `--no-audio`: Skip audio summary generation
- `--voice, -v`: Voice for audio summary (choices: alloy, echo, fable, onyx, nova, shimmer; default: alloy)
- `--language, -l`: Language code for transcription (e.g., en, es, fr)

### Examples

Generate a brief summary without audio:
```bash
python src/main.py "https://youtu.be/..." --style brief --no-audio
```

Include full transcript with Spanish transcription:
```bash
python src/main.py video.mp4 --include-transcript --language es
```

Use a different voice for audio summary:
```bash
python src/main.py "https://youtube.com/..." --voice nova
```

## Output

The application generates:

1. **Markdown Summary** (`output/[video_title]_[timestamp].md`):
   - Video metadata (title, duration, language)
   - Table of contents with timestamps (for detailed summaries)
   - Structured summary sections
   - Optional full transcript

2. **Audio Summary** (`output/[video_title]_audio_[timestamp].mp3`):
   - Spoken version of the summary
   - Customizable voice options

## Project Structure

```
yt-summarize/
├── src/
│   ├── video_handler.py      # YouTube download and video input handling
│   ├── audio_processor.py    # Audio extraction using FFmpeg
│   ├── transcription.py      # Whisper API transcription
│   ├── summarizer.py         # GPT-4 summarization
│   ├── output_generator.py   # Markdown and audio output generation
│   └── main.py              # CLI interface and main orchestration
├── output/                   # Generated summaries
├── temp/                     # Temporary files
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variables template
└── README.md                # This file
```

## Configuration

Environment variables (in `.env`):
- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `OUTPUT_DIR`: Output directory for summaries (default: ./output)
- `TEMP_DIR`: Temporary files directory (default: ./temp)

## Summary Styles

- **Brief**: 2-3 paragraph summary focusing on key points
- **Detailed**: Comprehensive summary with overview, key points, details, and conclusion
- **Bullet**: Concise bullet-point format

## Error Handling

The application includes robust error handling for:
- Invalid YouTube URLs
- Missing video files
- API failures
- Large file processing (automatic chunking for files >25MB)
- FFmpeg availability checks

## Limitations

- Maximum video length depends on your OpenAI API rate limits
- Audio files larger than 25MB are automatically split into chunks
- Summary quality depends on audio quality and clarity

## Troubleshooting

**FFmpeg not found:**
- Ensure FFmpeg is installed and in your system PATH
- Try running `ffmpeg -version` to verify installation

**OpenAI API errors:**
- Verify your API key is correctly set in `.env`
- Check your OpenAI account has sufficient credits
- Ensure you have access to GPT-4 and Whisper APIs

**Download failures:**
- Check internet connection
- Verify the YouTube URL is valid and accessible
- Some videos may have download restrictions

## License

[Your license here]

## Contributing

[Contributing guidelines if applicable]