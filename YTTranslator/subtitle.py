# ╔══════════════════════════════════════════════════════════════╗
# ║          YouTube HD Downloader + Auto Subtitle Burner        ║
# ║                  CLI Tool — Full Pipeline                    ║
# ╚══════════════════════════════════════════════════════════════╝

# REQUIREMENTS (install before running):
#     pip install yt-dlp openai-whisper rich colorama

# SYSTEM REQUIREMENTS:
#     - ffmpeg must be installed and available in PATH
#       • Ubuntu/Debian : sudo apt install ffmpeg
#       • macOS         : brew install ffmpeg
#       • Windows       : https://ffmpeg.org/download.html

# USAGE:
#     python subtitle.py
#     python subtitle.py --url "https://youtu.be/..."
#     python subtitle.py --url "..." --model large --style neon
#     python subtitle.py --language fr --position center

# NEW FEATURES:
#     • Subtitle language selection (Whisper multilingual transcription)
#     • Subtitle position: bottom (default) or center of screen
#     • Auto-detects .mp4 files in ~/SubtitleAble folder — no URL needed
#     • Exports a .vtt file alongside the burned video (exact timeline + text)
# """

# import os
# import sys
# import shutil
# import argparse
# import tempfile
# import subprocess
# import textwrap
# from pathlib import Path
# from datetime import timedelta

# # ── Dependency checks ──────────────────────────────────────────────────────────
# def check_dependencies():
#     missing_pip, missing_sys = [], []

#     try:
#         import yt_dlp          # noqa: F401
#     except ImportError:
#         missing_pip.append("yt-dlp")

#     try:
#         import whisper         # noqa: F401
#     except ImportError:
#         missing_pip.append("openai-whisper")

#     try:
#         import rich            # noqa: F401
#     except ImportError:
#         missing_pip.append("rich")

#     if shutil.which("ffmpeg") is None:
#         missing_sys.append("ffmpeg")

#     if missing_pip or missing_sys:
#         print("\n❌  Missing dependencies detected!\n")
#         if missing_pip:
#             print(f"  Install Python packages :  pip install {' '.join(missing_pip)}")
#         if missing_sys:
#             print(f"  Install system tools     :  {', '.join(missing_sys)}")
#             print("    Ubuntu/Debian : sudo apt install ffmpeg")
#             print("    macOS         : brew install ffmpeg")
#             print("    Windows       : https://ffmpeg.org/download.html")
#         print()
#         sys.exit(1)

# check_dependencies()

# # ── Imports after dependency check ─────────────────────────────────────────────
# import yt_dlp
# import whisper
# from rich.console import Console
# from rich.panel import Panel
# from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
# from rich.prompt import Prompt, Confirm
# from rich.table import Table
# from rich.text import Text
# from rich import box
# from rich.style import Style
# from rich.align import Align

# console = Console()

# # ══════════════════════════════════════════════════════════════════════════════
# #  SUBTITLE FOLDER
# # ══════════════════════════════════════════════════════════════════════════════
# SUBTITLEABLE_FOLDER = Path.home() / "SubtitleAble"

# # ══════════════════════════════════════════════════════════════════════════════
# #  LANGUAGE OPTIONS (Whisper-supported languages)
# # ══════════════════════════════════════════════════════════════════════════════
# LANGUAGES = {
#     "auto":  "Auto-detect",
#     "en":    "English",
#     "ur":    "Urdu",
#     "ar":    "Arabic",
#     "zh":    "Chinese",
#     "fr":    "French",
#     "de":    "German",
#     "es":    "Spanish",
#     "hi":    "Hindi",
#     "it":    "Italian",
#     "ja":    "Japanese",
#     "ko":    "Korean",
#     "pt":    "Portuguese",
#     "ru":    "Russian",
#     "tr":    "Turkish",
# }

# # ══════════════════════════════════════════════════════════════════════════════
# #  SUBTITLE POSITION OPTIONS
# #  ASS Alignment values: 2 = bottom-center, 5 = middle-center (true center)
# # ══════════════════════════════════════════════════════════════════════════════
# POSITIONS = {
#     "bottom": {"label": "⬇️   Bottom", "alignment": 2, "marginv": 40},
#     "center": {"label": "⏺️   Center", "alignment": 5, "marginv": 0},
# }

# # ══════════════════════════════════════════════════════════════════════════════
# #  SUBTITLE STYLE PRESETS
# # ══════════════════════════════════════════════════════════════════════════════
# def build_style_string(base_style: dict, alignment: int, marginv: int) -> dict:
#     """Rebuild style strings with the chosen alignment and margin."""
#     # Patch ass_style: field 18 (0-indexed) is Alignment, field 21 is MarginV
#     parts = base_style["ass_style"].split(",")
#     parts[18] = str(alignment)
#     parts[21] = str(marginv)
#     patched_ass = ",".join(parts)

#     # Patch ffmpeg_force_style
#     force = base_style["ffmpeg_force_style"]
#     import re
#     force = re.sub(r"Alignment=\d+", f"Alignment={alignment}", force)
#     force = re.sub(r"MarginV=\d+", f"MarginV={marginv}", force)

#     return {**base_style, "ass_style": patched_ass, "ffmpeg_force_style": force}


# SUBTITLE_STYLES = {
#     "neon": {
#         "name": "🌈  Neon Glow",
#         "description": "Bright cyan text with dark semi-transparent background",
#         "ass_style": (
#             "Style: Default,Arial,22,&H00E0FF00,&H000000FF,&H80000000,&H80000000,"
#             "0,0,0,0,100,100,0,0,1,2.5,1.5,2,20,20,30,1"
#         ),
#         "ffmpeg_force_style": (
#             "FontName=Arial,FontSize=22,PrimaryColour=&H00FFFF&,"
#             "OutlineColour=&H000000&,BackColour=&H80000000&,"
#             "Outline=2,Shadow=2,Bold=1,Alignment=2,MarginV=30"
#         ),
#     },
#     "cinematic": {
#         "name": "🎬  Cinematic",
#         "description": "White bold text with thick black outline — movie style",
#         "ass_style": (
#             "Style: Default,Arial Black,24,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,"
#             "1,0,0,0,100,100,0,0,1,3,1,2,30,30,40,1"
#         ),
#         "ffmpeg_force_style": (
#             "FontName=Arial Black,FontSize=24,PrimaryColour=&HFFFFFF&,"
#             "OutlineColour=&H000000&,BackColour=&H00000000&,"
#             "Outline=3,Shadow=1,Bold=1,Alignment=2,MarginV=40"
#         ),
#     },
#     "elegant": {
#         "name": "✨  Elegant",
#         "description": "Gold italic text with soft dark box background",
#         "ass_style": (
#             "Style: Default,Georgia,20,&H0000D7FF,&H000000FF,&HAA000000,&H00000000,"
#             "0,1,0,0,100,100,0,0,3,1,2,2,25,25,35,1"
#         ),
#         "ffmpeg_force_style": (
#             "FontName=Georgia,FontSize=20,PrimaryColour=&H00D7FF&,"
#             "OutlineColour=&H000000&,BackColour=&HAA000000&,"
#             "Outline=1,Shadow=2,Italic=1,Alignment=2,MarginV=35,BorderStyle=4"
#         ),
#     },
#     "pop": {
#         "name": "🎵  Pop / Karaoke",
#         "description": "Yellow text with magenta outline — vibrant and fun",
#         "ass_style": (
#             "Style: Default,Impact,26,&H0000FFFF,&H00FF00FF,&H80000000,&H00000000,"
#             "0,0,0,0,100,100,0,0,1,3,2,2,20,20,35,1"
#         ),
#         "ffmpeg_force_style": (
#             "FontName=Impact,FontSize=26,PrimaryColour=&H00FFFF&,"
#             "OutlineColour=&HFF00FF&,BackColour=&H80000000&,"
#             "Outline=3,Shadow=2,Bold=1,Alignment=2,MarginV=35"
#         ),
#     },
#     "minimal": {
#         "name": "⬜  Minimal",
#         "description": "Clean white text, no background, thin outline",
#         "ass_style": (
#             "Style: Default,Helvetica,18,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,"
#             "0,0,0,0,100,100,0,0,1,1.5,0,2,20,20,25,1"
#         ),
#         "ffmpeg_force_style": (
#             "FontName=Helvetica,FontSize=18,PrimaryColour=&HFFFFFF&,"
#             "OutlineColour=&H000000&,BackColour=&H00000000&,"
#             "Outline=1.5,Shadow=0,Alignment=2,MarginV=25"
#         ),
#     },
# }

# WHISPER_MODELS = {
#     "tiny":   "Fastest  (~1 GB VRAM) — lower accuracy",
#     "base":   "Fast     (~1 GB VRAM) — good for clear speech",
#     "small":  "Balanced (~2 GB VRAM) — recommended",
#     "medium": "Accurate (~5 GB VRAM) — great quality",
#     "large":  "Best     (~10 GB VRAM) — highest accuracy",
# }

# # ══════════════════════════════════════════════════════════════════════════════
# #  BANNER
# # ══════════════════════════════════════════════════════════════════════════════
# def print_banner():
#     banner = Text()
#     banner.append("  ██╗   ██╗████████╗    ", style="bold cyan")
#     banner.append("╔═╗╦ ╦╔╗ ╔╦╗╦╔╦╗╦  ╔═╗╦═╗\n", style="bold magenta")
#     banner.append("  ╚██╗ ██╔╝╚══██╔══╝    ", style="bold cyan")
#     banner.append("╚═╗║ ║╠╩╗ ║ ║ ║ ║  ║╣ ╠╦╝\n", style="bold magenta")
#     banner.append("   ╚████╔╝    ██║       ", style="bold cyan")
#     banner.append("╚═╝╚═╝╚═╝ ╩ ╩ ╩ ╩═╝╚═╝╩╚═\n", style="bold magenta")
#     banner.append("    ╚═══╝     ╚═╝  ", style="bold cyan")
#     banner.append("  Auto HD Downloader + Subtitle Burner", style="bold yellow")

#     console.print(Panel(
#         Align.center(banner),
#         border_style="bold blue",
#         padding=(1, 4),
#         subtitle="[dim]Powered by yt-dlp · Whisper AI · FFmpeg[/dim]",
#     ))
#     console.print()


# # ══════════════════════════════════════════════════════════════════════════════
# #  SOURCE DETECTION — Local MP4 or YouTube URL
# # ══════════════════════════════════════════════════════════════════════════════
# def detect_local_video() -> str | None:
#     """
#     Scan ~/SubtitleAble for .mp4 files.
#     Returns the path of the first found file, or None if the folder is empty.
#     """
#     SUBTITLEABLE_FOLDER.mkdir(parents=True, exist_ok=True)
#     mp4_files = sorted(SUBTITLEABLE_FOLDER.glob("*.mp4"))
#     if not mp4_files:
#         return None
#     if len(mp4_files) == 1:
#         return str(mp4_files[0])

#     # Multiple files — let the user pick
#     console.print(f"\n[bold]📂  Found {len(mp4_files)} video(s) in [cyan]{SUBTITLEABLE_FOLDER}[/cyan]:[/bold]")
#     table = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan")
#     table.add_column("#", width=4)
#     table.add_column("File", style="bold yellow")
#     table.add_column("Size", style="dim", justify="right")
#     for i, f in enumerate(mp4_files, 1):
#         size_mb = f.stat().st_size / (1024 * 1024)
#         table.add_row(str(i), f.name, f"{size_mb:.1f} MB")
#     console.print(table)

#     choice = Prompt.ask("  Enter number", default="1")
#     try:
#         idx = int(choice) - 1
#         return str(mp4_files[idx]) if 0 <= idx < len(mp4_files) else str(mp4_files[0])
#     except ValueError:
#         return str(mp4_files[0])


# def prompt_source(cli_url: str | None) -> tuple[str | None, str | None]:
#     """
#     Returns (local_video_path, youtube_url).
#     Priority:
#       1. CLI --url flag
#       2. .mp4 file(s) inside ~/SubtitleAble
#       3. Ask the user for a YouTube URL
#     """
#     # CLI override always wins
#     if cli_url:
#         return None, cli_url.strip()

#     # Auto-detect local file
#     local = detect_local_video()
#     if local:
#         console.print(
#             f"\n[bold green]📹  Local video detected:[/bold green] [cyan]{Path(local).name}[/cyan]"
#         )
#         if Confirm.ask("  Use this file?", default=True):
#             return local, None

#     # Fall back to YouTube URL
#     console.print("\n[dim]No local .mp4 found in ~/SubtitleAble (or you chose not to use it).[/dim]")
#     url = Prompt.ask("[bold yellow]🔗  Paste YouTube URL[/bold yellow]").strip()
#     return None, url


# # ══════════════════════════════════════════════════════════════════════════════
# #  STEP 1 — GET VIDEO INFO (YouTube only)
# # ══════════════════════════════════════════════════════════════════════════════
# def get_video_info(url: str) -> dict:
#     console.print("[bold cyan]🔍  Fetching video information…[/bold cyan]")
#     opts = {"quiet": True, "no_warnings": True, "skip_download": True}
#     with yt_dlp.YoutubeDL(opts) as ydl:
#         info = ydl.extract_info(url, download=False)
#     return info


# def display_video_info(info: dict):
#     table = Table(box=box.ROUNDED, border_style="cyan", show_header=False, padding=(0, 1))
#     table.add_column("Field", style="bold yellow", width=14)
#     table.add_column("Value", style="white")

#     duration = str(timedelta(seconds=info.get("duration", 0)))
#     views    = f"{info.get('view_count', 0):,}" if info.get("view_count") else "N/A"
#     uploader = info.get("uploader") or info.get("channel") or "Unknown"

#     table.add_row("📹  Title",    info.get("title", "Unknown"))
#     table.add_row("👤  Uploader", uploader)
#     table.add_row("⏱️  Duration", duration)
#     table.add_row("👁️  Views",    views)
#     table.add_row("📅  Upload",   info.get("upload_date", "N/A"))

#     console.print(Panel(table, title="[bold green]Video Details[/bold green]",
#                         border_style="green", padding=(0, 1)))
#     console.print()


# # ══════════════════════════════════════════════════════════════════════════════
# #  STEP 2 — DOWNLOAD VIDEO + AUDIO IN HD
# # ══════════════════════════════════════════════════════════════════════════════
# def download_video(url: str, output_dir: str) -> str:
#     output_template = os.path.join(output_dir, "%(title)s.%(ext)s")

#     ydl_opts = {
#         "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
#         "merge_output_format": "mp4",
#         "outtmpl": output_template,
#         "quiet": False,
#         "no_warnings": False,
#         "progress_hooks": [_download_hook],
#         "postprocessors": [
#             {
#                 "key": "FFmpegVideoConvertor",
#                 "preferedformat": "mp4",
#             }
#         ],
#         "writethumbnail": False,
#         "writeinfojson": False,
#     }

#     console.print("[bold cyan]⬇️   Downloading HD video + audio…[/bold cyan]\n")
#     with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#         info = ydl.extract_info(url, download=True)
#         filename = ydl.prepare_filename(info)
#         filename = Path(filename).with_suffix(".mp4")

#     if not Path(filename).exists():
#         mp4_files = list(Path(output_dir).glob("*.mp4"))
#         if not mp4_files:
#             raise FileNotFoundError("Download completed but no .mp4 file found.")
#         filename = max(mp4_files, key=lambda f: f.stat().st_mtime)

#     console.print(f"\n[bold green]✅  Downloaded:[/bold green] {Path(filename).name}\n")
#     return str(filename)


# _last_percent = -1

# def _download_hook(d):
#     global _last_percent
#     if d["status"] == "downloading":
#         pct_raw = d.get("_percent_str", "?%").strip()
#         try:
#             pct = int(float(pct_raw.replace("%", "")))
#         except ValueError:
#             pct = -1
#         if pct != _last_percent and pct % 5 == 0:
#             speed  = d.get("_speed_str", "?").strip()
#             eta    = d.get("_eta_str", "?").strip()
#             frag   = d.get("fragment_index", "")
#             frag_t = d.get("fragment_count", "")
#             frag_s = f" (frag {frag}/{frag_t})" if frag else ""
#             console.print(
#                 f"  [cyan]{pct:>3}%[/cyan]  speed=[yellow]{speed}[/yellow]"
#                 f"  ETA=[yellow]{eta}[/yellow]{frag_s}"
#             )
#             _last_percent = pct
#     elif d["status"] == "finished":
#         _last_percent = -1


# # ══════════════════════════════════════════════════════════════════════════════
# #  STEP 3 — EXTRACT AUDIO & TRANSCRIBE WITH WHISPER
# # ══════════════════════════════════════════════════════════════════════════════
# def extract_audio(video_path: str, audio_path: str):
#     console.print("[bold cyan]🎵  Extracting audio track…[/bold cyan]")
#     cmd = [
#         "ffmpeg", "-y", "-i", video_path,
#         "-vn",
#         "-acodec", "pcm_s16le",
#         "-ar", "16000",
#         "-ac", "1",
#         audio_path,
#     ]
#     result = subprocess.run(cmd, capture_output=True, text=True)
#     if result.returncode != 0:
#         console.print(f"[red]FFmpeg error:[/red]\n{result.stderr}")
#         raise RuntimeError("Audio extraction failed.")
#     console.print("[bold green]✅  Audio extracted.[/bold green]\n")


# def transcribe_audio(audio_path: str, model_name: str, language: str) -> list[dict]:
#     """
#     Transcribe audio with Whisper.
#     language='auto' → let Whisper detect; otherwise pass the ISO code.
#     """
#     console.print(
#         f"[bold cyan]🤖  Loading Whisper model '[yellow]{model_name}[/yellow]'…[/bold cyan]"
#     )
#     lang_display = LANGUAGES.get(language, language)
#     console.print(f"[dim]    Language: {lang_display}[/dim]\n")

#     with Progress(
#         SpinnerColumn(),
#         TextColumn("[progress.description]{task.description}"),
#         TimeElapsedColumn(),
#         console=console,
#         transient=True,
#     ) as progress:
#         task = progress.add_task("Downloading / loading model…", total=None)
#         model = whisper.load_model(model_name)
#         progress.update(task, description="Transcribing audio…")

#         transcribe_kwargs = {
#             "verbose": False,
#             "word_timestamps": False,
#             "task": "transcribe",
#         }
#         if language != "auto":
#             transcribe_kwargs["language"] = language

#         result = model.transcribe(audio_path, **transcribe_kwargs)
#         progress.update(task, description="Done!")

#     segments = result.get("segments", [])
#     detected = result.get("language", "unknown")
#     console.print(
#         f"[bold green]✅  Transcription complete — {len(segments)} segments "
#         f"(detected language: [yellow]{detected}[/yellow]).[/bold green]\n"
#     )
#     return segments


# # ══════════════════════════════════════════════════════════════════════════════
# #  STEP 4a — BUILD STYLED .ASS SUBTITLE FILE
# # ══════════════════════════════════════════════════════════════════════════════
# def seconds_to_ass_time(s: float) -> str:
#     h  = int(s // 3600)
#     m  = int((s % 3600) // 60)
#     sc = s % 60
#     return f"{h}:{m:02d}:{sc:05.2f}"


# def wrap_text(text: str, max_chars: int = 42) -> str:
#     """Wrap long lines so they fit the screen."""
#     lines = textwrap.wrap(text.strip(), width=max_chars)
#     return r"\N".join(lines) if lines else text.strip()


# def build_ass_subtitles(segments: list[dict], style_key: str, position_key: str) -> str:
#     pos   = POSITIONS[position_key]
#     style = build_style_string(SUBTITLE_STYLES[style_key], pos["alignment"], pos["marginv"])
#     ass_style = style["ass_style"]

#     header = textwrap.dedent(f"""\
#         [Script Info]
#         ScriptType: v4.00+
#         PlayResX: 1920
#         PlayResY: 1080
#         ScaledBorderAndShadow: yes
#         YCbCr Matrix: None

#         [V4+ Styles]
#         Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
#         {ass_style}

#         [Events]
#         Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
#     """)

#     events = []
#     for seg in segments:
#         start = seconds_to_ass_time(seg["start"])
#         end   = seconds_to_ass_time(seg["end"])
#         text  = wrap_text(seg["text"])
#         animated_text = r"{\fad(150,150)}" + text
#         events.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{animated_text}")

#     return header + "\n".join(events) + "\n"


# # ══════════════════════════════════════════════════════════════════════════════
# #  STEP 4b — BUILD .VTT SUBTITLE FILE (exact timeline)
# # ══════════════════════════════════════════════════════════════════════════════
# def seconds_to_vtt_time(s: float) -> str:
#     """Convert seconds to WebVTT timestamp: HH:MM:SS.mmm"""
#     h   = int(s // 3600)
#     m   = int((s % 3600) // 60)
#     sec = int(s % 60)
#     ms  = int(round((s % 1) * 1000))
#     return f"{h:02d}:{m:02d}:{sec:02d}.{ms:03d}"


# def build_vtt(segments: list[dict]) -> str:
#     """
#     Build a standards-compliant WebVTT string from Whisper segments.
#     Each cue uses the exact start/end timestamps from Whisper — no rounding.
#     """
#     lines = ["WEBVTT\n"]
#     for i, seg in enumerate(segments, 1):
#         start = seconds_to_vtt_time(seg["start"])
#         end   = seconds_to_vtt_time(seg["end"])
#         text  = seg["text"].strip()
#         lines.append(f"\n{i}")
#         lines.append(f"{start} --> {end}")
#         lines.append(text)
#     return "\n".join(lines) + "\n"


# def save_vtt(segments: list[dict], output_path: str):
#     """Write .vtt file next to the final video."""
#     vtt_content = build_vtt(segments)
#     with open(output_path, "w", encoding="utf-8") as f:
#         f.write(vtt_content)
#     console.print(f"[bold green]✅  VTT subtitle file saved:[/bold green] [cyan]{Path(output_path).name}[/cyan]\n")


# # ══════════════════════════════════════════════════════════════════════════════
# #  STEP 5 — BURN SUBTITLES INTO VIDEO
# # ══════════════════════════════════════════════════════════════════════════════
# def burn_subtitles(video_path: str, ass_path: str, output_path: str):
#     """
#     Burn an .ass subtitle file into a video using FFmpeg.

#     Windows-safe strategy: chdir into the .ass directory and pass only the
#     bare filename to avoid drive-letter colon conflicts in the filtergraph.
#     """
#     console.print("[bold cyan]🔥  Burning subtitles into video…[/bold cyan]")

#     ass_dir      = os.path.dirname(os.path.abspath(ass_path))
#     ass_filename = os.path.basename(ass_path)
#     video_abs    = os.path.abspath(video_path)
#     output_abs   = os.path.abspath(output_path)

#     cmd = [
#         "ffmpeg", "-y",
#         "-i", video_abs,
#         "-vf", f"ass={ass_filename}",
#         "-c:v", "libx264",
#         "-crf", "18",
#         "-preset", "fast",
#         "-c:a", "aac",
#         "-b:a", "192k",
#         "-movflags", "+faststart",
#         output_abs,
#     ]

#     stderr_lines = []
#     original_dir = os.getcwd()

#     try:
#         os.chdir(ass_dir)

#         with Progress(
#             SpinnerColumn(),
#             TextColumn("[progress.description]{task.description}"),
#             BarColumn(),
#             TimeElapsedColumn(),
#             console=console,
#             transient=True,
#         ) as progress:
#             task = progress.add_task("Encoding video…", total=None)
#             proc = subprocess.Popen(
#                 cmd,
#                 stderr=subprocess.PIPE,
#                 stdout=subprocess.DEVNULL,
#                 text=True,
#                 encoding="utf-8",
#                 errors="replace",
#             )

#             for line in proc.stderr:
#                 stderr_lines.append(line)
#                 if "frame=" in line:
#                     progress.update(task, description=f"Encoding… {line.strip()[:60]}")

#             proc.wait()

#     finally:
#         os.chdir(original_dir)

#     if proc.returncode != 0:
#         console.print("\n[bold red]FFmpeg error output (last 20 lines):[/bold red]")
#         for ln in stderr_lines[-20:]:
#             console.print(f"  [red]{ln.rstrip()}[/red]")
#         raise RuntimeError("FFmpeg subtitle burning failed. See error output above.")

#     console.print(f"[bold green]✅  Subtitle video saved.[/bold green]\n")


# # ══════════════════════════════════════════════════════════════════════════════
# #  INTERACTIVE PROMPTS
# # ══════════════════════════════════════════════════════════════════════════════
# def prompt_output_dir() -> str:
#     default = str(Path.home() / "Downloads")
#     path = Prompt.ask(
#         "[bold yellow]📁  Output folder[/bold yellow]",
#         default=default,
#     ).strip()
#     Path(path).mkdir(parents=True, exist_ok=True)
#     return path


# def prompt_model(cli_model: str | None) -> str:
#     if cli_model and cli_model in WHISPER_MODELS:
#         return cli_model

#     console.print("\n[bold]🧠  Choose Whisper transcription model:[/bold]")
#     table = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan")
#     table.add_column("#",      width=4)
#     table.add_column("Model",  style="bold yellow", width=8)
#     table.add_column("Info",   style="dim")

#     for i, (k, v) in enumerate(WHISPER_MODELS.items(), 1):
#         table.add_row(str(i), k, v)
#     console.print(table)

#     choice = Prompt.ask("  Enter number", default="3")
#     keys = list(WHISPER_MODELS.keys())
#     try:
#         idx = int(choice) - 1
#         return keys[idx] if 0 <= idx < len(keys) else "small"
#     except ValueError:
#         return "small"


# def prompt_style(cli_style: str | None) -> str:
#     if cli_style and cli_style in SUBTITLE_STYLES:
#         return cli_style

#     console.print("\n[bold]🎨  Choose subtitle style:[/bold]")
#     table = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan")
#     table.add_column("#",           width=4)
#     table.add_column("Style",       style="bold yellow", width=14)
#     table.add_column("Description", style="dim")

#     for i, (k, v) in enumerate(SUBTITLE_STYLES.items(), 1):
#         table.add_row(str(i), v["name"], v["description"])
#     console.print(table)

#     choice = Prompt.ask("  Enter number", default="1")
#     keys = list(SUBTITLE_STYLES.keys())
#     try:
#         idx = int(choice) - 1
#         return keys[idx] if 0 <= idx < len(keys) else "neon"
#     except ValueError:
#         return "neon"


# def prompt_language(cli_language: str | None) -> str:
#     """Ask the user which language the subtitles should be in."""
#     if cli_language and cli_language in LANGUAGES:
#         return cli_language

#     console.print("\n[bold]🌐  Choose subtitle language:[/bold]")
#     table = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan")
#     table.add_column("#",        width=4)
#     table.add_column("Code",     style="bold yellow", width=6)
#     table.add_column("Language", style="dim")

#     for i, (code, name) in enumerate(LANGUAGES.items(), 1):
#         table.add_row(str(i), code, name)
#     console.print(table)

#     choice = Prompt.ask("  Enter number (1 = auto-detect)", default="1")
#     keys = list(LANGUAGES.keys())
#     try:
#         idx = int(choice) - 1
#         return keys[idx] if 0 <= idx < len(keys) else "auto"
#     except ValueError:
#         return "auto"


# def prompt_position(cli_position: str | None) -> str:
#     """Ask the user where to place the subtitles."""
#     if cli_position and cli_position in POSITIONS:
#         return cli_position

#     console.print("\n[bold]📐  Choose subtitle position:[/bold]")
#     table = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan")
#     table.add_column("#",        width=4)
#     table.add_column("Position", style="bold yellow", width=10)

#     for i, (key, val) in enumerate(POSITIONS.items(), 1):
#         table.add_row(str(i), val["label"])
#     console.print(table)

#     choice = Prompt.ask("  Enter number (1 = bottom)", default="1")
#     keys = list(POSITIONS.keys())
#     try:
#         idx = int(choice) - 1
#         return keys[idx] if 0 <= idx < len(keys) else "bottom"
#     except ValueError:
#         return "bottom"


# # ══════════════════════════════════════════════════════════════════════════════
# #  CLEANUP
# # ══════════════════════════════════════════════════════════════════════════════
# def cleanup(paths: list[str]):
#     for p in paths:
#         try:
#             if p and Path(p).exists():
#                 Path(p).unlink()
#                 console.print(f"[dim]🗑️   Deleted temporary file: {Path(p).name}[/dim]")
#         except Exception as e:
#             console.print(f"[yellow]⚠️  Could not delete {p}: {e}[/yellow]")


# # ══════════════════════════════════════════════════════════════════════════════
# #  MAIN PIPELINE
# # ══════════════════════════════════════════════════════════════════════════════
# def main():
#     parser = argparse.ArgumentParser(
#         description="YouTube/Local HD Video Subtitle Burner",
#         formatter_class=argparse.RawDescriptionHelpFormatter,
#         epilog=textwrap.dedent("""\
#             Examples:
#               python subtitle.py
#               python subtitle.py --url "https://youtu.be/dQw4w9WgXcQ"
#               python subtitle.py --url "..." --model medium --style cinematic
#               python subtitle.py --language ur --position center
#               python subtitle.py --url "..." --keep-original
#         """),
#     )
#     parser.add_argument("--url",           type=str, help="YouTube video URL")
#     parser.add_argument("--output",        type=str, help="Output folder path")
#     parser.add_argument(
#         "--model", type=str,
#         choices=list(WHISPER_MODELS.keys()),
#         help="Whisper model (tiny/base/small/medium/large)",
#     )
#     parser.add_argument(
#         "--style", type=str,
#         choices=list(SUBTITLE_STYLES.keys()),
#         help="Subtitle style preset",
#     )
#     parser.add_argument(
#         "--language", type=str,
#         choices=list(LANGUAGES.keys()),
#         help="Subtitle language ISO code (e.g. en, ur, ar) or 'auto'",
#     )
#     parser.add_argument(
#         "--position", type=str,
#         choices=list(POSITIONS.keys()),
#         help="Subtitle position: bottom (default) or center",
#     )
#     parser.add_argument(
#         "--keep-original", action="store_true",
#         help="Keep the original downloaded video (default: delete after processing)",
#     )
#     args = parser.parse_args()

#     # ── Banner ────────────────────────────────────────────────────────────────
#     print_banner()

#     # ── Source: local file OR YouTube URL ─────────────────────────────────────
#     local_video_path, url = prompt_source(args.url)

#     # ── Other inputs ──────────────────────────────────────────────────────────
#     output_dir    = args.output or prompt_output_dir()
#     model_name    = prompt_model(args.model)
#     style_key     = prompt_style(args.style)
#     language_key  = prompt_language(args.language)
#     position_key  = prompt_position(args.position)

#     # ── Configuration summary ─────────────────────────────────────────────────
#     source_display = Path(local_video_path).name if local_video_path else url
#     console.print()
#     console.print(Panel(
#         f"[yellow]Source:[/yellow]   {source_display}\n"
#         f"[yellow]Output:[/yellow]   {output_dir}\n"
#         f"[yellow]Model:[/yellow]    {model_name}\n"
#         f"[yellow]Style:[/yellow]    {SUBTITLE_STYLES[style_key]['name']}\n"
#         f"[yellow]Language:[/yellow] {LANGUAGES.get(language_key, language_key)}\n"
#         f"[yellow]Position:[/yellow] {POSITIONS[position_key]['label']}",
#         title="[bold green]Configuration[/bold green]",
#         border_style="green",
#         padding=(0, 2),
#     ))
#     console.print()

#     if not Confirm.ask("[bold]▶  Start processing?[/bold]", default=True):
#         console.print("[yellow]Aborted.[/yellow]")
#         sys.exit(0)

#     # ── Temp workspace ────────────────────────────────────────────────────────
#     temp_dir            = tempfile.mkdtemp(prefix="yt_subtitler_")
#     original_video_path = None
#     audio_path          = None
#     ass_path            = None

#     try:
#         # ── Determine the video to process ───────────────────────────────────
#         if local_video_path:
#             # Use the local file directly — no download needed
#             console.rule("[bold blue]Step 1 — Local Video[/bold blue]")
#             console.print(f"[bold green]📹  Using local file:[/bold green] {Path(local_video_path).name}")
#             original_video_path = local_video_path
#             safe_title = Path(local_video_path).stem
#         else:
#             # YouTube: fetch info then download
#             console.rule("[bold blue]Step 1 — Video Info[/bold blue]")
#             info = get_video_info(url)
#             display_video_info(info)

#             console.rule("[bold blue]Step 2 — Download HD Video[/bold blue]")
#             original_video_path = download_video(url, temp_dir)
#             safe_title = "".join(
#                 c if c.isalnum() or c in " ._-()" else "_"
#                 for c in info.get("title", "video")
#             ).strip()

#         pos_label   = position_key          # "bottom" or "center"
#         lang_label  = language_key          # "en", "ur", "auto", …
#         final_stem  = f"{safe_title}_subtitled_{lang_label}_{pos_label}"
#         final_path  = os.path.join(output_dir, f"{final_stem}.mp4")
#         vtt_path    = os.path.join(output_dir, f"{final_stem}.vtt")

#         # STEP 3 — Extract audio & transcribe
#         console.rule("[bold blue]Step 3 — Audio Extraction & Transcription[/bold blue]")
#         audio_path = os.path.join(temp_dir, "audio.wav")
#         extract_audio(original_video_path, audio_path)
#         segments = transcribe_audio(audio_path, model_name, language_key)

#         # Preview a few lines
#         if segments:
#             console.print("[bold]📝  Sample subtitles:[/bold]")
#             for seg in segments[:4]:
#                 t = str(timedelta(seconds=int(seg["start"])))
#                 console.print(f"  [dim]{t}[/dim]  {seg['text'].strip()}")
#             if len(segments) > 4:
#                 console.print(f"  [dim]… and {len(segments) - 4} more segments[/dim]")
#             console.print()

#         # STEP 4a — Build .ass subtitles
#         console.rule("[bold blue]Step 4 — Build Styled Subtitles[/bold blue]")
#         console.print(f"[bold cyan]✍️  Generating {SUBTITLE_STYLES[style_key]['name']} subtitles "
#                       f"({POSITIONS[position_key]['label']})…[/bold cyan]")
#         ass_content = build_ass_subtitles(segments, style_key, position_key)
#         ass_path    = os.path.join(temp_dir, "subtitles.ass")
#         with open(ass_path, "w", encoding="utf-8") as f:
#             f.write(ass_content)
#         console.print(f"[bold green]✅  ASS subtitle file ready ({len(segments)} cues).[/bold green]\n")

#         # STEP 4b — Save .vtt file
#         save_vtt(segments, vtt_path)

#         # STEP 5 — Burn subtitles
#         console.rule("[bold blue]Step 5 — Burn Subtitles into Video[/bold blue]")
#         burn_subtitles(original_video_path, ass_path, final_path)

#         # ── Cleanup ───────────────────────────────────────────────────────────
#         console.rule("[bold blue]Cleanup[/bold blue]")
#         to_delete = [audio_path, ass_path]
#         # Only delete the video from temp if it was downloaded there
#         if not local_video_path and not args.keep_original:
#             to_delete.append(original_video_path)
#         cleanup(to_delete)

#         try:
#             remaining = list(Path(temp_dir).iterdir())
#             for f in remaining:
#                 f.unlink(missing_ok=True)
#             shutil.rmtree(temp_dir, ignore_errors=True)
#         except Exception:
#             pass

#         # ── Final summary ─────────────────────────────────────────────────────
#         size_mb = Path(final_path).stat().st_size / (1024 * 1024)
#         console.print()
#         console.print(Panel(
#             f"[bold green]🎉  All done![/bold green]\n\n"
#             f"  [yellow]Video :[/yellow] {final_path}\n"
#             f"  [yellow]VTT   :[/yellow] {vtt_path}\n"
#             f"  [yellow]Size  :[/yellow] {size_mb:.1f} MB\n"
#             f"  [yellow]Style :[/yellow] {SUBTITLE_STYLES[style_key]['name']}\n"
#             f"  [yellow]Lang  :[/yellow] {LANGUAGES.get(language_key, language_key)}\n"
#             f"  [yellow]Pos   :[/yellow] {POSITIONS[position_key]['label']}\n"
#             f"  [yellow]Cues  :[/yellow] {len(segments)} subtitle segments",
#             border_style="bold green",
#             padding=(1, 2),
#         ))

#     except KeyboardInterrupt:
#         console.print("\n[yellow]⚠️  Interrupted by user.[/yellow]")
#         shutil.rmtree(temp_dir, ignore_errors=True)
#         sys.exit(1)

#     except Exception as e:
#         console.print(f"\n[bold red]❌  Error:[/bold red] {e}")
#         shutil.rmtree(temp_dir, ignore_errors=True)
#         sys.exit(1)


# if __name__ == "__main__":
#     main()



#!/usr/bin/env python3
"""
YouTube Audio to Translated Subtitles Tool
Checks for local videos, downloads YouTube audio, generates and translates subtitles to VTT format
"""

import os
import sys
import glob
import argparse
from pathlib import Path
from datetime import timedelta

# ══════════════════════════════════════════════════════════════════════════════
#  DEPENDENCY CHECK
# ══════════════════════════════════════════════════════════════════════════════
def check_dependencies():
    """Check if all required dependencies are installed"""
    missing = []
    
    try:
        import yt_dlp
    except ImportError:
        missing.append("yt-dlp")
    
    try:
        import whisper
    except ImportError:
        missing.append("openai-whisper")
    
    try:
        from deep_translator import GoogleTranslator
    except ImportError:
        missing.append("deep-translator")
    
    if missing:
        print("\n❌ Missing dependencies detected!")
        print(f"   Install them with: pip install {' '.join(missing)}")
        print()
        sys.exit(1)

check_dependencies()

# Import after dependency check
import yt_dlp
import whisper
from deep_translator import GoogleTranslator

# ══════════════════════════════════════════════════════════════════════════════
#  SUPPORTED LANGUAGES FOR TRANSLATION
# ══════════════════════════════════════════════════════════════════════════════
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'it': 'Italian',
    'pt': 'Portuguese',
    'ru': 'Russian',
    'ja': 'Japanese',
    'ko': 'Korean',
    'zh-CN': 'Chinese (Simplified)',
    'ar': 'Arabic',
    'hi': 'Hindi',
    'ur': 'Urdu',
    'tr': 'Turkish',
    'nl': 'Dutch',
    'pl': 'Polish',
    'sv': 'Swedish',
    'da': 'Danish',
    'no': 'Norwegian',
    'fi': 'Finnish',
}

# ══════════════════════════════════════════════════════════════════════════════
#  STEP 1: CHECK FOR LOCAL VIDEO FILES
# ══════════════════════════════════════════════════════════════════════════════
def check_for_videos(folder="."):
    """Check current folder for any video files"""
    video_extensions = ['*.mp4', '*.avi', '*.mkv', '*.mov', '*.flv', '*.wmv', '*.webm']
    video_files = []
    
    for ext in video_extensions:
        video_files.extend(glob.glob(os.path.join(folder, ext)))
    
    return video_files

# ══════════════════════════════════════════════════════════════════════════════
#  STEP 2: GET USER INPUT (YouTube URL and Target Language)
# ══════════════════════════════════════════════════════════════════════════════
def get_user_input():
    """Ask user for YouTube URL and target subtitle language"""
    print("\n" + "="*70)
    print("📹  No local video found. Let's download from YouTube!")
    print("="*70)
    
    # Get YouTube URL
    url = input("\n🔗 Enter YouTube video URL: ").strip()
    if not url:
        print("❌ Error: URL cannot be empty!")
        sys.exit(1)
    
    # Show available languages
    print("\n📝 Available languages for translation:")
    print("-" * 70)
    for code, name in sorted(SUPPORTED_LANGUAGES.items()):
        print(f"   {code:8} - {name}")
    print("-" * 70)
    
    # Get target language
    target_lang = input("\n🌍 Enter target subtitle language code (e.g., 'en', 'ur', 'ar'): ").strip().lower()
    if target_lang not in SUPPORTED_LANGUAGES:
        print(f"❌ Error: '{target_lang}' is not supported!")
        print(f"   Please choose from: {', '.join(SUPPORTED_LANGUAGES.keys())}")
        sys.exit(1)
    
    return url, target_lang

# ══════════════════════════════════════════════════════════════════════════════
#  STEP 3: DOWNLOAD AUDIO FROM YOUTUBE
# ══════════════════════════════════════════════════════════════════════════════
def download_audio(url, output_path="audio.mp3"):
    """Download only audio from YouTube video"""
    print("\n" + "="*70)
    print("🎵  STEP 3: Downloading Audio from YouTube")
    print("="*70)
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': output_path.replace('.mp3', ''),
        'quiet': False,
        'no_warnings': False,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print("⏳ Downloading audio...")
            info = ydl.extract_info(url, download=True)
            print(f"✅ Audio downloaded successfully!")
            print(f"   Title: {info.get('title', 'Unknown')}")
            print(f"   Duration: {info.get('duration', 0)} seconds")
            return output_path
    except Exception as e:
        print(f"❌ Error downloading audio: {e}")
        sys.exit(1)

# ══════════════════════════════════════════════════════════════════════════════
#  STEP 4: DETECT LANGUAGE AND TRANSCRIBE AUDIO
# ══════════════════════════════════════════════════════════════════════════════
def transcribe_and_detect_language(audio_path, model_name="base"):
    """Detect language and transcribe audio using Whisper"""
    print("\n" + "="*70)
    print("🎤  STEP 4: Detecting Language and Transcribing Audio")
    print("="*70)
    
    try:
        print(f"⏳ Loading Whisper model '{model_name}'...")
        model = whisper.load_model(model_name)
        
        print("🔍 Detecting language and transcribing...")
        result = model.transcribe(audio_path, task="transcribe", verbose=False)
        
        detected_lang = result.get('language', 'unknown')
        detected_lang_name = SUPPORTED_LANGUAGES.get(detected_lang, detected_lang)
        
        print(f"✅ Transcription complete!")
        print(f"   Detected Language: {detected_lang_name} ({detected_lang})")
        print(f"   Total Segments: {len(result['segments'])}")
        
        return result['segments'], detected_lang
        
    except Exception as e:
        print(f"❌ Error during transcription: {e}")
        sys.exit(1)

# ══════════════════════════════════════════════════════════════════════════════
#  STEP 5: CONVERT SEGMENTS TO VTT FORMAT
# ══════════════════════════════════════════════════════════════════════════════
def format_timestamp(seconds):
    """Convert seconds to VTT timestamp format (HH:MM:SS.mmm)"""
    td = timedelta(seconds=seconds)
    hours = int(td.total_seconds() // 3600)
    minutes = int((td.total_seconds() % 3600) // 60)
    secs = td.total_seconds() % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"

def create_vtt_content(segments):
    """Create VTT file content from segments"""
    vtt_lines = ["WEBVTT\n"]
    
    for i, segment in enumerate(segments, 1):
        start_time = format_timestamp(segment['start'])
        end_time = format_timestamp(segment['end'])
        text = segment['text'].strip()
        
        vtt_lines.append(f"\n{i}")
        vtt_lines.append(f"{start_time} --> {end_time}")
        vtt_lines.append(f"{text}\n")
    
    return "\n".join(vtt_lines)

def save_vtt(segments, output_path):
    """Save segments as VTT file"""
    print("\n" + "="*70)
    print("💾  STEP 5: Creating VTT Subtitle File")
    print("="*70)
    
    try:
        vtt_content = create_vtt_content(segments)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(vtt_content)
        print(f"✅ Original VTT file saved: {output_path}")
        print(f"   Total subtitle entries: {len(segments)}")
        return output_path
    except Exception as e:
        print(f"❌ Error saving VTT file: {e}")
        sys.exit(1)

# ══════════════════════════════════════════════════════════════════════════════
#  STEP 6: TRANSLATE SUBTITLES
# ══════════════════════════════════════════════════════════════════════════════
def translate_segments(segments, source_lang, target_lang):
    """Translate subtitle segments to target language"""
    print("\n" + "="*70)
    print(f"🌐  STEP 6: Translating Subtitles ({source_lang} → {target_lang})")
    print("="*70)
    
    if source_lang == target_lang:
        print("⚠️  Source and target languages are the same. Skipping translation.")
        return segments
    
    try:
        translator = GoogleTranslator(source=source_lang, target=target_lang)
        translated_segments = []
        
        total = len(segments)
        print(f"⏳ Translating {total} subtitle segments...")
        
        for i, segment in enumerate(segments, 1):
            original_text = segment['text'].strip()
            
            # Translate the text
            try:
                translated_text = translator.translate(original_text)
            except Exception as e:
                print(f"⚠️  Warning: Could not translate segment {i}: {e}")
                translated_text = original_text  # Keep original if translation fails
            
            # Create new segment with translated text
            translated_segment = {
                'start': segment['start'],
                'end': segment['end'],
                'text': translated_text
            }
            translated_segments.append(translated_segment)
            
            # Progress indicator
            if i % 10 == 0 or i == total:
                print(f"   Progress: {i}/{total} segments translated")
        
        print(f"✅ Translation complete!")
        return translated_segments
        
    except Exception as e:
        print(f"❌ Error during translation: {e}")
        print("   Continuing with original language...")
        return segments

# ══════════════════════════════════════════════════════════════════════════════
#  STEP 7: SAVE TRANSLATED VTT FILE
# ══════════════════════════════════════════════════════════════════════════════
def save_translated_vtt(segments, output_path, target_lang):
    """Save translated segments as VTT file"""
    print("\n" + "="*70)
    print(f"💾  STEP 7: Saving Translated VTT File ({target_lang})")
    print("="*70)
    
    try:
        vtt_content = create_vtt_content(segments)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(vtt_content)
        
        file_size = os.path.getsize(output_path) / 1024  # KB
        print(f"✅ Translated VTT file saved successfully!")
        print(f"   File: {output_path}")
        print(f"   Size: {file_size:.2f} KB")
        print(f"   Language: {SUPPORTED_LANGUAGES[target_lang]}")
        print(f"   Total entries: {len(segments)}")
        
        return output_path
        
    except Exception as e:
        print(f"❌ Error saving translated VTT file: {e}")
        sys.exit(1)

# ══════════════════════════════════════════════════════════════════════════════
#  MAIN FUNCTION
# ══════════════════════════════════════════════════════════════════════════════
def main():
    """Main execution function"""
    print("\n" + "="*70)
    print("🎬  YOUTUBE AUDIO TO TRANSLATED SUBTITLES TOOL")
    print("="*70)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Generate translated subtitles from YouTube videos')
    parser.add_argument('--url', type=str, help='YouTube video URL')
    parser.add_argument('--lang', type=str, help='Target subtitle language (e.g., en, ur, ar)')
    parser.add_argument('--model', type=str, default='base', 
                       choices=['tiny', 'base', 'small', 'medium', 'large'],
                       help='Whisper model size (default: base)')
    parser.add_argument('--output', type=str, default='.',
                       help='Output directory for subtitle files')
    args = parser.parse_args()
    
    # STEP 1: Check for local videos
    print("\n" + "="*70)
    print("📂  STEP 1: Checking for Local Video Files")
    print("="*70)
    
    video_files = check_for_videos()
    
    if video_files:
        print(f"✅ Found {len(video_files)} video file(s) in current folder:")
        for i, vf in enumerate(video_files, 1):
            print(f"   {i}. {os.path.basename(vf)}")
        print("\n⚠️  Note: This tool downloads YouTube audio for transcription.")
        print("   Local video processing coming in future version!")
    else:
        print("❌ No video files found in current folder.")
    
    # STEP 2: Get YouTube URL and target language
    if args.url and args.lang:
        url = args.url
        target_lang = args.lang.lower()
        if target_lang not in SUPPORTED_LANGUAGES:
            print(f"❌ Error: '{target_lang}' is not supported!")
            sys.exit(1)
    else:
        url, target_lang = get_user_input()
    
    # Create output directory if it doesn't exist
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Set file paths
    audio_file = "downloaded_audio.mp3"
    original_vtt = output_dir / "subtitles_original.vtt"
    translated_vtt = output_dir / f"subtitles_{target_lang}.vtt"
    
    try:
        # STEP 3: Download audio
        audio_path = download_audio(url, audio_file)
        
        # STEP 4: Transcribe and detect language
        segments, detected_lang = transcribe_and_detect_language(audio_path, args.model)
        
        # STEP 5: Save original VTT
        save_vtt(segments, str(original_vtt))
        
        # STEP 6: Translate subtitles
        translated_segments = translate_segments(segments, detected_lang, target_lang)
        
        # STEP 7: Save translated VTT
        final_vtt_path = save_translated_vtt(translated_segments, str(translated_vtt), target_lang)
        
        # Final summary
        print("\n" + "="*70)
        print("🎉  ALL STEPS COMPLETED SUCCESSFULLY!")
        print("="*70)
        print(f"\n📋 Summary:")
        print(f"   • Detected Language: {SUPPORTED_LANGUAGES.get(detected_lang, detected_lang)}")
        print(f"   • Target Language: {SUPPORTED_LANGUAGES[target_lang]}")
        print(f"   • Original Subtitles: {original_vtt}")
        print(f"   • Translated Subtitles: {translated_vtt}")
        print(f"   • Total Segments: {len(segments)}")
        print("\n✅ Your translated subtitle file is ready to use!")
        print("="*70 + "\n")
        
        # Cleanup audio file
        if os.path.exists(audio_file):
            os.remove(audio_file)
            print("🧹 Temporary audio file cleaned up.\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user.")
        if os.path.exists(audio_file):
            os.remove(audio_file)
        sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        if os.path.exists(audio_file):
            os.remove(audio_file)
        sys.exit(1)


if __name__ == "__main__":
    main()