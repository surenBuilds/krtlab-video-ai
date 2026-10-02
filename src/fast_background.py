"""Fast speaker background replacement for short-form video.

Uses one GrabCut initialization and low-resolution optical flow propagation.
Designed as a fast alternative to full-resolution temporal compositing.
"""
from pathlib import Path
import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "input" / "video.mp4"
OUTPUT = ROOT / "output" / "studio_video.mp4"

def make_mask(frame):
    h, w = frame.shape[:2]
    scale = min(1.0, 720.0 / max(h, w))
    small = cv2.resize(frame, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    sh, sw = small.shape[:2]
    x1, x2 = int(sw*.12), int(sw*.88)
    y1, y2 = int(sh*.03), int(sh*.99)
    mask = np.full((sh, sw), cv2.GC_PR_BGD, np.uint8)
    mask[y1:y2, x1:x2] = cv2.GC_PR_FGD
    bgd, fgd = np.zeros((1,65),np.float64), np.zeros((1,65),np.float64)
    cv2.grabCut(small, mask, (x1,y1,x2-x1,y2-y1), bgd, fgd, 3, cv2.GC_INIT_WITH_RECT)
    m = np.where((mask==cv2.GC_FGD)|(mask==cv2.GC_PR_FGD),255,0).astype(np.uint8)
    return cv2.resize(m, (w,h), interpolation=cv2.INTER_LINEAR)

def background(h,w):
    y=np.linspace(0,1,h,dtype=np.float32)[:,None,None]
    top=np.array([238,238,238],np.float32)[None,None,:]
    bottom=np.array([198,207,216],np.float32)[None,None,:]
    return np.repeat(top*(1-y)+bottom*y,w,axis=1).astype(np.uint8)

def main():
    if not INPUT.exists(): raise SystemExit(f"Missing {INPUT}")
    cap=cv2.VideoCapture(str(INPUT))
    if not cap.isOpened(): raise SystemExit("Cannot open input video")
    fps=cap.get(cv2.CAP_PROP_FPS) or 30.0
    w,h=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    out=cv2.VideoWriter(str(OUTPUT),cv2.VideoWriter_fourcc(*"mp4v"),fps,(w,h))
    ok,prev=cap.read()
    if not ok: raise SystemExit("Cannot read first frame")
    mask=make_mask(prev)
    bg=background(h,w)
    flow_scale=min(1.0,480.0/max(h,w))
    prev_small=cv2.resize(prev,None,fx=flow_scale,fy=flow_scale,interpolation=cv2.INTER_AREA)
    yy,xx=np.mgrid[0:h,0:w].astype(np.float32)
    frame_no=0
    while True:
        soft=cv2.GaussianBlur(mask,(0,0),2).astype(np.float32)/255.0
        comp=(prev.astype(np.float32)*soft[...,None]+bg.astype(np.float32)*(1-soft[...,None])).astype(np.uint8)
        out.write(comp)
        ok,frame=cap.read()
        if not ok: break
        small=cv2.resize(frame,None,fx=flow_scale,fy=flow_scale,interpolation=cv2.INTER_AREA)
        pg=cv2.cvtColor(prev_small,cv2.COLOR_BGR2GRAY)
        cg=cv2.cvtColor(small,cv2.COLOR_BGR2GRAY)
        flow=cv2.calcOpticalFlowFarneback(pg,cg,None,.5,2,15,2,3,1.1,0)
        flow_full=cv2.resize(flow,(w,h),interpolation=cv2.INTER_LINEAR)/flow_scale
        mask=cv2.remap(mask,xx+flow_full[...,0],yy+flow_full[...,1],cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
        mask=(mask>105).astype(np.uint8)*255
        prev_small=small
        prev=frame
        frame_no+=1
        if frame_no%30==0: print(f"Processed {frame_no} frames...")
    cap.release(); out.release()
    print(f"Created: {OUTPUT}")

if __name__=="__main__": main()
