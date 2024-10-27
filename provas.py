from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                           QTreeWidget, QTreeWidgetItem, QStyleOption, QStyle)
from PyQt5.QtCore import Qt, QPoint, QPointF
from PyQt5.QtGui import QIcon, QFont, QPainter, QPen, QColor, QLinearGradient, QPolygonF
import sys

from simple_ide import SimpleIDE
from neumorphic_widgets import NeumorphicWidget, NeumorphicButton


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
                padding: 8px;
            }
            QTreeWidget {
                background-color: #2C2D3A;
                color: #E0E0E0;
                border: none;
            }
            QTreeWidget::item {
                padding: 5px;
            }
            QTreeWidget::item:selected {
                background-color: #3D3E4D;
            }
        """)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Left panel
        left_panel = QWidget()
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
        right_panel = QWidget()
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
        continue_button = NeumorphicButton("Continua senza codice")
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

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor("#E0E0E0"), 2))
        painter.setBrush(QColor("#E0E0E0"))
        
        # Draw diamond icon
        diamond = QPolygonF()
        diamond.append(QPointF(self.width() - 30, self.height() - 30))
        diamond.append(QPointF(self.width() - 20, self.height() - 30))
        diamond.append(QPointF(self.width() - 25, self.height() - 20))
        diamond.append(QPointF(self.width() - 30, self.height() - 30))
        painter.drawPolygon(diamond)