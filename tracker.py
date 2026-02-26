#!/usr/bin/env python3
"""
break-tracker: passive break time auditor using MyQ garage door events.

Polls the MyQ garage door state every N seconds (configurable). On each
state change, logs a row to Google Sheets with timestamp, event type
(OPEN/CLOSE), and duration since the last event.

Usage:
    python tracker.py              # live mode — writes to Google Sheets
    python tracker.py --dry-run   # prints events to stdout only

Config:  config.yaml (see config.yaml.example)
Secrets: config.yaml and credentials.json — both gitignored, never commit.
"""

import argparse
import asyncio
import logging
import sys
from datetime import datetime, timezone
from typing import Optional

import gspread
import pymyq
import yaml
from aiohttp import ClientSession

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("break-tracker")


def load_config(path: str = "config.yaml") -> dict:
    """Load YAML config. Exits with a clear message if the file is missing."""
    try:
        with open(path) as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        log.error("Config file not found: %s — copy config.yaml.example to config.yaml and fill it in.", path)
        sys.exit(1)


def get_sheet(cfg: dict) -> gspread.Worksheet:
    """Open the target Google Sheet worksheet via a service account."""
    gc = gspread.service_account(filename=cfg["google_sheets"]["credentials_file"])
    spreadsheet = gc.open_by_key(cfg["google_sheets"]["spreadsheet_id"])
    return spreadsheet.worksheet(cfg["google_sheets"]["worksheet_name"])


def append_row(
    sheet: Optional[gspread.Worksheet],
    timestamp: str,
    event: str,
    duration_min: Optional[float],
    notes: str,
    dry_run: bool,
) -> None:
    """Append one event row to the sheet, or print it if dry_run is True."""
    dur_str = f"{duration_min:.1f}" if duration_min is not None else ""
    row = [timestamp, event, dur_str, notes]
    if dry_run:
        print(f"[DRY RUN]  {timestamp}  {event:<6}  dur={dur_str:>6} min  notes={notes}")
    else:
        sheet.append_row(row, value_input_option="USER_ENTERED")
        log.info("Logged: %s  %s  duration=%s min", timestamp, event, dur_str or "n/a")


async def poll_loop(cfg: dict, sheet: Optional[gspread.Worksheet], dry_run: bool) -> None:
    """Main polling loop. Runs indefinitely until interrupted."""
    interval = cfg.get("polling_interval_seconds", 30)
    prev_state: Optional[str] = None
    last_open_time: Optional[datetime] = None

    log.info("Starting poll loop (interval=%ds, dry_run=%s)", interval, dry_run)

    async with ClientSession() as session:
        myq = await pymyq.login(
            cfg["myq"]["email"],
            cfg["myq"]["password"],
            session,
        )

        # Find the first garage door device
        devices = myq.devices
        if not devices:
            log.error("No MyQ devices found. Check credentials.")
            sys.exit(1)

        # Pick the first door-type device; log all available for reference
        door = None
        for dev_id, dev in devices.items():
            log.info("Found device: %s  type=%s  state=%s", dev.name, dev.device_type, dev.state)
            if door is None and "door" in (dev.device_type or "").lower():
                door = dev

        if door is None:
            # Fall back to first device if type detection failed
            door = next(iter(devices.values()))
            log.warning("No door-type device detected — using first device: %s", door.name)

        log.info("Monitoring: %s (id=%s)", door.name, door.device_id)

        while True:
            try:
                await door.update()
                current_state = door.state  # "open" or "closed"
                now = datetime.now(timezone.utc)
                ts = now.strftime("%Y-%m-%d %H:%M:%S UTC")

                if current_state != prev_state and prev_state is not None:
                    if current_state == "open":
                        last_open_time = now
                        append_row(sheet, ts, "OPEN", None, "", dry_run)
                    elif current_state == "closed":
                        duration_min: Optional[float] = None
                        if last_open_time is not None:
                            duration_min = (now - last_open_time).total_seconds() / 60.0
                        append_row(sheet, ts, "CLOSE", duration_min, "", dry_run)
                        last_open_time = None

                prev_state = current_state

            except Exception as exc:  # noqa: BLE001
                log.warning("Poll error (will retry): %s", exc)

            await asyncio.sleep(interval)


def main() -> None:
    parser = argparse.ArgumentParser(description="Break time tracker via MyQ garage door")
    parser.add_argument("--dry-run", action="store_true", help="Print events to stdout instead of writing to Sheets")
    parser.add_argument("--config", default="config.yaml", help="Path to config file (default: config.yaml)")
    args = parser.parse_args()

    cfg = load_config(args.config)

    sheet: Optional[gspread.Worksheet] = None
    if not args.dry_run:
        log.info("Connecting to Google Sheets...")
        sheet = get_sheet(cfg)
        log.info("Sheet ready: %s", cfg["google_sheets"]["spreadsheet_id"])

    try:
        asyncio.run(poll_loop(cfg, sheet, args.dry_run))
    except KeyboardInterrupt:
        log.info("Stopped.")


if __name__ == "__main__":
    main()
