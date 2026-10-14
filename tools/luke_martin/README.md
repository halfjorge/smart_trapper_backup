# DMB Luke Martin / DMB BALTIMORE FINAL (2026-10-14) - offline checks, not in the app
- The panel exports layers under 100% opacity with the opacity baked in (50% layer: max alpha 128),
  so the engine's 35% threshold cut those layers at 70% of their artwork: SHADOW PURPLE / SHADOW KEY
  kept 2.4% / 0.8% of their 35-70% soft edge (RED: 99.9%).
- Test fix (`main_opacity_fix_test.rs`): scale such layers back to full strength before the threshold
  (only when the pixels look baked). Rebuilt panel result vs client: 2.21% -> 2.16% of pixels differ;
  with anti-alias noise smoothed out 0.25% -> 0.30%. So the fix is correct in principle but is NOT
  what makes the before/after look different - most of the difference is soft edges made solid.
- luke_cmp2.py / luke_cmp3.py: rebuild the panel result from a job folder and compare with the client.

## Close key halo + overlays (2026-10-14)
after.pdf (Photoshop PDF) holds the layered file: its 'Layr' block was rebuilt into a PSB and read -
every colour matches the engine output exactly. The purple on cream paper came from Close key halo
(2 px): thin cream paper strokes next to the key were filled with the nearest colour, often
SHADOW PURPLE (50%). Test (`main_opacity_and_halo_test.rs`): overlays never fill halos + opacity fix.
SHADOW PURPLE on client paper 24,008 -> 6,569 px (rest = edge bitmapping). Other 5 jobs identical.
MPK check: colours under the shadow overlays were kept 100% (MPK skipped overlays).
