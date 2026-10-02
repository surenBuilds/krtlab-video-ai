from pathlib import Path
import shutil
import subprocess

import imageio_ffmpeg

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "input" / "video.mp4"
OUTPUT = ROOT / "output" / "final.mp4"


def main() -> None:
    if not INPUT.exists():
        raise SystemExit(f"Missing input video: {INPUT}")

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    vf = (
        "scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,"
        "eq=contrast=1.03:brightness=0.01:saturation=1.04,"
        "unsharp=5:5:0.5:5:5:0,"
        "format=yuv420p"
    )
    af = (
        "highpass=f=70,lowpass=f=14000,"
        "acompressor=threshold=-18dB:ratio=3:attack=5:release=80,"
        "loudnorm=I=-16:TP=-1.5:LRA=11"
    )

    cmd = [
        ffmpeg, "-y", "-i", str(INPUT),
        "-vf", vf, "-af", af,
        "-map", "0:v:0", "-map", "0:a?",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart", str(OUTPUT),
    ]
    print("Rendering KrtLab video...")
    subprocess.run(cmd, check=True)
    print(f"Created: {OUTPUT}")


if __name__ == "__main__":
    main()
