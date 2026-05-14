from __future__ import annotations

from PySide6 import QtCore

try:
    from pynput import keyboard
except ImportError:  # pragma: no cover - handled at runtime on incomplete installs
    keyboard = None


class HotkeySignals(QtCore.QObject):
    pressed = QtCore.Signal()
    released = QtCore.Signal()
    error = QtCore.Signal(str)


class PushToTalkHotkey:
    def __init__(self, required_keys: frozenset[str]) -> None:
        self.signals = HotkeySignals()
        self.required_keys = required_keys
        self._held: set[str] = set()
        self._active = False
        self._listener = None

    def start(self) -> None:
        if keyboard is None:
            self.signals.error.emit("pynput не установлен, горячая клавиша недоступна")
            return
        if self._listener is not None:
            return

        self._listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
        self._listener.daemon = True
        self._listener.start()

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener = None

    def _on_press(self, key: object) -> None:
        normalized = _normalize_key(key)
        if normalized is None:
            return

        self._held.add(normalized)
        if not self._active and self.required_keys.issubset(self._held):
            self._active = True
            self.signals.pressed.emit()

    def _on_release(self, key: object) -> None:
        normalized = _normalize_key(key)
        if normalized is None:
            return

        self._held.discard(normalized)
        if self._active and normalized in self.required_keys:
            self._active = False
            self.signals.released.emit()


def _normalize_key(key: object) -> str | None:
    if keyboard is None:
        return None

    ctrl_keys = {keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r}
    alt_keys = {keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt_gr}
    if key in ctrl_keys:
        return "ctrl"
    if key in alt_keys:
        return "alt"
    if key == keyboard.Key.space:
        return "space"

    char = getattr(key, "char", None)
    if isinstance(char, str) and char:
        return char.lower()
    return None

