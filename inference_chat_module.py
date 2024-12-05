import sys
import json
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
class ModelConfig:
    def __init__(self, name: str):
        self.name = name
        self.config = self._get_model_config()
    
    def _get_model_config(self) -> Dict:
        try:
            response = ollama.show(model=self.name)
            return response
        except Exception as e:
            print(f"Error getting model config: {e}")
            return {}
    
    @property
    def is_multimodal(self) -> bool:
        # Check model capabilities from metadata
        return "projector_info" in self.config

    @property
    def context_window(self) -> int:
        # Get context window size from model config
        return self.config.get('context_length', 4096)

class ModelManager(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Model Manager")
        self.setModal(True)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['background']};
                color: {COLORS['text']};
            }}
            QGroupBox {{
                border: 2px solid {COLORS['secondary']};
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 20px;
                color: {COLORS['text']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }}
            QLabel {{
                color: {COLORS['text']};
            }}
            QComboBox {{
                background-color: {COLORS['surface']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['secondary']};
                border-radius: 4px;
                padding: 5px;
            }}
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['secondary']};
            }}
            QCheckBox {{
                color: {COLORS['text']};
            }}
        """)
        
        # Create scroll area for parameters
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        main_widget = QWidget()
        self.layout = QVBoxLayout(main_widget)
        
        # Model selection group
        model_group = QGroupBox("Model Selection")
        model_layout = QHBoxLayout()
        
        self.model_combo = QComboBox()
        self.refresh_button = QPushButton()
        self.refresh_button.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        self.refresh_button.clicked.connect(self.refresh_models)
        
        model_layout.addWidget(self.model_combo)
        model_layout.addWidget(self.refresh_button)
        model_group.setLayout(model_layout)
        
        # Sampling parameters group
        sampling_group = QGroupBox("Sampling Parameters")
        sampling_layout = QGridLayout()
        
        # Temperature
        self.temperature = ThemedDoubleSpinBox()
        self.temperature.setRange(0.0, 2.0)
        self.temperature.setValue(0.8)
        self.temperature.setSingleStep(0.1)
        sampling_layout.addWidget(QLabel("Temperature:"), 0, 0)
        sampling_layout.addWidget(self.temperature, 0, 1)
        
        # Top-K
        self.top_k = ThemedSpinBox()
        self.top_k.setRange(0, 100)
        self.top_k.setValue(40)
        sampling_layout.addWidget(QLabel("Top K:"), 1, 0)
        sampling_layout.addWidget(self.top_k, 1, 1)
        
        # Top-P
        self.top_p = ThemedDoubleSpinBox()
        self.top_p.setRange(0.0, 1.0)
        self.top_p.setValue(0.9)
        self.top_p.setSingleStep(0.05)
        sampling_layout.addWidget(QLabel("Top P:"), 2, 0)
        sampling_layout.addWidget(self.top_p, 2, 1)
        
        # Min-P
        self.min_p = ThemedDoubleSpinBox()
        self.min_p.setRange(0.0, 1.0)
        self.min_p.setValue(0.05)
        self.min_p.setSingleStep(0.01)
        sampling_layout.addWidget(QLabel("Min P:"), 3, 0)
        sampling_layout.addWidget(self.min_p, 3, 1)
        
        sampling_group.setLayout(sampling_layout)
        
        # Context parameters group
        context_group = QGroupBox("Context Parameters")
        context_layout = QGridLayout()
        
        # Context window
        self.num_ctx = ThemedSpinBox()
        self.num_ctx.setRange(512, 8192)
        self.num_ctx.setValue(2048)
        self.num_ctx.setSingleStep(512)
        context_layout.addWidget(QLabel("Context Window:"), 0, 0)
        context_layout.addWidget(self.num_ctx, 0, 1)
        
        # Repeat penalty
        self.repeat_penalty = ThemedDoubleSpinBox()
        self.repeat_penalty.setRange(0.0, 2.0)
        self.repeat_penalty.setValue(1.1)
        self.repeat_penalty.setSingleStep(0.1)
        context_layout.addWidget(QLabel("Repeat Penalty:"), 1, 0)
        context_layout.addWidget(self.repeat_penalty, 1, 1)
        
        context_group.setLayout(context_layout)
        
        # Mirostat parameters group
        mirostat_group = QGroupBox("Mirostat Parameters")
        mirostat_layout = QGridLayout()
        
        # Mirostat mode
        self.mirostat = ThemedSpinBox()
        self.mirostat.setRange(0, 2)
        self.mirostat.setValue(0)
        mirostat_layout.addWidget(QLabel("Mirostat Mode:"), 0, 0)
        mirostat_layout.addWidget(self.mirostat, 0, 1)
        
        # Mirostat tau
        self.mirostat_tau = ThemedDoubleSpinBox()
        self.mirostat_tau.setRange(0.0, 10.0)
        self.mirostat_tau.setValue(5.0)
        self.mirostat_tau.setSingleStep(0.1)
        mirostat_layout.addWidget(QLabel("Mirostat Tau:"), 1, 0)
        mirostat_layout.addWidget(self.mirostat_tau, 1, 1)
        
        # Mirostat eta
        self.mirostat_eta = ThemedDoubleSpinBox()
        self.mirostat_eta.setRange(0.0, 1.0)
        self.mirostat_eta.setValue(0.1)
        self.mirostat_eta.setSingleStep(0.01)
        mirostat_layout.addWidget(QLabel("Mirostat Eta:"), 2, 0)
        mirostat_layout.addWidget(self.mirostat_eta, 2, 1)
        
        mirostat_group.setLayout(mirostat_layout)
        
        # Add all groups to main layout
        self.layout.addWidget(model_group)
        self.layout.addWidget(sampling_group)
        self.layout.addWidget(context_group)
        self.layout.addWidget(mirostat_group)
        
        # Apply button
        self.apply_button = QPushButton("Apply Settings")
        self.apply_button.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))
        self.apply_button.clicked.connect(self.accept)
        self.layout.addWidget(self.apply_button)
        
        scroll.setWidget(main_widget)
        
        # Main dialog layout
        dialog_layout = QVBoxLayout(self)
        dialog_layout.addWidget(scroll)
        
        self.refresh_models()
        
    def refresh_models(self):
        try:
            models = ollama.list()['models']
            self.model_combo.clear()
            for model in models:
                self.model_combo.addItem(model['model'])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to fetch models: {e}")
    
    def get_settings(self) -> Dict:
        return {
            'model': self.model_combo.currentText(),
            'temperature': self.temperature.value(),
            'top_k': self.top_k.value(),
            'top_p': self.top_p.value(),
            'min_p': self.min_p.value(),
            'num_ctx': self.num_ctx.value(),
            'repeat_penalty': self.repeat_penalty.value(),
            'mirostat': self.mirostat.value(),
            'mirostat_tau': self.mirostat_tau.value(),
            'mirostat_eta': self.mirostat_eta.value()
        }

class ChatThread(QThread):
    """Enhanced thread for handling Ollama API calls"""
    token_received = pyqtSignal(str)  # Changed to emit individual tokens
    error_occurred = pyqtSignal(str)
    finished_streaming = pyqtSignal()
    
    def __init__(self, message, context=None, model_settings=None):
        super().__init__()
        self.message = message
        self.context = context or []
        self.model_settings = model_settings or {}
        token_received = pyqtSignal(str)
        error_occurred = pyqtSignal(str)
        finished_streaming = pyqtSignal()
    
    def encode_image(self, image_path):
        """Convert image file to base64"""
        try:
            with open(image_path, 'rb') as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            print(f"Error encoding image: {e}")
            raise
    
    def run(self):
        try:
            options = {
                'num_thread': self.model_settings.get('num_threads', 4),
                'num_gpu': self.model_settings.get('gpu_layers', 50),
                'num_batch': self.model_settings.get('batch_size', 8),
                'offload': self.model_settings.get('ram_offload', False),
            }
            
            if isinstance(self.message, dict) and 'image' in self.message:
                message = {
                    'role': 'user',
                    'content': self.message['text'],
                    'images': [self.message['image']]
                }
            else:
                message = {
                    'role': 'user',
                    'content': self.message
                }
            
            stream = ollama.chat(
                model=self.model_settings.get('model'),
                messages=self.context + [message],
                stream=True#,
                #options=options
            )
            
            for chunk in stream:
                if 'message' in chunk and 'content' in chunk['message']:
                    # Emit tokens as they arrive from the model
                    self.token_received.emit(chunk['message']['content'])
            
            self.finished_streaming.emit()
            
        except Exception as e:
            self.error_occurred.emit(str(e))


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
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Advanced Ollama Chat")
        self.resize(1000, 800)
        
        # Initialize model manager and settings
        self.model_settings = {}
        self.current_model_config = None
        self.conversation_context = []
        self.message_stream = ""
        
        # Create UI
        self.setup_ui()
        self.image_button.setVisible(True)
        
        # Check connection and load initial model
        self.check_ollama_connection()
        self.show_model_manager()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Model info bar
        model_bar = QHBoxLayout()
        self.model_label = QLabel("No model selected")
        self.model_button = QPushButton("Change Model")
        self.model_button.clicked.connect(self.show_model_manager)
        model_bar.addWidget(self.model_label)
        model_bar.addWidget(self.model_button)
        layout.addLayout(model_bar)
        
        # Chat display
        self.chat_display = ChatWidget()
        layout.addWidget(self.chat_display)
        
        # Input area
        input_layout = QHBoxLayout()
        
        # Image attachment button
        self.image_button = ImageAttachButton()
        
        # Text input
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type your message here...")
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field)
        
        # Send button
        self.send_button = SendButton()
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.image_button)
        input_layout.addWidget(self.send_button)
        
        layout.addLayout(input_layout)
        
        # Apply styles
        self.apply_styles()
    
    def apply_styles(self):
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['background']};
            }}
            QTextBrowser {{
                background-color: {COLORS['surface']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['secondary']};
                border-radius: 5px;
                padding: 10px;
                font-family: 'Segoe UI', Arial, sans-serif;
                selection-background-color: {COLORS['primary']};
            }}
            QLineEdit {{
                padding: 10px;
                border: 2px solid {COLORS['secondary']};
                border-radius: 5px;
                font-size: 14px;
                background-color: {COLORS['surface']};
                color: {COLORS['text']};
            }}
            QLineEdit:focus {{
                border-color: {COLORS['primary']};
            }}
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['secondary']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['surface']};
            }}
            QPushButton:disabled {{
                background-color: {COLORS['surface']};
                color: {COLORS['secondary']};
            }}
            QLabel {{
                color: {COLORS['text']};
            }}
        """)
    
    def show_model_manager(self):
        dialog = ModelManager(self)
        if dialog.exec_() == QDialog.Accepted:
            self.model_settings = dialog.get_settings()
            self.current_model_config = ModelConfig(self.model_settings['model'])
            
            # Update UI based on model capabilities
            self.image_button.setVisible(self.current_model_config.is_multimodal)
            self.model_label.setText(f"Model: {self.model_settings['model']}")
            
            # Clear conversation when switching models
            self.conversation_context = []
            self.chat_display.clear()
    
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
        else:
            content = message
        
        # Display user message
        if self.image_button.current_image:
            self.chat_display.add_image_message(
                image_path=self.image_button.current_image,
                message=message,
                is_user=True
            )
            self.conversation_context.append({
                "role": "user",
                "content": f"{message}",  # [Image: {(Path(self.image_button.current_image).name)}]
                "images": [self.image_button.current_image]
            })
        else:
            self.chat_display.add_message(message, is_user=True)
            self.conversation_context.append({
                "role": "user",
                "content": message
            })
        
        # Prepare for streaming
        self.message_stream = ""
        
        # Disable input controls
        self.input_field.clear()
        self.input_field.setEnabled(False)
        self.send_button.setEnabled(False)
        self.image_button.setEnabled(False)
        
        # Initialize streaming
        self.chat_display.message_container.begin_streaming()
        
        # Start generation thread
        self.generate_thread = ChatThread(message=content, context=self.conversation_context, model_settings=self.model_settings)
        self.generate_thread.token_received.connect(self.handle_token)
        self.generate_thread.error_occurred.connect(self.handle_error)
        self.generate_thread.finished_streaming.connect(self.finish_streaming)
        self.generate_thread.start()
    
    def handle_token(self, token):
        self.message_stream += token
        self.chat_display.message_container.update_stream(token=token, ended=False)
    
    def finish_streaming(self):
        self.chat_display.message_container.update_stream(token="", ended=True)
        self.conversation_context.append({
            "role": "assistant",
            "content": self.message_stream
        })
        self.message_stream = ""
        self.enable_input()
        if self.image_button.current_image:
            self.image_button.clear_image()
    
    def enable_input(self):
        self.input_field.setEnabled(True)
        self.send_button.setEnabled(True)
        self.image_button.setEnabled(True)
        self.input_field.setFocus()
    
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
        self.chat_display.simulate_stream_response(f"ERROR: {error_text}")
        QMessageBox.warning(self, "Error", error_text)
        self.input_field.setEnabled(True)
        self.send_button.setEnabled(True)
        self.input_field.setFocus()

def main():
    app = QApplication(sys.argv)
    app.setFont(QFont('Segoe UI', 10))
    
    # Create a main window and add the chat widget
    main_window = QMainWindow()
    chat_widget = EnhancedChatWidget()
    main_window.setCentralWidget(chat_widget)
    main_window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()