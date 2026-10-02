# Professional editor workflow

1. Keep `input/video.mp4` local; never commit source media.
2. Run `python src/pro_editor.py` for the clean 9:16 speech render.
3. The production layer should add a tracked speaker mask, neutral office/studio background, phrase-level Armenian captions, subtle topic-driven motion graphics, and low-volume ducked music.
4. Export to `output/final.mp4`.

The editor prioritizes natural speaker edges and movement over aggressive AI background effects.
