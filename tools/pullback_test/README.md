# Key trap pullback from the paper side only (test, 2026-10-13 - not in Sara's code)
Today: key_allow = key shrunk by the pullback on EVERY edge. The colour only reaches 1 px into the key
(edge bias minimum), so at pullback 2+ a ring opens between each colour and its own trap under the key
(Sara's white lines, Peteschaw 14:01 run).
Test (`main_pullopen_test.rs`, env KEY_PULL_OPEN=1): per source colour, the trap is kept back only from
open area - paper or an uncovered lower colour (the round/bevel "showing" mask) - by the pullback.
Peteschaw 14:12 settings, follow-visible off: pullback 2 gaps 2.79 M -> 0.75 M px (= baseline, trap
ends deep in the key); 2.59 M px filled, 0 added near paper, 0 change outside the key.
Pullback 1: 4,105 px added, nothing near paper.
