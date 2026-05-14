from __future__ import annotations

import threading

from PySide6 import QtCore

from screen_creature.config import AppConfig
from screen_creature.overlay import OverlayWindow

from .commands import VoiceCommand, parse_voice_command
from .hotkey import PushToTalkHotkey
from .recognizer import VoskSpeechRecognizer
from .recorder import AudioRecorder


class VoiceSignals(QtCore.QObject):
    recognized = QtCore.Signal(str, object)
    error = QtCore.Signal(str)


class VoiceController(QtCore.QObject):
    def __init__(self, config: AppConfig, window: OverlayWindow) -> None:
        super().__init__()
        self.config = config
        self.window = window
        self.hotkey = PushToTalkHotkey(config.hotkey_required)
        self.recorder = AudioRecorder(config.sample_rate)
        self.recognizer = VoskSpeechRecognizer(config.model_path, config.sample_rate)
        self.signals = VoiceSignals()

        self.hotkey.signals.pressed.connect(self._start_recording)
        self.hotkey.signals.released.connect(self._stop_recording)
        self.hotkey.signals.error.connect(self.window.show_message)
        self.signals.recognized.connect(self._apply_recognized_text)
        self.signals.error.connect(self.window.show_message)

    def start(self) -> None:
        self.hotkey.start()

    def stop(self) -> None:
        self.hotkey.stop()
        if self.recorder.is_recording:
            self.recorder.stop()

    def startup_status(self) -> str:
        if self.recognizer.is_available:
            return f"Готово: {self.config.hotkey_label}"
        return f"Голос выключен: {self.recognizer.unavailable_reason}"

    def _start_recording(self) -> None:
        if self.recorder.is_recording:
            return
        if not self.recognizer.is_available:
            self.window.show_message(f"Голос недоступен: {self.recognizer.unavailable_reason}", seconds=4.0)
            return

        try:
            self.recorder.start()
        except Exception as exc:
            self.window.set_listening(False)
            self.window.show_message(str(exc), seconds=4.0)
            return

        self.window.set_listening(True)

    def _stop_recording(self) -> None:
        if not self.recorder.is_recording:
            self.window.set_listening(False)
            return

        try:
            audio = self.recorder.stop()
        except Exception as exc:
            self.window.set_listening(False)
            self.window.show_message(str(exc), seconds=4.0)
            return

        self.window.set_listening(False)
        if not self.recognizer.is_available:
            self.window.show_message(f"Голос недоступен: {self.recognizer.unavailable_reason}", seconds=4.0)
            return
        if len(audio) < int(self.config.sample_rate * 0.18) * 2:
            self.window.show_message("Слишком коротко")
            return

        thread = threading.Thread(target=self._recognize_in_background, args=(audio,), daemon=True)
        thread.start()

    def _recognize_in_background(self, audio: bytes) -> None:
        try:
            text = self.recognizer.recognize(audio)
        except Exception as exc:
            self.signals.error.emit(f"Ошибка распознавания: {exc}")
            return

        command = parse_voice_command(text)
        self.signals.recognized.emit(text, command)

    def _apply_recognized_text(self, text: str, command: VoiceCommand) -> None:
        if not text:
            self.window.show_message("Не расслышал")
            return
        self.window.apply_voice_command(command, text)
