from pygments.styles import get_style_by_name
from pygments.lexers import get_lexer_for_filename,get_lexer_by_name, ClassNotFound
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PyQt5.QtGui import QFont, QColor, QSyntaxHighlighter, QTextCharFormat
from PyQt5.QtCore import QTimer
from neumorphic_widgets import NeumorphicWidget, NeumorphicTextEdit
from syntax_highlighting import PythonHighlighter
from line_numbers import LineNumbers
from python_highlighter import SyntaxThemes, SyntaxFormatter
import os

class PygmentsHighlighter(QSyntaxHighlighter):
    def __init__(self, parent, lexer, theme_colors):
        super().__init__(parent)
        self.lexer = lexer
        self.theme_colors = theme_colors
        self.formats = {}
        
        # Map Pygments token types to theme colors
        self.token_color_map = {
            'Keyword': 'import',
            'Name.Function': 'function_definition',
            'Name.Class': 'class_definition',
            'String': 'string',
            'Number': 'integer',
            'Comment': 'comment',
            'Operator': 'call',
            'Name.Builtin': 'builtin_function',
            'Name': 'attribute'
        }
        


class CodeEditorWidget(QWidget):
    def __init__(self, filename=None, language=None, parent=None):
        super().__init__(parent)
        self.current_language = language
        self.current_highlighter = None
        self.syntax_themes = SyntaxThemes()
        self.current_theme = self.syntax_themes.themes['Tokyo Night']
        self.setup_ui()
        # Apply initial theme
        self.set_style('Tokyo Night')
        
        # Set the highlighter based on filename or language
        if filename:
            self.set_language(filename=filename)
        elif language:
            self.set_language(language=language)
        else:
            print("No language or filename provided, no highlighter set.")
        
    def setup_ui(self):
        print("setupping ")
        layout = QVBoxLayout(self)
        self.code_editor = NeumorphicTextEdit()
        self.code_editor.setFont(QFont("Fira Code", 12))
        self.selection_color = ""
        # Add line numbers
        self.line_numbers = LineNumbers(self.code_editor, parent=self)
        editor_layout = QHBoxLayout()
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(0)
        editor_layout.addWidget(self.line_numbers)
        editor_layout.addWidget(self.code_editor)
        
        layout.addLayout(editor_layout)
        self.setLayout(layout)
        
        # Apply neumorphic style
        self.setStyleSheet("""
            background-color: #2C2D3A;
            border-top-right-radius: 10px;
            border-bottom-right-radius: 10px;
            padding: 10px;
        """)
        
    def detect_language(self, filename):
        """Detect language based on file extension"""
        try:
            lexer = get_lexer_for_filename(filename)
            print(f"detected language {lexer}")
            return lexer.name.lower()
        except ClassNotFound:
            return None
            
    def set_language(self, language=None, filename=None):
        """Set the appropriate highlighter based on language or filename"""
        if language:
                try:
                        self.current_language = language.lower()
                        lexer = get_lexer_by_name(language)
                except:
                        print(f"error checking lexer for name : {language}")
        elif filename:
                try:
                        lexer = get_lexer_for_filename(filename)
                        self.current_language = lexer.name.lower()
                except:
                        print(f"error checking lexer for filename : {filename}")  
        else:
            self.current_language = None
        
        # Remove existing highlighter if any
        if self.current_highlighter:
            self.current_highlighter.setDocument(None)
            self.current_highlighter = None
        
        if self.current_language == 'python':
            # Use Tree-sitter based highlighter for Python
            print("using tree sitter")
            self.current_highlighter = SyntaxFormatter(
                self.code_editor.document(),
                self.current_theme
            )
        elif self.current_language:
            # Use Pygments based highlighter for other languages
            try:
                print("using pygments")
                lexer = get_lexer_by_name(self.current_language)
                self.current_highlighter = PygmentsHighlighter(
                    self.code_editor.document(),
                    lexer,
                    self.current_theme
                )
            except ClassNotFound:
                pass
        else:
            print("No language specified, no highlighter set.")
    
    def set_style(self, style_name):
        """Apply the selected theme to the editor"""
        self.current_theme = self.syntax_themes.themes[style_name]
        
        # Update editor colors
        self.background_color = self.current_theme['background']
        fg_color = self.current_theme['foreground']
        self.highlight_color = QColor(self.current_theme['highlight'])
        if (QColor(self.background_color).lightness() >= 50): # If the background is light:
                self.selection_color =self.highlight_color.darker(150)# Slightly darker version of the highlight color
        else:                                                                      #If the background is dark:
                self.selection_color = self.highlight_color.lighter(150)# Slightly lighter version of the highlight color

        # Apply colors to code editor
        self.code_editor.setStyleSheet(f"""
            QPlainTextEdit {{
                border-top-right-radius: 10px;
                border-bottom-right-radius: 10px;            
                padding: 10px;
                font-family: 'Fira Code', 'Consolas', monospace;
                margin: 0;
                background-color: {self.background_color};
                color: {fg_color};
                selection-background-color: {self.selection_color.name()};
            }}
            
            QTextEdit:focus {{
                border: 1px solid {self.highlight_color.name()};
            }}
        """)
        
        # Update line numbers colors
        self.line_numbers.highlight_color = QColor(self.highlight_color)
        self.line_numbers.line_number_color = QColor(fg_color)
        self.line_numbers.setStyleSheet(f"background-color: {self.background_color};")
        self.line_numbers.highlight_current_line()
        
        # Update highlighter if exists
        if self.current_highlighter:
            if isinstance(self.current_highlighter, SyntaxFormatter):
                self.current_highlighter.colors = self.current_theme
                #self.current_highlighter.highlightBlock()
            else:
                # Recreate Pygments highlighter with new theme
                self.current_highlighter.theme_colors = self.current_theme
                #self.current_highlighter.rehighlight()

    def set_content(self, content, filename=None):
        """Set editor content and apply appropriate highlighting"""
        self.code_editor.setPlainText(content)
        if filename and not self.current_language:
            self.set_language(filename=filename)
        else:
            # Ensure highlighter is set if language is already defined
            if self.current_language:
                self.set_language(language=self.current_language)
        
        # Force immediate rehighlighting
        if self.current_highlighter:
            self.current_highlighter.rehighlight_now()

    def blinkLine(self, line_number, blink_color):
        self.line_numbers.goToLine(line_number)
        self.line_numbers.highlightLine(line_number, QColor(blink_color))
        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(lambda: self.toggleBlink(line_number, blink_color))
        self.blink_timer.start(500)  # Blink every 500ms

    def toggleBlink(self, line_number, blink_color):
        current_color = self.line_numbers.getLineContent(line_number)
        if current_color == blink_color:
            self.line_numbers.highlightLine(line_number, QColor(self.current_theme['background']))
        else:
            self.line_numbers.highlightLine(line_number, QColor(blink_color))
