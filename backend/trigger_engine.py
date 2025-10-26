"""Keyboard trigger monitoring for OpenKeyFlow."""
from __future__ import annotations

import threading
import time
from typing import Callable, Dict, List, Tuple

import keyboard

try:
    import pyperclip
except ImportError:  # pragma: no cover - optional dependency
    pyperclip = None  # type: ignore

SHIFT_KEYS = {"shift", "left shift", "right shift"}
WHITESPACE = {" ", "\n", "\t"}
SPECIAL_KEYS = {
    "space": " ",
    "enter": "\n",
    "tab": "\t",
}
SHIFTED_SYMBOLS = {
    "1": "!",
    "2": "@",
    "3": "#",
    "4": "$",
    "5": "%",
    "6": "^",
    "7": "&",
    "8": "*",
    "9": "(",
    "0": ")",
    "-": "_",
    "=": "+",
    "[": "{",
    "]": "}",
    ";": ":",
    "'": '"',
    ",": "<",
    ".": ">",
    "/": "?",
    "\\": "|",
    "`": "~",
}


def _default_fire_callback(trigger: str, output: str) -> None:
    # Hook for tests – intentionally empty.
    return


def safe_write(text: str, *, paste_delay: float = 0.05) -> None:
    """Safely send text to the active window."""
    if pyperclip is None:
        keyboard.write(text, delay=0)
        return

    try:
        previous = pyperclip.paste()
    except Exception:
        keyboard.write(text, delay=0)
        return
    try:
        pyperclip.copy(text)
        time.sleep(paste_delay)
        keyboard.send("ctrl+v")
        time.sleep(paste_delay)
    finally:
        try:
            pyperclip.copy(previous)
        except Exception:
            pass


class TriggerEngine:
    """Monitor keyboard events and expand matching triggers."""

    def __init__(
        self,
        *,
        hotkeys: Dict[str, str] | None = None,
        cooldown: float = 0.3,
        paste_delay: float = 0.05,
        fire_callback: Callable[[str, str], None] = _default_fire_callback,
    ) -> None:
        self._hotkeys: Dict[str, str] = hotkeys or {}
        self._sorted_triggers: List[Tuple[str, str]] = []
        self._buffer = ""
        self._max_len = 0
        self._enabled = True
        self._cooldown = cooldown
        self._paste_delay = paste_delay
        self._fire_callback = fire_callback

        self._last_fire = 0.0
        self._suppress_events = False
        self._shift_active = False
        self._caps_lock = keyboard.is_toggled("caps lock") if hasattr(keyboard, "is_toggled") else False

        self._lock = threading.RLock()
        self._thread: threading.Thread | None = None
        self._hooked = False
        self._fired_count = 0

        self.update_hotkeys(self._hotkeys)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, name="TriggerEngine", daemon=True)
        self._thread.start()

    def set_enabled(self, enabled: bool) -> None:
        with self._lock:
            self._enabled = enabled
            if not enabled:
                self._buffer = ""

    def toggle_enabled(self) -> bool:
        with self._lock:
            self._enabled = not self._enabled
            if not self._enabled:
                self._buffer = ""
            return self._enabled

    def update_hotkeys(self, hotkeys: Dict[str, str]) -> None:
        with self._lock:
            self._hotkeys = dict(hotkeys)
            self._sorted_triggers = sorted(self._hotkeys.items(), key=lambda item: len(item[0]), reverse=True)
            self._max_len = max((len(trigger) for trigger in self._hotkeys), default=0)
            if len(self._buffer) > self._max_len:
                self._buffer = self._buffer[-self._max_len :]

    def set_cooldown(self, cooldown: float) -> None:
        with self._lock:
            self._cooldown = max(0.0, cooldown)

    def set_paste_delay(self, paste_delay: float) -> None:
        with self._lock:
            self._paste_delay = max(0.0, paste_delay)

    def get_stats(self) -> Dict[str, int]:
        with self._lock:
            return {"fired": self._fired_count}

    # ------------------------------------------------------------------
    # Internal logic
    # ------------------------------------------------------------------
    def _run(self) -> None:
        if self._hooked:
            return
        keyboard.hook(self._handle_event)
        self._hooked = True
        keyboard.wait()

    def _handle_event(self, event) -> None:
        if event.event_type not in ("down", "up"):
            return

        name = (event.name or "").lower()

        if name in SHIFT_KEYS:
            self._shift_active = event.event_type == "down"
            return

        if name == "caps lock" and event.event_type == "down":
            self._caps_lock = not self._caps_lock
            return

        if event.event_type != "down":
            return

        fired: Tuple[str, str] | None = None

        with self._lock:
            if not self._enabled or self._suppress_events or not self._sorted_triggers:
                if name == "backspace":
                    self._buffer = self._buffer[:-1]
                return

            if name == "backspace":
                self._buffer = self._buffer[:-1]
                return

            char = self._translate_key(name)
            if char is None:
                return

            if char in WHITESPACE:
                self._buffer = ""
                return

            self._buffer = (self._buffer + char)[-self._max_len :]

            match = self._find_match_locked()
            if match is None:
                return

            trigger, output = match
            now = time.time()
            if now - self._last_fire < self._cooldown:
                return

            self._last_fire = now
            fired = self._fire_locked(trigger, output)

        if fired is not None:
            fired_trigger, fired_output = fired
            self._fire_callback(fired_trigger, fired_output)

    def _find_match_locked(self) -> Tuple[str, str] | None:
        for trigger, output in self._sorted_triggers:
            if trigger and self._buffer.endswith(trigger):
                return trigger, output
        return None

    def _fire_locked(self, trigger: str, output: str) -> Tuple[str, str] | None:
        self._suppress_events = True
        try:
            for _ in range(len(trigger)):
                keyboard.send("backspace")
                time.sleep(self._paste_delay)
            safe_write(output, paste_delay=self._paste_delay)
            self._buffer = ""
            self._fired_count += 1
            return trigger, output
        finally:
            self._suppress_events = False
        return None

    def _translate_key(self, name: str) -> str | None:
        if len(name) == 1:
            if name.isalpha():
                uppercase = self._shift_active ^ self._caps_lock
                return name.upper() if uppercase else name.lower()
            if self._shift_active and name in SHIFTED_SYMBOLS:
                return SHIFTED_SYMBOLS[name]
            return name
        return SPECIAL_KEYS.get(name)
