import sys,os,json
from typing import Optional, Dict, List
import ollama
import google.generativeai as genai
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QPushButton, QComboBox, QStackedWidget,
                           QMessageBox, QGroupBox, QRadioButton, QButtonGroup,QWidget,QCheckBox)
from PyQt5.QtCore import Qt
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Generator
import base64
COLORS = {
    'primary': '#c678dd',    # Purple
    'text': '#abb2bf',       # Light gray
    'secondary': '#5c6370',  # Mid gray
    'surface': '#32363e',    # Dark gray
    'background': '#282c34'  # Darker gray
}
class ModelResponse:
    """Unified response object for different model providers"""
    def __init__(self, text: str, raw_response: any = None):
        self.text = text
        self.raw_response = raw_response

class ModelProvider(ABC):
    """Abstract base class for model providers"""
    @abstractmethod
    def list_models(self) -> List[Dict]:
        """List available models"""
        pass
    
    @abstractmethod
    def generate_stream(self, messages: List[Dict], model: str, settings: Dict) -> Generator:
        """Stream model responses"""
        pass
    
    @abstractmethod
    def get_model_info(self, model_name: str) -> Dict:
        """Get model capabilities and information"""
        pass

class OllamaProvider(ModelProvider):
    """Ollama-specific implementation"""
    def list_models(self) -> List[Dict]:
        models = ollama.list()['models']
        return [{'name': m['model'], 'provider': 'ollama'} for m in models]
    
    def generate_stream(self, messages: List[Dict], model: str, settings: Dict) -> Generator:
        stream = ollama.chat(
            model=model,
            messages=messages,
            stream=True,
            **settings
        )
        for chunk in stream:
            if 'message' in chunk and 'content' in chunk['message']:
                yield ModelResponse(chunk['message']['content'])
    
    def get_model_info(self, model_name: str) -> Dict:
        info = ollama.show(model=model_name)
        return {
            'name': model_name,
            'provider': 'ollama',
            'is_multimodal': "projector_info" in info,
            'context_length': info.get('context_length', 4096)
        }

class GeminiProvider(ModelProvider):
    """Google AI Studio (Gemini) implementation"""
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.available_models = {
            'gemini-2.0-flash-exp': {'multimodal': True, 'context_length': 8192},
            'gemini-1.5-flash': {'multimodal': False, 'context_length': 4096},
            'gemini-1.5-pro': {'multimodal': False, 'context_length': 4096}
        }
    
    def list_models(self) -> List[Dict]:
        return [{'name': name, 'provider': 'gemini'} for name in self.available_models.keys()]
    
    def generate_stream(self, messages: List[Dict], model: str, settings: Dict) -> Generator:
        # Convert settings to Gemini format
        gemini_settings = {
            'temperature': settings.get('temperature', 0.8),
            'top_k': settings.get('top_k', 40),
            'top_p': settings.get('top_p', 0.9),
        }
        
        model_instance = genai.GenerativeModel(model)
        
        # Convert messages to Gemini format
        prompt = self._convert_messages_to_prompt(messages)
        
        response = model_instance.generate_content(
            prompt,
            stream=True,
        )
        
        for chunk in response:
            if chunk.text:
                yield ModelResponse(chunk.text)
    
    def get_model_info(self, model_name: str) -> Dict:
        if model_name not in self.available_models:
            raise ValueError(f"Unknown model: {model_name}")
        
        model_info = self.available_models[model_name]
        return {
            'name': model_name,
            'provider': 'gemini',
            'is_multimodal': model_info['multimodal'],
            'context_length': model_info['context_length']
        }
    
    def _convert_messages_to_prompt(self, messages: List[Dict]) -> str:
        """Convert chat messages to Gemini prompt format"""
        result = []
        for msg in messages:
            role_prefix = "User: " if msg['role'] == 'user' else "Assistant: "
            content = msg['content']
            if isinstance(content, dict) and 'text' in content:
                content = content['text']
            result.append(f"{role_prefix}{content}")
        return "\n".join(result)
    
class ConfigManager:
    """Manages persistent configuration storage"""
    def __init__(self):
        self.config_dir = os.path.expanduser('~/.config/ollama-chat')
        self.config_file = os.path.join(self.config_dir, 'config.json')
        self._ensure_config_dir()
        self.config = self._load_config()

    def _ensure_config_dir(self):
        """Create config directory if it doesn't exist"""
        os.makedirs(self.config_dir, exist_ok=True)

    def _load_config(self) -> Dict:
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}

    def save_config(self):
        """Save current configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f)

    def get_api_key(self, provider: str) -> Optional[str]:
        """Get stored API key for provider"""
        return self.config.get('api_keys', {}).get(provider)

    def set_api_key(self, provider: str, api_key: str):
        """Store API key for provider"""
        if 'api_keys' not in self.config:
            self.config['api_keys'] = {}
        self.config['api_keys'][provider] = api_key
        self.save_config()


class APIKeyWidget(QWidget):
    """Widget for managing API key input and verification"""
    def __init__(self, provider: str, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self.provider = provider
        self.config_manager = config_manager
        self.setup_ui()
        self.load_saved_key()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText(f"Enter {self.provider} API Key")
        self.key_input.setEchoMode(QLineEdit.Password)
        self.key_input.textChanged.connect(self.on_key_changed)  # Add this line

        self.edit_button = QPushButton("Edit")
        self.edit_button.setVisible(False)
        self.edit_button.clicked.connect(self.enable_editing)

        self.status_label = QLabel()
        self.status_label.setFixedWidth(20)

        self.is_verified = False
        layout.addWidget(self.key_input)
        layout.addWidget(self.edit_button)
        layout.addWidget(self.status_label)

    def load_saved_key(self):
        """Load and verify saved API key"""
        api_key = self.config_manager.get_api_key(self.provider)
        if api_key:
            self.key_input.setText(api_key)
            self.verify_key(api_key)

    def on_key_changed(self, text):
        """Handle key changes and save if valid"""
        if text:
            if self.verify_key(text):
                self.config_manager.set_api_key(self.provider, text)
                self.config_manager.save_config()  # Make sure to save after setting
        else:
            self.set_unverified()

    def verify_key(self, api_key: str) -> bool:
        """Verify API key validity"""
        try:
            if self.provider == 'gemini':
                genai.configure(api_key=api_key)
                # Try to list models to verify key
                list(genai.list_models())
                self.set_verified()
                return True
            return False
        except Exception:
            self.set_unverified()
            return False

    def set_verified(self):
        """Set UI state for verified key"""
        self.status_label.setStyleSheet("color: #4CAF50")  # Green color
        self.status_label.setText("✓")
        self.key_input.setReadOnly(True)
        self.edit_button.setVisible(True)
        self.is_verified = True
        self.key_input.setStyleSheet(f"background-color: {COLORS['surface']}; color: #4CAF50")

    def set_unverified(self):
        """Set UI state for unverified key"""
        self.status_label.setText("")
        self.key_input.setReadOnly(False)
        self.edit_button.setVisible(False)
        self.key_input.setStyleSheet("")

    def enable_editing(self):
        """Enable API key editing"""
        self.key_input.setReadOnly(False)
        self.edit_button.setVisible(False)
        self.status_label.setText("")
        self.key_input.setStyleSheet("")

    def get_api_key(self) -> Optional[str]:
        """Get current API key"""
        return self.key_input.text()
    
class ModelSelectionDialog(QDialog):
    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Model Selection")
        self.setModal(True)
        self.resize(500, 300)
        self.config_manager = config_manager
        self.selected_provider = None
        self.selected_model = None
        
        self.setup_ui()
        self.setup_styles()
        self.load_available_models()
        
    def setup_styles(self):
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['background']};
                color: {COLORS['text']};
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
                min-width: 200px;
                min-height: 30px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {COLORS['text']};
            }}
            QPushButton {{
                background-color: {COLORS['surface']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['secondary']};
                border-radius: 4px;
                padding: 8px 16px;
                min-height: 30px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['secondary']};
                border-color: {COLORS['primary']};
            }}
            QLineEdit {{
                background-color: {COLORS['surface']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['secondary']};
                border-radius: 4px;
                padding: 5px;
                min-height: 30px;
            }}
            QGroupBox {{
                color: {COLORS['text']};
                border: 1px solid {COLORS['secondary']};
                border-radius: 4px;
                margin-top: 1em;
                padding-top: 1em;
            }}
            QCheckBox {{
                color: {COLORS['text']};
                border-radius: 5px;
            }}
            QCheckBox::indicator:checked {{
                background-color: green;
                border: 2px solid {COLORS['text']};
                
            }}
            QCheckBox::indicator{{
                width: 10px;
                height: 10px;
                border-radius: 5px;
            }}
        """)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Model selection at the top
        model_group = QGroupBox("Select Model")
        model_layout = QVBoxLayout()
        
        self.model_combo = QComboBox()
        self.model_combo.currentIndexChanged.connect(self.on_model_selected)
        
        model_layout.addWidget(self.model_combo)
        model_group.setLayout(model_layout)
        
        # API Keys section
        keys_group = QGroupBox("API Keys")
        keys_layout = QVBoxLayout()
        
        # Gemini API section
        gemini_layout = QHBoxLayout()
        self.api_key_widget = APIKeyWidget('gemini', self.config_manager)
        self.api_key_widget.key_input.textChanged.connect(self.on_gemini_key_changed)
        self.gemini_check = QCheckBox("Gemini API")
        if self.api_key_widget.is_verified:
            self.gemini_check.setChecked(True)
        else:
            self.gemini_check.setChecked(False)

        
        gemini_layout.addWidget(self.gemini_check)
        gemini_layout.addWidget(self.api_key_widget)
        
        # Ollama status section
        ollama_layout = QHBoxLayout()
        self.ollama_check = QCheckBox("Ollama Available")
        self.ollama_check.setEnabled(False)
        self.check_ollama_availability()
        
        ollama_layout.addWidget(self.ollama_check)
        ollama_layout.addStretch()
        
        keys_layout.addLayout(gemini_layout)
        keys_layout.addLayout(ollama_layout)
        keys_group.setLayout(keys_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")
        
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        
        # Add all widgets to main layout
        layout.addWidget(model_group)
        layout.addWidget(keys_group)
        layout.addStretch()
        layout.addLayout(button_layout)
    
    def check_ollama_availability(self):
        """Check if Ollama is available and update UI accordingly"""
        try:
            ollama.list()
            self.ollama_check.setChecked(True)
            return True
        except Exception:
            self.ollama_check.setChecked(False)
            return False

    def on_gemini_key_changed(self, text):
        """Handle Gemini API key changes"""
        if text:
            try:
                genai.configure(api_key=text)
                # Try to list models to verify key
                list(genai.list_models())
                self.gemini_check.setChecked(True)
                self.load_available_models()  # Reload models when key is valid
            except Exception:
                self.gemini_check.setChecked(False)
        else:
            self.gemini_check.setChecked(False)
    
    def on_model_selected(self, index):
        """Handle model selection changes"""
        if index >= 0:
            model_text = self.model_combo.currentText()
            if " (Gemini)" in model_text:
                self.selected_provider = 'gemini'
                self.selected_model = model_text.replace(" (Gemini)", "")
            else:
                self.selected_provider = 'ollama'
                self.selected_model = model_text.replace(" (Ollama)", "")
    
    def load_available_models(self):
        """Load available models from all providers"""
        self.model_combo.clear()
        
        # Load Ollama models
        if self.check_ollama_availability():
            try:
                ollama_models = ollama.list()['models']
                for model in ollama_models:
                    self.model_combo.addItem(f"{model['model']} (Ollama)")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to fetch Ollama models: {str(e)}")

        # Load Gemini models if API key is valid
        if self.api_key_widget.is_verified:
            try:
                for model in genai.list_models():
                    if "generateContent" in model.supported_generation_methods:
                        self.model_combo.addItem(f"{model.name.replace('models/', '')} (Gemini)")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to fetch Gemini models: {str(e)}")

    def accept(self):
        if not self.selected_model or not self.selected_provider:
                QMessageBox.warning(self, "Error", "Please select a model")
                return
    
        if self.selected_provider == 'gemini':
                if not self.gemini_check.isChecked():
                        QMessageBox.warning(self, "Error", "Please enter a valid Gemini API key")
                        return
                # Save the API key one final time to ensure it's persisted
                api_key = self.api_key_widget.get_api_key()
                if api_key:
                        self.config_manager.set_api_key('gemini', api_key)
                        self.config_manager.save_config()
    
        if self.selected_provider == 'ollama' and not self.ollama_check.isChecked():
                QMessageBox.warning(self, "Error", "Ollama is not available")
                return
    
        super().accept()

    def get_selected_model(self) -> Dict:
        return {
            'provider': self.selected_provider,
            'model': self.selected_model,
            'api_key': self.api_key_widget.get_api_key() if self.selected_provider == 'gemini' else None
        }

class ModelManager:
    def __init__(self):
        self.providers = {}
        self._current_provider = None
        self._current_model = None
        self.config_manager = ConfigManager()
        self.dialog = ModelSelectionDialog(self.config_manager)
    
    def add_provider(self, name: str, provider: ModelProvider):
        self.providers[name] = provider
    
    def list_all_models(self) -> List[Dict]:
        all_models = []
        for provider in self.providers.values():
            all_models.extend(provider.list_models())
        return all_models
    
    def set_current_model(self, provider: str, model: str):
        if provider not in self.providers:
            raise ValueError(f"Unknown provider: {provider}")
        self._current_provider = provider
        self._current_model = model
    
    def get_current_model_info(self) -> Dict:
        if not self._current_provider or not self._current_model:
            raise ValueError("No model selected")
        return self.providers[self._current_provider].get_model_info(self._current_model)
    
    def generate_stream(self, messages: List[Dict], settings: Dict) -> Generator:
        if not self._current_provider or not self._current_model:
            raise ValueError("No model selected")
        return self.providers[self._current_provider].generate_stream(
            messages,
            self._current_model,
            settings
        )
        
    def show_dialog(self) -> Optional[Dict]:
        """Show model selection dialog and return selected model info"""
        if self.dialog.exec_() == QDialog.Accepted:
            return self.dialog.get_selected_model()
        return None