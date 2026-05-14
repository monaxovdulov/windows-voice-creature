from __future__ import annotations

import math
import platform
import random
import time

from PySide6 import QtCore, QtGui, QtWidgets

from .config import AppConfig
from .voice.commands import CommandAction, VoiceCommand


class CreatureWidget(QtWidgets.QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.direction = 1
        self.state = "idle"
        self.message = ""
        self._phase = 0.0
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

    def set_creature_state(self, state: str, direction: int) -> None:
        self.state = state
        self.direction = 1 if direction >= 0 else -1
        self.update()

    def set_message(self, text: str) -> None:
        self.message = text
        self.update()

    def advance(self, dt: float) -> None:
        self._phase += dt
        self.update()

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        del event
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)

        width = self.width()
        height = self.height()
        bob = math.sin(self._phase * 8.0) * (3 if self.state == "walking" else 1)
        cx = width / 2
        cy = height * 0.62 + bob

        self._draw_shadow(painter, cx, height * 0.86)
        self._draw_tail(painter, cx, cy)
        self._draw_body(painter, cx, cy)
        self._draw_face(painter, cx, cy)

        if self.state == "listening":
            self._draw_listening_ring(painter, cx, cy)
        elif self.state == "dance":
            self._draw_sparkles(painter)

        if self.message:
            self._draw_message(painter, self.message)

    def _draw_shadow(self, painter: QtGui.QPainter, cx: float, y: float) -> None:
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(QtGui.QColor(0, 0, 0, 58))
        painter.drawEllipse(QtCore.QPointF(cx, y), 48, 12)

    def _draw_tail(self, painter: QtGui.QPainter, cx: float, cy: float) -> None:
        sign = self.direction
        tail_path = QtGui.QPainterPath()
        tail_path.moveTo(cx - sign * 43, cy + 8)
        tail_path.cubicTo(cx - sign * 78, cy - 12, cx - sign * 66, cy - 42, cx - sign * 36, cy - 26)
        painter.setPen(QtGui.QPen(QtGui.QColor(32, 98, 94), 11, QtCore.Qt.PenStyle.SolidLine,
                                  QtCore.Qt.PenCapStyle.RoundCap))
        painter.drawPath(tail_path)

    def _draw_body(self, painter: QtGui.QPainter, cx: float, cy: float) -> None:
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(QtGui.QColor(44, 171, 155))
        painter.drawEllipse(QtCore.QPointF(cx, cy), 48, 43)

        painter.setBrush(QtGui.QColor(87, 216, 184))
        painter.drawEllipse(QtCore.QPointF(cx + 7, cy + 9), 28, 22)

        ear_y = cy - 38
        painter.setBrush(QtGui.QColor(35, 143, 139))
        painter.drawEllipse(QtCore.QPointF(cx - 25, ear_y), 18, 26)
        painter.drawEllipse(QtCore.QPointF(cx + 25, ear_y), 18, 26)

        foot_y = cy + 38
        step = math.sin(self._phase * 10.0) * (5 if self.state == "walking" else 0)
        painter.setBrush(QtGui.QColor(32, 112, 112))
        painter.drawEllipse(QtCore.QPointF(cx - 24, foot_y + step), 17, 9)
        painter.drawEllipse(QtCore.QPointF(cx + 24, foot_y - step), 17, 9)

    def _draw_face(self, painter: QtGui.QPainter, cx: float, cy: float) -> None:
        look = 5 * self.direction
        painter.setBrush(QtGui.QColor(8, 29, 34))
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.drawEllipse(QtCore.QPointF(cx - 15 + look, cy - 8), 5, 7)
        painter.drawEllipse(QtCore.QPointF(cx + 15 + look, cy - 8), 5, 7)

        painter.setPen(QtGui.QPen(QtGui.QColor(8, 29, 34), 3, QtCore.Qt.PenStyle.SolidLine,
                                  QtCore.Qt.PenCapStyle.RoundCap))
        mouth = QtGui.QPainterPath()
        mouth.moveTo(cx - 8 + look, cy + 12)
        mouth.quadTo(cx + look, cy + 18, cx + 8 + look, cy + 12)
        painter.drawPath(mouth)

    def _draw_listening_ring(self, painter: QtGui.QPainter, cx: float, cy: float) -> None:
        pulse = (math.sin(self._phase * 6.0) + 1.0) / 2.0
        color = QtGui.QColor(255, 204, 77, 120)
        painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        painter.setPen(QtGui.QPen(color, 4))
        painter.drawEllipse(QtCore.QPointF(cx, cy), 58 + pulse * 8, 53 + pulse * 8)

    def _draw_sparkles(self, painter: QtGui.QPainter) -> None:
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 219, 87), 3, QtCore.Qt.PenStyle.SolidLine,
                                  QtCore.Qt.PenCapStyle.RoundCap))
        for index, (x, y) in enumerate(((36, 42), (132, 48), (118, 26))):
            pulse = 4 + math.sin(self._phase * 9 + index) * 2
            painter.drawLine(QtCore.QPointF(x - pulse, y), QtCore.QPointF(x + pulse, y))
            painter.drawLine(QtCore.QPointF(x, y - pulse), QtCore.QPointF(x, y + pulse))

    def _draw_message(self, painter: QtGui.QPainter, text: str) -> None:
        painter.setFont(QtGui.QFont("Segoe UI", 8))
        metrics = painter.fontMetrics()
        clipped = metrics.elidedText(text, QtCore.Qt.TextElideMode.ElideRight, self.width() - 22)
        rect = QtCore.QRectF(9, 8, self.width() - 18, 27)

        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(QtGui.QColor(255, 255, 255, 232))
        painter.drawRoundedRect(rect, 8, 8)
        painter.setPen(QtGui.QColor(24, 45, 52))
        painter.drawText(rect, QtCore.Qt.AlignmentFlag.AlignCenter, clipped)


class OverlayWindow(QtWidgets.QWidget):
    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.config = config
        self.creature = CreatureWidget()
        self.direction = 1
        self.autonomous = True
        self._velocity_x = 0.0
        self._command_until = 0.0
        self._next_decision = 0.0
        self._message_until = 0.0
        self._listening = False
        self._last_tick = time.monotonic()

        self._setup_window()
        self._setup_layout()
        self._place_initially()

        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def set_listening(self, listening: bool) -> None:
        self._listening = listening
        self.creature.set_creature_state("listening" if listening else "idle", self.direction)
        if listening:
            self.show_message("Слушаю...")

    def show_message(self, text: str, seconds: float = 2.8) -> None:
        self.creature.set_message(text)
        self._message_until = time.monotonic() + seconds

    def apply_voice_command(self, command: VoiceCommand, heard_text: str) -> None:
        if command.action is CommandAction.UNKNOWN:
            self.show_message(f"Не понял: {heard_text or 'пусто'}")
            return

        labels = {
            CommandAction.MOVE_FORWARD: "Вперед",
            CommandAction.MOVE_BACKWARD: "Назад",
            CommandAction.MOVE_LEFT: "Влево",
            CommandAction.MOVE_RIGHT: "Вправо",
            CommandAction.STOP: "Стою",
            CommandAction.COME_TO_CURSOR: "Иду",
            CommandAction.DANCE: "Танцую",
        }
        self.show_message(labels[command.action])
        now = time.monotonic()

        if command.action is CommandAction.STOP:
            self._velocity_x = 0.0
            self._command_until = now + 3.0
        elif command.action is CommandAction.MOVE_FORWARD:
            self._velocity_x = self.direction * self.config.base_speed * 1.35
            self._command_until = now + 2.5
        elif command.action is CommandAction.MOVE_BACKWARD:
            self._velocity_x = -self.direction * self.config.base_speed * 1.15
            self._command_until = now + 2.2
        elif command.action is CommandAction.MOVE_LEFT:
            self.direction = -1
            self._velocity_x = -self.config.base_speed * 1.35
            self._command_until = now + 2.5
        elif command.action is CommandAction.MOVE_RIGHT:
            self.direction = 1
            self._velocity_x = self.config.base_speed * 1.35
            self._command_until = now + 2.5
        elif command.action is CommandAction.COME_TO_CURSOR:
            cursor_x = QtGui.QCursor.pos().x()
            center_x = self.x() + self.width() / 2
            self.direction = 1 if cursor_x >= center_x else -1
            self._velocity_x = self.direction * self.config.base_speed * 1.45
            self._command_until = now + min(3.5, max(0.6, abs(cursor_x - center_x) / self.config.base_speed))
        elif command.action is CommandAction.DANCE:
            self._velocity_x = 0.0
            self._command_until = now + 3.0
            self.creature.set_creature_state("dance", self.direction)

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent) -> None:
        menu = QtWidgets.QMenu(self)
        pause_action = menu.addAction("Выключить самостоятельное движение" if self.autonomous else "Включить самостоятельное движение")
        quit_action = menu.addAction("Выход")
        selected = menu.exec(event.globalPos())
        if selected == pause_action:
            self.autonomous = not self.autonomous
            self._velocity_x = 0.0
        elif selected == quit_action:
            QtWidgets.QApplication.quit()

    def _setup_window(self) -> None:
        flags = (
            QtCore.Qt.WindowType.FramelessWindowHint
            | QtCore.Qt.WindowType.WindowStaysOnTopHint
            | QtCore.Qt.WindowType.Tool
        )
        self.setWindowFlags(flags)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setWindowTitle("Screen Creature")
        self.resize(self.config.creature_size, self.config.creature_size)
        if self.config.click_through:
            self._enable_click_through()

    def _setup_layout(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.creature)

    def _place_initially(self) -> None:
        geo = _available_geometry()
        x = geo.x() + geo.width() - self.width() - 48
        y = geo.y() + geo.height() - self.height() - 18
        self.move(x, y)

    def _tick(self) -> None:
        now = time.monotonic()
        dt = max(0.001, min(0.05, now - self._last_tick))
        self._last_tick = now

        if self._message_until and now >= self._message_until:
            self.creature.set_message("")
            self._message_until = 0.0

        if self._listening:
            self._velocity_x = 0.0
            state = "listening"
        else:
            self._update_behavior(now)
            state = self._current_state(now)

        self._move(dt)
        self.creature.set_creature_state(state, self.direction)
        self.creature.advance(dt)

    def _update_behavior(self, now: float) -> None:
        if self._command_until and now < self._command_until:
            return
        if self._command_until and now >= self._command_until:
            self._command_until = 0.0
            self._velocity_x = 0.0

        if not self.autonomous:
            self._velocity_x = 0.0
            return

        if now < self._next_decision:
            return

        choice = random.choice(("idle", "idle", "left", "right"))
        if choice == "idle":
            self._velocity_x = 0.0
            self._next_decision = now + random.uniform(1.0, 2.6)
        else:
            self.direction = -1 if choice == "left" else 1
            self._velocity_x = self.direction * random.uniform(
                self.config.base_speed * 0.55,
                self.config.base_speed * 0.95,
            )
            self._next_decision = now + random.uniform(1.3, 3.4)

    def _current_state(self, now: float) -> str:
        if self.creature.state == "dance" and self._command_until and now < self._command_until:
            return "dance"
        return "walking" if abs(self._velocity_x) > 1 else "idle"

    def _move(self, dt: float) -> None:
        if abs(self._velocity_x) <= 1:
            return

        geo = _available_geometry()
        min_x = geo.x()
        max_x = geo.x() + geo.width() - self.width()
        new_x = self.x() + self._velocity_x * dt

        if new_x <= min_x:
            new_x = min_x
            self.direction = 1
            self._velocity_x = abs(self._velocity_x)
        elif new_x >= max_x:
            new_x = max_x
            self.direction = -1
            self._velocity_x = -abs(self._velocity_x)
        elif self._velocity_x > 0:
            self.direction = 1
        else:
            self.direction = -1

        self.move(round(new_x), self.y())

    def _enable_click_through(self) -> None:
        if platform.system() != "Windows":
            return
        try:
            import ctypes

            hwnd = int(self.winId())
            user32 = ctypes.windll.user32
            gwl_exstyle = -20
            ws_ex_layered = 0x00080000
            ws_ex_transparent = 0x00000020
            current_style = user32.GetWindowLongW(hwnd, gwl_exstyle)
            user32.SetWindowLongW(hwnd, gwl_exstyle, current_style | ws_ex_layered | ws_ex_transparent)
        except Exception:
            return


def _available_geometry() -> QtCore.QRect:
    screen = QtGui.QGuiApplication.primaryScreen()
    if screen is None:
        return QtCore.QRect(0, 0, 1280, 720)
    return screen.availableGeometry()

