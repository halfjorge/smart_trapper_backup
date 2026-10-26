# Smart Trapper user guide (for the co-worker's install)

`Smart_Trapper_Guide.pdf` - DRAFT (2026-10-26) for Sara's review. The Mac install page is a placeholder
until the install package is built and tested on the Mac.

Every setting picture is made by running the REAL engine on small test drawings (setting off vs on);
the knockout / Clean Colors / Cut Top Key pictures are drawings. Nothing here touches Sara's files.

Rebuild (cloud workspace; paths at the top of each script point at /home/claude/work/...):
1. Build the engine (tools/dev/engine_build_kit_cloud.zip) - `ENGINE` in demo_lib.py.
2. `python3 demo_trapwidth.py && python3 demo_all.py && python3 illus.py` -> img_*.png + demo_log.json
   (engine numbers quoted in the captions).
3. Panel pictures: run tools/ui_tests first (makes out_shared/panel_test.html), then `node shots.js`.
4. `python3 build_guide.py && node topdf.js` -> Smart_Trapper_Guide.pdf.
If a setting's behaviour or a file type's values change, re-run all of it so the pictures stay true.
