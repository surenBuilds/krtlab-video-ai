from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "motion_plan.txt"

# Conservative motion language for a founder/product talking-head video.
# Timing is generated from the actual caption segments by the renderer later.
PLAN = [
    "0-1000ms: subtle opening scale-in",
    "keyword moments: small lower-third keyword card",
    "problem/solution transitions: short directional slide",
    "important product terms: minimal floating icon/shape",
    "section changes: 8-frame soft zoom transition",
    "final 1500ms: subtle scale-out and clean hold",
]

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text("\n".join(PLAN), encoding="utf-8")
print(f"Created motion plan: {OUTPUT}")
