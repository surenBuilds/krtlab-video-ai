from pathlib import Path
import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "input" / "video.mp4"
OUTPUT = ROOT / "output" / "studio_preview.mp4"


def composite() -> None:
    cap = cv2.VideoCapture(str(INPUT))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open {INPUT}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(OUTPUT), fourcc, fps, (w, h))

    # Neutral studio background. A smooth gradient avoids a visibly artificial flat plate.
    yy = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    top = np.array([235, 235, 235], np.float32)
    bottom = np.array([205, 205, 205], np.float32)
    bg = np.tile((top * (1 - yy) + bottom * yy)[:, None, :], (1, w, 1))
    bg = np.clip(bg, 0, 255).astype(np.uint8)

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        # Conservative central mask. Production segmentation can replace this function
        # without changing the rest of the pipeline.
        m = np.zeros((h, w), np.uint8)
        cv2.ellipse(m, (w//2, int(h*.47)), (int(w*.30), int(h*.48)), 0, 0, 360, 255, -1)
        m = cv2.GaussianBlur(m, (0, 0), max(3, int(min(w,h)*.012)))
        alpha = (m.astype(np.float32) / 255.0)[..., None]
        comp = (frame.astype(np.float32) * alpha + bg.astype(np.float32) * (1-alpha)).astype(np.uint8)
        out.write(comp)

    cap.release()
    out.release()
    print(f"Created: {OUTPUT}")


if __name__ == "__main__":
    composite()
