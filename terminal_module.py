import sys,os
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, 
                             QLabel, QFrame, QLineEdit, QScrollArea, QHBoxLayout, 
                             QSizePolicy, QComboBox, QTextEdit)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont, QPalette, QColor, QTextOption, QTextDocument
import subprocess
from terminal_handler import TerminalHandler
from enum import Enum, auto
import threading
from output_types import OutputType
from copy import deepcopy
class TerminalThemes:
    THEMES = {
        'Dark': {
            'background_color': '#1E1F2A',
            'border_color': '#374151',
            'text_color': '#D1D5DB',
            'prompt_color': '#34D399',
            'error_color': '#EF4444',
            'selection_color': '#4B5563',
            'cursor_color': '#D1D5DB',
            'link_color': '#E0F2F1'
        },
        'Light': {
            'background_color': '#F9FAFB',
            'border_color': '#E5E7EB',
            'text_color': '#1F2937',
            'prompt_color': '#059669',
            'error_color': '#DC2626',
            'selection_color': '#E5E7EB',
            'cursor_color': '#1F2937',
            'link_color': '#311B92'
        },
        'Matrix': {
            'background_color': '#0C0C0C',
            'border_color': '#1A4B1A',
            'text_color': '#00FF00',
            'prompt_color': '#00FF00',
            'error_color': '#FF0000',
            'selection_color': '#1A4B1A',
            'cursor_color': '#00FF00',
            'link_color': '#E0F2F1'
        },
        'Monokai': {
            'background_color': '#272822',
            'border_color': '#49483E',
            'text_color': '#F8F8F2',
            'prompt_color': '#A6E22E',
            'error_color': '#F92672',
            'selection_color': '#49483E',
            'cursor_color': '#F8F8F2',
            'link_color': '#E0F2F1'
        }
    }


class Terminal(QWidget):
    output_received = pyqtSignal(str, str)  # (content, type)
    cwd_changed = pyqtSignal(str)  # New signal for CWD updates

    def __init__(self, parent=None, initial_height=300, collapsed_height=50,
                 font_size=12, padding=5, border_radius=8, initial_history=None,
                 shell_enabled=True, theme='Dark', initial_cwd=None):
        super().__init__(parent)
        self.history_lock = threading.Lock()
        self.output_received.connect(self.update_output)
        self.cwd_changed.connect(self.update_cwd)
        
        # Store configuration
        self.config = {
            'expanded_size': initial_height,
            'collapsed_size': collapsed_height,
            'font_size': font_size,
            'padding': padding,
            'border_radius': border_radius,
            'shell_enabled': shell_enabled,
            'theme': theme
        }
        
        # Initialize current working directory
        self.current_cwd = initial_cwd or os.getcwd()
        self.last_cwd = initial_cwd or os.getcwd()
        # Update theme colors
        self.config.update(TerminalThemes.THEMES[theme])
        self.terminal_parser = TerminalHandler(initial_cwd=self.current_cwd)
        self.terminal_parser.start()
        # State variables
        self.is_expanded = True
        self.history = initial_history if initial_history else []
        self.cursor_visible = True
        
        # Setup cursor blink timer
        self.cursor_timer = QTimer(self)
        self.cursor_timer.timeout.connect(self.toggle_cursor)
        self.cursor_timer.start(530)  # Standard terminal cursor blink rate
        self.terminal_printer = None
        self.init_ui()

    def init_ui(self):
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(
                self.config['padding'],
                self.config['padding'],
                self.config['padding'],
                self.config['padding']
        )
        self.main_layout.setSpacing(0)

        # Header
        self.header = QFrame()
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(8, 8, 8, 8)
        # Theme selector
        self.theme_selector = QComboBox()
        self.theme_selector.addItems(TerminalThemes.THEMES.keys())
        self.theme_selector.setCurrentText(self.config['theme'])
        self.theme_selector.currentTextChanged.connect(self.change_theme)
        self.theme_selector.setStyleSheet(f"""
                QComboBox {{
                color: {self.config['text_color']};
                background-color: {self.config['background_color']};
                border: 1px solid {self.config['border_color']};
                border-radius: 4px;
                padding: 2px 8px;
                }}
                QComboBox::drop-down {{
                border: none;
                }}
                QComboBox::down-arrow {{
                image: none;
                border: none;
                }}
        """)
        header_layout.addWidget(self.theme_selector)
        
        # Terminal text
        terminal_text = QLabel("Terminal")
        terminal_text.setFont(QFont("Consolas", self.config['font_size']))
        header_layout.addWidget(terminal_text)

        # Toggle button
        self.toggle_btn = QPushButton("▲")
        self.toggle_btn.clicked.connect(self.toggle_terminal)
        header_layout.addWidget(self.toggle_btn)
        
        self.update_header_style()
        self.main_layout.addWidget(self.header)

        # Terminal content
        self.terminal_content = QFrame()
        self.terminal_content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        content_layout = QVBoxLayout(self.terminal_content)
        content_layout.setSpacing(0)
        # Input line with cursor
        self.input_container = QWidget()
        input_layout = QHBoxLayout(self.input_container)
        input_layout.setContentsMargins(12, 6, 12, 12)
        input_layout.setSpacing(8)
        
        self.prompt_label = QLabel(f'<a style="color:{self.config['prompt_color']}" href="{self.current_cwd}">{self.current_cwd}</a>>')
        self.prompt_label.linkActivated.connect(os.startfile)
        self.prompt_label.setStyleSheet(f"border-radius: {self.config['border_radius']}px;")
        self.prompt_label.setFont(QFont("Consolas", self.config['font_size']))
        input_layout.addWidget(self.prompt_label)
        
        self.input_field = QLineEdit()
        self.input_field.setFont(QFont("Consolas", self.config['font_size']))
        self.input_field.setStyleSheet(f"""
                QLineEdit {{
                border: none;
                background-color: transparent;
                padding: 0px;
                selection-background-color: {self.config['selection_color']};
                }}
        """)
        input_layout.addWidget(self.input_field)
        
        content_layout.addWidget(self.input_container)
        
        # Scroll area for output
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        
        # Output text edit with terminal-like styling
        self.output_text_edit = QTextEdit()
        self.output_text_edit.setReadOnly(True)
        self.output_text_edit.setFont(QFont("Consolas", self.config['font_size']))
        self.output_text_edit.setWordWrapMode(QTextOption.WrapAnywhere)
        self.output_text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.config['background_color']};
                color: {self.config['text_color']};
                border: none;
                padding: 12px;
            }}
        """)
        
        # Imposta il size policy per espandersi orizzontalmente
        self.output_text_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.scroll_area.setWidget(self.output_text_edit)
        content_layout.addWidget(self.scroll_area)
        
        self.main_layout.addWidget(self.terminal_content)
        
        # Set initial size and update styles
        self.setMinimumHeight(self.config['expanded_size'])
        self.setMaximumHeight(16777215)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.update_terminal_style()

        # Connect input handler
        if self.config['shell_enabled']:
            self.input_field.returnPressed.connect(self.start_handle_command_thread)
        
        # Display initial history
        self.display_history()
        
        # Set focus to input field
        self.input_field.setFocus()

    def update_header_style(self):
        self.header.setStyleSheet(f"""
            QFrame {{
                background-color: {self.config['background_color']};
                border: 1px solid {self.config['border_color']};
                border-radius: {self.config['border_radius']}px;
                border-bottom-right-radius: 0px;
                border-bottom-left-radius: 0px;
            }}
           QLabel{{
                border-radius: {self.config['border_radius']}px;
            }}
        """)
        
        for i in range(self.header.layout().count()):
            widget = self.header.layout().itemAt(i).widget()
            if isinstance(widget, QLabel):
                widget.setStyleSheet(f"color: {self.config['text_color']};")
            elif isinstance(widget, QPushButton):
                widget.setStyleSheet(f"""
                    QPushButton {{
                        color: {self.config['text_color']};
                        border: none;
                        padding: 2px;
                        font-size: {self.config['font_size'] - 2}px;
                    }}
                """)

    def update_terminal_style(self):
        # Update terminal content styles    
        self.terminal_content.setStyleSheet(f"""
            QFrame {{
                background-color: {self.config['background_color']};
                border: 1px solid {self.config['border_color']};
                border-radius: {self.config['border_radius']}px;
                border-top-right-radius: 0px;
                border-top-left-radius: 0px;
            }}
            QLabel{{
                border-radius: {self.config['border_radius']}px;
            }}
        """)
        
        # Update scroll area styles   padding: none;     
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {self.config['background_color']};
            }}
            QScrollBar:vertical {{
                background-color: {self.config['background_color']};
                width: 10px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {self.config['border_color']};
                border-radius: 5px;
                min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
        
        # Update prompt and input field styles
        self.prompt_label.setStyleSheet(f"color: {self.config['prompt_color']};")
        self.input_field.setStyleSheet(f"""
            QLineEdit {{
                color: {self.config['text_color']};
                border: none;
                background-color: transparent;
                selection-background-color: {self.config['selection_color']};
            }}
        """)
        
        # Update output text edit style
        self.output_text_edit.setStyleSheet(f"""
            QTextEdit {{
                color: {self.config['text_color']};
                background-color: {self.config['background_color']};
                padding: 4px 13px 4px 13px;
                border: 0;
                
                
            }}
        """)

    def toggle_cursor(self):
        """Toggle the cursor visibility for the blinking effect"""
        self.cursor_visible = not self.cursor_visible
        if self.input_field.hasFocus():
            cursor_char = '█' if self.cursor_visible else ' '
            current_text = self.input_field.text()
            cursor_pos = self.input_field.cursorPosition()
            
            # Only update if necessary
            if cursor_pos == len(current_text):
                self.input_field.setCursorPosition(cursor_pos)

    def change_theme(self, theme_name):
        """Change the terminal theme"""
        self.config.update(TerminalThemes.THEMES[theme_name])
        self.config['theme'] = theme_name
        self.update_terminal_style()
        self.display_history()

        

    @pyqtSlot(str)
    def update_cwd(self, new_cwd):
        """Update the current working directory display"""
        self.last_cwd = self.current_cwd
        self.current_cwd = new_cwd
        self.prompt_label.setText(f'<a style="color:{self.config['prompt_color']}" href="{new_cwd}">{new_cwd}></a>>')

    def handle_command(self, command):
        """Process command input in separate thread"""
        if self.config['shell_enabled']:
                if command.lower() in ("cls", "clear"):
                        self.output_received.emit("", "clear")
                        return
                
                try:
                        self.terminal_parser.execute_command(command)
                        while self.terminal_parser.has_pending_commands():
                                message = self.terminal_parser.get_output()
                                if message:  # Check message first
                                        print(f"Type: {message.type}, Message: {message.content}")
                                        if message.type == OutputType.CWD:
                                                self.cwd_changed.emit(message.content)
                                        elif message.type == OutputType.ERROR:
                                                self.output_received.emit(message.content, "error")
                                        elif message.type == OutputType.STDERR:
                                                self.output_received.emit(message.content, "error")
                                        elif message.type == OutputType.INFO:
                                                print(f"\033[92m[INFO] {message.content}\033[0m")
                                        elif message.type == OutputType.STDOUT:
                                                self.output_received.emit(message.content, "output")
                                        else :
                                                self.output_received.emit("Type not recognized", "error")
                                        
                except Exception as e:
                        self.output_received.emit(str(e), "error")
        
            
    def start_handle_command_thread(self):
        """Start a new thread to handle the command"""
        command = self.input_field.text().strip()
        self.input_field.clear()
        
        if command:
            with self.history_lock:
                # Create a command group in history to keep command and its output together
                command_group = {
                    "type": "command_group",
                    "command": command,
                    "outputs": []
                }
                self.history.insert(0, command_group)
            
            # Use signal to update UI from main thread
            self.output_received.emit(command, "command")
            
            self.terminal_printer = threading.Thread(
                target=self.handle_command,
                args=(command,),
                daemon=True
            )
            self.terminal_printer.start()

    def add_to_history(self, entry_type, content, details=None):
        """Thread-safe method to add entries to history"""
        with self.history_lock:
            if entry_type == "command":
                return
                
            if self.history and isinstance(self.history[0], dict) and "outputs" in self.history[0]:
                self.history[0]["outputs"].append({
                    "type": entry_type,
                    "content": content,
                    "details": details if details else None
                })
            else:
                entry = {
                    "type": entry_type,
                    "content": content,
                    "details": details if details else None
                }
                self.history.insert(0, entry)

    def display_history(self):
        """Update the terminal display with current history"""
        output_content = ""
        
        # Make a thread-safe copy of history for display
        with self.history_lock:
            history_copy = self.history.copy()
        
        for entry in history_copy:
            if isinstance(entry, dict) and "type" in entry:
                if entry["type"] == "command_group":
                    # Display command first
                    output_content +=f'<span style="color: {self.config["prompt_color"]}"><a style="color:{self.config['prompt_color']}" href="{self.current_cwd}">{self.current_cwd}</a>> {entry["command"]}</span>'
                    # Then display all its outputs
                    for output in entry["outputs"]:
                        if output["type"] == "output":
                            output_content += f'<div style="margin: 4px 0px; white-space: pre-wrap; ">{output["content"].removeprefix(f"{self.last_cwd}>")}</div><br>'
                        elif output["type"] == "error":
                            output_content += f'<br><span style="color: {self.config["error_color"]}">{output["content"]}</span><br>'
                
                elif entry["type"] == "output":
                    output_content += f'<div style="margin: 4px 0px; white-space: pre-wrap; ">{entry["content"]}</div>'
                elif entry["type"] == "error":
                    output_content += f'<br><span style="color: {self.config["error_color"]}">{entry["content"]}</span><br>'

        self.output_text_edit.setHtml(output_content)
        

    @pyqtSlot(str, str)
    def update_output(self, content, output_type):
        """Update the terminal output (runs in main thread)"""
        if output_type == "clear":
            with self.history_lock:
                self.history = []
            self.display_history()
        else:
            self.add_to_history(output_type, content)
            self.display_history()

    def clear_history(self):
        """Thread-safe method to clear history"""
        with self.history_lock:
            self.history = []
        self.display_history()

    def set_prompt(self, prompt_text):
        """Change the terminal prompt"""
        self.prompt_label.setText(prompt_text)

    def enable_input(self, enabled=True):
        """Enable or disable terminal input"""
        self.input_field.setEnabled(enabled)
        self.input_container.setVisible(enabled)

    def focusInEvent(self, event):
        """Handle focus in event"""
        super().focusInEvent(event)
        self.input_field.setFocus()
        
    def resizeEvent(self, event):
        """Handle resize event"""
        super().resizeEvent(event)
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )

    def toggle_terminal(self):
        """Toggle terminal expansion state"""
        self.is_expanded = not self.is_expanded
        self.terminal_content.setVisible(self.is_expanded)
        self.toggle_btn.setText("▲" if self.is_expanded else "▼")
        
        # Animate the height change
        height = (
            #self.config['expanded_size'] if self.is_expanded 
            16777215 if self.is_expanded
            else self.config['collapsed_size']
        )
        self.setMinimumHeight(height)
        self.setMaximumHeight(height)
        
        # Set focus to input field when expanded
        if self.is_expanded:
            self.input_field.setFocus()

