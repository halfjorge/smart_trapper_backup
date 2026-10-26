#!/bin/bash
# Removes the Smart Trapper helper and engine. Keeps ~/SmartTrapper (your job folders) and the Photoshop panel
# (remove the panel in Creative Cloud > Stock & Marketplace > Plugins > Manage plugins).
AGENT_ID="com.thehalfandhalf.smarttrapper.helper"
launchctl bootout "gui/$(id -u)/$AGENT_ID" >/dev/null 2>&1
rm -f "$HOME/Library/LaunchAgents/$AGENT_ID.plist"
pkill -f "SmartTrapper/smart_trapper_helpe[r]" >/dev/null 2>&1
rm -rf "$HOME/Library/Application Support/SmartTrapper"
echo "Smart Trapper helper and engine removed. Your ~/SmartTrapper folder was kept."
[ -z "${SMART_TRAPPER_CI:-}" ] && osascript -e 'display dialog "Smart Trapper helper removed.\n\nTo remove the Photoshop panel too: Creative Cloud app > Plugins > Manage plugins." buttons {"OK"} with title "Smart Trapper"' >/dev/null 2>&1
