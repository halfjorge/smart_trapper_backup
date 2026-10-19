# Obey: "joints" where two colours' traps meet (offline what-if, NOT in the engine yet)

Sara's cleaned file (Sepped_GM-SHEP-AUTO TRAP_CLEANED.pdf) changed only hidden trap pixels at 11 spots,
all where two colours meet each other and then run into the key ("joints").

Problems in the trapper output (engine rule: each trap pixel goes to the NEAREST colour, fast.rs key_edge_owner):
1. On a slanted edge the split between the two colours turns straight up/down under the key -> blocky step,
   often a notch / a few bare pixels.
2. Scattered dots: where both colours are exactly the same distance away (diagonals), ties always go to the
   colour listed first, so every other pixel flips -> dotted pattern (e.g. yellow dots in cream at x2994 y667).

What-if rule (Sara chose "follow the edge where it meets the key", 2026-10-19, under ALL colours not just key):
- For every colour T, every joint between two colours A and B that both trap under T:
  - fit the A|B edge direction from the last ~12 px before T (sub-pixel midpoints) and carry that line
    through the trap zone under T (straight edges come out straight, curves follow their end direction);
  - if that line would run along T's edge instead of into it, keep the trapper's split and only remove
    stray pixels (3x3 majority, CLEAN edge pixels included) - this is what removes the dots.
- Only pixels inside T (covered by T on press) move between A and B. What prints visibly does not change.

Files: joint_fix.py (rule), build_obey_psd.py (layered PSD; hidden magenta layer shows every changed pixel).
Obey numbers: 59 key joints straightened, 17 key + 20 colour joints despeckled; ~17k px changed.

Pipeline: pdf2psb.py (Photoshop PDF -> raw Layr block) -> bin2psb.py (wrap as PSB for psd-tools)
-> obey_diff.py (per-layer packed masks a_/b_ + diff report) -> obey_labels.py (labels.npy)
-> joint_fix.py -> build_obey_psd.py. obey_sheet.py / obey_proto.py make the before/after pictures.
Check: printed (top-most) colour identical to the trapper output at every pixel (0 px differ).
Delivered to Sara: Trap Examples\Obey\Obey_joint_fix_test.zip (test) and Obey_joint_fix_600.zip (2026-10-19).
build_obey_original.py: copies the trapper file record-for-record (low memory), swaps the fixed CLEAN__/TRAP__ pixels, drops the white PDF layer, writes .psd at 600 ppi.
