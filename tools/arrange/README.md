# Arrange a messy client PSD into the standard "before" structure (Claude, 2026-10-12)

First used on Wilco (`Trap Examples\wilco`): about 80 layers in 18 groups, with layer masks, a
group mask, clipped layers, hidden layers and a "DELETE ME" white fill. Cloud-only scripts, not
part of the app yet. Paths and the "wilco_" file prefix are hard-coded, so adjust them before reuse.

1. `list_layer_colors.py <psd>`: the main colours of every layer. Use it to pick the inks.
2. `arrange_pass1.py <psd> <out prefix> '<inks json>' '<alias json>'`
   - inks: name -> hex, and must include "paper". Aliases: near-identical hexes to merge into an ink.
   - Walks the stack bottom to top, honouring visibility, layer masks, group masks and clipping.
     Hidden layers and "DELETE ME" are skipped.
   - Each layer is one ink: the main ink of its solid pixels. A layer that mixes inks gets a
     WARNING.
   - It replays the original order. A solid paint of an ink wipes every darker ink under it at that
     spot, because in the new darkest-on-top order those inks would otherwise cover it. Faint tints
     painted on top are kept.
3. `arrange_pass2.py <dir>`: stacks the inks by lightness (CIE L*, darkest = top = key) and
   compares the new stack with the original look.
4. `arrange_write.py <dir> <src psd> <out psd>`: writes the PSD.
   - Layer order: paper at the bottom, then the inks lightest to darkest. All layers Normal.
   - Real transparency, 300 ppi copied from the source.

Wilco result:
- 6 inks plus green paper (the green Background is treated as paper; Sara to confirm).
- Visible change vs the original: 0.045% of solid areas. 13.7k px of that is the #362710 brown
  merged into #382505; the rest is off-shade specks and faint lighter washes over darker inks.
