import sys
import webbrowser
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTextEdit, QLineEdit, QPushButton, 
                             QLabel, QScrollArea, QFrame,QSizePolicy,QPlainTextEdit)
from PyQt5.QtCore import (Qt, QTimer, pyqtSignal, QSize, QPropertyAnimation, 
                          QPoint, QSequentialAnimationGroup, QParallelAnimationGroup,QUrl, QRectF
, QRect)
from PyQt5.QtGui import QPainter,QPixmap, QPalette, QColor,QPen, QFont, QIcon,QTextCursor,QDesktopServices,QTextOption,QMovie, QPainterPath, QLinearGradient
from code_editor_widget import CodeEditorWidget
import markdown
import re
import time
from python_highlighter import SyntaxThemes
from pygments.lexers import get_lexer_by_name,guess_lexer,BashLexer
class LoadingSpinner(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        try:
            self.setFixedSize(32, 16)
            self.movie = QMovie("loading.gif")
            self.movie.setScaledSize(QSize(32, 16))
            self.setMovie(self.movie)
            self.setVisible(False)
        except Exception as e:
            print(f"Error: {str(e)}")

            
    def setVisible(self, visible):
        super().setVisible(visible)
        if visible:
            self.movie.start()
        else:
            self.movie.stop()

class ThoughtHeader(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.start_time = None
        self.init_ui()
        
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        
        # Create a container for the status and spinner
        status_container = QWidget()
        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(4)
        
        self.status_label = QLabel("Thinking")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #7982a9;
                font-family: 'Segoe UI', sans-serif;
                font-weight: bold;
            }
        """)
        custom_font = QFont()
        custom_font.setWeight(100)
        custom_font.setBold(True)
        self.status_label.setFont(custom_font)
        self.loading_spinner = LoadingSpinner()
        
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.loading_spinner)
        status_layout.addStretch()
        
        self.expand_button = QPushButton("▼")
        self.expand_button.setFixedSize(32, 32)
        self.expand_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #7aa2f7;
                font-size: 16px;
            }
            QPushButton:hover {
                color: #89ddff;
            }
        """)
        
        layout.addWidget(status_container)
        layout.addWidget(self.expand_button)
        
        self.setStyleSheet("""
            ThoughtHeader {
                background-color: #24283b;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
            }
        """)
        self.setFixedHeight(64)
        
    def start_thinking(self):
        self.start_time = time.time()
        self.status_label.setText("Thinking")
        self.loading_spinner.setVisible(True)
        
    def stop_thinking(self):
        if self.start_time:
            elapsed = int(time.time() - self.start_time)
            self.status_label.setText(f"Thought for {elapsed}s")
            self.loading_spinner.setVisible(False)
            
    def set_expanded(self, expanded: bool):
        self.expand_button.setText("▲" if expanded else "▼")



class CodeBlockDialog(CodeEditorWidget):
    def __init__(self, language,code='', number=0, parent=None):
        super().__init__(parent,language=language)
        self.language = language
        self.code_editor.setPlainText(code)
        self.code_editor.setReadOnly(True)
        self.added = False
        self.number = number
        self.aidee = parent
        
    def update_code(self, code):
        if not self.added and hasattr(self.aidee, 'add_suggestion_tab'):
            self.aidee.add_suggestion_tab(editor=self, suggestion_number=self.number)
        self.set_content(code)


     



class CustomMarkdownConverter:
    def __init__(self,parent = None,):
        self.aidee = parent
        self.code_blocks = []
        self.in_code_block = False
        self.code_block_language = ''
        self.code_block_content = ''
        self.code_dialogs = []
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
                html_text = markdown.markdown(line, extensions=['extra', 'nl2br'])
                html_text = html_text.replace('<pre>', '<pre class="wrap-pre">')
        return '\n'.join(html_lines), self.code_blocks


class MarkdownTextEdit(QTextEdit):
    def __init__(self, parent, converter,container):
        super().__init__(parent)
        # Original MarkdownTextEdit initialization
        self.aidee = parent
        self.container_widget = container
        self.code_converter = converter
        self.setReadOnly(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setMinimumWidth(20)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.code_blocks = []
        self.code_dialogs = []
        self.document().contentsChanged.connect(self.updateGeometry)

        # Command box related initialization
        self.command_boxes = []
        self.setMouseTracking(True)
        self.last_content = ""
        self.update_needed = True
        self.hover_box_index = -1
        
        # Configure fonts for command boxes
        self.command_font = QFont("Consolas", 10)
        self.button_font = QFont("Segoe UI", 9)
        self.button_font.setBold(True)
        
        # Colors for command boxes
        self.colors = {
            'box_bg': QColor(32, 33, 36),
            'box_border': QColor(45, 46, 50),
            'command_text': QColor(220, 220, 220),
            'button_normal': QColor(45, 121, 224),
            'button_hover': QColor(55, 131, 234),
            'button_text': QColor(255, 255, 255)
        }

    def sizeHint(self):
        size = super().sizeHint()
        doc_height = self.document().size().height()
        size.setHeight(int(doc_height))
        return size
   
    def minimumSizeHint(self):
        return self.sizeHint()

    def updateGeometry(self):
        super().updateGeometry()
        self.parentWidget().updateGeometry()
        self.update_needed = True

    def set_markdown_text(self, markdown_text):
        self.code_blocks = []
        converter = self.code_converter
        html_text, self.code_blocks = converter.convert(markdown_text)
        self.setHtml(html_text)
        self.update_size()
        self.update_needed = True
        self.findCommandPlaceholders()

    def set_markdown_text_simple(self, markdown_text):
        html_text = markdown.markdown(markdown_text, extensions=['extra', 'nl2br'])
        self.setHtml(html_text)
        self.update_size()

    def findCommandPlaceholders(self):
        try:
            current_content = self.toPlainText() 
            if current_content != self.last_content:
                self.command_boxes = []
                self.last_content = current_content
                
                document = self.document()
                block = document.begin()
                
                while block.isValid():
                    line_text = block.text()
                    match = re.search(r'\[\[COMMAND_PLACEHOLDER:command="([^"]+)"\]\]', line_text)
                    #print(f"Current content is {match}: {block.text()}")
                    if match:
                        self.command_boxes.append({
                            'command': match.group(1),
                            'block': block.blockNumber(),
                            'height': 40
                        })
                    
                    block = block.next()
                
                self.update_needed = False
        except Exception as e:
            print(f"Error finding command placeholders: {e}")
            self.command_boxes = []

    def mouseMoveEvent(self, event):
        pos = event.pos()
        old_hover_index = self.hover_box_index
        self.hover_box_index = -1
        
        for i, box in enumerate(self.command_boxes):
            if 'button_rect' in box and box['button_rect'].contains(pos):
                self.hover_box_index = i
                break
                
        if old_hover_index != self.hover_box_index:
            self.viewport().update()
        
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        # First check for command box clicks
        pos = event.pos()
        command_clicked = False
        
        for box in self.command_boxes:
            if 'button_rect' in box and box['button_rect'].contains(pos):
                command = box.get('command', '')
                if command:
                    print(f"Executing command: {command}")
                    try:
                        self.aidee.terminal.handle_command(command)
                    except Exception as e:
                        print(f"Error executing command: {e}")
                command_clicked = True
                break
        
        # If no command box was clicked, handle markdown links
        if not command_clicked:
            cursor = self.cursorForPosition(event.pos())
            char_format = cursor.charFormat()
            if char_format.isAnchor():
                href = char_format.anchorHref()
                if href.startswith("codeblock://"):
                    block_id_str = href[len("codeblock://"):]
                    try:
                        block_id = int(block_id_str)
                        if 0 <= block_id < len(self.code_converter.code_dialogs):
                            code_dialog = self.code_converter.code_dialogs[block_id]
                            code, language = self.code_converter.code_blocks[block_id]
                            self.aidee.add_suggestion_tab(editor=code_dialog, suggestion_number=block_id)
                            code_dialog.set_language(language=language)
                            code_dialog.set_content(content=code)
                            print(f"Setting to path : virtual/Suggestion {block_id + 1}")
                        else:
                            print(f"Error: block_id {block_id} is out of range")
                    except (ValueError, IndexError) as e:
                        print(f"Error handling code block: {e}")
                else:
                    QDesktopServices.openUrl(QUrl(href))
            else:
                super().mousePressEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        
        if self.update_needed:
            self.findCommandPlaceholders()
        
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.Antialiasing)
        
        document = self.document()
        for i, box_info in enumerate(self.command_boxes):
            try:
                block = document.findBlockByNumber(box_info['block'])
                cursor = QTextCursor(block)
                rect = self.cursorRect(cursor)
                
                y = rect.y()
                box_height = box_info['height']
                margin = 5
                box_width = self.viewport().width() - (margin * 2)
                
                if y + box_height >= 0 and y <= self.viewport().height():
                    # Main box
                    box_rect = QRectF(margin, y, box_width, box_height)
                    path = QPainterPath()
                    path.addRoundedRect(box_rect, 6, 6)
                    painter.fillPath(path, self.colors['box_bg'])
                    painter.setPen(QPen(self.colors['box_border'], 1))
                    painter.drawPath(path)
                    
                    # Command text
                    command_rect = QRectF(margin + 15, y, box_width - 100, box_height)
                    painter.setPen(self.colors['command_text'])
                    painter.setFont(self.command_font)
                    painter.drawText(command_rect, Qt.AlignLeft | Qt.AlignVCenter, box_info['command'])
                    
                    # Run button
                    button_width = 60
                    button_height = 28
                    button_rect = QRectF(
                        box_width - button_width - margin - 10,
                        y + (box_height - button_height) / 2,
                        button_width,
                        button_height
                    )
                    
                    box_info['button_rect'] = QRect(
                        int(button_rect.x()),
                        int(button_rect.y()),
                        int(button_rect.width()),
                        int(button_rect.height())
                    )
                    
                    button_path = QPainterPath()
                    button_path.addRoundedRect(button_rect, 4, 4)
                    button_color = self.colors['button_hover'] if i == self.hover_box_index else self.colors['button_normal']
                    painter.fillPath(button_path, button_color)
                    
                    painter.setPen(self.colors['button_text'])
                    painter.setFont(self.button_font)
                    painter.drawText(button_rect, Qt.AlignCenter, "Run")
                    
            except Exception as e:
                print(f"Error painting box: {e}")
                continue

    def update_size(self):
        document = self.document()
        document.setTextWidth(self.viewport().width())
        doc_height = document.size().height()
        
        # Add extra height for command boxes
        extra_height = sum(box.get('height', 40) for box in self.command_boxes)
        
        # Set fixed height to match content plus command boxes
        self.setFixedHeight(int(doc_height) + extra_height + 20)  # Add small padding
        
        # Update minimum width based on content
        text_width = document.idealWidth()
        min_width = min(400, max(100, text_width + 40))
        self.setMinimumWidth(int(min_width))

class MessageWidget(QWidget):
    def __init__(self, parent, converter,container, message, is_user=True,):
        super().__init__(parent)
        self.aidee = parent
        self.container_widget = container
        self.code_converter = converter
        self.theme = SyntaxThemes().tokyo_night
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.layout.setContentsMargins(10, 5, 10, 5)
        self.layout.setSpacing(0)
        
        # Thought process section (only for assistant messages)
        self.thought_section = None
        self.thought_container = None
        self.thought_text = None
        self.header = None
        
        if not is_user:
            self.setup_thought_section()
        
        # Create message container
        self.message_container = QWidget()
        self.message_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        message_layout = QVBoxLayout(self.message_container)
        message_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create and configure MarkdownTextEdit
        self.text = MarkdownTextEdit(parent=self.aidee, converter=converter, container=self.container_widget)
        self.text.setReadOnly(True)
        self.text.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        #self.text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.text.document().setDocumentMargin(8)
        
        if is_user:
            # User message styling
            self.message_container.setMaximumWidth(int(self.aidee.voice_assistant_dock.width() * 0.8))
            self.layout.addWidget(self.message_container, 0, Qt.AlignRight)
            message_layout.addWidget(self.text)
            self.set_as_user_message()
        else:
            # Assistant message styling
            self.layout.addWidget(self.message_container)
            self.message_container.setMaximumWidth(int(self.aidee.voice_assistant_dock.width()))
            message_layout.addWidget(self.text)
            self.set_as_assistant_message()
            # Ensure text wraps properly
            self.text.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
            self.text.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Set the text after widget is fully configured
        print(f"setting message to {message}")
        self.setText(message)
        
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1b26;
            }
            QTextEdit {
                background-color: #1a1b26;
                border: none;
                border-radius: 5px;
                padding: 8px;
                color: #c0caf5;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                line-height: 1.4;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #1a1b26;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #24283b;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #414868;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background-color: transparent;
            }
            .thought-header {
                background-color: #24283b;
                color: #7982a9;
                padding: 8px;
                border-radius: 5px;
                margin: 4px 0;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                font-style: italic;
            }
        """)
    def setup_thought_section(self):
        self.thought_section = QWidget()
        self.thought_section.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        thought_layout = QVBoxLayout(self.thought_section)
        thought_layout.setContentsMargins(0, 0, 0, 0)
        thought_layout.setSpacing(0)
        
        self.header = ThoughtHeader()
        self.header.expand_button.clicked.connect(self.toggle_thought)
        thought_layout.addWidget(self.header)
        
        self.thought_container = QWidget()
        self.thought_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.thought_container.setVisible(False)
        
        thought_container_layout = QVBoxLayout(self.thought_container)
        thought_container_layout.setContentsMargins(8, 8, 8, 8)
        
        self.thought_text = MarkdownTextEdit(parent=self.aidee, converter=self.code_converter, container=self.container_widget)
        self.thought_text.setReadOnly(True)
        self.thought_text.setStyleSheet("""
            QTextEdit {
                background-color: #24283b;
                border: none;
                padding: 8px;
                color: #7982a9;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                line-height: 1.4;
            }
        """)
        
        thought_container_layout.addWidget(self.thought_text)
        thought_layout.addWidget(self.thought_container)
        self.layout.addWidget(self.thought_section)
       

    def toggle_thought(self):
        if self.thought_container:
            is_visible = self.thought_container.isVisible()
            self.thought_container.setVisible(not is_visible)
            self.header.set_expanded(not is_visible)
            self.updateSize()
    
    def start_thinking(self):
        if self.header:
            self.header.start_thinking()
    
    def stop_thinking(self):
        if self.header:
            self.header.stop_thinking()

    def setText(self, message):
        self.text.set_markdown_text_simple(message)
        # Update size after setting text
        self.updateSize()
        
    def updateSize(self):
        """
        Update the size of the widget based on its content.
        """
        # First, ensure the document is using the correct width for wrapping
        document = self.text.document()
        viewport_width = self.text.viewport().width()
        document.setTextWidth(viewport_width)
        
        # Calculate the height needed based on the document size
        doc_height = document.size().height()
        
        # Set fixed height to match content plus padding
        self.text.setFixedHeight(int(doc_height) + 16)  # Add padding
        
        # For assistant messages, ensure width fills available space
        if not hasattr(self, 'thought_section'):  # User message
            # Keep the existing width behavior for user messages
            min_width = max(200, document.idealWidth() + 32)  # Add padding
            max_width = min(int(self.aidee.width() * 0.8), min_width)
            self.message_container.setMaximumWidth(max_width)
        else:  # Assistant message
            # Assistant messages should use the full available width
            self.text.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
            self.text.document().setTextWidth(viewport_width)
            
            # Update thought text if it exists
            if self.thought_text:
                self.thought_text.document().setTextWidth(viewport_width)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Force the text widget to rewrap its content
        self.text.document().setTextWidth(self.text.viewport().width())
        self.updateSize()



    def add_image(self, image_path):
        pixmap = QPixmap(image_path)
        scaled_pixmap = pixmap.scaled(QSize(200, 200), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        image_label = QLabel()
        image_label.setPixmap(scaled_pixmap)
        self.message_container.addWidget(image_label)

    def set_as_user_message(self):
        # Style for the message bubble
        self.message_container.setStyleSheet(f"""
            QWidget {{
                background-color: {self.theme['description_background']};
                border-radius: 10px;
            }}
        """)
        
        # Style for the text
        self.text.setStyleSheet(f"""
            QTextEdit {{
                background-color: transparent;
                border: none;
                padding: 8px;
                color: {self.theme['description_foreground']};
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                line-height: 1.4;
            }}
        """)
        
    def set_as_assistant_message(self):
        self.message_container.setStyleSheet(f"""
            QWidget {{
                background-color: transparent;
                border: none;
            }}
        """)
        
        self.text.setStyleSheet(f"""
            QTextEdit {{
                background-color: transparent;
                border: none;
                padding: 8px;
                color: {self.theme['main_foreground']};
                margin: 0;
                font-family: 'Segoe UI', sans-serif;
                font-size: 15px;
                line-height: 1.4;
            }}
        """)

class MessageContainerWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.aidee = parent
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.layout.setSpacing(8)
        self.layout.addStretch()
        self.current_stream_message = None
        self.stream_buffer = ""
        self.code_converter = CustomMarkdownConverter(parent=parent)
        
        # State tracking for code blocks
        self.in_code_block = False
        self.current_code_buffer = ""
        self.current_code_language = ""
        self.code_blocks_count = 0
        self.partial_token = ""
        self.check_next_token = False
        self._lexer = None  # Initialize lexer as None

        # State tracking for thought blocks
        self.in_thought_block = False
        self.current_thought_buffer = ""    

        # Buffer for accumulating tokens
        self.token_buffer = ""
        self.last_token_was_backtick = False
        self.in_command_block = False
        self.current_command_buffer = ""


    def add_message(self, message, is_user=True):
        print(f"Adding message: {message}")
        message_widget = MessageWidget(parent=self.aidee, message=message, is_user=is_user, converter = self.code_converter,container = self)
        self.layout.addWidget(message_widget)
        QTimer.singleShot(100, self.scroll_to_bottom)

    def add_image_message(self, image_path, message="", is_user=True):
        message_widget = MessageWidget(parent=self.aidee, message=message, is_user=is_user, converter = self.code_converter,container = self)
        message_widget.add_image(image_path)
        self.layout.addWidget(message_widget)
        QTimer.singleShot(100, self.scroll_to_bottom)

    def simulate_stream_response(self, message): 
        self.current_stream_message = MessageWidget(parent=self.aidee, message=message, is_user=is_user, converter = self.code_converter,container = self)
        self.layout.addWidget(self.current_stream_message)
        self.stream_buffer = ""
        for i in range(len(message)):
            QTimer.singleShot(50 * i, lambda x=i: self.update_stream(token=message[x], ended=(x == len(message) - 1)))

    def begin_streaming(self):
        """Initialize a new streaming message."""
        self.current_stream_message = MessageWidget(
            parent=self.aidee,
            message="",
            is_user=False,
            converter=self.code_converter,
            container = self
        )
        self.layout.addWidget(self.current_stream_message)
        self.stream_buffer = ""
        self.token_buffer = ""
        self.in_code_block = False
        self.current_code_buffer = ""
        self.current_code_language = ""
        self.last_token_was_backtick = False
        self.in_command_block = False
        self.current_command_buffer = ""
        self.in_thought_block = False
        self.current_thought_buffer = ""
        self._lexer = None
        self.scroll_to_bottom()

    def update_stream(self, chunk,ended=False):
        """Process streaming chunks from Google AI API."""
        try:
            if self.current_stream_message is None:
                self.begin_streaming()
            
            # Get the text from the chunk
            if hasattr(chunk, 'text'):
                token = chunk.text
            else:
                token = str(chunk)
            
            self.token_buffer += token
            
            # Check for code block markers
            if '```' in self.token_buffer:
                if not self.in_code_block:
                    # Start of code block
                    parts = self.token_buffer.split('```', 1)
                    if parts[0]:
                        self.stream_buffer += parts[0]
                        self._update_message_content()
                    
                    self.in_code_block = True
                    self.current_code_buffer = ""
                    
                    # Extract language if present
                    remaining = parts[1]
                    if '\n' in remaining:
                        lang, code = remaining.split('\n', 1)
                        if lang.strip() != '':
                            self.current_code_language = lang.strip()
                        else:
                            # Check if language in on a new line and get it from the next line
                            lang, code_new = code.split('\n', 1)
                            # Test if it is a valid language with pygments
                            try:
                                self._lexer = get_lexer_by_name(lang)
                                self.current_code_language = self._lexer.name.lower()

                                code = code_new
                            except:
                                # Try guessing the language
                                try:
                                    self._lexer = guess_lexer(code)
                                    self.current_code_language = self._lexer.name.lower()
                                except:
                                    print(f"Error checking lexer for code : {code}")
                                    self.current_code_language = "text"
                                    self._lexer = None  # Explicitly set to None if we can't determine the lexer
                        print(f"Language: {self.current_code_language}")
                        
                        if self.current_code_language == 'bash':
                            print("bash command")
                            if '```' not in code:
                                # Single token command block
                                print("single token command block")
                                self.in_code_block = False
                                self.in_command_block = True
                                self.current_command_buffer = code
                            else:
                                # Multi-token command block, keep accumulating until we find the end
                                print("multi-token command block")
                                parts = code.split('```', 1)
                                if len(parts) > 1:
                                    # We have both start and end in this token
                                    self.in_code_block = False
                                    self.in_command_block = False
                                    command = parts[0].strip()
                                    command_placeholder = f'[[COMMAND_PLACEHOLDER:command="{command}"]]<br> '
                                    print(f"Setting placeholder to {command_placeholder}")
                                    self.stream_buffer += command_placeholder
                                    self.current_stream_message.text.repaint()
                                    self._update_message_content()
                                    self.token_buffer = parts[1]
                                else:
                                    # Only have the start, keep accumulating
                                    print("accumulating to buffer")
                                    self.in_command_block = True
                                    self.current_command_buffer = code
                                    self.in_code_block = False
                            return
                        self.current_code_buffer = code
                    else:
                        self.current_code_language = "text"
                        self.current_code_buffer = remaining
                    
                    # Create code block placeholder and dialog
                    self._create_code_block()
                    
                else:
                    # End of code block
                    parts = self.token_buffer.split('```', 1)
                    self.current_code_buffer += parts[0]
                    self._update_code_block()
                    
                    self.in_code_block = False
                    if len(parts) > 1:
                        self.stream_buffer += parts[1]
                        self._update_message_content()
                
                self.token_buffer = ""

            elif '<Thought>' in self.stream_buffer and not self.in_thought_block:
                self.in_thought_block = True
                self.current_thought_buffer = ""
                parts = self.stream_buffer.split('<Thought>', 1)
                if parts[0]:
                    self.stream_buffer = parts[0]
                    self._update_message_content()
                self.current_thought_buffer = parts[1]
                self._update_thought_block()
                self.token_buffer = ""
                self.stream_buffer = self.stream_buffer.replace('<Thought>', '')
            elif '</Thought>' in self.current_thought_buffer and self.in_thought_block:
                self.in_thought_block = False
                parts = self.current_thought_buffer.split('</Thought>', 1)
                self.current_thought_buffer = parts[0]
                self._update_thought_block()
                if len(parts) > 1:
                    # Process the remaining content in the next iteration
                    self.token_buffer = parts[1] + self.token_buffer  # Prepend remaining content
                self.current_thought_buffer = ""
                self.stream_buffer = self.stream_buffer.replace('</Thought>', '')
            elif self.in_code_block:
                self.current_code_buffer += self.token_buffer
                self._update_code_block()
                self.token_buffer = ""
            elif self.in_command_block:
                if '```' in self.token_buffer:
                    # Found the end of the command block
                    parts = self.token_buffer.split('```', 1)
                    self.current_command_buffer += parts[0]
                    command = self.current_command_buffer.strip()
                    command_placeholder = f'[[COMMAND_PLACEHOLDER:command="{command}"]]<br> '
                    self.stream_buffer += command_placeholder
                    self._update_message_content()
                    self.in_command_block = False
                    if len(parts) > 1:
                        self.stream_buffer += parts[1]
                        self._update_message_content()
                else:
                    # Still accumulating command content
                    self.current_command_buffer += self.token_buffer
                self.token_buffer = ""
            elif self.in_thought_block:
                self.current_thought_buffer += self.token_buffer
                self._update_thought_block()
                self.token_buffer = ""
            else:
                self.stream_buffer += self.token_buffer
                self._update_message_content()
                self.token_buffer = ""
            
            self.scroll_to_bottom()
            if(ended):
                self.finalize_streaming()
            
        except Exception as e:
            print(f"Error in update_stream: {str(e)}")
            import traceback
            traceback.print_exc()


    def _create_code_block(self):
        """Create a new code block dialog and placeholder."""
        block_index = len(self.code_converter.code_blocks)  # Use the actual length of code_blocks
        
        # Create code dialog
        print(f"setting language to {self.current_code_language}")
        code_dialog = CodeBlockDialog(
            language=self.current_code_language,
            parent=self.aidee,
            number=block_index,
            code=""
        )
        code_dialog.show()
        
        # Add placeholder to message
        placeholder = (
            f'<br><a href="codeblock://{block_index}" '
            f'style="padding:10px;font-size:15px;color:#37474F;'
            f'text-decoration:none;border-radius:8px;background:#D1C4E9" '
            f'class="code-block-placeholder"><span>📄 Code Block '
            f'({self.current_code_language.upper()}) - Click to View</span></a><br>'
        )
        self.stream_buffer += placeholder
        self._update_message_content()
        
        self.code_converter.code_blocks.append(("",self.current_code_language))
        self.code_converter.code_dialogs.append(code_dialog) # Store the dialog directly

    def _update_code_block(self):
        """Update the current code block content."""
        if self.code_converter.code_dialogs: #check if the list isn't empty
            block_index = len(self.code_converter.code_dialogs) - 1
            code_dialog = self.code_converter.code_dialogs[block_index]
            code_dialog.update_code(self.current_code_buffer)
            self.code_converter.code_blocks[block_index] = (
                self.current_code_buffer,
                self.current_code_language
            )

    def _update_message_content(self):
        """Update the message content with current buffer."""
        if self.stream_buffer:
            html_content = markdown.markdown(self.stream_buffer, extensions=['extra', 'nl2br'])
            self.current_stream_message.text.setHtml(html_content)
            self.current_stream_message.updateSize()
    def _update_thought_block(self):
        """Update the message content with current buffer."""
        if self.current_thought_buffer:
            html_content = markdown.markdown(self.current_thought_buffer, extensions=['extra', 'nl2br'])
            self.current_stream_message.thought_text.setHtml(html_content)
    def finalize_streaming(self):
        """Finalize the streaming message."""
        if self.in_code_block:
            self._update_code_block()
            self.in_code_block = False
        
        if self.token_buffer:
            self.stream_buffer += self.token_buffer
            self._update_message_content()
        #print(f" Complete stream: {self.stream_buffer}")
        self.current_stream_message = None
        self.stream_buffer = ""
        self.token_buffer = ""
        self.scroll_to_bottom()

    def scroll_to_bottom(self):
        scrollbar = self.layout.parentWidget().parentWidget().parentWidget().verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

class ChatWidget(QWidget):
    def __init__(self,aidee,parent=None):
        super().__init__(parent)
        
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(0)  # Reduce spacing between elements
        self.layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        
        # Messages container
        self.message_container = MessageContainerWidget(parent=aidee)
        self.message_container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
        
        # Scroll area for messages
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.message_container)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.layout.addWidget(self.scroll_area, stretch=1)
        
        # Set size policy for ChatWidget itself
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
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
                
    def resizeEvent(self, event):
        # Call parent's resize event
        super().resizeEvent(event)
        
        # Get the new width of the chat widget
        new_width = self.width()
        
        # Calculate the effective message width
        scrollbar_width = self.scroll_area.verticalScrollBar().width() if self.scroll_area.verticalScrollBar().isVisible() else 0
        effective_width = new_width - scrollbar_width - 20  # 20px for container margins
        
        # Update message container width
        self.message_container.setFixedWidth(effective_width)
        
        # Iterate through all message widgets
        for i in range(self.message_container.layout.count()):
            widget_item = self.message_container.layout.itemAt(i)
            if widget_item and isinstance(widget_item.widget(), MessageWidget):
                message_widget = widget_item.widget()
                
                # Determine if it's a user message
                is_user_message = not hasattr(message_widget, 'thought_section')
                
                if is_user_message:
                    max_width = int(effective_width * 0.8)
                else:
                    max_width = effective_width
                
                # Set the container width
                message_widget.message_container.setMaximumWidth(max_width)
                
                # Force the text widget to rewrap its content
                message_widget.text.document().setTextWidth(message_widget.text.viewport().width())
                
                # Update the widget size
                message_widget.updateSize()
                
        # Ensure scroll position is maintained
        current_scroll = self.scroll_area.verticalScrollBar().value()
        self.scroll_area.verticalScrollBar().setValue(current_scroll)


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Set application-wide font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    window = QMainWindow()
    window.setWindowTitle("Markdown Chat")
    window.setMinimumSize(600, 800)
    
    chat_widget = ChatWidget(aidee=window)
    window.setCentralWidget(chat_widget)
    
    # Add some example messages with Markdown
    chat_widget.add_message("# Welcome to Markdown Chat!\n\nThis is a **bold** example with some *italic* text.\n\n## Features\n- Markdown rendering\n- Code blocks\n- Links and more!", False)
    chat_widget.add_message("Here's a code block:\n```python\ndef hello_world():\n    print('Hello, Markdown!')\n```\n\nAnd a [link to Anthropic](https://www.anthropic.com)", False)
    chat_widget.add_message("### Table Example\n| Column 1 | Column 2 |\n|----------|----------|\n| Row 1, Col 1 | Row 1, Col 2 |\n| Row 2, Col 1 | Row 2, Col 2 |", False)
    
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()