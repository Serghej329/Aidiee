import os
import shutil
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTreeView, QFileSystemModel,
    QInputDialog, QMessageBox, QMenu
)
from PyQt5.QtCore import Qt, QDir
from PyQt5.QtGui import QIcon

class FileExplorerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(250)
        self.setup_ui()
        
    def setup_ui(self):
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
        self.model.setRootPath(QDir.currentPath())
        
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
        
        self.model = CustomFileSystemModel()
        self.model.setRootPath(QDir.currentPath())
        self.tree_view.setModel(self.model)
        self.tree_view.setRootIndex(self.model.index(QDir.currentPath()))
        
        # Nascondi le colonne non necessarie
        for i in range(1, 4):
            self.tree_view.hideColumn(i)
            
        layout.addWidget(self.tree_view)
        
        # Context Menu
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.show_context_menu)
        
        # Connetti il segnale di doppio click
        self.tree_view.doubleClicked.connect(self.open_file)
        
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
                
    def open_file(self, index):
        path = self.model.filePath(index)
        if os.path.isfile(path):
            # Qui dovresti emettere un segnale per aprire il file nell'editor
            # O chiamare direttamente il metodo dell'IDE per aprire il file
            if hasattr(self.parent(), 'open_file'):
                self.parent().open_file(path)