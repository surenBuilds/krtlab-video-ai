from pathlib import Path
import subprocess
import shutil

INPUT = Path.home() / "Downloads" / "20260930_094350(1).mp4"
OUTPUT = Path("output") / "krtlab_final.mp4"
SRT = Path("output") / "subtitles.srt"

if not INPUT.exists():
    raise SystemExit(f"Video not found: {INPUT}")

if shutil.which("ffmpeg") is None:
    raise SystemExit("FFmpeg is not installed or not on PATH.")

OUTPUT.parent.mkdir(exist_ok=True)

filters = (
    "scale=1080:1920:force_original_aspect_ratio=increase,"
    "crop=1080:1920,"
    "setsar=1,"
    "eq=contrast=1.03:brightness=0.01:saturation=1.04,"
    "unsharp=5:5:0.5:5:5:0,"
    "format=yuv420p"
)

if SRT.exists():
    subtitle = SRT.resolve().as_posix().replace(":", r"\:")
    subtitle = subtitle.replace("'", r"\'")
    filters += f",subtitles='{subtitle}'"

audio = (
    "highpass=f=70,"
    "lowpass=f=14000,"
    "acompressor=threshold=-18dB:ratio=3:attack=5:release=80,"
    "loudnorm=I=-16:TP=-1.5:LRA=11"
)

cmd = [
    "ffmpeg", "-y",
    "-i", str(INPUT),
    "-vf", filters,
    "-af", audio,
    "-c:v", "libx264",
    "-preset", "veryfast",
    "-crf", "21",
    "-c:a", "aac",
    "-b:a", "192k",
    "-movflags", "+faststart",
    str(OUTPUT)
]

print("Rendering KrtLab video...")
subprocess.run(cmd, check=True)

print(f"\nDONE: {OUTPUT.resolve()}")
