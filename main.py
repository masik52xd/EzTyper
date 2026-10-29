import os
import sys
import webview  # pip install pywebview

try:
    OPEN, SAVE = webview.FileDialog.OPEN, webview.FileDialog.SAVE
except AttributeError:  # старіші версії pywebview
    OPEN, SAVE = webview.OPEN_DIALOG, webview.SAVE_DIALOG

FILTER = ("Text (*.txt;*.md;*.py;*.json)", "All files (*.*)")
HERE = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))


STATE = os.path.join(os.path.expanduser("~"), ".eztyper", "state.json")


def read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return {"name": os.path.basename(path), "path": path, "text": f.read()}


class Api:
    def load_state(self):
        try:
            with open(STATE, encoding="utf-8") as f:
                return f.read()
        except OSError:
            return None

    def save_state(self, data):
        os.makedirs(os.path.dirname(STATE), exist_ok=True)
        with open(STATE, "w", encoding="utf-8") as f:
            f.write(data)

    def startup(self):
        # файл, переданий через "Відкрити за допомогою"
        if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
            return read(sys.argv[1])

    def open_file(self):
        r = webview.windows[0].create_file_dialog(OPEN, file_types=FILTER)
        return read(r[0]) if r else None

    def save_file(self, name, text, path=None):
        if not path:
            r = webview.windows[0].create_file_dialog(SAVE, save_filename=name, file_types=FILTER)
            if not r:
                return None
            path = r if isinstance(r, str) else r[0]
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(text)
        return {"name": os.path.basename(path), "path": path}


webview.create_window("EzTyper", os.path.join(HERE, "index.html"), js_api=Api(), width=1100, height=720)
webview.start()
