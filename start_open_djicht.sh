#!/bin/bash
# OpenDjicht Governance API Server Startup Script
cd /Users/dlandman/OpenMythos/openmythos-benchmark
mkdir -p /Users/dlandman/logs

# Load API keys from shell config (launchd runs without a login shell, so PATH/python3 can't be trusted here)
source ~/.zshrc 2>/dev/null || true

# Start server (explicit interpreter — under launchd, `python3` on PATH resolves to Apple's old system Python)
exec /opt/homebrew/bin/python3 scripts/open_djicht_api.py --host 0.0.0.0 --port 8080
