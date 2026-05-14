from __future__ import annotations

import platform
import sys

from PySide6 import QtCore, QtWidgets

from .config import AppConfig
from .overlay import OverlayWindow
from .voice.controller import VoiceController


def main() -> int:
    _set_windows_app_id()
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("Screen Creature")
    app.setOrganizationName("monaxovdulov")
    app.setQuitOnLastWindowClosed(False)

    config = AppConfig.from_env()
    window = OverlayWindow(config)
    controller = VoiceController(config, window)

    app.aboutToQuit.connect(controller.stop)
    window.show()
    controller.start()
    QtCore.QTimer.singleShot(350, lambda: window.show_message(controller.startup_status(), seconds=4.5))

    return app.exec()


def _set_windows_app_id() -> None:
    if platform.system() != "Windows":
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "monaxovdulov.windows-voice-creature"
        )
    except Exception:
        return

