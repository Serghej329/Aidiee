import sys
import os
import asyncio
import json
import ctypes

from PyQt5.QtWidgets import (
    QWidget, QTextEdit, QVBoxLayout, QComboBox, QHBoxLayout, QSpacerItem,
    QSizePolicy, QPushButton, QApplication, QLabel, QMenuBar, QMenu, QAction,
    QMainWindow, QDockWidget, QLineEdit, QScrollArea, QTabWidget, QSplitter,QFileDialog
)
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal, pyqtSlot, QTimer, QObject, QUrl, QPoint
from PyQt5.QtGui import QFont, QIcon, QPalette, QPixmap
from PyQt5.QtSvg import QSvgWidget
from neumorphic_widgets import NeumorphicWidget, NeumorphicTextEdit
from syntax_highlighting import PythonHighlighter
from animated_wave_background import AnimatedWaveBackground
from pygments.styles import get_style_by_name
from voice_detection_module import CombinedDetector
from animated_circle_button import AnimatedCircleButton  # Salva il codice dell'artifact in questo file
from file_explorer_widget import FileExplorerWidget
from tabs_dictionary import tabs_dictionary
from terminal_module import Terminal
from cosmic_splitter import CosmicSplitter

#from datetime import datetime
from projects import ProjectManager
# Ottieni il percorso relativo della cartella img
current_dir = os.path.dirname(os.path.abspath(__file__))
img_dir = os.path.join(current_dir, 'img')

#TODO - Settings tab, per impostazione dell'assistente vocale e implementazioni future
#               NOTA: per il tipo di modello indicare se è già installato o necessita installazione
#               NOTA_2: dopo ogni modifica dei parametri dell'assistente vocale è necessario fare il restart

#FIXME - Aggiustare funzionamento della finestra e dei sui controlli (attualmente minimizza ed espandi non sono funzionanti), anche il drag della finestra non è funzionante

#FIXME - Ri-aggiungere la possibilità di ridimensionare il dock-widget 


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

class TitleBar(QWidget):
    def __init__(self, parent=None, ide_instance=None):
        super().__init__(parent)
        self.ide_instance = ide_instance
        self.setFixedHeight(40)
        self.parent_window = parent
        self.pressing = False
        self.start = QPoint(0, 0)
        
        # Abilita il tracciamento del mouse per il drag
        self.setMouseTracking(True)
        
        self.setStyleSheet("""
            background-color: #2C2D3A;
            color: #E0E0E0;
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(0)

        # Logo
        logo_path = os.path.join(img_dir, 'logo.svg')
        logo_widget = QSvgWidget(logo_path)
        logo_widget.setFixedSize(30, 30)
        layout.addWidget(logo_widget)

        # Menu Bar
        self.menu_bar = QMenuBar(self)
        self.setup_menubar_style()
        layout.addWidget(self.menu_bar)

        # Spacer
        layout.addSpacerItem(QSpacerItem(60, 30, QSizePolicy.Expanding ))

        # Window Control Buttons
        self.create_buttons(layout)
        
        # Create Menus
        self.create_menus()

    def setup_menubar_style(self):
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

    def create_buttons(self, layout):
        button_style = """
            QPushButton {
                background-color: transparent;
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

        # Minimize Button
        self.minimize_button = QPushButton("−")
        self.minimize_button.setFixedSize(30, 30)
        self.minimize_button.setStyleSheet(button_style)
        self.minimize_button.clicked.connect(self.minimize_window)
        layout.addWidget(self.minimize_button)

        # Maximize Button
        self.maximize_button = QPushButton("□")
        self.maximize_button.setFixedSize(30, 30)
        self.maximize_button.setStyleSheet(button_style)
        self.maximize_button.clicked.connect(self.toggle_maximize_restore)
        layout.addWidget(self.maximize_button)

        # Close Button
        self.close_button = QPushButton("×")
        self.close_button.setFixedSize(30, 30)
        self.close_button.setStyleSheet(button_style)
        self.close_button.clicked.connect(self.close_window)
        layout.addWidget(self.close_button)

    # Eventi del mouse per il drag della finestra
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.pressing = True
            self.start = event.globalPos()
            self.window_pos = self.parent_window.pos()

    def mouseMoveEvent(self, event):
        if self.pressing and not self.parent_window.isMaximized():
            delta = event.globalPos() - self.start
            self.parent_window.move(self.window_pos + delta)

    def mouseReleaseEvent(self, event):
        self.pressing = False

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.toggle_maximize_restore()

    # Funzioni per i controlli della finestra
    def minimize_window(self):
        self.parent_window.showMinimized()

    def toggle_maximize_restore(self):
        if self.parent_window.isMaximized():
            self.parent_window.showNormal()
            self.maximize_button.setText("□")
        else:
            self.parent_window.showMaximized()
            self.maximize_button.setText("❐")

    def close_window(self):
        self.parent_window.close()

    def create_menus(self):
        file_menu = self.menu_bar.addMenu("File")
        new_file_action = file_menu.addAction("New File")
        new_file_action.triggered.connect(self.ide_instance.create_new_file)
        open_project = file_menu.addAction("Open Project")
        open_project.triggered.connect(lambda: self.ide_instance.project_manager.open_project(self))
        
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
        self.code_editor.setStyleSheet("""
            QTextEdit {
                background-color: #272822;  /* Monokai background */
                color: #f8f8f2;            /* Monokai default text */
                border-radius: 10px;
                padding: 10px;
                selection-background-color: #49483e;  /* Monokai selection */
                selection-color: #f8f8f2;
                font-family: 'Fira Code', 'Consolas', monospace;
            }
            
            QTextEdit:focus {
                border: 1px solid #49483e;
            }
        """)

class SimpleIDE(QMainWindow):
    def __init__(self, project_path):
        super().__init__()
        
        # Imposta le dimensioni minime della finestra
        self.setMinimumSize(800, 600)
        
        # Imposta una dimensione iniziale di default
        self.resize(1200, 800)
        
        # Rimuovi eventuali flag che impediscono il ridimensionamento
        self.setWindowFlags(Qt.Window)
        
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
        
        self.file_explorer = FileExplorerWidget(self, project_path)
        self.folder_dialog = QFileDialog
        self.project_manager = ProjectManager(self.folder_dialog, self.file_explorer)
        self.title_bar = TitleBar(self, ide_instance=self)
        main_layout.addWidget(self.title_bar)
        
        # Splitter orizzontale principale
        self.h_splitter = CosmicSplitter(Qt.Horizontal)
        
        # Aggiungi file explorer
        self.h_splitter.addWidget(self.file_explorer)
        
        # Crea splitter verticale per editor e terminale
        self.v_splitter = CosmicSplitter(Qt.Vertical)
        
        # Configura tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(lambda index: self.close_tab(index))
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
        
        # Aggiungi tab widget al splitter verticale
        self.v_splitter.addWidget(self.tab_widget)
        
        # Crea e aggiungi il terminale al splitter verticale
        self.terminal = Terminal(
            parent=self,
            initial_height=200,
            theme='Monokai'
        )
        self.v_splitter.addWidget(self.terminal)
        
        # Imposta le proporzioni del splitter verticale
        self.v_splitter.setSizes([600, 200])  # Modifica questi valori per cambiare le proporzioni
        
        # Aggiungi il splitter verticale al splitter orizzontale
        self.h_splitter.addWidget(self.v_splitter)
        
        # Imposta le dimensioni del splitter orizzontale
        self.h_splitter.setSizes([250, self.width() - 250])
        
        # Aggiungi il splitter orizzontale al layout principale
        main_layout.addWidget(self.h_splitter)
        
        self.button_container = QWidget()
        self.button_container.setMinimumHeight(50)
        button_container_layout = QVBoxLayout(self.button_container)
        button_container_layout.setContentsMargins(0, 0, 0, 0)
        button_container_layout.setSpacing(0)
        self.change_style("monokai")
        self.create_dock_widget()
        
        # Initialize detector and thread
        self.detector = CombinedDetector()
        self.detector_thread = None
        
        self.tabs = tabs_dictionary()
        # Connetti i pulsanti nel dock widget
        self.start_button.clicked.connect(self.start_detector)
        self.stop_button.clicked.connect(self.stop_detector)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Aggiorna il dock widget quando la finestra viene ridimensionata
        if hasattr(self, 'dock_widget') and self.dock_widget.isVisible():
            self.update_dock_widget_style(self.dockWidgetArea(self.dock_widget))
        
        # Aggiorna le proporzioni dei splitter
        total_width = self.width()
        total_height = self.height()
        
        # Mantieni le proporzioni del file explorer (circa 20% della larghezza)
        file_explorer_width = int(total_width * 0.2)
        editor_width = total_width - file_explorer_width
        self.h_splitter.setSizes([file_explorer_width, editor_width])
        
        # Mantieni le proporzioni del terminale (circa 25% dell'altezza)
        editor_height = int(total_height * 0.75)
        terminal_height = total_height - editor_height
        self.v_splitter.setSizes([editor_height, terminal_height])
        
    def create_dock_widget(self):
        self.dock_widget = QDockWidget("Voice Assistant", self)
        self.dock_widget.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.dock_widget.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetClosable)
        
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

        dock_content = NeumorphicWidget()
        dock_layout = QVBoxLayout(dock_content)
        dock_layout.setContentsMargins(5, 5, 5, 5)
        dock_layout.setSpacing(5)

        # Status label
        self.status_label = QLabel("Assistant not active")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #E0E0E0;
                padding: 5px;
            }
        """)
        dock_layout.addWidget(self.status_label)

        # Transcription text area
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

        # Control buttons
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
            QPushButton:disabled {
                background-color: #1E1F2B;
                color: #808080;
            }
        """
        
        self.start_button = QPushButton("Start Assistant")
        self.stop_button = QPushButton("Stop Assistant")
        self.stop_button.setEnabled(False)
        
        for button in [self.start_button, self.stop_button]:
            button.setStyleSheet(button_style)
            control_layout.addWidget(button)
            
        dock_layout.addLayout(control_layout)

        # Add spacer to push wave background to the bottom
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        dock_layout.addItem(spacer)

        # Add AI button and wave background container
        wave_container = QWidget()
        wave_container_layout = QVBoxLayout(wave_container)
        wave_container_layout.setContentsMargins(0, 0, 0, 0)
        wave_container_layout.setSpacing(0)

        # Add AI button
        self.ai_button = AnimatedCircleButton()
        self.ai_button.setMinimumSize(64, 64)
        self.ai_button.setMaximumSize(120, 120)
        
        button_container = QHBoxLayout()
        button_container.addWidget(self.ai_button, 0, Qt.AlignCenter)
        wave_container_layout.addLayout(button_container)

        # Add wave background
        self.wave_background = AnimatedWaveBackground(wave_container)
        self.wave_background.setFixedHeight(80)
        self.wave_background.setAttribute(Qt.WA_TransparentForMouseEvents)
        wave_container_layout.addWidget(self.wave_background)

        dock_layout.addWidget(wave_container)

        # Scroll area setup
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
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_widget)
        self.dock_widget.hide()


    def create_new_file(self):
        self.file_explorer.create_new_file()

    def add_file_to_tabs(self, file_path):
        if os.path.splitext(file_path)[1] == ".py":
            editor_widget = CodeEditorWidget()
            with open(file_path, "r", encoding="utf8") as f:
                file_content = f.read()
            editor_widget.code_editor.setText(file_content)
            file_name = os.path.basename(file_path)
            if not self.tabs.tab_exists(file_name):
                self.tab_widget.addTab(editor_widget, file_name)
                self.tabs.add_tab(file_name, path=file_path, index=self.tab_widget.count())
                self.tab_widget.setCurrentWidget(editor_widget)
            else:
                data = self.tabs.get_tab(file_name)
                self.tab_widget.setCurrentIndex(data["index"] - 1)

            self.change_style(self.current_style)

    def close_tab(self, index):
        self.tab_widget.removeTab(index)
        self.tabs.remove_tab(self.tabs.get_tab_by_index(index + 1))

    def start_detector(self):
        self.detector_thread = DetectorThread(self.detector)
        self.detector_thread.keyword_detected.connect(self.on_keyword_detected)
        self.detector_thread.silence_detected.connect(self.on_silence_detected)
        self.detector_thread.transcription_ready.connect(self.on_transcription_ready)
        self.detector_thread.start()
        self.stopped = False
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status_label.setText("Assistant active - Waiting for 'Alexa'...")
        #self.ai_button.start_animation()

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
        
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText("Assistant stopped")
        #self.ai_button.stop_animation()

    def on_keyword_detected(self):
        self.status_label.setText("Alexa detected! Listening...")
        #self.ai_button.set_active_state(True)

    def on_silence_detected(self):
        self.status_label.setText("Processing audio...")
        #self.ai_button.set_processing_state(True)

    def on_transcription_ready(self, transcription):
        current_text = self.transcription_text.toPlainText()
        if current_text:
            new_text = f"{current_text}\n{transcription}"
        else:
            new_text = transcription
        self.transcription_text.setPlainText(new_text)
        self.status_label.setText("Assistant active - Waiting for 'Alexa'...")
       # self.ai_button.set_active_state(False)
       # self.ai_button.set_processing_state(False)

    def closeEvent(self, event):
        self.stop_detector()
        event.accept()

    def toggle_dock_widget(self):
        
        if self.dock_widget.isVisible():
            self.dock_widget.hide()
        else:
            self.dock_widget.show()

    def change_style(self, style_name="monokai"):
        self.current_style = style_name
        for index in range(self.tab_widget.count()):
            editor_widget = self.tab_widget.widget(index)
            editor_widget.set_style(style_name)

    def update_dock_widget_style(self, dock_area):
        screen_size = QApplication.desktop().screenGeometry()
        if self.dock_widget.isFloating():
            # Dimensioni quadrate prestabilite per la modalità floating
            square_size = 300  
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

#     def open_project(self):
#         project_folder = None
#         project_folder = self.folder_dialog.getExistingDirectory(self,"Open Project", "/")
#         project_name = os.path.basename(project_folder)
#         now = datetime.now()
#         print(now.timestamp())
#         timestamp = now.timestamp()
#         #root_path = os.path.join(os.path.dirname(os.path.abspath(__file__)))
#         #with open(os.path.join(root_path,"/my-projects.aide.json", 'rw')) as file:
#         all_projects = {"projects": []}
#         my_projects_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),  "my-projects.aide.json")
#         if os.path.isfile(my_projects_path) is False:
#              all_projects = list(all_projects["projects"])

#              all_projects.append({
#                 "name": os.path.basename(project_folder),
#                 "path": project_folder,
#                 "timestamp": timestamp,
#              })
#         else:
#                 with open(my_projects_path) as file:
#                         all_projects = json.load(file)
#                         all_projects.append({
#                                 "name": project_name,
#                                 "path": project_folder,
#                                 "timestamp": timestamp,
#                         })
#         with open(my_projects_path, 'w') as file:
#                 json.dump(all_projects, file, indent=4,  separators=(',',': '))
#         self.file_explorer.update_ui(project_folder)
#         json_data =  '{"project_name":"'+project_name+'"}'
#         self.update_project_json(project_folder, json_data)

#     def update_project_json(self,path, data): #IF DONT EXIST CREATE IT
#         # Create the full file path with a dot prefix
#         filename = "project.aide.json"  # Change this to your desired filename
#         full_path = os.path.join(path, filename)
#         if sys.platform == "win32" and os.path.exists(full_path):
#                 FILE_ATTRIBUTE_NORMAL = 0x80
#                 ctypes.windll.kernel32.SetFileAttributesW(full_path, FILE_ATTRIBUTE_NORMAL)
#         # Write the JSON file
#         with open(full_path, 'w') as f:
#                 json.dump(data, f, indent=4)
#         # Make file hidden on Windows
#         if sys.platform == "win32":
#                 FILE_ATTRIBUTE_HIDDEN = 0x02
#                 ctypes.windll.kernel32.SetFileAttributesW(full_path, FILE_ATTRIBUTE_HIDDEN)