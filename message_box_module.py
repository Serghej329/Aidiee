import sys
import webbrowser
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTextEdit, QLineEdit, QPushButton, 
                             QLabel, QScrollArea, QFrame,QSizePolicy,QPlainTextEdit)
from PyQt5.QtCore import (Qt, QTimer, pyqtSignal, QSize, QPropertyAnimation, 
                          QPoint, QSequentialAnimationGroup, QParallelAnimationGroup,QUrl)
from PyQt5.QtGui import QPixmap, QPalette, QColor, QFont, QIcon,QTextCursor,QDesktopServices,QSyntaxHighlighter,QTextCharFormat
from code_editor_widget import CodeEditorWidget
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


class CodeBlockDialog(CodeEditorWidget):
    def __init__(self, code='', language='',number=0, parent=None,):
        super().__init__(parent)
        #self.setWindowTitle(f"Code Block ({language.upper() if language else 'Plain Text'})")
       # self.resize(600, 400)
        #layout = QVBoxLayout(self)
        #self.text_edit = QPlainTextEdit()
        print("setting up codeblock dialog")
        self.language = language
        
        #self.highlighter = PythonSyntaxHighlighter(self.text_edit.document())
        #layout.addWidget(self.text_edit)
        #copy_button = QPushButton("Copy Code")
        #copy_button.clicked.connect(self.copy_code)
        #layout.addWidget(copy_button)
        self.code_editor.setPlainText(code)
        self.code_editor.setReadOnly(True)
        self.added = False
        self.number = number
        self.aidee = parent
        
    def update_code(self, code):
        #self.verticalScrollBar().setValue(self.code_editor.verticalScrollBar().maximum())
        if not self.added:
              self.aidee.add_suggestion_tab(editor=self,suggestion_number = self.number)
        self.set_content(code)


     




class CustomMarkdownConverter:
    def __init__(self,parent = None,):
        self.aidee = parent
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
                    #html_lines.append(f'<a href="codeblock://{len(self.code_blocks)-1}" class="code-block-placeholder">📄 Code Block ({self.code_block_language.upper() if self.code_block_language else "Plain Text"}) - Click to View</a>')
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
    def __init__(self, parent,converter):
        super().__init__(parent)
        self.aidee = parent
        self.code_converter = converter
        self.setReadOnly(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setMinimumWidth(20)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.code_blocks = []
        self.code_dialogs = []
        
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
                    if(block_id>=0 and block_id<=len(self.code_converter.code_blocks)):
                        code,language  = self.code_converter.code_blocks[block_id]
                        print(f"language is : {language}\ncode is: {code}")
                        editor_dialog = CodeBlockDialog(code = code ,language=language, number = block_id)
                        self.aidee.add_suggestion_tab(suggestion_number = block_id,editor = editor_dialog)
                        editor_dialog.set_language(language=language)
                        editor_dialog.set_content(content=code)
                        print(f"Setting to path : virtual/Suggestion {block_id+1}")
                except (ValueError, IndexError) as e:
                    print(f"Error accessing block ID {block_id_str}: {e}")
                    print(f"Invalid block_id: {block_id}")
                    print(f"Code blocks available: {self.code_converter.code_blocks}")
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
    def __init__(self,parent, converter,message="", is_user=True ):
        super().__init__(parent)
        self.aidee = parent
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Message bubble
        self.bubble = QFrame()
        self.bubble.setObjectName("userBubble" if is_user else "assistantBubble")
        self.bubble_layout = QVBoxLayout()
        self.bubble.setLayout(self.bubble_layout)
        
        # Create and configure MarkdownTextEdit
        self.text = MarkdownTextEdit(parent = self.aidee, converter = converter)
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
        self.aidee = parent
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(8)
        self.layout.addStretch()
        self.writing_indicator = WritingIndicator()
        self.current_stream_message = None
        self.stream_buffer = ""
        self.code_converter = CustomMarkdownConverter(parent=parent)
        self.current_code_dialog = None
        self.current_code_buffer = ""
        self.is_first_code_block_token = True
        self.in_code_block = False
        self.code_blocks_index = 0
        self.apply_styles()
        # self.simulate_stream_response(message="""'''python
        #                  for i in test:
        #                  i +=1print(i)
        #                  '''""")
    def apply_styles(self):
        self.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                border: none;
                padding: 5px;
                font-size: 14px;
            }
            
            QTextEdit a {
                color: red;
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
            
        message_widget = MessageWidget(parent=self.aidee, message=message, is_user=is_user, converter = self.code_converter)
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
        self.current_stream_message = MessageWidget("", False,parent=self.aidee)
        self.layout.addWidget(self.current_stream_message)
        self.stream_buffer = ""
        for i in range(len(message)):
            QTimer.singleShot(50 * i, lambda x=i: self.update_stream(token=message[x], ended=(x == len(message) - 1)))

    def begin_streaming(self):
        """Initialize a new streaming message"""
        self.toggle_writing_indicator(False)
        if self.current_stream_message is None:
                self.current_stream_message = MessageWidget(parent=self.aidee,message="", is_user=False,converter = self.code_converter)
                self.layout.addWidget(self.current_stream_message)
        self.stream_buffer = ""
        self.in_code_block = False
        self.current_code_buffer = ""
        self.current_code_dialog = None
        self.scroll_to_bottom()

    def update_stream(self, token: str, ended: bool = False):
        """Update the streaming message with new content"""
        try:
                # Ensure we have a current message widget
                if self.current_stream_message is None:
                        self.begin_streaming()
                
                if not ended:
                        if self.in_code_block:      
                                self.current_code_buffer += token
                                #Check if we're ending a code block
                                if "```" in self.current_code_buffer:
                                        # Split at the end marker
                                        parts = self.current_code_buffer.rsplit("```", 1)
                                        if len(parts) == 2:
                                                # Finalize code block content
                                                code_content, remaining_text = parts
                                                if self.current_code_dialog:
                                                        self.current_code_dialog.update_code(code_content)
                                                        # Get the language from the dialog title
                                                        language = self.current_code_buffer.rsplit(" ", 1)[0]
                                                        # Add to code blocks before updating the HTML
                                                        #block_index = len(self.code_converter.code_blocks)
                                                        self.code_converter.code_blocks.append((language, code_content))
                                                        
                                                        # Get current HTML content and preserve it
                                                        self.current_stream_message.updateSize()
                                                        
                                                        # Add remaining text to buffer if any
                                                        if remaining_text.strip():
                                                                self.stream_buffer += remaining_text.strip()

                                                        # Reset token flag
                                                        self.is_first_code_block_token = True

                                                self.in_code_block = False
                                                self.current_code_buffer = ""
                                                self.current_code_dialog = None
                                elif self.current_code_dialog:
                                        if self.is_first_code_block_token:# If its the first token of the codeblock (need errorproof for missing language)
                                                self.is_first_code_block_token = False
                                                # Preserve existing content and add code block placeholder
                                                current_content = self.stream_buffer.replace("```", "")
                                                placeholder = f'<br><a href="codeblock://{len(self.code_converter.code_blocks)}" style="padding:10px;font-size:15px;color:#37474F;text-decoration: none;border-radius:8px;background:#D1C4E9" class="code-block-placeholder" style="font-weight:bold;"><span >📄 Code Block ({self.current_code_buffer.upper()}) - Click to View</span></a><br>'
                                                self.stream_buffer = current_content + placeholder
                                                # Convert the entire buffer to HTML and update
                                                html_content = markdown.markdown(self.stream_buffer, extensions=['extra', 'nl2br'])
                                                self.current_stream_message.text.setHtml(html_content)
                                                # Update Message Size
                                                self.current_stream_message.updateSize()
                                                self.current_code_buffer = ""
                                        else:
                                                self.current_code_dialog.update_code(self.current_code_buffer)
                                return

                        self.stream_buffer += token

                        # Check if we're starting a code block
                        if '```' in self.stream_buffer and not self.in_code_block:
                                # Split content at the code block marker
                                parts = self.stream_buffer.rsplit('```', 1)

                                # Process text before code block while preserving existing content
                                if parts[0].strip():
                                        # current_html = self.current_stream_message.text.toHtml()
                                        new_html = markdown.markdown(parts[0].strip(), extensions=['extra', 'nl2br'])
                                        self.current_stream_message.text.setHtml(new_html)
                                        self.current_stream_message.updateSize()
                                
                                # Start new code block
                                self.in_code_block = True
                                rest = parts[1]
                                language = rest.split('\n', 1)[0].strip() if '\n' in rest else rest.strip()
                                block_index = len(self.code_converter.code_blocks)
                                # Create and show code block dialog
                                self.current_code_dialog = CodeBlockDialog(language=language, parent=self.aidee,number = block_index,code = "")
                                self.current_code_dialog.show()
                                return

                        # Regular text content - update the complete buffer each time
                        if self.stream_buffer:
                                # Convert the entire accumulated buffer to HTML
                                html_content = markdown.markdown(self.stream_buffer, extensions=['extra', 'nl2br'])
                                
                                if self.current_stream_message and self.current_stream_message.text:
                                        self.current_stream_message.text.setHtml(html_content)
                                        self.current_stream_message.updateSize()
                                        self.scroll_to_bottom()
                        
                else:  # Stream ended
                        if self.in_code_block:
                                # Finalize code block while preserving existing content
                                if self.current_code_dialog:
                                        final_code = self.current_code_buffer.rstrip('`').strip()
                                        self.current_code_dialog.update_code(final_code)
                                        
                                        # Get language and add to code blocks
                                        language = self.current_code_dialog.windowTitle().split('(')[1].split(')')[0].lower()
                                        #block_index = len(self.code_converter.code_blocks)
                                        self.code_converter.code_blocks.append((language, final_code))
                                        self.code_converter.code_dialogs.append((self.current_code_dialog,len(self.code_converter.code_blocks)))
                                        self.current_stream_message.updateSize()
                
                                self.in_code_block = False
                                self.current_code_buffer = ""
                                self.current_code_dialog = None
                        #print(f"the stream buffer was :{self.stream_buffer}")
                        self.current_stream_message = None
                        self.stream_buffer = ""
                        self.toggle_writing_indicator(False)
                        self.scroll_to_bottom()

        except Exception as e:
                print(f"Error in update_stream: {str(e)}")
                import traceback
                traceback.print_exc()

    def scroll_to_bottom(self):
        scrollbar = self.layout.parentWidget().parentWidget().parentWidget().verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

class ChatWidget(QWidget):
    def __init__(self,aidee,parent=None):
        super().__init__(parent)
        
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(0)  # Reduce spacing between elements
        
        # Messages container
        self.message_container = MessageContainerWidget(parent = aidee)
        
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