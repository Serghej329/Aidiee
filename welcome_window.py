from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                           QTreeWidget, QTreeWidgetItem,QFileDialog)
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QIcon, QFont, QPainter, QPen, QColor, QLinearGradient
import sys
import json
import os
from projects import ProjectManager
from file_explorer_widget import FileExplorerWidget

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

class WelcomeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.folder_dialog = QFileDialog
        self.file_explorer = FileExplorerWidget
        self.project_manager = ProjectManager(self.folder_dialog,self.file_explorer)
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
        # oggi = QTreeWidgetItem(tree, ["Oggi"])
        # prova1 = QTreeWidgetItem(oggi, ["prova1"])
        # prova1.addChild(QTreeWidgetItem(["C:\\Users\\user\\Desktop\\Informatica"]))
        
        # In WelcomeWindow.__init__, replace the existing tree widget creation with:
        self.tree = ButtonTreeWidget()
        left_layout.addWidget(self.tree)

        # Example of how to populate the tree with different project categories:
        today_projects = self.project_manager.getTodayProjects()
        month_projects = self.project_manager.getMonthProjects()
        all_projects = self.project_manager.getAllProjects()

        make_tree(self.tree, "Today", today_projects)
        make_tree(self.tree, "This Month", month_projects)
        make_tree(self.tree, "All", all_projects)

        # Connect the tree's itemClicked signal to handle project opening
        self.tree.projectClicked.connect(lambda path: self.open_main_window(path))

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
        from simple_ide import SimpleIDE
        # Now project_path will contain the actual path from the clicked project
        self.main_window = SimpleIDE(project_path)  
        self.main_window.showMaximized()
        self.close()
    
    def  loadProjects(self):
        root_path = os.path.join(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(root_path,"/my-projects.aide.json", 'r')) as file:
                data = json.load(file)
        
from PyQt5.QtWidgets import (QTreeWidgetItem, QTreeWidget, QPushButton, 
                           QWidget, QHBoxLayout)
from PyQt5.QtCore import Qt, pyqtSignal

class ButtonTreeWidget(QTreeWidget):
    """Custom Tree Widget that supports button items"""
    projectClicked = pyqtSignal(str)  # Signal to emit the project path when clicked
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderHidden(True)
        self.setStyleSheet("""
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

class TreeButtonWidget(QWidget):
    """Custom widget that contains a button for tree items"""
    clicked = pyqtSignal(str)  # Signal to emit the project path when clicked
    
    def __init__(self, text, project_path, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.button = QPushButton(text)
        self.button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #E0E0E0;
                border: none;
                text-align: left;
                padding: 5px;
                width: 100%;
            }
            QPushButton:hover {
                background-color: #3D3E4D;
                border-radius: 5px;
            }
        """)
        self.project_path = project_path
        self.button.clicked.connect(self._on_clicked)
        
        layout.addWidget(self.button)
        
    def _on_clicked(self):
        folder_dialog = QFileDialog
        file_explorer = FileExplorerWidget
        project_manager = ProjectManager(folder_dialog, file_explorer)
        project_manager.updateTimestamp(self.project_path)
        self.clicked.emit(self.project_path)

def make_tree(tree_widget, label, projects):
    """
    Create a tree with buttons from a list of projects.
    
    Args:
        tree_widget (ButtonTreeWidget): The tree widget to populate
        label (str): Label for the root item (e.g., "Today", "This Month")
        projects (list): List of project dictionaries from ProjectManager
    """
    # Create root item
    root_item = QTreeWidgetItem(tree_widget)
    root_item.setText(0, label)
    root_item.setExpanded(True)
    
    # Add project items
    for project in projects:
        # Create item to hold the button widget
        item = QTreeWidgetItem(root_item)
        
        # Create button widget with project name and hidden path
        button_widget = TreeButtonWidget(project["name"], project["path"])
        button_widget.clicked.connect(tree_widget.projectClicked.emit)
        
        # Set the button widget for the item
        tree_widget.setItemWidget(item, 0, button_widget)
        
    return root_item
