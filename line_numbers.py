from PyQt5.QtWidgets import QWidget, QTextEdit, QPlainTextEdit, QVBoxLayout, QHBoxLayout, QSizePolicy
from PyQt5.QtGui import QPainter, QTextFormat, QColor, QFontMetrics, QTextCursor, QFont
from PyQt5.QtCore import Qt, QRect, QSize, QPoint

class LineNumbers(QWidget):
    def __init__(self,code_editor,parent=None ):
        super().__init__(code_editor)
        self.code_widget = parent
        self.code_editor = code_editor
        self.code_editor.blockCountChanged.connect(self.update_width)
        self.code_editor.updateRequest.connect(self.update_on_scroll)
        self.code_editor.cursorPositionChanged.connect(self.highlight_current_line)
        self.current_line_number_color = self.code_widget.selection_color  # Color for the current line number
        self.line_number_color = QColor("#f8f8f2")  # Default line number color
        
        # Set the font for the line numbers
        self.line_number_font = QFont("Fira Code")
        self.line_number_font.setBold(True)
        self.setFont(self.line_number_font)
        self.update_width(1)

    def update_width(self, block_count):
        width = self.fontMetrics().width(str(block_count)) + 10
        if self.width() != width:
            self.setFixedWidth(width)

    def update_on_scroll(self, rect, scroll):
        if scroll:
            self.scroll(0, scroll)
        else:
            self.update(0, rect.y(), self.width(), rect.height())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(event.rect(), QColor(self.code_widget.background_color))  # Background color
        block = self.code_editor.firstVisibleBlock()
        block_number = block.blockNumber()
        block_geometry = self.code_editor.blockBoundingGeometry(block).translated(self.code_editor.contentOffset())
        top = block_geometry.top()
        bottom = top + block_geometry.height()

        # Get the font metrics from the QPlainTextEdit
        font_metrics = self.code_editor.fontMetrics()
        line_height = font_metrics.height()

        # Get the top padding of the QPlainTextEdit
        top_padding = self.code_editor.contentsMargins().top()

        cursor = self.code_editor.textCursor()
        current_block_number = cursor.blockNumber()
        self.current_line_number_color = self.code_widget.selection_color  # Color for the current line number
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                if block_number == current_block_number:
                    painter.setPen(self.current_line_number_color)
                else:
                    painter.setPen(self.line_number_color)
                rect = QRect(0, int(top + top_padding + 4), self.width(), line_height)
                painter.drawText(rect, Qt.AlignRight, number)

            block = block.next()
            block_geometry = self.code_editor.blockBoundingGeometry(block).translated(self.code_editor.contentOffset())
            top = block_geometry.top()
            bottom = top + block_geometry.height()
            block_number += 1

    def highlight_current_line(self):
        extra_selections = []
        if not self.code_editor.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(self.code_widget.highlight_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.code_editor.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        self.code_editor.setExtraSelections(extra_selections)

        # Highlight the corresponding line number
        self.update()  # Force a repaint to update the line number color

    def highlightLine(self, line_number, highlight_color):
        cursor = self.code_editor.textCursor()
        cursor.movePosition(QTextCursor.Start)
        for _ in range(line_number - 1):
            cursor.movePosition(QTextCursor.Down)
        cursor.movePosition(QTextCursor.StartOfLine)
        cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
        format = cursor.charFormat()
        format.setBackground(QColor(highlight_color))
        cursor.setCharFormat(format)

    def goToLine(self, line_number):
        cursor = self.code_editor.textCursor()
        cursor.movePosition(QTextCursor.Start)
        for _ in range(line_number - 1):
            cursor.movePosition(QTextCursor.Down)
        self.code_editor.setTextCursor(cursor)

    def getLineContent(self, line_number):
        cursor = self.code_editor.textCursor()
        cursor.movePosition(QTextCursor.Start)
        for _ in range(line_number - 1):
            cursor.movePosition(QTextCursor.Down)
        cursor.movePosition(QTextCursor.StartOfLine)
        cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
        return cursor.selectedText()