# Recipe: DMB Fall Tour 2026 poster

**What it is:** every colour is a single ink whose tone and grain sit in the layer's transparency, over a black key with line work and stipple. The paper shows through on purpose.

**Approved files:**
- Offline full poster: `DMB_Fall_tour_2026_trapped.zip` (sent in chat, 134 MB)
- Test crop: `Trap Examples\DMB Tour\DMB_Tour_test_crop_5x5in_trapped.zip`
- Panel run with Tonal inks, 2026-10-26 17-56. It matches the offline poster exactly.

## The easy way now: in the app
Use the **Tonal / grayscale** type from `presets.json`: Tonal inks ON, at 300 ppi with trap 5 px.
- Round, smooth, bevel and overlay are ignored in this mode.
- **Do not run Cut Top Key.** The key must not cut the inks. The panel now blocks this.
- Ignore the white top layer from the PDF.

## How it was first made offline (Claude, `tools/dmb_tour/` in the repo)
**Sara's rules (2026-10-20):**
- Trap 5 px at 300 ppi.
- Keep the layer order as it is.
- Output a layered PSD.
- Leave paper showing through untouched.
- Leave the key's stipple specks alone.

**How it works:**
- Each ink grows only under SOLID key line work: key at 100%, with the stipple removed and stopping 1 px back from non-solid key.
- Each ink also grows into the soft line edge on its own side: key at 50% or more, within 2 px of the ink.
- Growth is square, with all inks growing at the same time, so where two inks meet in a line they split midway.
- The trap's tone is copied from the ink pixel mirrored across the edge, so the grain carries on.

Commands:
```
python3 tools/obey/layr_read_full.py ...        # read PSD/PSB layers with full tone values
python3 tone_trap.py T 2100 1200 3600 2700 CROP 5   # 5x5 in test crop
python3 tone_trap.py T 0 0 5400 7200 FULL 5         # full poster (5400x7200 @300)
python3 psd_from_layers.py ...                       # layered PSD: CLEAN__<ink> + TRAP__<ink>_under_Key
```

**Checks it passed:**
- 0 px of trap sit under key below 50%.
- 0 doubled ink.
- 0 pixels have two inks.
- With the key shifted 2 px, white slivers were 80–92% fewer.

Note: the small green date type spreads 5 px into the solid black around it. This is hidden when in register.
