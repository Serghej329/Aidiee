import sys
import os
import asyncio
import json
import ctypes

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QFileDialog, QFrame
)
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtSvg import QSvgWidget
from qframelesswindow import FramelessMainWindow

from titlebar import CustomTitleBar
from styles import DarkThemeStyles
from file_explorer_widget import FileExplorerWidget
from terminal_module import Terminal
from projects import ProjectManager
from cosmic_splitter import CosmicSplitter
from voice_assistant_dock import VoiceAssistantDock
from voice_detection_module import CombinedDetector
from tabs_dictionary import tabs_dictionary
from code_editor_widget import CodeEditorWidget
from python_highlighter import SyntaxThemes 

class DetectorThread(QThread):
    keyword_detected = pyqtSignal()
    silence_detected = pyqtSignal()
    transcription_ready = pyqtSignal(str)

    def __init__(self, detector):
        super().__init__()
        self.detector = detector
        self.stopped = False

    def run(self):
        self.detector.start()
        while not self.stopped:
            if self.detector.keyword_detected.wait():
                if self.stopped:
                    break
                self.keyword_detected.emit()

                if self.detector.silence_detected.wait():
                    if self.stopped:
                        break
                    audio_data = self.detector.get_audio_data()
                    transcription = self.detector.transcribe_audio(audio_data)
                    self.transcription_ready.emit(transcription)
                    self.detector.reset_audio_data()

                self.silence_detected.emit()
                self.detector.keyword_detected.clear()
                self.detector.silence_detected.clear()

    def stop(self):
        self.stopped = True
        self.detector.keyword_detected.set()
        self.detector.silence_detected.set()


class SimpleIDE(FramelessMainWindow):
    def __init__(self, project_path):
        super().__init__()
        self.setWindowTitle("Aidee")
        # Get the absolute path of the current script
        default_path = os.path.abspath(os.path.dirname(__file__))
        icon_path = os.path.join(default_path, "icons", "logo_new.ico")
        if not os.path.exists(icon_path):
                print("Icon file does not exist:", icon_path)
        else:
                print("Icon file found.")
        # Set the window icon
        self.setWindowIcon(QIcon(icon_path))
        # Creating modules objects
        self.project_path = project_path
        self.file_explorer = FileExplorerWidget(self, self.project_path)
        self.folder_dialog = QFileDialog
        self.project_manager = ProjectManager(self.folder_dialog, self.file_explorer)
        # Setting the style for the window and building the ui
        self.setMinimumSize(800, 600)
        self.resize(1200, 800)
        self.setup_ui()
        self.apply_styles()
        self.titleBar.raise_()

    def setup_ui(self):
        # Creazione del widget centrale
        self.central_widget = QWidget()
        self.central_widget.setObjectName("centralWidget")
        self.setCentralWidget(self.central_widget)

        # Layout principale
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Setup della barra del titolo personalizzata
        self.custom_titlebar = CustomTitleBar(ide_instance=self)

        # Creazione del QSplitter orizzontale principale
        self.h_splitter = CosmicSplitter(Qt.Horizontal)

        # Aggiunta del file explorer al QSplitter orizzontale
        self.h_splitter.addWidget(self.file_explorer)

        # Creazione del QSplitter verticale principale
        self.v_splitter = CosmicSplitter(Qt.Vertical)

        # Configurazione del QTabWidget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(lambda index: self.close_tab(index))

        # Aggiunta del QTabWidget al QSplitter verticale
        self.v_splitter.addWidget(self.tab_widget)

        # Creazione del terminale personalizzato
        self.terminal = Terminal(
            parent=self,
            initial_height=200,
            initial_cwd=self.project_path
        )

        # Aggiunta del terminale al QSplitter verticale
        self.v_splitter.addWidget(self.terminal)

        # Impostazione delle dimensioni iniziali del QSplitter verticale
        self.v_splitter.setSizes([800, 200])

        # Aggiunta del QSplitter verticale al QSplitter orizzontale
        self.h_splitter.addWidget(self.v_splitter)

        # Impostazione delle dimensioni iniziali del QSplitter orizzontale
        self.h_splitter.setSizes([250, self.width() - 250])

        # Aggiunta del QSplitter orizzontale al layout principale
        main_layout.addWidget(self.h_splitter)

        # Impostazione dello stile predefinito per l'editor di codice (Tokyo Night)
        self.change_style()

        # Creazione del dock per l'assistente vocale e aggiunta alla finestra principale
        self.voice_assistant_dock = VoiceAssistantDock(ide_instance=self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.voice_assistant_dock)

        # Inizializzazione del rilevatore vocale e del thread
        self.detector = CombinedDetector(whisper_model_version="base")
        self.detector_thread = None

        # Inizializzazione del dizionario delle schede
        self.tabs = tabs_dictionary()


    def change_style(self, style_name="Tokyo Night"):
        self.current_style = style_name
        for index in range(self.tab_widget.count()):
            editor_widget = self.tab_widget.widget(index)
            editor_widget.set_style(style_name)

    def start_detector(self):
        if self.detector_thread and self.detector_thread.isRunning():
            return

        self.detector_thread = DetectorThread(self.detector)
        self.detector_thread.keyword_detected.connect(self.voice_assistant_dock.on_keyword_detected)
        self.detector_thread.silence_detected.connect(self.voice_assistant_dock.on_silence_detected)
        self.detector_thread.transcription_ready.connect(self.voice_assistant_dock.on_transcription_ready)
        self.detector_thread.start()
        self.stopped = False
        self.voice_assistant_dock.status_label.setText("Assistant active - Waiting for 'Alexa'...")

    def stop_detector(self):
        if self.detector_thread:
            self.detector_thread.stopped = True
            self.detector.running = False
            self.detector.keyword_detected.set()
            self.detector.silence_detected.set()
            self.detector_thread.wait()

            if self.detector_thread.isRunning():
                print("Warning: Detector thread did not stop cleanly.")

            self.detector.stop()
            self.detector_thread = None

        self.voice_assistant_dock.status_label.setText("Assistant stopped")
        # self.ai_button.stop_animation()

    def on_keyword_detected(self):
        self.voice_assistant_dock.status_label.setText("Alexa detected! Listening...")
        # self.ai_button.set_active_state(True)

    def on_silence_detected(self):
        self.voice_assistant_dock.status_label.setText("Processing audio...")
        # self.ai_button.set_processing_state(True)

    def on_transcription_ready(self, transcription):
        current_text = self.voice_assistant_dock.transcription_text.toPlainText()
        if current_text:
            new_text = f"{current_text}\n{transcription}"
        else:
            new_text = transcription
        self.voice_assistant_dock.transcription_text.setPlainText(new_text)
        self.voice_assistant_dock.status_label.setText("Assistant active - Waiting for 'Alexa'...")
        # self.ai_button.set_active_state(False)
        # self.ai_button.set_processing_state(False)

    def create_new_file(self):
        self.file_explorer.create_new_file()

    def add_file_to_tabs(self, file_path):
        if os.path.splitext(file_path)[1] == ".py":
            editor_widget = CodeEditorWidget()
            with open(file_path, "r", encoding="utf8") as f:
                file_content = f.read()
            file_name = os.path.basename(file_path)
            editor_widget.set_content(file_content,file_name)
            if not self.tabs.tab_exists(file_name):
                self.tab_widget.addTab(editor_widget, file_name)
                self.tabs.add_tab(file_name, path=file_path, index=self.tab_widget.count())
                self.tab_widget.setCurrentWidget(editor_widget)
            else:
                data = self.tabs.get_tab(file_name)
                self.tab_widget.setCurrentIndex(data["index"] - 1)

            self.change_style(self.current_style)

    def add_suggestion_tab(self,editor,suggestion_number):
        """
        Add a tab not connected to a file, usually use to display the llm code
        
        Args:
            text: Input code to show in the tab
            
        """
        editor_widget = editor
        suggestion_name = f"Suggestion {suggestion_number+1}"
        if not self.tabs.tab_exists(suggestion_name) and editor_widget:
                self.tab_widget.addTab(editor_widget, suggestion_name)
                self.tabs.add_tab(suggestion_name, path=f"virtual/suggestion_name", index=self.tab_widget.count())
                self.tab_widget.setCurrentWidget(editor_widget)
        else:
                data = self.tabs.get_tab(suggestion_name)
                self.tab_widget.setCurrentIndex(data["index"] - 1)

    def close_tab(self, index):
        self.tab_widget.removeTab(index)
        self.tabs.remove_tab(self.tabs.get_tab_by_index(index + 1))

    def closeEvent(self, event):
        self.stop_detector()
        event.accept()

    def apply_styles(self):
        # Apply main window styles
        syntax_themes = SyntaxThemes()
        self.syntax_themes = SyntaxThemes()
        self.current_theme = self.syntax_themes.themes['Tokyo Night']
        background = self.current_theme['main_background']
        foreground = self.current_theme['main_foreground']
        self.setStyleSheet(f"background:{background}")
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background-color: {background};
                border-radius: 10px;
                padding: 5px;
            }}
            QTabBar::tab {{
                background-color: {background};
                color: #E0E0E0;
                border: none;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                padding: 10px;
                margin-right: 5px;
                border-bottom: 2px solid #1E1F2B;
            }}
            QTabBar::tab:selected {{
                background-color: #3D3E4D;
                color: #E0E0E0;
                border-bottom: 2px solid #3D3E4D;
            }}
            QTabBar::tab:hover {{
                background-color: #3D3E4D;
            }}
            QTabBar::close-button {{
                image: url(img/close_icon.png);
                subcontrol-position: right;
                padding: 1.5px;
            }}
        """)
        self.central_widget.setStyleSheet(f"""
            #centralWidget {{
                background-color: {background};
                margin:0;
                padding:0;
            }}
        """)
        # dark_palette = DarkThemeStyles.get_dark_palette()
        # self.setStyleSheet(DarkThemeStyles.get_main_style_sheet(dark_palette))
        self.setStyleSheet(f"background-color:{background};color:{foreground}")