"""Final studio render: preserve the generated background replacement and restore original audio."""
from pathlib import Path
import imageio_ffmpeg
import subprocess

ROOT = Path(__file__).resolve().parents[1]
VIDEO = ROOT / "output" / "studio_video.mp4"
AUDIO_SOURCE = ROOT / "input" / "video.mp4"
OUTPUT = ROOT / "output" / "final.mp4"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

def main():
    if not VIDEO.exists():
        raise SystemExit(f"Missing {VIDEO}. Run fast_background.py first.")
    if not AUDIO_SOURCE.exists():
        raise SystemExit(f"Missing {AUDIO_SOURCE}.")

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
        FFMPEG, "-y",
        "-i", str(VIDEO),
        "-i", str(AUDIO_SOURCE),
        "-vf", vf,
        "-af", af,
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",
        str(OUTPUT)
    ]
    print("Rendering final KrtLab studio master with original speech...")
    subprocess.run(cmd, check=True)
    print(f"Created: {OUTPUT}")

if __name__ == "__main__":
    main()
