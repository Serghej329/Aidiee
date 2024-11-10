from PyQt5.QtWidgets import (
    QDockWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpacerItem, QSizePolicy, QWidget, QScrollArea, QApplication
)
from PyQt5.QtCore import Qt
from neumorphic_widgets import NeumorphicWidget, NeumorphicTextEdit
from animated_wave_background import AnimatedWaveBackground
from animated_circle_button import AnimatedCircleButton
class VoiceAssistantDock(QDockWidget):
    def __init__(self, parent=None,ide_instance=None):
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

    def setup_ui(self):
        """Set up the main UI components"""
        dock_content = NeumorphicWidget()
        dock_layout = QVBoxLayout(dock_content)
        dock_layout.setContentsMargins(5, 5, 5, 5)
        dock_layout.setSpacing(5)

        self._setup_status_label(dock_layout)
        self._setup_transcription_area(dock_layout)
        self._setup_control_buttons(dock_layout)
        self._add_spacer(dock_layout)
        self._setup_wave_container(dock_layout)
        self._setup_scroll_area(dock_content)

    def _setup_status_label(self, layout):
        """Set up the status label"""
        self.status_label = QLabel("Assistant not active")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #E0E0E0;
                padding: 5px;
            }
        """)
        layout.addWidget(self.status_label)

    def _setup_transcription_area(self, layout):
        """Set up the transcription text area"""
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
        layout.addWidget(self.transcription_text)

    def _setup_control_buttons(self, layout):
        """Set up the control buttons"""
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
        self.start_button.clicked.connect(self.ide_instance.start_detector)
        self.stop_button.clicked.connect(self.ide_instance.stop_detector)
        
        self.stop_button.setEnabled(False)

        for button in [self.start_button, self.stop_button]:
            button.setStyleSheet(button_style)
            control_layout.addWidget(button)

        layout.addLayout(control_layout)

    def _add_spacer(self, layout):
        """Add spacer to push wave background to the bottom"""
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout.addItem(spacer)

    def _setup_wave_container(self, layout):
        """Set up the wave container with AI button and wave background"""
        wave_container = QWidget()
        wave_container_layout = QVBoxLayout(wave_container)
        wave_container_layout.setContentsMargins(0, 0, 0, 0)
        wave_container_layout.setSpacing(0)

        # AI button
        self.ai_button = AnimatedCircleButton()
        self.ai_button.setMinimumSize(64, 64)
        self.ai_button.setMaximumSize(120, 120)

        button_container = QHBoxLayout()
        button_container.addWidget(self.ai_button, 0, Qt.AlignCenter)
        wave_container_layout.addLayout(button_container)

        # Wave background
        self.wave_background = AnimatedWaveBackground(wave_container)
        self.wave_background.setFixedHeight(80)
        self.wave_background.setAttribute(Qt.WA_TransparentForMouseEvents)
        wave_container_layout.addWidget(self.wave_background)

        layout.addWidget(wave_container)

    def _setup_scroll_area(self, content_widget):
        """Set up the scroll area"""
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
        self.setWidget(scroll_area)

    def on_keyword_detected(self):
        """Handle keyword detection"""
        self.status_label.setText("Alexa detected! Listening...")
        #self.ai_button.set_active_state(True)

    def on_silence_detected(self):
        """Handle silence detection"""
        self.status_label.setText("Processing audio...")
        #self.ai_button.set_processing_state(True)

    def on_transcription_ready(self, transcription):
        """Handle transcription ready"""
        current_text = self.transcription_text.toPlainText()
        if current_text:
            new_text = f"{current_text}\n{transcription}"
        else:
            new_text = transcription
        self.transcription_text.setPlainText(new_text)
        self.status_label.setText("Assistant active - Waiting for 'Alexa'...")
        #self.ai_button.set_active_state(False)
        #self.ai_button.set_processing_state(False)

    def toggle_visibility(self):
        """Toggle dock widget visibility"""
        if self.isVisible():
            self.hide()
        else:
            self.show()

    def update_style(self, dock_area):
        """Update dock widget style based on dock area"""
        screen_size = QApplication.desktop().screenGeometry()
        if self.isFloating():
            square_size = 300
            self.setFixedSize(square_size, square_size)
        else:
            if dock_area in (Qt.TopDockWidgetArea, Qt.BottomDockWidgetArea):
                self.setFixedHeight(screen_size.height() // 4)
                self.setFixedWidth(screen_size.width())
            elif dock_area in (Qt.LeftDockWidgetArea, Qt.RightDockWidgetArea):
                self.setFixedHeight(screen_size.height())
                self.setFixedWidth(screen_size.width() // 4)