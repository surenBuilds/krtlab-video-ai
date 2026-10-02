"""One-command local KrtLab video processor.

Reads input/video.mp4 and creates output/final.mp4.
No source media is uploaded to GitHub.
"""
from pathlib import Path
import subprocess
import cv2
import numpy as np
import imageio_ffmpeg

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "input" / "video.mp4"
TEMP = ROOT / "output" / "_video_no_audio.mp4"
OUTPUT = ROOT / "output" / "final.mp4"
CAPTIONS = ROOT / "output" / "captions.ass"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

def segment(frame):
    h, w = frame.shape[:2]
    scale = min(1.0, 900.0 / max(h, w))
    small = cv2.resize(frame, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    sh, sw = small.shape[:2]
    x1, x2 = int(sw*.06), int(sw*.94)
    y1, y2 = int(sh*.005), int(sh*.995)
    mask = np.full((sh, sw), cv2.GC_PR_BGD, np.uint8)
    mask[y1:y2, x1:x2] = cv2.GC_PR_FGD
    bgd, fgd = np.zeros((1,65),np.float64), np.zeros((1,65),np.float64)
    cv2.grabCut(small, mask, (x1,y1,x2-x1,y2-y1), bgd, fgd, 5, cv2.GC_INIT_WITH_RECT)
    mask = np.where((mask==cv2.GC_FGD)|(mask==cv2.GC_PR_FGD),255,0).astype(np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5,5),np.uint8))
    return cv2.resize(mask, (w,h), interpolation=cv2.INTER_CUBIC)

def make_bg(h,w):
    y = np.linspace(0,1,h,dtype=np.float32)[:,None,None]
    top = np.array([246,244,241],np.float32)[None,None,:]
    bottom = np.array([211,220,229],np.float32)[None,None,:]
    bg = np.repeat(top*(1-y)+bottom*y,w,axis=1)
    # restrained studio light
    yy,xx = np.mgrid[0:h,0:w].astype(np.float32)
    glow = np.exp(-(((xx-w*.72)/(w*.65))**2 + ((yy-h*.22)/(h*.55))**2))*16
    bg += glow[...,None]
    return np.clip(bg,0,255).astype(np.uint8)

def render_video():
    cap=cv2.VideoCapture(str(INPUT))
    if not cap.isOpened(): raise SystemExit(f"Cannot open {INPUT}")
    fps=cap.get(cv2.CAP_PROP_FPS) or 30.0
    w=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); h=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    TEMP.parent.mkdir(parents=True,exist_ok=True)
    ff=subprocess.Popen([FFMPEG,"-y","-f","rawvideo","-pix_fmt","bgr24","-s",f"{w}x{h}","-r",str(fps),"-i","-","-an","-c:v","libx264","-preset","veryfast","-crf","17","-pix_fmt","yuv420p","-movflags","+faststart",str(TEMP)],stdin=subprocess.PIPE)
    ok,frame=cap.read()
    if not ok: raise SystemExit("Cannot read first frame")
    mask=segment(frame)
    bg=make_bg(h,w)
    flow_scale=min(1.0,600/max(h,w))
    prev_small=cv2.resize(frame,None,fx=flow_scale,fy=flow_scale,interpolation=cv2.INTER_AREA)
    yy,xx=np.mgrid[0:h,0:w].astype(np.float32)
    n=0
    while True:
        if n and n%45==0:
            mask=segment(frame)
        soft=cv2.GaussianBlur(mask,(0,0),1.4).astype(np.float32)/255.0
        # subtle contact shadow behind the speaker
        shadow=cv2.GaussianBlur((mask<80).astype(np.float32),(0,0),18)*0.10
        comp=frame.astype(np.float32)*soft[...,None]+bg.astype(np.float32)*(1-soft[...,None])
        comp*= (1-shadow[...,None]*0.08)
        ff.stdin.write(np.clip(comp,0,255).astype(np.uint8).tobytes())
        ok,new=cap.read()
        if not ok: break
        small=cv2.resize(new,None,fx=flow_scale,fy=flow_scale,interpolation=cv2.INTER_AREA)
        a=cv2.cvtColor(prev_small,cv2.COLOR_BGR2GRAY); b=cv2.cvtColor(small,cv2.COLOR_BGR2GRAY)
        flow=cv2.calcOpticalFlowFarneback(a,b,None,.5,2,15,2,3,1.1,0)
        flow=cv2.resize(flow,(w,h),interpolation=cv2.INTER_LINEAR)/flow_scale
        mask=cv2.remap(mask,xx+flow[...,0],yy+flow[...,1],cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
        mask=(mask>100).astype(np.uint8)*255
        prev_small=small; frame=new; n+=1
        if n%60==0: print(f"Processed {n} frames...")
    cap.release(); ff.stdin.close(); rc=ff.wait()
    if rc: raise SystemExit(f"Video encoder failed: {rc}")

def mux_audio():
    af = (
        "highpass=f=70,lowpass=f=14500,"
        "acompressor=threshold=-20dB:ratio=2.5:attack=8:release=100:makeup=2,"
        "loudnorm=I=-15:TP=-1.5:LRA=9"
    )
    # Keep the final deliverable social-ready at 1080x1920 and burn in the
    # Armenian captions generated from the actual speech when available.
    vf = (
        "scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,"
        "setsar=1,"
        "eq=contrast=1.025:brightness=0.008:saturation=1.035,"
        "unsharp=5:5:0.35:5:5:0"
    )
    if CAPTIONS.exists():
        subtitle = CAPTIONS.resolve().as_posix().replace(":", r"\\:")
        subtitle = subtitle.replace("'", r"\\'")
        vf += f",subtitles='{subtitle}'"
    vf += ",format=yuv420p"
    subprocess.run([
        FFMPEG, "-y",
        "-i", str(TEMP),
        "-i", str(INPUT),
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-vf", vf,
        "-af", af,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "20",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "48000",
        "-shortest",
        "-movflags", "+faststart",
        str(OUTPUT)
    ], check=True)

