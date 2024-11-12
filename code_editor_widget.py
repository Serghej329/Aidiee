from pygments.styles import get_style_by_name
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PyQt5.QtGui import QFont,QColor
from PyQt5.QtCore import QTimer
from neumorphic_widgets import NeumorphicWidget, NeumorphicTextEdit
from syntax_highlighting import PythonHighlighter
from line_numbers import LineNumbers

class CodeEditorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.code_editor = NeumorphicTextEdit()
        self.code_editor.setFont(QFont("Fira Code", 12))
        self.highlighter = PythonHighlighter(self.code_editor.document())
        layout.addWidget(self.code_editor)
        self.setLayout(layout)

        # Apply neumorphic style to the CodeEditorWidget
        self.setStyleSheet("""
            background-color: #2C2D3A;
            border-radius: 10px;
            padding: 10px;
        """)

        # Add line numbers
        self.line_numbers = LineNumbers(self.code_editor)
        editor_layout = QHBoxLayout()
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.addWidget(self.line_numbers)
        editor_layout.addWidget(self.code_editor)
        layout.addLayout(editor_layout)

    def set_style(self, style_name):
        self.highlighter = PythonHighlighter(self.code_editor.document(), style_name=style_name)
        style = get_style_by_name(style_name)
        background_color = style.background_color
        default_color = style.highlight_color
        highlight_color = QColor(210, 225, 255)
        self.code_editor.setStyleSheet("""
            QTextEdit {
                background-color: #272822;  /* Monokai background */
                color: #f8f8f2;            /* Monokai default text */
                border-radius: 10px;
                padding: 10px;
                selection-background-color: #49483e;  /* Monokai selection */
                selection-color: #f8f8f2;
                font-family: 'Fira Code', 'Consolas', monospace;
            }

            QTextEdit:focus {
                border: 1px solid #49483e;
            }
        """)
        self.line_numbers.highlight_color = QColor(default_color)
        self.line_numbers.line_number_color = highlight_color

    def blinkLine(self, line_number, blink_color):
        self.line_numbers.goToLine(line_number)
        self.line_numbers.highlightLine(line_number, blink_color)
        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(lambda: self.toggleBlink(line_number, blink_color))
        self.blink_timer.start(500)  # Blink every 500ms

    def toggleBlink(self, line_number, blink_color):
        current_color = self.line_numbers.getLineContent(line_number)
        if current_color == blink_color:
            self.line_numbers.highlightLine(line_number, QColor("#272822"))  # Reset to background color
        else:
            self.line_numbers.highlightLine(line_number, blink_color)