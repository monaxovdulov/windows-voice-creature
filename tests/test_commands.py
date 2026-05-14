from screen_creature.voice.commands import CommandAction, parse_voice_command


def test_parse_stop_command() -> None:
    command = parse_voice_command("стой")

    assert command.action is CommandAction.STOP
    assert command.is_known


def test_parse_direction_with_extra_words() -> None:
    command = parse_voice_command("пожалуйста иди вправо")

    assert command.action is CommandAction.MOVE_RIGHT


def test_parse_yo_normalization() -> None:
    command = parse_voice_command("иди вперёд")

    assert command.action is CommandAction.MOVE_FORWARD


def test_unknown_command() -> None:
    command = parse_voice_command("включи музыку")

    assert command.action is CommandAction.UNKNOWN
    assert not command.is_known

