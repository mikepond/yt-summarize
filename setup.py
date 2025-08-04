from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="yt-summarize",
    version="1.0.0",
    author="Your Name",
    description="A YouTube video summarizer using OpenAI APIs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/yt-summarize",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Video",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "yt-dlp>=2024.1.0",
        "ffmpeg-python>=0.2.0",
        "openai>=1.0.0",
        "pydub>=0.25.1",
        "click>=8.1.0",
        "python-dotenv>=1.0.0",
        "tqdm>=4.66.0",
        "requests>=2.31.0",
    ],
    entry_points={
        "console_scripts": [
            "yt-summarize=src.main:main",
        ],
    },
)