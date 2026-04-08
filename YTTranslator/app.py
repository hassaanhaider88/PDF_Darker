# # #!/usr/bin/env python3
# # """
# # ╔══════════════════════════════════════════════════════════════╗
# # ║          YouTube Video Audio Translator — CLI Tool          ║
# # ║  Downloads, Transcribes, Translates, Syncs & Merges Audio  ║
# # ╚══════════════════════════════════════════════════════════════╝

# # Dependencies:
# #     pip install yt-dlp openai-whisper deep-translator edge-tts rich colorama

# # System requirement:
# #     ffmpeg  →  winget install ffmpeg   OR   https://ffmpeg.org/download.html
# #     (pydub is NOT required — audio is assembled purely via ffmpeg)

# # Optional neural lip-sync:
# #     Wav2Lip →  https://github.com/Rudrabha/Wav2Lip
# #                Set WAV2LIP_PATH below once installed.
# # """

# # import os
# # import sys
# # import time
# # import json
# # import shutil
# # import asyncio
# # import argparse
# # import tempfile
# # import textwrap
# # import subprocess
# # from pathlib import Path
# # from datetime import datetime

# # # ─── Wav2Lip optional path ────────────────────────────────────────────────────
# # WAV2LIP_PATH = ""   # e.g. "C:/Wav2Lip" — leave empty to skip

# # # ─── Colour helpers ───────────────────────────────────────────────────────────
# # try:
# #     from colorama import Style, init as colorama_init
# #     colorama_init(autoreset=True)
# #     def c(text, colour): return f"{colour}{text}{Style.RESET_ALL}"
# # except ImportError:
# #     def c(text, _colour): return text

# # try:
# #     from rich.console import Console
# #     from rich.panel import Panel
# #     from rich.table import Table
# #     RICH = True
# #     console = Console()
# # except ImportError:
# #     RICH = False
# #     console = None

# # # ─── Supported languages ──────────────────────────────────────────────────────
# # LANGUAGES = {
# #     "af":"Afrikaans",  "sq":"Albanian",   "ar":"Arabic",
# #     "bn":"Bengali",    "bs":"Bosnian",    "ca":"Catalan",
# #     "zh":"Chinese",    "hr":"Croatian",   "cs":"Czech",
# #     "da":"Danish",     "nl":"Dutch",      "en":"English",
# #     "eo":"Esperanto",  "et":"Estonian",   "tl":"Filipino",
# #     "fi":"Finnish",    "fr":"French",     "de":"German",
# #     "el":"Greek",      "gu":"Gujarati",   "hi":"Hindi",
# #     "hu":"Hungarian",  "id":"Indonesian", "it":"Italian",
# #     "ja":"Japanese",   "kn":"Kannada",    "ko":"Korean",
# #     "la":"Latin",      "lv":"Latvian",    "lt":"Lithuanian",
# #     "ms":"Malay",      "ml":"Malayalam",  "mr":"Marathi",
# #     "my":"Myanmar",    "ne":"Nepali",     "no":"Norwegian",
# #     "pa":"Punjabi",    "pl":"Polish",     "pt":"Portuguese",
# #     "ro":"Romanian",   "ru":"Russian",    "sr":"Serbian",
# #     "si":"Sinhala",    "sk":"Slovak",     "es":"Spanish",
# #     "su":"Sundanese",  "sw":"Swahili",    "sv":"Swedish",
# #     "ta":"Tamil",      "te":"Telugu",     "th":"Thai",
# #     "tr":"Turkish",    "uk":"Ukrainian",  "ur":"Urdu",
# #     "vi":"Vietnamese", "cy":"Welsh",
# # }

# # # ─── Edge-TTS voice map ───────────────────────────────────────────────────────
# # TTS_VOICES = {
# #     "af":"af-ZA-AdriNeural",     "sq":"sq-AL-AnilaNeural",
# #     "ar":"ar-SA-ZariyahNeural",  "bn":"bn-BD-NabanitaNeural",
# #     "bs":"bs-BA-VesnaNeural",    "ca":"ca-ES-JoanaNeural",
# #     "zh":"zh-CN-XiaoxiaoNeural", "hr":"hr-HR-GabrijelaNeural",
# #     "cs":"cs-CZ-VlastaNeural",   "da":"da-DK-ChristelNeural",
# #     "nl":"nl-NL-ColetteNeural",  "en":"en-US-JennyNeural",
# #     "et":"et-EE-AnuNeural",      "tl":"fil-PH-BlessicaNeural",
# #     "fi":"fi-FI-NooraNeural",    "fr":"fr-FR-DeniseNeural",
# #     "de":"de-DE-KatjaNeural",    "el":"el-GR-AthinaNeural",
# #     "gu":"gu-IN-DhwaniNeural",   "hi":"hi-IN-SwaraNeural",
# #     "hu":"hu-HU-NoemiNeural",    "id":"id-ID-GadisNeural",
# #     "it":"it-IT-ElsaNeural",     "ja":"ja-JP-NanamiNeural",
# #     "kn":"kn-IN-SapnaNeural",    "ko":"ko-KR-SunHiNeural",
# #     "lv":"lv-LV-EveritaNeural",  "lt":"lt-LT-OnaNeural",
# #     "ms":"ms-MY-YasminNeural",   "ml":"ml-IN-SobhanaNeural",
# #     "mr":"mr-IN-AarohiNeural",   "ne":"ne-NP-HemkalaNeural",
# #     "no":"nb-NO-PernilleNeural", "pa":"pa-IN-OjasNeural",
# #     "pl":"pl-PL-ZofiaNeural",    "pt":"pt-BR-FranciscaNeural",
# #     "ro":"ro-RO-AlinaNeural",    "ru":"ru-RU-SvetlanaNeural",
# #     "sr":"sr-RS-SophieNeural",   "si":"si-LK-ThiliniNeural",
# #     "sk":"sk-SK-ViktoriaNeural", "es":"es-ES-ElviraNeural",
# #     "sw":"sw-KE-ZuriNeural",     "sv":"sv-SE-SofieNeural",
# #     "ta":"ta-IN-PallaviNeural",  "te":"te-IN-ShrutiNeural",
# #     "th":"th-TH-PremwadeeNeural","tr":"tr-TR-EmelNeural",
# #     "uk":"uk-UA-PolinaNeural",   "ur":"ur-PK-UzmaNeural",
# #     "vi":"vi-VN-HoaiMyNeural",   "cy":"cy-GB-NiaNeural",
# # }


# # # ══════════════════════════════════════════════════════════════════════════════
# # #  Logging helpers
# # # ══════════════════════════════════════════════════════════════════════════════

# # def banner():
# #     art = r"""
# #   __  ______   ___________  _    ____ ___ ____  ___
# #   \ \/ /_  /  |_   _|  _ \| |  / ___|_ _/ ___|/ _ \
# #    \  / / /     | | | |_) | | | |  _ | |\___ \ | | |
# #    / // /_      | | |  _ <| |__| |_| || | ___) | |_| |
# #   /_//____|     |_| |_| \_\_____\____|___|____/ \___/
# #     YouTube Video Translator — CLI  (Audio Dub + Lip Sync)
# # """
# #     if RICH:
# #         console.print(Panel(art, style="bold cyan"))
# #     else:
# #         print(art)

# # def step(msg):
# #     ts = datetime.now().strftime("%H:%M:%S")
# #     if RICH:
# #         console.print(f"\n[bold cyan][{ts}][/bold cyan] [bold white]{msg}[/bold white]")
# #     else:
# #         print(f"\n[{ts}] {msg}")

# # def ok(msg):
# #     if RICH: console.print(f"  [bold green]✔[/bold green] {msg}")
# #     else:    print(f"  ✔ {msg}")

# # def warn(msg):
# #     if RICH: console.print(f"  [bold yellow]⚠[/bold yellow]  {msg}")
# #     else:    print(f"  ⚠  {msg}")

# # def err(msg):
# #     if RICH: console.print(f"\n  [bold red]✘[/bold red] {msg}")
# #     else:    print(f"\n  ✘ {msg}")
# #     sys.exit(1)

# # def info(msg):
# #     if RICH: console.print(f"     [dim]{msg}[/dim]")
# #     else:    print(f"     {msg}")


# # # ══════════════════════════════════════════════════════════════════════════════
# # #  Dependency check  (NO pydub)
# # # ══════════════════════════════════════════════════════════════════════════════

# # def check_dependencies():
# #     step("Checking dependencies …")
# #     missing = []

# #     if shutil.which("ffmpeg") is None:
# #         missing.append("ffmpeg  →  run:  winget install ffmpeg   (then reopen terminal)")

# #     pkgs = {
# #         "yt_dlp":          "yt-dlp",
# #         "whisper":         "openai-whisper",
# #         "deep_translator": "deep-translator",
# #         "edge_tts":        "edge-tts",
# #         "rich":            "rich",
# #         "colorama":        "colorama",
# #     }
# #     for mod, pip_name in pkgs.items():
# #         try:
# #             __import__(mod)
# #         except ImportError:
# #             missing.append(f"pip install {pip_name}")

# #     if missing:
# #         print()
# #         for m in missing:
# #             err_line = f"  • {m}"
# #             if RICH: console.print(f"[red]{err_line}[/red]")
# #             else:    print(err_line)
# #         err("Fix the above, then re-run the script.")

# #     ok("All dependencies OK — no pydub needed.")


# # # ══════════════════════════════════════════════════════════════════════════════
# # #  Pure-ffmpeg audio helpers
# # # ══════════════════════════════════════════════════════════════════════════════

# # def _run_ffmpeg(*args):
# #     """Run ffmpeg -y <args>. Raises RuntimeError on failure."""
# #     cmd = ["ffmpeg", "-y"] + list(str(a) for a in args)
# #     r = subprocess.run(cmd, capture_output=True, text=True)
# #     if r.returncode != 0:
# #         raise RuntimeError(r.stderr[-2000:])


# # def get_audio_duration(path: Path) -> float:
# #     r = subprocess.run(
# #         ["ffprobe", "-v", "quiet", "-print_format", "json",
# #          "-show_format", str(path)],
# #         capture_output=True, text=True
# #     )
# #     try:
# #         return float(json.loads(r.stdout)["format"]["duration"])
# #     except Exception:
# #         return 0.0


# # def make_silence(path: Path, duration: float, sr: int = 24000):
# #     duration = max(duration, 0.05)
# #     _run_ffmpeg(
# #         "-f", "lavfi", "-i", f"anullsrc=r={sr}:cl=mono",
# #         "-t", str(duration), "-ar", str(sr), "-ac", "1", path
# #     )


# # def speed_audio_ffmpeg(src: Path, dst: Path, ratio: float):
# #     """
# #     Change audio speed by `ratio` using atempo filter chains.
# #     atempo is clamped to [0.5, 2.0] per step, so we chain multiple.
# #     """
# #     ratio = max(0.4, min(ratio, 3.0))
# #     filters = []
# #     r = ratio
# #     while r > 2.0:
# #         filters.append("atempo=2.0")
# #         r /= 2.0
# #     while r < 0.5:
# #         filters.append("atempo=0.5")
# #         r /= 0.5
# #     filters.append(f"atempo={r:.6f}")
# #     _run_ffmpeg("-i", src, "-filter:a", ",".join(filters),
# #                 "-ar", "24000", "-ac", "1", dst)


# # def trim_pad_ffmpeg(src: Path, dst: Path, target_dur: float, sr: int = 24000):
# #     """Trim or silence-pad a WAV to exactly target_dur seconds."""
# #     src_dur = get_audio_duration(src)
# #     if src_dur <= 0:
# #         make_silence(dst, target_dur, sr)
# #         return

# #     if src_dur >= target_dur:
# #         _run_ffmpeg("-i", src, "-t", str(target_dur), "-ar", str(sr), "-ac", "1", dst)
# #     else:
# #         # Pad: concat with silence
# #         pad_dur = target_dur - src_dur
# #         pad_file = dst.parent / f"_pad_{dst.stem}.wav"
# #         make_silence(pad_file, pad_dur, sr)

# #         list_file = dst.parent / f"_cat_{dst.stem}.txt"
# #         list_file.write_text(
# #             f"file '{src.resolve()}'\nfile '{pad_file.resolve()}'\n",
# #             encoding="utf-8"
# #         )
# #         _run_ffmpeg("-f", "concat", "-safe", "0", "-i", list_file,
# #                     "-ar", str(sr), "-ac", "1", dst)
# #         list_file.unlink(missing_ok=True)
# #         pad_file.unlink(missing_ok=True)


# # def assemble_timeline(segments: list, tts_dir: Path,
# #                       workdir: Path, video_duration: float) -> Path:
# #     """
# #     Place each TTS clip at its original timestamp using ffmpeg's
# #     adelay + amix. No pydub required. Works on Python 3.14+.
# #     """
# #     SR = 24000
# #     total = video_duration + 1.5

# #     ready_dir = workdir / "_ready"
# #     ready_dir.mkdir(exist_ok=True)

# #     placed = []  # list of (delay_ms, Path)

# #     for i, seg in enumerate(segments):
# #         raw = tts_dir / f"seg_{i:04d}.wav"
# #         if not raw.exists():
# #             continue

# #         slot = max(seg["end"] - seg["start"], 0.1)
# #         src_dur = get_audio_duration(raw)
# #         if src_dur <= 0:
# #             continue

# #         # Speed-adjust
# #         speed_out = ready_dir / f"{i:04d}_s.wav"
# #         ratio = src_dur / slot
# #         ratio = max(0.4, min(ratio, 3.0))
# #         try:
# #             if abs(ratio - 1.0) > 0.05:
# #                 speed_audio_ffmpeg(raw, speed_out, ratio)
# #             else:
# #                 shutil.copy2(str(raw), str(speed_out))
# #         except Exception as e:
# #             warn(f"Speed-adjust seg {i}: {e}")
# #             shutil.copy2(str(raw), str(speed_out))

# #         # Trim/pad to exact slot
# #         final_out = ready_dir / f"{i:04d}_f.wav"
# #         try:
# #             trim_pad_ffmpeg(speed_out, final_out, slot, SR)
# #         except Exception as e:
# #             warn(f"Trim/pad seg {i}: {e}")
# #             shutil.copy2(str(speed_out), str(final_out))
# #         speed_out.unlink(missing_ok=True)

# #         placed.append((int(seg["start"] * 1000), final_out))

# #     out_path = workdir / "dubbed_audio.wav"

# #     if not placed:
# #         warn("No TTS segments — writing silence.")
# #         make_silence(out_path, total, SR)
# #         return out_path

# #     # Build timeline by batching amix (20 segments at a time)
# #     tmp_dir = workdir / "_timeline"
# #     tmp_dir.mkdir(exist_ok=True)
# #     current = tmp_dir / "base.wav"
# #     make_silence(current, total, SR)

# #     BATCH = 20
# #     for b_start in range(0, len(placed), BATCH):
# #         chunk = placed[b_start: b_start + BATCH]
# #         inputs = ["-i", str(current)]
# #         for _, wav in chunk:
# #             inputs += ["-i", str(wav)]

# #         n = len(chunk)
# #         fc_parts = []
# #         for j, (delay_ms, _) in enumerate(chunk):
# #             fc_parts.append(f"[{j+1}:a]adelay={delay_ms}|{delay_ms}[d{j}]")

# #         mix_in = "[0:a]" + "".join(f"[d{j}]" for j in range(n))
# #         fc_parts.append(f"{mix_in}amix=inputs={n+1}:duration=longest:normalize=0[out]")

# #         batch_out = tmp_dir / f"b{b_start:05d}.wav"
# #         cmd = (["ffmpeg", "-y"]
# #                + inputs
# #                + ["-filter_complex", ";".join(fc_parts),
# #                   "-map", "[out]",
# #                   "-ar", str(SR), "-ac", "1", str(batch_out)])
# #         r = subprocess.run(cmd, capture_output=True, text=True)
# #         if r.returncode != 0:
# #             warn(f"Batch mix {b_start} failed — skipping: {r.stderr[-300:]}")
# #         else:
# #             current = batch_out

# #     shutil.copy2(str(current), str(out_path))
# #     shutil.rmtree(str(tmp_dir), ignore_errors=True)
# #     shutil.rmtree(str(ready_dir), ignore_errors=True)
# #     return out_path


# # # ══════════════════════════════════════════════════════════════════════════════
# # #  Step 1 — Download
# # # ══════════════════════════════════════════════════════════════════════════════

# # def download_video(url: str, workdir: Path):
# #     import yt_dlp
# #     step("Downloading video & audio from YouTube …")

# #     # ── Video (no audio) ──────────────────────────────────────────────────
# #     ydl_v = {
# #         "format": "bestvideo[height<=1080][ext=mp4]/bestvideo[height<=1080]/bestvideo",
# #         "outtmpl": str(workdir / "video_raw.%(ext)s"),
# #         "quiet": True, "no_warnings": True,
# #     }
# #     title = "video"; duration = 0.0
# #     with yt_dlp.YoutubeDL(ydl_v) as ydl:
# #         meta = ydl.extract_info(url, download=True)
# #         title    = meta.get("title", "video")
# #         duration = float(meta.get("duration", 0))

# #     # Normalise to mp4
# #     video_path = workdir / "video_raw.mp4"
# #     for ext in ("mp4", "webm", "mkv", "avi", "mov"):
# #         cand = workdir / f"video_raw.{ext}"
# #         if cand.exists():
# #             if ext != "mp4":
# #                 _run_ffmpeg("-i", cand, "-c:v", "libx264",
# #                             "-crf", "18", "-preset", "fast", video_path)
# #                 cand.unlink(missing_ok=True)
# #             else:
# #                 video_path = cand
# #             break

# #     # ── Audio WAV ─────────────────────────────────────────────────────────
# #     audio_path = workdir / "audio_original.wav"
# #     ydl_a = {
# #         "format": "bestaudio/best",
# #         "outtmpl": str(workdir / "audio_dl.%(ext)s"),
# #         "quiet": True, "no_warnings": True,
# #         "postprocessors": [{
# #             "key": "FFmpegExtractAudio",
# #             "preferredcodec": "wav", "preferredquality": "0",
# #         }],
# #     }
# #     with yt_dlp.YoutubeDL(ydl_a) as ydl:
# #         ydl.download([url])

# #     # Locate the wav
# #     for f in workdir.iterdir():
# #         if "audio_dl" in f.stem and f.suffix == ".wav":
# #             f.rename(audio_path); break

# #     # Fallback: convert whatever yt-dlp left behind
# #     if not audio_path.exists():
# #         for f in workdir.iterdir():
# #             if "audio_dl" in f.stem:
# #                 _run_ffmpeg("-i", f, "-ar", "16000", "-ac", "1", audio_path)
# #                 f.unlink(missing_ok=True); break

# #     info(f"Title    : {title}")
# #     info(f"Duration : {int(duration//60)}m {int(duration%60)}s")
# #     ok(f"Video  →  {video_path.name}")
# #     ok(f"Audio  →  {audio_path.name}")
# #     return video_path, audio_path, title, duration


# # # ══════════════════════════════════════════════════════════════════════════════
# # #  Step 2 — Transcribe
# # # ══════════════════════════════════════════════════════════════════════════════

# # def transcribe_audio(audio_path: Path, workdir: Path, model_size: str = "base"):
# #     import whisper
# #     step(f"Transcribing with Whisper [{model_size}] …")
# #     info("First run downloads the model (~150 MB for base). Please wait.")

# #     model  = whisper.load_model(model_size)
# #     result = model.transcribe(str(audio_path), verbose=False)

# #     segments = [
# #         {"start": s["start"], "end": s["end"], "text": s["text"].strip()}
# #         for s in result["segments"] if s["text"].strip()
# #     ]

# #     _write_srt(segments, workdir / "transcript_original.srt")
# #     detected = result.get("language", "unknown")
# #     ok(f"Transcribed {len(segments)} segments — detected language: {detected}")
# #     return segments, detected


# # def _write_srt(segs, path: Path):
# #     lines = []
# #     for i, s in enumerate(segs, 1):
# #         text = s.get("translated", s["text"])
# #         lines += [str(i), f"{_ts(s['start'])} --> {_ts(s['end'])}", text, ""]
# #     path.write_text("\n".join(lines), encoding="utf-8")

# # def _ts(sec: float) -> str:
# #     h, r = divmod(int(sec), 3600); m, s = divmod(r, 60)
# #     return f"{h:02d}:{m:02d}:{s:02d},{int((sec%1)*1000):03d}"


# # # ══════════════════════════════════════════════════════════════════════════════
# # #  Step 3 — Translate
# # # ══════════════════════════════════════════════════════════════════════════════

# # def translate_segments(segments, target_lang, workdir):
# #     from deep_translator import GoogleTranslator
# #     step(f"Translating {len(segments)} segments → {LANGUAGES.get(target_lang, target_lang)} …")

# #     tr = GoogleTranslator(source="auto", target=target_lang)
# #     errs = 0
# #     for i, seg in enumerate(segments, 1):
# #         try:
# #             seg["translated"] = tr.translate(seg["text"]) or seg["text"]
# #         except Exception as e:
# #             warn(f"Seg {i} error: {e}")
# #             seg["translated"] = seg["text"]
# #             errs += 1
# #         if i % 10 == 0:
# #             time.sleep(0.25)

# #     _write_srt(segments, workdir / f"transcript_{target_lang}.srt")
# #     ok(f"Translation done ({errs} errors).")
# #     return segments


# # # ══════════════════════════════════════════════════════════════════════════════
# # #  Step 4 — TTS + timeline
# # # ══════════════════════════════════════════════════════════════════════════════

# # async def _synth_one(text: str, voice: str, out_mp3: Path):
# #     import edge_tts
# #     await edge_tts.Communicate(text, voice).save(str(out_mp3))


# # def synthesise_speech(segments, target_lang, workdir, video_duration) -> Path:
# #     step(f"Synthesising speech with edge-tts …")
# #     voice   = TTS_VOICES.get(target_lang, TTS_VOICES["en"])
# #     tts_dir = workdir / "tts_segments"
# #     tts_dir.mkdir(exist_ok=True)
# #     info(f"Voice: {voice}")

# #     loop = asyncio.new_event_loop()
# #     asyncio.set_event_loop(loop)
# #     done = 0

# #     for i, seg in enumerate(segments):
# #         text    = seg.get("translated", seg["text"]).strip()
# #         mp3_out = tts_dir / f"seg_{i:04d}.mp3"
# #         wav_out = tts_dir / f"seg_{i:04d}.wav"

# #         if not text:
# #             make_silence(wav_out, max(seg["end"] - seg["start"], 0.1))
# #             continue

# #         try:
# #             loop.run_until_complete(_synth_one(text, voice, mp3_out))
# #             _run_ffmpeg("-i", mp3_out,
# #                         "-ar", "24000", "-ac", "1", "-sample_fmt", "s16",
# #                         wav_out)
# #             mp3_out.unlink(missing_ok=True)
# #             done += 1
# #         except Exception as e:
# #             warn(f"TTS seg {i}: {e}")
# #             make_silence(wav_out, max(seg["end"] - seg["start"], 0.1))

# #     loop.close()
# #     ok(f"Synthesised {done}/{len(segments)} segments.")

# #     step("Building audio timeline with ffmpeg …")
# #     dubbed = assemble_timeline(segments, tts_dir, workdir, video_duration)
# #     ok(f"Dubbed audio ready  →  {dubbed.name}")
# #     return dubbed


# # # ══════════════════════════════════════════════════════════════════════════════
# # #  Step 5 — Merge
# # # ══════════════════════════════════════════════════════════════════════════════

# # def merge_audio_video(video: Path, audio: Path,
# #                       workdir: Path, title: str, lang: str) -> Path:
# #     step("Merging dubbed audio with video …")
# #     safe = "".join(ch for ch in title if ch.isalnum() or ch in " _-")[:55].strip()
# #     out  = workdir / f"{safe}_{lang}_dubbed.mp4"
# #     _run_ffmpeg(
# #         "-i", video, "-i", audio,
# #         "-c:v", "copy",
# #         "-c:a", "aac", "-b:a", "192k",
# #         "-map", "0:v:0", "-map", "1:a:0",
# #         "-shortest", out
# #     )
# #     mb = out.stat().st_size / 1_048_576
# #     ok(f"Merged  →  {out.name}  ({mb:.1f} MB)")
# #     return out


# # # ══════════════════════════════════════════════════════════════════════════════
# # #  Step 6 (optional) — Wav2Lip
# # # ══════════════════════════════════════════════════════════════════════════════

# # def apply_wav2lip(video: Path, audio: Path, workdir: Path) -> Path:
# #     if not WAV2LIP_PATH:
# #         warn("WAV2LIP_PATH not set — skipping neural lip-sync.")
# #         return video
# #     w2l = Path(WAV2LIP_PATH)
# #     if not w2l.exists():
# #         warn(f"Wav2Lip not found at {w2l} — skipping.")
# #         return video

# #     step("Applying Wav2Lip neural lip-sync …")
# #     out = workdir / "lip_synced.mp4"
# #     r = subprocess.run([
# #         sys.executable, str(w2l / "inference.py"),
# #         "--checkpoint_path", str(w2l / "checkpoints" / "wav2lip_gan.pth"),
# #         "--face",    str(video),
# #         "--audio",   str(audio),
# #         "--outfile", str(out),
# #         "--pads",    "0", "10", "0", "0",
# #         "--resize_factor", "1",
# #     ], capture_output=True, text=True, cwd=str(w2l))

# #     if r.returncode != 0:
# #         warn(f"Wav2Lip failed — using merged video.\n{r.stderr[-600:]}")
# #         return video
# #     ok(f"Lip-synced  →  {out.name}")
# #     return out


# # # ══════════════════════════════════════════════════════════════════════════════
# # #  Step 7 — Deliver + cleanup
# # # ══════════════════════════════════════════════════════════════════════════════

# # def deliver_and_cleanup(final: Path, out_dir: Path,
# #                         workdir: Path, keep: bool = False):
# #     step("Saving final video …")
# #     out_dir.mkdir(parents=True, exist_ok=True)
# #     dest = out_dir / final.name
# #     shutil.copy2(str(final), str(dest))
# #     ok(f"Saved  →  {dest}")

# #     if not keep:
# #         step("Cleaning up temp workspace …")
# #         shutil.rmtree(str(workdir), ignore_errors=True)
# #         ok("Workspace cleared.")
# #     else:
# #         info(f"Workspace kept at: {workdir}")

# #     if RICH:
# #         console.print(Panel(
# #             f"[bold green]✔  All done![/bold green]\n\n"
# #             f"[white]Your dubbed video:[/white]\n[bold cyan]{dest}[/bold cyan]",
# #             title="Complete", border_style="green"
# #         ))
# #     else:
# #         print(f"\n{'='*60}\n  ✔  Done!\n  Output: {dest}\n{'='*60}\n")


# # # ══════════════════════════════════════════════════════════════════════════════
# # #  Helpers: language listing + interactive mode + CLI parser
# # # ══════════════════════════════════════════════════════════════════════════════

# # def list_languages():
# #     if RICH:
# #         t = Table(title="Supported Languages", border_style="cyan")
# #         t.add_column("Code", style="bold yellow", width=8)
# #         t.add_column("Language", width=20)
# #         t.add_column("Code", style="bold yellow", width=8)
# #         t.add_column("Language", width=20)
# #         items = sorted(LANGUAGES.items())
# #         half  = (len(items) + 1) // 2
# #         for (c1, n1), (c2, n2) in zip(items[:half], items[half:] + [("","")]):
# #             t.add_row(c1, n1, c2, n2)
# #         console.print(t)
# #     else:
# #         print("\nLanguage codes:")
# #         for code, name in sorted(LANGUAGES.items()):
# #             print(f"  {code:6s}  {name}")
# #     print()


# # def interactive_mode():
# #     banner()
# #     print("  Interactive Setup\n")
# #     url = input("  ➤  YouTube URL: ").strip()
# #     if not url:
# #         err("No URL provided.")
# #     list_languages()
# #     lang = input("  ➤  Target language code (e.g. 'fr', 'ur', 'es'): ").strip().lower()
# #     if lang not in LANGUAGES:
# #         err(f"Unknown code '{lang}'. Run with --list-languages.")
# #     model  = input("  ➤  Whisper model [tiny/base/small/medium/large] (default: base): ").strip() or "base"
# #     output = input("  ➤  Output directory (default: ./output): ").strip() or "./output"
# #     keep   = input("  ➤  Keep temp files? [y/N]: ").strip().lower() == "y"
# #     return argparse.Namespace(
# #         url=url, lang=lang, model=model, output=output,
# #         keep=keep, list_languages=False, wav2lip=bool(WAV2LIP_PATH)
# #     )


# # def build_parser():
# #     p = argparse.ArgumentParser(
# #         prog="yt_translator",
# #         description="YouTube Video Audio Translator — dubs audio into any language.",
# #         formatter_class=argparse.RawDescriptionHelpFormatter
# #     )
# #     p.add_argument("url",  nargs="?", help="YouTube video URL")
# #     p.add_argument("-l", "--lang",   default="es", help="Target language code (default: es)")
# #     p.add_argument("-m", "--model",  default="base",
# #                    choices=["tiny","base","small","medium","large"],
# #                    help="Whisper model size (default: base)")
# #     p.add_argument("-o", "--output", default="./output", help="Output directory (default: ./output)")
# #     p.add_argument("-k", "--keep",   action="store_true", help="Keep temp files")
# #     p.add_argument("--wav2lip",      action="store_true", help="Apply Wav2Lip lip-sync")
# #     p.add_argument("--list-languages", action="store_true", help="Print language codes and exit")
# #     return p


# # # ══════════════════════════════════════════════════════════════════════════════
# # #  Main
# # # ══════════════════════════════════════════════════════════════════════════════

# # def main():
# #     args = build_parser().parse_args()

# #     if args.list_languages:
# #         list_languages(); sys.exit(0)

# #     if not args.url:
# #         args = interactive_mode()

# #     banner()
# #     check_dependencies()

# #     if args.lang not in LANGUAGES:
# #         err(f"Unknown language '{args.lang}'. Run --list-languages.")

# #     ts      = datetime.now().strftime("%Y%m%d_%H%M%S")
# #     workdir = Path(tempfile.gettempdir()) / f"yt_translator_{ts}"
# #     workdir.mkdir(parents=True, exist_ok=True)
# #     info(f"Workspace: {workdir}")

# #     t0 = time.time()
# #     try:
# #         video_path, audio_path, title, duration = download_video(args.url, workdir)
# #         segments, src_lang = transcribe_audio(audio_path, workdir, args.model)
# #         if not segments:
# #             err("No speech detected.")

# #         if src_lang == args.lang:
# #             warn(f"Source already '{args.lang}' — skipping translation.")
# #             for s in segments: s["translated"] = s["text"]
# #         else:
# #             segments = translate_segments(segments, args.lang, workdir)

# #         dubbed_audio = synthesise_speech(segments, args.lang, workdir, duration)
# #         merged       = merge_audio_video(video_path, dubbed_audio, workdir, title, args.lang)
# #         final        = apply_wav2lip(merged, dubbed_audio, workdir) if (args.wav2lip or WAV2LIP_PATH) else merged

# #         deliver_and_cleanup(final, Path(args.output), workdir, keep=args.keep)
# #         info(f"Total time: {int((time.time()-t0)//60)}m {int((time.time()-t0)%60)}s")

# #     except KeyboardInterrupt:
# #         warn("Interrupted. Cleaning up …")
# #         shutil.rmtree(str(workdir), ignore_errors=True)
# #         sys.exit(1)
# #     except SystemExit:
# #         raise
# #     except Exception as exc:
# #         err(f"Unexpected error: {exc}")
# #         raise


# # if __name__ == "__main__":
# #     main()



# #!/usr/bin/env python3
# """
# ╔══════════════════════════════════════════════════════════════╗
# ║          YouTube Video Audio Translator — CLI Tool          ║
# ║  Downloads, Transcribes, Translates, Syncs & Merges Audio  ║
# ╚══════════════════════════════════════════════════════════════╝

# Usage:
#     python app.py                          # interactive
#     python app.py <URL> -l fr              # French dub
#     python app.py <URL> -l ur -m small     # Urdu, better model
#     python app.py --list-languages         # see all codes

# Dependencies (installed via setup.py):
#     yt-dlp, openai-whisper, deep-translator, edge-tts, rich, colorama

# System requirement:
#     ffmpeg + ffprobe  →  https://ffmpeg.org/download.html
#     Windows : winget install ffmpeg   (then reopen terminal)
#     macOS   : brew install ffmpeg
#     Linux   : sudo apt install ffmpeg

# Optional neural lip-sync:
#     Wav2Lip → https://github.com/Rudrabha/Wav2Lip
#     Set WAV2LIP_PATH below once installed.
# """

# import os
# import re
# import sys
# import time
# import json
# import shutil
# import asyncio
# import argparse
# import tempfile
# import subprocess
# from pathlib import Path
# from datetime import datetime
# from typing import Optional

# # ─── Wav2Lip optional path ────────────────────────────────────────────────────
# WAV2LIP_PATH = ""   # e.g. "C:/Wav2Lip" — leave empty to skip

# # ─── Colour helpers ───────────────────────────────────────────────────────────
# try:
#     from colorama import Style, init as colorama_init
#     colorama_init(autoreset=True)
#     def c(text, colour): return f"{colour}{text}{Style.RESET_ALL}"
# except ImportError:
#     def c(text, _colour): return text

# try:
#     from rich.console import Console
#     from rich.panel import Panel
#     from rich.table import Table
#     RICH = True
#     console = Console()
# except ImportError:
#     RICH = False
#     console = None

# # ─── Supported languages ──────────────────────────────────────────────────────
# LANGUAGES = {
#     "af": "Afrikaans",  "sq": "Albanian",   "ar": "Arabic",
#     "bn": "Bengali",    "bs": "Bosnian",    "ca": "Catalan",
#     "zh": "Chinese",    "hr": "Croatian",   "cs": "Czech",
#     "da": "Danish",     "nl": "Dutch",      "en": "English",
#     "eo": "Esperanto",  "et": "Estonian",   "tl": "Filipino",
#     "fi": "Finnish",    "fr": "French",     "de": "German",
#     "el": "Greek",      "gu": "Gujarati",   "hi": "Hindi",
#     "hu": "Hungarian",  "id": "Indonesian", "it": "Italian",
#     "ja": "Japanese",   "kn": "Kannada",    "ko": "Korean",
#     "la": "Latin",      "lv": "Latvian",    "lt": "Lithuanian",
#     "ms": "Malay",      "ml": "Malayalam",  "mr": "Marathi",
#     "my": "Myanmar",    "ne": "Nepali",     "no": "Norwegian",
#     "pa": "Punjabi",    "pl": "Polish",     "pt": "Portuguese",
#     "ro": "Romanian",   "ru": "Russian",    "sr": "Serbian",
#     "si": "Sinhala",    "sk": "Slovak",     "es": "Spanish",
#     "su": "Sundanese",  "sw": "Swahili",    "sv": "Swedish",
#     "ta": "Tamil",      "te": "Telugu",     "th": "Thai",
#     "tr": "Turkish",    "uk": "Ukrainian",  "ur": "Urdu",
#     "vi": "Vietnamese", "cy": "Welsh",
# }

# # ─── Edge-TTS voice map ───────────────────────────────────────────────────────
# TTS_VOICES = {
#     "af": "af-ZA-AdriNeural",     "sq": "sq-AL-AnilaNeural",
#     "ar": "ar-SA-ZariyahNeural",  "bn": "bn-BD-NabanitaNeural",
#     "bs": "bs-BA-VesnaNeural",    "ca": "ca-ES-JoanaNeural",
#     "zh": "zh-CN-XiaoxiaoNeural", "hr": "hr-HR-GabrijelaNeural",
#     "cs": "cs-CZ-VlastaNeural",   "da": "da-DK-ChristelNeural",
#     "nl": "nl-NL-ColetteNeural",  "en": "en-US-JennyNeural",
#     "et": "et-EE-AnuNeural",      "tl": "fil-PH-BlessicaNeural",
#     "fi": "fi-FI-NooraNeural",    "fr": "fr-FR-DeniseNeural",
#     "de": "de-DE-KatjaNeural",    "el": "el-GR-AthinaNeural",
#     "gu": "gu-IN-DhwaniNeural",   "hi": "hi-IN-SwaraNeural",
#     "hu": "hu-HU-NoemiNeural",    "id": "id-ID-GadisNeural",
#     "it": "it-IT-ElsaNeural",     "ja": "ja-JP-NanamiNeural",
#     "kn": "kn-IN-SapnaNeural",    "ko": "ko-KR-SunHiNeural",
#     "lv": "lv-LV-EveritaNeural",  "lt": "lt-LT-OnaNeural",
#     "ms": "ms-MY-YasminNeural",   "ml": "ml-IN-SobhanaNeural",
#     "mr": "mr-IN-AarohiNeural",   "ne": "ne-NP-HemkalaNeural",
#     "no": "nb-NO-PernilleNeural", "pa": "pa-IN-OjasNeural",
#     "pl": "pl-PL-ZofiaNeural",    "pt": "pt-BR-FranciscaNeural",
#     "ro": "ro-RO-AlinaNeural",    "ru": "ru-RU-SvetlanaNeural",
#     "sr": "sr-RS-SophieNeural",   "si": "si-LK-ThiliniNeural",
#     "sk": "sk-SK-ViktoriaNeural", "es": "es-ES-ElviraNeural",
#     "sw": "sw-KE-ZuriNeural",     "sv": "sv-SE-SofieNeural",
#     "ta": "ta-IN-PallaviNeural",  "te": "te-IN-ShrutiNeural",
#     "th": "th-TH-PremwadeeNeural","tr": "tr-TR-EmelNeural",
#     "uk": "uk-UA-PolinaNeural",   "ur": "ur-PK-UzmaNeural",
#     "vi": "vi-VN-HoaiMyNeural",   "cy": "cy-GB-NiaNeural",
# }

# # Max chars per TTS request — stay well under edge-tts limits
# TTS_MAX_CHARS = 480


# # ══════════════════════════════════════════════════════════════════════════════
# #  Logging helpers
# # ══════════════════════════════════════════════════════════════════════════════

# def banner():
#     art = r"""
#   __  ______   ___________  _    ____ ___ ____  ___
#   \ \/ /_  /  |_   _|  _ \| |  / ___|_ _/ ___|/ _ \
#    \  / / /     | | | |_) | | | |  _ | |\___ \ | | |
#    / // /_      | | |  _ <| |__| |_| || | ___) | |_| |
#   /_//____|     |_| |_| \_\_____\____|___|____/ \___/
#     YouTube Video Translator — CLI  (Audio Dub + Lip Sync)
# """
#     if RICH:
#         console.print(Panel(art, style="bold cyan"))
#     else:
#         print(art)


# def step(msg: str):
#     ts = datetime.now().strftime("%H:%M:%S")
#     if RICH:
#         console.print(f"\n[bold cyan][{ts}][/bold cyan] [bold white]{msg}[/bold white]")
#     else:
#         print(f"\n[{ts}] {msg}")


# def ok(msg: str):
#     if RICH: console.print(f"  [bold green]✔[/bold green] {msg}")
#     else:    print(f"  ✔ {msg}")


# def warn(msg: str):
#     if RICH: console.print(f"  [bold yellow]⚠[/bold yellow]  {msg}")
#     else:    print(f"  ⚠  {msg}")


# def err(msg: str):
#     if RICH: console.print(f"\n  [bold red]✘[/bold red] {msg}")
#     else:    print(f"\n  ✘ {msg}")
#     sys.exit(1)


# def info(msg: str):
#     if RICH: console.print(f"     [dim]{msg}[/dim]")
#     else:    print(f"     {msg}")


# # ══════════════════════════════════════════════════════════════════════════════
# #  Dependency check
# # ══════════════════════════════════════════════════════════════════════════════

# def check_dependencies():
#     step("Checking dependencies …")
#     missing = []

#     # ffmpeg AND ffprobe are both required
#     for tool in ("ffmpeg", "ffprobe"):
#         if shutil.which(tool) is None:
#             if sys.platform == "win32":
#                 missing.append(
#                     f"{tool}  →  winget install ffmpeg  (then reopen terminal)"
#                 )
#             elif sys.platform == "darwin":
#                 missing.append(f"{tool}  →  brew install ffmpeg")
#             else:
#                 missing.append(f"{tool}  →  sudo apt install ffmpeg")

#     # Python packages
#     pkgs = {
#         "yt_dlp":          "yt-dlp",
#         "whisper":         "openai-whisper",
#         "deep_translator": "deep-translator",
#         "edge_tts":        "edge-tts",
#         "rich":            "rich",
#         "colorama":        "colorama",
#     }
#     for mod, pip_name in pkgs.items():
#         try:
#             __import__(mod)
#         except ImportError:
#             missing.append(f"pip install {pip_name}")

#     if missing:
#         print()
#         for m in missing:
#             line = f"  • {m}"
#             if RICH: console.print(f"[red]{line}[/red]")
#             else:    print(line)
#         err("Install the above, then re-run.")

#     ok("All dependencies satisfied.")


# # ══════════════════════════════════════════════════════════════════════════════
# #  Pure-ffmpeg audio helpers
# # ══════════════════════════════════════════════════════════════════════════════

# def _run_ffmpeg(*args, timeout: int = 300):
#     """
#     Run: ffmpeg -y -loglevel error <args>
#     Raises RuntimeError on non-zero exit or timeout.
#     """
#     cmd = ["ffmpeg", "-y", "-loglevel", "error"] + [str(a) for a in args]
#     try:
#         r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
#     except subprocess.TimeoutExpired:
#         raise RuntimeError(f"ffmpeg timed out after {timeout}s")
#     if r.returncode != 0:
#         raise RuntimeError(r.stderr[-3000:] or "ffmpeg returned non-zero exit code")


# def get_audio_duration(path: Path) -> float:
#     """Return audio/video duration in seconds via ffprobe, or 0.0 on failure."""
#     try:
#         r = subprocess.run(
#             ["ffprobe", "-v", "quiet", "-print_format", "json",
#              "-show_format", str(path)],
#             capture_output=True, text=True, timeout=30,
#         )
#         return float(json.loads(r.stdout)["format"]["duration"])
#     except Exception:
#         return 0.0


# def make_silence(path: Path, duration: float, sr: int = 24000):
#     """Write a PCM WAV file of pure silence."""
#     duration = max(duration, 0.05)
#     _run_ffmpeg(
#         "-f", "lavfi", "-i", f"anullsrc=r={sr}:cl=mono",
#         "-t", str(duration),
#         "-ar", str(sr), "-ac", "1", "-acodec", "pcm_s16le",
#         path,
#     )


# def speed_audio_ffmpeg(src: Path, dst: Path, ratio: float):
#     """
#     Change playback speed by `ratio` using chained atempo filters.
#     Each atempo step must be in [0.5, 2.0], so we chain multiple steps.

#     Examples:
#         ratio=3.0  → atempo=2.0, atempo=1.5
#         ratio=0.25 → atempo=0.5, atempo=0.5
#     """
#     ratio = max(0.4, min(ratio, 4.0))
#     filters: list = []
#     r = ratio

#     # Decompose values above 2.0 into 2.0× steps
#     while r > 2.0:
#         filters.append("atempo=2.0")
#         r /= 2.0

#     # Decompose values below 0.5 into 0.5× steps
#     # (r *= 2.0 compensates so the final r stays in [0.5, 2.0])
#     while r < 0.5:
#         filters.append("atempo=0.5")
#         r *= 2.0

#     filters.append(f"atempo={r:.6f}")

#     _run_ffmpeg(
#         "-i", src,
#         "-filter:a", ",".join(filters),
#         "-ar", "24000", "-ac", "1", "-acodec", "pcm_s16le",
#         dst,
#     )


# def trim_pad_ffmpeg(src: Path, dst: Path, target_dur: float, sr: int = 24000):
#     """Trim or silence-pad a WAV to exactly `target_dur` seconds."""
#     src_dur = get_audio_duration(src)
#     if src_dur <= 0:
#         make_silence(dst, target_dur, sr)
#         return

#     if src_dur >= target_dur:
#         _run_ffmpeg(
#             "-i", src, "-t", str(target_dur),
#             "-ar", str(sr), "-ac", "1", "-acodec", "pcm_s16le",
#             dst,
#         )
#     else:
#         # Concatenate source + silence padding
#         pad_dur  = target_dur - src_dur
#         pad_file = dst.parent / f"_pad_{dst.stem}.wav"
#         make_silence(pad_file, pad_dur, sr)

#         # IMPORTANT: ffmpeg concat demuxer requires POSIX (forward-slash) paths
#         # even on Windows — using .as_posix() fixes Windows path failures.
#         list_file = dst.parent / f"_cat_{dst.stem}.txt"
#         list_file.write_text(
#             f"file '{src.resolve().as_posix()}'\n"
#             f"file '{pad_file.resolve().as_posix()}'\n",
#             encoding="utf-8",
#         )
#         try:
#             _run_ffmpeg(
#                 "-f", "concat", "-safe", "0", "-i", list_file,
#                 "-ar", str(sr), "-ac", "1", "-acodec", "pcm_s16le",
#                 dst,
#             )
#         finally:
#             list_file.unlink(missing_ok=True)
#             pad_file.unlink(missing_ok=True)


# def assemble_timeline(
#     segments: list, tts_dir: Path, workdir: Path, video_duration: float
# ) -> Path:
#     """
#     Place every TTS clip at its original timestamp using ffmpeg's
#     adelay + amix. Processes in batches of 16 for stability.
#     No pydub required.
#     """
#     SR    = 24000
#     total = video_duration + 2.0   # small safety tail

#     ready_dir = workdir / "_ready"
#     ready_dir.mkdir(exist_ok=True)

#     placed: list = []   # list of (delay_ms: int, wav: Path)

#     for i, seg in enumerate(segments):
#         raw = tts_dir / f"seg_{i:04d}.wav"
#         if not raw.exists():
#             continue

#         slot    = max(seg["end"] - seg["start"], 0.1)
#         src_dur = get_audio_duration(raw)
#         if src_dur <= 0:
#             continue

#         # ── Speed-adjust TTS to fit the subtitle slot ────────────────────
#         speed_out = ready_dir / f"{i:04d}_s.wav"
#         ratio     = max(0.4, min(src_dur / slot, 4.0))
#         try:
#             if abs(ratio - 1.0) > 0.05:
#                 speed_audio_ffmpeg(raw, speed_out, ratio)
#             else:
#                 shutil.copy2(str(raw), str(speed_out))
#         except Exception as e:
#             warn(f"Speed-adjust seg {i}: {e} — using original length")
#             shutil.copy2(str(raw), str(speed_out))

#         # ── Trim / pad to exact slot length ──────────────────────────────
#         final_out = ready_dir / f"{i:04d}_f.wav"
#         try:
#             trim_pad_ffmpeg(speed_out, final_out, slot, SR)
#         except Exception as e:
#             warn(f"Trim/pad seg {i}: {e} — using speed-adjusted file")
#             shutil.copy2(str(speed_out), str(final_out))
#         speed_out.unlink(missing_ok=True)

#         placed.append((int(seg["start"] * 1000), final_out))

#     out_path = workdir / "dubbed_audio.wav"

#     if not placed:
#         warn("No TTS segments placed — output will be silence.")
#         make_silence(out_path, total, SR)
#         return out_path

#     # ── Build final track: start from silence, mix in batches ────────────
#     tmp_dir = workdir / "_timeline"
#     tmp_dir.mkdir(exist_ok=True)
#     current = tmp_dir / "base.wav"
#     make_silence(current, total, SR)

#     BATCH = 16   # smaller batch = more stable on older ffmpeg builds
#     for b_start in range(0, len(placed), BATCH):
#         chunk = placed[b_start: b_start + BATCH]
#         n     = len(chunk)

#         inputs: list = ["-i", str(current)]
#         for _, wav in chunk:
#             inputs += ["-i", str(wav)]

#         fc_parts: list = []
#         for j, (delay_ms, _) in enumerate(chunk):
#             fc_parts.append(
#                 f"[{j+1}:a]adelay={delay_ms}|{delay_ms}[d{j}]"
#             )
#         mix_inputs = "[0:a]" + "".join(f"[d{j}]" for j in range(n))
#         # normalize=0   → don't reduce volume when mixing
#         # dropout_transition=0 → no fade when a stream ends
#         fc_parts.append(
#             f"{mix_inputs}amix=inputs={n+1}:duration=longest"
#             f":normalize=0:dropout_transition=0[out]"
#         )

#         batch_out = tmp_dir / f"b{b_start:05d}.wav"
#         cmd = (
#             ["ffmpeg", "-y", "-loglevel", "error"]
#             + inputs
#             + [
#                 "-filter_complex", ";".join(fc_parts),
#                 "-map", "[out]",
#                 "-ar", str(SR), "-ac", "1", "-acodec", "pcm_s16le",
#                 str(batch_out),
#             ]
#         )
#         try:
#             r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
#             if r.returncode == 0:
#                 current = batch_out
#             else:
#                 warn(f"Batch {b_start} mix failed — skipping: {r.stderr[-400:]}")
#         except subprocess.TimeoutExpired:
#             warn(f"Batch {b_start} mix timed out — skipping.")

#     shutil.copy2(str(current), str(out_path))
#     shutil.rmtree(str(tmp_dir),   ignore_errors=True)
#     shutil.rmtree(str(ready_dir), ignore_errors=True)
#     return out_path


# # ══════════════════════════════════════════════════════════════════════════════
# #  Step 1 — Download
# # ══════════════════════════════════════════════════════════════════════════════

# def download_video(url: str, workdir: Path):
#     import yt_dlp
#     step("Downloading video & audio from YouTube …")

#     # ── Video only (no audio) ─────────────────────────────────────────────
#     ydl_v_opts = {
#         "format":      "bestvideo[height<=1080][ext=mp4]/bestvideo[height<=1080]/bestvideo",
#         "outtmpl":     str(workdir / "video_raw.%(ext)s"),
#         "quiet":       True,
#         "no_warnings": True,
#     }
#     title = "video"
#     duration = 0.0
#     with yt_dlp.YoutubeDL(ydl_v_opts) as ydl:
#         meta     = ydl.extract_info(url, download=True)
#         title    = meta.get("title", "video")
#         duration = float(meta.get("duration") or 0)

#     # Normalise whatever we got to MP4
#     video_path = workdir / "video_raw.mp4"
#     converted  = False
#     for ext in ("mp4", "webm", "mkv", "avi", "mov"):
#         cand = workdir / f"video_raw.{ext}"
#         if cand.exists():
#             if ext != "mp4":
#                 info(f"Converting {ext} → mp4 …")
#                 _run_ffmpeg(
#                     "-i", cand, "-c:v", "libx264",
#                     "-crf", "18", "-preset", "fast", "-an",
#                     video_path, timeout=600,
#                 )
#                 cand.unlink(missing_ok=True)
#             else:
#                 video_path = cand
#             converted = True
#             break

#     if not converted:
#         candidates = list(workdir.glob("video_raw.*"))
#         if not candidates:
#             raise RuntimeError(
#                 "Video download failed — no output file found. "
#                 "Check the URL and your network connection."
#             )
#         cand = candidates[0]
#         info(f"Converting {cand.suffix} → mp4 …")
#         _run_ffmpeg(
#             "-i", cand, "-c:v", "libx264",
#             "-crf", "18", "-preset", "fast", "-an",
#             video_path, timeout=600,
#         )
#         cand.unlink(missing_ok=True)

#     # ── Audio WAV ─────────────────────────────────────────────────────────
#     audio_path  = workdir / "audio_original.wav"
#     ydl_a_opts = {
#         "format":      "bestaudio/best",
#         "outtmpl":     str(workdir / "audio_dl.%(ext)s"),
#         "quiet":       True,
#         "no_warnings": True,
#         "postprocessors": [{
#             "key":              "FFmpegExtractAudio",
#             "preferredcodec":   "wav",
#             "preferredquality": "0",
#         }],
#     }
#     with yt_dlp.YoutubeDL(ydl_a_opts) as ydl:
#         ydl.download([url])

#     # Find the produced WAV (yt-dlp may rename to audio_dl.wav directly)
#     found_audio: Optional[Path] = None
#     for f in workdir.iterdir():
#         if "audio_dl" in f.name and f.suffix.lower() == ".wav":
#             found_audio = f
#             break

#     if found_audio:
#         found_audio.rename(audio_path)
#     else:
#         # Fallback: convert any audio_dl.* file we can find
#         candidates = [f for f in workdir.iterdir() if "audio_dl" in f.name]
#         if candidates:
#             src = candidates[0]
#             info(f"Converting {src.suffix} → wav …")
#             _run_ffmpeg(
#                 "-i", src,
#                 "-ar", "16000", "-ac", "1", "-acodec", "pcm_s16le",
#                 audio_path,
#             )
#             src.unlink(missing_ok=True)
#         else:
#             raise RuntimeError(
#                 "Audio download failed — no audio_dl file found. "
#                 "Check the URL and your network connection."
#             )

#     info(f"Title    : {title}")
#     info(f"Duration : {int(duration // 60)}m {int(duration % 60)}s")
#     ok(f"Video  →  {video_path.name}")
#     ok(f"Audio  →  {audio_path.name}")
#     return video_path, audio_path, title, duration


# # ══════════════════════════════════════════════════════════════════════════════
# #  Step 2 — Transcribe
# # ══════════════════════════════════════════════════════════════════════════════

# def transcribe_audio(audio_path: Path, workdir: Path, model_size: str = "base"):
#     import whisper
#     step(f"Transcribing with Whisper [{model_size}] …")
#     info("First run downloads the model — please wait.")
#     info("Size reference: tiny≈75 MB | base≈150 MB | small≈480 MB | medium≈1.5 GB")

#     model  = whisper.load_model(model_size)
#     result = model.transcribe(
#         str(audio_path),
#         verbose=None,          # show segment progress
#         word_timestamps=False,
#         fp16=False,            # suppress FP16 warnings on CPU-only systems
#     )

#     segments = [
#         {
#             "start": float(s["start"]),
#             "end":   float(s["end"]),
#             "text":  s["text"].strip(),
#         }
#         for s in result.get("segments", [])
#         if s["text"].strip()
#     ]

#     _write_srt(segments, workdir / "transcript_original.srt")
#     detected = result.get("language", "unknown")
#     ok(f"Transcribed {len(segments)} segments — detected language: {detected}")
#     return segments, detected


# def _write_srt(segs: list, path: Path):
#     lines: list = []
#     for i, s in enumerate(segs, 1):
#         text = s.get("translated", s["text"])
#         lines += [str(i), f"{_ts(s['start'])} --> {_ts(s['end'])}", text, ""]
#     path.write_text("\n".join(lines), encoding="utf-8")


# def _ts(sec: float) -> str:
#     # Convert to integer milliseconds first to avoid floating-point drift.
#     total_ms = round(max(0.0, float(sec)) * 1000)
#     ms       = total_ms % 1000
#     total_s  = total_ms // 1000
#     h, r     = divmod(total_s, 3600)
#     m, s     = divmod(r, 60)
#     return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


# # ══════════════════════════════════════════════════════════════════════════════
# #  Step 3 — Translate
# # ══════════════════════════════════════════════════════════════════════════════

# def translate_segments(segments: list, target_lang: str, workdir: Path) -> list:
#     from deep_translator import GoogleTranslator
#     step(
#         f"Translating {len(segments)} segments → "
#         f"{LANGUAGES.get(target_lang, target_lang)} …"
#     )

#     tr   = GoogleTranslator(source="auto", target=target_lang)
#     errs = 0

#     for i, seg in enumerate(segments, 1):
#         text = seg["text"].strip()
#         if not text:
#             seg["translated"] = ""
#             continue

#         # Retry up to 3 times with exponential back-off
#         for attempt in range(3):
#             try:
#                 result = tr.translate(text)
#                 seg["translated"] = result if result else text
#                 break
#             except Exception as e:
#                 if attempt == 2:
#                     warn(f"Seg {i} failed after 3 attempts: {e}")
#                     seg["translated"] = text
#                     errs += 1
#                 else:
#                     time.sleep(1.5 * (attempt + 1))

#         # Gentle rate-limiting — avoid 429 responses from Google
#         if i % 5 == 0:
#             time.sleep(0.4)

#     _write_srt(segments, workdir / f"transcript_{target_lang}.srt")
#     ok(f"Translation done ({errs} error(s)).")
#     return segments


# # ══════════════════════════════════════════════════════════════════════════════
# #  Step 4 — TTS + timeline assembly
# # ══════════════════════════════════════════════════════════════════════════════

# def _sanitize_tts(text: str) -> str:
#     """Remove characters that break edge-tts and normalise whitespace."""
#     text = re.sub(r"<[^>]+>", " ", text)                            # XML/HTML tags
#     text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)  # control chars
#     text = " ".join(text.split())                                    # collapse spaces
#     return text.strip()


# def _chunk_text(text: str, max_chars: int = TTS_MAX_CHARS) -> list:
#     """
#     Split text into chunks of at most `max_chars` characters.
#     Prefers sentence boundaries (. ! ? ।), then word boundaries.
#     """
#     if len(text) <= max_chars:
#         return [text]

#     chunks: list = []
#     current = ""
#     for sentence in re.split(r"(?<=[.!?।])\s+", text):
#         if len(current) + len(sentence) + 1 <= max_chars:
#             current = f"{current} {sentence}".strip() if current else sentence
#         else:
#             if current:
#                 chunks.append(current)
#             if len(sentence) > max_chars:
#                 # Hard word-level split
#                 current = ""
#                 for word in sentence.split():
#                     if len(current) + len(word) + 1 <= max_chars:
#                         current = f"{current} {word}".strip() if current else word
#                     else:
#                         if current:
#                             chunks.append(current)
#                         current = word
#             else:
#                 current = sentence

#     if current:
#         chunks.append(current)
#     return chunks or [text[:max_chars]]


# async def _tts_to_wav(text: str, voice: str, out_wav: Path, tmp_dir: Path):
#     """Synthesize `text` → PCM WAV, splitting long text into chunks first."""
#     import edge_tts
#     chunks = _chunk_text(text)

#     if len(chunks) == 1:
#         mp3 = out_wav.with_suffix(".mp3")
#         await edge_tts.Communicate(chunks[0], voice).save(str(mp3))
#         _run_ffmpeg(
#             "-i", mp3,
#             "-ar", "24000", "-ac", "1", "-acodec", "pcm_s16le",
#             out_wav,
#         )
#         mp3.unlink(missing_ok=True)
#     else:
#         # Synthesize each chunk then concatenate into one WAV
#         chunk_wavs: list = []
#         for ci, chunk in enumerate(chunks):
#             mp3 = tmp_dir / f"_ck_{out_wav.stem}_{ci}.mp3"
#             wav = tmp_dir / f"_ck_{out_wav.stem}_{ci}.wav"
#             await edge_tts.Communicate(chunk, voice).save(str(mp3))
#             _run_ffmpeg(
#                 "-i", mp3,
#                 "-ar", "24000", "-ac", "1", "-acodec", "pcm_s16le",
#                 wav,
#             )
#             mp3.unlink(missing_ok=True)
#             chunk_wavs.append(wav)

#         list_f = tmp_dir / f"_ck_{out_wav.stem}.txt"
#         list_f.write_text(
#             "\n".join(f"file '{w.resolve().as_posix()}'" for w in chunk_wavs),
#             encoding="utf-8",
#         )
#         try:
#             _run_ffmpeg(
#                 "-f", "concat", "-safe", "0", "-i", list_f,
#                 "-ar", "24000", "-ac", "1", "-acodec", "pcm_s16le",
#                 out_wav,
#             )
#         finally:
#             list_f.unlink(missing_ok=True)
#             for w in chunk_wavs:
#                 w.unlink(missing_ok=True)


# async def _synth_all(
#     segments: list, voice: str, tts_dir: Path, tmp_dir: Path
# ) -> int:
#     """Async driver: synthesize every segment with per-segment retry."""
#     done = 0
#     for i, seg in enumerate(segments):
#         text    = _sanitize_tts(seg.get("translated", seg["text"]))
#         wav_out = tts_dir / f"seg_{i:04d}.wav"
#         slot    = max(seg["end"] - seg["start"], 0.1)

#         if not text:
#             make_silence(wav_out, slot)
#             continue

#         success = False
#         for attempt in range(3):
#             try:
#                 await _tts_to_wav(text, voice, wav_out, tmp_dir)
#                 success = True
#                 done += 1
#                 break
#             except Exception as e:
#                 if attempt < 2:
#                     await asyncio.sleep(1.5 * (attempt + 1))
#                 else:
#                     warn(f"TTS seg {i} failed after 3 attempts: {e}")

#         if not success:
#             make_silence(wav_out, slot)

#     return done


# def synthesise_speech(
#     segments: list, target_lang: str, workdir: Path, video_duration: float
# ) -> Path:
#     step("Synthesising speech with edge-tts …")
#     voice   = TTS_VOICES.get(target_lang, TTS_VOICES["en"])
#     tts_dir = workdir / "tts_segments"
#     tts_dir.mkdir(exist_ok=True)
#     info(f"Voice    : {voice}")
#     info(f"Segments : {len(segments)}")

#     # asyncio.run() correctly creates, uses, and closes the event loop —
#     # safe on Python 3.9+ on all platforms (Windows, macOS, Linux).
#     done = asyncio.run(_synth_all(segments, voice, tts_dir, workdir))
#     ok(f"Synthesised {done}/{len(segments)} segments.")

#     step("Building audio timeline with ffmpeg …")
#     dubbed = assemble_timeline(segments, tts_dir, workdir, video_duration)
#     ok(f"Dubbed audio  →  {dubbed.name}")
#     return dubbed


# # ══════════════════════════════════════════════════════════════════════════════
# #  Step 5 — Merge audio + video
# # ══════════════════════════════════════════════════════════════════════════════

# def merge_audio_video(
#     video: Path, audio: Path, workdir: Path, title: str, lang: str
# ) -> Path:
#     step("Merging dubbed audio with video …")
#     # Safe filename: keep letters, digits, spaces, hyphens, underscores
#     safe = re.sub(r"[^\w\s\-]", "", title, flags=re.UNICODE)[:55].strip()
#     safe = re.sub(r"\s+", "_", safe) or "output"
#     out  = workdir / f"{safe}_{lang}_dubbed.mp4"
#     _run_ffmpeg(
#         "-i", video, "-i", audio,
#         "-c:v", "copy",
#         "-c:a", "aac", "-b:a", "192k",
#         "-map", "0:v:0", "-map", "1:a:0",
#         "-shortest",
#         out,
#         timeout=600,
#     )
#     mb = out.stat().st_size / 1_048_576
#     ok(f"Merged  →  {out.name}  ({mb:.1f} MB)")
#     return out


# # ══════════════════════════════════════════════════════════════════════════════
# #  Step 6 (optional) — Wav2Lip neural lip-sync
# # ══════════════════════════════════════════════════════════════════════════════

# def apply_wav2lip(video: Path, audio: Path, workdir: Path) -> Path:
#     if not WAV2LIP_PATH:
#         warn("WAV2LIP_PATH not set — skipping neural lip-sync.")
#         return video
#     w2l = Path(WAV2LIP_PATH)
#     if not w2l.exists():
#         warn(f"Wav2Lip not found at {w2l} — skipping.")
#         return video

#     step("Applying Wav2Lip neural lip-sync …")
#     out = workdir / "lip_synced.mp4"
#     r   = subprocess.run(
#         [
#             sys.executable, str(w2l / "inference.py"),
#             "--checkpoint_path", str(w2l / "checkpoints" / "wav2lip_gan.pth"),
#             "--face",    str(video),
#             "--audio",   str(audio),
#             "--outfile", str(out),
#             "--pads",    "0", "10", "0", "0",
#             "--resize_factor", "1",
#         ],
#         capture_output=True, text=True,
#         cwd=str(w2l), timeout=1800,
#     )
#     if r.returncode != 0:
#         warn(f"Wav2Lip failed — using merged video.\n{r.stderr[-600:]}")
#         return video
#     ok(f"Lip-synced  →  {out.name}")
#     return out


# # ══════════════════════════════════════════════════════════════════════════════
# #  Step 7 — Deliver & clean up
# # ══════════════════════════════════════════════════════════════════════════════

# def deliver_and_cleanup(
#     final: Path, out_dir: Path, workdir: Path, keep: bool = False
# ):
#     step("Saving final video …")
#     out_dir.mkdir(parents=True, exist_ok=True)
#     dest = out_dir / final.name
#     shutil.copy2(str(final), str(dest))
#     ok(f"Saved  →  {dest}")

#     if not keep:
#         step("Cleaning up temp workspace …")
#         shutil.rmtree(str(workdir), ignore_errors=True)
#         ok("Workspace cleared.")
#     else:
#         info(f"Workspace kept at: {workdir}")

#     if RICH:
#         console.print(Panel(
#             f"[bold green]✔  All done![/bold green]\n\n"
#             f"[white]Your dubbed video:[/white]\n[bold cyan]{dest}[/bold cyan]",
#             title="Complete", border_style="green",
#         ))
#     else:
#         print(f"\n{'=' * 60}\n  ✔  Done!\n  Output: {dest}\n{'=' * 60}\n")


# # ══════════════════════════════════════════════════════════════════════════════
# #  Utilities: language list, interactive mode, CLI parser
# # ══════════════════════════════════════════════════════════════════════════════

# def list_languages():
#     if RICH:
#         t = Table(title="Supported Languages", border_style="cyan")
#         t.add_column("Code",     style="bold yellow", width=8)
#         t.add_column("Language", width=20)
#         t.add_column("Code",     style="bold yellow", width=8)
#         t.add_column("Language", width=20)
#         items = sorted(LANGUAGES.items())
#         half  = (len(items) + 1) // 2
#         for (c1, n1), (c2, n2) in zip(items[:half], items[half:] + [("", "")]):
#             t.add_row(c1, n1, c2, n2)
#         console.print(t)
#     else:
#         print("\nLanguage codes:")
#         for code, name in sorted(LANGUAGES.items()):
#             print(f"  {code:6s}  {name}")
#     print()


# def interactive_mode() -> argparse.Namespace:
#     banner()
#     print("  Interactive Setup\n")
#     url = input("  ➤  YouTube URL: ").strip()
#     if not url:
#         err("No URL provided.")

#     list_languages()
#     lang = input(
#         "  ➤  Target language code (e.g. 'fr', 'ur', 'es'): "
#     ).strip().lower()
#     if lang not in LANGUAGES:
#         err(f"Unknown code '{lang}'. Run with --list-languages to see all codes.")

#     model  = (
#         input("  ➤  Whisper model [tiny/base/small/medium/large] (default: base): ")
#         .strip() or "base"
#     )
#     output = input("  ➤  Output directory (default: ./output): ").strip() or "./output"
#     keep   = input("  ➤  Keep temp files? [y/N]: ").strip().lower() == "y"

#     return argparse.Namespace(
#         url=url, lang=lang, model=model, output=output,
#         keep=keep, list_languages=False, wav2lip=bool(WAV2LIP_PATH),
#     )


# def build_parser() -> argparse.ArgumentParser:
#     p = argparse.ArgumentParser(
#         prog="app",
#         description="YouTube Video Audio Translator — dubs audio into any language.",
#         formatter_class=argparse.RawDescriptionHelpFormatter,
#         epilog=(
#             "Examples:\n"
#             "  python app.py                           # interactive\n"
#             "  python app.py <URL> -l fr               # French dub\n"
#             "  python app.py <URL> -l ur -m small      # Urdu, better model\n"
#             "  python app.py --list-languages           # see all codes\n"
#         ),
#     )
#     p.add_argument("url",  nargs="?", help="YouTube video URL")
#     p.add_argument("-l", "--lang",   default="es",
#                    help="Target language code (default: es)")
#     p.add_argument("-m", "--model",  default="base",
#                    choices=["tiny", "base", "small", "medium", "large"],
#                    help="Whisper model size (default: base)")
#     p.add_argument("-o", "--output", default="./output",
#                    help="Output directory (default: ./output)")
#     p.add_argument("-k", "--keep",   action="store_true",
#                    help="Keep temp workspace after completion")
#     p.add_argument("--wav2lip",      action="store_true",
#                    help="Apply Wav2Lip neural lip-sync (requires Wav2Lip setup)")
#     p.add_argument("--list-languages", action="store_true",
#                    help="Print all supported language codes and exit")
#     return p


# # ══════════════════════════════════════════════════════════════════════════════
# #  Main entry point
# # ══════════════════════════════════════════════════════════════════════════════

# def main():
#     args = build_parser().parse_args()

#     if args.list_languages:
#         list_languages()
#         sys.exit(0)

#     if not args.url:
#         args = interactive_mode()

#     banner()
#     check_dependencies()

#     if args.lang not in LANGUAGES:
#         err(f"Unknown language code '{args.lang}'. Run --list-languages.")

#     ts      = datetime.now().strftime("%Y%m%d_%H%M%S")
#     workdir = Path(tempfile.gettempdir()) / f"yt_translator_{ts}"
#     workdir.mkdir(parents=True, exist_ok=True)
#     info(f"Workspace: {workdir}")

#     t0 = time.time()
#     try:
#         video_path, audio_path, title, duration = download_video(args.url, workdir)

#         # Fallback if yt-dlp didn't report a duration
#         if duration <= 0:
#             warn("Duration unknown from metadata — measuring audio length …")
#             duration = get_audio_duration(audio_path)

#         segments, src_lang = transcribe_audio(audio_path, workdir, args.model)
#         if not segments:
#             err(
#                 "No speech detected in audio. "
#                 "Try a larger Whisper model (e.g. -m small) or check the video."
#             )

#         if src_lang == args.lang:
#             warn(
#                 f"Detected language is already '{args.lang}' — "
#                 "skipping translation (TTS will still run)."
#             )
#             for s in segments:
#                 s["translated"] = s["text"]
#         else:
#             segments = translate_segments(segments, args.lang, workdir)

#         dubbed_audio = synthesise_speech(segments, args.lang, workdir, duration)
#         merged       = merge_audio_video(video_path, dubbed_audio, workdir, title, args.lang)
#         final        = (
#             apply_wav2lip(merged, dubbed_audio, workdir)
#             if (args.wav2lip or WAV2LIP_PATH)
#             else merged
#         )

#         deliver_and_cleanup(final, Path(args.output), workdir, keep=args.keep)

#         elapsed = time.time() - t0
#         info(f"Total time: {int(elapsed // 60)}m {int(elapsed % 60)}s")

#     except KeyboardInterrupt:
#         warn("\nInterrupted by user. Cleaning up …")
#         shutil.rmtree(str(workdir), ignore_errors=True)
#         sys.exit(130)
#     except SystemExit:
#         raise
#     except Exception as exc:
#         err(f"Unexpected error: {exc}")


# if __name__ == "__main__":
#     main()

# #!/usr/bin/env python3
# """
# ╔══════════════════════════════════════════════════════════════╗
# ║          YouTube Video Audio Translator — CLI Tool          ║
# ║  Downloads, Transcribes, Translates, Syncs & Merges Audio  ║
# ╚══════════════════════════════════════════════════════════════╝

# Dependencies:
#     pip install yt-dlp openai-whisper deep-translator edge-tts rich colorama

# System requirement:
#     ffmpeg  →  winget install ffmpeg   OR   https://ffmpeg.org/download.html
#     (pydub is NOT required — audio is assembled purely via ffmpeg)

# Optional neural lip-sync:
#     Wav2Lip →  https://github.com/Rudrabha/Wav2Lip
#                Set WAV2LIP_PATH below once installed.
# """

# import os
# import sys
# import time
# import json
# import shutil
# import asyncio
# import argparse
# import tempfile
# import textwrap
# import subprocess
# from pathlib import Path
# from datetime import datetime

# # ─── Wav2Lip optional path ────────────────────────────────────────────────────
# WAV2LIP_PATH = ""   # e.g. "C:/Wav2Lip" — leave empty to skip

# # ─── Colour helpers ───────────────────────────────────────────────────────────
# try:
#     from colorama import Style, init as colorama_init
#     colorama_init(autoreset=True)
#     def c(text, colour): return f"{colour}{text}{Style.RESET_ALL}"
# except ImportError:
#     def c(text, _colour): return text

# try:
#     from rich.console import Console
#     from rich.panel import Panel
#     from rich.table import Table
#     RICH = True
#     console = Console()
# except ImportError:
#     RICH = False
#     console = None

# # ─── Supported languages ──────────────────────────────────────────────────────
# LANGUAGES = {
#     "af":"Afrikaans",  "sq":"Albanian",   "ar":"Arabic",
#     "bn":"Bengali",    "bs":"Bosnian",    "ca":"Catalan",
#     "zh":"Chinese",    "hr":"Croatian",   "cs":"Czech",
#     "da":"Danish",     "nl":"Dutch",      "en":"English",
#     "eo":"Esperanto",  "et":"Estonian",   "tl":"Filipino",
#     "fi":"Finnish",    "fr":"French",     "de":"German",
#     "el":"Greek",      "gu":"Gujarati",   "hi":"Hindi",
#     "hu":"Hungarian",  "id":"Indonesian", "it":"Italian",
#     "ja":"Japanese",   "kn":"Kannada",    "ko":"Korean",
#     "la":"Latin",      "lv":"Latvian",    "lt":"Lithuanian",
#     "ms":"Malay",      "ml":"Malayalam",  "mr":"Marathi",
#     "my":"Myanmar",    "ne":"Nepali",     "no":"Norwegian",
#     "pa":"Punjabi",    "pl":"Polish",     "pt":"Portuguese",
#     "ro":"Romanian",   "ru":"Russian",    "sr":"Serbian",
#     "si":"Sinhala",    "sk":"Slovak",     "es":"Spanish",
#     "su":"Sundanese",  "sw":"Swahili",    "sv":"Swedish",
#     "ta":"Tamil",      "te":"Telugu",     "th":"Thai",
#     "tr":"Turkish",    "uk":"Ukrainian",  "ur":"Urdu",
#     "vi":"Vietnamese", "cy":"Welsh",
# }

# # ─── Edge-TTS voice map ───────────────────────────────────────────────────────
# # Voices separated by gender (male/female)
# TTS_VOICES = {
#     "af": {"female": "af-ZA-AdriNeural",      "male": "af-ZA-WillemNeural"},
#     "sq": {"female": "sq-AL-AnilaNeural",     "male": "sq-AL-IlirNeural"},
#     "ar": {"female": "ar-SA-ZariyahNeural",   "male": "ar-SA-HamedNeural"},
#     "bn": {"female": "bn-BD-NabanitaNeural",  "male": "bn-BD-PradeepNeural"},
#     "bs": {"female": "bs-BA-VesnaNeural",     "male": "bs-BA-GoranNeural"},
#     "ca": {"female": "ca-ES-JoanaNeural",     "male": "ca-ES-EnricNeural"},
#     "zh": {"female": "zh-CN-XiaoxiaoNeural",  "male": "zh-CN-YunxiNeural"},
#     "hr": {"female": "hr-HR-GabrijelaNeural", "male": "hr-HR-SreckoNeural"},
#     "cs": {"female": "cs-CZ-VlastaNeural",    "male": "cs-CZ-AntoninNeural"},
#     "da": {"female": "da-DK-ChristelNeural",  "male": "da-DK-JeppeNeural"},
#     "nl": {"female": "nl-NL-ColetteNeural",   "male": "nl-NL-MaartenNeural"},
#     "en": {"female": "en-US-JennyNeural",     "male": "en-US-GuyNeural"},
#     "et": {"female": "et-EE-AnuNeural",       "male": "et-EE-KertNeural"},
#     "tl": {"female": "fil-PH-BlessicaNeural", "male": "fil-PH-AngeloNeural"},
#     "fi": {"female": "fi-FI-NooraNeural",     "male": "fi-FI-HarriNeural"},
#     "fr": {"female": "fr-FR-DeniseNeural",    "male": "fr-FR-HenriNeural"},
#     "de": {"female": "de-DE-KatjaNeural",     "male": "de-DE-ConradNeural"},
#     "el": {"female": "el-GR-AthinaNeural",    "male": "el-GR-NestorasNeural"},
#     "gu": {"female": "gu-IN-DhwaniNeural",    "male": "gu-IN-NiranjanNeural"},
#     "hi": {"female": "hi-IN-SwaraNeural",     "male": "hi-IN-MadhurNeural"},
#     "hu": {"female": "hu-HU-NoemiNeural",     "male": "hu-HU-TamasNeural"},
#     "id": {"female": "id-ID-GadisNeural",     "male": "id-ID-ArdiNeural"},
#     "it": {"female": "it-IT-ElsaNeural",      "male": "it-IT-DiegoNeural"},
#     "ja": {"female": "ja-JP-NanamiNeural",    "male": "ja-JP-KeitaNeural"},
#     "kn": {"female": "kn-IN-SapnaNeural",     "male": "kn-IN-GaganNeural"},
#     "ko": {"female": "ko-KR-SunHiNeural",     "male": "ko-KR-InJoonNeural"},
#     "lv": {"female": "lv-LV-EveritaNeural",   "male": "lv-LV-NilsNeural"},
#     "lt": {"female": "lt-LT-OnaNeural",       "male": "lt-LT-LeonasNeural"},
#     "ms": {"female": "ms-MY-YasminNeural",    "male": "ms-MY-OsmanNeural"},
#     "ml": {"female": "ml-IN-SobhanaNeural",   "male": "ml-IN-MidhunNeural"},
#     "mr": {"female": "mr-IN-AarohiNeural",    "male": "mr-IN-ManoharNeural"},
#     "ne": {"female": "ne-NP-HemkalaNeural",   "male": "ne-NP-SagarNeural"},
#     "no": {"female": "nb-NO-PernilleNeural",  "male": "nb-NO-FinnNeural"},
#     "pa": {"female": "pa-IN-OjasNeural",      "male": "pa-IN-GaganNeural"},
#     "pl": {"female": "pl-PL-ZofiaNeural",     "male": "pl-PL-MarekNeural"},
#     "pt": {"female": "pt-BR-FranciscaNeural", "male": "pt-BR-AntonioNeural"},
#     "ro": {"female": "ro-RO-AlinaNeural",     "male": "ro-RO-EmilNeural"},
#     "ru": {"female": "ru-RU-SvetlanaNeural",  "male": "ru-RU-DmitryNeural"},
#     "sr": {"female": "sr-RS-SophieNeural",    "male": "sr-RS-NicholasNeural"},
#     "si": {"female": "si-LK-ThiliniNeural",   "male": "si-LK-SameeraNeural"},
#     "sk": {"female": "sk-SK-ViktoriaNeural",  "male": "sk-SK-LukasNeural"},
#     "es": {"female": "es-ES-ElviraNeural",    "male": "es-ES-AlvaroNeural"},
#     "sw": {"female": "sw-KE-ZuriNeural",      "male": "sw-KE-RafikiNeural"},
#     "sv": {"female": "sv-SE-SofieNeural",     "male": "sv-SE-MattiasNeural"},
#     "ta": {"female": "ta-IN-PallaviNeural",   "male": "ta-IN-ValluvarNeural"},
#     "te": {"female": "te-IN-ShrutiNeural",    "male": "te-IN-MohanNeural"},
#     "th": {"female": "th-TH-PremwadeeNeural", "male": "th-TH-NiwatNeural"},
#     "tr": {"female": "tr-TR-EmelNeural",      "male": "tr-TR-AhmetNeural"},
#     "uk": {"female": "uk-UA-PolinaNeural",    "male": "uk-UA-OstapNeural"},
#     "ur": {"female": "ur-PK-UzmaNeural",      "male": "ur-PK-AsadNeural"},
#     "vi": {"female": "vi-VN-HoaiMyNeural",    "male": "vi-VN-NamMinhNeural"},
#     "cy": {"female": "cy-GB-NiaNeural",       "male": "cy-GB-AledNeural"},
# }


# # ══════════════════════════════════════════════════════════════════════════════
# #  Logging helpers
# # ══════════════════════════════════════════════════════════════════════════════

# def banner():
#     art = r"""
#   __  ______   ___________  _    ____ ___ ____  ___
#   \ \/ /_  /  |_   _|  _ \| |  / ___|_ _/ ___|/ _ \
#    \  / / /     | | | |_) | | | |  _ | |\___ \ | | |
#    / // /_      | | |  _ <| |__| |_| || | ___) | |_| |
#   /_//____|     |_| |_| \_\_____\____|___|____/ \___/
#     YouTube Video Translator — CLI  (Audio Dub + Lip Sync)
# """
#     if RICH:
#         console.print(Panel(art, style="bold cyan"))
#     else:
#         print(art)

# def step(msg):
#     ts = datetime.now().strftime("%H:%M:%S")
#     if RICH:
#         console.print(f"\n[bold cyan][{ts}][/bold cyan] [bold white]{msg}[/bold white]")
#     else:
#         print(f"\n[{ts}] {msg}")

# def ok(msg):
#     if RICH: console.print(f"  [bold green]✔[/bold green] {msg}")
#     else:    print(f"  ✔ {msg}")

# def warn(msg):
#     if RICH: console.print(f"  [bold yellow]⚠[/bold yellow]  {msg}")
#     else:    print(f"  ⚠  {msg}")

# def err(msg):
#     if RICH: console.print(f"\n  [bold red]✘[/bold red] {msg}")
#     else:    print(f"\n  ✘ {msg}")
#     sys.exit(1)

# def info(msg):
#     if RICH: console.print(f"     [dim]{msg}[/dim]")
#     else:    print(f"     {msg}")


# # ══════════════════════════════════════════════════════════════════════════════
# #  Dependency check  (NO pydub)
# # ══════════════════════════════════════════════════════════════════════════════

# def check_dependencies():
#     step("Checking dependencies …")
#     missing = []

#     if shutil.which("ffmpeg") is None:
#         missing.append("ffmpeg  →  run:  winget install ffmpeg   (then reopen terminal)")

#     pkgs = {
#         "yt_dlp":          "yt-dlp",
#         "whisper":         "openai-whisper",
#         "deep_translator": "deep-translator",
#         "edge_tts":        "edge-tts",
#         "rich":            "rich",
#         "colorama":        "colorama",
#     }
#     for mod, pip_name in pkgs.items():
#         try:
#             __import__(mod)
#         except ImportError:
#             missing.append(f"pip install {pip_name}")

#     if missing:
#         print()
#         for m in missing:
#             err_line = f"  • {m}"
#             if RICH: console.print(f"[red]{err_line}[/red]")
#             else:    print(err_line)
#         err("Fix the above, then re-run the script.")

#     ok("All dependencies OK — no pydub needed.")


# # ══════════════════════════════════════════════════════════════════════════════
# #  Pure-ffmpeg audio helpers
# # ══════════════════════════════════════════════════════════════════════════════

# def _run_ffmpeg(*args):
#     """Run ffmpeg -y <args>. Raises RuntimeError on failure."""
#     cmd = ["ffmpeg", "-y"] + list(str(a) for a in args)
#     r = subprocess.run(cmd, capture_output=True, text=True)
#     if r.returncode != 0:
#         raise RuntimeError(r.stderr[-2000:])


# def get_audio_duration(path: Path) -> float:
#     r = subprocess.run(
#         ["ffprobe", "-v", "quiet", "-print_format", "json",
#          "-show_format", str(path)],
#         capture_output=True, text=True
#     )
#     try:
#         return float(json.loads(r.stdout)["format"]["duration"])
#     except Exception:
#         return 0.0


# def make_silence(path: Path, duration: float, sr: int = 24000):
#     duration = max(duration, 0.05)
#     _run_ffmpeg(
#         "-f", "lavfi", "-i", f"anullsrc=r={sr}:cl=mono",
#         "-t", str(duration), "-ar", str(sr), "-ac", "1", path
#     )


# def speed_audio_ffmpeg(src: Path, dst: Path, ratio: float):
#     """
#     Change audio speed by `ratio` using atempo filter chains.
#     atempo is clamped to [0.5, 2.0] per step, so we chain multiple.
#     """
#     ratio = max(0.4, min(ratio, 3.0))
#     filters = []
#     r = ratio
#     while r > 2.0:
#         filters.append("atempo=2.0")
#         r /= 2.0
#     while r < 0.5:
#         filters.append("atempo=0.5")
#         r /= 0.5
#     filters.append(f"atempo={r:.6f}")
#     _run_ffmpeg("-i", src, "-filter:a", ",".join(filters),
#                 "-ar", "24000", "-ac", "1", dst)


# def trim_pad_ffmpeg(src: Path, dst: Path, target_dur: float, sr: int = 24000):
#     """Trim or silence-pad a WAV to exactly target_dur seconds."""
#     src_dur = get_audio_duration(src)
#     if src_dur <= 0:
#         make_silence(dst, target_dur, sr)
#         return

#     if src_dur >= target_dur:
#         _run_ffmpeg("-i", src, "-t", str(target_dur), "-ar", str(sr), "-ac", "1", dst)
#     else:
#         # Pad: concat with silence
#         pad_dur = target_dur - src_dur
#         pad_file = dst.parent / f"_pad_{dst.stem}.wav"
#         make_silence(pad_file, pad_dur, sr)

#         list_file = dst.parent / f"_cat_{dst.stem}.txt"
#         list_file.write_text(
#             f"file '{src.resolve()}'\nfile '{pad_file.resolve()}'\n",
#             encoding="utf-8"
#         )
#         _run_ffmpeg("-f", "concat", "-safe", "0", "-i", list_file,
#                     "-ar", str(sr), "-ac", "1", dst)
#         list_file.unlink(missing_ok=True)
#         pad_file.unlink(missing_ok=True)


# def assemble_timeline(segments: list, tts_dir: Path,
#                       workdir: Path, video_duration: float) -> Path:
#     """
#     Place each TTS clip at its original timestamp using ffmpeg's
#     adelay + amix. No pydub required. Works on Python 3.14+.
#     """
#     SR = 24000
#     total = video_duration + 1.5

#     ready_dir = workdir / "_ready"
#     ready_dir.mkdir(exist_ok=True)

#     placed = []  # list of (delay_ms, Path)

#     for i, seg in enumerate(segments):
#         raw = tts_dir / f"seg_{i:04d}.wav"
#         if not raw.exists():
#             continue

#         slot = max(seg["end"] - seg["start"], 0.1)
#         src_dur = get_audio_duration(raw)
#         if src_dur <= 0:
#             continue

#         # Speed-adjust
#         speed_out = ready_dir / f"{i:04d}_s.wav"
#         ratio = src_dur / slot
#         ratio = max(0.4, min(ratio, 3.0))
#         try:
#             if abs(ratio - 1.0) > 0.05:
#                 speed_audio_ffmpeg(raw, speed_out, ratio)
#             else:
#                 shutil.copy2(str(raw), str(speed_out))
#         except Exception as e:
#             warn(f"Speed-adjust seg {i}: {e}")
#             shutil.copy2(str(raw), str(speed_out))

#         # Trim/pad to exact slot
#         final_out = ready_dir / f"{i:04d}_f.wav"
#         try:
#             trim_pad_ffmpeg(speed_out, final_out, slot, SR)
#         except Exception as e:
#             warn(f"Trim/pad seg {i}: {e}")
#             shutil.copy2(str(speed_out), str(final_out))
#         speed_out.unlink(missing_ok=True)

#         placed.append((int(seg["start"] * 1000), final_out))

#     out_path = workdir / "dubbed_audio.wav"

#     if not placed:
#         warn("No TTS segments — writing silence.")
#         make_silence(out_path, total, SR)
#         return out_path

#     # Build timeline by batching amix (20 segments at a time)
#     tmp_dir = workdir / "_timeline"
#     tmp_dir.mkdir(exist_ok=True)
#     current = tmp_dir / "base.wav"
#     make_silence(current, total, SR)

#     BATCH = 20
#     for b_start in range(0, len(placed), BATCH):
#         chunk = placed[b_start: b_start + BATCH]
#         inputs = ["-i", str(current)]
#         for _, wav in chunk:
#             inputs += ["-i", str(wav)]

#         n = len(chunk)
#         fc_parts = []
#         for j, (delay_ms, _) in enumerate(chunk):
#             fc_parts.append(f"[{j+1}:a]adelay={delay_ms}|{delay_ms}[d{j}]")

#         mix_in = "[0:a]" + "".join(f"[d{j}]" for j in range(n))
#         fc_parts.append(f"{mix_in}amix=inputs={n+1}:duration=longest:normalize=0[out]")

#         batch_out = tmp_dir / f"b{b_start:05d}.wav"
#         cmd = (["ffmpeg", "-y"]
#                + inputs
#                + ["-filter_complex", ";".join(fc_parts),
#                   "-map", "[out]",
#                   "-ar", str(SR), "-ac", "1", str(batch_out)])
#         r = subprocess.run(cmd, capture_output=True, text=True)
#         if r.returncode != 0:
#             warn(f"Batch mix {b_start} failed — skipping: {r.stderr[-300:]}")
#         else:
#             current = batch_out

#     shutil.copy2(str(current), str(out_path))
#     shutil.rmtree(str(tmp_dir), ignore_errors=True)
#     shutil.rmtree(str(ready_dir), ignore_errors=True)
#     return out_path


# # ══════════════════════════════════════════════════════════════════════════════
# #  Step 1 — Download
# # ══════════════════════════════════════════════════════════════════════════════

# def download_video(url: str, workdir: Path):
#     import yt_dlp
#     step("Downloading video & audio from YouTube …")

#     # ── Video (no audio) ──────────────────────────────────────────────────
#     ydl_v = {
#         "format": "bestvideo[height<=1080][ext=mp4]/bestvideo[height<=1080]/bestvideo",
#         "outtmpl": str(workdir / "video_raw.%(ext)s"),
#         "quiet": True, "no_warnings": True,
#     }
#     title = "video"; duration = 0.0
#     with yt_dlp.YoutubeDL(ydl_v) as ydl:
#         meta = ydl.extract_info(url, download=True)
#         title    = meta.get("title", "video")
#         duration = float(meta.get("duration", 0))

#     # Normalise to mp4
#     video_path = workdir / "video_raw.mp4"
#     for ext in ("mp4", "webm", "mkv", "avi", "mov"):
#         cand = workdir / f"video_raw.{ext}"
#         if cand.exists():
#             if ext != "mp4":
#                 _run_ffmpeg("-i", cand, "-c:v", "libx264",
#                             "-crf", "18", "-preset", "fast", video_path)
#                 cand.unlink(missing_ok=True)
#             else:
#                 video_path = cand
#             break

#     # ── Audio WAV ─────────────────────────────────────────────────────────
#     audio_path = workdir / "audio_original.wav"
#     ydl_a = {
#         "format": "bestaudio/best",
#         "outtmpl": str(workdir / "audio_dl.%(ext)s"),
#         "quiet": True, "no_warnings": True,
#         "postprocessors": [{
#             "key": "FFmpegExtractAudio",
#             "preferredcodec": "wav", "preferredquality": "0",
#         }],
#     }
#     with yt_dlp.YoutubeDL(ydl_a) as ydl:
#         ydl.download([url])

#     # Locate the wav
#     for f in workdir.iterdir():
#         if "audio_dl" in f.stem and f.suffix == ".wav":
#             f.rename(audio_path); break

#     # Fallback: convert whatever yt-dlp left behind
#     if not audio_path.exists():
#         for f in workdir.iterdir():
#             if "audio_dl" in f.stem:
#                 _run_ffmpeg("-i", f, "-ar", "16000", "-ac", "1", audio_path)
#                 f.unlink(missing_ok=True); break

#     info(f"Title    : {title}")
#     info(f"Duration : {int(duration//60)}m {int(duration%60)}s")
#     ok(f"Video  →  {video_path.name}")
#     ok(f"Audio  →  {audio_path.name}")
#     return video_path, audio_path, title, duration


# # ══════════════════════════════════════════════════════════════════════════════
# #  Step 2 — Transcribe
# # ══════════════════════════════════════════════════════════════════════════════

# def transcribe_audio(audio_path: Path, workdir: Path, model_size: str = "base"):
#     import whisper
#     step(f"Transcribing with Whisper [{model_size}] …")
#     info("First run downloads the model (~150 MB for base). Please wait.")

#     model  = whisper.load_model(model_size)
#     result = model.transcribe(str(audio_path), verbose=False)

#     segments = [
#         {"start": s["start"], "end": s["end"], "text": s["text"].strip()}
#         for s in result["segments"] if s["text"].strip()
#     ]

#     _write_srt(segments, workdir / "transcript_original.srt")
#     detected = result.get("language", "unknown")
#     ok(f"Transcribed {len(segments)} segments — detected language: {detected}")
#     return segments, detected


# def _write_srt(segs, path: Path):
#     lines = []
#     for i, s in enumerate(segs, 1):
#         text = s.get("translated", s["text"])
#         lines += [str(i), f"{_ts(s['start'])} --> {_ts(s['end'])}", text, ""]
#     path.write_text("\n".join(lines), encoding="utf-8")

# def _ts(sec: float) -> str:
#     h, r = divmod(int(sec), 3600); m, s = divmod(r, 60)
#     return f"{h:02d}:{m:02d}:{s:02d},{int((sec%1)*1000):03d}"


# # ══════════════════════════════════════════════════════════════════════════════
# #  Step 3 — Translate
# # ══════════════════════════════════════════════════════════════════════════════

# def translate_segments(segments, target_lang, workdir):
#     from deep_translator import GoogleTranslator
#     step(f"Translating {len(segments)} segments → {LANGUAGES.get(target_lang, target_lang)} …")

#     tr = GoogleTranslator(source="auto", target=target_lang)
#     errs = 0
#     for i, seg in enumerate(segments, 1):
#         try:
#             seg["translated"] = tr.translate(seg["text"]) or seg["text"]
#         except Exception as e:
#             warn(f"Seg {i} error: {e}")
#             seg["translated"] = seg["text"]
#             errs += 1
#         if i % 10 == 0:
#             time.sleep(0.25)

#     _write_srt(segments, workdir / f"transcript_{target_lang}.srt")
#     ok(f"Translation done ({errs} errors).")
#     return segments


# # ══════════════════════════════════════════════════════════════════════════════
# #  Step 4 — TTS + timeline
# # ══════════════════════════════════════════════════════════════════════════════

# async def _synth_one(text: str, voice: str, out_mp3: Path):
#     import edge_tts
#     await edge_tts.Communicate(text, voice).save(str(out_mp3))


# def synthesise_speech(segments, target_lang, workdir, video_duration, gender="female") -> Path:
#     step(f"Synthesising speech with edge-tts …")
#     voices  = TTS_VOICES.get(target_lang, TTS_VOICES["en"])
#     voice   = voices.get(gender, voices.get("female"))  # fallback to female if gender not found
#     tts_dir = workdir / "tts_segments"
#     tts_dir.mkdir(exist_ok=True)
#     info(f"Voice: {voice} ({gender})")

#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)
#     done = 0

#     for i, seg in enumerate(segments):
#         text    = seg.get("translated", seg["text"]).strip()
#         mp3_out = tts_dir / f"seg_{i:04d}.mp3"
#         wav_out = tts_dir / f"seg_{i:04d}.wav"

#         if not text:
#             make_silence(wav_out, max(seg["end"] - seg["start"], 0.1))
#             continue

#         try:
#             loop.run_until_complete(_synth_one(text, voice, mp3_out))
#             _run_ffmpeg("-i", mp3_out,
#                         "-ar", "24000", "-ac", "1", "-sample_fmt", "s16",
#                         wav_out)
#             mp3_out.unlink(missing_ok=True)
#             done += 1
#         except Exception as e:
#             warn(f"TTS seg {i}: {e}")
#             make_silence(wav_out, max(seg["end"] - seg["start"], 0.1))

#     loop.close()
#     ok(f"Synthesised {done}/{len(segments)} segments.")

#     step("Building audio timeline with ffmpeg …")
#     dubbed = assemble_timeline(segments, tts_dir, workdir, video_duration)
#     ok(f"Dubbed audio ready  →  {dubbed.name}")
#     return dubbed


# # ══════════════════════════════════════════════════════════════════════════════
# #  Step 5 — Merge
# # ══════════════════════════════════════════════════════════════════════════════

# def merge_audio_video(video: Path, audio: Path,
#                       workdir: Path, title: str, lang: str) -> Path:
#     step("Merging dubbed audio with video …")
#     safe = "".join(ch for ch in title if ch.isalnum() or ch in " _-")[:55].strip()
#     out  = workdir / f"{safe}_{lang}_dubbed.mp4"
#     _run_ffmpeg(
#         "-i", video, "-i", audio,
#         "-c:v", "copy",
#         "-c:a", "aac", "-b:a", "192k",
#         "-map", "0:v:0", "-map", "1:a:0",
#         "-shortest", out
#     )
#     mb = out.stat().st_size / 1_048_576
#     ok(f"Merged  →  {out.name}  ({mb:.1f} MB)")
#     return out


# # ══════════════════════════════════════════════════════════════════════════════
# #  Step 6 (optional) — Wav2Lip
# # ══════════════════════════════════════════════════════════════════════════════

# def apply_wav2lip(video: Path, audio: Path, workdir: Path) -> Path:
#     if not WAV2LIP_PATH:
#         warn("WAV2LIP_PATH not set — skipping neural lip-sync.")
#         return video
#     w2l = Path(WAV2LIP_PATH)
#     if not w2l.exists():
#         warn(f"Wav2Lip not found at {w2l} — skipping.")
#         return video

#     step("Applying Wav2Lip neural lip-sync …")
#     out = workdir / "lip_synced.mp4"
#     r = subprocess.run([
#         sys.executable, str(w2l / "inference.py"),
#         "--checkpoint_path", str(w2l / "checkpoints" / "wav2lip_gan.pth"),
#         "--face",    str(video),
#         "--audio",   str(audio),
#         "--outfile", str(out),
#         "--pads",    "0", "10", "0", "0",
#         "--resize_factor", "1",
#     ], capture_output=True, text=True, cwd=str(w2l))

#     if r.returncode != 0:
#         warn(f"Wav2Lip failed — using merged video.\n{r.stderr[-600:]}")
#         return video
#     ok(f"Lip-synced  →  {out.name}")
#     return out


# # ══════════════════════════════════════════════════════════════════════════════
# #  Step 7 — Deliver + cleanup
# # ══════════════════════════════════════════════════════════════════════════════

# def deliver_and_cleanup(final: Path, out_dir: Path,
#                         workdir: Path, keep: bool = False):
#     step("Saving final video …")
#     out_dir.mkdir(parents=True, exist_ok=True)
#     dest = out_dir / final.name
#     shutil.copy2(str(final), str(dest))
#     ok(f"Saved  →  {dest}")

#     if not keep:
#         step("Cleaning up temp workspace …")
#         shutil.rmtree(str(workdir), ignore_errors=True)
#         ok("Workspace cleared.")
#     else:
#         info(f"Workspace kept at: {workdir}")

#     if RICH:
#         console.print(Panel(
#             f"[bold green]✔  All done![/bold green]\n\n"
#             f"[white]Your dubbed video:[/white]\n[bold cyan]{dest}[/bold cyan]",
#             title="Complete", border_style="green"
#         ))
#     else:
#         print(f"\n{'='*60}\n  ✔  Done!\n  Output: {dest}\n{'='*60}\n")


# # ══════════════════════════════════════════════════════════════════════════════
# #  Helpers: language listing + interactive mode + CLI parser
# # ══════════════════════════════════════════════════════════════════════════════

# def list_languages():
#     if RICH:
#         t = Table(title="Supported Languages", border_style="cyan")
#         t.add_column("Code", style="bold yellow", width=8)
#         t.add_column("Language", width=20)
#         t.add_column("Code", style="bold yellow", width=8)
#         t.add_column("Language", width=20)
#         items = sorted(LANGUAGES.items())
#         half  = (len(items) + 1) // 2
#         for (c1, n1), (c2, n2) in zip(items[:half], items[half:] + [("","")]):
#             t.add_row(c1, n1, c2, n2)
#         console.print(t)
#     else:
#         print("\nLanguage codes:")
#         for code, name in sorted(LANGUAGES.items()):
#             print(f"  {code:6s}  {name}")
#     print()


# def interactive_mode():
#     banner()
#     print("  Interactive Setup\n")
#     url = input("  ➤  YouTube URL: ").strip()
#     if not url:
#         err("No URL provided.")
#     list_languages()
#     lang = input("  ➤  Target language code (e.g. 'fr', 'ur', 'es'): ").strip().lower()
#     if lang not in LANGUAGES:
#         err(f"Unknown code '{lang}'. Run with --list-languages.")
#     model  = input("  ➤  Whisper model [tiny/base/small/medium/large] (default: base): ").strip() or "base"
#     output = input("  ➤  Output directory (default: ./output): ").strip() or "./output"
#     keep   = input("  ➤  Keep temp files? [y/N]: ").strip().lower() == "y"
#     return argparse.Namespace(
#         url=url, lang=lang, model=model, output=output,
#         keep=keep, list_languages=False, wav2lip=bool(WAV2LIP_PATH)
#     )


# def build_parser():
#     p = argparse.ArgumentParser(
#         prog="yt_translator",
#         description="YouTube Video Audio Translator — dubs audio into any language.",
#         formatter_class=argparse.RawDescriptionHelpFormatter
#     )
#     p.add_argument("url",  nargs="?", help="YouTube video URL")
#     p.add_argument("-l", "--lang",   default="es", help="Target language code (default: es)")
#     p.add_argument("-m", "--model",  default="base",
#                    choices=["tiny","base","small","medium","large"],
#                    help="Whisper model size (default: base)")
#     p.add_argument("-o", "--output", default="./output", help="Output directory (default: ./output)")
#     p.add_argument("-k", "--keep",   action="store_true", help="Keep temp files")
#     p.add_argument("--wav2lip",      action="store_true", help="Apply Wav2Lip lip-sync")
#     p.add_argument("--list-languages", action="store_true", help="Print language codes and exit")
#     return p


# # ══════════════════════════════════════════════════════════════════════════════
# #  Main
# # ══════════════════════════════════════════════════════════════════════════════

# def main():
#     args = build_parser().parse_args()

#     if args.list_languages:
#         list_languages(); sys.exit(0)

#     if not args.url:
#         args = interactive_mode()

#     banner()
#     check_dependencies()

#     if args.lang not in LANGUAGES:
#         err(f"Unknown language '{args.lang}'. Run --list-languages.")

#     ts      = datetime.now().strftime("%Y%m%d_%H%M%S")
#     workdir = Path(tempfile.gettempdir()) / f"yt_translator_{ts}"
#     workdir.mkdir(parents=True, exist_ok=True)
#     info(f"Workspace: {workdir}")

#     t0 = time.time()
#     try:
#         video_path, audio_path, title, duration = download_video(args.url, workdir)
#         segments, src_lang = transcribe_audio(audio_path, workdir, args.model)
#         if not segments:
#             err("No speech detected.")

#         if src_lang == args.lang:
#             warn(f"Source already '{args.lang}' — skipping translation.")
#             for s in segments: s["translated"] = s["text"]
#         else:
#             segments = translate_segments(segments, args.lang, workdir)

#         dubbed_audio = synthesise_speech(segments, args.lang, workdir, duration)
#         merged       = merge_audio_video(video_path, dubbed_audio, workdir, title, args.lang)
#         final        = apply_wav2lip(merged, dubbed_audio, workdir) if (args.wav2lip or WAV2LIP_PATH) else merged

#         deliver_and_cleanup(final, Path(args.output), workdir, keep=args.keep)
#         info(f"Total time: {int((time.time()-t0)//60)}m {int((time.time()-t0)%60)}s")

#     except KeyboardInterrupt:
#         warn("Interrupted. Cleaning up …")
#         shutil.rmtree(str(workdir), ignore_errors=True)
#         sys.exit(1)
#     except SystemExit:
#         raise
#     except Exception as exc:
#         err(f"Unexpected error: {exc}")
#         raise


# if __name__ == "__main__":
#     main()



import os
import re
import sys
import time
import json
import shutil
import asyncio
import argparse
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional

# ─── Wav2Lip optional path ────────────────────────────────────────────────────
WAV2LIP_PATH = ""   # e.g. "C:/Wav2Lip" — leave empty to skip

# ─── Colour helpers ───────────────────────────────────────────────────────────
try:
    from colorama import Style, init as colorama_init
    colorama_init(autoreset=True)
    def c(text, colour): return f"{colour}{text}{Style.RESET_ALL}"
except ImportError:
    def c(text, _colour): return text

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    RICH = True
    console = Console()
except ImportError:
    RICH = False
    console = None

# ─── Supported languages ──────────────────────────────────────────────────────
LANGUAGES = {
    "af": "Afrikaans",  "sq": "Albanian",   "ar": "Arabic",
    "bn": "Bengali",    "bs": "Bosnian",    "ca": "Catalan",
    "zh": "Chinese",    "hr": "Croatian",   "cs": "Czech",
    "da": "Danish",     "nl": "Dutch",      "en": "English",
    "eo": "Esperanto",  "et": "Estonian",   "tl": "Filipino",
    "fi": "Finnish",    "fr": "French",     "de": "German",
    "el": "Greek",      "gu": "Gujarati",   "hi": "Hindi",
    "hu": "Hungarian",  "id": "Indonesian", "it": "Italian",
    "ja": "Japanese",   "kn": "Kannada",    "ko": "Korean",
    "la": "Latin",      "lv": "Latvian",    "lt": "Lithuanian",
    "ms": "Malay",      "ml": "Malayalam",  "mr": "Marathi",
    "my": "Myanmar",    "ne": "Nepali",     "no": "Norwegian",
    "pa": "Punjabi",    "pl": "Polish",     "pt": "Portuguese",
    "ro": "Romanian",   "ru": "Russian",    "sr": "Serbian",
    "si": "Sinhala",    "sk": "Slovak",     "es": "Spanish",
    "su": "Sundanese",  "sw": "Swahili",    "sv": "Swedish",
    "ta": "Tamil",      "te": "Telugu",     "th": "Thai",
    "tr": "Turkish",    "uk": "Ukrainian",  "ur": "Urdu",
    "vi": "Vietnamese", "cy": "Welsh",
}

# ─── Edge-TTS voice map (FEMALE voices) ───────────────────────────────────────
TTS_VOICES_FEMALE = {
    "af": "af-ZA-AdriNeural",     "sq": "sq-AL-AnilaNeural",
    "ar": "ar-SA-ZariyahNeural",  "bn": "bn-BD-NabanitaNeural",
    "bs": "bs-BA-VesnaNeural",    "ca": "ca-ES-JoanaNeural",
    "zh": "zh-CN-XiaoxiaoNeural", "hr": "hr-HR-GabrijelaNeural",
    "cs": "cs-CZ-VlastaNeural",   "da": "da-DK-ChristelNeural",
    "nl": "nl-NL-ColetteNeural",  "en": "en-US-JennyNeural",
    "et": "et-EE-AnuNeural",      "tl": "fil-PH-BlessicaNeural",
    "fi": "fi-FI-NooraNeural",    "fr": "fr-FR-DeniseNeural",
    "de": "de-DE-KatjaNeural",    "el": "el-GR-AthinaNeural",
    "gu": "gu-IN-DhwaniNeural",   "hi": "hi-IN-SwaraNeural",
    "hu": "hu-HU-NoemiNeural",    "id": "id-ID-GadisNeural",
    "it": "it-IT-ElsaNeural",     "ja": "ja-JP-NanamiNeural",
    "kn": "kn-IN-SapnaNeural",    "ko": "ko-KR-SunHiNeural",
    "lv": "lv-LV-EveritaNeural",  "lt": "lt-LT-OnaNeural",
    "ms": "ms-MY-YasminNeural",   "ml": "ml-IN-SobhanaNeural",
    "mr": "mr-IN-AarohiNeural",   "ne": "ne-NP-HemkalaNeural",
    "no": "nb-NO-PernilleNeural", "pa": "pa-IN-OjasNeural",
    "pl": "pl-PL-ZofiaNeural",    "pt": "pt-BR-FranciscaNeural",
    "ro": "ro-RO-AlinaNeural",    "ru": "ru-RU-SvetlanaNeural",
    "sr": "sr-RS-SophieNeural",   "si": "si-LK-ThiliniNeural",
    "sk": "sk-SK-ViktoriaNeural", "es": "es-ES-ElviraNeural",
    "sw": "sw-KE-ZuriNeural",     "sv": "sv-SE-SofieNeural",
    "ta": "ta-IN-PallaviNeural",  "te": "te-IN-ShrutiNeural",
    "th": "th-TH-PremwadeeNeural","tr": "tr-TR-EmelNeural",
    "uk": "uk-UA-PolinaNeural",   "ur": "ur-PK-UzmaNeural",
    "vi": "vi-VN-HoaiMyNeural",   "cy": "cy-GB-NiaNeural",
}

# ─── Edge-TTS voice map (MALE voices) ─────────────────────────────────────────
TTS_VOICES_MALE = {
    "af": "af-ZA-WillemNeural",   "sq": "sq-AL-IlirNeural",
    "ar": "ar-SA-HamedNeural",    "bn": "bn-BD-PradeepNeural",
    "bs": "bs-BA-GoranNeural",    "ca": "ca-ES-EnricNeural",
    "zh": "zh-CN-YunxiNeural",    "hr": "hr-HR-SreckoNeural",
    "cs": "cs-CZ-AntoninNeural",  "da": "da-DK-JeppeNeural",
    "nl": "nl-NL-MaartenNeural",  "en": "en-US-GuyNeural",
    "et": "et-EE-KertNeural",     "tl": "fil-PH-AngeloNeural",
    "fi": "fi-FI-HarriNeural",    "fr": "fr-FR-HenriNeural",
    "de": "de-DE-ConradNeural",   "el": "el-GR-NestorasNeural",
    "gu": "gu-IN-NiranjanNeural", "hi": "hi-IN-MadhurNeural",
    "hu": "hu-HU-TamasNeural",    "id": "id-ID-ArdiNeural",
    "it": "it-IT-DiegoNeural",    "ja": "ja-JP-KeitaNeural",
    "kn": "kn-IN-GaganNeural",    "ko": "ko-KR-InJoonNeural",
    "lv": "lv-LV-NilsNeural",     "lt": "lt-LT-LeonasNeural",
    "ms": "ms-MY-OsmanNeural",    "ml": "ml-IN-MidhunNeural",
    "mr": "mr-IN-ManoharNeural",  "ne": "ne-NP-SagarNeural",
    "no": "nb-NO-FinnNeural",     "pa": "pa-IN-OjasNeural",
    "pl": "pl-PL-MarekNeural",    "pt": "pt-BR-AntonioNeural",
    "ro": "ro-RO-EmilNeural",     "ru": "ru-RU-DmitryNeural",
    "sr": "sr-RS-NicholasNeural", "si": "si-LK-SameeraNeural",
    "sk": "sk-SK-LukasNeural",    "es": "es-ES-AlvaroNeural",
    "sw": "sw-KE-RafikiNeural",   "sv": "sv-SE-MattiasNeural",
    "ta": "ta-IN-ValluvarNeural", "te": "te-IN-MohanNeural",
    "th": "th-TH-NiwatNeural",    "tr": "tr-TR-AhmetNeural",
    "uk": "uk-UA-OstapNeural",    "ur": "ur-PK-AsadNeural",
    "vi": "vi-VN-NamMinhNeural",  "cy": "cy-GB-AledNeural",
}

# Max chars per TTS request — stay well under edge-tts limits
TTS_MAX_CHARS = 480


# ══════════════════════════════════════════════════════════════════════════════
#  Logging helpers
# ══════════════════════════════════════════════════════════════════════════════

def banner():
    art = r"""
  __  ______   ___________  _    ____ ___ ____  ___
  \ \/ /_  /  |_   _|  _ \| |  / ___|_ _/ ___|/ _ \
   \  / / /     | | | |_) | | | |  _ | |\___ \ | | |
   / // /_      | | |  _ <| |__| |_| || | ___) | |_| |
  /_//____|     |_| |_| \_\_____\____|___|____/ \___/
    YouTube Video Translator — CLI  (Audio Dub + Lip Sync)
"""
    if RICH:
        console.print(Panel(art, style="bold cyan"))
    else:
        print(art)


def step(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    if RICH:
        console.print(f"\n[bold cyan][{ts}][/bold cyan] [bold white]{msg}[/bold white]")
    else:
        print(f"\n[{ts}] {msg}")


def ok(msg: str):
    if RICH: console.print(f"  [bold green]✔[/bold green] {msg}")
    else:    print(f"  ✔ {msg}")


def warn(msg: str):
    if RICH: console.print(f"  [bold yellow]⚠[/bold yellow]  {msg}")
    else:    print(f"  ⚠  {msg}")


def err(msg: str):
    if RICH: console.print(f"\n  [bold red]✘[/bold red] {msg}")
    else:    print(f"\n  ✘ {msg}")
    sys.exit(1)


def info(msg: str):
    if RICH: console.print(f"     [dim]{msg}[/dim]")
    else:    print(f"     {msg}")


# ══════════════════════════════════════════════════════════════════════════════
#  Dependency check
# ══════════════════════════════════════════════════════════════════════════════

def check_dependencies():
    step("Checking dependencies …")
    missing = []

    # ffmpeg AND ffprobe are both required
    for tool in ("ffmpeg", "ffprobe"):
        if shutil.which(tool) is None:
            if sys.platform == "win32":
                missing.append(
                    f"{tool}  →  winget install ffmpeg  (then reopen terminal)"
                )
            elif sys.platform == "darwin":
                missing.append(f"{tool}  →  brew install ffmpeg")
            else:
                missing.append(f"{tool}  →  sudo apt install ffmpeg")

    # Python packages
    pkgs = {
        "yt_dlp":          "yt-dlp",
        "whisper":         "openai-whisper",
        "deep_translator": "deep-translator",
        "edge_tts":        "edge-tts",
        "rich":            "rich",
        "colorama":        "colorama",
    }
    for mod, pip_name in pkgs.items():
        try:
            __import__(mod)
        except ImportError:
            missing.append(f"pip install {pip_name}")

    if missing:
        print()
        for m in missing:
            line = f"  • {m}"
            if RICH: console.print(f"[red]{line}[/red]")
            else:    print(line)
        err("Install the above, then re-run.")

    ok("All dependencies satisfied.")


# ══════════════════════════════════════════════════════════════════════════════
#  Pure-ffmpeg audio helpers
# ══════════════════════════════════════════════════════════════════════════════

def _run_ffmpeg(*args, timeout: int = 300):
    """
    Run: ffmpeg -y -loglevel error <args>
    Raises RuntimeError on non-zero exit or timeout.
    """
    cmd = ["ffmpeg", "-y", "-loglevel", "error"] + [str(a) for a in args]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"ffmpeg timed out after {timeout}s")
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-3000:] or "ffmpeg returned non-zero exit code")


def get_audio_duration(path: Path) -> float:
    """Return audio/video duration in seconds via ffprobe, or 0.0 on failure."""
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_format", str(path)],
            capture_output=True, text=True, timeout=30,
        )
        return float(json.loads(r.stdout)["format"]["duration"])
    except Exception:
        return 0.0


def make_silence(path: Path, duration: float, sr: int = 24000):
    """Write a PCM WAV file of pure silence."""
    duration = max(duration, 0.05)
    _run_ffmpeg(
        "-f", "lavfi", "-i", f"anullsrc=r={sr}:cl=mono",
        "-t", str(duration),
        "-ar", str(sr), "-ac", "1", "-acodec", "pcm_s16le",
        path,
    )


def speed_audio_ffmpeg(src: Path, dst: Path, ratio: float):
    """
    Change playback speed by `ratio` using chained atempo filters.
    Each atempo step must be in [0.5, 2.0], so we chain multiple steps.

    Examples:
        ratio=3.0  → atempo=2.0, atempo=1.5
        ratio=0.25 → atempo=0.5, atempo=0.5
    """
    ratio = max(0.4, min(ratio, 4.0))
    filters: list = []
    r = ratio

    # Decompose values above 2.0 into 2.0× steps
    while r > 2.0:
        filters.append("atempo=2.0")
        r /= 2.0

    # Decompose values below 0.5 into 0.5× steps
    # (r *= 2.0 compensates so the final r stays in [0.5, 2.0])
    while r < 0.5:
        filters.append("atempo=0.5")
        r *= 2.0

    filters.append(f"atempo={r:.6f}")

    _run_ffmpeg(
        "-i", src,
        "-filter:a", ",".join(filters),
        "-ar", "24000", "-ac", "1", "-acodec", "pcm_s16le",
        dst,
    )


def trim_pad_ffmpeg(src: Path, dst: Path, target_dur: float, sr: int = 24000):
    """Trim or silence-pad a WAV to exactly `target_dur` seconds."""
    src_dur = get_audio_duration(src)
    if src_dur <= 0:
        make_silence(dst, target_dur, sr)
        return

    if src_dur >= target_dur:
        _run_ffmpeg(
            "-i", src, "-t", str(target_dur),
            "-ar", str(sr), "-ac", "1", "-acodec", "pcm_s16le",
            dst,
        )
    else:
        # Concatenate source + silence padding
        pad_dur  = target_dur - src_dur
        pad_file = dst.parent / f"_pad_{dst.stem}.wav"
        make_silence(pad_file, pad_dur, sr)

        # IMPORTANT: ffmpeg concat demuxer requires POSIX (forward-slash) paths
        # even on Windows — using .as_posix() fixes Windows path failures.
        list_file = dst.parent / f"_cat_{dst.stem}.txt"
        list_file.write_text(
            f"file '{src.resolve().as_posix()}'\n"
            f"file '{pad_file.resolve().as_posix()}'\n",
            encoding="utf-8",
        )
        try:
            _run_ffmpeg(
                "-f", "concat", "-safe", "0", "-i", list_file,
                "-ar", str(sr), "-ac", "1", "-acodec", "pcm_s16le",
                dst,
            )
        finally:
            list_file.unlink(missing_ok=True)
            pad_file.unlink(missing_ok=True)


def assemble_timeline(
    segments: list, tts_dir: Path, workdir: Path, video_duration: float
) -> Path:
    """
    Place every TTS clip at its original timestamp using ffmpeg's
    adelay + amix. Processes in batches of 16 for stability.
    No pydub required.
    """
    SR    = 24000
    total = video_duration + 2.0   # small safety tail

    ready_dir = workdir / "_ready"
    ready_dir.mkdir(exist_ok=True)

    placed: list = []   # list of (delay_ms: int, wav: Path)

    for i, seg in enumerate(segments):
        raw = tts_dir / f"seg_{i:04d}.wav"
        if not raw.exists():
            continue

        slot    = max(seg["end"] - seg["start"], 0.1)
        src_dur = get_audio_duration(raw)
        if src_dur <= 0:
            continue

        # ── Speed-adjust TTS to fit the subtitle slot ────────────────────
        speed_out = ready_dir / f"{i:04d}_s.wav"
        ratio     = max(0.4, min(src_dur / slot, 4.0))
        try:
            if abs(ratio - 1.0) > 0.05:
                speed_audio_ffmpeg(raw, speed_out, ratio)
            else:
                shutil.copy2(str(raw), str(speed_out))
        except Exception as e:
            warn(f"Speed-adjust seg {i}: {e} — using original length")
            shutil.copy2(str(raw), str(speed_out))

        # ── Trim / pad to exact slot length ──────────────────────────────
        final_out = ready_dir / f"{i:04d}_f.wav"
        try:
            trim_pad_ffmpeg(speed_out, final_out, slot, SR)
        except Exception as e:
            warn(f"Trim/pad seg {i}: {e} — using speed-adjusted file")
            shutil.copy2(str(speed_out), str(final_out))
        speed_out.unlink(missing_ok=True)

        placed.append((int(seg["start"] * 1000), final_out))

    out_path = workdir / "dubbed_audio.wav"

    if not placed:
        warn("No TTS segments placed — output will be silence.")
        make_silence(out_path, total, SR)
        return out_path

    # ── Build final track: start from silence, mix in batches ────────────
    tmp_dir = workdir / "_timeline"
    tmp_dir.mkdir(exist_ok=True)
    current = tmp_dir / "base.wav"
    make_silence(current, total, SR)

    BATCH = 16   # smaller batch = more stable on older ffmpeg builds
    for b_start in range(0, len(placed), BATCH):
        chunk = placed[b_start: b_start + BATCH]
        n     = len(chunk)

        inputs: list = ["-i", str(current)]
        for _, wav in chunk:
            inputs += ["-i", str(wav)]

        fc_parts: list = []
        for j, (delay_ms, _) in enumerate(chunk):
            fc_parts.append(
                f"[{j+1}:a]adelay={delay_ms}|{delay_ms}[d{j}]"
            )
        mix_inputs = "[0:a]" + "".join(f"[d{j}]" for j in range(n))
        # normalize=0   → don't reduce volume when mixing
        # dropout_transition=0 → no fade when a stream ends
        fc_parts.append(
            f"{mix_inputs}amix=inputs={n+1}:duration=longest"
            f":normalize=0:dropout_transition=0[out]"
        )

        batch_out = tmp_dir / f"b{b_start:05d}.wav"
        cmd = (
            ["ffmpeg", "-y", "-loglevel", "error"]
            + inputs
            + [
                "-filter_complex", ";".join(fc_parts),
                "-map", "[out]",
                "-ar", str(SR), "-ac", "1", "-acodec", "pcm_s16le",
                str(batch_out),
            ]
        )
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if r.returncode == 0:
                current = batch_out
            else:
                warn(f"Batch {b_start} mix failed — skipping: {r.stderr[-400:]}")
        except subprocess.TimeoutExpired:
            warn(f"Batch {b_start} mix timed out — skipping.")

    shutil.copy2(str(current), str(out_path))
    shutil.rmtree(str(tmp_dir),   ignore_errors=True)
    shutil.rmtree(str(ready_dir), ignore_errors=True)
    return out_path


# ══════════════════════════════════════════════════════════════════════════════
#  Step 1 — Download
# ══════════════════════════════════════════════════════════════════════════════

def download_video(url: str, workdir: Path):
    import yt_dlp
    step("Downloading video & audio from YouTube …")

    # ── Video only (no audio) ─────────────────────────────────────────────
    ydl_v_opts = {
        "format":      "bestvideo[height<=1080][ext=mp4]/bestvideo[height<=1080]/bestvideo",
        "outtmpl":     str(workdir / "video_raw.%(ext)s"),
        "quiet":       True,
        "no_warnings": True,
    }
    title = "video"
    duration = 0.0
    with yt_dlp.YoutubeDL(ydl_v_opts) as ydl:
        meta     = ydl.extract_info(url, download=True)
        title    = meta.get("title", "video")
        duration = float(meta.get("duration") or 0)

    # Normalise whatever we got to MP4
    video_path = workdir / "video_raw.mp4"
    converted  = False
    for ext in ("mp4", "webm", "mkv", "avi", "mov"):
        cand = workdir / f"video_raw.{ext}"
        if cand.exists():
            if ext != "mp4":
                info(f"Converting {ext} → mp4 …")
                _run_ffmpeg(
                    "-i", cand, "-c:v", "libx264",
                    "-crf", "18", "-preset", "fast", "-an",
                    video_path, timeout=600,
                )
                cand.unlink(missing_ok=True)
            else:
                video_path = cand
            converted = True
            break

    if not converted:
        candidates = list(workdir.glob("video_raw.*"))
        if not candidates:
            raise RuntimeError(
                "Video download failed — no output file found. "
                "Check the URL and your network connection."
            )
        cand = candidates[0]
        info(f"Converting {cand.suffix} → mp4 …")
        _run_ffmpeg(
            "-i", cand, "-c:v", "libx264",
            "-crf", "18", "-preset", "fast", "-an",
            video_path, timeout=600,
        )
        cand.unlink(missing_ok=True)

    # ── Audio WAV ─────────────────────────────────────────────────────────
    audio_path  = workdir / "audio_original.wav"
    ydl_a_opts = {
        "format":      "bestaudio/best",
        "outtmpl":     str(workdir / "audio_dl.%(ext)s"),
        "quiet":       True,
        "no_warnings": True,
        "postprocessors": [{
            "key":              "FFmpegExtractAudio",
            "preferredcodec":   "wav",
            "preferredquality": "0",
        }],
    }
    with yt_dlp.YoutubeDL(ydl_a_opts) as ydl:
        ydl.download([url])

    # Find the produced WAV (yt-dlp may rename to audio_dl.wav directly)
    found_audio: Optional[Path] = None
    for f in workdir.iterdir():
        if "audio_dl" in f.name and f.suffix.lower() == ".wav":
            found_audio = f
            break

    if found_audio:
        found_audio.rename(audio_path)
    else:
        # Fallback: convert any audio_dl.* file we can find
        candidates = [f for f in workdir.iterdir() if "audio_dl" in f.name]
        if candidates:
            src = candidates[0]
            info(f"Converting {src.suffix} → wav …")
            _run_ffmpeg(
                "-i", src,
                "-ar", "16000", "-ac", "1", "-acodec", "pcm_s16le",
                audio_path,
            )
            src.unlink(missing_ok=True)
        else:
            raise RuntimeError(
                "Audio download failed — no audio_dl file found. "
                "Check the URL and your network connection."
            )

    info(f"Title    : {title}")
    info(f"Duration : {int(duration // 60)}m {int(duration % 60)}s")
    ok(f"Video  →  {video_path.name}")
    ok(f"Audio  →  {audio_path.name}")
    return video_path, audio_path, title, duration


# ══════════════════════════════════════════════════════════════════════════════
#  Step 2 — Transcribe
# ══════════════════════════════════════════════════════════════════════════════

def transcribe_audio(audio_path: Path, workdir: Path, model_size: str = "base"):
    import whisper
    step(f"Transcribing with Whisper [{model_size}] …")
    info("First run downloads the model — please wait.")
    info("Size reference: tiny≈75 MB | base≈150 MB | small≈480 MB | medium≈1.5 GB")

    model  = whisper.load_model(model_size)
    result = model.transcribe(
        str(audio_path),
        verbose=None,          # show segment progress
        word_timestamps=False,
        fp16=False,            # suppress FP16 warnings on CPU-only systems
    )

    segments = [
        {
            "start": float(s["start"]),
            "end":   float(s["end"]),
            "text":  s["text"].strip(),
        }
        for s in result.get("segments", [])
        if s["text"].strip()
    ]

    _write_srt(segments, workdir / "transcript_original.srt")
    detected = result.get("language", "unknown")
    ok(f"Transcribed {len(segments)} segments — detected language: {detected}")
    return segments, detected


def _write_srt(segs: list, path: Path):
    lines: list = []
    for i, s in enumerate(segs, 1):
        text = s.get("translated", s["text"])
        lines += [str(i), f"{_ts(s['start'])} --> {_ts(s['end'])}", text, ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def _ts(sec: float) -> str:
    # Convert to integer milliseconds first to avoid floating-point drift.
    total_ms = round(max(0.0, float(sec)) * 1000)
    ms       = total_ms % 1000
    total_s  = total_ms // 1000
    h, r     = divmod(total_s, 3600)
    m, s     = divmod(r, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


# ══════════════════════════════════════════════════════════════════════════════
#  Step 3 — Translate
# ══════════════════════════════════════════════════════════════════════════════

def translate_segments(segments: list, target_lang: str, workdir: Path) -> list:
    from deep_translator import GoogleTranslator
    step(
        f"Translating {len(segments)} segments → "
        f"{LANGUAGES.get(target_lang, target_lang)} …"
    )

    tr   = GoogleTranslator(source="auto", target=target_lang)
    errs = 0

    for i, seg in enumerate(segments, 1):
        text = seg["text"].strip()
        if not text:
            seg["translated"] = ""
            continue

        # Retry up to 3 times with exponential back-off
        for attempt in range(3):
            try:
                result = tr.translate(text)
                seg["translated"] = result if result else text
                break
            except Exception as e:
                if attempt == 2:
                    warn(f"Seg {i} failed after 3 attempts: {e}")
                    seg["translated"] = text
                    errs += 1
                else:
                    time.sleep(1.5 * (attempt + 1))

        # Gentle rate-limiting — avoid 429 responses from Google
        if i % 5 == 0:
            time.sleep(0.4)

    _write_srt(segments, workdir / f"transcript_{target_lang}.srt")
    ok(f"Translation done ({errs} error(s)).")
    return segments


# ══════════════════════════════════════════════════════════════════════════════
#  Step 4 — TTS + timeline assembly
# ══════════════════════════════════════════════════════════════════════════════

def _sanitize_tts(text: str) -> str:
    """Remove characters that break edge-tts and normalise whitespace."""
    text = re.sub(r"<[^>]+>", " ", text)                            # XML/HTML tags
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)  # control chars
    text = " ".join(text.split())                                    # collapse spaces
    return text.strip()


def _chunk_text(text: str, max_chars: int = TTS_MAX_CHARS) -> list:
    """
    Split text into chunks of at most `max_chars` characters.
    Prefers sentence boundaries (. ! ? ।), then word boundaries.
    """
    if len(text) <= max_chars:
        return [text]

    chunks: list = []
    current = ""
    for sentence in re.split(r"(?<=[.!?।])\s+", text):
        if len(current) + len(sentence) + 1 <= max_chars:
            current = f"{current} {sentence}".strip() if current else sentence
        else:
            if current:
                chunks.append(current)
            if len(sentence) > max_chars:
                # Hard word-level split
                current = ""
                for word in sentence.split():
                    if len(current) + len(word) + 1 <= max_chars:
                        current = f"{current} {word}".strip() if current else word
                    else:
                        if current:
                            chunks.append(current)
                        current = word
            else:
                current = sentence

    if current:
        chunks.append(current)
    return chunks or [text[:max_chars]]


async def _tts_to_wav(text: str, voice: str, out_wav: Path, tmp_dir: Path):
    """Synthesize `text` → PCM WAV, splitting long text into chunks first."""
    import edge_tts
    chunks = _chunk_text(text)

    if len(chunks) == 1:
        mp3 = out_wav.with_suffix(".mp3")
        await edge_tts.Communicate(chunks[0], voice).save(str(mp3))
        _run_ffmpeg(
            "-i", mp3,
            "-ar", "24000", "-ac", "1", "-acodec", "pcm_s16le",
            out_wav,
        )
        mp3.unlink(missing_ok=True)
    else:
        # Synthesize each chunk then concatenate into one WAV
        chunk_wavs: list = []
        for ci, chunk in enumerate(chunks):
            mp3 = tmp_dir / f"_ck_{out_wav.stem}_{ci}.mp3"
            wav = tmp_dir / f"_ck_{out_wav.stem}_{ci}.wav"
            await edge_tts.Communicate(chunk, voice).save(str(mp3))
            _run_ffmpeg(
                "-i", mp3,
                "-ar", "24000", "-ac", "1", "-acodec", "pcm_s16le",
                wav,
            )
            mp3.unlink(missing_ok=True)
            chunk_wavs.append(wav)

        list_f = tmp_dir / f"_ck_{out_wav.stem}.txt"
        list_f.write_text(
            "\n".join(f"file '{w.resolve().as_posix()}'" for w in chunk_wavs),
            encoding="utf-8",
        )
        try:
            _run_ffmpeg(
                "-f", "concat", "-safe", "0", "-i", list_f,
                "-ar", "24000", "-ac", "1", "-acodec", "pcm_s16le",
                out_wav,
            )
        finally:
            list_f.unlink(missing_ok=True)
            for w in chunk_wavs:
                w.unlink(missing_ok=True)


async def _synth_all(
    segments: list, voice: str, tts_dir: Path, tmp_dir: Path
) -> int:
    """Async driver: synthesize every segment with per-segment retry."""
    done = 0
    for i, seg in enumerate(segments):
        text    = _sanitize_tts(seg.get("translated", seg["text"]))
        wav_out = tts_dir / f"seg_{i:04d}.wav"
        slot    = max(seg["end"] - seg["start"], 0.1)

        if not text:
            make_silence(wav_out, slot)
            continue

        success = False
        for attempt in range(3):
            try:
                await _tts_to_wav(text, voice, wav_out, tmp_dir)
                success = True
                done += 1
                break
            except Exception as e:
                if attempt < 2:
                    await asyncio.sleep(1.5 * (attempt + 1))
                else:
                    warn(f"TTS seg {i} failed after 3 attempts: {e}")

        if not success:
            make_silence(wav_out, slot)

    return done


def synthesise_speech(
    segments: list, target_lang: str, workdir: Path, video_duration: float, gender: str = "female"
) -> Path:
    """
    Synthesize speech for all segments using Edge TTS.
    
    Args:
        segments: List of text segments to synthesize
        target_lang: Target language code
        workdir: Working directory
        video_duration: Total video duration in seconds
        gender: Voice gender ("male" or "female")
    """
    step("Synthesising speech with edge-tts …")
    
    # Select voice based on gender
    if gender.lower() == "male":
        voice = TTS_VOICES_MALE.get(target_lang, TTS_VOICES_MALE.get("en", "en-US-GuyNeural"))
    else:
        voice = TTS_VOICES_FEMALE.get(target_lang, TTS_VOICES_FEMALE.get("en", "en-US-JennyNeural"))
    
    tts_dir = workdir / "tts_segments"
    tts_dir.mkdir(exist_ok=True)
    info(f"Voice    : {voice} ({gender})")
    info(f"Segments : {len(segments)}")

    # asyncio.run() correctly creates, uses, and closes the event loop —
    # safe on Python 3.9+ on all platforms (Windows, macOS, Linux).
    done = asyncio.run(_synth_all(segments, voice, tts_dir, workdir))
    ok(f"Synthesised {done}/{len(segments)} segments.")

    step("Building audio timeline with ffmpeg …")
    dubbed = assemble_timeline(segments, tts_dir, workdir, video_duration)
    ok(f"Dubbed audio  →  {dubbed.name}")
    return dubbed


# ══════════════════════════════════════════════════════════════════════════════
#  Step 5 — Merge audio + video
# ══════════════════════════════════════════════════════════════════════════════

def merge_audio_video(
    video: Path, audio: Path, workdir: Path, title: str, lang: str
) -> Path:
    step("Merging dubbed audio with video …")
    # Safe filename: keep letters, digits, spaces, hyphens, underscores
    safe = re.sub(r"[^\w\s\-]", "", title, flags=re.UNICODE)[:55].strip()
    safe = re.sub(r"\s+", "_", safe) or "output"
    out  = workdir / f"{safe}_{lang}_dubbed.mp4"
    _run_ffmpeg(
        "-i", video, "-i", audio,
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-map", "0:v:0", "-map", "1:a:0",
        "-shortest",
        out,
        timeout=600,
    )
    mb = out.stat().st_size / 1_048_576
    ok(f"Merged  →  {out.name}  ({mb:.1f} MB)")
    return out


# ══════════════════════════════════════════════════════════════════════════════
#  Step 6 (optional) — Wav2Lip neural lip-sync
# ══════════════════════════════════════════════════════════════════════════════

def apply_wav2lip(video: Path, audio: Path, workdir: Path) -> Path:
    if not WAV2LIP_PATH:
        warn("WAV2LIP_PATH not set — skipping neural lip-sync.")
        return video
    w2l = Path(WAV2LIP_PATH)
    if not w2l.exists():
        warn(f"Wav2Lip not found at {w2l} — skipping.")
        return video

    step("Applying Wav2Lip neural lip-sync …")
    out = workdir / "lip_synced.mp4"
    r   = subprocess.run(
        [
            sys.executable, str(w2l / "inference.py"),
            "--checkpoint_path", str(w2l / "checkpoints" / "wav2lip_gan.pth"),
            "--face",    str(video),
            "--audio",   str(audio),
            "--outfile", str(out),
            "--pads",    "0", "10", "0", "0",
            "--resize_factor", "1",
        ],
        capture_output=True, text=True,
        cwd=str(w2l), timeout=1800,
    )
    if r.returncode != 0:
        warn(f"Wav2Lip failed — using merged video.\n{r.stderr[-600:]}")
        return video
    ok(f"Lip-synced  →  {out.name}")
    return out


# ══════════════════════════════════════════════════════════════════════════════
#  Step 7 — Deliver & clean up
# ══════════════════════════════════════════════════════════════════════════════

def deliver_and_cleanup(
    final: Path, out_dir: Path, workdir: Path, keep: bool = False
):
    step("Saving final video …")
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / final.name
    shutil.copy2(str(final), str(dest))
    ok(f"Saved  →  {dest}")

    if not keep:
        step("Cleaning up temp workspace …")
        shutil.rmtree(str(workdir), ignore_errors=True)
        ok("Workspace cleared.")
    else:
        info(f"Workspace kept at: {workdir}")

    if RICH:
        console.print(Panel(
            f"[bold green]✔  All done![/bold green]\n\n"
            f"[white]Your dubbed video:[/white]\n[bold cyan]{dest}[/bold cyan]",
            title="Complete", border_style="green",
        ))
    else:
        print(f"\n{'=' * 60}\n  ✔  Done!\n  Output: {dest}\n{'=' * 60}\n")


# ══════════════════════════════════════════════════════════════════════════════
#  Utilities: language list, interactive mode, CLI parser
# ══════════════════════════════════════════════════════════════════════════════

def list_languages():
    if RICH:
        t = Table(title="Supported Languages", border_style="cyan")
        t.add_column("Code",     style="bold yellow", width=8)
        t.add_column("Language", width=20)
        t.add_column("Code",     style="bold yellow", width=8)
        t.add_column("Language", width=20)
        items = sorted(LANGUAGES.items())
        half  = (len(items) + 1) // 2
        for (c1, n1), (c2, n2) in zip(items[:half], items[half:] + [("", "")]):
            t.add_row(c1, n1, c2, n2)
        console.print(t)
    else:
        print("\nLanguage codes:")
        for code, name in sorted(LANGUAGES.items()):
            print(f"  {code:6s}  {name}")
    print()


def interactive_mode() -> argparse.Namespace:
    banner()
    print("  Interactive Setup\n")
    url = input("  ➤  YouTube URL: ").strip()
    if not url:
        err("No URL provided.")

    list_languages()
    lang = input(
        "  ➤  Target language code (e.g. 'fr', 'ur', 'es'): "
    ).strip().lower()
    if lang not in LANGUAGES:
        err(f"Unknown code '{lang}'. Run with --list-languages to see all codes.")

    gender = input("  ➤  Voice gender [male/female] (default: female): ").strip().lower()
    if gender not in ["male", "female", ""]:
        warn(f"Invalid gender '{gender}', defaulting to female.")
        gender = "female"
    if not gender:
        gender = "female"

    model  = (
        input("  ➤  Whisper model [tiny/base/small/medium/large] (default: base): ")
        .strip() or "base"
    )
    output = input("  ➤  Output directory (default: ./output): ").strip() or "./output"
    keep   = input("  ➤  Keep temp files? [y/N]: ").strip().lower() == "y"

    return argparse.Namespace(
        url=url, lang=lang, gender=gender, model=model, output=output,
        keep=keep, list_languages=False, wav2lip=bool(WAV2LIP_PATH),
    )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="app",
        description="YouTube Video Audio Translator — dubs audio into any language.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python app.py                           # interactive\n"
            "  python app.py <URL> -l fr               # French dub (female voice)\n"
            "  python app.py <URL> -l ur -m small      # Urdu, better model (female)\n"
            "  python app.py <URL> -l es -g male       # Spanish with male voice\n"
            "  python app.py --list-languages          # see all codes\n"
        ),
    )
    p.add_argument("url",  nargs="?", help="YouTube video URL")
    p.add_argument("-l", "--lang",   default="es",
                   help="Target language code (default: es)")
    p.add_argument("-g", "--gender", default="female",
                   choices=["male", "female"],
                   help="Voice gender for TTS (default: female)")
    p.add_argument("-m", "--model",  default="base",
                   choices=["tiny", "base", "small", "medium", "large"],
                   help="Whisper model size (default: base)")
    p.add_argument("-o", "--output", default="./output",
                   help="Output directory (default: ./output)")
    p.add_argument("-k", "--keep",   action="store_true",
                   help="Keep temp workspace after completion")
    p.add_argument("--wav2lip",      action="store_true",
                   help="Apply Wav2Lip neural lip-sync (requires Wav2Lip setup)")
    p.add_argument("--list-languages", action="store_true",
                   help="Print all supported language codes and exit")
    return p


# ══════════════════════════════════════════════════════════════════════════════
#  Main entry point
# ══════════════════════════════════════════════════════════════════════════════

def main():
    args = build_parser().parse_args()

    if args.list_languages:
        list_languages()
        sys.exit(0)

    if not args.url:
        args = interactive_mode()

    banner()
    check_dependencies()

    if args.lang not in LANGUAGES:
        err(f"Unknown language code '{args.lang}'. Run --list-languages.")

    ts      = datetime.now().strftime("%Y%m%d_%H%M%S")
    workdir = Path(tempfile.gettempdir()) / f"yt_translator_{ts}"
    workdir.mkdir(parents=True, exist_ok=True)
    info(f"Workspace: {workdir}")

    t0 = time.time()
    try:
        video_path, audio_path, title, duration = download_video(args.url, workdir)

        # Fallback if yt-dlp didn't report a duration
        if duration <= 0:
            warn("Duration unknown from metadata — measuring audio length …")
            duration = get_audio_duration(audio_path)

        segments, src_lang = transcribe_audio(audio_path, workdir, args.model)
        if not segments:
            err(
                "No speech detected in audio. "
                "Try a larger Whisper model (e.g. -m small) or check the video."
            )

        if src_lang == args.lang:
            warn(
                f"Detected language is already '{args.lang}' — "
                "skipping translation (TTS will still run)."
            )
            for s in segments:
                s["translated"] = s["text"]
        else:
            segments = translate_segments(segments, args.lang, workdir)

        # Fixed: Pass gender parameter correctly
        dubbed_audio = synthesise_speech(segments, args.lang, workdir, duration, args.gender)
        merged       = merge_audio_video(video_path, dubbed_audio, workdir, title, args.lang)
        final        = (
            apply_wav2lip(merged, dubbed_audio, workdir)
            if (args.wav2lip or WAV2LIP_PATH)
            else merged
        )

        deliver_and_cleanup(final, Path(args.output), workdir, keep=args.keep)

        elapsed = time.time() - t0
        info(f"Total time: {int(elapsed // 60)}m {int(elapsed % 60)}s")

    except KeyboardInterrupt:
        warn("\nInterrupted by user. Cleaning up …")
        shutil.rmtree(str(workdir), ignore_errors=True)
        sys.exit(130)
    except SystemExit:
        raise
    except Exception as exc:
        err(f"Unexpected error: {exc}")


if __name__ == "__main__":
    main()