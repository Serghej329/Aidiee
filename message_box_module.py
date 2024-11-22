import sys
import webbrowser
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTextEdit, QLineEdit, QPushButton, 
                             QLabel, QScrollArea, QFrame,QSizePolicy,QDialog,QPlainTextEdit)
from PyQt5.QtCore import (Qt, QTimer, pyqtSignal, QSize, QPropertyAnimation, 
                          QPoint, QSequentialAnimationGroup, QParallelAnimationGroup,QUrl)
from PyQt5.QtGui import QPixmap, QPalette, QColor, QFont, QIcon,QTextCursor,QDesktopServices,QSyntaxHighlighter,QTextCharFormat
import markdown
import re
class ShadowDot(QFrame):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setFixedSize(6, 6)

        self.setObjectName("dot")

        

        # Create shadow animation

        self.animation = QPropertyAnimation(self, b"styleSheet")

        self.animation.setDuration(1000)

        self.animation.setLoopCount(-1)

        

        # Define keyframes for shadow effect

        self.animation.setStartValue("background-color: #65676B; border-radius: 3px; margin: 0px;")

        self.animation.setEndValue("background-color: #65676B; border-radius: 3px; margin: 3px;")



class WritingIndicator(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        layout = QHBoxLayout(self)

        layout.setContentsMargins(10, 5, 10, 5)

        

        # Background frame

        self.frame = QFrame()

        self.frame.setObjectName("writingIndicator")

        frame_layout = QHBoxLayout(self.frame)

        frame_layout.setSpacing(4)

        

        # Label

        self.label = QLabel("Writing")

        self.label.setObjectName("writingLabel")

        frame_layout.addWidget(self.label)

        

        # Create three dots with shadow animation

        self.dots = []

        for _ in range(3):

            dot = ShadowDot()

            frame_layout.addWidget(dot)

            self.dots.append(dot)

            

        frame_layout.addStretch()

        layout.addWidget(self.frame)

        layout.addStretch()

        

        # Initially hidden

        self.hide()

        

    def start(self):

        self.show()

        for i, dot in enumerate(self.dots):

            dot.animation.setStartValue(f"background-color: #65676B; border-radius: 3px; margin: {i}px;")

            dot.animation.start()

        

    def stop(self):

        for dot in self.dots:

            dot.animation.stop()

        self.hide()

class PythonSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Define basic syntax highlighting rules
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#007020"))
        keyword_format.setFontWeight(QFont.Bold)
        
        keywords = [
            "def", "class", "import", "from", "as", "if", "else", "elif", 
            "for", "while", "in", "return", "break", "continue", "pass", 
            "True", "False", "None"
        ]
        
        self.highlighting_rules = [(r'\b' + keyword + r'\b', keyword_format) for keyword in keywords]
        
        # String highlighting
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#4070A0"))
        self.highlighting_rules.append((r'".*?"', string_format))
        self.highlighting_rules.append((r"'.*?'", string_format))
        
        # Comment highlighting
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#60A0B0"))
        comment_format.setFontItalic(True)
        self.highlighting_rules.append((r'#.*', comment_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            import re
            expression = re.compile(pattern)
            for match in expression.finditer(text):
                start = match.start()
                length = match.end() - start
                self.setFormat(start, length, format)


class CodeBlockDialog(QDialog):
    def __init__(self, code, language='', parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Code Block ({language.upper() if language else 'Plain Text'})")
        self.resize(600, 400)
        layout = QVBoxLayout(self)
        self.text_edit = QPlainTextEdit()
        self.text_edit.setPlainText(code)
        self.text_edit.setFont(QFont("Consolas", 10))
        self.text_edit.setReadOnly(True)
        self.highlighter = PythonSyntaxHighlighter(self.text_edit.document())
        layout.addWidget(self.text_edit)
        copy_button = QPushButton("Copy Code")
        copy_button.clicked.connect(self.copy_code)
        layout.addWidget(copy_button)

    def copy_code(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text_edit.toPlainText())




class CustomMarkdownConverter:
    def __init__(self):
        self.code_blocks = []
        self.in_code_block = False
        self.code_block_language = ''
        self.code_block_content = ''

    def convert(self, markdown_text):
        lines = markdown_text.split('\n')
        html_lines = []
        for line in lines:
            if line.startswith('```'):
                if self.in_code_block:
                    # End of code block
                    self.code_blocks.append((self.code_block_language, self.code_block_content))
                    html_lines.append(f'<a href="codeblock://{len(self.code_blocks)-1}" class="code-block-placeholder">📄 Code Block ({self.code_block_language.upper() if self.code_block_language else "Plain Text"}) - Click to View</a>')
                    self.in_code_block = False
                    self.code_block_language = ''
                    self.code_block_content = ''
                else:
                    # Start of code block
                    parts = line.split(' ', 1)
                    self.code_block_language = parts[0].strip('`') if len(parts) > 1 else ''
                    self.in_code_block = True
                continue
            if self.in_code_block:
                self.code_block_content += line + '\n'
            else:
                # Process regular markdown line
                html_line = markdown.markdown(line, extras={'link-patterns': None})
                html_lines.append(html_line)
        return '\n'.join(html_lines), self.code_blocks

class MarkdownTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setMinimumWidth(20)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.code_blocks = []
        
    def set_markdown_text(self, markdown_text):
        self.code_blocks = []
        converter = CustomMarkdownConverter()
        html_text, self.code_blocks = converter.convert(markdown_text)
        self.setHtml(html_text)
        self.update_size()

        
    def mousePressEvent(self, event):
        cursor = self.cursorForPosition(event.pos())
        char_format = cursor.charFormat()
        if char_format.isAnchor():
            href = char_format.anchorHref()
            if href.startswith("codeblock://"):
                block_id_str = href[len("codeblock://"):]
                try:
                    block_id = int(block_id_str)
                    if 0 <= block_id < len(self.code_blocks):
                        language, code = self.code_blocks[block_id]
                        dialog = CodeBlockDialog(code, language)
                        dialog.exec_()
                except (ValueError, IndexError) as e:
                    print(f"Error accessing block ID {block_id_str}: {e}")
            else:
                QDesktopServices.openUrl(QUrl(href))
        else:
            super().mousePressEvent(event)
        
    def update_size(self):
        document = self.document()
        document.setTextWidth(self.viewport().width())
        doc_height = document.size().height()
        self.setFixedHeight(int(doc_height) + 20)
        text_width = document.idealWidth()
        min_width = min(400, max(100, text_width + 40))
        self.setMinimumWidth(int(min_width))

class MessageWidget(QWidget):
    def __init__(self, message="", is_user=True, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Message bubble
        self.bubble = QFrame()
        self.bubble.setObjectName("userBubble" if is_user else "assistantBubble")
        self.bubble_layout = QVBoxLayout()
        self.bubble.setLayout(self.bubble_layout)
        
        # Create and configure MarkdownTextEdit
        self.text = MarkdownTextEdit()
        self.bubble_layout.addWidget(self.text)
        
        # Add bubble to main layout with proper alignment
        if is_user:
            self.layout.addStretch()
            self.layout.addWidget(self.bubble)
        else:
            self.layout.addWidget(self.bubble)
            self.layout.addStretch()
        
        # Set the text after widget is fully configured
        self.setText(message)

    def setText(self, message):
        self.text.set_markdown_text(message)
        # Update size after setting text
        self.updateSize()
        
    def updateSize(self):
        # Calculate required height based on content
        document = self.text.document()
        document.setTextWidth(self.text.viewport().width())
        doc_height = document.size().height()
        
        # Set fixed height to match content
        self.text.setFixedHeight(int(doc_height) + 10)  # Add small padding
        
        # Update minimum width based on content
        text_width = document.idealWidth()
        min_width = min(400, max(100, text_width + 40))  # Keep within reasonable bounds
        self.text.setMinimumWidth(int(min_width))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.updateSize()

    def add_image(self, image_path):
        pixmap = QPixmap(image_path)
        scaled_pixmap = pixmap.scaled(QSize(200, 200), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        image_label = QLabel()
        image_label.setPixmap(scaled_pixmap)
        self.bubble_layout.addWidget(image_label)

class MessageContainerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(8)
        self.layout.addStretch()
        self.writing_indicator = WritingIndicator()
        self.current_stream_message = None
        self.stream_buffer = ""
        self.code_converter = CustomMarkdownConverter()
        self.apply_styles()
    def apply_styles(self):
        self.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                border: none;
                padding: 5px;
                font-size: 14px;
            }
            
            QTextEdit a {
                color: #0084ff;
                text-decoration: none;
            }
            
            QTextEdit a:hover {
                text-decoration: underline;
            }
            
            QTextEdit code {
                background-color: #f0f0f0;
                border-radius: 3px;
                padding: 2px 4px;
                font-family: monospace;
                font-size: 13px;
            }
            
            QTextEdit pre {
                background-color: #f4f4f4;
                border-radius: 5px;
                padding: 10px;
                font-family: monospace;
                font-size: 13px;
                white-space: pre-wrap;
                word-wrap: break-word;
                overflow-x: auto;
            }
            
            QTextEdit blockquote {
                border-left: 4px solid #ccc;
                padding-left: 10px;
                color: #666;
                font-style: italic;
                margin: 0;
            }
            
            QTextEdit table {
                border-collapse: collapse;
                width: 100%;
                margin-bottom: 10px;
            }
            
            QTextEdit th, QTextEdit td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }
            
            QTextEdit th {
                background-color: #f2f2f2;
            }
            
            #userBubble {
                background-color: #0084ff;
                border-radius: 15px;
                padding: 10px;
                margin: 2px;
                min-width: 50px;
                max-width: 400px;
                color: white;
            }
            
            #userBubble QTextEdit {
                color: white;
            }
            
            #assistantBubble {
                background-color: #e4e6eb;
                border-radius: 15px;
                padding: 10px;
                margin: 2px;
                min-width: 50px;
                max-width: 400px;
            }
            
            #assistantBubble QTextEdit {
                color: black;
            }
            
            #writingIndicator {
                background-color: #e4e6eb;
                border-radius: 12px;
                padding: 5px 10px;
                margin: 2px;
                max-width: 100px;
            }
            
            #writingLabel {
                color: #65676B;
                font-size: 13px;
            }
        """)
    def toggle_writing_indicator(self, show=True):
        if show:
            self.writing_indicator.start()
        else:
            self.writing_indicator.stop()

    def add_message(self, message, is_user=True):
        if self.writing_indicator in self.findChildren(WritingIndicator):
            self.layout.removeWidget(self.writing_indicator)
            self.writing_indicator.hide()
            
        message_widget = MessageWidget(message, is_user)
        self.layout.addWidget(message_widget)
        
        if not is_user:
            self.layout.addWidget(self.writing_indicator)
        
        QTimer.singleShot(100, self.scroll_to_bottom)

    def add_image_message(self, image_path, message="", is_user=True):
        message_widget = MessageWidget(message, is_user)
        message_widget.add_image(image_path)
        self.layout.addWidget(message_widget)
        QTimer.singleShot(100, self.scroll_to_bottom)

    def simulate_stream_response(self, message):
        self.toggle_writing_indicator(False)
        self.current_stream_message = MessageWidget("", False)
        self.layout.addWidget(self.current_stream_message)
        self.stream_buffer = ""
        for i in range(len(message)):
            QTimer.singleShot(100 * i, lambda x=i: self.update_stream(token=message[x], ended=(x == len(message) - 1)))

    def begin_streaming(self):
        self.toggle_writing_indicator(False)
        self.current_stream_message = MessageWidget("", False)
        self.layout.addWidget(self.current_stream_message)
        self.stream_buffer = ""
    

    def update_stream(self, token: str, ended: bool = False):
        if not ended:
            self.stream_buffer += token
            lines = self.stream_buffer.split('\n')
            for line in lines:
                if line.startswith('```'):
                    if self.code_converter.in_code_block:
                        # End of code block
                        self.code_converter.code_blocks.append((self.code_converter.code_block_language, self.code_converter.code_block_content))
                        placeholder = f'<a href="codeblock://{len(self.code_converter.code_blocks)-1}" class="code-block-placeholder">📄 Code Block ({self.code_converter.code_block_language.upper() if self.code_converter.code_block_language else "Plain Text"}) - Click to View</a>'
                        self.current_stream_message.text.setHtml(placeholder)
                        self.code_converter.in_code_block = False
                        self.code_converter.code_block_language = ''
                        self.code_converter.code_block_content = ''
                    else:
                        # Start of code block
                        parts = line.split(' ', 1)
                        self.code_converter.code_block_language = parts[0].strip('`') if len(parts) > 1 else ''
                        self.code_converter.in_code_block = True
                elif self.code_converter.in_code_block:
                    # Collect code content
                    self.code_converter.code_block_content += line + '\n'
                else:
                    # Render regular markdown line
                    html_line = markdown.markdown(line, extras={'link-patterns': None})
                    self.current_stream_message.text.setHtml(html_line)
        else:
            if self.current_stream_message:
                _, code_blocks = self.code_converter.convert(self.stream_buffer)
                # Render final message with placeholders
                self.current_stream_message.text.code_blocks = code_blocks
                self.current_stream_message.text.set_markdown_text(self.stream_buffer)
            self.current_stream_message = None
            self.stream_buffer = ""
            self.toggle_writing_indicator(False)

    def scroll_to_bottom(self):
        scrollbar = self.layout.parentWidget().parentWidget().parentWidget().verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

class ChatWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(0)  # Reduce spacing between elements
        
        # Messages container
        self.message_container = MessageContainerWidget()
        
        # Scroll area for messages
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.message_container)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.layout.addWidget(self.scroll_area, stretch=1)  # Give messages area more space
        
        # Apply styles
        self.apply_styles()
        
    def apply_styles(self):
        self.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            
            QLineEdit {
                border: 1px solid #e0e0e0;
                border-radius: 20px;
                padding: 8px 15px;
                background-color: white;
                font-size: 14px;
            }
            
            QPushButton {
                background-color: #0084ff;
                border-radius: 20px;
                padding: 10px;
                margin: 0px;
            }
            
            QPushButton:hover {
                background-color: #0073e6;
            }
        """)

    def send_message(self):
        message = self.input_area.text()
        if message:
            self.message_container.add_message(message, is_user=True)
            self.input_area.clear()

    def add_message(self, message, is_user=True):
        self.message_container.add_message(message, is_user)

    def add_image_message(self, image_path, message="", is_user=True):
        self.message_container.add_image_message(image_path, message, is_user)

    def simulate_stream_response(self, message):
        self.message_container.simulate_stream_response(message)

    def clear(self):
        # Clear all messages
        for i in reversed(range(self.message_container.layout.count())):
            item = self.message_container.layout.itemAt(i)
            if item.widget():
                item.widget().setParent(None)

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Set application-wide font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    window = QMainWindow()
    window.setWindowTitle("Markdown Chat")
    window.setMinimumSize(600, 800)
    
    chat_widget = ChatWidget()
    window.setCentralWidget(chat_widget)
    
    # Add some example messages with Markdown
    chat_widget.add_message("# Welcome to Markdown Chat!\n\nThis is a **bold** example with some *italic* text.\n\n## Features\n- Markdown rendering\n- Code blocks\n- Links and more!", False)
    chat_widget.add_message("Here's a code block:\n```python\ndef hello_world():\n    print('Hello, Markdown!')\n```\n\nAnd a [link to Anthropic](https://www.anthropic.com)", False)
    chat_widget.add_message("### Table Example\n| Column 1 | Column 2 |\n|----------|----------|\n| Row 1, Col 1 | Row 1, Col 2 |\n| Row 2, Col 1 | Row 2, Col 2 |", False)
    
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()