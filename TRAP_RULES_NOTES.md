# Smart Trapper - trapping rules learned from examples
Running notes from before/after examples in Desktop\Trap Examples. No code changed yet:
collect examples first, agree on rules, then build and test against all examples at once.

## House conventions (from Sara)
- Top layer is always the key, whatever its name. Bottom layer is always a blank paper layer.
- Colour order is fixed by hand before running the trapper; the trapper never reorders.
- Standard trap: 5 px at 300 ppi.
- Prints waterbased and UV inks on uncoated and coated PAPER (posters). No white underbases.
- Grayscale layers are trapped as GRAY and only halftoned/dithered later (RIP at screen burning).
  The trapper must not flatten intentional gray to solid ink - only clean fuzz on solid-ink layers.
- If a before/after pair differs in a way that isn't explained, ASK before deciding the engine needs a change.
- Press-ready files are set up 2-up (two posters side by side on one sheet). The "after" examples were
  cropped back to one poster for comparison, so differences at the canvas edges (trimmed strips,
  canvas size/offset changes like Phish's +150 px border) are cropping artifacts: ignore them.

## File types (Sara's categories)
1. EASY - all layers 100% solid fills, Normal blend. (DMB, Methane, Phish)
2. MEDIUM - solid Normal layers plus solid overlay (Multiply/Darken) layers. (Mempho, Helton)
3. HARD - a mix of: solid layers, solid layers with some gray/gradient, solid overlays, and overlays
   with some gray/gradient. (Ocean)
Overlays and gray must be handled differently from solid layers in BOTH trapping and knockouts.
The trapper could report which type a file is when you run it.

## Rules
1. Rule #1: with all layers on, the trapped file should look like the client file.
   Exceptions are deliberate fixes, e.g. cleaning fuzzy/grey pixels into solid ink (screens need
   pure bitmap) and closing artist-error halos (see 4).
2. Each colour is knocked out under the OPAQUE (Normal, 100%) layers above it, keeping a trap
   overlap. Measured: Mempho ~5 px round under the key; DMB 6-7 px (squarish); Methane ~6 px.
   Hand-made "5 px" traps typically come out ~6 px.
3. Colours under a MULTIPLY / transparent layer are NOT knocked out and NOT trapped under it - the
   overprint is part of the art (yellow over blue = green). Multiply layers overlapping each other
   outside the key are kept too. Multiply layers ARE knocked out under the opaque key (5 px trap).
   (Mempho; today's trapper would visibly change ~3% of that print.)
   DARKEN counts as an overlay too (Helton). Treat any non-Normal blend mode or <100% opacity as an
   overlay - confirm with Sara if a new blend mode shows up.
4. Halo of missing pixels around a poor-quality key (artist error) should be closed, then the colour
   trapped under the key (Phish: 1-2 px paper halo). Judgment call -> detect it, report it, and make
   the fix an optional setting rather than automatic.
   BUILT 2026-10-09: 'Close key halo' checkbox (default off). It fills paper gaps of 2 px or less
   between a colour and the key with the nearest colour, then traps it under the key as normal.
   Phish: 97% of the hand-filled halo is closed, the colour matches the hand file in 99.8% of
   pixels, and nothing else changes.
5. Don't fill solid under every line. Trapping x px from each side is fine, even if the two sides
   meet in the middle under a thin line.

6. Cleanup order (Sara's intent for Alpha threshold + Edge bias): (a) threshold every layer to solid
   ink to remove fuzz; (b) grow edges back out to close hairlines the threshold created - between ANY
   two colours or a colour and the key - but never onto open paper; (c) then trap.
   CONFIRMED: Edge bias closes ONLY hairline gaps - ones created by the threshold step, or hairline
   gaps/halos already in the client art (Phish). It never extends colour onto open paper.
   Today's engine only grows edges where the key covers, so hairlines between two colours stay open
   and get no trap. Fix this; it also covers the Phish key-halo case (rule 4) with the same setting.
   DECIDED 2026-10-09 (Sara): the colour-to-colour hairline fix is ON HOLD. It can't tell threshold
   damage from thin paper lines or dots the artist put in on purpose. Only the key halo (rule 4)
   was built, as its own on/off option.
   Note: manual work rounds soft edges up from ~12-15% opacity; panel threshold 90 (~35%) is stricter.
   Test lower thresholds (~30-40) against the examples.
   Thresholds vary by job: Methane colours ~12-15%; Helton colours exactly 50%, Helton key ~30%
   (key edges came out slightly bolder). So the threshold stays a per-job setting.

7. GRAY layers (Ocean: smooth gradients stored as layer transparency):
   - Gray values are never changed where they show (100% untouched).
   - Under the solid key they are cut back with a 5 px trap, and the trap band keeps the ORIGINAL gray
     values (not made solid).
   - Where a layer above is itself semi-transparent (gray), layers below are kept under it, like an
     overlay - because they show through.
   - So per pixel: only fully solid ink above should cut what's below.
   - Gradient-heavy jobs (Ocean: 4 of 6 layers gray): colours are NOT cut under each other, only under
     the key - cutting would mean more gray traps, which are tedious by hand.
   - Ocean's orange 'Layer 1' is an artifact of manual trapping: ignore.
   - Running the panel's Manual Progressive Knockout on Ocean visibly changed ~17% of the print
     (octopus head lighter, crab tones shifted): it cut gray layers out from under semi-transparent
     layers they show through. Gray/overlay-heavy files must NOT be progressively knocked out.

8. DECIDED: Run Trapper never cuts anything out. All cutting is the operator's choice, made with the
   panel buttons BEFORE trapping (Manual Progressive Knockout, Cut Top Key From Colors).
   Run Trapper only cleans edges (rule 6) and adds traps. (Knockout suits 'sheet' files like DMB;
   it's wrong for gradient files like Ocean.)

9. 'Backing' / flat fills (BTS): in areas of fine detail or hatching, a colour is backed with a solid
   fill of another colour underneath. Reasons: misregistration shows the fill colour instead of bare
   paper; fewer tiny traps; and ink printed over ink has a different sheen than ink over paper, so
   lots of small trapped bits look patchy - a solid backing evens the sheen. JUDGMENT CALL: left out
   of the trapper for now (possible future panel tool: select area + colour -> fill underneath).

10. NO BUTT REGISTRATION (Sara): wherever two inks meet and the key does not cover the join, the
    finished file must have an overlap (trap). Butt joins are only acceptable under the key.
    Known sources today: hairline gaps (Phish), three-colour corners, key trap pullback (under key = OK).
    Example (Byrne, Sara 2026-10-07): RED trapped under small GREY dots near the calendar reached the dots'
    paper edge, so red and grey butted there. BUILT: 'Colour trap pullback (px)' (default 2) keeps traps that
    many px inside any edge of the covering colour that is open (paper or a colour below the source).
    Byrne: 53k trap pixels touched open edges before, 0 after; ~2% of trap pixels removed, none visible.

## Planned panel tools
- 'Clean Colors' - BUILT (panel button, 2026-10-06). Optional, before trapping: refills each layer
  with its majority colour (Fill with Preserve Transparency), keeping shape and soft edges. Every
  visible layer except the paper, key included; skips overlay layers (non-Normal / <100% opacity or
  fill), gray layers (>35% of ink pixels semi-transparent) and layers whose main colour covers <50%.
  One history step. Phish Jackson check: most off-colour pixels sit in the semi-transparent patches
  (WATER BLUE: ~1% of solid pixels off, ~6.5% soft pixels; LIGHT GREEN: solid pixels clean, ~10.7% soft).
  So Clean Colors fixes the colour; Alpha threshold then decides whether those soft patches stay.

- File check banner - BUILT 2026-10-07 (Sara asked after running Vista at 600 ppi, which halved the traps): when a document is opened, the panel should check colour mode
  and resolution. If it is not RGB and 300 ppi, show that in red at the top of the panel (e.g. "CMYK -
  convert to RGB?" / "600 ppi - downscale to 300?") so the user can fix it before running anything.

- Round traps - BUILT 2026-10-07 (checkbox, default on). Disk growth (true 5 px every direction) plus
  Sara's corner rule: a trap pixel under another colour is kept only if it is at least as close to its
  own colour as to any open area (paper / colour below the source). Ends traps flush with the end of the
  lower shape instead of wrapping round it. Not applied under the key. Byrne: -10% trap px, 0 open-edge
  contacts, composite unchanged. Verified against an exact reference (1 px difference in 4.6 M).

- DEFAULT SETUP (Sara, 2026-10-07): Round traps ON, Colour trap pullback 0. Byrne check with this setup:
  nothing visible with all layers on; 6,871 trap px still touch an open edge (mostly 1 px specks at small
  gray dots; 27 spots over 10 px) vs 53,063 with old square traps and 0 with pullback 2. Revisit
  pullback 2 if those specks ever show on press.

## Open questions

## Known issues to investigate later
- Results sometimes differ when art is full bleed (touches the canvas edge) vs. has a border/gutter.
  Suspect: some engine steps treat the canvas edge as "no ink" (e.g. key pullback erodes at the edge).

## Examples so far
- DMB: colours supplied as full "sheets"; knocked out with 6-7 px overlap. Today's trapper (after
  Manual Progressive Knockout) is a near-subset of the manual result; trap 6 matches best.
- Phish: key line work has a 1-2 px paper halo; manual filled it and trapped ~5 px under the key.
  Today's trapper leaves the halo (would print as a thin shirt-coloured outline).
- Mempho: two Multiply overlay layers; see rule 3.
- DMB Methane: client colours mostly pre-knocked out except a big hatch-under-shack sheet. Manual result:
  knockout + ~6 px trap under every opaque layer above (same as DMB). Stack re-ordered by hand
  (orange to bottom, hatch/skyu swapped) - a manual pre-step, not a trapper job. Looks the same as the
  client file except soft edges rounded up to solid ink.
- Helton: '2985 U' is a DARKEN overlay - colours under it are kept (no knockout), knocked out under the
  opaque key with a clean 5 px trap (same as Mempho). Key: soft pixels from ~30% up made solid.
  Bottom checker row of the key trimmed ~110 px from the bottom edge (confirmed: 2-up layout/crop).
  The overlay's preview colour was changed (35,151,207 -> 57,150,171): display only, masks unaffected (confirmed).
- DMB Bourbon: EXCLUDED from rules (Sara unsure of its discrepancies). Overlay rule held; but the grey
  Multiply overlay was left as a full sheet under the black key instead of cut with a 5 px trap.
- DMB Ocean: gray/gradient layers - see rule 7 and open questions.
- BTS (type 1, easy): client file already knocked out. Manual work FILLED lower colours under upper
  ones: normal ~5 px traps plus big flat fills (see open questions). Orange moved down the stack.
