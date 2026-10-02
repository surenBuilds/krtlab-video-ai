"""Final studio render: use locally generated studio_video.mp4 and make a social-ready 9:16 master."""
from pathlib import Path
import imageio_ffmpeg
import subprocess

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "output" / "studio_video.mp4"
OUTPUT = ROOT / "output" / "final.mp4"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

def main():
    if not INPUT.exists():
        raise SystemExit(f"Missing {INPUT}. Run fast_background.py first.")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    vf = (
        "scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,"
        "setsar=1,"
        "eq=contrast=1.025:brightness=0.008:saturation=1.035,"
        "unsharp=5:5:0.35:5:5:0,"
        "format=yuv420p"
    )
    af = (
        "highpass=f=70,lowpass=f=14500,"
        "acompressor=threshold=-20dB:ratio=2.5:attack=8:release=100:makeup=2,"
        "loudnorm=I=-15:TP=-1.5:LRA=9"
    )

    cmd = [
        FFMPEG, "-y", "-i", str(INPUT),
        "-vf", vf, "-af", af,
        "-map", "0:v:0", "-map", "0:a?",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
        str(OUTPUT)
    ]
    print("Rendering final KrtLab studio master...")
    subprocess.run(cmd, check=True)
    print(f"Created: {OUTPUT}")

if __name__ == "__main__":
    main()
