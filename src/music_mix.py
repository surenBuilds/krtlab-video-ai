from pathlib import Path
import imageio_ffmpeg
import subprocess

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "input" / "video.mp4"
MUSIC = ROOT / "assets" / "music.mp3"
OUTPUT = ROOT / "output" / "with_music.mp4"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def main() -> None:
    if not MUSIC.exists():
        print("No assets/music.mp3 found; keeping original audio.")
        return
    cmd = [FFMPEG,"-y","-i",str(INPUT),"-stream_loop","-1","-i",str(MUSIC),
           "-filter_complex","[1:a]volume=0.075,afade=t=in:st=0:d=1,afade=t=out:st=44:d=3[m];[0:a][m]amix=inputs=2:duration=first:dropout_transition=2[a]",
           "-map","0:v:0","-map","[a]","-c:v","copy","-c:a","aac","-b:a","192k",str(OUTPUT)]
    subprocess.run(cmd, check=True)
    print(f"Created: {OUTPUT}")

if __name__ == "__main__":
    main()
