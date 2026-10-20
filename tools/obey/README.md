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

Bleed (2026-10-19): bleed.py builds one position map (0.25in = 150 px at 600 ppi) from all visible ink layers:
straight colour edges are carried outward at their own angle; runs of curvy pattern edges are mirrored (spans start
and end on a colour edge, and never mirror a neighbouring line); edge lines where paper shows through (Obey bottom:
4 rows) are rebuilt. add_bleed_psd.py pushes every layer (hidden too) and the flattened preview through the same map.
Delivered: Trap Examples\Obey\Obey_joint_fix_600_bleed.zip (9900 x 12300 px, 16.5 x 20.5 in @ 600 ppi).

2026-10-19 afternoon: joint_fix.py tightened (45 deg entry rule, re-split radius ~1.5 x trap, no
trap growth via closing), tidy.py (no doubled ink + pin-hole fill under key). DRAFTS, UNTESTED:
specks.py (stray dots under key), extend_bands.py (carry A-under-B trap bands into the key).
Next: Sara's own square-trap re-run (300 ppi, trapPx 5, round off, follow-visible off) + a
joint-mitre pass on top of it. See PROJECT_NOTES.md section 0.

## 2026-10-19 evening: joint-mitre pass on Sara's square-trap run (Obey_roundtraps_off.pdf)
No psd-tools needed (not installable in the cloud workspace):
1. `python3 pdf2psb.py Obey_roundtraps_off.pdf new` -> new.bin (raw Layr block; the PDF holds 9600x12000)
2. `python3 layr_read.py new.bin L 9600 12000` -> L/layers.json + L/m_<i>.npy (packed masks)
3. `python3 labels_from_layers.py L` -> labels.npy (top-most art colour per pixel, Key = 7)
4. `python3 mitre.py L F` -> F/m_<i>.npy for changed layers, F/joint_log.json, F/zones.npy
   (straight joints: split along the A|B edge line within 2 trap widths; shallow/curved: keep overlap,
   clear slivers < 5 px; square real corners; loose dots; no doubled ink). Trap depth D=12 at 600 ppi.
5. `python3 mitre_check.py L F` -> must say ALL CHECKS PASS
6. F/changed.npy (union of changed pixels) -> hidden magenta layer
7. `python3 psd_write.py new.bin L F out.psd 600` then `python3 psd_verify.py out.psd L F`
render.py / charmap.py: multiply-preview crops and per-pixel layer maps for checking joints.
Delivered: Trap Examples\Obey\Obey_roundtraps_off_MITRED_600.zip

## 2026-10-20: v2 "blue line" rule (Sara's choice)
At a mitred joint the LOWER colour's trap band (TRAP__low_under_up) now carries on under the key at the
same angle to the key trap depth; the upper colour still ends on its own edge, so they overlap under the
key by the band width, as above it. Mitre cutoff lowered from 45 deg to 25 deg (MIN_ANGLE) between the
colour edge and the key edge. Result: 79 of 88 joints mitred with band carried on; all checks pass.
Delivered for review: Trap Examples\Obey\Obey_roundtraps_off_MITRED_v2_600.zip (+ Obey_v2_blue_line_compare.png).

## 2026-10-20: bleed on v2 (canvas untouched)
B2/ = j_<name>.npy links to the v2 visible ink masks + vis_layers.json -> `python3 bleed.py B2 150` (map;
insets t0 b4 l0 r0) -> `python3 bleed_psd.py v2.psd B2/bleed_map.npz out.psd`: every layer and the flattened
image go through the map, then the ORIGINAL canvas is pasted back exactly (unlike add_bleed_psd.py, which
rebuilt the 4 bottom rows). Checks: 0 px different inside the 9600x12000 canvas (all layers, all channels);
bleed has 0 bare paper, 0 doubled ink. Known: v2 itself has a 4-row paper sliver (1,370 px, x2145-6404) at the
bottom trim edge, left as-is per Sara. Delivered: Trap Examples\Obey\Obey_roundtraps_off_MITRED_v2_600_bleed.zip

## 2026-10-20: bleed fix (white bottom line + pattern seam)
`python3 bleed_pattern_fix.py B2/bleed_map.npz labels.npy B2/bleed_map_fixed.npz` then
`python3 bleed_psd.py v2.psd B2/bleed_map_fixed.npz out.psd --fill-inset` and
`python3 bleed_check.py v2.psd out.psd L 4`. In busy light-blue/blue texture zones (widened over any solid
shape they touch): solid shapes carried by their own edges only, texture mirrored at the trim, plain blue
background where a mirror would reflect a solid shape. --fill-inset rebuilds the 4-row paper sliver.
Delivered: Trap Examples\Obey\Obey_roundtraps_off_MITRED_v2_600_bleed_fixed.zip
