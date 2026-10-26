# Recipe: Obey poster (GM-SHEP), October 2026

**What it is:** a geometric, hard-edged poster with a black key line. It was trapped in the panel, then Claude fixed the joints at the key offline and added bleed.
**Final approved file:** `Trap Examples\Obey\Obey_roundtraps_off_MITRED_v2_600.zip`
**With bleed:** `Trap Examples\Obey\Obey_roundtraps_off_MITRED_v2_600_bleed_fixed.zip` (delivered; no verdict recorded yet)

## Step 1: panel run (Sara)
Use the **Geometric / flat shapes** type from `presets.json`:
- Round traps OFF
- Key traps follow the colour you see OFF
- Smooth ON and Bevel ON
- 300 ppi, trap 5 px
- Preflight ON, alpha 90, edge bias 1, key pullback 1, colour pullback 0

Save the trapped file as a Photoshop PDF. Sara's file was `Obey_roundtraps_off.pdf`.

## Step 2: joint mitre, offline (Claude, `tools/obey/` in the repo)
**What it fixes:** where two colours meet and run into the key, the app splits the trap in a blocky, dotted way.

**The rule Sara chose (the "blue line" rule):**
- At each joint, the LOWER colour's trap band carries on under the key at the same angle.
- The UPPER colour stops on its own edge line.
- A joint is mitred only when the colour edge meets the key at 25° or more.
- Shallow, curved or short joints keep the app's overlap, and slivers under 5 px are cleared.
- Real corners are squared.
- Loose dots are removed.
- No doubled ink is allowed.

Trap depth under the key is 12 px at 600 ppi. Only hidden pixels change: what prints on top stays the same.

Commands:
```
python3 pdf2psb.py Obey_roundtraps_off.pdf new          # PDF -> raw layer block (9600x12000)
python3 layr_read.py new.bin L 9600 12000               # layers -> L/
python3 labels_from_layers.py L                         # top colour per pixel (Key = 7)
python3 mitre.py L F                                    # the fix -> F/   (MIN_ANGLE = 25)
python3 mitre_check.py L F                              # must say ALL CHECKS PASS
python3 psd_write.py new.bin L F out.psd 600
python3 psd_verify.py out.psd L F
```
Result: 79 of 88 joints were mitred, and all checks passed. A hidden magenta layer shows every pixel that changed.

## Step 3: bleed, 0.25 in (Claude)
**Rules:**
- The original canvas is left exactly as it was.
- Solid shapes carry on at their own angle.
- Busy texture is mirrored at the trim.
- Plain background is used where a mirror would reflect a solid shape.
- The 4-row paper sliver at the bottom is filled.

Commands:
```
python3 bleed.py B2 150                                  # position map, 150 px = 0.25 in @600
python3 bleed_pattern_fix.py B2/bleed_map.npz labels.npy B2/bleed_map_fixed.npz
python3 bleed_psd.py v2.psd B2/bleed_map_fixed.npz out.psd --fill-inset
python3 bleed_check.py v2.psd out.psd L 4
```
Output canvas: 9900 x 12300 px (16.5 x 20.5 in at 600 ppi).

## What went wrong along the way (don't repeat)
- **Round traps / follow-visible on this art (12-10 run):** caps poked past corners and dots appeared at diagonals. REJECTED.
- **Mitre v1:** a yellow "finger" at a shallow joint, and the light-blue band stopped dead at the key. Fixed in v2.
- **Bleed v1:** a white line at the bottom trim and a visible pattern seam. Fixed in bleed_fixed.

## Status in the app
Steps 2 and 3 are NOT in the app yet. They are parked as "promote into the app" and need Sara's OK first.
