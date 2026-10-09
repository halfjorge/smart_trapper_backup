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
