# Smart Trapper - test results

Newest first. Every result here comes from running the real engine on the Trap Examples with
`tools/example_checks/easy_check.py`.

## How to read the tables

**Settings used:** Sara's own. Preflight cleanup on, alpha threshold 89, edge bias 1, key trap
pullback 1, colour trap pullback 0, round traps on, trap width 5 px.

**Steps run:** Manual Progressive Knockout, then the engine. The result is all `CLEAN__` layers plus
all traps.

**The columns:**
- **Visible change vs client:** pixels outside the key that look different from the client file
  with all layers on. It should be 0 apart from deliberate fixes.
  - *paper→ink*: soft edges rounded up to solid, or halo fill.
  - *ink→paper*: colour lost.
  - *colour swap*: a different colour shows.
- **Butt px:** pixels where two colours meet outside the key with no overlap. This breaks rule 10;
  the target is 0.
- **Trap at open edge:** hidden trap pixels touching paper or a lower colour. These are where a trap
  could peek out on a misregistered sheet (the Byrne case). Smaller is better, but this trades off
  against butt px.
- **Trap width:** p50 / p90 distance a colour runs under the colours above it, in px. The key isn't
  included.
- **Hand:** Sara's hand-trapped after file, measured the same way.

## 2026-10-26 - Agreed preset values in the picker (panel only)
file_type_test.js updated to the agreed values: 28 checks PASS on Sara's copy and the co-worker's copy
(new check: Sara's MMJ run-2 settings open as "Overlay / Multiply layers", values unchanged). job.json
from each type == the same boxes ticked by hand. Run Trapper suite (18 situations + individual buttons):
same results as before on both copies.

## 2026-10-26 - "What kind of file is this?" picker (panel only, stand-in Photoshop)
Tool: `tools/ui_tests/file_type_test.js` (after run_trapper_button_test.js). 27 checks, all PASS, on
Sara's copy and on the co-worker's copy:
- Fresh install starts on Standard poster with Standard values.
- Each type fills in exactly its values, is saved and survives Reload; bridge URL / folders untouched.
- Changing boxes after picking: type kept, note lists the changes ("Trap width 6 (usual 5)"), values
  saved; "Put back" restores the type; clicking a setting's name also updates the note.
- Custom changes nothing.
- Saved settings never replaced: Obey-style settings show as Geometric with values unchanged; alpha 89
  shows as Custom with values unchanged; very old saved settings keep newer boxes off.
- job.json from picking each type == job.json from ticking the same boxes by hand (no fileType in it).
  Geometric: trapShape square, smooth on, bevel off, follow-visible off.
Run Trapper suite (18 situations + individual buttons): same results as before.

## 2026-10-26 - One-button "Run Trapper" (panel only, stand-in Photoshop)
Tool: `tools/ui_tests/run_trapper_button_test.js` - the real panel in Chromium, Photoshop stood in,
REAL helper (real_bridge.py) + REAL engine (built from the cloud kit) on small test jobs. Run on Sara's
copy and on the co-worker's copy (made by make_shared_copy.py): identical results.

| Situation | Steps that ran | Result |
|---|---|---|
| Normal file | knockout, engine, prepare, import | FINISHED (engine made 2 traps) |
| Tonal inks ticked | engine, prepare, import | FINISHED, knockout skipped |
| Overlay layer, box ticked | all four | FINISHED |
| Overlay layer, box NOT ticked | none | STOPPED before anything changed |
| No document / only 2 layers / already trapped | none | STOPPED before anything changed |
| Helper not running | none | STOPPED before anything changed (knockout NOT done) |
| 600 ppi / CMYK / Trap width 0 | none | STOPPED before anything changed |
| Knockout error | knockout | STOPPED at step 1, says knockout may be partly done |
| Engine error (broken job) | knockout, engine | STOPPED at step 2 ("Engine run failed") |
| Engine makes 0 traps | knockout, engine | STOPPED at step 2 with the 0-traps help |
| A colour gets no CLEAN layer | all four | FINISHED - WITH WARNINGS, names the colour |
| 1 of 3 trap layers fails to import | all four | FINISHED - WITH WARNINGS |
| A step throws unexpectedly | up to the failing step | STOPPED, lists what was already done |
| Double-click while running | all four, once | one run only |

Individual buttons (Sara's copy): each still calls only its own step and shows its usual
"... complete." pop-up; engine-only run made 2 traps. Code check: the only lines removed from main.js
are 8 bare `return;` lines (now `return { ok, reason }`) and two button labels/positions.
Not tested here: real Photoshop (Sara: Reload and run a file you know).

## 2026-10-26 - "Tonal inks (grayscale layers)" in the engine + panel (new option, default off)
| Check | Result |
|---|---|
| DMB Tour job (tonalInks on) vs approved offline poster | identical: 0 of 5,460,779 trap px, CLEAN tones identical |
| DMB Nash job, box off: old engine vs new engine | IDENTICAL (22 files) |
| cargo test (vendored kit, offline) | 7 passed |
| Engine time, DMB Tour 5400 x 7200 | 15 s |

## 2026-10-20 - DMB Fall Tour 2026: content-aware trapping of tonal inks (offline)
Inks carry tone in alpha; trap 5 px @300 under SOLID key line work only (not stipple/specks), tone mirrored from
the ink edge, lines split mid-way. Test crop approved by Sara, then full poster (tools/dmb_tour):
| Check | Result |
|---|---|
| Trap pixels | 5.46M |
| Under key < 50% / doubled / two inks per pixel | 0 / 0 / 0 |
| Key shifted 2 px: white slivers beside inks | 80-92% fewer (3 px: 96%) |
| Full run vs approved crop | identical |
| PSD read back | 13 layers, 0 mismatches |

## 2026-10-20 - Obey v2 (blue line) + bleed (offline)
| Check | v2 | v2 + bleed (fixed) |
|---|---|---|
| Joints mitred / gentle | 79 / 9 | - |
| Separation changed outside the key | 0 px | - |
| Doubled ink | 0 | 0 in bleed |
| Inside-trim pixels changed vs v2 | - | 0 (except 4 bottom rows: 5,465 paper px filled) |
| Bare paper in bleed | - | 0 |
| PSD read back | 45 layers, 0 px mismatch | 9900 x 12300, 600 ppi |
Sara: v2 "looks good"; first bleed had a white bottom line + obvious flower seam -> fixed (bleed_pattern_fix.py).

## 2026-10-19 evening - Obey square-trap run + joint-mitre pass (offline, NOT in the engine)
- Source: Trap Examples\Obey\Obey_roundtraps_off.pdf (Sara's panel run: 600 ppi 9600x12000 in the
  PDF, trapPx 5 @300 -> 12 px under key, round OFF, follow-visible OFF). Reference: Sara's before/after
  screenshots of the top-left frame (hand-mitred joints, square inside corners, dots gone).
- tools/obey: layr_read.py (no psd-tools needed) -> mitre.py -> mitre_check.py -> psd_write.py -> psd_verify.py.

| Check | Result |
|---|---|
| Key joints found / mitred / gentle (shallow, curved, short) | 88 / 60 / 28 |
| Pixels changed (all under the key) | 11,354 |
| Separation changed outside the key, any colour | 0 px |
| Doubled ink (same colour in 2 layers): trapper output -> fixed | 1,846 -> 0 |
| Bare key pixels inside the 12 px trap band | 122,713 -> 120,959 |
| Square corners filled (bevel removed) | 561 px at 134 corners |
| Trap lost away from joints | loose dots only (~30 px, covered by another colour) |
| PSD read back (independent reader) | 45 layers, 600 ppi, 0 px mismatch |

Delivered: Obey_roundtraps_off_MITRED_600.zip + Obey_mitre_before_after.png. Waiting for Sara.

## 2026-10-19 - Obey (geometric, flat + key), offline joint-fix and bleed what-ifs
- Source: Trap Examples\Obey\Sepped_GM-SHEP-AUTO TRAP.pdf (trapper output, 600 ppi 9600x12000,
  trapPx 10, round ON, follow-visible ON) and Sara's partly hand-cleaned _CLEANED.pdf (11 joint spots).
- Joint fix v1: 59 key joints mitred, rest despeckled; printed top colour identical to the trapper
  output at every pixel (0 px). Sara found doubled-ink lines and cut-off light blue trap in the
  flower area -> fixed offline (no doubling, 45 deg rule, re-split radius ~1.5 x trap); after the
  fix the flower area matches the trapper's own split; pin-hole gaps under the key filled (~200 px).
  NOT re-delivered.
- Bleed 0.25 in: every layer through one map; Key and a trap layer checked pixel-exact vs the map.
- Sara's own re-run 2026-10-19 15:33 (300 ppi, trapPx 5, round OFF, follow-visible OFF): better;
  remaining hand work = mitred joints at the key. Next test = mitre pass on that run.

## 2026-10-14 - 50% opacity fix + halo never fills with an overlay (fixes, always on)

Baltimore (DMB BALTIMORE FINAL, Sara's 10:06 job, her exact settings incl. halo 2 px):
| Check | Result |
|---|---|
| Current engine vs Sara's run | identical |
| Sara's after.pdf (layers rebuilt) vs engine output | identical, every colour |
| SHADOW PURPLE / SHADOW KEY soft edge (35-70%) kept, before fix | 2.4% / 0.8% (RED 99.9%) |
| SHADOW PURPLE on client paper | 24,008 -> 6,569 px |
| SHADOW KEY on client paper | 3,054 -> 2,158 px |
| Layer 1 on client paper (halo, solid colour - unchanged by design) | 27,535 -> 27,742 px |
| Other 5 job folders | identical |
Scripts: `tools/luke_martin`.

## 2026-10-13 - Key trap pullback from open area only (fix, always on)

| Job (as run) | Pixels added under the key (per colour, summed) | Outside the key | New ink near paper |
|---|---|---|---|
| PETESCHAW 11:52 (pullback 1) | 83,311 (58 px of new ink overall) | 0 | 0 |
| Untitled-1 | 310 | 0 | 0 |
| Frankenstein | 3,477 | 0 | 0 |
| before.psd 12-24 | 2,043 | 0 | 0 |
| Helton | 2,280 | 0 | 0 |
| PETESCHAW 14:12 settings at pullback 2, follow box off | 2,586,364 (the white ring) | 0 | 0 |

Engine identical to the offline test version Sara checked (Peteschaw_pullback2_fixed.psd).
Scripts: `tools/pullback_test`.

## 2026-10-13 - "Key traps follow the colour you see" (new option, default off)

Engine run on copies of all 5 finished job folders. Test: move the key 2 px (and 4 px) in 8
directions; where the key used to be, does the colour seen next to that spot in register show?
(Spots in the key pullback next to paper and the canvas edge are left out.)
Script: `tools/peteschaw_whatif/own_eval.py`.

| Job | Colours (overlays) | Box off vs current engine | Wrong colour, key 2 px off: today -> box on | 4 px off | Change outside the key | New ink near paper | Run time off -> on |
|---|---|---|---|---|---|---|---|
| PETESCHAW | 3 (0) | identical | 12.0% -> 0.1% | 11.9% -> 0.4% | 0 px | 0 | 22 -> 27 s |
| Untitled-1 | 3 (1) | identical | 6.4% -> 0.0% | 6.6% -> 0.0% | 0 px | 0 | 11 -> 15 s |
| Untitled-2 (Frankenstein) | 6 (0) | identical | 1.8% -> 0.0% | 2.1% -> 0.1% | 0 px | 0 | 25 -> 36 s |
| before.psd 12-24 | 3 (2) | identical | 0.0% -> 0.0% | 0.0% -> 0.0% | 0 px | 0 | 4 -> 5 s |
| before.psd 12-28 (Helton) | 3 (1) | identical | 0.3% -> 0.0% | 0.3% -> 0.0% | 0 px | 0 | 10 -> 13 s |

- Frankenstein with smoothing + bevel also on: 1.6% -> 0.0%, no change outside the key.
- Tried letting smoothing keep the pixels this rule gives a colour: Peteschaw 0.6% -> 0.5% (old
  metric). Not worth it, smoothing left as is.
- cargo test (fast.rs): 7/7 (new test: olive sees through a thin blue line to the key).

## 2026-10-12 - "Bevel trap corners next to paper" (new option, default off)

Engine run on a copy of Sara's Frankenstein job `Untitled-2__UXP__2026-10-12T15-59-41-372Z`:

| Check | Result |
|---|---|
| Box off vs Sara's real run (`--compare-jobs`) | identical |
| Box on vs independent Python reference (`tools/frank_whatif/bevel_ref.py`) | 0 px different, every colour |
| Trap px removed under the key | green1 20 · hotpink 23 · green2 484 · violet 1,591 · green3 531 · purple 10,997 |
| Traps not under the key | unchanged |
| Run time in the cloud | 25.5 s off, 29.8 s on |
| cargo test | 6/6 |

## 2026-10-12 - "Smooth traps under the key" (new option, default off)

Engine run on a copy of Sara's Helton job `before.psd__UXP__2026-10-12T12-28-48-291Z`:

| Check | Result |
|---|---|
| Box off vs Sara's real run (`--compare-jobs`) | identical |
| Box on, trap px removed under the key | 142 U 23,736 · 2985 U 24,838 · warm red 1,297 (of 3.65 M) |
| Box on vs the Helton test file Sara reviewed | 0 px different, colour by colour |
| Traps not under the key (142 / 2985 under warm red) | unchanged |
| cargo test | 6/6 (new: smooth_key_trap_matches_plain_version) |

## 2026-10-12 - Helton, Sara's real Photoshop run with the overlay box ticked

Job folder `before.psd__UXP__2026-10-12T12-28-48-291Z`. Settings are the same as the Mempho run.
The engine logged "overlay mode ON: 1 overlay colour: 2985 U (darken)".

| Check | Result |
|---|---|
| Visible change vs client, solid areas | **0** (soft-edge zone 3.30%, the same as the simulation; hand file 5.7%) |
| 142 U kept under 2985 U Darken (knockout and final) | 100% / 100% |
| Colours under the key after knockout | 0 |
| Trap under the key, p50/p90/p99 | 3.0-3.6 / 6.1-6.4 / 7.1-7.2 px (hand file 3.0 / 5.0 / 5.4) |
| Trap layers | 5: three under the key, plus 142 U and 2985 U under warm red (solid). None under 2985 U |
| Prepare Import | COLOR__2985 U set to Darken 100% (status log) |

**MEDIUM files (rule 3) pass on both examples in real Photoshop runs.**

## 2026-10-12 - Mempho, Sara's real Photoshop run with the overlay box ticked

Job folder `before.psd__UXP__2026-10-12T12-24-30-173Z`. Settings: overlay box on, threshold 90,
edge bias 0 (engine uses 1), key pullback 1, colour pullback 0, round, trap 5. Engine was rebuilt
at 12:15 and logged "overlay mode ON: 2 overlay colours".

Steps: Manual Progressive Knockout, Run Trapper, Prepare Import, Import Traps.

| Check | Result |
|---|---|
| Visible change vs client, solid areas | **0** (soft-edge zone 0.78%, the same as the simulation) |
| 2985 U kept under match / under 115 u (knockout and final) | 100% / 100% |
| match kept under 115 u | 95.2% after knockout, 99.3% final (6k px, soft edges) |
| Colours under the key after knockout | 0 (cut, as rule 3 says) |
| Overlay trap under the key, p50/p90/p99 | 3.0-3.6 / 6.1-6.4 / 7.1 px |
| Trap layers | 3, all under the key |
| Prepare Import | COLOR__match and COLOR__115 u set to Multiply 100% (status log) |

The number boxes took edits: colour pullback went from 2 back to 0 after the focus fix.

## 2026-10-09 - MEDIUM files with the overlay tick box (rule 3 built)

`medium_check.py <job> --overlay` simulates the box being ticked: MPK skips overlay cutters, the
engine gets `overlayMode: true`, and the overlay keeps its blend mode on import (the COLOR__ group
takes it).

| File | Run | Visible change, solid areas | Total incl. soft edges | Colour kept under overlay | Overlay under key p50/p90/p99 px |
|---|---|---|---|---|---|
| Mempho | hand | 0.09% | 1.0% | 99.6%, 100% | 2.8 / 5.0 / 5.7 |
| | box ON, MPK + engine | **0** (was 2.18%) | 0.78% | 100%, 100% (match under 115 u 99.3%) | 3.0 / 6.1 / 7.1 |
| | box ON, engine only | 0 (was 0.12%) | 0.77% | 100%, 100% | 6.0 / 19 / 51 (not cut) |
| Helton | hand | 0.05% | 5.7% | 100% | 3.0 / 5.0 / 5.4 |
| | box ON, MPK + engine | **0** (was 3.45%) | 3.3% | 100% | 3.6 / 6.4 / 7.2 |
| | box ON, engine only | 0 (was 0.04%) | 2.6% | 100% | 7.1 / 19 / 53 (not cut) |

Trap layers made with the box on and MPK:
- Mempho: only the three under the key (none under match or 115 u).
- Helton: under the key, plus 142 U and 2985 U under warm red (solid).

**Nothing changes for solid files.** Checked with `--compare-jobs`, old engine vs new, on traps
and clean masks:

| File | Box off | Box on |
|---|---|---|
| DMB | identical | identical |
| Phish | identical | identical |
| Mempho | identical | n/a |

Each was checked with and without MPK. The panel changes only run when the box is ticked. The one
exception is the red banner hint, which only shows text.

## 2026-10-09 - MEDIUM files baseline (Mempho, Helton): today's trapper, before any rule-3 change

Measured with the new `tools/example_checks/medium_check.py`. It compares blend-aware composites
(Multiply = below × colour / 255, Darken = min, opacity respected), each layer drawn in its single ink
colour. Visible change means any channel differs by more than 12 levels. It's split into the
**soft-edge zone** (within 2 px of soft client pixels, where rounding up to solid is a deliberate fix)
and **solid areas** (real changes). Sara's settings, engine as of commit e53875f (5/5 cargo tests pass).

"Blend kept/lost" covers Prepare Import. By the code, `CLEAN__` and `TRAP__` layers are made with no
blend mode inside a pass-through group, so an overlay would come back Normal ("lost"). That still
needs confirming in Photoshop's layer panel. Lost figures use white paper: the cream paper layer
alone makes Darken differ from Normal on open paper (Helton 12.1% vs 3.6%).

| File | Run | Visible change, solid areas | Total incl. soft edges | Colour kept under overlay (rule 3) | Overlay under key p50/p90/p99 px |
|---|---|---|---|---|---|
| Mempho | hand | **0.09%** | 1.0% | 2985 under match 99.6%, under 115 u 100% | 2.8 / 5.0 / 5.7 (match) |
| | MPK + engine, blend kept | **2.18%** | 4.0% | 68.2%, **2.2%** | 3.0 / 6.1 / 7.1 |
| | MPK + engine, blend lost | 2.45% | 5.0% | same | same |
| | engine only (no MPK), blend kept | 0.12% | 1.3% | 100%, 100% | 6.0 / 19 / 51 (not cut) |
| | engine only, blend lost | 2.45% | 5.0% | 100%, 100% | same |
| Helton | hand | **0.05%** | 5.7% | 142 under 2985 100% | 3.0 / 5.0 / 5.4 |
| | MPK + engine, blend kept | **3.45%** | 8.8% | **12.2%** | 3.6 / 6.4 / 7.2 |
| | MPK + engine, blend lost | 3.60% | 9.5% | same | same |
| | engine only, blend kept | 0.04% | 2.8% | 100% | 7.1 / 19 / 53 (not cut) |
| | engine only, blend lost | 3.60% | 8.8% | 100% | same |

(Helton's soft-edge totals are large because the key has 3.5 M soft pixels; the hand file also
rounds those up.)

**Findings**
- **MPK breaks rule 3.** It cuts colours out from under the overlays:
  - Mempho: 2985 U loses 440k px under match and 115 u (2.2% of the print).
  - Helton: 142 U loses 1.42 M px under 2985 U Darken (3.5% of the print).
  - This confirms the "about 3%". All of the solid-area change comes from that one cause.
- **The engine traps under overlays.** It makes `TRAP__x_under_<overlay>` layers: Mempho 2985 under
  match / 115 u, match under 115 u; Helton 142 under 2985.
  - Under a Multiply/Darken layer those traps show as a darker 5 px rim. Without MPK that's
    Mempho 0.12% (mostly match under 115 u, 23k px) and Helton 0.04% (16k px).
- **Without MPK, overlays are not cut under the key at all** (p90 19 px, p99 about 52 px). The 5 px
  overlay trap under the key currently only happens through MPK. MPK gives about 6 px (p90),
  close to the hand file's 5.
- **If Prepare Import does drop the blend mode,** that alone changes about 2.5% (Mempho) or
  3.6% (Helton) of the print, whatever the engine does.
- The hand files match rule 3: colours kept 100% under the overlays, and overlays cut under the
  key at about 5 px.

## 2026-10-09 - Byrne: colour under the key, and pullback

Measured on Sara's own Byrne run masks (job folder before.tif__UXP__2026-10-09T13-41-38-280Z).

**Colour under key** is the share of the key (DARK BLUE) area that has a colour underneath it. With
the key hidden, the rest shows as paper.

| Engine / settings | Colour under key | Butt px |
|---|---|---|
| Sara's previous after file (Oct 7, square traps) | 67.6% | - |
| Edge bias 0, trap 6, pullback 2 (Sara's runs today, old engine) | 40.0% | 20,937 |
| Edge bias 1, trap 5, pullback 0, round | 63.8% | 0 |
| Edge bias 1, trap 5, pullback 0, square | 67.6% | - |
| New engine, Edge bias 0, trap 6, pullback 2 | 66.9% | 0 |

**Fixes:**
- Edge bias minimum of 1.
- Pullback keeps 1 px of overlap.

The small remaining difference from the reference comes from round versus square traps at corners.

## 2026-10-09 - easy files re-check (engine with Close key halo + 1 px minimum overlap)

| File | Run | paper→ink | ink→paper | colour swap | butt px | trap at open edge | trap width p50/p90 |
|---|---|---|---|---|---|---|---|
| Phish | hand | 364,003 | 50 | 345 | 2 | 0 | 1.0 / 3.0 |
| | trapper | 112,344 | 0 | 0 | **0** | 42 | 1.4 / 3.2 |
| | trapper + key halo | 354,044 | 0 | 0 | **0** | 31 | 2.0 / 4.0 |
| DMB | hand | 22 | 0 | 0 | 0 | 224,429 | 2.2 / 6.4 |
| | trapper | 0 | 0 | 0 | **0** (was 26,221) | 170,219 | 2.0 / 4.4 |
| DMB Methane | hand | 55,808 | 1,321 | 67,184 | 1,777 | 2,743 | 2.8 / 5.8 |
| | trapper | 1,810 | 0 | 0 | **0** (was 388) | 1,099 | 2.2 / 5.0 |
| Byrne | trapper (no hand file) | 0 | 0 | 0 | **0** (was 1,684) | 8,449 (was 6,771) | 2.2 / 4.4 |
| BTS | hand | 53 | 730 | 202,427 | 22,771 | 82,206 | 5.0 / 25.0 |
| | trapper | 0 | 0 | 0 | **0** (was 8,832) | 40,926 | 2.0 / 4.2 |
| Phish Jackson | trapper (no hand file) | 14,972 | 0 | 0 | 0 | 27,145 | 2.2 / 5.0 |

**Findings**

- **Rule #1 holds everywhere.** The trapper never removes ink and never changes which colour shows.
  - The only visible changes are paper→ink:
    - soft key edges healed by edge bias 1 (Phish, Phish Jackson)
    - soft edges rounded to solid (Methane)
  - In the hand files, the colour swaps come from Sara reordering layers by hand (Methane, BTS),
    and from BTS's backing fills.
- **Butt joins: fixed.** The round-trap corner rule cut the trap wherever a third, lower colour was
  as close as the trapping colour. That produced butts, mostly single pixels:
  - in DMB's diffusion-dithered gradient (26k px)
  - in fine detail in BTS, Byrne and Methane

  Round traps now always keep the first 1.4 px ring next to the colour, which gives 0 butts in every
  file. The cost is a little more trap at open edges, e.g. Byrne 6,771 → 8,449 px, all 1 px deep.
- **Close key halo is only right for Phish-type files.** Results with it on:
  - Phish: matches the hand file. 97% of the halo is closed, and 100% of the filled pixels have
    ink in the hand file too.
  - Phish Jackson: it would fill 230k px. This is likely the same kind of halo, but there's no hand
    file to confirm.
  - BTS: it would fill 16,797 px that Sara left as paper on purpose (0% match).
  - Methane: 18,992 px, only 24% where the hand file has ink.
  - Byrne: 3,070 px. DMB: 41 px.

  **Keep it off by default and only tick it for halo files.**
- **Trap width:**
  - The trapper's 5 px round trap measures about 4.4-5 px at p90 under other colours.
  - Sara's hand traps are wider on DMB (about 6.4) and narrower on Phish (about 3).
  - BTS hand p90 of 25 px is the backing fills (rule 9, left out on purpose).
- **Ink use:**
  - DMB: trapper 36.0 M ink px vs hand 38.4 M. The hand file left more of the "sheets" under the
    other colours.
  - BTS: 32.8 M vs 41.2 M, the difference being the backing fills.

**Not covered**
- Vista: only the final separated file is in the folder, so there's no before/after pair.
- Smashing Pumpkins: only the client file and Claude's press file.
- DMB Bourbon: excluded by Sara.
- Medium and hard files (overlays, gray): next step.
