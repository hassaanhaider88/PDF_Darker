#!/usr/bin/env python3
"""
YouTube HD Downloader CLI Tool
Downloads video and audio separately, then merges into HD quality

REQUIREMENTS:
    pip install yt-dlp

SYSTEM REQUIREMENTS:
    - ffmpeg must be installed and available in PATH
      • Ubuntu/Debian: sudo apt install ffmpeg
      • macOS: brew install ffmpeg
      • Windows: https://ffmpeg.org/download.html

USAGE:
    python main.py
    python main.py --url "https://youtu.be/..."
    python main.py --url "..." --quality 1080
    python main.py --url "..." --output /path/to/folder
"""

import os
import sys
import re
import shutil
import argparse
import subprocess
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    print("\n❌ Error: yt-dlp is not installed!")
    print("   Install it with: pip install yt-dlp\n")
    sys.exit(1)


def check_ffmpeg():
    """Check if ffmpeg is installed."""
    if shutil.which("ffmpeg") is None:
        print("\n❌ Error: FFmpeg is not installed!")
        print("   FFmpeg is required to merge video and audio.")
        print("\n   Installation instructions:")
        print("   • Ubuntu/Debian: sudo apt install ffmpeg")
        print("   • macOS: brew install ffmpeg")
        print("   • Windows: Download from https://ffmpeg.org/download.html\n")
        sys.exit(1)
    return True


def sanitize_filename(name: str) -> str:
    """Remove invalid characters from filename."""
    return re.sub(r'[\\/*?:"<>|]', "_", name)[:200]


def get_video_info(url: str) -> dict:
    """Fetch video metadata."""
    print("\n📡 Fetching video information...")
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info
    except Exception as e:
        print(f"\n❌ Error fetching video info: {e}")
        sys.exit(1)


def display_video_info(info: dict):
    """Display video metadata in a nice format."""
    print("\n" + "=" * 70)
    print(f"📹 Title    : {info.get('title', 'Unknown')}")
    print(f"👤 Uploader : {info.get('uploader', 'Unknown')}")
    print(f"⏱️  Duration : {info.get('duration', 0) // 60} min {info.get('duration', 0) % 60} sec")
    print(f"👁️  Views    : {info.get('view_count', 0):,}")
    print("=" * 70)


def download_video(url: str, output_dir: Path, quality: str = "best") -> str:
    """
    Download video and audio separately, then merge them.
    This ensures the best quality by selecting optimal streams.
    """
    print("\n🎬 Starting HD download process...")
    print(f"   Quality: {quality}")
    print(f"   Output: {output_dir}")
    
    # Create output directory
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine format selection based on quality
    if quality == "best":
        format_str = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best"
        print("   Format: Best available quality")
    elif quality == "4k" or quality == "2160":
        format_str = "bestvideo[height<=2160][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=2160]+bestaudio/best[height<=2160]"
        print("   Format: 4K (2160p)")
    elif quality == "2k" or quality == "1440":
        format_str = "bestvideo[height<=1440][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1440]+bestaudio/best[height<=1440]"
        print("   Format: 2K (1440p)")
    elif quality == "1080":
        format_str = "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best[height<=1080]"
        print("   Format: Full HD (1080p)")
    elif quality == "720":
        format_str = "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=720]+bestaudio/best[height<=720]"
        print("   Format: HD (720p)")
    else:
        format_str = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best"
        print("   Format: Best available quality")
    
    # Download options
    ydl_opts = {
        'format': format_str,
        'outtmpl': str(output_dir / '%(title)s.%(ext)s'),
        'merge_output_format': 'mp4',
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
        'postprocessor_args': [
            '-c:v', 'copy',      # Copy video stream (no re-encoding)
            '-c:a', 'aac',       # Convert audio to AAC
            '-b:a', '192k',      # Audio bitrate 192k
        ],
        'prefer_ffmpeg': True,
        'keepvideo': False,
        'quiet': False,
        'no_warnings': False,
        'progress_hooks': [download_progress_hook],
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Download and merge
            info = ydl.extract_info(url, download=True)
            
            # Get the final filename
            filename = ydl.prepare_filename(info)
            # Handle the case where extension might change after processing
            if not os.path.exists(filename):
                # Try with .mp4 extension
                filename = os.path.splitext(filename)[0] + '.mp4'
            
            if os.path.exists(filename):
                file_size = os.path.getsize(filename) / (1024 * 1024)  # Convert to MB
                print(f"\n✅ Download complete!")
                print(f"   File: {Path(filename).name}")
                print(f"   Size: {file_size:.1f} MB")
                print(f"   Path: {filename}")
                return filename
            else:
                print(f"\n⚠️  File saved but path not found. Check output directory: {output_dir}")
                return None
                
    except Exception as e:
        print(f"\n❌ Download error: {e}")
        sys.exit(1)


def download_progress_hook(d):
    """Display download progress."""
    if d['status'] == 'downloading':
        # Get progress information
        total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
        downloaded = d.get('downloaded_bytes', 0)
        speed = d.get('speed', 0)
        
        if total > 0:
            percent = (downloaded / total) * 100
            downloaded_mb = downloaded / (1024 * 1024)
            total_mb = total / (1024 * 1024)
            speed_mb = (speed / (1024 * 1024)) if speed else 0
            
            # Create progress bar
            bar_length = 40
            filled = int(bar_length * downloaded / total)
            bar = '█' * filled + '░' * (bar_length - filled)
            
            print(f"\r   Progress: [{bar}] {percent:.1f}% | "
                  f"{downloaded_mb:.1f}/{total_mb:.1f} MB | "
                  f"Speed: {speed_mb:.2f} MB/s", end='', flush=True)
    
    elif d['status'] == 'finished':
        print("\n   ✓ Download finished, now merging...")


def prompt_url():
    """Prompt user for YouTube URL."""
    print("\n" + "=" * 70)
    url = input("🔗 Enter YouTube URL: ").strip()
    
    if not url:
        print("❌ No URL provided!")
        sys.exit(1)
    
    # Basic URL validation
    if 'youtube.com' not in url and 'youtu.be' not in url:
        print("⚠️  Warning: This doesn't look like a YouTube URL!")
        confirm = input("   Continue anyway? (y/n): ").strip().lower()
        if confirm != 'y':
            sys.exit(1)
    
    return url


def prompt_quality():
    """Prompt user for video quality."""
    print("\n📊 Select quality:")
    print("   1. Best available (default)")
    print("   2. 4K (2160p)")
    print("   3. 2K (1440p)")
    print("   4. Full HD (1080p)")
    print("   5. HD (720p)")
    
    choice = input("\n   Choice (1-5, default=1): ").strip()
    
    quality_map = {
        '1': 'best',
        '2': '2160',
        '3': '1440',
        '4': '1080',
        '5': '720',
        '': 'best',  # Default
    }
    
    return quality_map.get(choice, 'best')


def prompt_output_dir():
    """Prompt user for output directory."""
    default_dir = Path.cwd() / "downloads"
    print(f"\n📁 Output directory (default: {default_dir})")
    output = input("   Path (press Enter for default): ").strip()
    
    if not output:
        return default_dir
    
    return Path(output)


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="YouTube HD Downloader - Downloads video and audio separately, then merges",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py
  python main.py --url "https://youtu.be/dQw4w9WgXcQ"
  python main.py --url "..." --quality 1080
  python main.py --url "..." --quality best --output ./my_videos
        """
    )
    
    parser.add_argument('--url', type=str, help='YouTube video URL')
    parser.add_argument('--quality', type=str, 
                       choices=['best', '4k', '2160', '2k', '1440', '1080', '720'],
                       help='Video quality (best/4k/2k/1080/720)')
    parser.add_argument('--output', type=str, help='Output directory path')
    
    args = parser.parse_args()
    
    # Print banner
    print("\n" + "=" * 70)
    print("   🎬 YouTube HD Downloader")
    print("   Downloads video + audio separately, then merges in HD quality")
    print("=" * 70)
    
    # Check ffmpeg
    check_ffmpeg()
    
    # Get URL
    url = args.url if args.url else prompt_url()
    
    # Get video info
    info = get_video_info(url)
    display_video_info(info)
    
    # Get quality
    quality = args.quality if args.quality else prompt_quality()
    
    # Get output directory
    output_dir = Path(args.output) if args.output else prompt_output_dir()
    
    # Confirm
    print("\n" + "=" * 70)
    print(f"✓ URL     : {url}")
    print(f"✓ Quality : {quality}")
    print(f"✓ Output  : {output_dir}")
    print("=" * 70)
    
    confirm = input("\n▶  Start download? (Y/n): ").strip().lower()
    if confirm and confirm != 'y':
        print("\n❌ Download cancelled.")
        sys.exit(0)
    
    # Download
    output_file = download_video(url, output_dir, quality)
    
    if output_file:
        print("\n" + "=" * 70)
        print("   ✅ SUCCESS!")
        print("=" * 70)
        print(f"\n   Your video is ready: {output_file}\n")
    else:
        print("\n❌ Download completed but file path unknown. Check output directory.")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Download interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)