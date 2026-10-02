from pathlib import Path
import subprocess
import imageio_ffmpeg
from faster_whisper import WhisperModel

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "input" / "video.mp4"
OUTPUT = ROOT / "output" / "captions.ass"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def ass_time(seconds: float) -> str:
    cs = max(0, int(round(seconds * 100)))
    h, r = divmod(cs, 360000)
    m, r = divmod(r, 6000)
    s, c = divmod(r, 100)
    return f"{h}:{m:02d}:{s:02d}.{c:02d}"


def extract_audio() -> bytes:
    cmd = [FFMPEG, "-v", "error", "-i", str(INPUT), "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"]
    return subprocess.run(cmd, check=True, stdout=subprocess.PIPE).stdout


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    raw = extract_audio()
    import numpy as np
    audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(audio, language="hy", beam_size=1, vad_filter=True, condition_on_previous_text=False)

    with OUTPUT.open("w", encoding="utf-8") as f:
        f.write("""[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Alignment, MarginL, MarginR, MarginV\nStyle: KrtLab,Arial,58,&H00FFFFFF,&H00FFFFFF,&H00151515,&H99000000,1,0,2,70,70,175\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n""")
        for seg in segments:
            text = seg.text.strip().replace("{", "(").replace("}", ")")
            if not text:
                continue
            f.write(f"Dialogue: 0,{ass_time(seg.start)},{ass_time(seg.end)},KrtLab,,0,0,0,,{text}\n")
    print(f"Created Armenian captions: {OUTPUT}")


if __name__ == "__main__":
    main()
