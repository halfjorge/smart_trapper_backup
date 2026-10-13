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
