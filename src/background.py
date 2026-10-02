"""Background replacement helper.

Uses OpenCV GrabCut to create a soft foreground mask around a centered
speaker. It is deliberately conservative: preserving the speaker is more
important than removing every background pixel. The generated mask can be
composited over a clean studio color/background by the render pipeline.
"""
from pathlib import Path
import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "input" / "video.mp4"
MASK_DIR = ROOT / "output" / "masks"


def make_preview_mask() -> None:
    MASK_DIR.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(INPUT))
    ok, frame = cap.read()
    cap.release()
    if not ok:
        raise RuntimeError("Could not read input video")

    h, w = frame.shape[:2]
    mask = np.full((h, w), cv2.GC_PR_BGD, np.uint8)
    # Conservative central probable-foreground region for a talking-head shot.
    x1, x2 = int(w * .18), int(w * .82)
    y1, y2 = int(h * .08), int(h * .98)
    mask[y1:y2, x1:x2] = cv2.GC_PR_FGD
    bgd = np.zeros((1, 65), np.float64)
    fgd = np.zeros((1, 65), np.float64)
    cv2.grabCut(frame, mask, (x1, y1, x2-x1, y2-y1), bgd, fgd, 5, cv2.GC_INIT_WITH_RECT)
    out = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    out = cv2.GaussianBlur(out, (0, 0), 1.5)
    cv2.imwrite(str(MASK_DIR / "first_frame_mask.png"), out)
    print(f"Created preview mask: {MASK_DIR / 'first_frame_mask.png'}")


if __name__ == "__main__":
    make_preview_mask()
