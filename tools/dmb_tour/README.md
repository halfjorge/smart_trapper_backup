# DMB Fall Tour 2026 - content-aware trapping of tonal inks (offline, NOT in the engine)

File: Trap Examples\DMB Tour\DMB_Fall_tour_2026.pdf (5400 x 7200 @ 300 ppi, PSD-layout Layr block).
Layers: Background (paper 253,251,242), Orange, Light Red, Purple, Dark Red, Layer 1 (green), Black/keyline,
Layer 2 (white PDF top layer - ignored). Inks are one colour each with the TONE in the alpha (median ~56%,
grain/streaks), knocked out from each other; 96% of ink edges stop at the edge of a black line (12-17 px wide).
The key is solid line work + a stipple texture with holes (paper specks are intended - leave them).

Rules (Sara 2026-10-20): trap 5 px @300; layer order as is; layered PSD output; paper showing through untouched.
tone_trap.py: grows each ink under SOLID line work only (key 255, opening r2 removes stipple, 1 px back from
non-solid key) plus the soft anti-aliased line edge on the ink side (key >= 50%, within 2 px of the ink),
square growth, all inks at once (line split mid-way), tone/grain copied from the ink pixel mirrored across the
edge. psd_from_layers.py writes the layered PSD (CLEAN__ + TRAP__<ink>_under_Key per ink, hidden marker).
Readers: tools/obey/layr_read_full.py (PSD or PSB Layr, full channel values).

Test crop 2026-10-20: x2100-3600 y1200-2700 (5 x 5 in). Trap px 362k; 0 px outside key >= 50%; 0 doubled;
0 two inks on one pixel; in register 299 px change slightly (soft key edge); key shifted 2 px: white
slivers beside inks 80-93% fewer (3 px: 96%). Delivered: DMB Tour\DMB_Tour_test_crop_5x5in_trapped.zip

Full poster 2026-10-20 (Sara approved the crop): `python3 tone_trap.py T 0 0 5400 7200 FULL 5`.
Trap px 5.46M (Orange 1.41M, Light Red 0.97M, Purple 0.16M, Dark Red 0.86M, Layer 1 2.06M); 97% mirrored tone.
0 px under key < 50%; 0 doubled; 0 two inks per pixel; identical to the approved crop inside it.
Key shifted 2 px: white slivers beside inks 80-92% fewer (3 px: 96%). PSD read back: 13 layers, 0 mismatches.
Note: small green date type is spread 5 px into the solid black around it (hidden in register).
Delivered: Trap Examples\DMB Tour\DMB_Fall_tour_2026_trapped.zip (+ DMB_Tour_full_spotchecks.png)
