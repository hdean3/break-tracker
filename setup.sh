#!/usr/bin/env bash
# setup.sh — one-time setup for break-tracker on a Raspberry Pi (or any Linux host)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "==> Creating Python virtual environment..."
python3 -m venv venv

echo "==> Installing dependencies..."
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

echo ""
echo "Done. Next steps:"
echo ""
echo "  1. SET UP GOOGLE SERVICE ACCOUNT"
echo "     a. Go to https://console.cloud.google.com/"
echo "     b. Create a project (or use an existing one)"
echo "     c. Enable APIs: Google Sheets API + Google Drive API"
echo "     d. IAM & Admin > Service Accounts > Create Service Account"
echo "     e. Create a JSON key for the service account, download it"
echo "     f. Save the JSON key as:  ${SCRIPT_DIR}/credentials.json"
echo "     g. Create a Google Sheet and share it with the service account email (Editor)"
echo ""
echo "  2. CONFIGURE THE TRACKER"
echo "     cp config.yaml.example config.yaml"
echo "     # Edit config.yaml: fill in MyQ credentials and Google Sheet ID"
echo ""
echo "  3. TEST IT (dry run — no Sheets writes)"
echo "     ./venv/bin/python tracker.py --dry-run"
echo ""
echo "  4. INSTALL AS SYSTEMD SERVICE (run as root or with sudo)"
echo "     sudo cp break_tracker.service /etc/systemd/system/"
echo "     sudo systemctl daemon-reload"
echo "     sudo systemctl enable break_tracker"
echo "     sudo systemctl start break_tracker"
echo "     sudo journalctl -fu break_tracker   # watch live logs"
echo ""
