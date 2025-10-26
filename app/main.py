"""Application entry point for OpenKeyFlow."""
from __future__ import annotations

import sys

from PyQt5 import QtCore, QtWidgets

from backend import storage
from backend.trigger_engine import TriggerEngine
from .main_window import APP_NAME, MainWindow


def main() -> None:
    storage.ensure_data_dir()
    config = storage.load_config()
    hotkeys = storage.load_hotkeys()

    engine = TriggerEngine(
        hotkeys=hotkeys,
        cooldown=float(config.get("cooldown", 0.3)),
        paste_delay=float(config.get("paste_delay", 0.05)),
    )
    engine.start()

    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName(APP_NAME)

    window = MainWindow(engine)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
