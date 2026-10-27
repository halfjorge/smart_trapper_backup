# Panel tests without Photoshop (stand-in Photoshop)

`run_trapper_button_test.js` loads the real panel (main.js + styles.css) in the pre-installed
Chromium (Playwright) with a stand-in for Photoshop, and clicks the one-button **Run Trapper** in 18
situations (normal, tonal, overlay box on/off, 600 ppi, CMYK, trap width 0, no document, already
trapped, helper not running, knockout error, engine error, 0 traps, CLEAN warning, import failure,
unexpected error, 2 layers, double-click), then the four individual step buttons.

Real: panel markup, every check, the engine step's code talking to the REAL helper
(`real_bridge.py`) and REAL engine. Stand-ins: Photoshop (document/layers) and the Photoshop-only
parts of the steps (knockout, snapshot layer, mask export, prepare, import) - they record that they
were called and return what the real ones return.

How to run (cloud workspace):
1. Build the engine (tools/dev/engine_build_kit_cloud.zip, see PROJECT_NOTES section 9).
2. Make a folder `bridge_root/` with `UXP_Trapper/real_bridge.py` and the engine at
   `SmartTrapperB1/engine/target/release/smart_trapper_b1`; start `python3 real_bridge.py` there.
3. `python3 make_test_job.py /path/job_ok` and `python3 make_test_job.py /path/job_zero zero`;
   `mkdir job_broken && echo '{bad' > job_broken/job.json`.
4. `node run_trapper_button_test.js <main.js> <styles.css> <outdir>` (paths of the test jobs are set
   at the top: TEMPLATES / JOBS). Screenshots + results.json go to <outdir>.

`file_type_test.js` (picker, 28 checks) and `shared_folder_test.js` (shared Dropbox folder, 18 checks) run after
run_trapper_button_test.js: `node shared_folder_test.js <outdir> fixtures/presets_test.json ../../shared_folder/presets.json`.
