#!/usr/bin/env python3
"""Make the CO-WORKER ("shared") copy of the Smart Trapper panel from Sara's copy.

There is ONE panel source: UXP_Trapper/main.js (Sara's copy, in git). The shared copy is made from
it by this script, never edited by hand, so the two can't drift apart. The only difference today:

  SHOW_INDIVIDUAL_STEPS = false  -> the four individual step buttons (Manual Progressive Knockout,
                                    Run Trapper (engine only), Prepare Import Structure, Import
                                    Traps) are hidden; the one "Run Trapper" button does all four.

Usage:  python tools/dev/make_shared_copy.py [output_folder]
        (default output: dist/SmartTrapper_Shared/UXP_Trapper - not in git)

Later (Mac install stage) this script will also set the job/log folders for the other computer
and pack the plugin + helper + engine. Keep every shared-copy difference in this one script and
list it in PROJECT_NOTES.md ("Two versions").
"""
import shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "UXP_Trapper"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "dist" / "SmartTrapper_Shared" / "UXP_Trapper"
FILES = ["manifest.json", "index.html", "styles.css", "main.js", "real_bridge.py"]

# (what Sara's copy says, what the shared copy says) - each must appear exactly once
CHANGES = [
    ("const SHOW_INDIVIDUAL_STEPS = true;", "const SHOW_INDIVIDUAL_STEPS = false;"),
]

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        shutil.copy2(SRC / name, OUT / name)
    js = (OUT / "main.js").read_text(encoding="utf-8")
    for old, new in CHANGES:
        n = js.count(old)
        if n != 1:
            sys.exit(f"STOP: expected '{old}' once in main.js, found {n}. Shared copy NOT made.")
        js = js.replace(old, new)
    (OUT / "main.js").write_text(js, encoding="utf-8")
    print(f"Shared copy written to {OUT}")
    for old, new in CHANGES:
        print(f"  {old}  ->  {new}")

if __name__ == "__main__":
    main()
