# Peteschaw what-if: "the colour you see next to the key owns the trap under it"

Offline test only (2026-10-13). Nothing in the panel or engine uses this yet.

Run from a folder holding a copy of a job folder (here `pete_asrun`):

    python ownership_rule.py pete_asrun . guard     # writes pete_owner_g.npz
    python misregister_test.py pete_asrun 2          # key shifted 2 px, 8 directions: NOW vs NEW RULE
    python misregister_view.py pete_asrun out.png 2 2 2905,4667 2874,4690
    python before_after_view.py pete_asrun out.png 2905,4667 2874,4690

Rule: under the key, within 5 px of the key edge, each spot belongs to the nearest colour that
shows when everything is in register (slivers under 3 px thick count as the colour they lie against).
That colour is put on top there (added if missing, higher colours removed). Nothing changes within
1.5 px of paper (pullback guard). Results are in TRAP_RULES_NOTES.md (Peteschaw).

## 2026-10-13 - "1 px ring" test (not in Sara's code yet)
Sara's 14:12 run showed olive/marigold butting the thin edges of light-blue speckles (pink in her
screenshot): the sliver rule treated those thin edges as the colour behind them. Test version
(`fast_ring_test.rs` / `main_ring_test.rs`, smoothing protection was behind OWN_PROTECT=1 in the test build):
- a visible colour keeps the first ring (<= 1.42 px) under the key next to itself;
- smoothing does not remove pixels the rule gave a colour.
Results on the 14:12 job: butting blue 68,569 -> 0; olive behind a thin blue line on top in the
2-5 px band: 88.6% (now) -> 61.7% (ring only) -> 97.7% (ring + smoothing protection).
Test PSD: `build_pete.py` -> Peteschaw_key_traps_follow_v2.psd.
