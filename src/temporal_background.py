"""Temporal speaker mask + clean studio background compositor."""
from pathlib import Path
import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "input" / "video.mp4"
OUTPUT = ROOT / "output" / "studio_video.mp4"

def make_mask(frame):
    h, w = frame.shape[:2]
    mask = np.full((h, w), cv2.GC_PR_BGD, np.uint8)
    x1, x2 = int(w * .16), int(w * .84)
    y1, y2 = int(h * .05), int(h * .99)
    mask[y1:y2, x1:x2] = cv2.GC_PR_FGD
    bgd = np.zeros((1, 65), np.float64)
    fgd = np.zeros((1, 65), np.float64)
    cv2.grabCut(frame, mask, (x1, y1, x2-x1, y2-y1), bgd, fgd, 5, cv2.GC_INIT_WITH_RECT)
    return np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)

def background(h, w):
    y = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    top = np.array([238, 238, 238], np.float32)[None, None, :]
    bottom = np.array([198, 207, 216], np.float32)[None, None, :]
    return np.repeat((top * (1-y) + bottom*y), w, axis=1).astype(np.uint8)

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
    out = cv2.VideoWriter(str(OUTPUT), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    ok, prev = cap.read()
    if not ok:
        raise SystemExit("Cannot read first frame")
    mask = make_mask(prev)
    prev_gray = cv2.cvtColor(prev, cv2.COLOR_BGR2GRAY)
    bg = background(h, w)
    while True:
        frame = prev
        soft = cv2.GaussianBlur(mask, (0, 0), 2.0).astype(np.float32) / 255.0
        alpha = soft[..., None]
        comp = (frame.astype(np.float32)*alpha + bg.astype(np.float32)*(1-alpha)).astype(np.uint8)
        out.write(comp)
        ok, frame = cap.read()
        if not ok:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        flow = cv2.calcOpticalFlowFarneback(prev_gray, gray, None, .5, 3, 21, 3, 5, 1.2, 0)
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        mask = cv2.remap(mask, xx + flow[...,0], yy + flow[...,1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        mask = (mask > 110).astype(np.uint8) * 255
        prev_gray = gray
        prev = frame
    cap.release()
    out.release()
    print(f"Created: {OUTPUT}")

if __name__ == "__main__":
    main()
