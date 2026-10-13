# Huron (grays / gradients) - offline test, 2026-10-13 (not in the app)
Sara: gradients in files like this are halftoned or dithered by the RIP; pink = halftone + ink in clear base (overlay).
- `gray_trap.py <ex dir> <work dir>`: per layer solid / soft edge / GRAY (in-between values filling a patch);
  knockout where gray parts and overlays don't cut; real engine (Sara's settings) with grays counted as ink;
  CLEAN keeps gray values, traps carry the nearest own value, no trap under a gray part of a colour above
  (outside the key).
- `gray_eval.py`: blend-aware compare with the client file. Today 16.3% of the print changes; test 2.9%
  (soft edges 2.8%, solid 0.14%). Colours under a gray of a colour above kept 99.8-100%.
- `build_psd.py`: layered PSD (Prepare Import layout) - Huron_grays_trapped.psd.
