"""High-quality fast background replacement for the current portrait source."""
from pathlib import Path
import cv2
import numpy as np
import imageio_ffmpeg
import subprocess

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "input" / "video.mp4"
OUTPUT = ROOT / "output" / "studio_video.mp4"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

def make_mask(frame):
    h, w = frame.shape[:2]
    scale = min(1.0, 900.0 / max(h, w))
    small = cv2.resize(frame, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    sh, sw = small.shape[:2]
    x1, x2 = int(sw * 0.08), int(sw * 0.92)
    y1, y2 = int(sh * 0.01), int(sh * 0.995)
    mask = np.full((sh, sw), cv2.GC_PR_BGD, np.uint8)
    mask[y1:y2, x1:x2] = cv2.GC_PR_FGD
    bgd = np.zeros((1, 65), np.float64)
    fgd = np.zeros((1, 65), np.float64)
    cv2.grabCut(small, mask, (x1, y1, x2-x1, y2-y1), bgd, fgd, 5, cv2.GC_INIT_WITH_RECT)
    m = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5,5), np.uint8))
    return cv2.resize(m, (w, h), interpolation=cv2.INTER_CUBIC)

def background(h, w):
    y = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    top = np.array([242, 242, 242], np.float32)[None, None, :]
    bottom = np.array([205, 214, 224], np.float32)[None, None, :]
    return np.repeat(top * (1-y) + bottom * y, w, axis=1).astype(np.uint8)

def main():
    if not INPUT.exists():
        raise SystemExit(f"Missing {INPUT}")
    cap = cv2.VideoCapture(str(INPUT))
    if not cap.isOpened():
        raise SystemExit("Cannot open input video")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    ff = subprocess.Popen([
        FFMPEG, "-y", "-f", "rawvideo", "-pix_fmt", "bgr24",
        "-s", f"{w}x{h}", "-r", f"{fps}", "-i", "-",
        "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(OUTPUT)
    ], stdin=subprocess.PIPE)

    ok, prev = cap.read()
    if not ok:
        raise SystemExit("Cannot read first frame")
    mask = make_mask(prev)
    bg = background(h, w)
    flow_scale = min(1.0, 600.0 / max(h, w))
    prev_small = cv2.resize(prev, None, fx=flow_scale, fy=flow_scale, interpolation=cv2.INTER_AREA)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)

    frame_no = 0
    while True:
        soft = cv2.GaussianBlur(mask, (0, 0), 1.5).astype(np.float32) / 255.0
        comp = (prev.astype(np.float32) * soft[..., None] + bg.astype(np.float32) * (1-soft[..., None])).astype(np.uint8)
        ff.stdin.write(comp.tobytes())

        ok, frame = cap.read()
        if not ok:
            break
        small = cv2.resize(frame, None, fx=flow_scale, fy=flow_scale, interpolation=cv2.INTER_AREA)
        pg = cv2.cvtColor(prev_small, cv2.COLOR_BGR2GRAY)
        cg = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        flow = cv2.calcOpticalFlowFarneback(pg, cg, None, .5, 2, 15, 2, 3, 1.1, 0)
        flow_full = cv2.resize(flow, (w, h), interpolation=cv2.INTER_LINEAR) / flow_scale
        mask = cv2.remap(mask, xx + flow_full[...,0], yy + flow_full[...,1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        mask = (mask > 100).astype(np.uint8) * 255
        prev_small = small
        prev = frame
        frame_no += 1
        if frame_no % 60 == 0:
            print(f"Processed {frame_no} frames...")

    cap.release()
    ff.stdin.close()
    ff.wait()
    if ff.returncode != 0:
        raise SystemExit(f"FFmpeg failed with code {ff.returncode}")
    print(f"Created: {OUTPUT}")

if __name__ == "__main__":
    main()
