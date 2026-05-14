from __future__ import annotations

import json
from pathlib import Path

from .commands import GRAMMAR_PHRASES

try:
    from vosk import KaldiRecognizer, Model, SetLogLevel
except ImportError:  # pragma: no cover - handled at runtime on incomplete installs
    KaldiRecognizer = None
    Model = None

    def SetLogLevel(level: int) -> None:
        del level


class VoskSpeechRecognizer:
    def __init__(self, model_path: Path, sample_rate: int) -> None:
        self.model_path = model_path
        self.sample_rate = sample_rate
        self._model = None
        self.unavailable_reason = ""
        self._load_model()

    @property
    def is_available(self) -> bool:
        return self._model is not None

    def recognize(self, audio: bytes) -> str:
        if not audio or self._model is None or KaldiRecognizer is None:
            return ""

        grammar = json.dumps([*GRAMMAR_PHRASES, "[unk]"], ensure_ascii=False)
        recognizer = KaldiRecognizer(self._model, self.sample_rate, grammar)
        recognizer.AcceptWaveform(audio)
        result = json.loads(recognizer.FinalResult())
        return str(result.get("text", "")).strip()

    def _load_model(self) -> None:
        if Model is None:
            self.unavailable_reason = "vosk не установлен"
            return
        if not self.model_path.exists():
            self.unavailable_reason = f"модель не найдена: {self.model_path}"
            return

        SetLogLevel(-1)
        try:
            self._model = Model(str(self.model_path))
            self.unavailable_reason = ""
        except Exception as exc:  # pragma: no cover - depends on local model files
            self._model = None
            self.unavailable_reason = f"не удалось загрузить Vosk-модель: {exc}"

