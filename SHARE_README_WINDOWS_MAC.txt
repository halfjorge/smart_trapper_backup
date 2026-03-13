Smart Trapper Share Package

Contents
- Phase2_Run_All.jsx
- Phase2_Export.jsx
- Phase2_Import.jsx
- SmartTrapperB1/engine/Cargo.toml
- SmartTrapperB1/engine/Cargo.lock
- SmartTrapperB1/engine/src/main.rs

What This Package Does
- Exports Photoshop masks from the open PSD
- Runs the Rust trapping engine
- Imports the generated trap masks back into Photoshop

Requirements
- Adobe Photoshop with JSX/ExtendScript support
- Rust toolchain (`cargo`) installed if you need to build the engine

Windows Setup
1. Put the package folder anywhere convenient.
2. Build the engine:
   - Open a terminal in `SmartTrapperB1/engine`
   - Run: `cargo build --release`
3. Confirm the executable exists at:
   - `SmartTrapperB1/engine/target/release/smart_trapper_b1.exe`
4. Open your PSD in Photoshop.
5. Run `Phase2_Run_All.jsx`.

macOS Setup
1. Put the package folder anywhere convenient.
2. Build the engine:
   - Open Terminal
   - `cd` into `SmartTrapperB1/engine`
   - Run: `cargo build --release`
3. Confirm the executable exists at:
   - `SmartTrapperB1/engine/target/release/smart_trapper_b1`
4. If macOS blocks execution, remove quarantine from the built binary if needed:
   - `xattr -d com.apple.quarantine SmartTrapperB1/engine/target/release/smart_trapper_b1`
5. Open your PSD in Photoshop.
6. Run `Phase2_Run_All.jsx`.

How The Runner Finds The Engine
- The controller first looks for the engine relative to the script bundle:
  - Windows: `SmartTrapperB1/engine/target/release/smart_trapper_b1.exe`
  - macOS: `SmartTrapperB1/engine/target/release/smart_trapper_b1`
- If it is not found, the script prompts the user to select the engine executable manually.

Typical Test Flow
1. Open a PSD.
2. Run `Phase2_Run_All.jsx`.
3. Answer the prompts:
   - debug logging
   - cleanup on/off
   - cleanup values if enabled
   - trap width
4. Choose the export base folder when prompted.
5. Wait for the job folder, trap generation, and import to complete.

Notes
- The same JSX files should run on Windows and macOS.
- The main platform-specific difference is how the Rust engine is built and launched.
- The controller now writes and runs:
  - `run_trapper.bat` on Windows
  - `run_trapper.sh` on macOS

If The Mac Test Fails
- Verify the engine binary exists and runs from Terminal.
- Verify Photoshop has permission to launch shell commands.
- Check the generated `trapper_log.txt` and `import_debug_log.txt` in the job folder.
