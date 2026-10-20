# Quadratic functions: teaching video (10:21)

A narrated, chalkboard-style explainer for high-school quadratic functions: what a does, vertex form, completing the square, axis of symmetry, roots and the discriminant, two worked examples, three practice problems and a recap. 1280x720, 30 fps. Built 2026-10-19.

**Watch / download:** the finished `quadratic-functions.mp4` is attached to the [v1.0 release](../../releases/tag/v1.0) (not committed to git).

## How it is made
Everything is drawn frame by frame in Python (Pillow + numpy) by a small custom animation engine; the voice-over is Microsoft Edge neural TTS (`edge-tts`, voice en-US-AndrewNeural); ffmpeg encodes the result.

## How to render
```
python3 -m venv venv && . venv/bin/activate
pip install numpy pillow edge-tts
# needs ffmpeg and DejaVu fonts (/usr/share/fonts/truetype/dejavu/)
python3 scenes.py render                 # -> quadratic-functions.mp4 (+ audio.wav, cache/)
python3 scenes.py frames 12.5 300        # -> frames/t*.png stills at given seconds
```
TTS clips are cached in `cache/`; `audio.wav`, `cache/`, `frames/` and the mp4 are git-ignored.

## Files
- `engine.py`: drawing primitives, easing, TTS + audio helpers.
- `scenes.py`: the 12 scenes, narration lines and the renderer / ffmpeg pipeline.
- `script.md`: the narration script with timestamps.
- `quadratic-functions.srt`: subtitles.
