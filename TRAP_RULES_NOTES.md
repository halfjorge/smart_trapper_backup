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
   BUILT 2026-10-09 behind the tick box 'File has transparent / overlay layers' (default off; Sara:
   overlay rules must not touch solid-file behaviour). With the box on:
   - MPK: overlays don't cut.
   - Engine (`overlayMode`): no traps under overlays, and overlays don't count as cover for the
     round/pullback rules.
   - Prepare Import: the overlay's COLOR__ group takes its blend mode and opacity.
   Results:
   - Mempho / Helton: solid-area change 2.2% / 3.5% → 0, colours under overlays kept 100%.
   - Easy files: identical with the box on or off.
   Not yet done: the trapper reporting the file type by itself. For now the banner warns when
   overlays are found and the box is off.
   FIXED 2026-10-14 (Baltimore / DMB Luke Martin): a layer under 100% opacity is exported with the
   opacity baked into its pixels (50% layer: most solid pixel = 128), so the alpha threshold cut it at
   70% of its artwork instead of 35%. The engine now scales such a layer back to full strength before
   the threshold (only when its pixels really look baked). Not tied to the tick box.
   MPK check on Baltimore: colours under the 50% shadows were kept 100% (MPK skipped the overlays).
4. Halo of missing pixels around a poor-quality key (artist error) should be closed, then the colour
   trapped under the key (Phish: 1-2 px paper halo). Judgment call -> detect it, report it, and make
   the fix an optional setting rather than automatic.
   BUILT 2026-10-09: 'Close key halo' checkbox (default off). It fills paper gaps of 2 px or less
   between a colour and the key with the nearest colour, then traps it under the key as normal.
   Phish: 97% of the hand-filled halo is closed, the colour matches the hand file in 99.8% of
   pixels, and nothing else changes.
   2026-10-14 (Baltimore): an overlay never fills a halo (with the overlay box on) - a 50% shadow
   filling a paper gap prints a tint where paper was meant to show. On artwork with thin paper
   strokes beside the key (Baltimore's cream feather highlights) the halo fills those strokes with
   solid colours too: leave the box off on files like that.
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

## Learned 2026-10-19 (Obey - geometric file)
- **Square traps for geometric art.** Round traps leave rounded caps that poke past corners and
  shave trap off corners next to open area. Sara prefers Round traps OFF on files like Obey.
- **Key traps follow visible colour OFF on geometric art.** The nearest-colour split under the key
  flips back and forth on diagonals (ties go to the first colour) -> scattered single-pixel dots,
  and at shallow joints it hands one colour's trap to its neighbour.
- **Joints must be mitred.** Where two colours' edge runs into the key, the boundary between their
  traps under the key continues the colours' own edge line (straight edges straight, curves along
  their end direction); no stair-step, dot, notch or bare paper at the joint. Only near the joint
  (about one trap width); further along each colour keeps its own trap.
- **Trap bands continue into the key.** Where A traps under B along their shared edge and that
  edge meets the key, A's band carries on under the key (same angle) to the key trap depth, so the
  A/B/key corner is covered (examples: light blue outline along blue stems, yellow band along the
  cream at the key).
- **Inside frame corners crisp and square** (Sara's after screenshot): no bevel on the key trap where
  the key wraps round a colour's corner. Only at real corners, not along curves.
- **Shallow joints are different** (edge runs along the key rather than into it, > 45 deg off):
  no mitre line there; keep the overlap, only clear slivers/dots. (Offline pass 2026-10-19 evening.)
- **No doubled ink.** A pixel must not be in two layers of the same colour (CLEAN + TRAP or two
  TRAPs): it does not change the separation, but shows as a dark line in Sara's multiply preview
  and reads as an error.

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
- MINIMUM OVERLAP - BUILT 2026-10-09. Round traps always keep the first ring next to the colour
  (1.4 px) even where the corner rule would cut it. Without it, a lower third colour that was as
  close as the trapping colour removed the overlap entirely: butt joins, e.g. 26k px in DMB's
  dithered gradient. Butt px are now 0 in all easy examples (TEST_RESULTS.md).
- DECIDED 2026-10-09 (Sara): Colour trap pullback default stays 0. Use 2 only by choice on
  dot-heavy files. Poster registration drift is about 5 px; the '2 px' figure was fine art only.
- PULLBACK KEEPS 1 PX - BUILT 2026-10-09. Colour trap pullback never removes the first ring next to
  the colour either (Byrne pullback 2: 20,937 butt px -> 0). Sara prefers pullback 2 visually
  around small dots.
- KEY EDGE MINIMUM - BUILT 2026-10-09. Edge bias 0-1 is treated as 1. Client colours usually stop
  1 px short of the key's soft edge, and without 1 px of growth nothing traps under the key lines.
  Byrne at Edge bias 0: colour under 40% of the key area, vs 67% now; Sara's previous after file
  has 68%.

## Open questions
- "Fingers" under the key (Sara, 2026-10-12, Helton). Thin slivers of trap where the key line narrows
  to a tip or horn: the 5 px trap grows into the tip but stops 1 px inside the key's edge (key
  pullback), so it is squeezed thin. Not visible with all layers on.
  - Counts, thin bits under 5 px wide:
    - Helton trapper about 1,500 pieces of 142 U (hand file 1,260).
    - Mempho trapper about 200-280 per colour.
    The hand files have about as many.
  - Offline what-if, app not changed: smooth the trap under the key (opening), always keeping the
    first 1.5 px next to the colour.
    - Removing bits under 3 px wide: 0.1-0.2% of trap px.
    - Removing bits under 5 px wide: 0.4-1.4% of trap px, and up to 2.5% of the trap right at
      the key edge is lost.
  - Waiting on Sara: does she want this (as an on/off option?), and at what strength?
  - BUILT 2026-10-12: Sara reviewed the Helton test file and said "let's add that".
    - Tick box "Smooth traps under the key" (job.json `smoothKeyTraps`, default off).
    - Strong strength: opening with a 5x5 ellipse, keeping the first ring next to the colour.
    - Engine `fast::smooth_key_trap`, with a unit test against a plain version.
    - Helton engine output equals the test file pixel for pixel.

- "Trap corners" under the key next to bare paper (Sara, 2026-10-12, Frankenstein ribbon at "MON").
  - Where a colour's trap under the key runs up to a paper gap in the key (the cream letter
    strokes), the trap end comes out square, right against the paper.
  - Sara hand-cut it into a bevel: rows 5/4/3/2/1 px up from the colour stop about 7/5/3/2/0 px
    short of the paper.
  - Offline what-ifs, app not changed:
    - Today's corner rule (kept if paper >= own) only nicks 2-4 px.
    - "B": kept if distance to paper >= 1.5 x distance to own colour. Matches her bevel.
      - On its own it also shortens traps across thin key lines that have paper on the far side:
        about 40% of its cut, about 2,200 px within 3 px of the colour.
      - "B corners only" fixes that: it only cuts where the paper is beside the trap, not straight
        across the key line (angle between "to own colour" and "to paper" under 135 degrees).
        It removes 13,536 of 1.49 M trap px under the key (0.91%).
  - Proposed as a tick box, default off. Waiting on Sara: test file first, or build?
  - BUILT 2026-10-12 (Sara: "I agree - let's add that as a tick box").
    - Tick box "Bevel trap corners next to paper" (job.json `bevelKeyCorners`, default off).
    - Engine: `fast::bevel_key_corners`, using exact nearest pixels within radius (own colour
      trap+2, open area 1.5x that +1).
    - Rule: cut if d_open < 1.5 x d_own AND the angle between them is under 135 degrees.
    - Applied after "Smooth traps under the key".
    - Matches an independent Python reference pixel for pixel on Frankenstein (13,646 px).

- "Key traps follow the colour you see" (Sara, 2026-10-13, Peteschaw: "it should apply to any color
  in any file where the logic is needed").
  - Problem: pairwise traps seed from the colour each one touches. Olive touches a 1-2 px blue line,
    not the key, so under the key blue ends up on top and peeks out when the key is off register.
    Same one level down: olive on top of marigold under the key next to visible marigold.
  - BUILT 2026-10-13 as a tick box (job.json `keyTrapsFollowVisible`, default off).
    - What shows in register (opaque colours only; overlays left out) -> slivers under 3 px of a
      later colour within 2 px of a lower visible colour count as that lower colour.
    - Each key px within trap px of the key edge belongs to the nearest visible class (paper or a
      colour; ties go to the lower one). Nothing within pullback + 0.5 px of visible paper.
    - The owner is added to its trap under the key; later opaque colours are removed there (clean
      layer and every trap of theirs). Applied before smoothing and bevel.
    - Engine `fast::key_edge_owner`; the clean layers are written after the owner map.
  - Tested 2026-10-13, NOT used (Sara preferred the version in her code): a visible colour keeps
    the first 1 px under the key next to itself, plus smoothing leaves the rule's pixels alone.
    It stopped olive/marigold butting the thin edges of light-blue speckles (68,569 px -> 0 on
    the 14:12 run), but olive then starts 1 px further from the blue lines. Test code and PSD
    builder: tools/peteschaw_whatif (fast_ring_test.rs, main_ring_test.rs, build_pete.py).

## Known issues to investigate later
- Results sometimes differ when art is full bleed (touches the canvas edge) vs. has a border/gutter.
  Suspect: some engine steps treat the canvas edge as "no ink" (e.g. key pullback erodes at the edge).
  (2026-10-13: key pullback no longer treats the canvas edge as open area.)
- Key trap pullback 2+ made a white ring between each colour and its own trap under the key
  (Peteschaw 14:01 run). FIXED 2026-10-13: the key used to be shrunk on every edge; now the trap is
  kept back only from open area (paper / a colour below that nothing covers), per source colour.
  Pullback 2 on Peteschaw: 2.59 M ring px filled, nothing new near paper, nothing outside the key.

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
- Peteschaw (2026-10-13, offline test only, tools/peteschaw_whatif): olive prints under blue and is
  trapped to blue, but blue (1-2 px sliver) sits between olive and the key, so under the key blue is on
  top and peeks out when the key misregisters. Same thing one level down: olive sits on top of
  marigold under the key next to visible marigold. What-if rule "the colour you see next to the key
  owns the 5 px under it" (thin slivers count as the colour they lie against, 1.5 px paper guard):
  key shifted 2 px in 8 directions, wrong colour peeking out 11.1% -> 0.6% (4 px: 11.8% -> 0.9%).
  Nothing visible changes when in register; no new ink near paper. Correction: the masks are
  already knocked out (0 px of art under the key); the ink the rule removes under the key is the
  trapper's own 1 px edge growth / heal pass and traps, not client art.
- DMB Bourbon (looked at 2026-10-13, then set aside: Sara - "a file like that can only be cleaned
  up by hand"). Client art is blurry (46% of the key's pixels soft). Hand file = every layer made
  solid at about 44% (alpha 112; the black matches to ~2,000 px of 11.9 M), then normal knockout +
  ~5 px trap; grey Multiply left under the black almost everywhere. Today's trapper leaves the soft
  key as supplied. Idea parked: a "clean up soft / blurry art" box (solid at one cut-off, key too).
