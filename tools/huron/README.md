# Huron (grays / gradients) - offline test, 2026-10-13 (not in the app)
Sara: gradients in files like this are halftoned or dithered by the RIP; pink = halftone + ink in clear base (overlay).
- `gray_trap.py <ex dir> <work dir>`: per layer solid / soft edge / GRAY (in-between values filling a patch);
  knockout where gray parts and overlays don't cut; real engine (Sara's settings) with grays counted as ink;
  CLEAN keeps gray values, traps carry the nearest own value, no trap under a gray part of a colour above
  (outside the key).
- `gray_eval.py`: blend-aware compare with the client file. Today 16.3% of the print changes; test 2.9%
  (soft edges 2.8%, solid 0.14%). Colours under a gray of a colour above kept 99.8-100%.
- `build_psd.py`: layered PSD (Prepare Import layout) - Huron_grays_trapped.psd.

## DMB Ocean (2026-10-14) - same scripts, PAPER_LAYERS=0,1 (white + manilla paper)
Visible change vs client 1.37% (soft edges 1.30%, solid 0.07%); colours under grays kept 99.7-100%.
Vs Sara's hand after: the only real difference is that the hand file did not knock colours out under
SOLID colours above (rule 7) - 91-99% of the hand-only ink is hidden under solid colours above.

## "Cut back" (Sara 2026-10-14, after the Ocean butt problem) - cutback.py
Knock-out-then-regrow left 14% of Ocean's key edge butting (client 1.0%, hand 0.9%): it removed
client ink that was correctly under the key and didn't grow it all back. Cut back instead:
client layers untouched; ink removed only > 5 px inside the key or a SOLID colour above; big-gray
layers (>50% gradient) left alone; overlays don't cover; empty key px within 5 px of a visible
colour get filled (client butts). Ocean: butting key edge 0.51%, visible change 0.01%.
