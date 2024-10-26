from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                           QTreeWidget, QTreeWidgetItem)
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QIcon, QFont, QPainter, QPen, QColor, QLinearGradient
import sys

from simple_ide import SimpleIDE

class NeumorphicWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAutoFillBackground(True)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        bg_color = QColor("#2C2D3A")
        dark_shadow = bg_color.darker(130)
        light_shadow = bg_color.lighter(110)
        
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, bg_color.lighter(105))
        gradient.setColorAt(1, bg_color)
        
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 10, 10)
        
        painter.setPen(QPen(dark_shadow, 2))
        painter.drawLine(self.rect().topLeft() + QPoint(5, 5),
                        self.rect().bottomLeft() + QPoint(5, -5))
        painter.drawLine(self.rect().topLeft() + QPoint(5, 5),
                        self.rect().topRight() + QPoint(-5, 5))
        
        painter.setPen(QPen(light_shadow, 2))
        painter.drawLine(self.rect().bottomLeft() + QPoint(5, -5),
                        self.rect().bottomRight() + QPoint(-5, -5))
        painter.drawLine(self.rect().topRight() + QPoint(-5, 5),
                        self.rect().bottomRight() + QPoint(-5, -5))

class NeumorphicButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QPushButton {
                background-color: #2C2D3A;
                color: #E0E0E0;
                border: none;
                border-radius: 10px;
                padding: 10px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #3D3E4D;
            }
        """)

class VSCodeClone(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Visual Studio 2022")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1E1F2B;
            }
            QLabel {
                color: #E0E0E0;
            }
            QLineEdit {
                background-color: #2C2D3A;
                color: #E0E0E0;
                border: none;
                border-radius: 10px;
                padding: 8px;
            }
            QTreeWidget {
                background-color: #2C2D3A;
                color: #E0E0E0;
                border: none;
                border-radius: 10px;
            }
            QTreeWidget::item {
                padding: 5px;
            }
            QTreeWidget::item:selected {
                background-color: #3D3E4D;
            }
        """)
        
        # Central widget with neumorphic style
        central_widget = NeumorphicWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Left panel
        left_panel = NeumorphicWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Recent section
        recent_label = QLabel("Apri recenti")
        recent_label.setFont(QFont("Segoe UI", 14))
        search_box = QLineEdit()
        search_box.setPlaceholderText("Cerca in recenti (ALT+S)")
        
        # Tree widget for recent files
        tree = QTreeWidget()
        tree.setHeaderHidden(True)
        
        # Adding recent items
        oggi = QTreeWidgetItem(tree, ["Oggi"])
        prova1 = QTreeWidgetItem(oggi, ["prova1"])
        prova1.addChild(QTreeWidgetItem(["C:\\Users\\user\\Desktop\\Informatica"]))
        
        redphone = QTreeWidgetItem(oggi, ["RedPhone"])
        redphone.addChild(QTreeWidgetItem(["C:\\Users\\user\\source\\repos"]))
        
        left_layout.addWidget(recent_label)
        left_layout.addWidget(search_box)
        left_layout.addWidget(tree)
        left_layout.addStretch()
        
        # Right panel
        right_panel = NeumorphicWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Start section
        start_label = QLabel("Inizia subito")
        start_label.setFont(QFont("Segoe UI", 14))
        
        # Action buttons
        actions = [
            ("Clona un repository", "Consente di ottenere il codice da un repository\nonline, come GitHub o Azure DevOps"),
            ("Apri un progetto o una soluzione", "Consente di aprire un progetto locale o un file\ncon estensione sln di Visual Studio"),
            ("Apri una cartella locale", "Consente di esplorare e modificare il codice in\nqualsiasi cartella"),
            ("Crea un nuovo progetto", "Consente di scegliere un progetto modello con\nscaffolding del codice per iniziare")
        ]
        
        right_layout.addWidget(start_label)
        
        for action, description in actions:
            action_button = NeumorphicButton(f"{action}\n{description}")
            action_button.setMinimumHeight(80)
            right_layout.addWidget(action_button)
        
        right_layout.addStretch()
        
        # Continue without code button
        continue_button = NeumorphicButton("Continua senza codice →")
        continue_button.clicked.connect(self.open_main_window)
        continue_button.setStyleSheet(continue_button.styleSheet() + "text-align: right;")
        right_layout.addWidget(continue_button)
        
        # Add panels to main layout with spacing
        main_layout.addWidget(left_panel, 1)
        main_layout.addSpacing(20)
        main_layout.addWidget(right_panel, 2)
        
    def open_main_window(self, project_path):
        """Open the main IDE window with the selected project"""
        self.main_window = SimpleIDE(project_path)  # Your existing main window class
        self.main_window.showMaximized()  # Imposta la finestra a full size di default
        self.close()
        

