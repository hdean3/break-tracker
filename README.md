# break-tracker

Passive break time auditor for remote work.

## How it works

The garage door is the most reliable signal for leaving and returning home. This script watches the Chamberlain MyQ garage door state via the unofficial pymyq API and logs every open/close event to a Google Sheet.

- **Break starts** when the garage door opens (you're leaving)
- **Break ends** when the garage door closes (you're back)
- **Duration** is calculated automatically on each CLOSE event

The Ring doorbell can optionally be wired in via IFTTT as a secondary "arrival home" marker, but the garage door is the primary signal.

## Accuracy caveat

This is an **auditing aid, not exact tracking**. Family members may open/close the door too, so events are logged for review, not treated as gospel. The goal is ±10-15 min accuracy to confirm you took a break, not to time it to the second.

## Stack

| Component | Tool | Cost |
|-----------|------|------|
| Garage door API | pymyq (unofficial MyQ) | Free |
| Break log storage | Google Sheets | Free |
| Hosting | Raspberry Pi (Pi-hole, already on network) | $0 extra |
| Ring integration | IFTTT webhook | Free tier |

No cloud server, no paid APIs, no monthly bill.

## Setup

### 1. Clone and create virtualenv

```bash
git clone https://github.com/hdean3/break-tracker.git
cd break-tracker
./setup.sh
```

### 2. Configure Google Sheets

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project, enable **Google Sheets API** and **Google Drive API**
3. Create a **Service Account**, download the JSON key → save as `credentials.json`
4. Create a Google Sheet, note the spreadsheet ID from the URL
5. Share the sheet with the service account email (Editor access)

### 3. Configure tracker

```bash
cp config.yaml.example config.yaml
# Edit config.yaml with your MyQ credentials, spreadsheet ID, etc.
```

### 4. Test it

```bash
# Dry run — prints events to stdout, does NOT write to Sheets
./venv/bin/python tracker.py --dry-run
```

### 5. Install as systemd service (Pi)

```bash
sudo cp break_tracker.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable break_tracker
sudo systemctl start break_tracker
sudo journalctl -fu break_tracker   # watch logs
```

## Google Sheet columns

| Column | Value |
|--------|-------|
| Timestamp | ISO 8601 datetime of the event |
| Event | OPEN or CLOSE |
| Duration (min) | Minutes since last OPEN (only on CLOSE events) |
| Notes | e.g., "break", "family member" |

## Ring doorbell integration (optional)

Use IFTTT to POST to a local webhook when the Ring doorbell detects motion or a press. Planned in issue #2.

## Roadmap

See [GitHub Issues](https://github.com/hdean3/break-tracker/issues).
