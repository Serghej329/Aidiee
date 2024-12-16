import sys
import json
import os
import base64
from pathlib import Path
from typing import Optional, List, Dict
import ollama
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QTextBrowser, QLineEdit, QPushButton, QLabel,
                            QMessageBox, QHBoxLayout, QComboBox, QFileDialog,
                            QSpinBox, QDoubleSpinBox, QCheckBox, QDialog,
                            QGroupBox, QGridLayout, QScrollArea, QStyle)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor, QPixmap,QImage
from io import BytesIO
from message_box_module import ChatWidget
from python_highlighter import SyntaxThemes
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Generator
import ollama
import google.generativeai as genai
import model_manager_module as ModelTools
COLORS = {
    'primary': '#c678dd',  # Purple
    'text': '#abb2bf',     # Light gray
    'secondary': '#5c6370', # Mid gray
    'surface': '#32363e',   # Dark gray
    'background': '#282c34' # Darker gray
}
class ThemedSpinBox(QSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QSpinBox {{
                background-color: {COLORS['surface']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['secondary']};
                border-radius: 4px;
                padding: 5px;
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                background-color: {COLORS['secondary']};
                border: none;
            }}
        """)

class ThemedDoubleSpinBox(QDoubleSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QDoubleSpinBox {{
                background-color: {COLORS['surface']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['secondary']};
                border-radius: 4px;
                padding: 5px;
            }}
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
                background-color: {COLORS['secondary']};
                border: none;
            }}
        """)



class ChatThread(QThread):
    """Enhanced thread for handling multiple model providers"""
    token_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    finished_streaming = pyqtSignal()
    
    def __init__(self, message, context=None, model_manager=None, settings=None):
        super().__init__()
        self.message = message
        self.context = context or []
        self.model_manager = model_manager
        self.settings = settings or {}
    
    def run(self):
        try:
            if isinstance(self.message, dict) and 'image' in self.message:
                message = {
                    'role': 'user',
                    'content': {
                        'text': self.message['text'],
                        'images': [self.message['image']]
                    }
                }
            else:
                message = {
                    'role': 'user',
                    'content': self.message
                }
            
            stream = self.model_manager.generate_stream(
                messages=self.context + [message],
                settings=self.settings
            )
            
            for response in stream:
                self.token_received.emit(response.text)
            
            self.finished_streaming.emit()
            
        except Exception as e:
            self.error_occurred.emit(str(e))

class ModelConfig:
    """Updated model configuration class"""
    def __init__(self, model_manager, provider: str, model: str):
        self.model_manager = model_manager
        self.provider = provider
        self.name = model
        self.info = self._get_model_info()
    
    def _get_model_info(self) -> Dict:
        try:
            self.model_manager.set_current_model(self.provider, self.name)
            return self.model_manager.get_current_model_info()
        except Exception as e:
            print(f"Error getting model info: {e}")
            return {}
    
    @property
    def is_multimodal(self) -> bool:
        return self.info.get('is_multimodal', False)
    
    @property
    def context_window(self) -> int:
        return self.info.get('context_length', 4096)

class IconProvider:
    @staticmethod
    def get_send_icon():
        svg_data = '''
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <path fill="#c678dd" d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
</svg>
'''
        return QIcon(QPixmap.fromImage(QImage.fromData(svg_data.encode())))

    @staticmethod
    def get_attach_icon():
        svg_data = '''
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <path fill="#c678dd" d="M16.5 6v11.5c0 2.21-1.79 4-4 4s-4-1.79-4-4V5c0-1.38 1.12-2.5 2.5-2.5s2.5 1.12 2.5 2.5v10.5c0 .55-.45 1-1 1s-1-.45-1-1V6H10v9.5c0 1.38 1.12 2.5 2.5 2.5s2.5-1.12 2.5-2.5V5c0-2.21-1.79-4-4-4S7 2.79 7 5v12.5c0 3.04 2.46 5.5 5.5 5.5s5.5-2.46 5.5-5.5V6h-1.5z"/>
</svg>
'''
        return QIcon(QPixmap.fromImage(QImage.fromData(svg_data.encode())))

class ThemedIconButton(QPushButton):
    def __init__(self, icon, size=QSize(40, 40), parent=None):
        super().__init__(parent)
        self.setIcon(icon)
        self.setIconSize(QSize(24, 24))
        self.setFixedSize(size)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['surface']};
                border: 2px solid {COLORS['secondary']};
                border-radius: {size.width()//2}px;
                padding: 5px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['secondary']};
                border-color: {COLORS['primary']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['primary']};
            }}
        """)
class ImageAttachButton(ThemedIconButton):
    def __init__(self, parent=None):
        super().__init__(IconProvider.get_attach_icon(), parent=parent)
        self.clicked.connect(self.select_image)
        self.current_image: Optional[str] = None
    
    def select_image(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "", "Images (*.png *.jpg *.jpeg)"
        )
        if file_name:
            self.set_image(file_name)
            # Visual feedback when image is selected
            self.setStyleSheet(self.styleSheet() + f"""
                QPushButton {{
                    border-color: {COLORS['primary']};
                }}
            """)
    
    def set_image(self, file_path: str):
        self.current_image = file_path
    
    def clear_image(self):
        self.current_image = None
        self.setStyleSheet(self.styleSheet())

class SendButton(ThemedIconButton):
    def __init__(self, parent=None):
        super().__init__(IconProvider.get_send_icon(), parent=parent)

class EnhancedChatWidget(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.setWindowTitle("Advanced Ollama Chat")
        self.resize(1000, 800)
        self.parent = parent
        self.theme = SyntaxThemes().tokyo_night
        
        # Initialize model manager and settings
        self.model_settings = {}
        self.current_model_config = None
        self.conversation_context = []
        self.message_stream = ""
        self.current_message = None
        self.code_blocks = []
        
        # Create UI
        self.setup_ui()
        self.image_button.setVisible(True)

        # Initialize model manager with providers
        self.model_manager = ModelTools.ModelManager()
        self.model_manager.add_provider('ollama', ModelTools.OllamaProvider())
        
        # Add Gemini provider if API key is available
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        if gemini_api_key:
                self.model_manager.add_provider('gemini', ModelTools.GeminiProvider(gemini_api_key))
        # Check connection and load initial model
        self.check_ollama_connection()
        self.show_model_manager()
        
    def add_suggestion_tab(self, editor, suggestion_number):
        """Handle code blocks in voice assistant context"""
        if hasattr(self.parent, 'add_suggestion_tab'):
            self.parent.add_suggestion_tab(editor=editor, suggestion_number=suggestion_number)
        else:
            # If we're not in the IDE context, just show the code in a read-only editor
            editor.show()
    
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 5, 10, 5)
        main_layout.setSpacing(0)
        
        # Set the background color for the entire widget
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {self.theme['main_background']};
            }}
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QScrollBar:vertical {{
                background-color: {self.theme['main_background']};
                width: 12px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {self.theme['description_background']};
                border-radius: 6px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {self.theme['highlight']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background-color: transparent;
            }}
            QTextEdit {{
                background-color: {self.theme['main_background']};
                border: none;
                border-radius: 5px;
                padding: 8px;
                color: {self.theme['main_foreground']};
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
            }}
        """)
        
        # Model info bar
        model_bar = QWidget()
        model_bar_layout = QHBoxLayout(model_bar)
        model_bar_layout.setContentsMargins(10, 10, 10, 0)
        self.model_label = QLabel("No model selected")
        self.model_button = QPushButton("Change Model")
        self.model_button.clicked.connect(self.show_model_manager)
        model_bar_layout.addWidget(self.model_label)
        model_bar_layout.addWidget(self.model_button)
        main_layout.addWidget(model_bar)
        
        # Chat area
        self.chat_widget = ChatWidget(aidee = self.parent)
        main_layout.addWidget(self.chat_widget)
        
        # Input area
        input_container = QWidget()
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(10, 10, 10, 10)
        
        # Image attachment button
        self.image_button = ImageAttachButton(self)
        input_layout.addWidget(self.image_button)
        
        # Text input
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type your message...")
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field)
        
        # Send button
        self.send_button = SendButton()
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)
        
        main_layout.addWidget(input_container)
        
    def send_message(self):
        if not self.current_model_config:
                QMessageBox.warning(self, "Error", "Please select a model first")
                return
                
        message = self.input_field.text().strip()
        if not message and not self.image_button.current_image:
                return
                
        # Prepare message content
        if self.image_button.current_image:
                content = {
                "text": message or "What's in this image?",
                "image": self.image_button.current_image
                }
                self.conversation_context.append({
                "role": "user",
                "content": f"{message}",
                "images": [self.image_button.current_image]
                })
                self.chat_widget.add_image_message(self.image_button.current_image, message, is_user=True)
                self.image_button.clear_image()
        else:
                content = message
                self.conversation_context.append({
                "role": "user",
                "content": message
                })
                self.chat_widget.add_message(message, is_user=True)
        
        self.input_field.clear()
        self.input_field.setEnabled(False)
        self.send_button.setEnabled(False)
        self.image_button.setEnabled(False)
        
        # Start assistant message
        self.current_message = self.chat_widget.message_container.current_stream_message
        if self.current_message:
                self.current_message.start_thinking()
        
        # Create and start chat thread with the model manager
        self.chat_thread = ChatThread(
                content, 
                self.conversation_context, 
                self.model_manager,  # Pass the model manager instead of settings
                {}  # Empty settings dict for now - you can add model-specific settings here if needed
        )
        self.chat_thread.token_received.connect(self.handle_token)
        self.chat_thread.error_occurred.connect(self.handle_error)
        self.chat_thread.finished_streaming.connect(self.finish_streaming)
        self.chat_thread.start()
        
    def handle_token(self, token):
        """Handle incoming token from the chat thread"""
        if not self.current_message:
            self.chat_widget.message_container.begin_streaming()
            self.current_message = self.chat_widget.message_container.current_stream_message
            if self.current_message:
                self.current_message.start_thinking()
        
        self.chat_widget.message_container.update_stream(token)
        
    def finish_streaming(self):
        """Handle end of streaming"""
        if self.current_message:
            self.current_message.stop_thinking()
        self.chat_widget.message_container.update_stream("", ended=True)
        self.enable_input()
        self.current_message = None
        
    def enable_input(self):
        """Re-enable input controls after message is sent"""
        self.input_field.setEnabled(True)
        self.send_button.setEnabled(True)
        self.image_button.setEnabled(True)
        self.input_field.setFocus()
    
    def show_model_manager(self):
        model_manager = ModelTools.ModelManager()
        model_info = model_manager.show_dialog()
        
        if model_info:
                provider = model_info['provider']
                model_name = model_info['model']
                
                # Update model managers and configurations
                if provider == 'gemini' and model_info['api_key']:
                        self.model_manager.add_provider('gemini', ModelTools.GeminiProvider(model_info['api_key']))
                
                self.current_model_config = ModelConfig(
                self.model_manager,
                        provider,
                        model_name
                )
                
                # Update UI
                self.image_button.setVisible(self.current_model_config.is_multimodal)
                self.model_label.setText(f"Model: {model_name}")
                
                # Clear conversation when switching models
                self.conversation_context = []
                self.chat_widget.clear()
    
    def check_ollama_connection(self):
        try:
            ollama.list()
        except ConnectionRefusedError:
            QMessageBox.critical(
                self,
                "Connection Error",
                "Could not connect to Ollama server.\n\n"
                "Please make sure to:\n"
                "1. Start the Ollama application\n"
                "2. Wait for it to fully load\n"
                "3. Try running this application again"
            )
            sys.exit(1)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred while connecting to Ollama:\n{str(e)}"
            )
            sys.exit(1)
    
    def handle_error(self, error_text):
        self.chat_widget.simulate_stream_response(f"ERROR: {error_text}")
        self.chat_widget.message_container.update_stream("", ended=True)
        QMessageBox.warning(self, "Error", error_text)
        self.input_field.setEnabled(True)
        self.send_button.setEnabled(True)
        self.image_button.setEnabled(True)
        self.input_field.setFocus()

def main():
    app = QApplication(sys.argv)
    app.setFont(QFont('Segoe UI', 10))
    
    # Create a main window and add the chat widget
    main_window = QMainWindow()
    chat_widget = EnhancedChatWidget(parent=main_window)
    main_window.setCentralWidget(chat_widget)
    main_window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()