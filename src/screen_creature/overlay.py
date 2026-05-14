from __future__ import annotations

import math
import platform
import random
import time
from dataclasses import dataclass

from PySide6 import QtCore, QtGui, QtWidgets

from .config import AppConfig
from .voice.commands import CommandAction, VoiceCommand


CLICK_MESSAGES = (
    "Привет!",
    "Я тут.",
    "Ай, щекотно!",
    "Что делаем?",
    "Поймал клик.",
    "Не отвлекайся.",
)
DRAG_THRESHOLD_PX = 6
FALL_GRAVITY = 2300.0
GROUND_MARGIN = 18
IMPACT_SECONDS = 0.45
STAND_COLLAPSED_WIDTH = 10
STAND_HEIGHT = 376
STAND_SHELF_Y = 62
STAND_WIDTH = 170
TYPEWRITER_CHARS_PER_SECOND = 18.0

ColorValue = tuple[int, int, int]


@dataclass(frozen=True)
class CreatureSkin:
    name: str
    body: ColorValue
    belly: ColorValue
    accent: ColorValue
    foot: ColorValue
    eye: ColorValue
    sparkle: ColorValue
    feature: str
    movement: str
    expression: str
    ability: str
    ability_label: str


CREATURE_SKINS = (
    CreatureSkin(
        name="Мятный",
        body=(44, 171, 155),
        belly=(87, 216, 184),
        accent=(35, 143, 139),
        foot=(32, 112, 112),
        eye=(8, 29, 34),
        sparkle=(255, 219, 87),
        feature="ears",
        movement="waddle",
        expression="curious",
        ability="nest",
        ability_label="Уют",
    ),
    CreatureSkin(
        name="Ночной",
        body=(92, 82, 198),
        belly=(151, 139, 255),
        accent=(58, 55, 134),
        foot=(48, 45, 113),
        eye=(255, 246, 184),
        sparkle=(140, 214, 255),
        feature="antennae",
        movement="hover",
        expression="dreamy",
        ability="portal",
        ability_label="Портал",
    ),
    CreatureSkin(
        name="Искра",
        body=(221, 95, 58),
        belly=(255, 188, 91),
        accent=(159, 56, 44),
        foot=(127, 48, 42),
        eye=(35, 20, 22),
        sparkle=(255, 231, 102),
        feature="horns",
        movement="spark",
        expression="fierce",
        ability="dash",
        ability_label="Рывок",
    ),
)


class CreatureWidget(QtWidgets.QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.direction = 1
        self.state = "idle"
        self.message = ""
        self.talking = False
        self.impact = 0.0
        self.skin = CREATURE_SKINS[0]
        self._phase = 0.0
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

    def set_creature_state(self, state: str, direction: int) -> None:
        self.state = state
        self.direction = 1 if direction >= 0 else -1
        self.update()

    def set_message(self, text: str, talking: bool = False) -> None:
        self.message = text
        self.talking = talking
        self.update()

    def set_impact(self, strength: float) -> None:
        self.impact = max(0.0, min(1.0, strength))
        self.update()

    def set_skin(self, skin: CreatureSkin) -> None:
        self.skin = skin
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
        bob = self._body_bob()
        cx = width / 2
        cy = height * 0.62 + bob + self.impact * 5

        self._draw_shadow(painter, cx, height * 0.86)
        if self.state == "falling":
            self._draw_fall_lines(painter)
        self._draw_tail(painter, cx, cy)
        self._draw_body(painter, cx, cy)
        self._draw_face(painter, cx, cy)
        if self.impact:
            self._draw_impact_puffs(painter)

        if self.state == "listening":
            self._draw_listening_ring(painter, cx, cy)
        elif self.state == "dance":
            self._draw_sparkles(painter)

        if self.message:
            self._draw_message(painter, self.message)

    def _body_bob(self) -> float:
        if self.state == "floating":
            return math.sin(self._phase * 3.0) * 7 - 5
        if self.state == "dashing":
            return -abs(math.sin(self._phase * 15.0)) * 9
        if self.state == "walking":
            return math.sin(self._phase * 8.0) * 3
        return math.sin(self._phase * 8.0)

    def _draw_shadow(self, painter: QtGui.QPainter, cx: float, y: float) -> None:
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(QtGui.QColor(0, 0, 0, 58))
        painter.drawEllipse(QtCore.QPointF(cx, y), 48, 12)

    def _draw_tail(self, painter: QtGui.QPainter, cx: float, cy: float) -> None:
        sign = self.direction
        tail_path = QtGui.QPainterPath()
        tail_path.moveTo(cx - sign * 43, cy + 8)
        tail_path.cubicTo(cx - sign * 78, cy - 12, cx - sign * 66, cy - 42, cx - sign * 36, cy - 26)
        painter.setPen(QtGui.QPen(_color(self.skin.foot), 11, QtCore.Qt.PenStyle.SolidLine,
                                  QtCore.Qt.PenCapStyle.RoundCap))
        painter.drawPath(tail_path)

    def _draw_body(self, painter: QtGui.QPainter, cx: float, cy: float) -> None:
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        squash_x = 1.0 + self.impact * 0.2
        squash_y = 1.0 - self.impact * 0.16
        painter.setBrush(_color(self.skin.body))
        painter.drawEllipse(QtCore.QPointF(cx, cy), 48 * squash_x, 43 * squash_y)

        painter.setBrush(_color(self.skin.belly))
        painter.drawEllipse(QtCore.QPointF(cx + 7, cy + 9), 28 * squash_x, 22 * squash_y)

        self._draw_head_feature(painter, cx, cy)

        foot_y = cy + 38
        step = self._foot_step()
        painter.setBrush(_color(self.skin.foot))
        if self.skin.movement == "hover":
            painter.drawEllipse(QtCore.QPointF(cx - 23, foot_y + 2), 13, 6)
            painter.drawEllipse(QtCore.QPointF(cx + 23, foot_y - 2), 13, 6)
        elif self.skin.movement == "spark":
            painter.drawEllipse(QtCore.QPointF(cx - 25, foot_y + step), 18, 10)
            painter.drawEllipse(QtCore.QPointF(cx + 25, foot_y - step), 18, 10)
            self._draw_spark_trail(painter, cx, foot_y)
        else:
            painter.drawEllipse(QtCore.QPointF(cx - 24, foot_y + step), 17, 9)
            painter.drawEllipse(QtCore.QPointF(cx + 24, foot_y - step), 17, 9)

    def _foot_step(self) -> float:
        if self.state == "dashing":
            return math.sin(self._phase * 24.0) * 8
        if self.state == "walking":
            return math.sin(self._phase * 10.0) * 5
        return 0.0

    def _draw_spark_trail(self, painter: QtGui.QPainter, cx: float, foot_y: float) -> None:
        if self.state != "dashing":
            return
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(_color(self.skin.sparkle, 120))
        painter.drawEllipse(QtCore.QPointF(cx - self.direction * 54, foot_y + 4), 10, 5)
        painter.drawEllipse(QtCore.QPointF(cx - self.direction * 72, foot_y + 8), 6, 3)

    def _draw_head_feature(self, painter: QtGui.QPainter, cx: float, cy: float) -> None:
        if self.skin.feature == "antennae":
            painter.setPen(QtGui.QPen(_color(self.skin.accent), 5,
                                      QtCore.Qt.PenStyle.SolidLine,
                                      QtCore.Qt.PenCapStyle.RoundCap))
            for sign in (-1, 1):
                start = QtCore.QPointF(cx + sign * 20, cy - 32)
                end = QtCore.QPointF(cx + sign * 33, cy - 60)
                painter.drawLine(start, end)
                painter.setPen(QtCore.Qt.PenStyle.NoPen)
                painter.setBrush(_color(self.skin.sparkle))
                painter.drawEllipse(end, 7, 7)
                painter.setPen(QtGui.QPen(_color(self.skin.accent), 5,
                                          QtCore.Qt.PenStyle.SolidLine,
                                          QtCore.Qt.PenCapStyle.RoundCap))
            return

        if self.skin.feature == "horns":
            painter.setPen(QtCore.Qt.PenStyle.NoPen)
            painter.setBrush(_color(self.skin.sparkle))
            for sign in (-1, 1):
                horn = QtGui.QPainterPath()
                horn.moveTo(cx + sign * 17, cy - 35)
                horn.lineTo(cx + sign * 31, cy - 65)
                horn.lineTo(cx + sign * 38, cy - 28)
                horn.closeSubpath()
                painter.drawPath(horn)
            painter.setBrush(_color(self.skin.accent))
            painter.drawEllipse(QtCore.QPointF(cx - 25, cy - 38), 12, 18)
            painter.drawEllipse(QtCore.QPointF(cx + 25, cy - 38), 12, 18)
            return

        ear_y = cy - 38
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(_color(self.skin.accent))
        painter.drawEllipse(QtCore.QPointF(cx - 25, ear_y), 18, 26)
        painter.drawEllipse(QtCore.QPointF(cx + 25, ear_y), 18, 26)

    def _draw_face(self, painter: QtGui.QPainter, cx: float, cy: float) -> None:
        look = 5 * self.direction
        eye_color = _color(self.skin.eye)
        painter.setBrush(eye_color)
        painter.setPen(QtCore.Qt.PenStyle.NoPen)

        if self.skin.expression == "dreamy":
            painter.setPen(QtGui.QPen(eye_color, 4, QtCore.Qt.PenStyle.SolidLine,
                                      QtCore.Qt.PenCapStyle.RoundCap))
            painter.drawLine(QtCore.QPointF(cx - 21 + look, cy - 8),
                             QtCore.QPointF(cx - 10 + look, cy - 8))
            painter.drawLine(QtCore.QPointF(cx + 10 + look, cy - 8),
                             QtCore.QPointF(cx + 21 + look, cy - 8))
        elif self.skin.expression == "fierce":
            for sign in (-1, 1):
                eye = QtGui.QPainterPath()
                eye.moveTo(cx + sign * 9 + look, cy - 13)
                eye.lineTo(cx + sign * 23 + look, cy - 8)
                eye.lineTo(cx + sign * 10 + look, cy - 3)
                eye.closeSubpath()
                painter.drawPath(eye)
            painter.setPen(QtGui.QPen(eye_color, 3, QtCore.Qt.PenStyle.SolidLine,
                                      QtCore.Qt.PenCapStyle.RoundCap))
            painter.drawLine(QtCore.QPointF(cx - 24 + look, cy - 18),
                             QtCore.QPointF(cx - 10 + look, cy - 14))
            painter.drawLine(QtCore.QPointF(cx + 24 + look, cy - 18),
                             QtCore.QPointF(cx + 10 + look, cy - 14))
        else:
            painter.drawEllipse(QtCore.QPointF(cx - 15 + look, cy - 8), 5, 7)
            painter.drawEllipse(QtCore.QPointF(cx + 15 + look, cy - 8), 5, 7)

        if self.talking:
            mouth_height = 5 + (math.sin(self._phase * 34.0) + 1.0) * 4
            mouth_rect = QtCore.QRectF(cx - 7 + look, cy + 7, 14, mouth_height)
            painter.setPen(QtCore.Qt.PenStyle.NoPen)
            painter.setBrush(eye_color)
            painter.drawEllipse(mouth_rect)
            return

        painter.setPen(QtGui.QPen(eye_color, 3, QtCore.Qt.PenStyle.SolidLine,
                                  QtCore.Qt.PenCapStyle.RoundCap))
        mouth = QtGui.QPainterPath()
        if self.skin.expression == "dreamy":
            painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QtCore.QPointF(cx + look, cy + 11), 5, 4)
            return
        if self.skin.expression == "fierce":
            mouth.moveTo(cx - 10 + look, cy + 12)
            mouth.lineTo(cx - 2 + look, cy + 16)
            mouth.lineTo(cx + 10 + look, cy + 10)
            painter.drawPath(mouth)
            return

        mouth.moveTo(cx - 8 + look, cy + 12)
        mouth.quadTo(cx + look, cy + 18, cx + 8 + look, cy + 12)
        painter.drawPath(mouth)

    def _draw_listening_ring(self, painter: QtGui.QPainter, cx: float, cy: float) -> None:
        pulse = (math.sin(self._phase * 6.0) + 1.0) / 2.0
        color = _color(self.skin.sparkle, 120)
        painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        painter.setPen(QtGui.QPen(color, 4))
        painter.drawEllipse(QtCore.QPointF(cx, cy), 58 + pulse * 8, 53 + pulse * 8)

    def _draw_sparkles(self, painter: QtGui.QPainter) -> None:
        painter.setPen(QtGui.QPen(_color(self.skin.sparkle), 3, QtCore.Qt.PenStyle.SolidLine,
                                  QtCore.Qt.PenCapStyle.RoundCap))
        for index, (x, y) in enumerate(((36, 42), (132, 48), (118, 26))):
            pulse = 4 + math.sin(self._phase * 9 + index) * 2
            painter.drawLine(QtCore.QPointF(x - pulse, y), QtCore.QPointF(x + pulse, y))
            painter.drawLine(QtCore.QPointF(x, y - pulse), QtCore.QPointF(x, y + pulse))

    def _draw_fall_lines(self, painter: QtGui.QPainter) -> None:
        painter.setPen(QtGui.QPen(_color(self.skin.accent, 95), 2,
                                  QtCore.Qt.PenStyle.SolidLine,
                                  QtCore.Qt.PenCapStyle.RoundCap))
        offset = (self._phase * 220) % 22
        for x, y in ((42, 28), (73, 18), (126, 32)):
            painter.drawLine(QtCore.QPointF(x, y + offset), QtCore.QPointF(x, y + 16 + offset))

    def _draw_impact_puffs(self, painter: QtGui.QPainter) -> None:
        alpha = int(155 * self.impact)
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, alpha), 3,
                                  QtCore.Qt.PenStyle.SolidLine,
                                  QtCore.Qt.PenCapStyle.RoundCap))
        painter.setBrush(QtGui.QColor(255, 255, 255, int(75 * self.impact)))
        y = self.height() * 0.86
        spread = 28 + (1.0 - self.impact) * 22
        painter.drawEllipse(QtCore.QPointF(self.width() / 2 - spread, y + 2), 10, 5)
        painter.drawEllipse(QtCore.QPointF(self.width() / 2 + spread, y + 2), 10, 5)
        painter.drawLine(QtCore.QPointF(34, y - 5), QtCore.QPointF(16, y - 13))
        painter.drawLine(QtCore.QPointF(self.width() - 34, y - 5),
                         QtCore.QPointF(self.width() - 16, y - 13))

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


class SmartStandWindow(QtWidgets.QWidget):
    def __init__(self, owner: OverlayWindow) -> None:
        super().__init__()
        self.owner = owner
        self.collapsed = False

        self.setWindowFlags(
            QtCore.Qt.WindowType.FramelessWindowHint
            | QtCore.Qt.WindowType.WindowStaysOnTopHint
            | QtCore.Qt.WindowType.Tool
        )
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setWindowTitle("Creature Stand")

        self._status = QtWidgets.QLabel("Гуляет")
        self._status.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self._status.setWordWrap(True)

        self._home_button = QtWidgets.QPushButton("Домой")
        self._home_button.clicked.connect(lambda: self.owner.move_to_stand())

        self._drop_button = QtWidgets.QPushButton("Вниз")
        self._drop_button.clicked.connect(lambda: self.owner.drop_from_stand())

        self._dance_button = QtWidgets.QPushButton("Танец")
        self._dance_button.clicked.connect(lambda: self.owner.start_dance())

        self._skin_button = QtWidgets.QPushButton("Скин")
        self._skin_button.clicked.connect(lambda: self.owner.next_skin())

        self._ability_button = QtWidgets.QPushButton("Способность")
        self._ability_button.clicked.connect(lambda: self.owner.use_skin_ability())

        self._walk_button = QtWidgets.QPushButton("Пауза")
        self._walk_button.clicked.connect(lambda: self.owner.toggle_autonomous())

        self._collapse_button = QtWidgets.QPushButton("Свернуть")
        self._collapse_button.clicked.connect(lambda: self.set_collapsed(True))

        self._quit_button = QtWidgets.QPushButton("Выход")
        self._quit_button.clicked.connect(lambda: QtWidgets.QApplication.quit())

        self._controls = (
            self._status,
            self._home_button,
            self._drop_button,
            self._dance_button,
            self._skin_button,
            self._ability_button,
            self._walk_button,
            self._collapse_button,
            self._quit_button,
        )
        self._setup_layout()
        self._apply_style()
        self.set_collapsed(False)

    def set_collapsed(self, collapsed: bool) -> None:
        self.collapsed = collapsed
        for widget in self._controls:
            widget.setVisible(not collapsed)

        width = STAND_COLLAPSED_WIDTH if collapsed else STAND_WIDTH
        self.resize(width, STAND_HEIGHT)
        self._place()
        self.update()

    def update_status(
        self,
        text: str,
        autonomous: bool,
        skin_name: str,
        ability_label: str,
    ) -> None:
        self._status.setText(f"{text}\nСкин: {skin_name}")
        self._walk_button.setText("Пауза" if autonomous else "Ходить")
        self._skin_button.setText(f"Скин: {skin_name}")
        self._ability_button.setText(f"Сила: {ability_label}")

    def landing_y_for(self, creature_height: int) -> int | None:
        if self.collapsed:
            return None
        return self.y() + STAND_SHELF_Y - round(creature_height * 0.86)

    def landing_rect(self) -> QtCore.QRect | None:
        if self.collapsed:
            return None
        return QtCore.QRect(self.x() + 14, self.y() + STAND_SHELF_Y - 5, self.width() - 28, 14)

    def stand_position_for(self, creature_size: QtCore.QSize) -> QtCore.QPoint:
        self.set_collapsed(False)
        shelf = self.landing_rect()
        if shelf is None:
            return QtCore.QPoint(self.x(), self.y())
        x = shelf.center().x() - creature_size.width() // 2
        y = self.y() + STAND_SHELF_Y - round(creature_size.height() * 0.86)
        return QtCore.QPoint(x, y)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if self.collapsed and event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.set_collapsed(False)
            event.accept()
            return
        super().mousePressEvent(event)

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        del event
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)

        if self.collapsed:
            rect = QtCore.QRectF(1, 10, self.width() - 2, self.height() - 20)
            painter.setPen(QtCore.Qt.PenStyle.NoPen)
            painter.setBrush(QtGui.QColor(43, 145, 134, 210))
            painter.drawRoundedRect(rect, 5, 5)
            painter.setBrush(QtGui.QColor(255, 255, 255, 120))
            painter.drawRoundedRect(QtCore.QRectF(4, 26, 2, self.height() - 52), 1, 1)
            return

        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(QtGui.QColor(18, 38, 45, 218))
        painter.drawRoundedRect(QtCore.QRectF(0, 0, self.width(), self.height()), 14, 14)

        shelf = self.landing_rect()
        if shelf is None:
            return
        local_shelf = QtCore.QRectF(
            shelf.x() - self.x(),
            shelf.y() - self.y(),
            shelf.width(),
            shelf.height(),
        )
        painter.setBrush(QtGui.QColor(74, 218, 180, 235))
        painter.drawRoundedRect(local_shelf, 7, 7)
        painter.setBrush(QtGui.QColor(255, 255, 255, 70))
        painter.drawRoundedRect(local_shelf.adjusted(8, 2, -8, -8), 4, 4)

    def _setup_layout(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, STAND_SHELF_Y + 18, 12, 12)
        layout.setSpacing(7)
        layout.addWidget(self._status)
        layout.addWidget(self._home_button)
        layout.addWidget(self._drop_button)
        layout.addWidget(self._dance_button)
        layout.addWidget(self._skin_button)
        layout.addWidget(self._ability_button)
        layout.addWidget(self._walk_button)
        layout.addStretch(1)
        layout.addWidget(self._collapse_button)
        layout.addWidget(self._quit_button)

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QLabel {
                color: #f0fffb;
                font: 600 12px "Segoe UI";
            }
            QPushButton {
                background: rgba(255, 255, 255, 218);
                border: 0;
                border-radius: 6px;
                color: #173038;
                font: 600 11px "Segoe UI";
                min-height: 24px;
                padding: 3px 8px;
            }
            QPushButton:hover {
                background: white;
            }
            QPushButton:pressed {
                background: #bff5e7;
            }
            """
        )

    def _place(self) -> None:
        geo = _available_geometry()
        x = geo.x() + geo.width() - self.width() - 8
        y = geo.y() + max(60, (geo.height() - self.height()) // 2)
        self.move(x, y)


class OverlayWindow(QtWidgets.QWidget):
    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.config = config
        self.creature = CreatureWidget()
        self.direction = 1
        self.autonomous = True
        self._skin_index = 0
        self._velocity_x = 0.0
        self._command_until = 0.0
        self._next_decision = 0.0
        self._message_until = 0.0
        self._message_started = 0.0
        self._message_text = ""
        self._listening = False
        self._dragging = False
        self._drag_moved = False
        self._drag_start_global = QtCore.QPoint()
        self._drag_start_window_pos = QtCore.QPoint()
        self._falling = False
        self._on_stand = False
        self._vertical_velocity = 0.0
        self._impact_until = 0.0
        self._last_tick = time.monotonic()

        self._setup_window()
        self._setup_layout()
        self._place_initially()
        self._stand = SmartStandWindow(self)
        self._stand.show()
        self._update_stand_status()

        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def set_listening(self, listening: bool) -> None:
        self._listening = listening
        self.creature.set_creature_state("listening" if listening else "idle", self.direction)
        if listening:
            self.show_message("Слушаю...")
        self._update_stand_status()

    def show_message(self, text: str, seconds: float = 2.8) -> None:
        now = time.monotonic()
        self._message_text = text
        self._message_started = now
        self._message_until = now + _typing_duration(text) + seconds
        self._update_visible_message(now)

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

    def move_to_stand(self) -> None:
        self._falling = False
        self._on_stand = True
        self._velocity_x = 0.0
        self._vertical_velocity = 0.0
        self._command_until = 0.0
        self.autonomous = False
        self.move(self._stand.stand_position_for(self.size()))
        self.show_message("Я на базе.", seconds=1.8)
        self._update_stand_status()

    def drop_from_stand(self) -> None:
        self._on_stand = False
        if self.y() < self._ground_y() - 2:
            self._start_fall()
        else:
            self.show_message("Я уже внизу.", seconds=1.6)
        self._update_stand_status()

    def start_dance(self) -> None:
        self._velocity_x = 0.0
        self._command_until = time.monotonic() + 3.0
        self.creature.set_creature_state("dance", self.direction)
        self.show_message("Танцую!", seconds=1.8)
        self._update_stand_status()

    def next_skin(self) -> None:
        self._skin_index = _next_skin_index(self._skin_index)
        skin = CREATURE_SKINS[self._skin_index]
        self.creature.set_skin(skin)
        self.show_message(f"Теперь я {skin.name}.", seconds=1.8)
        self._update_stand_status()

    def use_skin_ability(self) -> None:
        skin = CREATURE_SKINS[self._skin_index]
        if skin.ability == "nest":
            self.move_to_stand()
            self.show_message("Уютный режим.", seconds=1.8)
        elif skin.ability == "portal":
            self._portal_to_cursor()
        elif skin.ability == "dash":
            self._spark_dash()
        self._update_stand_status()

    def toggle_autonomous(self) -> None:
        self.autonomous = not self.autonomous
        if self.autonomous:
            was_on_stand = self._on_stand
            self._on_stand = False
            if was_on_stand and self.y() < self._ground_y() - 2:
                self._start_fall()
            self.show_message("Иду гулять.", seconds=1.8)
        else:
            self._velocity_x = 0.0
            self.show_message("Постояю тут.", seconds=1.8)
        self._update_stand_status()

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent) -> None:
        menu = QtWidgets.QMenu(self)
        pause_action = menu.addAction("Выключить самостоятельное движение" if self.autonomous else "Включить самостоятельное движение")
        quit_action = menu.addAction("Выход")
        selected = menu.exec(event.globalPos())
        if selected == pause_action:
            self.toggle_autonomous()
        elif selected == quit_action:
            QtWidgets.QApplication.quit()

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self._begin_drag(_event_global_position(event))
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        if self._dragging and event.buttons() & QtCore.Qt.MouseButton.LeftButton:
            self._drag_to(_event_global_position(event))
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        if self._dragging and event.button() == QtCore.Qt.MouseButton.LeftButton:
            self._finish_drag()
            event.accept()
            return
        super().mouseReleaseEvent(event)

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
        y = _ground_y_for_geometry(geo, self.height())
        self.move(x, y)

    def _tick(self) -> None:
        now = time.monotonic()
        dt = max(0.001, min(0.05, now - self._last_tick))
        self._last_tick = now
        self._update_impact(now)

        if self._message_until and now >= self._message_until:
            self._clear_message()
        elif self._message_text:
            self._update_visible_message(now)

        if self._dragging:
            self._velocity_x = 0.0
            state = "idle"
        elif self._falling:
            self._update_fall(dt)
            state = "falling" if self._falling else "idle"
        elif self._on_stand:
            self._velocity_x = 0.0
            state = self._current_state(now)
        elif self._listening:
            self._velocity_x = 0.0
            state = "listening"
        else:
            self._update_behavior(now)
            state = self._current_state(now)

        if not self._dragging and not self._falling:
            self._move(dt)
        self.creature.set_creature_state(state, self.direction)
        self.creature.advance(dt)
        self._update_stand_status()

    def _begin_drag(self, global_position: QtCore.QPoint) -> None:
        self._dragging = True
        self._drag_moved = False
        self._drag_start_global = global_position
        self._drag_start_window_pos = self.pos()
        self._falling = False
        self._on_stand = False
        self._vertical_velocity = 0.0
        self._velocity_x = 0.0
        self._command_until = 0.0
        self._impact_until = 0.0
        self.creature.set_impact(0.0)
        self.setCursor(QtCore.Qt.CursorShape.ClosedHandCursor)
        self.grabMouse()

    def _drag_to(self, global_position: QtCore.QPoint) -> None:
        delta = global_position - self._drag_start_global
        if delta.manhattanLength() >= DRAG_THRESHOLD_PX:
            self._drag_moved = True

        target = self._drag_start_window_pos + delta
        geo = _available_geometry()
        x = _clamp(target.x(), geo.x(), geo.x() + geo.width() - self.width())
        y = _clamp(target.y(), geo.y(), self._ground_y())
        self.move(round(x), round(y))

    def _finish_drag(self) -> None:
        self._dragging = False
        self.releaseMouse()
        self.unsetCursor()

        if not self._drag_moved:
            self.show_message(random.choice(CLICK_MESSAGES), seconds=2.4)
            return

        if self.y() < self._ground_y() - 2:
            self._start_fall()
        else:
            self.move(self.x(), self._ground_y())

    def _portal_to_cursor(self) -> None:
        geo = _available_geometry()
        cursor = QtGui.QCursor.pos()
        x = _clamp(cursor.x() - self.width() / 2, geo.x(), geo.x() + geo.width() - self.width())
        y = _clamp(cursor.y() - self.height() / 2, geo.y(), self._ground_y())
        self._falling = False
        self._on_stand = False
        self._velocity_x = 0.0
        self._vertical_velocity = 0.0
        self._command_until = time.monotonic() + 1.0
        self.autonomous = False
        self.move(round(x), round(y))
        self.show_message("Портал открыт.", seconds=1.6)

    def _spark_dash(self) -> None:
        now = time.monotonic()
        cursor_x = QtGui.QCursor.pos().x()
        center_x = self.x() + self.width() / 2
        self.direction = 1 if cursor_x >= center_x else -1
        self._falling = False
        self._on_stand = False
        self.autonomous = True
        self._velocity_x = self.direction * self.config.base_speed * 4.8
        self._command_until = now + 0.9
        self._next_decision = now + 1.2
        self.show_message("Рывок!", seconds=1.1)

    def _start_fall(self) -> None:
        self._falling = True
        self._on_stand = False
        self._vertical_velocity = 0.0
        self._velocity_x = 0.0
        self._next_decision = time.monotonic() + 1.2

    def _update_fall(self, dt: float) -> None:
        target_y, target_kind = self._fall_target()
        y, velocity, landed = _fall_step(
            y=float(self.y()),
            velocity=self._vertical_velocity,
            dt=dt,
            ground_y=float(target_y),
        )
        self._vertical_velocity = velocity
        self.move(self.x(), round(y))
        if landed:
            self._land(on_stand=target_kind == "stand")

    def _land(self, on_stand: bool = False) -> None:
        now = time.monotonic()
        self._falling = False
        self._on_stand = on_stand
        self._vertical_velocity = 0.0
        self._impact_until = now + IMPACT_SECONDS
        self.creature.set_impact(1.0)
        self._next_decision = now + 1.2
        if on_stand:
            self.autonomous = False
            self.show_message("На базе.", seconds=1.4)
        else:
            self.show_message("Бум!", seconds=1.0)
        self._update_stand_status()

    def _update_impact(self, now: float) -> None:
        if not self._impact_until:
            return
        if now >= self._impact_until:
            self._impact_until = 0.0
            self.creature.set_impact(0.0)
            return
        self.creature.set_impact((self._impact_until - now) / IMPACT_SECONDS)

    def _ground_y(self) -> int:
        return _ground_y_for_geometry(_available_geometry(), self.height())

    def _fall_target(self) -> tuple[int, str]:
        ground_y = self._ground_y()
        stand_y = self._stand_landing_y()
        if stand_y is not None and self.y() <= stand_y < ground_y:
            return stand_y, "stand"
        return ground_y, "ground"

    def _stand_landing_y(self) -> int | None:
        landing_y = self._stand.landing_y_for(self.height())
        landing_rect = self._stand.landing_rect()
        creature_rect = QtCore.QRect(self.x(), self.y(), self.width(), self.height())
        if landing_y is None or landing_rect is None:
            return None
        if not _rects_overlap_horizontally(creature_rect, landing_rect):
            return None
        return landing_y

    def _update_stand_status(self) -> None:
        if self._on_stand:
            status = "На базе"
        elif self._falling:
            status = "Падает"
        elif self._listening:
            status = "Слушает"
        elif self.autonomous:
            status = "Гуляет"
        else:
            status = "Пауза"
        self._stand.update_status(
            status,
            autonomous=self.autonomous,
            skin_name=CREATURE_SKINS[self._skin_index].name,
            ability_label=CREATURE_SKINS[self._skin_index].ability_label,
        )

    def _update_visible_message(self, now: float) -> None:
        text, talking = _typed_message_state(
            self._message_text,
            self._message_started,
            now,
        )
        self.creature.set_message(text, talking=talking)

    def _clear_message(self) -> None:
        self._message_text = ""
        self._message_started = 0.0
        self._message_until = 0.0
        self.creature.set_message("", talking=False)

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

        skin = CREATURE_SKINS[self._skin_index]
        if skin.movement == "hover":
            choice = random.choice(("idle", "left", "right", "right"))
            if choice == "idle":
                self._velocity_x = 0.0
                self._next_decision = now + random.uniform(1.6, 3.2)
            else:
                self.direction = -1 if choice == "left" else 1
                self._velocity_x = self.direction * random.uniform(
                    self.config.base_speed * 0.28,
                    self.config.base_speed * 0.62,
                )
                self._next_decision = now + random.uniform(2.0, 4.4)
            return

        if skin.movement == "spark":
            choice = random.choice(("idle", "left", "right", "right"))
            if choice == "idle":
                self._velocity_x = 0.0
                self._next_decision = now + random.uniform(0.45, 1.1)
            else:
                self.direction = -1 if choice == "left" else 1
                self._velocity_x = self.direction * random.uniform(
                    self.config.base_speed * 1.35,
                    self.config.base_speed * 2.05,
                )
                self._next_decision = now + random.uniform(0.35, 0.85)
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
        return _moving_state_for_skin(CREATURE_SKINS[self._skin_index], self._velocity_x)

    def _move(self, dt: float) -> None:
        if abs(self._velocity_x) <= 1:
            if CREATURE_SKINS[self._skin_index].movement == "hover" and not self._on_stand:
                self.move(self.x(), round(self._hover_y()))
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

        y = self._hover_y() if CREATURE_SKINS[self._skin_index].movement == "hover" else self.y()
        self.move(round(new_x), round(y))

    def _hover_y(self) -> float:
        return self._ground_y() - 20 + math.sin(self.creature._phase * 1.8) * 7

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


def _event_global_position(event: QtGui.QMouseEvent) -> QtCore.QPoint:
    return event.globalPosition().toPoint()


def _color(value: ColorValue, alpha: int | None = None) -> QtGui.QColor:
    if alpha is None:
        return QtGui.QColor(*value)
    return QtGui.QColor(value[0], value[1], value[2], alpha)


def _next_skin_index(index: int) -> int:
    return (index + 1) % len(CREATURE_SKINS)


def _moving_state_for_skin(skin: CreatureSkin, velocity_x: float) -> str:
    if skin.movement == "hover":
        return "floating"
    if abs(velocity_x) <= 1:
        return "idle"
    if skin.movement == "spark":
        return "dashing"
    return "walking"


def _ground_y_for_geometry(geometry: QtCore.QRect, window_height: int) -> int:
    return geometry.y() + geometry.height() - window_height - GROUND_MARGIN


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _rects_overlap_horizontally(left: QtCore.QRect, right: QtCore.QRect) -> bool:
    return left.left() <= right.right() and right.left() <= left.right()


def _fall_step(y: float, velocity: float, dt: float, ground_y: float) -> tuple[float, float, bool]:
    velocity += FALL_GRAVITY * dt
    y += velocity * dt
    if y >= ground_y:
        return ground_y, 0.0, True
    return y, velocity, False


def _typing_duration(text: str) -> float:
    if len(text) <= 1:
        return 0.0
    return (len(text) - 1) / TYPEWRITER_CHARS_PER_SECOND


def _typed_message_state(text: str, started_at: float, now: float) -> tuple[str, bool]:
    if not text:
        return "", False

    elapsed = max(0.0, now - started_at)
    visible_count = min(len(text), int(elapsed * TYPEWRITER_CHARS_PER_SECOND) + 1)
    return text[:visible_count], visible_count < len(text)

