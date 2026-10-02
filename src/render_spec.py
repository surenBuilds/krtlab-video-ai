from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "input" / "video.mp4"
OUTPUT = ROOT / "output" / "final.mp4"

EDIT_SPEC = {
    "format": "1080x1920",
    "background": {
        "mode": "tracked_speaker_replacement",
        "style": "minimal_modern_office_or_neutral_studio",
        "color": "soft_neutral",
        "edge_quality": "natural",
        "motion_tracking": True,
    },
    "speaker": {
        "keep_original_motion": True,
        "subtle_punch_ins": True,
        "color_correction": True,
    },
    "audio": {
        "speech_cleanup": True,
        "speech_target_lufs": -15,
        "music": "subtle_instrumental",
        "music_ducking": True,
    },
    "captions": {
        "language": "hy",
        "phrase_level": True,
        "mobile_safe": True,
        "keyword_emphasis": True,
    },
    "motion_graphics": {
        "enabled": True,
        "style": "clean_tech_education",
        "speech_driven": True,
        "avoid_template_feel": True,
    },
}

if not INPUT.exists():
    raise SystemExit(f"Source video not found: {INPUT}")

print("KrtLab production specification loaded")
print(f"Input: {INPUT}")
print(f"Output: {OUTPUT}")
print("Background: tracked natural speaker replacement")
print("Captions: Armenian phrase-level")
print("Graphics: speech-driven KrtLab style")
