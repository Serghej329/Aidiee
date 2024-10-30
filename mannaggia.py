from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, 
                           QPlainTextEdit, QFrame)
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect
from PyQt5.QtGui import QColor, QFont

class CollapsibleTerminal(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Colori tema scuro
        self.BACKGROUND_COLOR = "#2C2D3A"
        self.TEXT_COLOR = "#E4E4E4"
        self.ERROR_COLOR = "#FF5555"
        self.BORDER_COLOR = "#383A59"
        
        self.is_expanded = False
        self.setupUI()
        
    def setupUI(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Contenitore principale con bordo
        self.container = QFrame(self)
        self.container.setStyleSheet(f"""
            QFrame {{
                background-color: {self.BACKGROUND_COLOR};
                border: 1px solid {self.BORDER_COLOR};
                border-radius: 4px;
            }}
        """)
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(10, 10, 10, 10)
        container_layout.setSpacing(5)
        
        # Header con errore principale
        self.header = QWidget()
        header_layout = QVBoxLayout(self.header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Label "_terminal" con stile
        terminal_label = QLabel("_terminal")
        terminal_label.setStyleSheet(f"""
            QLabel {{
                color: {self.TEXT_COLOR};
                font-family: 'Consolas';
                font-size: 12px;
            }}
        """)
        
        # Errore principale
        self.error_label = QLabel("Error on line 142 - Reference error")
        self.error_label.setStyleSheet(f"""
            QLabel {{
                color: {self.ERROR_COLOR};
                font-family: 'Consolas';
                font-size: 12px;
                font-weight: bold;
            }}
        """)
        
        header_layout.addWidget(terminal_label)
        header_layout.addWidget(self.error_label)
        
        # Pulsante espansione (triangolo)
        self.expand_button = QPushButton("▼")
        self.expand_button.setStyleSheet(f"""
            QPushButton {{
                color: {self.TEXT_COLOR};
                border: none;
                background: transparent;
                padding: 5px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                color: #FFFFFF;
            }}
        """)
        self.expand_button.clicked.connect(self.toggle_expansion)
        
        # Area dettagli errore (inizialmente nascosta)
        self.details_area = QWidget()
        details_layout = QVBoxLayout(self.details_area)
        details_layout.setContentsMargins(0, 10, 0, 0)
        
        # Prompt e dettagli errore
        self.prompt_label = QLabel("matteo@progetto_ai:$")
        self.prompt_label.setStyleSheet(f"""
            QLabel {{
                color: #50FA7B;
                font-family: 'Consolas';
                font-size: 12px;
            }}
        """)
        
        self.error_details = QPlainTextEdit()
        self.error_details.setPlainText("AttributeError: A instance has no attribute 'v'\n"
                                      "ValueError: invalid literal for int() with base 10: 'xyz'")
        self.error_details.setReadOnly(True)
        self.error_details.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: transparent;
                color: {self.ERROR_COLOR};
                border: none;
                font-family: 'Consolas';
                font-size: 12px;
            }}
        """)
        self.error_details.setFixedHeight(60)
        
        details_layout.addWidget(self.prompt_label)
        details_layout.addWidget(self.error_details)
        
        # Inizialmente nascondiamo i dettagli
        self.details_area.hide()
        
        # Aggiunta widgets al layout principale
        container_layout.addWidget(self.header)
        container_layout.addWidget(self.expand_button, 0, Qt.AlignRight)
        container_layout.addWidget(self.details_area)
        
        self.layout.addWidget(self.container)
        
        # Impostiamo dimensioni iniziali
        self.setFixedHeight(80)
    
    def toggle_expansion(self):
        self.is_expanded = not self.is_expanded
        
        # Animazione espansione
        animation = QPropertyAnimation(self, b"minimumHeight")
        animation.setDuration(200)
        
        if self.is_expanded:
            self.details_area.show()
            animation.setStartValue(80)
            animation.setEndValue(200)
            self.expand_button.setText("▲")
        else:
            animation.setStartValue(200)
            animation.setEndValue(80)
            animation.finished.connect(lambda: self.details_area.hide())
            self.expand_button.setText("▼")
            
        animation.start()
    
    def set_error(self, main_error, detailed_error):
        self.error_label.setText(main_error)
        self.error_details.setPlainText(detailed_error)

# Esempio di utilizzo
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    terminal = CollapsibleTerminal()
    terminal.set_error(
        "Error on line 142 - Reference error",
        "AttributeError: A instance has no attribute 'v'\n"
        "ValueError: invalid literal for int() with base 10: 'xyz'"
    )
    terminal.show()
    
    sys.exit(app.exec_())