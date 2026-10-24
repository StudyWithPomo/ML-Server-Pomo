"""python -m pomo [--preview] [--hz 2]"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import cv2

from .capture import Webcam
from .focus import FocusConfig, FocusEngine, FocusResult
from .preview import draw_overlay
from .signals import VisionSignals
from .vision import FaceTracker
from .windows import StubWindowSource, WindowSource


def _preview(frame, res: FocusResult, sig: VisionSignals, ear_closed: float) -> int:
    draw_overlay(frame, sig, res.state, ear_closed)
    lines = [
        f"focus {res.score}  {res.state}",
        f"reason: {res.reason}",
    ]
    if res.state == "calibrating":
        lines.append("calibrating: look at the screen")
    for i, text in enumerate(lines):
        cv2.putText(frame, text, (10, 25 + 24 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    cv2.imshow("pomo", frame)  # shown on screen only, never saved
    return cv2.waitKey(1) & 0xFF


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pomo")
    parser.add_argument("--preview", action="store_true", help="show camera with overlay (q quit, c recalibrate)")
    parser.add_argument("--hz", type=float, default=2.0, help="JSON lines per second")
    parser.add_argument("--camera", type=int, default=0, help="camera index")
    parser.add_argument(
        "--config",
        type=str,
        default="config/focus.yaml",
        help="YAML file overriding FocusConfig thresholds (default config/focus.yaml)",
    )
    args = parser.parse_args(argv)

    if os.path.isfile(args.config):
        engine = FocusEngine(FocusConfig.from_yaml(args.config))
    else:
        engine = FocusEngine()
    windows: WindowSource = StubWindowSource()
    period = 1.0 / args.hz
    next_emit = 0.0
    misses = 0

    try:
        with Webcam(args.camera) as cam, FaceTracker() as tracker:
            while True:
                frame = cam.read()
                if frame is None:
                    misses += 1
                    if misses >= 50:
                        print("error: camera stopped returning frames", file=sys.stderr)
                        return 1
                    continue
                misses = 0

                now = time.monotonic()
                sig = tracker.process(frame)
                category = windows.category()
                res = engine.update(sig, category, now)

                if now >= next_emit:
                    next_emit = now + period
                    print(
                        json.dumps(
                            {
                                "ts": round(time.time(), 2),
                                "focus": res.score,
                                "state": res.state,
                                "reason": res.reason,
                                "window": category,
                                "yaw": round(sig.yaw_deg, 1),
                                "pitch": round(sig.pitch_deg, 1),
                                "ear": round(sig.ear, 3),
                            }
                        ),
                        flush=True,
                    )

                if args.preview:
                    key = _preview(frame, res, sig, engine.cfg.ear_closed)
                    if key == ord("q"):
                        break
                    if key == ord("c"):
                        engine.recalibrate()
    except KeyboardInterrupt:
        pass
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    finally:
        if args.preview:
            cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
