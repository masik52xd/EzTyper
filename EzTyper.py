import sys
import os
import json
import random
import webbrowser
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPlainTextEdit, QTextEdit, QLabel, QPushButton, QTabWidget, QDialog, QFormLayout,
    QSpinBox, QComboBox, QCheckBox, QFrame, QMessageBox
)
from PyQt6.QtGui import QFont, QColor, QPalette, QShortcut, QKeySequence, QPainter
from PyQt6.QtCore import Qt, QTimer, QRect, QSize

# Файл для автоматичного збереження сесії
SESSION_FILE = "session_restore.json"

# Словник доступних тем інтерфейсу
THEMES = {
    "Deep Purple (Original)": {
        "BG": "#0c0714", "CARD": "#150d22", "TEXT": "#e3def2", "MUTED": "#8e869c", "ACCENT": "#7a4bf5"
    },
    "Cyber Midnight (Neon)": {
        "BG": "#071114", "CARD": "#0e2025", "TEXT": "#bbf7fc", "MUTED": "#5f9599", "ACCENT": "#00ffcc"
    },
    "Nordic Dark": {
        "BG": "#2e3440", "CARD": "#3b4252", "TEXT": "#eceff4", "MUTED": "#8e9bb0", "ACCENT": "#88c0d0"
    },
    "Light Mint": {
        "BG": "#f4f7f6", "CARD": "#ffffff", "TEXT": "#2c3e50", "MUTED": "#7f8c8d", "ACCENT": "#2ecc71"
    }
}

# Шаблони для генератора ідей
IDEAS_TEMPLATES = [
    ("Огляд RTX 5050 у 2026", "# Нове народне рішення?\n\nІтак, сьогодні ми поговоримо про *RTX 5050*.\n\n## Характеристики:\n* **Пам'ять:** 8 GB GDDR7\n* **Шина:** 128 bit\n\nЧи варто переплачувати? Давайте розбиратись."),
    ("Історія Mac OS", "# Чому Apple змінила світ?\n\n**Mac OS** пройшла довгий шлях від першої системи до сучасної *macOS Sequoia*.\n\n## Етапи розвитку:\n1. Ера NeXTSTEP\n2. Повернення Джобса\n3. Сучасна екосистема"),
    ("Топ девайсів до $100", "# "
                             "Крутий сетап за копійки\n\nМи підібрали найкращі пристрої, які суттєво покращать ваше життя:\n\n* **Клавіатура:** Механічна 75%\n* **Звук:** USB-мікрофон з пантографом"),
    ("Як оптимізувати ОС", "# Збільшуємо FPS за 5 хвилин\n\nНе вірте міфам про оптимізацію! Ось **реально дієві** кроки:\n\n1. Налаштування схеми живлення\n2. Вимкнення фонового сміття"),
    ("Мій робочий сетап", "# Робоче місце блогера\n\nОсь із чого складається мій сетап:\n\n* *Монітор:* 27 дюймів IPS\n* *Світло:* Кільцева лампа\n* *Крісло:* Ергономічне")
]

class LineNumberArea(QWidget):
    """Область ліворуч від редактора для малювання номерів рядків."""
    def __init__(self, editor):
        super().__init__(editor)
        self.codeEditor = editor

    def sizeHint(self):
        return QSize(self.codeEditor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.codeEditor.lineNumberAreaPaintEvent(event)

class CustomCodeEditor(QPlainTextEdit):
    """Професійний редактор коду з підримкою номерів рядків."""
    def __init__(self, parent_window, parent=None):
        super().__init__(parent)
        self.parent_window = parent_window
        self.lineNumberArea = LineNumberArea(self)

        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)

        self.updateLineNumberAreaWidth(0)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)

        # Комфортний моноширинний чи системний шрифт
        font = QFont("Consolas", 12)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)

    def lineNumberAreaWidth(self):
        digits = 1
        max_b = max(1, self.blockCount())
        while max_b >= 10:
            max_b /= 10
            digits += 1
        # Визначаємо ширину залежно від кількості розрядів цифр
        space = 15 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.lineNumberArea)
        
        # Визначаємо колір відповідно до поточної теми програми
        theme = THEMES[self.parent_window.current_theme_name]
        bg_color = QColor(theme['CARD'])
        text_color = QColor(theme['MUTED'])
        
        painter.fillRect(event.rect(), bg_color)

        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        painter.setFont(self.font())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                painter.setPen(text_color)
                # Малюємо номери рядків із вирівнюванням праворуч
                painter.drawText(0, int(top), self.lineNumberArea.width() - 8, self.fontMetrics().height(),
                                 Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, number)

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            blockNumber += 1

class PreviewWindow(QWidget):
    """Окреме вікно для попереднього перегляду Markdown-форматування."""
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Window)
        self.parent_window = parent
        self.setWindowTitle("Попередній перегляд (Markdown)")
        self.resize(550, 700)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        self.text_preview = QTextEdit()
        self.text_preview.setReadOnly(True)
        layout.addWidget(self.text_preview)
        
        self.apply_theme()
        
    def apply_theme(self):
        if not self.parent_window:
            return
        theme = THEMES[self.parent_window.current_theme_name]
        font_size = self.parent_window.preview_font_size
        
        self.setStyleSheet(f"background-color: {theme['BG']};")
        self.text_preview.setStyleSheet(f"""
            QTextEdit {{
                background-color: {theme['CARD']};
                color: {theme['TEXT']};
                border: 1px solid {theme['MUTED']};
                border-radius: 6px;
                font-size: {font_size}px;
                line-height: 1.6;
                padding: 20px 25px; /* Комфортні внутрішні відступи в прев'ю */
            }}
        """)
        
    def update_content(self, text):
        """Рендерить текст із використанням правил Markdown."""
        lines = text.split('\n')
        processed_lines = []
        for line in lines:
            # Якщо це заголовок Markdown або порожній рядок — не додаємо пробіли
            if line.strip().startswith('#') or not line.strip():
                processed_lines.append(line)
            else:
                # Додаємо два пробіли в кінець звичайних рядків, щоб зберегти поодинокі переноси
                processed_lines.append(line + "  ")
        
        processed_text = "\n".join(processed_lines)
        self.text_preview.setMarkdown(processed_text)
        
    def closeEvent(self, event):
        if self.parent_window:
            self.parent_window.preview_window = None
        event.accept()

class SettingsDialog(QDialog):
    """Вікно налаштувань програми."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Налаштування EzTyper")
        self.resize(500, 500)
        
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        # Налаштування фокусу
        self.spin_margin_side = QSpinBox()
        self.spin_margin_side.setRange(0, 400)
        self.spin_margin_side.setValue(self.parent.margin_side)
        self.spin_margin_side.valueChanged.connect(self.update_margins)
        
        self.spin_margin_top = QSpinBox()
        self.spin_margin_top.setRange(0, 200)
        self.spin_margin_top.setValue(self.parent.margin_top)
        self.spin_margin_top.valueChanged.connect(self.update_margins)

        self.spin_margin_bottom = QSpinBox()
        self.spin_margin_bottom.setRange(0, 200)
        self.spin_margin_bottom.setValue(self.parent.margin_bottom)
        self.spin_margin_bottom.valueChanged.connect(self.update_margins)

        form_layout.addRow(QLabel("Відступ по боках (px):"), self.spin_margin_side)
        form_layout.addRow(QLabel("Відступ зверху (px):"), self.spin_margin_top)
        form_layout.addRow(QLabel("Відступ знизу (px):"), self.spin_margin_bottom)
        
        # Вибір теми
        self.combo_theme = QComboBox()
        self.combo_theme.addItems(list(THEMES.keys()))
        self.combo_theme.setCurrentText(self.parent.current_theme_name)
        self.combo_theme.currentTextChanged.connect(self.change_theme)
        form_layout.addRow(QLabel("Тема оформлення:"), self.combo_theme)
        
        # Розрахунок часу
        self.combo_time_mode = QComboBox()
        self.combo_time_mode.addItems([
            "Примерное время чтения",
            "Примерное время чтения вслух",
            "Примерное время письма неспеша",
            "Примерное время письма в спешке"
        ])
        self.combo_time_mode.setCurrentIndex(self.parent.time_mode_index)
        self.combo_time_mode.currentIndexChanged.connect(self.update_time_mode)
        form_layout.addRow(QLabel("Розрахунок часу:"), self.combo_time_mode)
        
        # Налаштування прев'ю
        self.chk_auto_preview = QCheckBox("Оновлювати в живому часі")
        self.chk_auto_preview.setChecked(self.parent.preview_auto_update)
        self.chk_auto_preview.stateChanged.connect(self.update_preview_settings)
        
        self.spin_preview_font = QSpinBox()
        self.spin_preview_font.setRange(10, 36)
        self.spin_preview_font.setValue(self.parent.preview_font_size)
        self.spin_preview_font.valueChanged.connect(self.update_preview_settings)
        
        form_layout.addRow(QLabel("Живе прев'ю (F5):"), self.chk_auto_preview)
        form_layout.addRow(QLabel("Шрифт прев'ю (px):"), self.spin_preview_font)
        
        layout.addLayout(form_layout)
        
        # Блок "Про автора"
        author_frame = QFrame()
        author_frame.setObjectName("AuthorFrame")
        author_layout = QVBoxLayout(author_frame)
        
        lbl_author = QLabel("Розробник: mwkdev")
        lbl_author.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        btn_website = QPushButton("Перейти на сайт: mwkdev.pp.ua")
        btn_website.clicked.connect(self.open_developer_site)
        
        author_layout.addWidget(lbl_author)
        author_layout.addWidget(btn_website)
        layout.addWidget(author_frame)
        
        btn_close = QPushButton("Закрити")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignRight)
        
        self.apply_dialog_theme()

    def update_margins(self):
        self.parent.margin_side = self.spin_margin_side.value()
        self.parent.margin_top = self.spin_margin_top.value()
        self.parent.margin_bottom = self.spin_margin_bottom.value()
        self.parent.apply_layout_margins()

    def change_theme(self, theme_name):
        self.parent.current_theme_name = theme_name
        self.parent.apply_theme()
        self.apply_dialog_theme()

    def update_time_mode(self, index):
        self.parent.time_mode_index = index
        self.parent.update_statistics()

    def update_preview_settings(self):
        self.parent.preview_auto_update = self.chk_auto_preview.isChecked()
        self.parent.preview_font_size = self.spin_preview_font.value()
        if self.parent.preview_window:
            self.parent.preview_window.apply_theme()
            self.parent.update_preview_live()

    def open_developer_site(self):
        webbrowser.open("https://mwkdev.pp.ua")

    def apply_dialog_theme(self):
        theme = THEMES[self.parent.current_theme_name]
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {theme['BG']};
                color: {theme['TEXT']};
            }}
            QLabel {{
                color: {theme['TEXT']};
                font-size: 13px;
            }}
            QSpinBox, QComboBox {{
                background-color: {theme['CARD']};
                color: {theme['TEXT']};
                border: 1px solid {theme['MUTED']};
                border-radius: 4px;
                padding: 4px;
            }}
            QCheckBox {{
                color: {theme['TEXT']};
            }}
            QFrame#AuthorFrame {{
                background-color: {theme['CARD']};
                border: 1px solid {theme['MUTED']};
                border-radius: 6px;
                margin-top: 15px;
                padding: 10px;
            }}
            QPushButton {{
                background-color: {theme['CARD']};
                color: {theme['TEXT']};
                border: 1px solid {theme['MUTED']};
                border-radius: 4px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                border-color: {theme['ACCENT']};
            }}
        """)

class EzTyperClone(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EzTyper - Python Edition")
        self.resize(1150, 750)
        
        # Налаштування за замовчуванням (зменшили боковий відступ до комфортних 80)
        self.margin_side = 80
        self.margin_top = 20
        self.margin_bottom = 20
        self.time_mode_index = 1
        self.current_theme_name = "Deep Purple (Original)"
        
        # Налаштування прев'ю
        self.preview_window = None
        self.preview_auto_update = True
        self.preview_font_size = 16
        
        # Змінні таймера Pomodoro
        self.pomodoro_timer = QTimer(self)
        self.pomodoro_timer.timeout.connect(self.tick_pomodoro)
        self.pomodoro_time_left = 0
        self.pomodoro_active = False
        
        # Таймер автозбереження
        self.autosave_timer = QTimer(self)
        self.autosave_timer.setSingleShot(True)
        self.autosave_timer.setInterval(1000)
        self.autosave_timer.timeout.connect(self.save_session)
        
        self.init_ui()
        self.apply_theme()
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. Верхня панель інструментів
        self.toolbar_layout = QHBoxLayout()
        self.toolbar_layout.setContentsMargins(15, 10, 15, 10)
        
        self.btn_open = QPushButton("Открыть")
        self.btn_save = QPushButton("Сохранить")
        self.btn_new_tab = QPushButton("Новая вкладка")
        
        self.btn_idea = QPushButton("💡 Ідея дня")
        self.btn_idea.clicked.connect(self.generate_random_idea)
        
        self.btn_pomodoro = QPushButton("⏱️ Помодоро: Вимк")
        self.btn_pomodoro.clicked.connect(self.toggle_pomodoro)
        
        self.btn_clean = QPushButton("🧹 Клінер")
        self.btn_clean.clicked.connect(self.clean_text)
        
        self.btn_settings = QPushButton("Настройки")
        
        self.toolbar_layout.addWidget(self.btn_open)
        self.toolbar_layout.addWidget(self.btn_save)
        self.toolbar_layout.addWidget(self.btn_new_tab)
        self.toolbar_layout.addWidget(self.btn_idea)
        self.toolbar_layout.addWidget(self.btn_pomodoro)
        self.toolbar_layout.addWidget(self.btn_clean)
        self.toolbar_layout.addStretch()
        self.toolbar_layout.addWidget(self.btn_settings)
        
        main_layout.addLayout(self.toolbar_layout)
        
        # 2. Статистика
        self.lbl_chars = QLabel("Символов: 0")
        self.lbl_words = QLabel("Слов: 0")
        self.lbl_paragraphs = QLabel("Абзацев: 0")
        self.lbl_lines = QLabel("Строк: 0")
        self.lbl_time = QLabel("Время чтения вслух: 0 мин.")
        
        self.status_bar = QHBoxLayout()
        self.status_bar.setContentsMargins(15, 5, 15, 5)
        
        for lbl in [self.lbl_chars, self.lbl_words, self.lbl_paragraphs, self.lbl_lines, self.lbl_time]:
            self.status_bar.addWidget(lbl)
            self.status_bar.addSpacing(15)
            
        self.status_bar.addStretch()
        
        # 3. Система вкладок (Таби)
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.update_statistics)
        self.tab_widget.currentChanged.connect(self.update_preview_live)
        self.tab_widget.currentChanged.connect(self.save_session)
        
        self.add_tab_btn = QPushButton("+")
        self.add_tab_btn.setObjectName("AddTabButton")
        self.add_tab_btn.setFixedSize(30, 25)
        self.add_tab_btn.clicked.connect(lambda: self.add_new_tab("Без имени"))
        self.tab_widget.setCornerWidget(self.add_tab_btn, Qt.Corner.TopRightCorner)
        
        main_layout.addWidget(self.tab_widget)
        main_layout.addLayout(self.status_bar)
        
        # Гарячі клавіші
        self.shortcut_new = QShortcut(QKeySequence("Ctrl+T"), self)
        self.shortcut_new.activated.connect(lambda: self.add_new_tab("Без имени"))
        
        self.shortcut_close = QShortcut(QKeySequence("Ctrl+W"), self)
        self.shortcut_close.activated.connect(lambda: self.close_tab(self.tab_widget.currentIndex()))
        
        self.shortcut_preview = QShortcut(QKeySequence("F5"), self)
        self.shortcut_preview.activated.connect(self.toggle_preview)
        
        self.btn_new_tab.clicked.connect(lambda: self.add_new_tab("Без имени"))
        self.btn_settings.clicked.connect(self.open_settings)
        
        # Відновлення сесії
        if not self.load_session():
            self.add_new_tab("Без имени", "Введіть ваш текст сюди...")
        
    def add_new_tab(self, title, content=""):
        container = QWidget()
        layout = QVBoxLayout(container)
        
        # Створюємо редактор із номерами рядків
        text_edit = CustomCodeEditor(self)
        text_edit.setPlainText(content)
        text_edit.textChanged.connect(self.update_statistics)
        text_edit.textChanged.connect(self.trigger_autosave)
        text_edit.textChanged.connect(self.update_preview_live)
        
        layout.addWidget(text_edit)
        container.setLayout(layout)
        
        container.text_edit = text_edit
        container.focus_layout = layout
        
        index = self.tab_widget.addTab(container, title)
        self.tab_widget.setCurrentIndex(index)
        self.apply_layout_margins()
        self.apply_theme_to_text_edit(text_edit)
        return index
        
    def close_tab(self, index):
        if self.tab_widget.count() > 1:
            self.tab_widget.removeTab(index)
            self.save_session()
        else:
            current_widget = self.tab_widget.currentWidget()
            if current_widget and hasattr(current_widget, 'text_edit'):
                current_widget.text_edit.clear()
                self.tab_widget.setTabText(0, "Без имени")
                self.save_session()
            
    def apply_layout_margins(self):
        for i in range(self.tab_widget.count()):
            container = self.tab_widget.widget(i)
            if hasattr(container, 'focus_layout'):
                container.focus_layout.setContentsMargins(
                    self.margin_side, self.margin_top, self.margin_side, self.margin_bottom
                )
                
    def open_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec()
        
    def trigger_autosave(self):
        self.autosave_timer.start()

    # --- Прев'ю (F5) ---
    def toggle_preview(self):
        if self.preview_window is None:
            self.preview_window = PreviewWindow(self)
            self.preview_window.show()
            self.force_update_preview()
        else:
            self.preview_window.close()
            self.preview_window = None

    def update_preview_live(self):
        if self.preview_window and self.preview_auto_update:
            self.force_update_preview()

    def force_update_preview(self):
        if self.preview_window:
            current_widget = self.tab_widget.currentWidget()
            if current_widget and hasattr(current_widget, 'text_edit'):
                text = current_widget.text_edit.toPlainText()
                self.preview_window.update_content(text)

    # --- Бурмалда утиліти ---
    def generate_random_idea(self):
        title, content = random.choice(IDEAS_TEMPLATES)
        self.add_new_tab(title, content)

    def clean_text(self):
        current_widget = self.tab_widget.currentWidget()
        if not current_widget or not hasattr(current_widget, 'text_edit'):
            return
            
        text_edit = current_widget.text_edit
        old_text = text_edit.toPlainText()
        
        lines = old_text.splitlines()
        cleaned_lines = []
        for line in lines:
            line = " ".join(line.split())
            cleaned_lines.append(line)
            
        new_text = "\n".join(cleaned_lines)
        while "\n\n\n" in new_text:
            new_text = new_text.replace("\n\n\n", "\n\n")
            
        text_edit.setPlainText(new_text.strip())

    def toggle_pomodoro(self):
        if self.pomodoro_active:
            self.pomodoro_timer.stop()
            self.pomodoro_active = False
            self.btn_pomodoro.setText("⏱️ Помодоро: Вимк")
        else:
            self.pomodoro_time_left = 25 * 60
            self.pomodoro_timer.start(1000)
            self.pomodoro_active = True
            self.update_pomodoro_display()

    def tick_pomodoro(self):
        if self.pomodoro_time_left > 0:
            self.pomodoro_time_left -= 1
            self.update_pomodoro_display()
        else:
            self.pomodoro_timer.stop()
            self.pomodoro_active = False
            self.btn_pomodoro.setText("⏱️ Помодоро: Готово!")
            QApplication.beep()
            QMessageBox.information(self, "Помодоро", "25 хвилин минуло! Час зробити перерву.")

    def update_pomodoro_display(self):
        mins = self.pomodoro_time_left // 60
        secs = self.pomodoro_time_left % 60
        self.btn_pomodoro.setText(f"⏱️ {mins:02d}:{secs:02d}")

    # --- Робота з файлом сесії ---
    def save_session(self):
        tabs_data = []
        for i in range(self.tab_widget.count()):
            container = self.tab_widget.widget(i)
            if hasattr(container, 'text_edit'):
                title = self.tab_widget.tabText(i)
                content = container.text_edit.toPlainText()
                tabs_data.append({
                    "title": title,
                    "content": content
                })
        
        session = {
            "tabs": tabs_data,
            "active_tab": self.tab_widget.currentIndex(),
            "theme": self.current_theme_name,
            "margin_side": self.margin_side,
            "margin_top": self.margin_top,
            "margin_bottom": self.margin_bottom,
            "time_mode_index": self.time_mode_index,
            "preview_auto_update": self.preview_auto_update,
            "preview_font_size": self.preview_font_size
        }
        
        try:
            with open(SESSION_FILE, "w", encoding="utf-8") as f:
                json.dump(session, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Помилка збереження сесії: {e}")

    def load_session(self):
        if os.path.exists(SESSION_FILE):
            try:
                with open(SESSION_FILE, "r", encoding="utf-8") as f:
                    session = json.load(f)
                
                self.current_theme_name = session.get("theme", "Deep Purple (Original)")
                if self.current_theme_name not in THEMES:
                    self.current_theme_name = "Deep Purple (Original)"
                self.margin_side = session.get("margin_side", 80)
                self.margin_top = session.get("margin_top", 20)
                self.margin_bottom = session.get("margin_bottom", 20)
                self.time_mode_index = session.get("time_mode_index", 1)
                
                self.preview_auto_update = session.get("preview_auto_update", True)
                self.preview_font_size = session.get("preview_font_size", 16)
                
                tabs = session.get("tabs", [])
                if tabs:
                    self.autosave_timer.blockSignals(True)
                    for tab in tabs:
                        self.add_new_tab(tab.get("title", "Без имени"), tab.get("content", ""))
                    
                    active_tab = session.get("active_tab", 0)
                    if 0 <= active_tab < self.tab_widget.count():
                        self.tab_widget.setCurrentIndex(active_tab)
                    
                    self.autosave_timer.blockSignals(False)
                    return True
            except Exception as e:
                print(f"Помилка відновлення сесії: {e}")
        return False

    def closeEvent(self, event):
        if self.preview_window:
            self.preview_window.close()
        self.save_session()
        event.accept()

    def update_statistics(self):
        current_widget = self.tab_widget.currentWidget()
        if not current_widget or not hasattr(current_widget, 'text_edit'):
            return
            
        text = current_widget.text_edit.toPlainText()
        
        current_index = self.tab_widget.currentIndex()
        if self.tab_widget.tabText(current_index) == "Без имени" and text.strip():
            first_words = " ".join(text.split()[:3])[:15]
            if first_words:
                self.tab_widget.setTabText(current_index, first_words)
        
        char_count = len(text)
        word_count = len(text.split()) if text.strip() else 0
        paragraph_count = len([p for p in text.split('\n') if p.strip()]) if text.strip() else 0
        line_count = text.count('\n') + 1 if text else 0
        
        self.lbl_chars.setText(f"Символов: {char_count}")
        self.lbl_words.setText(f"Слов: {word_count}")
        self.lbl_paragraphs.setText(f"Абзацев: {paragraph_count}")
        self.lbl_lines.setText(f"Строк: {line_count}")
        
        modes_info = [
            ("Время чтения", 230),
            ("Время чтения вслух", 150),
            ("Время письма неспеша", 20),
            ("Время письма в спешке", 35)
        ]
        
        mode_name, wpm = modes_info[self.time_mode_index]
        minutes = max(1, round(word_count / wpm)) if word_count > 0 else 0
        
        self.lbl_time.setText(f"{mode_name}: {minutes} мин.")

    def apply_theme_to_text_edit(self, text_edit):
        theme = THEMES[self.current_theme_name]
        text_edit.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: transparent;
                color: {theme['TEXT']};
                border: none;
                font-size: 16px;
                line-height: 1.5;
            }}
        """)
        # Примусово оновлюємо область номерів рядків для нової теми
        text_edit.lineNumberArea.update()

    def apply_theme(self):
        theme = THEMES[self.current_theme_name]
        
        for i in range(self.tab_widget.count()):
            container = self.tab_widget.widget(i)
            if hasattr(container, 'text_edit'):
                self.apply_theme_to_text_edit(container.text_edit)
                
        if self.preview_window:
            self.preview_window.apply_theme()
                
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {theme['BG']};
            }}
            QLabel {{
                color: {theme['TEXT']};
            }}
            QTabWidget::pane {{
                border: none;
                background-color: {theme['BG']};
            }}
            QTabBar::tab {{
                background-color: {theme['BG']};
                color: {theme['MUTED']};
                padding: 8px 16px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background-color: {theme['CARD']};
                color: {theme['TEXT']};
                border-bottom: 2px solid {theme['ACCENT']};
            }}
            QPushButton {{
                background-color: {theme['CARD']};
                color: {theme['TEXT']};
                border: 1px solid {theme['MUTED']};
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                border-color: {theme['ACCENT']};
            }}
            QPushButton#AddTabButton {{
                background-color: transparent;
                border: none;
                color: {theme['MUTED']};
                font-size: 18px;
                font-weight: bold;
                padding: 0;
            }}
            QPushButton#AddTabButton:hover {{
                color: {theme['TEXT']};
                background-color: {theme['CARD']};
                border-radius: 4px;
            }}
        """)
        
        for lbl in [self.lbl_chars, self.lbl_words, self.lbl_paragraphs, self.lbl_lines, self.lbl_time]:
            lbl.setStyleSheet(f"color: {theme['MUTED']}; font-size: 12px;")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EzTyperClone()
    window.show()
    sys.exit(app.exec())