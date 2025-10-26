"""Qt application window for OpenKeyFlow."""
from __future__ import annotations

import os
import sys
import threading
from pathlib import Path
from typing import Dict

import keyboard
from PIL import Image, ImageDraw, ImageFont
from PyQt5 import QtCore, QtGui, QtWidgets

from backend import storage
from backend.trigger_engine import TriggerEngine

try:
    from win32com.client import Dispatch
except Exception:  # pragma: no cover - optional dependency on Windows
    Dispatch = None

APP_NAME = "OpenKeyFlow"
ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"
ACTIVE_ICON_PATH = ASSETS_DIR / "OpenKeyFlow_active.ico"
IDLE_ICON_PATH = ASSETS_DIR / "OpenKeyFlow_idle.ico"


class HotkeyFilter(QtCore.QSortFilterProxyModel):
    def __init__(self) -> None:
        super().__init__()
        self.query = ""

    def setQuery(self, text: str) -> None:  # noqa: N802 (Qt naming)
        self.query = text.lower()
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QtCore.QModelIndex) -> bool:  # noqa: N802
        if not self.query:
            return True
        model = self.sourceModel()
        key_idx = model.index(source_row, 0, source_parent)
        val_idx = model.index(source_row, 1, source_parent)
        trigger = (model.data(key_idx, QtCore.Qt.DisplayRole) or "").lower()
        output = (model.data(val_idx, QtCore.Qt.DisplayRole) or "").lower()
        return self.query in trigger or self.query in output


def make_status_icon(enabled: bool) -> QtGui.QIcon:

    color = QtGui.QColor("#2ecc71" if enabled else "#e74c3c")
    
    pixmap = QtGui.QPixmap(64, 64)
    pixmap.fill(QtCore.Qt.transparent)

    painter = QtGui.QPainter(pixmap)
    painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

    painter.setPen(QtCore.Qt.NoPen)
    painter.setBrush(color)
    painter.drawEllipse(8, 8, 48, 48)
    painter.end()

    return QtGui.QIcon(pixmap)
    img = Image.new("RGB", (64, 64), "white")
    draw = ImageDraw.Draw(img)
    draw.rectangle((8, 8, 56, 56), fill="lightgray", outline="black")
    try:
        font = ImageFont.load_default()
    except Exception:  # pragma: no cover
        font = None
    draw.text((20, 22), "KF", fill="black", font=font)
    qimg = QtGui.QImage(img.tobytes(), img.size[0], img.size[1], QtGui.QImage.Format_RGB888)
    pix = QtGui.QPixmap.fromImage(qimg)
    return QtGui.QIcon(pix)


def set_app_palette(dark: bool) -> None:
    app = QtWidgets.QApplication.instance()
    if not app:
        return

    palette = QtGui.QPalette()
    if dark:
        palette.setColor(QtGui.QPalette.Window, QtGui.QColor(30, 30, 30))
        palette.setColor(QtGui.QPalette.WindowText, QtCore.Qt.white)
        palette.setColor(QtGui.QPalette.Base, QtGui.QColor(37, 37, 38))
        palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(45, 45, 48))
        palette.setColor(QtGui.QPalette.ToolTipBase, QtCore.Qt.white)
        palette.setColor(QtGui.QPalette.ToolTipText, QtCore.Qt.white)
        palette.setColor(QtGui.QPalette.Text, QtCore.Qt.white)
        palette.setColor(QtGui.QPalette.Button, QtGui.QColor(0, 0, 0))
        palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor(255, 51, 51))
        palette.setColor(QtGui.QPalette.PlaceholderText, QtGui.QColor(255, 120, 120))
        palette.setColor(QtGui.QPalette.BrightText, QtGui.QColor(224, 224, 224))
        palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(0, 122, 204))
        palette.setColor(QtGui.QPalette.HighlightedText, QtCore.Qt.white)
        app.setPalette(palette)  
        app.setStyleSheet(
            """
            QPushButton {
                background-color: black;
                color: rgb(255, 51, 51);
            }
            QPushButton:disabled {
                background-color: rgb(45, 45, 45);
                color: rgba(255, 51, 51, 140);
            }
            QLineEdit, QPlainTextEdit, QTextEdit {
                background-color: black;
                color: rgb(255, 51, 51);
                selection-background-color: rgb(80, 80, 80);
                selection-color: white;
            }
            QLineEdit:disabled, QPlainTextEdit:disabled, QTextEdit:disabled {
                background-color: rgb(45, 45, 45);
                color: rgba(255, 51, 51, 140);
            }
            """
        )
    else:
        app.setPalette(palette)
        app.setStyleSheet("")


def startup_shortcut_path() -> Path:
    appdata = Path(os.environ.get("APPDATA", ""))
    startup_dir = appdata / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    return startup_dir / f"{APP_NAME}.lnk"


def toggle_autostart(parent: QtWidgets.QWidget) -> None:
    if Dispatch is None:
        QtWidgets.QMessageBox.warning(parent, "Autostart", "pywin32 is not available on this system.")
        return
    shortcut = startup_shortcut_path()
    if shortcut.exists():
        try:
            shortcut.unlink()
            QtWidgets.QMessageBox.information(parent, "Autostart", "Autostart disabled.")
        except Exception as exc:  # pragma: no cover - Windows only
            QtWidgets.QMessageBox.warning(parent, "Autostart", f"Failed to remove shortcut:\n{exc}")
    else:
        try:
            shortcut.parent.mkdir(parents=True, exist_ok=True)
            shell = Dispatch("WScript.Shell")
            link = shell.CreateShortcut(str(shortcut))
            link.TargetPath = str(Path(sys.executable))
            script_path = Path(__file__).resolve().parent / "main.py"
            link.Arguments = str(script_path)
            link.WorkingDirectory = str(Path(__file__).resolve().parent)
            link.IconLocation = link.TargetPath
            link.save()
            QtWidgets.QMessageBox.information(parent, "Autostart", "Autostart enabled.")
        except Exception as exc:  # pragma: no cover
            QtWidgets.QMessageBox.warning(parent, "Autostart", f"Failed to create shortcut:\n{exc}")


class SpecialAddDialog(QtWidgets.QDialog):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Special Add")
        self.setModal(True)

        layout = QtWidgets.QVBoxLayout(self)
        instructions = QtWidgets.QLabel(
            "Enter a trigger and multi-line output. The trigger cannot contain spaces."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        form_layout = QtWidgets.QFormLayout()
        self.trigger_edit = QtWidgets.QLineEdit()
        self.trigger_edit.setPlaceholderText("Trigger (no spaces)")
        form_layout.addRow("Trigger:", self.trigger_edit)

        self.output_edit = QtWidgets.QPlainTextEdit()
        self.output_edit.setPlaceholderText("Expansion output (supports multiple lines)")
        self.output_edit.setMinimumHeight(160)
        form_layout.addRow("Output:", self.output_edit)
        layout.addLayout(form_layout)

        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self) -> tuple[str, str]:
        return self.trigger_edit.text(), self.output_edit.toPlainText()

    def accept(self) -> None:  # noqa: D401 - inherited docs
        trigger = self.trigger_edit.text().strip()
        output = self.output_edit.toPlainText()
        if not trigger or not output.strip():
            QtWidgets.QMessageBox.warning(self, "Special Add", "Trigger and output are required.")
            return
        if " " in trigger:
            QtWidgets.QMessageBox.warning(self, "Special Add", "Triggers cannot contain spaces.")
            return
        self.trigger_edit.setText(trigger)
        super().accept()


class MainWindow(QtWidgets.QMainWindow):
    updateCounters = QtCore.pyqtSignal()

    def __init__(self, engine: TriggerEngine) -> None:
        super().__init__()
        self.engine = engine
        self.hotkeys: Dict[str, str] = storage.load_hotkeys()
        self.config = storage.load_config()
        self.dark_mode = bool(self.config.get("dark_mode", False))
        self.enabled = True
        self.hotkey_lock = threading.RLock()

        self.engine.set_cooldown(float(self.config.get("cooldown", 0.3)))
        self.engine.set_paste_delay(float(self.config.get("paste_delay", 0.05)))
        self.engine.update_hotkeys(self.hotkeys)

        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(760, 480)

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)

        input_row = QtWidgets.QHBoxLayout()
        self.key_edit = QtWidgets.QLineEdit()
        self.key_edit.setPlaceholderText("Hotkey trigger")
        self.value_edit = QtWidgets.QLineEdit()
        self.value_edit.setPlaceholderText("Expansion output")
        add_btn = QtWidgets.QPushButton("Add")
        delete_btn = QtWidgets.QPushButton("Delete Selected")
        import_btn = QtWidgets.QPushButton("Import CSV")
        export_btn = QtWidgets.QPushButton("Export CSV")
        autostart_btn = QtWidgets.QPushButton("Toggle Autostart")

        add_btn.clicked.connect(self.add_hotkey)
        delete_btn.clicked.connect(self.delete_selected)
        import_btn.clicked.connect(self.import_csv)
        export_btn.clicked.connect(self.export_csv)
        autostart_btn.clicked.connect(lambda: toggle_autostart(self))
        self.key_edit.returnPressed.connect(self._handle_return_pressed)
        self.value_edit.returnPressed.connect(self._handle_return_pressed)

        input_row.addWidget(QtWidgets.QLabel("Hotkey:"))
        input_row.addWidget(self.key_edit, 1)
        input_row.addWidget(QtWidgets.QLabel("→"))
        input_row.addWidget(self.value_edit, 2)
        input_row.addWidget(add_btn)
        input_row.addWidget(delete_btn)
        input_row.addWidget(import_btn)
        input_row.addWidget(export_btn)
        input_row.addWidget(autostart_btn)
        layout.addLayout(input_row)

        search_row = QtWidgets.QHBoxLayout()
        self.search_edit = QtWidgets.QLineEdit()
        self.search_edit.setPlaceholderText("Search triggers or outputs…")
        search_row.addWidget(self.search_edit, 1)

        self.theme_btn = QtWidgets.QPushButton("Toggle Dark Mode")
        self.theme_btn.clicked.connect(self.toggle_theme)
        search_row.addWidget(self.theme_btn)
        layout.addLayout(search_row)

        self.model = QtGui.QStandardItemModel(0, 2, self)
        self.model.setHorizontalHeaderLabels(["Hotkey", "Output"])
        self.populate_model()

        self.proxy = HotkeyFilter()
        self.proxy.setSourceModel(self.model)

        self.table = QtWidgets.QTableView()
        self.table.setModel(self.proxy)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table, 1)

        self._apply_table_header_theme()

        bottom_row = QtWidgets.QHBoxLayout()
        donate_btn = QtWidgets.QPushButton("Donate")
        donate_btn.setFixedSize(75, 20)
        donate_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        donate_btn.clicked.connect(
            lambda: QtGui.QDesktopServices.openUrl(QtCore.QUrl("https://buymeacoffee.com/exoteriklabs"))
        )
        github_btn = QtWidgets.QPushButton("GitHub")
        github_btn.setFixedSize(75, 20)
        github_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        github_btn.clicked.connect(
            lambda: QtGui.QDesktopServices.openUrl(QtCore.QUrl("https://github.com/exoteriklabs"))
        )

        help_btn = QtWidgets.QPushButton("Help")
        help_btn.setFixedSize(75, 20)
        help_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        help_btn.clicked.connect(
            lambda: QtGui.QDesktopServices.openUrl(
                QtCore.QUrl("https://github.com/exoteriklabs/openkeyflow/main/README.md")
            )
        )


        bottom_row.addWidget(donate_btn)
        bottom_row.addWidget(github_btn)
        bottom_row.addWidget(help_btn)
        bottom_row.addSpacing(16)

        bottom_row.addWidget(QtWidgets.QLabel("Status:"))
        self.status_dot = QtWidgets.QLabel()
        self.status_dot.setFixedSize(16, 16)
        bottom_row.addWidget(self.status_dot)
        bottom_row.addStretch(1)

        self.hotkey_count_label = QtWidgets.QLabel()
        self.fired_count_label = QtWidgets.QLabel()
        bottom_row.addWidget(self.hotkey_count_label)
        bottom_row.addWidget(self.fired_count_label)

        self.toggle_btn = QtWidgets.QPushButton("Disable")
        self.toggle_btn.clicked.connect(self.toggle_enabled)
        bottom_row.addWidget(self.toggle_btn)

        layout.addLayout(bottom_row)

        self.search_edit.textChanged.connect(self.proxy.setQuery)
        self.tray: QtWidgets.QSystemTrayIcon | None = None
        self.refresh_status_ui()

        self.counter_timer = QtCore.QTimer(self)
        self.counter_timer.setInterval(300)
        self.counter_timer.timeout.connect(self.refresh_counters_only)
        self.counter_timer.start()

        self.tray = QtWidgets.QSystemTrayIcon(self)
        self.tray.setIcon(make_status_icon(self.enabled))
        tray_menu = QtWidgets.QMenu()
        tray_menu.addAction("Toggle Enabled", self.toggle_enabled)
        tray_menu.addSeparator()
        tray_menu.addAction("Show/Hide", self.toggle_window_visibility)
        tray_menu.addAction("Quit", self.quit_app)
        self.tray.setContextMenu(tray_menu)
        self.tray.activated.connect(self._tray_activated)
        self.tray.setToolTip(APP_NAME)
        self.tray.show()

        keyboard.add_hotkey("ctrl+f12", self.toggle_enabled)
        self._was_hidden_to_tray = False

        set_app_palette(self.dark_mode)
        self.update_theme_button_text()
        self._apply_table_header_theme()

    # ------------------------------------------------------------------
    # UI helpers
    # ------------------------------------------------------------------
    def populate_model(self) -> None:
        self.model.setRowCount(0)
        for trigger, output in self.hotkeys.items():
            items = [QtGui.QStandardItem(trigger), QtGui.QStandardItem(output)]
            self.model.appendRow(items)

    def refresh_status_ui(self) -> None:
        self.refresh_counters_only()
        pixmap = QtGui.QPixmap(16, 16)
        pixmap.fill(QtGui.QColor("#2ecc71" if self.enabled else "#e74c3c"))
        self.status_dot.setPixmap(pixmap)
        self.toggle_btn.setText("Disable" if self.enabled else "Enable")
        self.toggle_btn.setStyleSheet(
            "background-color: #2ecc71; color: black;"
            if self.enabled
            else "background-color: #e74c3c; color: #d9d9d9;"
        )
        if self.tray is not None:
            self.tray.setIcon(make_status_icon(self.enabled))

    def _apply_table_header_theme(self) -> None:
        header = self.table.horizontalHeader()
        if self.dark_mode:
            header.setStyleSheet(
                "QHeaderView::section { background-color: black; color: rgb(255, 51, 51); }"
            )
        else:
            header.setStyleSheet("")
            
    def _maybe_show_use_policy_prompt(self) -> None:
        if self.config.get("accepted_use_policy"):
            return

        msg = QtWidgets.QMessageBox(self)
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.setWindowTitle("Acceptable Use Policy")
        msg.setText(
            "OpenKeyFlow is intended for accessibility and productivity automation only."
        )
        msg.setInformativeText(
            "By clicking OK, you confirm you will operate OpenKeyFlow ethically and lawfully."
        )
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
        msg.setDefaultButton(QtWidgets.QMessageBox.Ok)
        result = msg.exec_()

        if result == QtWidgets.QMessageBox.Ok:
            self.config["accepted_use_policy"] = True
            storage.save_config(self.config)
        else:
            QtWidgets.QApplication.instance().quit()

    def refresh_counters_only(self) -> None:
        fired = self.engine.get_stats()["fired"]
        self.hotkey_count_label.setText(f"Hotkeys: {len(self.hotkeys)}")
        self.fired_count_label.setText(f"Fired: {fired}")

    def update_theme_button_text(self) -> None:
        self.theme_btn.setText("Dark Mode" if not self.dark_mode else "Light Mode")

    def toggle_window_visibility(self) -> None:
        if self.isVisible():
            self.hide()
            self._was_hidden_to_tray = True
        else:
            self.showNormal()
            self.activateWindow()
            self.raise_()

    def _handle_return_pressed(self) -> None:
        trigger = self.key_edit.text()
        output = self.value_edit.text()
        if trigger and output:
            self.add_hotkey()
        elif not trigger and not output:
            self.open_special_add()
        elif not trigger:
            self.key_edit.setFocus()
        else:
            self.value_edit.setFocus()

    def _tray_activated(self, reason: QtWidgets.QSystemTrayIcon.ActivationReason) -> None:
        if reason == QtWidgets.QSystemTrayIcon.Trigger:
            self.toggle_window_visibility()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:  # noqa: N802
        if self._was_hidden_to_tray:
            event.accept()
            return
        self.hide()
        self._was_hidden_to_tray = True
        event.ignore()

    def quit_app(self) -> None:
        try:
            keyboard.remove_hotkey("ctrl+f12")
        except Exception:
            pass
        QtWidgets.QApplication.instance().quit()

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def add_hotkey(self) -> None:
        trigger = self.key_edit.text()
        output = self.value_edit.text()
        if not trigger and not output:
            self.open_special_add()
            return
        if not trigger or not output:
            QtWidgets.QMessageBox.warning(self, "Add Hotkey", "Both trigger and output are required.")
            return
        if self._add_hotkey(trigger, output):
            self.key_edit.clear()
            self.value_edit.clear()

    def open_special_add(self) -> None:
        dialog = SpecialAddDialog(self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            trigger, output = dialog.get_data()
            self._add_hotkey(trigger, output)

    def _add_hotkey(self, trigger: str, output: str) -> bool:
        normalized_trigger = trigger.strip()
        if not normalized_trigger:
            QtWidgets.QMessageBox.warning(self, "Add Hotkey", "Trigger is required.")
            return False
        if " " in normalized_trigger:
            QtWidgets.QMessageBox.warning(self, "Add Hotkey", "Triggers cannot contain spaces.")
            return False
        if not output:
            QtWidgets.QMessageBox.warning(self, "Add Hotkey", "Output is required.")
            return False

        with self.hotkey_lock:
            if normalized_trigger in self.hotkeys:
                QtWidgets.QMessageBox.warning(self, "Add Hotkey", "Trigger already exists.")
                return False
            overlaps = [
                existing
                for existing in self.hotkeys
                if existing != normalized_trigger
                and (existing.startswith(normalized_trigger) or normalized_trigger.startswith(existing))
            ]

        if overlaps:
            overlaps_text = "\n".join(f"• {name}" for name in overlaps)
            response = QtWidgets.QMessageBox.question(
                self,
                "Potential Conflict",
                (
                    "This trigger overlaps with existing ones and may cause unreliable expansions.\n\n"
                    f"Existing overlaps:\n{overlaps_text}\n\n"
                    "Do you want to add it anyway?"
                ),
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No,
            )
            if response != QtWidgets.QMessageBox.Yes:
                return False

        with self.hotkey_lock:
            if normalized_trigger in self.hotkeys:
                QtWidgets.QMessageBox.warning(self, "Add Hotkey", "Trigger already exists.")
                return False
            self.hotkeys[normalized_trigger] = output

        storage.save_hotkeys(self.hotkeys)
        self.engine.update_hotkeys(self.hotkeys)
        self.populate_model()
        self.refresh_status_ui()
        return True

    def delete_selected(self) -> None:
        selection = self.table.selectionModel().selectedRows()
        if not selection:
            return
        to_delete = []
        for index in selection:
            source = self.proxy.mapToSource(index)
            trigger = self.model.item(source.row(), 0).text()
            to_delete.append(trigger)
        if not to_delete:
            return
        with self.hotkey_lock:
            for trigger in to_delete:
                self.hotkeys.pop(trigger, None)
        storage.save_hotkeys(self.hotkeys)
        self.engine.update_hotkeys(self.hotkeys)
        self.populate_model()
        self.refresh_status_ui()

    def import_csv(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Import CSV", "", "CSV Files (*.csv)")
        if not path:
            return
        added = 0
        with self.hotkey_lock:
            for trigger, output in storage.import_hotkeys_from_csv(Path(path)):
                self.hotkeys[trigger] = output
                added += 1
        storage.save_hotkeys(self.hotkeys)
        self.engine.update_hotkeys(self.hotkeys)
        self.populate_model()
        self.refresh_status_ui()
        QtWidgets.QMessageBox.information(self, "Import", f"Imported {added} hotkeys.")

    def export_csv(self) -> None:
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Export CSV", "", "CSV Files (*.csv)")
        if not path:
            return
        storage.export_hotkeys_to_csv(Path(path), self.hotkeys)
        QtWidgets.QMessageBox.information(self, "Export", f"Exported {len(self.hotkeys)} hotkeys.")

    def toggle_enabled(self) -> None:
        self.enabled = self.engine.toggle_enabled()
        self.refresh_status_ui()

    def toggle_theme(self) -> None:
        self.dark_mode = not self.dark_mode
        set_app_palette(self.dark_mode)
        self.update_theme_button_text()
        self._apply_table_header_theme()
        self.config["dark_mode"] = self.dark_mode
        storage.save_config(self.config)
