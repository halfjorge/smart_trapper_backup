# Example checks (test scripts, not part of the app)

Python scripts used to check the engine against Sara's hand-trapped examples in
`Desktop\Trap Examples\<job>\before.psd` and `after.psd`. They need Python 3 with numpy,
opencv-python, Pillow and psd-tools (tifffile for TIFFs). Paths inside point to Claude's cloud
workspace (`/home/claude/ex/...`), so adjust them before running.

**Start with these**
- `extract.py <psd> <outdir>`: writes every top-level layer as full-canvas RGBA `.npy`, plus
  meta.json.
- `halo_test.py <job> <after-offset> <trapPx> <halo list>`: the newest, cleanest harness.
  - Uses real soft alpha and Sara's settings.
  - Runs Manual Progressive Knockout, then the real engine binary.
  - Compares with the hand file: paper still showing, visible change outside the key, and halo fill.
  - Example: `halo_test.py Phish 150 5 0,2`
- `sim.py`: the older harness (binary masks); reports manual-only / trapper-only pixels per colour.

**Per-example investigations**
- `phish2.py`, `hyp.py`, `hyp2.py`, `shape.py`, `diffview.py`: Phish key halo
- `methane.py`, `methane2.py`: Methane
- `overlay.py`, `ovcheck.py`: Mempho overlays
- `helton.py`: Helton Darken
- `gray.py`: Ocean gray layers
- `direction.py`, `bts_engine.py`: BTS
- `byrne_engine.py`: Byrne butt joins and round traps
- `vista_check.py`: Vista

**General before/after analysis**
- `analyze.py`, `generic.py`, `cmp_run.py`, `preview.py`
- `tifflayers.py`: reads the layers of a layered TIFF
- `make_sp_press.py`: built the Smashing Pumpkins press TIFF

**Engine speed and regression**
- `make_job.py`: builds a synthetic job
- `runm.py`: times a run
- `cmp.py`: checks two engine outputs pixel by pixel
