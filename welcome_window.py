import json
import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTreeWidget, QTreeWidgetItem, QFileDialog, QStyleOption, QStyle)
from PyQt5.QtCore import Qt, QPoint, QPointF, pyqtSignal
from PyQt5.QtGui import QIcon, QFont, QPainter, QPen, QColor, QLinearGradient, QPolygonF
from file_explorer_widget import FileExplorerWidget
from projects import ProjectManager
from Aidee import SimpleIDE
from neumorphic_widgets import NeumorphicButton


class WelcomeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.folder_dialog = QFileDialog
        self.file_explorer = FileExplorerWidget
        self.project_manager = ProjectManager(self.folder_dialog, self.file_explorer)
        # Get the absolute path of the current script
        default_path = os.path.abspath(os.path.dirname(__file__))
        icon_path = os.path.join(default_path, "icons", "logo_new.ico")
        if not os.path.exists(icon_path):
                print("Icon file does not exist:", icon_path)
        else:
                print("Icon file found.")
        # Set the window icon
        import ctypes
        myappid = 'mountain.aidee.0.1v' # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        self.setWindowIcon(QIcon(icon_path))
        self.setWindowTitle("Visual Studio 2022")
        self.setGeometry(100, 100, 1200, 700)  # Dimensioni aumentate per migliore leggibilità
        
        # Stile principale migliorato
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1E1F2B;
            }
            QLabel {
                color: #E0E0E0;
                font-family: 'Segoe UI';
            }
            QLabel#headerLabel {
                font-size: 24px;
                font-weight: bold;
                padding: 10px 0;
            }
            QLineEdit {
                background-color: #2C2D3A;
                color: #E0E0E0;
                border: 1px solid #3D3E4D;
                border-radius: 4px;
                padding: 8px 12px;
                font-family: 'Segoe UI';
                font-size: 13px;
                margin: 5px 0;
            }
            QLineEdit:focus {
                border: 1px solid #0078D4;
                background-color: #252632;
            }
            QTreeWidget {
                background-color: transparent;
                color: #E0E0E0;
                border: none;
                font-family: 'Segoe UI';
                font-size: 13px;
                padding: 5px;
            }
            QTreeWidget::item {
                padding: 8px 4px;
                border-radius: 4px;
            }
            QTreeWidget::item:selected {
                background-color: #3D3E4D;
            }
            QTreeWidget::branch {
                background: transparent;
                border: none;
            }
            QTreeWidget::branch:has-children:!has-siblings,
            QTreeWidget::branch:has-children:has-siblings {
                border: none;
            }
        """)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(30, 30, 30, 30)  # Margini esterni aumentati
        main_layout.setSpacing(40)  # Spazio tra i pannelli
        
        # Left panel
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(15)  # Spazio tra elementi
        
        # Recent section
        recent_label = QLabel("Apri recenti")
        recent_label.setObjectName("headerLabel")
        
        search_box = QLineEdit()
        search_box.setPlaceholderText("Cerca in recenti (ALT+S)")
        search_box.setMinimumHeight(32)
        
        # Tree widget
        self.tree = ButtonTreeWidget()
        
        # Popolamento tree
        today_projects = self.project_manager.getTodayProjects()
        month_projects = self.project_manager.getMonthProjects()
        all_projects = self.project_manager.getAllProjects()

        make_tree(self.tree, "Today", today_projects)
        make_tree(self.tree, "This Month", month_projects)
        make_tree(self.tree, "All", all_projects)

        self.tree.projectClicked.connect(lambda path: self.open_main_window(path))

        left_layout.addWidget(recent_label)
        left_layout.addWidget(search_box)
        left_layout.addWidget(self.tree, 1)
        
        # Right panel
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(15)
        
        # Start section
        start_label = QLabel("Inizia subito")
        start_label.setObjectName("headerLabel")
        right_layout.addWidget(start_label)
        
        # Action buttons con stile migliorato
        actions = [
            ("Clona un repository", "Consente di ottenere il codice da un repository\nonline, come GitHub o Azure DevOps"),
            ("Apri un progetto o una soluzione", "Consente di aprire un progetto locale o un file\ncon estensione sln di Visual Studio"),
            ("Apri una cartella locale", "Consente di esplorare e modificare il codice in\nqualsiasi cartella"),
            ("Crea un nuovo progetto", "Consente di scegliere un progetto modello con\nscaffolding del codice per iniziare")
        ]
        
        for action, description in actions:
            action_button = QPushButton()
            action_button.setStyleSheet("""
                QPushButton {
                    background-color: #2C2D3A;
                    color: #E0E0E0;
                    border: none;
                    border-radius: 4px;
                    padding: 15px;
                    text-align: left;
                    font-family: 'Segoe UI';
                }
                QPushButton:hover {
                    background-color: #3D3E4D;
                }
                QPushButton:pressed {
                    background-color: #252632;
                }
            """)
            
            # Layout del bottone
            button_layout = QVBoxLayout()
            button_layout.setSpacing(5)
            
            title = QLabel(action)
            title.setStyleSheet("font-size: 14px; font-weight: bold; color: #E0E0E0;")
            desc = QLabel(description)
            desc.setStyleSheet("font-size: 12px; color: #A0A0A0;")
            
            button_layout.addWidget(title)
            button_layout.addWidget(desc)
            action_button.setLayout(button_layout)
            action_button.setMinimumHeight(80)
            
            right_layout.addWidget(action_button)
        
        right_layout.addStretch()
        
        # Continue button
        continue_button = QPushButton("Continua senza codice →")
        continue_button.clicked.connect(self.open_main_window)
        continue_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #0078D4;
                border: none;
                padding: 10px;
                text-align: right;
                font-family: 'Segoe UI';
                font-size: 13px;
            }
            QPushButton:hover {
                color: #2297E9;
                text-decoration: underline;
            }
        """)
        right_layout.addWidget(continue_button)
        
        # Add panels to main layout
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 2)
        
    def open_main_window(self, project_path=None):
        self.main_window = SimpleIDE(project_path)
        self.main_window.showMaximized()
        self.close()
    
    def loadProjects(self):
        root_path = os.path.join(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(root_path,"/my-projects.aide.json", 'r')) as file:
                data = json.load(file)


class ButtonTreeWidget(QTreeWidget):
    projectClicked = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderHidden(True)
        self.setStyleSheet("""
            QTreeWidget {
                background-color: transparent;
                color: #E0E0E0;
                border: none;
                font-family: 'Segoe UI';
                padding: 5px;
            }
            QTreeWidget::item {
                padding: 8px;
                border-radius: 4px;
            }
            QTreeWidget::item:selected {
                background-color: #3D3E4D;
            }
            QTreeWidget::branch {
                background: transparent;
            }
            QTreeWidget::branch:has-children {
                border-image: none;
                image: none;
            }
            QTreeWidget::branch:has-children:open {
                border-image: none;
                image: none;
            }
        """)


class TreeButtonWidget(QWidget):
    clicked = pyqtSignal(str)
    
    def __init__(self, text, project_path, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.button = QPushButton(text)  
        self.button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #E0E0E0;
                border: none;
                text-align: left;
                font-family: 'Segoe UI';
                font-size: 13px;
                border-radius: 4px;
                padding-left: 8px;
                padding-right: 8px;
                margin: 0;
                height: 50px;
                line-height: 50px;  
            }
            QPushButton:hover {
                background-color: #3D3E4D;
            }
            QPushButton:pressed {
                background-color: #252632;
            }
        """)
        self.button.setMinimumSize(100, 30)
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
    root_item = QTreeWidgetItem(tree_widget)
    root_item.setText(0, label)
    root_item.setExpanded(True)
    
    for project in projects:
        item = QTreeWidgetItem(root_item)
        button_widget = TreeButtonWidget(project["name"], project["path"])
        button_widget.clicked.connect(tree_widget.projectClicked.emit)
        tree_widget.setItemWidget(item, 0, button_widget)
        
    return root_item