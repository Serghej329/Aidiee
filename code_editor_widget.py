from pygments.styles import get_style_by_name
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtGui import QFont
from neumorphic_widgets import NeumorphicWidget, NeumorphicTextEdit
from syntax_highlighting import PythonHighlighter

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

    def set_style(self, style_name):
        self.highlighter = PythonHighlighter(self.code_editor.document(), style_name=style_name)
        style = get_style_by_name(style_name)
        background_color = style.background_color
        default_color = style.highlight_color
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
