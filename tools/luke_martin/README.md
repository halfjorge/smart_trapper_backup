# DMB Luke Martin / DMB BALTIMORE FINAL (2026-10-14) - offline checks, not in the app
- The panel exports layers under 100% opacity with the opacity baked in (50% layer: max alpha 128),
  so the engine's 35% threshold cut those layers at 70% of their artwork: SHADOW PURPLE / SHADOW KEY
  kept 2.4% / 0.8% of their 35-70% soft edge (RED: 99.9%).
- Test fix (`main_opacity_fix_test.rs`): scale such layers back to full strength before the threshold
  (only when the pixels look baked). Rebuilt panel result vs client: 2.21% -> 2.16% of pixels differ;
  with anti-alias noise smoothed out 0.25% -> 0.30%. So the fix is correct in principle but is NOT
  what makes the before/after look different - most of the difference is soft edges made solid.
- luke_cmp2.py / luke_cmp3.py: rebuild the panel result from a job folder and compare with the client.
