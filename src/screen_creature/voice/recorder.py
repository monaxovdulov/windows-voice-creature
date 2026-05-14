from __future__ import annotations

import queue

try:
    import sounddevice as sd
except ImportError:  # pragma: no cover - handled at runtime on incomplete installs
    sd = None


class AudioRecorder:
    def __init__(self, sample_rate: int) -> None:
        self.sample_rate = sample_rate
        self._stream = None
        self._frames: queue.Queue[bytes] = queue.Queue()

    @property
    def is_recording(self) -> bool:
        return self._stream is not None

    def start(self) -> None:
        if sd is None:
            raise RuntimeError("sounddevice не установлен, запись микрофона недоступна")
        if self._stream is not None:
            return

        self._frames = queue.Queue()
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="int16",
            callback=self._on_audio,
        )
        self._stream.start()

    def stop(self) -> bytes:
        if self._stream is None:
            return b""

        stream = self._stream
        self._stream = None
        stream.stop()
        stream.close()

        chunks: list[bytes] = []
        while True:
            try:
                chunks.append(self._frames.get_nowait())
            except queue.Empty:
                break
        return b"".join(chunks)

    def _on_audio(self, indata: object, frames: int, time: object, status: object) -> None:
        del frames, time
        if status:
            return
        self._frames.put(indata.copy().tobytes())

