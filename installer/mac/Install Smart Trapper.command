#!/bin/bash
# Smart Trapper - Mac installer. Double-click me.
# Puts the engine + helper in ~/Library/Application Support/SmartTrapper, makes the helper start by itself
# at login, makes ~/SmartTrapper/TrapJobs, and installs the Photoshop panel. Nothing needs admin rights
# except possibly Adobe's own plugin installer.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
PAYLOAD="$HERE/payload"
DEST="$HOME/Library/Application Support/SmartTrapper"
AGENT_ID="com.thehalfandhalf.smarttrapper.helper"
AGENT="$HOME/Library/LaunchAgents/$AGENT_ID.plist"
UPIA="/Library/Application Support/Adobe/Adobe Desktop Common/RemoteComponents/UPI/UnifiedPluginInstallerAgent/UnifiedPluginInstallerAgent.app/Contents/MacOS/UnifiedPluginInstallerAgent"
LOG="$DEST/install.log"
say() { echo ""; echo "  $*"; }
fail() { say "PROBLEM: $*"; [ -z "${SMART_TRAPPER_CI:-}" ] && osascript -e "display dialog \"Smart Trapper could not finish installing:\n\n$*\n\nTake a screenshot of the Terminal window and send it to Sara.\" buttons {\"OK\"} with icon stop with title \"Smart Trapper\"" >/dev/null 2>&1; exit 1; }

echo "=============================================="
echo "  Installing Smart Trapper"
echo "=============================================="
[ -f "$PAYLOAD/smart_trapper_b1" ] && [ -f "$PAYLOAD/smart_trapper_helper" ] || fail "The installer folder is incomplete (payload missing). Unzip the whole download again."

say "1 of 5  Copying the trapper programs..."
mkdir -p "$DEST" || fail "Could not make $DEST"
launchctl bootout "gui/$(id -u)/$AGENT_ID" >/dev/null 2>&1   # stop an older helper before replacing it
pkill -f "SmartTrapper/smart_trapper_helpe[r]" >/dev/null 2>&1
cp -f "$PAYLOAD/smart_trapper_b1" "$PAYLOAD/smart_trapper_helper" "$DEST/" || fail "Could not copy the programs."
[ -f "$PAYLOAD/VERSION.txt" ] && cp -f "$PAYLOAD/VERSION.txt" "$DEST/"
chmod +x "$DEST/smart_trapper_b1" "$DEST/smart_trapper_helper"
xattr -dr com.apple.quarantine "$DEST" >/dev/null 2>&1    # our own shop tool: don't let macOS block it
# Does the engine start on this Mac? (No job given, so it should answer "cannot read job.json".)
"$DEST/smart_trapper_b1" "$DEST/no_such_job" 5 2>&1 | grep -q "job.json" || fail "The engine program won't run on this Mac."
"$DEST/smart_trapper_helper" --check 2>/dev/null | grep -q '"engineExists": true' || fail "The helper program won't run on this Mac."
echo "$(date) installed from $HERE" >> "$LOG"

say "2 of 5  Making the job folders (Home > SmartTrapper)..."
mkdir -p "$HOME/SmartTrapper/TrapJobs" "$HOME/SmartTrapper/status_logs" || fail "Could not make ~/SmartTrapper"
[ -f "$HERE/Smart_Trapper_Guide.pdf" ] && cp -f "$HERE/Smart_Trapper_Guide.pdf" "$HOME/SmartTrapper/"

say "3 of 5  Setting the helper to start by itself..."
mkdir -p "$HOME/Library/LaunchAgents"
cat > "$AGENT" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$AGENT_ID</string>
  <key>ProgramArguments</key><array><string>$DEST/smart_trapper_helper</string></array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><dict><key>SuccessfulExit</key><false/></dict>
  <key>StandardOutPath</key><string>$DEST/helper_stdout.log</string>
  <key>StandardErrorPath</key><string>$DEST/helper_stderr.log</string>
</dict>
</plist>
PLIST
launchctl bootstrap "gui/$(id -u)" "$AGENT" >/dev/null 2>&1 || launchctl load -w "$AGENT" >/dev/null 2>&1
ok=""
for i in $(seq 1 20); do
  if curl -s -m 2 http://127.0.0.1:8765/health | grep -q '"engineExists": true'; then ok=1; break; fi
  sleep 0.5
done
if [ -z "$ok" ]; then
  # Fallback (e.g. no login session): start it now; it will still start by itself at the next login.
  nohup "$DEST/smart_trapper_helper" >/dev/null 2>&1 &
  sleep 1
  curl -s -m 2 http://127.0.0.1:8765/health | grep -q '"engineExists": true' || fail "The helper did not start."
fi
echo "     helper is running."

say "4 of 5  Adding the panel to Photoshop..."
if [ -n "${SMART_TRAPPER_CI:-}" ]; then
  echo "     (test run - Photoshop panel install skipped)"
elif [ -x "$UPIA" ]; then
  "$UPIA" --install "$PAYLOAD/SmartTrapper.ccx" >> "$LOG" 2>&1 && echo "     panel installed." || {
    echo "     Adobe's installer did not finish - opening the panel file in Creative Cloud instead."
    open "$PAYLOAD/SmartTrapper.ccx"; }
else
  echo "     Opening the panel file in Creative Cloud (click Install when it asks)."
  open "$PAYLOAD/SmartTrapper.ccx"
fi

# Shared Dropbox folder (team presets): find it so we can say exactly which folder to pick in the panel.
SHARED=""
for root in "$HOME/Library/CloudStorage" "$HOME"; do
  [ -d "$root" ] || continue
  SHARED="$(find "$root" -maxdepth 6 -type d -name "SmartTrapper Shared" -path "*Dropbox*" 2>/dev/null | head -1)"
  [ -n "$SHARED" ] && break
done
if [ -n "$SHARED" ]; then
  echo "     Shared Dropbox folder found: $SHARED"
  echo "$(date) shared folder: $SHARED" >> "$LOG"
  SHARED_MSG="In the panel, open Setup > Shared folder... and pick:\n$SHARED"
else
  echo "     Shared Dropbox folder \"SmartTrapper Shared\" not found yet (Dropbox not set up?). The panel works without it."
  SHARED_MSG="Later: when Dropbox is set up, open Setup > Shared folder... in the panel and pick the \"SmartTrapper Shared\" folder."
fi

say "5 of 5  Done."
echo ""
echo "  Quit and reopen Photoshop, then open: Plugins > Smart Trapper UXP > Smart Trapper"
[ -f "$HOME/SmartTrapper/Smart_Trapper_Guide.pdf" ] && echo "  The guide is in your Home folder > SmartTrapper > Smart_Trapper_Guide.pdf"
echo ""
[ -z "${SMART_TRAPPER_CI:-}" ] && osascript -e "display dialog \"Smart Trapper is installed.\n\nQuit and reopen Photoshop, then open:\nPlugins > Smart Trapper UXP > Smart Trapper\n\n$SHARED_MSG\" buttons {\"OK\"} default button \"OK\" with title \"Smart Trapper\"" >/dev/null 2>&1
exit 0
