from PyQt5.QtGui import QTextCharFormat, QSyntaxHighlighter, QColor, QFont
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatter import Formatter
from pygments.styles import get_style_by_name
from pygments.token import Token

class PygmentsFormatter(Formatter):
    def __init__(self, highlighter, style_name='monokai'):
        super().__init__()
        self.highlighter = highlighter
        self.style = get_style_by_name(style_name)
        self.formats = {}

        # Crea QTextCharFormat per ogni tipo di token
        for token, style in self.style:
            text_format = QTextCharFormat()
            if style['color']:
                text_format.setForeground(QColor(f'#{style["color"]}'))
            if style['bold']:
                text_format.setFontWeight(QFont.Bold)
            if style['italic']:
                text_format.setFontItalic(True)
            self.formats[token] = text_format

    def format(self, tokensource, outfile):
        for ttype, value in tokensource:
            text_format = self.formats.get(ttype, QTextCharFormat())
            start = self.highlighter.current_block_position
            length = len(value)
            self.highlighter.setFormat(start, length, text_format)
            self.highlighter.current_block_position += length

class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, document, style_name='monokai'):
        super().__init__(document)
        self.lexer = PythonLexer()
        self.formatter = PygmentsFormatter(self, style_name)

    def highlightBlock(self, text):
        self.current_block_position = 0
        highlight(text, self.lexer, self.formatter)