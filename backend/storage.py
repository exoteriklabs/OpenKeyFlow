"""Data storage helpers for OpenKeyFlow."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, Iterable, Tuple

_BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = _BASE_DIR / "okf_data"
HOTKEYS_FILE = DATA_DIR / "hotkeys.json"
CONFIG_FILE = DATA_DIR / "config.json"
CSV_TEMPLATE = DATA_DIR / "export_sample.csv"

DEFAULT_CONFIG = {
    "dark_mode": False,
    "cooldown": 0.3,
    "paste_delay": 0.05,
    "accepted_use_policy": False,
}


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not HOTKEYS_FILE.exists():
        HOTKEYS_FILE.write_text("{}", encoding="utf-8")
    if not CONFIG_FILE.exists():
        CONFIG_FILE.write_text(json.dumps(DEFAULT_CONFIG, indent=2), encoding="utf-8")
    if not CSV_TEMPLATE.exists():
        with CSV_TEMPLATE.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)
            writer.writerow(["Trigger", "Output"])


def load_hotkeys() -> Dict[str, str]:
    ensure_data_dir()
    with HOTKEYS_FILE.open("r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {}
    if not isinstance(data, dict):
        data = {}
    if not data:
        HOTKEYS_FILE.write_text("{}", encoding="utf-8")
    return {str(k): str(v) for k, v in data.items()}


def save_hotkeys(hotkeys: Dict[str, str]) -> None:
    ensure_data_dir()
    with HOTKEYS_FILE.open("w", encoding="utf-8") as f:
        json.dump(hotkeys, f, indent=4, ensure_ascii=False)


def load_config() -> Dict[str, float]:
    ensure_data_dir()
    if CONFIG_FILE.exists():
        with CONFIG_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        merged = DEFAULT_CONFIG.copy()
        merged.update({k: data.get(k, v) for k, v in DEFAULT_CONFIG.items()})
        return merged
    return DEFAULT_CONFIG.copy()


def save_config(config: Dict[str, float]) -> None:
    ensure_data_dir()
    merged = DEFAULT_CONFIG.copy()
    merged.update(config)
    with CONFIG_FILE.open("w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2)


def export_hotkeys_to_csv(path: Path, hotkeys: Dict[str, str]) -> None:
    path = Path(path)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerow(["Trigger", "Output"])
        for trigger, output in hotkeys.items():
            writer.writerow([trigger, output])


def import_hotkeys_from_csv(path: Path) -> Iterable[Tuple[str, str]]:
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f, skipinitialspace=True)
        for row in reader:
            trigger = (row.get("Trigger") or row.get("trigger") or row.get("Hotkey") or "").strip()
            output = (row.get("Output") or row.get("output") or row.get("Text") or "").strip()
            if trigger and output:
                yield trigger, output
