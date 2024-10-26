import os
import shutil
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTreeView, QFileSystemModel,
    QInputDialog, QMessageBox, QMenu
)
from PyQt5.QtCore import Qt, QDir
from PyQt5.QtGui import QIcon

#TODO Implementazione dei progetti con tutti i path dei vari .proj.json files salvati in un projects.json

#TODO La cartella selezionata nel file explorer dovrebbe cambiare se si cambiano le tab (necessarie modifiche anche al file "tab_dictionary.py")

class FileExplorerWidget(QWidget):
    def __init__(self, simple_ide): 
        super().__init__()
        self.simple_ide = simple_ide
        self.setMinimumWidth(250)
        self.setup_ui("")

    def update_ui(self,updated_path):
        self.model.setRootPath(updated_path)
        self.tree_view.setRootIndex(self.model.index(updated_path))
        
    def onExplorerClicked(self, index):
        path = self.sender().model().filePath(index)
        self.simple_ide.add_file_to_tabs(path)

    def setup_ui(self,path_to_show):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        # Header
        header = QWidget()
        header.setFixedHeight(30)
        header.setStyleSheet("""
            background-color: #2C2D3A;
            color: #E0E0E0;
            padding: 5px;
            font-weight: bold;
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 0, 10, 0)
        
        explorer_label = QLabel("EXPLORER")
        explorer_label.setStyleSheet("color: #E0E0E0;")
        header_layout.addWidget(explorer_label)
        
        layout.addWidget(header)
        
        # Tree View
        self.tree_view = QTreeView()
        self.tree_view.clicked.connect(self.onExplorerClicked)
        self.tree_view.setStyleSheet("""
            QTreeView {
                background-color: #2C2D3A;
                border: none;
                color: #E0E0E0;
            }
            QTreeView::item {
                padding: 5px;
                border-radius: 3px;
            }
            QTreeView::item:selected {
                background-color: #3D3E4D;
            }
            QTreeView::item:hover {
                background-color: #3D3E4D;
            }
            QTreeView::branch {
                background-color: #2C2D3A;
            }
            QTreeView::branch:has-siblings:!adjoins-item {
                border-image: url(img/vline.svg) 0;
            }
            QTreeView::branch:has-siblings:adjoins-item {
                border-image: url(img/branch-more.svg) 0;
            }
            QTreeView::branch:!has-children:!has-siblings:adjoins-item {
                border-image: url(img/branch-end.svg) 0;
            }
            QTreeView::branch:has-children:!has-siblings:closed,
            QTreeView::branch:closed:has-children:has-siblings {
                border-image: none;
                image: url(img/branch-closed.svg);
            }
            QTreeView::branch:open:has-children:!has-siblings,
            QTreeView::branch:open:has-children:has-siblings {
                border-image: none;
                image: url(img/branch-open.svg);
            }
        """)
        
        # File System Model
        
        self.model = QFileSystemModel()
        self.model.setRootPath(path_to_show)#
        
        # Custom File System Model per le icone personalizzate
        class CustomFileSystemModel(QFileSystemModel):
            def data(self, index, role):
                if role == Qt.DecorationRole:
                    fileInfo = self.fileInfo(index)
                    if fileInfo.isDir():
                        return QIcon("img/folder.svg")
                    else:
                        return QIcon("img/file.svg")
                return super().data(index, role)
        '''
        self.model = CustomFileSystemModel()
        self.model.setRootPath(QDir.currentPath())
        '''
        self.tree_view.setModel(self.model)
        self.tree_view.setRootIndex(self.model.index(path_to_show))
        
        # Nascondi le colonne non necessarie
        for i in range(1, 4):
            self.tree_view.hideColumn(i)
            
        layout.addWidget(self.tree_view)
        
        # Context Menu
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.show_context_menu)
        

        
    def show_context_menu(self, position):
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #2C2D3A;
                color: #E0E0E0;
                border: 1px solid #3D3E4D;
                border-radius: 5px;
            }
            QMenu::item {
                padding: 5px 20px;
            }
            QMenu::item:selected {
                background-color: #3D3E4D;
                border-radius: 3px;
            }
        """)
        
        new_file = menu.addAction("New File")
        new_folder = menu.addAction("New Folder")
        menu.addSeparator()
        rename = menu.addAction("Rename")
        delete = menu.addAction("Delete")
        
        # Connetti le azioni
        new_file.triggered.connect(self.create_new_file)
        new_folder.triggered.connect(self.create_new_folder)
        rename.triggered.connect(self.rename_item)
        delete.triggered.connect(self.delete_item)
        
        menu.exec_(self.tree_view.mapToGlobal(position))
        
    def create_new_file(self):
        index = self.tree_view.currentIndex()
        current_path = self.model.filePath(index)
        if not self.model.isDir(index):
            current_path = os.path.dirname(current_path)
            
        name, ok = QInputDialog.getText(self, "New File", "Enter file name:")
        if ok and name:
            file_path = os.path.join(current_path, name)
            with open(file_path, 'w') as f:
                self.simple_ide.add_file_to_tabs(file_path)
                pass
            
    def create_new_folder(self):
        index = self.tree_view.currentIndex()
        current_path = self.model.filePath(index)
        if not self.model.isDir(index):
            current_path = os.path.dirname(current_path)
            
        name, ok = QInputDialog.getText(self, "New Folder", "Enter folder name:")
        if ok and name:
            folder_path = os.path.join(current_path, name)
            os.makedirs(folder_path, exist_ok=True)
            
    def rename_item(self):
        index = self.tree_view.currentIndex()
        current_path = self.model.filePath(index)
        current_name = os.path.basename(current_path)
        
        name, ok = QInputDialog.getText(self, "Rename", "Enter new name:", text=current_name)
        if ok and name:
            new_path = os.path.join(os.path.dirname(current_path), name)
            os.rename(current_path, new_path)
            
    def delete_item(self):
        index = self.tree_view.currentIndex()
        path = self.model.filePath(index)
        
        reply = QMessageBox.question(self, "Delete",
                                   f"Are you sure you want to delete {os.path.basename(path)}?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
                