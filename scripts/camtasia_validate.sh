#!/bin/bash
echo "=== pycamtasia Camtasia Integration Test ==="

# Check if Camtasia is installed
if [ ! -d "/Applications/Camtasia.app" ]; then
    echo "SKIP: Camtasia not installed"
    exit 0
fi

PROJECT="/tmp/Anomaly Detection Demo (v3).cmproj"
BACKUP="/tmp/before-multispeed.json"
LOG="/tmp/cam_validate.log"

if [ ! -f "$BACKUP" ]; then
    echo "SKIP: No backup project at $BACKUP"
    exit 0
fi

# Rebuild
cp "$BACKUP" "$PROJECT/project.tscproj"
PYTHONPATH=~/Documents/pycamtasia/src python3 -c "
import warnings; warnings.filterwarnings('ignore')
from camtasia import load_project
proj = load_project('$PROJECT')
proj.save()
"

if [ -f ~/Desktop/Anomaly\ Detection\ Demo\ v3/assemble_project_v2.py ]; then
    cd ~/Desktop/Anomaly\ Detection\ Demo\ v3
    PYTHONPATH=~/Documents/pycamtasia/src python3 assemble_project_v2.py
else
    echo "NOTE: Assembly script not found, skipping assemble step"
fi

# Launch Camtasia
pkill -f Camtasia 2>/dev/null; sleep 3
rm -f "$PROJECT/~project.tscproj"
/Applications/Camtasia.app/Contents/MacOS/Camtasia "$PROJECT" 2>"$LOG" &
sleep 20

EXCEPTIONS=$(grep -c 'EXCEPTION' "$LOG" 2>/dev/null) || EXCEPTIONS=0
pkill -f Camtasia 2>/dev/null

if [ "$EXCEPTIONS" = "0" ]; then
    echo "✅ PASS: Camtasia opened project with 0 exceptions"
    exit 0
else
    echo "❌ FAIL: Camtasia found $EXCEPTIONS exceptions"
    grep 'EXCEPTION' "$LOG" | head -5
    exit 1
fi
