from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    hotkey_label: str = "Ctrl+Alt+Space"
    hotkey_required: frozenset[str] = frozenset({"ctrl", "alt", "space"})
    model_path: Path = Path("models/vosk-model-small-ru-0.22")
    sample_rate: int = 16_000
    creature_size: int = 168
    base_speed: float = 115.0
    click_through: bool = False

    @classmethod
    def from_env(cls) -> "AppConfig":
        model_path = Path(os.getenv("CREATURE_VOSK_MODEL", cls.model_path.as_posix()))
        base_speed = _float_env("CREATURE_SPEED", cls.base_speed)
        sample_rate = int(_float_env("CREATURE_SAMPLE_RATE", float(cls.sample_rate)))
        click_through = os.getenv("CREATURE_CLICK_THROUGH", "").lower() in {"1", "true", "yes", "on"}
        return cls(
            model_path=model_path,
            sample_rate=sample_rate,
            base_speed=base_speed,
            click_through=click_through,
        )


def _float_env(name: str, default: float) -> float:
    value = os.getenv(name)
    if not value:
        return default
    try:
        return float(value)
    except ValueError:
        return default

