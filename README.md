# pomo-companion

Webcam focus tracker for Pomo. Prints one JSON line per tick; the ESP32 pet reacts to it.
Frames are processed in memory only, never saved or sent anywhere.

## Setup (Fedora)
    sudo dnf install uv
    uv venv --python 3.12
    uv pip install -e ".[dev]"

## Run
    uv run python -m pomo --preview     # q quits, c recalibrates
    uv run python -m pomo --hz 2        # JSON lines only
    uv run pytest

Output: `{"ts", "focus": 0-100, "state", "reason", "window", "yaw", "pitch", "ear"}`
- state: calibrating | focused | drifting | unfocused
- reason: absent | drowsy | looking_away | slouching | bad_window | null

## How it works
- The first 5 s are calibration: look at the screen and sit normally. Head angle and posture are scored relative to that baseline.
- Score starts at 100, penalties apply while a condition holds for its duration, then an EMA (alpha 0.2) smooths it.
- All thresholds live in `FocusConfig` in `src/pomo/focus.py`.
  They can be tuned in `config/focus.yaml` instead of editing Python, e.g. `uv run python -m pomo --config path/to/yaml`.
  Only the keys present in the file override the defaults; missing keys keep their defaults.

## Assumptions / not done yet
- `mediapipe` is pinned to 0.10.21: newer releases removed the `mp.solutions` API this code uses.
  We depend on `opencv-contrib-python` (what mediapipe pulls in) so two cv2 packages don't clash.
- Posture is a proxy: face size and vertical position vs baseline (no pose model).
- EAR threshold 0.20 is a guess; tune it with `--preview` if your eyes read differently.
- Window tracking is a stub that always returns "neutral". `classify()` and `config/windows.yaml`
  are ready for a real `WindowSource` (Wayland needs a GNOME extension; X11 can use xdotool).
- No serial/WebSocket link to the ESP32 yet; stdout is the interface for now.
