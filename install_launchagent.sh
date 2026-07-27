#!/bin/bash
# Install OpenDjicht as macOS LaunchAgent (auto-start on boot)
# Run: bash install_launchagent.sh

PLIST_SRC="com.open-djicht.governance.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.open-djicht.governance.plist"

# Update the plist with current paths
cat > "$PLIST_DST" << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.open-djicht.governance</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/Users/dlandman/OpenMythos/openmythos-benchmark/start_open_djicht.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/dlandman/logs/open-djicht.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/dlandman/logs/open-djicht-error.log</string>
    <key>WorkingDirectory</key>
    <string>/Users/dlandman/OpenMythos/openmythos-benchmark</string>
</dict>
</plist>
PLIST

# Load it
launchctl bootstrap gui/$(id -u) "$PLIST_DST" 2>/dev/null || launchctl load "$PLIST_DST" 2>/dev/null || true

echo "LaunchAgent installed to: $PLIST_DST"
echo "OpenDjicht will auto-start on next login."
echo ""
echo "Commands:"
echo "  Start now:  launchctl start com.open-djicht.governance"
echo "  Stop:       launchctl stop com.open-djicht.governance"
echo "  Status:     launchctl list | grep open-djicht"
echo "  Logs:       tail -f /Users/dlandman/logs/open-djicht.log"
