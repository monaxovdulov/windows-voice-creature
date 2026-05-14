import pytest

from PySide6 import QtCore

from screen_creature.overlay import (
    CREATURE_SKINS,
    _fall_step,
    _ground_y_for_geometry,
    _moving_state_for_skin,
    _next_skin_index,
    _rects_overlap_horizontally,
    _typed_message_state,
    _typing_duration,
)


def test_typewriter_starts_with_first_character() -> None:
    text, talking = _typed_message_state("Привет", started_at=10.0, now=10.0)

    assert text == "П"
    assert talking


def test_typewriter_finishes_after_full_duration() -> None:
    started_at = 10.0
    message = "Привет"

    text, talking = _typed_message_state(
        message,
        started_at=started_at,
        now=started_at + _typing_duration(message),
    )

    assert text == message
    assert not talking


def test_typing_duration_counts_first_character_as_visible() -> None:
    assert _typing_duration("Привет") == pytest.approx(5 / 18)


def test_fall_step_accelerates_downward() -> None:
    y, velocity, landed = _fall_step(y=100.0, velocity=0.0, dt=0.1, ground_y=500.0)

    assert y == pytest.approx(123.0)
    assert velocity == pytest.approx(230.0)
    assert not landed


def test_fall_step_lands_on_ground() -> None:
    y, velocity, landed = _fall_step(y=495.0, velocity=200.0, dt=0.1, ground_y=500.0)

    assert y == 500.0
    assert velocity == 0.0
    assert landed


def test_ground_y_uses_bottom_margin() -> None:
    geometry = QtCore.QRect(0, 0, 1280, 720)

    assert _ground_y_for_geometry(geometry, window_height=168) == 534


def test_horizontal_rect_overlap_detects_creature_above_stand() -> None:
    creature = QtCore.QRect(1010, 120, 168, 168)
    stand_shelf = QtCore.QRect(1090, 280, 130, 14)

    assert _rects_overlap_horizontally(creature, stand_shelf)


def test_horizontal_rect_overlap_rejects_missed_stand() -> None:
    creature = QtCore.QRect(600, 120, 168, 168)
    stand_shelf = QtCore.QRect(1090, 280, 130, 14)

    assert not _rects_overlap_horizontally(creature, stand_shelf)


def test_skin_system_has_multiple_distinct_creatures() -> None:
    names = {skin.name for skin in CREATURE_SKINS}
    features = {skin.feature for skin in CREATURE_SKINS}
    movements = {skin.movement for skin in CREATURE_SKINS}
    abilities = {skin.ability for skin in CREATURE_SKINS}

    assert names == {"Мятный", "Ночной", "Искра"}
    assert features == {"ears", "antennae", "horns"}
    assert movements == {"waddle", "hover", "spark"}
    assert abilities == {"nest", "portal", "dash"}


def test_skin_switch_wraps_around() -> None:
    assert _next_skin_index(0) == 1
    assert _next_skin_index(len(CREATURE_SKINS) - 1) == 0


def test_skin_movement_states_are_distinct() -> None:
    mint, night, spark = CREATURE_SKINS

    assert _moving_state_for_skin(mint, velocity_x=120.0) == "walking"
    assert _moving_state_for_skin(night, velocity_x=0.0) == "floating"
    assert _moving_state_for_skin(spark, velocity_x=240.0) == "dashing"
