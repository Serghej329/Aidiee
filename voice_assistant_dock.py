from PyQt5.QtWidgets import (
    QDockWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpacerItem, QSizePolicy, QWidget, QScrollArea, QApplication, QLineEdit, QPlainTextEdit, QSplitter, QMenu
)
from PyQt5.QtCore import Qt
from neumorphic_widgets import NeumorphicWidget, NeumorphicButton, NeumorphicComboBox, NeumorphicTextEdit
from animated_wave_background import AnimatedWaveBackground
from animated_circle_button import SimpleVoiceButton
from PyQt5.QtWidgets import QLabel, QGraphicsDropShadowEffect

class VoiceAssistantDock(QDockWidget):
    def __init__(self, parent=None, ide_instance=None):
        super().__init__("Voice Assistant", parent)
        
        self.ide_instance = ide_instance
        self.setup_dock_widget()
        self.setup_ui()
        self.hide()

    def setup_dock_widget(self):
        """Configure the basic dock widget properties"""
        self.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.setFeatures(
            QDockWidget.DockWidgetMovable |
            QDockWidget.DockWidgetFloatable |
            QDockWidget.DockWidgetClosable
        )
        self.setStyleSheet("""
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
        
        # Minimalist neumorphic styling for the title
        title_widget = NeumorphicWidget()
        title_layout = QHBoxLayout(title_widget)
        title_layout.setContentsMargins(5, 5, 5, 5)
        title_layout.setSpacing(0)

        title_label = QLabel("Voice Assistant")
        title_label.setAlignment(Qt.AlignCenter)

        title_label.setStyleSheet("""
            color: #f5f5f5;
            font-size: 16px;
            font-weight: bold;
        """)
        
        shadow_effect = QGraphicsDropShadowEffect()
        shadow_effect.setOffset(1, 1)
        shadow_effect.setBlurRadius(5)
        shadow_effect.setColor(Qt.black)

        title_label.setGraphicsEffect(shadow_effect)

        title_layout.addWidget(title_label)
        self.setTitleBarWidget(title_widget)

    def setup_ui(self):
        """Set up the main UI components"""
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # Widget contenitore - scorrevole
        content_widget = NeumorphicWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(5, 5, 5, 5)
        content_layout.setSpacing(5)

        self._setup_status_label(content_layout)

        # Splitter per l'area di chat e la casella di testo
        splitter = QSplitter(Qt.Vertical)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #4c3d4d;
                height: 5px;
            }
        """)

        # Configura l'area di testo della chat
        self.chat_text = NeumorphicTextEdit()
        self.chat_text.setReadOnly(True)
        self.chat_text.setMinimumHeight(100)
        self.chat_text.setStyleSheet("""
            QTextEdit {
                background-color: #1E1F2B;
                border: none;
                padding: 8px;
                color: #E0E0E0;
            }
        """)
        splitter.addWidget(self.chat_text)

        # textbox below transcription area
        self.textbox = QPlainTextEdit(self)
        self.textbox.setPlaceholderText("Digita il tuo comando...")
        self.textbox.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1E1F2B;
                color: #E0E0E0;
                padding: 8px;
            }
        """)
        self.textbox.setMinimumHeight(50)
        splitter.addWidget(self.textbox)

        # Imposta le dimensioni iniziali per il splitter
        splitter.setSizes([200, 50])

        content_layout.addWidget(splitter)

        # Scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(content_widget)
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

        main_layout.addWidget(scroll_area, 1)

        # Unified container for both button and waves
        bottom_widget = NeumorphicWidget()
        bottom_widget.setMinimumHeight(100)
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(0)

        interaction_container = QWidget()
        interaction_container.setStyleSheet("background: transparent;")
        
        self.wave_background = AnimatedWaveBackground(interaction_container)
        self.wave_background.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.wave_background.setStyleSheet("background: transparent;")
        
        self.ai_button = SimpleVoiceButton(interaction_container, ide_instance=self.ide_instance)
        self.ai_button.setFixedSize(128, 128)
        
        self.wave_background.lower()
        self.ai_button.raise_()
        
        bottom_layout.addWidget(interaction_container)

        main_layout.addWidget(bottom_widget, 0)

        self.setWidget(main_widget)
        interaction_container.resizeEvent = lambda e: self._handle_resize(e, interaction_container)


    def _setup_status_label(self, layout):
        """Set up the status label"""
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(5)

        self.status_label = QLabel("Assistente non attivo")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #E0E0E0;
                padding: 5px;
            }
        """)
        status_layout.addWidget(self.status_label)

        # Aggiunge un piccolo pulsante a destra della label di stato
        self.menu_button = QPushButton("▼")
        self.menu_button.setFixedSize(20, 20)
        self.menu_button.setStyleSheet("""
            QPushButton {
                background-color: #3D3E4D;
                color: #E0E0E0;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #4D4E5D;
            }
        """)
        self.menu_button.clicked.connect(self.show_menu)
        status_layout.addWidget(self.menu_button)

        status_widget = QWidget()
        status_widget.setLayout(status_layout)
        layout.addWidget(status_widget)

    def _handle_resize(self, event, container):
        """Gestisce gli eventi di ridimensionamento per il QSplitter"""
        self.wave_background.setGeometry(0, 0, container.width(), container.height())
        
        self.ai_button.move(
            (container.width() - self.ai_button.width()) // 2,
            (container.height() - self.ai_button.height()) // 2
        )
        
        self.wave_background.lower()
        self.ai_button.raise_()
        
        QWidget.resizeEvent(container, event)

    def on_keyword_detected(self):
        """Handle keyword detection"""
        self.status_label.setText("Alexa detected! Listening...")

    def on_silence_detected(self):
        """Handle silence detection"""
        self.status_label.setText("Processing audio...")

    def on_transcription_ready(self, transcription):
        """Handle transcription ready"""
        current_text = self.textbox.toPlainText()
        if current_text:
            new_text = f"{current_text}\n{transcription}"
        else:
            new_text = transcription
        self.textbox.setPlainText(new_text)
        self.status_label.setText("Assistant active - Waiting for 'Alexa'...")

    def toggle_visibility(self):
        """Toggle dock widget visibility"""
        if self.isVisible():
            self.hide()
        else:
            self.show()

    def show_menu(self):
        """Menu dei modelli con gestione del cambio modello"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2C2D3A;
                border: none;
                padding: 5px;
                color: #E0E0E0;
            }
            QMenu::item {
                padding: 10px;
                text-align: left;
                border-radius:5px;
            }
            QMenu::item:selected {
                background-color: #3D3E4D;
            }
        """)
        

        menu.addAction("Base")
        menu.addAction("Medium")
        menu.addAction("Advanced")
        
        
        """Posizione corretta del btn"""
        menu.exec_(self.menu_button.mapToGlobal(self.menu_button.rect().bottomLeft()))
        # self.ide_instance.CombineDetector.whisper_model_version = "large"
       

        