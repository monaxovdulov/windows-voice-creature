from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CommandAction(str, Enum):
    MOVE_FORWARD = "move_forward"
    MOVE_BACKWARD = "move_backward"
    MOVE_LEFT = "move_left"
    MOVE_RIGHT = "move_right"
    STOP = "stop"
    COME_TO_CURSOR = "come_to_cursor"
    DANCE = "dance"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class VoiceCommand:
    action: CommandAction
    raw_text: str

    @property
    def is_known(self) -> bool:
        return self.action is not CommandAction.UNKNOWN


COMMAND_ALIASES: dict[CommandAction, tuple[str, ...]] = {
    CommandAction.MOVE_FORWARD: ("вперед", "иди вперед", "пошли вперед", "forward"),
    CommandAction.MOVE_BACKWARD: ("назад", "иди назад", "отступи", "back"),
    CommandAction.MOVE_LEFT: ("влево", "налево", "иди влево", "left"),
    CommandAction.MOVE_RIGHT: ("вправо", "направо", "иди вправо", "right"),
    CommandAction.STOP: ("стой", "стоп", "остановись", "замри", "stop"),
    CommandAction.COME_TO_CURSOR: ("ко мне", "иди ко мне", "подойди", "сюда"),
    CommandAction.DANCE: ("танцуй", "потанцуй", "dance"),
}


def normalize_text(text: str) -> str:
    return " ".join(text.lower().replace("ё", "е").strip().split())


def _is_cyrillic_or_space(text: str) -> bool:
    return all(("а" <= char <= "я") or char == " " for char in normalize_text(text))


GRAMMAR_PHRASES: list[str] = sorted(
    {
        phrase
        for aliases in COMMAND_ALIASES.values()
        for phrase in aliases
        if _is_cyrillic_or_space(phrase)
    }
)


def parse_voice_command(text: str) -> VoiceCommand:
    normalized = normalize_text(text)
    if not normalized:
        return VoiceCommand(CommandAction.UNKNOWN, text)

    for action, aliases in COMMAND_ALIASES.items():
        if any(alias in normalized for alias in aliases):
            return VoiceCommand(action, text)

    return VoiceCommand(CommandAction.UNKNOWN, text)
