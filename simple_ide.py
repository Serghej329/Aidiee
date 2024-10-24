import sys
import os
import asyncio
from PyQt5.QtWidgets import (
    QWidget, QTextEdit, QVBoxLayout, QComboBox, QHBoxLayout, QSpacerItem,
    QSizePolicy, QPushButton, QApplication, QLabel, QMenuBar, QMenu, QAction,
    QMainWindow, QDockWidget, QLineEdit, QScrollArea, QTabWidget, QSplitter
)
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal, pyqtSlot, QTimer, QObject, QUrl
from PyQt5.QtGui import QFont, QIcon, QPalette, QPixmap
from PyQt5.QtSvg import QSvgWidget
from neumorphic_widgets import NeumorphicWidget, NeumorphicTextEdit
from syntax_highlighting import PythonHighlighter
from animated_wave_background import AnimatedWaveBackground
from pygments.styles import get_style_by_name
from voice_detection_module import VoiceDetector
from animated_circle_button import AnimatedCircleButton  # Salva il codice dell'artifact in questo file
from file_explorer_widget import FileExplorerWidget

class VoiceDetectionThread(QThread):
    transcription_signal = pyqtSignal(str)
    state_signal = pyqtSignal(str)

    def __init__(self, detector):
        super().__init__()
        self.detector = detector
        self.running = False
        self.loop = None

    def run(self):
        self.running = True     
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self.continuous_transcription())
        except Exception as e:
            print(f"Error in VoiceDetectionThread: {e}")
        finally:
            self.loop.close()
            self.running = False

    async def continuous_transcription(self):
        while self.running:
            activated = await self.detector.listen_for_activation()
            if activated:
                async for transcribed_text in self.detector.transcribe_speech():
                    self.transcription_signal.emit(transcribed_text)
                    self.state_signal.emit("active")
                self.state_signal.emit("inactive")

    def stop(self):
        self.running = False
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.close)

class TitleBar(QWidget):
    def __init__(self, parent=None, ide_instance=None):
        super().__init__(parent)
        self.ide_instance = ide_instance
        self.setFixedHeight(40)
        self.setStyleSheet("""
            background-color: #2C2D3A;
            color: #E0E0E0;
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(0)

        # Logo - use an SVG icon
        logo_widget = QSvgWidget('img/logo.svg')  # Adjust the path to your SVG
        logo_widget.setFixedSize(30, 30)  # Set size according to your logo
        layout.addWidget(logo_widget)

        # Menu Bar
        self.menu_bar = QMenuBar(self)
        self.menu_bar.setStyleSheet("""
            QMenuBar {
                background-color: transparent;
                color: #E0E0E0;
            }
            QMenuBar::item {
                padding: 5px 10px;
                background: transparent;
                color: #E0E0E0;
            }
            QMenuBar::item:selected {
                background: #3D3E4D;
                border-radius: 5px;
            }
            QMenu {
                background-color: #2C2D3A;
                border: 1px solid #3D3E4D;
                border-radius: 5px;
            }
            QMenu::item {
                padding: 5px 20px;
                background-color: transparent;
                color: #E0E0E0;
            }
            QMenu::item:selected {
                background-color: #3D3E4D;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.menu_bar)

        # Spacer
        layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # Buttons
        self.create_buttons(layout)

        # Create Menus
        self.create_menus()
        
    def create_buttons(self, layout):
        button_style = """
            QPushButton {
                background-color: #2C2D3A;
                border: none;
                color: #E0E0E0;
                font-size: 16px;
                padding: 5px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #3D3E4D;
            }
            QPushButton:pressed {
                background-color: #1E1F2B;
            }
        """

        self.minimize_button = QPushButton("−")
        self.minimize_button.setFixedSize(30, 30)
        self.minimize_button.clicked.connect(self.parent().showMinimized)
        self.minimize_button.setStyleSheet(button_style)
        layout.addWidget(self.minimize_button)

        self.maximize_button = QPushButton("□")
        self.maximize_button.setFixedSize(30, 30)
        self.maximize_button.clicked.connect(self.toggle_maximize_restore)
        self.maximize_button.setStyleSheet(button_style)
        layout.addWidget(self.maximize_button)

        self.close_button = QPushButton("×")
        self.close_button.setFixedSize(30, 30)
        self.close_button.clicked.connect(self.parent().close)
        self.close_button.setStyleSheet(button_style)
        layout.addWidget(self.close_button)

    def toggle_maximize_restore(self):
        if self.parent().isMaximized():
            self.parent().showNormal()
            self.maximize_button.setText("□")
        else:
            self.parent().showMaximized()
            self.maximize_button.setText("❐")

    def create_menus(self):
        file_menu = self.menu_bar.addMenu("File")
        new_file_action = file_menu.addAction("New File")
        new_file_action.triggered.connect(self.ide_instance.create_new_file)
        file_menu.addAction("Open File")
        file_menu.addAction("Save")
        file_menu.addSeparator()
        file_menu.addAction("Exit")

        edit_menu = self.menu_bar.addMenu("Edit")
        edit_menu.addAction("Undo")
        edit_menu.addAction("Redo")
        edit_menu.addSeparator()
        edit_menu.addAction("Cut")
        edit_menu.addAction("Copy")
        edit_menu.addAction("Paste")

        view_menu = self.menu_bar.addMenu("View")
        editor_template_menu = view_menu.addMenu("Editor Template")
        
        styles = ["monokai", "default", "friendly", "fruity", "manni", "paraiso-dark", "solarized-dark"]
        for style_name in styles:
            style_action = QAction(style_name, self)
            style_action.triggered.connect(lambda checked, s=style_name: self.ide_instance.change_style(s))
            editor_template_menu.addAction(style_action)
        
        # Add "Dock Widget" toggle action
        dock_widget_action = QAction("Toggle Dock Widget", self)
        dock_widget_action.triggered.connect(self.ide_instance.toggle_dock_widget)
        view_menu.addAction(dock_widget_action)
        
        section_menu = self.menu_bar.addMenu("Section")
        section_menu.addAction("Add Section")
        section_menu.addAction("Remove Section")

        go_menu = self.menu_bar.addMenu("Go")
        go_menu.addAction("Go to Line")
        go_menu.addAction("Go to Definition")

        run_menu = self.menu_bar.addMenu("Run")
        run_menu.addAction("Run Code")
        run_menu.addAction("Debug Code")

        terminal_menu = self.menu_bar.addMenu("Terminal")
        terminal_menu.addAction("New Terminal")
        terminal_menu.addAction("Close Terminal")

        assistant_menu = self.menu_bar.addMenu("AI Assistant")
        assistant_menu.addAction("Open Assistant")
        assistant_menu.addAction("Close Assistant")

        help_menu = self.menu_bar.addMenu("Help")
        help_menu.addAction("Documentation")
        help_menu.addAction("About")
        
        
class CodeEditorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.code_editor = NeumorphicTextEdit()
        self.code_editor.setFont(QFont("Fira Code", 12))
        self.highlighter = PythonHighlighter(self.code_editor.document())
        layout.addWidget(self.code_editor)
        self.setLayout(layout)

        # Apply neumorphic style to the CodeEditorWidget
        self.setStyleSheet("""
            background-color: #2C2D3A;
            border-radius: 10px;
            padding: 10px;
            
        """)

    def set_style(self, style_name):
        self.highlighter = PythonHighlighter(self.code_editor.document(), style_name=style_name)
        style = get_style_by_name(style_name)
        background_color = style.background_color
        default_color = style.highlight_color
        self.code_editor.setStyleSheet(f"""
            QTextEdit {{
                
                background-color: {background_color};
                color: {default_color};
                border-radius: 10px;
                padding: 10px;
            }}
            
             QTextEdit {{
                
                background-color: {background_color};
                color: {default_color};
                border-radius: 10px;
                padding: 10px;
            }}
            
            
            
        """)

class SimpleIDE(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setStyleSheet("QMainWindow::separator{ width: 0px; height: 0px; }")
        
        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        central_widget.setStyleSheet("""
            #centralWidget {
                background-color: #2C2D3A;
                margin:0;
                padding:0;
            }
        """)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.title_bar = TitleBar(self, ide_instance=self)
        main_layout.addWidget(self.title_bar)

        self.splitter = QSplitter(Qt.Horizontal)
        self.file_explorer = FileExplorerWidget(self)
        self.splitter.addWidget(self.file_explorer)

        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: #2C2D3A;
                border-radius: 10px;
                padding: 5px;
            }
            QTabBar::tab {
                background-color: #2C2D3A;
                color: #E0E0E0;
                border: none;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                padding: 10px;
                margin-right: 5px;
                border-bottom: 2px solid #1E1F2B;
            }
            QTabBar::tab:selected {
                background-color: #3D3E4D;
                color: #E0E0E0;
                border-bottom: 2px solid #3D3E4D;
            }
            QTabBar::tab:hover {
                background-color: #3D3E4D;
            }
            QTabBar::close-button {
                image: url(img/close_icon.png);
                subcontrol-position: right;
                padding: 1.5px;
            }
        """)
        self.splitter.addWidget(self.tab_widget)
        self.splitter.setSizes([250, self.width() - 250])
        main_layout.addWidget(self.splitter)

        self.create_new_file()
        
        self.button_container = QWidget()
        self.button_container.setMinimumHeight(50)
        button_container_layout = QVBoxLayout(self.button_container)
        button_container_layout.setContentsMargins(0, 0, 0, 0)
        button_container_layout.setSpacing(0)

        self.button_frame = NeumorphicWidget()
        self.button_frame.setMinimumHeight(50)
        self.button_frame.setStyleSheet("""
            background-color: #2C2D3A;
        """)
        button_container_layout.addWidget(self.button_frame)

        button_layout = QHBoxLayout(self.button_frame)
        button_layout.setContentsMargins(10, 10, 10, 10)

        self.wave_background = AnimatedWaveBackground(self.button_frame)
        self.wave_background.setFixedHeight(40)
        self.wave_background.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.wave_background.raise_()  # Ensure the wave background is above other widgets

        self.ai_button = AnimatedCircleButton()
        self.ai_button.setMinimumSize(64, 64)
        self.ai_button.setMaximumSize(120, 120)
        button_layout.addWidget(self.ai_button, 0, Qt.AlignCenter)

        main_layout.addWidget(self.button_container)

        self.change_style("monokai")
        self.create_dock_widget()

        self.detection_thread = None
        self.setup_voice_detection()

    
    #TODO
    def create_new_file(self):
        editor_widget = CodeEditorWidget()
        self.tab_widget.addTab(editor_widget, f"Untitled-{self.tab_widget.count() + 1}")
        self.tab_widget.setCurrentWidget(editor_widget)

    def close_tab(self, index):
        self.tab_widget.removeTab(index)

    def resizeEvent(self, event):
        super().resizeEvent(event)

        # Calculate dynamic height for the button container
        frame_height = self.height() * 0.08
        self.button_container.setFixedHeight(int(frame_height))

        # Calculate dynamically the height of the wave as a proportion of the button_frame
        if hasattr(self, 'wave_background'):
            wave_height = int(self.button_frame.height() * 1.2)  # Modify the proportion to increase the wave height
            self.wave_background.setFixedHeight(wave_height)

            # Ensure the wave does not get clipped
            self.button_frame.setStyleSheet("""
                background-color: #2C2D3A;
                overflow: visible;
            """)

            # Position the wave so it overflows downwards
            self.wave_background.resize(self.button_frame.width(), wave_height)
            self.wave_background.move(0, self.button_frame.height() - wave_height)

        if hasattr(self, 'ai_button'):
            self.ai_button.raise_()
            button_frame_height = self.button_frame.height()
            ai_button_size = self.ai_button.height()

            # Position the center of the button at the middle of the top section of the button_frame
            top_section_mid = button_frame_height * 0.25 - ai_button_size / 2
            self.ai_button.move(self.button_frame.width() // 2 - self.ai_button.width() // 2, int(top_section_mid))

    def create_dock_widget(self):
        self.dock_widget = QDockWidget("Voice Transcription", self)
        self.dock_widget.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.dock_widget.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetClosable)
        
        # Reduced border-radius for dock widget
        self.dock_widget.setStyleSheet("""
            QDockWidget {
                background-color: #2C2D3A;
                color: #E0E0E0;
                border: none;
            }
            QDockWidget::title {
                background-color: #2C2D3A;
                color: #E0E0E0;
                padding: 8px;
                text-align: left;
            }
        """)

        # Create a NeumorphicWidget as the main container
        dock_content = NeumorphicWidget()
        dock_layout = QVBoxLayout(dock_content)
        dock_layout.setContentsMargins(5, 5, 5, 5)
        dock_layout.setSpacing(5)

        # Use NeumorphicTextEdit with reduced border radius
        self.transcription_text = NeumorphicTextEdit()
        self.transcription_text.setReadOnly(True)
        self.transcription_text.setStyleSheet("""
            QTextEdit {
                background-color: #1E1F2B;
                border: none;
                border-radius: 5px;
                padding: 8px;
                color: #E0E0E0;
            }
        """)
        dock_layout.addWidget(self.transcription_text)

        # Activation phrase input with reduced border radius
        self.activation_input = QLineEdit()
        self.activation_input.setPlaceholderText("Enter activation phrase")
        self.activation_input.setStyleSheet("""
            QLineEdit {
                background-color: #1E1F2B;
                color: #E0E0E0;
                border: none;
                border-radius: 5px;
                padding: 8px;
            }
            QLineEdit:focus {
                background-color: #2C2D3A;
            }
        """)
        dock_layout.addWidget(self.activation_input)

        # Control buttons with reduced border radius
        control_layout = QHBoxLayout()
        button_style = """
            QPushButton {
                background-color: #2C2D3A;
                color: #E0E0E0;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: #3D3E4D;
            }
            QPushButton:pressed {
                background-color: #1E1F2B;
                padding: 9px 15px 7px 17px;
            }
        """
        
        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        self.restart_button = QPushButton("Restart")
        
        for button in [self.start_button, self.stop_button, self.restart_button]:
            button.setStyleSheet(button_style)
            control_layout.addWidget(button)
            
        dock_layout.addLayout(control_layout)

        # Optimized scroll area with reduced border radius
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(dock_content)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #2C2D3A;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #2C2D3A;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #3D3E4D;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #4D4E5D;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
        self.dock_widget.setWidget(scroll_area)

        # Connect buttons
        self.start_button.clicked.connect(self.start_detection)
        self.stop_button.clicked.connect(self.stop_detection)
        self.restart_button.clicked.connect(self.restart_detection)

        # Set initial position and size
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_widget)
        self.dock_widget.hide()

        screen_size = QApplication.desktop().screenGeometry()
        dock_width = screen_size.width() // 4
        self.dock_widget.setMinimumWidth(dock_width)

        # Connect dock location changed signal
        self.dock_widget.dockLocationChanged.connect(self.update_dock_widget_style)

    def setup_voice_detection(self):
        # Assicurati di collegare i segnali del rilevamento vocale
        self.voice_thread = VoiceDetectionThread(detector=VoiceDetector(
            activation_phrase="your_activation_phrase",
            whisper_model_dir="path/to/your/whisper/model",
            whisper_model_version="base",
            silence_duration=1,
            silence_threshold=-10,
            language="it-IT"
        ))
        self.voice_thread.transcription_signal.connect(self.transcription_text.append)
        self.voice_thread.state_signal.connect(self.update_status)
        self.voice_thread.start()

    def start_detection(self):
        activation_phrase = self.activation_input.text().strip()
        if not activation_phrase:
            self.transcription_text.append("Please enter an activation phrase.")
            return

        self.detector = VoiceDetector(
            activation_phrase=activation_phrase,
            whisper_model_dir="path/to/your/whisper/model",
            whisper_model_version="base",
            silence_duration=1,
            silence_threshold=-10,
            language="it-IT"
        )

        self.detection_thread = VoiceDetectionThread(self.detector)
        
        self.detection_thread.transcription_signal.connect(self.update_transcription)
        self.detection_thread.state_signal.connect(self.update_state)

        if not self.detection_thread.isRunning():
            self.detection_thread.start()

    def stop_detection(self):
        if self.detection_thread and self.detection_thread.isRunning():
            self.detection_thread.stop()
            self.detection_thread.wait()

    def restart_detection(self):
        self.stop_detection()
        self.start_detection()

    def update_transcription(self, text):
        self.transcription_text.append(text)
        
    def update_status(self, status):
        # Aggiorna lo stato del rilevamento vocale
        self.transcription_text.setPlainText(f"Stato: {status}")

    def update_state(self, state):
        print(f"Voice detection state: {state}")

    def toggle_dock_widget(self):
        # Alterna la visibilità del Dock Widget
        if self.dock_widget.isVisible():
            self.dock_widget.hide()
        else:
            self.dock_widget.show()

    def change_style(self, style_name="monokai"):
        for index in range(self.tab_widget.count()):
            editor_widget = self.tab_widget.widget(index)
            editor_widget.set_style(style_name)

    def closeEvent(self, event):
        self.stop_detection()
        event.accept()

    def update_dock_widget_style(self, dock_area):
        screen_size = QApplication.desktop().screenGeometry()
        if self.dock_widget.isFloating():
            # Dimensioni quadrate prestabilite per la modalità floating
            square_size = 300  # Puoi cambiare questo valore a seconda delle tue esigenze
            self.dock_widget.setFixedSize(square_size, square_size)
        else:
            if dock_area == Qt.TopDockWidgetArea:
                self.dock_widget.setFixedHeight(screen_size.height() // 4)
                self.dock_widget.setFixedWidth(screen_size.width())
            elif dock_area == Qt.BottomDockWidgetArea:
                self.dock_widget.setFixedHeight(screen_size.height() // 4)
                self.dock_widget.setFixedWidth(screen_size.width())
            elif dock_area == Qt.LeftDockWidgetArea or dock_area == Qt.RightDockWidgetArea:
                self.dock_widget.setFixedHeight(screen_size.height())
                self.dock_widget.setFixedWidth(screen_size.width() // 4)

    def open_file(self, file_path):
        with open(file_path, 'r') as f:
            content = f.read()
        
        editor_widget = CodeEditorWidget()
        editor_widget.code_editor.setPlainText(content)
        
        file_name = os.path.basename(file_path)
        self.tab_widget.addTab(editor_widget, file_name)
        self.tab_widget.setCurrentWidget(editor_widget)

'''import sys
import asyncio
from PyQt5.QtWidgets import (
    QWidget, QTextEdit, QVBoxLayout, QComboBox, QHBoxLayout, QSpacerItem,
    QSizePolicy, QPushButton, QApplication, QLabel, QMenuBar, QMenu, QAction,
    QMainWindow, QDockWidget, QLineEdit
)
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal
from PyQt5.QtGui import QFont
from neumorphic_widgets import NeumorphicWidget, NeumorphicTextEdit
from syntax_highlighting import PythonHighlighter
from animated_wave_background import AnimatedWaveBackground
from ai_assistant_button import AIAssistantButton
from pygments.styles import get_style_by_name
from voice_detection_module import VoiceDetector

class VoiceDetectionThread(QThread):
    transcription_signal = pyqtSignal(str)
    state_signal = pyqtSignal(str)

    def __init__(self, detector):
        super().__init__()
        self.detector = detector
        self.running = False
        self.loop = None

    def run(self):
        self.running = True     
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self.continuous_transcription())
        except Exception as e:
            print(f"Error in VoiceDetectionThread: {e}")
        finally:
            self.loop.close()
            self.running = False

    async def continuous_transcription(self):
        while self.running:
            activated = await self.detector.listen_for_activation()
            if activated:
                async for transcribed_text in self.detector.transcribe_speech():
                    self.transcription_signal.emit(transcribed_text)
                    self.state_signal.emit("active")
                self.state_signal.emit("inactive")

    def stop(self):
        self.running = False
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.close)

class TitleBar(QWidget):
    def __init__(self, parent=None, ide_instance=None):
        super().__init__(parent)
        self.ide_instance = ide_instance
        self.setFixedHeight(30)
        self.setStyleSheet("background-color: #3C3D37; color: white;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Menu Bar
        self.menu_bar = QMenuBar(self)
        self.menu_bar.setStyleSheet("""
            QMenuBar {
                background-color: #3C3D37;
                color: white;
            }
            QMenuBar::item {
                padding: 5px 10px;
                background: transparent;
                color: white;
            }
            QMenuBar::item:selected {
                background: #4D4E48;
            }
            QMenu {
                background-color: #3C3D37;
                border: 1px solid #5E5E5E;
            }
            QMenu::item {
                padding: 5px 20px;
                background-color: transparent;
            }
            QMenu::item:selected {
                background-color: #4D4E48;
            }
        """)
        layout.addWidget(self.menu_bar)

        # Spacer
        layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # Buttons
        self.create_buttons(layout)

        # Create Menus
        self.create_menus()

    def create_buttons(self, layout):
        self.minimize_button = QPushButton("-")
        self.minimize_button.setFixedSize(30, 30)
        self.minimize_button.clicked.connect(self.parent().showMinimized)
        layout.addWidget(self.minimize_button)

        self.maximize_button = QPushButton("□")
        self.maximize_button.setFixedSize(30, 30)
        self.maximize_button.clicked.connect(self.toggle_maximize_restore)
        layout.addWidget(self.maximize_button)

        self.close_button = QPushButton("×")
        self.close_button.setFixedSize(30, 30)
        self.close_button.clicked.connect(self.parent().close)
        layout.addWidget(self.close_button)

    def toggle_maximize_restore(self):
        if self.parent().isMaximized():
            self.parent().showNormal()
            self.maximize_button.setText("□")
        else:
            self.parent().showMaximized()
            self.maximize_button.setText("❐")

    def create_menus(self):
        file_menu = self.menu_bar.addMenu("File")
        file_menu.addAction("New File")
        file_menu.addAction("Open File")
        file_menu.addAction("Save")
        file_menu.addSeparator()
        file_menu.addAction("Exit")

        edit_menu = self.menu_bar.addMenu("Edit")
        edit_menu.addAction("Undo")
        edit_menu.addAction("Redo")
        edit_menu.addSeparator()
        edit_menu.addAction("Cut")
        edit_menu.addAction("Copy")
        edit_menu.addAction("Paste")

        view_menu = self.menu_bar.addMenu("View")
        editor_template_menu = view_menu.addMenu("Editor Template")
        
        styles = ["monokai", "default", "friendly", "fruity", "manni", "paraiso-dark", "solarized-dark"]
        for style_name in styles:
            style_action = QAction(style_name, self)
            style_action.triggered.connect(lambda checked, s=style_name: self.ide_instance.change_style(s))
            editor_template_menu.addAction(style_action)
        
        # Add "Dock Widget" toggle action
        dock_widget_action = QAction("Toggle Dock Widget", self)
        dock_widget_action.triggered.connect(self.ide_instance.toggle_dock_widget)
        view_menu.addAction(dock_widget_action)
        
        
        section_menu = self.menu_bar.addMenu("Section")
        section_menu.addAction("Add Section")
        section_menu.addAction("Remove Section")

        go_menu = self.menu_bar.addMenu("Go")
        go_menu.addAction("Go to Line")
        go_menu.addAction("Go to Definition")

        run_menu = self.menu_bar.addMenu("Run")
        run_menu.addAction("Run Code")
        run_menu.addAction("Debug Code")

        terminal_menu = self.menu_bar.addMenu("Terminal")
        terminal_menu.addAction("New Terminal")
        terminal_menu.addAction("Close Terminal")

        assistant_menu = self.menu_bar.addMenu("AI Assistant")
        assistant_menu.addAction("Open Assistant")
        assistant_menu.addAction("Close Assistant")

        help_menu = self.menu_bar.addMenu("Help")
        help_menu.addAction("Documentation")
        help_menu.addAction("About")
    

class SimpleIDE(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setStyleSheet("background-color: #3C3D37;")

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Title Bar
        self.title_bar = TitleBar(self, ide_instance=self)
        main_layout.addWidget(self.title_bar)

        # Code Editor
        self.code_editor = NeumorphicTextEdit()
        self.code_editor.setFont(QFont("Monospace", 10))
        self.highlighter = PythonHighlighter(self.code_editor.document())
        main_layout.addWidget(self.code_editor)

        # Button Frame
        self.button_frame = NeumorphicWidget()
        self.button_frame.setMinimumHeight(70)
        button_layout = QHBoxLayout(self.button_frame)
        button_layout.setContentsMargins(0, 0, 0, 0)

        button_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.ai_button = AIAssistantButton()
        button_layout.addWidget(self.ai_button, 0, Qt.AlignCenter)

        button_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        main_layout.addWidget(self.button_frame)

        self.change_style("monokai")

        # Add the AnimatedWaveBackground
        self.wave_background = AnimatedWaveBackground(self.button_frame)
        self.wave_background.resize(self.button_frame.size())
        self.wave_background.stackUnder(self.ai_button)

        # Create and configure the QDockWidget
        self.create_dock_widget()

        # Voice Detection Setup
        self.setup_voice_detection()

    def create_dock_widget(self):
        self.dock_widget = QDockWidget("Voice Transcription", self)
        self.dock_widget.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.dock_widget.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetClosable)

        # Dock widget content
        dock_content = QWidget()
        dock_layout = QVBoxLayout(dock_content)

        self.transcription_text = QTextEdit()
        self.transcription_text.setReadOnly(True)
        dock_layout.addWidget(self.transcription_text)

        self.activation_input = QLineEdit()
        self.activation_input.setPlaceholderText("Enter activation phrase")
        dock_layout.addWidget(self.activation_input)

        control_layout = QHBoxLayout()
        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        self.restart_button = QPushButton("Restart")
        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addWidget(self.restart_button)
        dock_layout.addLayout(control_layout)

        self.dock_widget.setWidget(dock_content)

        # Connect buttons
        self.start_button.clicked.connect(self.start_detection)
        self.stop_button.clicked.connect(self.stop_detection)
        self.restart_button.clicked.connect(self.restart_detection)

        # Add the dock widget to the main window
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_widget)

        # Set initial size to 1/4 of the screen
        screen_size = QApplication.desktop().screenGeometry()
        dock_width = screen_size.width() // 4
        self.dock_widget.setMinimumWidth(dock_width)
        self.dock_widget.setMaximumWidth(dock_width)

    def setup_voice_detection(self):
        self.detector = None
        self.detection_thread = None

    def start_detection(self):
        activation_phrase = self.activation_input.text().strip()
        if not activation_phrase:
            self.transcription_text.append("Please enter an activation phrase.")
            return

        self.detector = VoiceDetector(
            activation_phrase=activation_phrase,
            whisper_model_dir=r"C:/Users/ivald/Desktop/Informatica/voice detection pyq5/Models",
            whisper_model_version="base",
            silence_duration=1,
            silence_threshold=-10,
            language="it-IT"
        )

        self.detection_thread = VoiceDetectionThread(self.detector)
        self.detection_thread.transcription_signal.connect(self.update_transcription)
        self.detection_thread.state_signal.connect(self.update_state)

        if not self.detection_thread.isRunning():
            self.detection_thread.start()

    def stop_detection(self):
        if self.detection_thread and self.detection_thread.isRunning():
            self.detection_thread.stop()
            self.detection_thread.wait()

    def restart_detection(self):
        self.stop_detection()
        self.start_detection()

    def update_transcription(self, text):
        self.transcription_text.append(text)

    def update_state(self, state):
        print(f"Voice detection state: {state}")

    def toggle_dock_widget(self):
        if self.dock_widget.isVisible():
            self.dock_widget.hide()
        else:
            self.dock_widget.show()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'wave_background'):
            self.wave_background.resize(self.button_frame.size())
            self.wave_background.move(0, 0)

    def change_style(self, style_name="monokai"):
        self.highlighter = PythonHighlighter(self.code_editor.document(), style_name=style_name)
        style = get_style_by_name(style_name)
        background_color = style.background_color
        default_color = style.highlight_color
        self.code_editor.setStyleSheet(f"QTextEdit {{ background-color: {background_color}; color: {default_color}; border-radius: 10px; padding: 10px; }}")
    

    def closeEvent(self, event):
        self.stop_detection()
        event.accept()
'''


'''import sys
from PyQt5.QtWidgets import (
    QWidget, QTextEdit, QVBoxLayout, QComboBox, QHBoxLayout, QSpacerItem,
    QSizePolicy, QPushButton, QApplication, QLabel, QMenuBar, QMenu, QAction,
    QMainWindow, QDockWidget
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont
from neumorphic_widgets import NeumorphicWidget, NeumorphicTextEdit
from syntax_highlighting import PythonHighlighter
from animated_wave_background import AnimatedWaveBackground
from ai_assistant_button import AIAssistantButton
from pygments.styles import get_style_by_name

class TitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(30)
        self.setStyleSheet("background-color: #3C3D37; color: white;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Menu Bar
        self.menu_bar = QMenuBar(self)
        self.menu_bar.setStyleSheet("""
            QMenuBar {
                background-color: #3C3D37;
                color: white;
            }
            QMenuBar::item {
                padding: 5px 10px;
                background: transparent;
                color: white;
            }
            QMenuBar::item:selected {
                background: #4D4E48;
            }
            QMenu {
                background-color: #3C3D37;
                border: 1px solid #5E5E5E;
            }
            QMenu::item {
                padding: 5px 20px;
                background-color: transparent;
            }
            QMenu::item:selected {
                background-color: #4D4E48;
            }
        """)
        layout.addWidget(self.menu_bar)

        # Spacer
        layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # Buttons
        self.create_buttons(layout)

        # Create Menus
        self.create_menus()

    def create_buttons(self, layout):
        self.minimize_button = QPushButton("-")
        self.minimize_button.setFixedSize(30, 30)
        self.minimize_button.clicked.connect(self.parent().showMinimized)
        layout.addWidget(self.minimize_button)

        self.maximize_button = QPushButton("□")
        self.maximize_button.setFixedSize(30, 30)
        self.maximize_button.clicked.connect(self.toggle_maximize_restore)
        layout.addWidget(self.maximize_button)

        self.close_button = QPushButton("×")
        self.close_button.setFixedSize(30, 30)
        self.close_button.clicked.connect(self.parent().close)
        layout.addWidget(self.close_button)

    def toggle_maximize_restore(self):
        if self.parent().isMaximized():
            self.parent().showNormal()
            self.maximize_button.setText("□")
        else:
            self.parent().showMaximized()
            self.maximize_button.setText("❐")

    def create_menus(self):
        file_menu = self.menu_bar.addMenu("File")
        file_menu.addAction("New File")
        file_menu.addAction("Open File")
        file_menu.addAction("Save")
        file_menu.addSeparator()
        file_menu.addAction("Exit")

        edit_menu = self.menu_bar.addMenu("Edit")
        edit_menu.addAction("Undo")
        edit_menu.addAction("Redo")
        edit_menu.addSeparator()
        edit_menu.addAction("Cut")
        edit_menu.addAction("Copy")
        edit_menu.addAction("Paste")

        view_menu = self.menu_bar.addMenu("View")
        editor_template_menu = view_menu.addMenu("Editor Template")
        
        styles = ["monokai", "default", "friendly", "fruity", "manni", "paraiso-dark", "solarized-dark"]
        for style_name in styles:
            style_action = QAction(style_name, self)
            style_action.triggered.connect(lambda _, s=style_name: self.parent().change_style(s))
            editor_template_menu.addAction(style_action)
        
        # Add "Dock Widget" toggle action
        dock_widget_action = QAction("Toggle Dock Widget", self)
        dock_widget_action.triggered.connect(self.parent().toggle_dock_widget)
        view_menu.addAction(dock_widget_action)

        section_menu = self.menu_bar.addMenu("Section")
        section_menu.addAction("Add Section")
        section_menu.addAction("Remove Section")

        go_menu = self.menu_bar.addMenu("Go")
        go_menu.addAction("Go to Line")
        go_menu.addAction("Go to Definition")

        run_menu = self.menu_bar.addMenu("Run")
        run_menu.addAction("Run Code")
        run_menu.addAction("Debug Code")

        terminal_menu = self.menu_bar.addMenu("Terminal")
        terminal_menu.addAction("New Terminal")
        terminal_menu.addAction("Close Terminal")

        assistant_menu = self.menu_bar.addMenu("AI Assistant")
        assistant_menu.addAction("Open Assistant")
        assistant_menu.addAction("Close Assistant")

        help_menu = self.menu_bar.addMenu("Help")
        help_menu.addAction("Documentation")
        help_menu.addAction("About")
    

class SimpleIDE(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setStyleSheet("background-color: #3C3D37;")

        # Creiamo un widget centrale
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Title Bar
        self.title_bar = TitleBar(self)
        main_layout.addWidget(self.title_bar)

        # Code Editor
        self.code_editor = NeumorphicTextEdit()
        self.code_editor.setFont(QFont("Monospace", 10))
        self.highlighter = PythonHighlighter(self.code_editor.document())
        main_layout.addWidget(self.code_editor)

        # Button Frame
        self.button_frame = NeumorphicWidget()
        self.button_frame.setMinimumHeight(70)
        button_layout = QHBoxLayout(self.button_frame)
        button_layout.setContentsMargins(0, 0, 0, 0)

        button_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.ai_button = AIAssistantButton()
        button_layout.addWidget(self.ai_button, 0, Qt.AlignCenter)

        button_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        main_layout.addWidget(self.button_frame)

        self.change_style("monokai")

        # Add the AnimatedWaveBackground
        self.wave_background = AnimatedWaveBackground(self.button_frame)
        self.wave_background.resize(self.button_frame.size())
        self.wave_background.stackUnder(self.ai_button)

        # Creiamo e configuriamo il QDockWidget
        self.create_dock_widget()

    def create_dock_widget(self):
        self.dock_widget = QDockWidget("Dock Widget", self)
        self.dock_widget.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.dock_widget.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetClosable)

        # Contenuto del dock widget
        dock_content = QTextEdit()
        dock_content.setPlainText("ciaooooo qua inseriremo il testo convertito da audio a testo")
        dock_content.setReadOnly(True)  # Imposta il dock widget come sola lettura
        self.dock_widget.setWidget(dock_content)

        # Aggiungiamo il dock widget alla finestra principale
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_widget)

        # Impostiamo la dimensione iniziale a 1/4 dello schermo
        screen_size = QApplication.desktop().screenGeometry()
        dock_width = screen_size.width() // 4
        self.dock_widget.setMinimumWidth(dock_width)
        self.dock_widget.setMaximumWidth(dock_width)
        
    # function to toggle dock widget visibility
    def toggle_dock_widget(self):
        if self.dock_widget.isVisible():
            self.dock_widget.hide()
        else:
            self.dock_widget.show()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'wave_background'):
            self.wave_background.resize(self.button_frame.size())
            self.wave_background.move(0, 0)

    def change_style(self, style_name="monokai"):
        self.highlighter = PythonHighlighter(self.code_editor.document(), style_name=style_name)
        style = get_style_by_name(style_name)
        background_color = style.background_color
        default_color = style.highlight_color
        self.code_editor.setStyleSheet(f"QTextEdit {{ background-color: {background_color}; color: {default_color}; border-radius: 10px; padding: 10px; }}")

'''