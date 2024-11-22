import os
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMenuBar, QWidget, QMenu, QAction, QLabel
from PyQt5.QtGui import QIcon, QPixmap
from qframelesswindow import StandardTitleBar

class CustomTitleBar(StandardTitleBar):
    def __init__(self, parent=None, ide_instance=None):
        super().__init__(parent)
        self.ide_instance = ide_instance
        self.setFixedHeight(40)
        self.create_menus()
        
        # self.ide_instance.setStyleSheet("background: #3D3E4D;")
        
        # Menu Bar
        self.menuBar = QMenuBar(self)
        self.apply_styles()

    def create_menus(self):
        # Logo
        logo_label = QLabel(self)
        logo_pixmap = QPixmap('./img/logo.svg')
        logo_label.setPixmap(logo_pixmap.scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        
        # Create and setup menubar
        self.menuBar = QMenuBar(self.ide_instance.titleBar)
        
        file_menu = self.menuBar.addMenu("File")
        new_file_action = file_menu.addAction("New File")
        open_project = file_menu.addAction("Open Project")
        open_project.triggered.connect(lambda: self.ide_instance.project_manager.open_project(self))

        file_menu.addAction("Save")
        file_menu.addSeparator()
        file_menu.addAction("Exit")

        edit_menu = self.menuBar.addMenu("Edit")
        edit_menu.addAction("Undo")
        edit_menu.addAction("Redo")
        edit_menu.addSeparator()
        edit_menu.addAction("Cut")
        edit_menu.addAction("Copy")
        edit_menu.addAction("Paste")

        view_menu = self.menuBar.addMenu("View")
        editor_template_menu = view_menu.addMenu("Editor Template")

        styles = ["monokai", "default", "friendly", "fruity", "manni", "paraiso-dark", "solarized-dark"]
        for style_name in styles:
            style_action = QAction(style_name, self)
            style_action.triggered.connect(lambda checked, s=style_name: self.ide_instance.change_style(s))
            editor_template_menu.addAction(style_action)

        dock_widget_action = QAction("Toggle Dock Widget", self)
        dock_widget_action.triggered.connect(lambda: self.ide_instance.voice_assistant_dock.toggle_visibility())
        view_menu.addAction(dock_widget_action)

        section_menu = self.menuBar.addMenu("Section")
        section_menu.addAction("Add Section")
        section_menu.addAction("Remove Section")

        go_menu = self.menuBar.addMenu("Go")
        go_menu.addAction("Go to Line")
        go_menu.addAction("Go to Definition")

        run_menu = self.menuBar.addMenu("Run")
        run_menu.addAction("Run Code")
        run_menu.addAction("Debug Code")

        terminal_menu = self.menuBar.addMenu("Terminal")
        terminal_menu.addAction("New Terminal")
        terminal_menu.addAction("Close Terminal")

        assistant_menu = self.menuBar.addMenu("Aidee Assistant")
        assistant_start = assistant_menu.addAction("Start")
        assistant_stop = assistant_menu.addAction("Stop")
        assistant_start.triggered.connect(self.ide_instance.start_detector)
        assistant_stop.triggered.connect(self.ide_instance.stop_detector)

        help_menu = self.menuBar.addMenu("Help")
        help_menu.addAction("Documentation")
        help_menu.addAction("About")
        
        # Add logo and menubar to titlebar layout
        self.ide_instance.titleBar.layout().insertWidget(0, logo_label, alignment=Qt.AlignLeft)
        self.ide_instance.titleBar.layout().insertWidget(1, self.menuBar, 1, Qt.AlignCenter)  # Center the menu bar
        self.ide_instance.titleBar.layout().insertStretch(1, 1)
        self.ide_instance.setMenuWidget(self.ide_instance.titleBar)

        self.ide_instance.titleBar.minBtn.setHoverColor(Qt.white)
        self.ide_instance.titleBar.minBtn.setPressedColor(Qt.white)
        self.ide_instance.titleBar.maxBtn.setHoverColor(Qt.white)
        self.ide_instance.titleBar.maxBtn.setPressedColor(Qt.white)
    def apply_styles(self):
        # Dark theme colors
        self.dark_palette = {
            'background': '#2b2b2b',
            'foreground': '#ffffff',
            'accent': '#3d3d3d',
            'highlight': '#323232',
            'button_hover': '#404040'
        }
        
        self.ide_instance.titleBar.setStyleSheet(f"""
            /* Title Bar */
            #titleBar {{
                background-color: {self.dark_palette['background']};
            }}
            
            /* Menu Bar */
            QMenuBar {{
                background-color: {self.dark_palette['background']};
                color: {self.dark_palette['foreground']};
                padding: 5px 0;
                font-weight: bold;
            }}
            
            QMenuBar::item {{
                background-color: transparent;
                padding: 5px 10px;
                border-radius: 5px;
            }}
            
            QMenuBar::item:selected {{
                background-color: {self.dark_palette['highlight']};
            }}
            
            /* Menu */
            QMenu {{
                background-color: {self.dark_palette['background']};
                color: {self.dark_palette['foreground']};
                border: 1px solid {self.dark_palette['accent']};
            }}
            
            QMenu::item {{
                padding: 5px 30px 5px 20px;
            }}
            
            QMenu::item:selected {{
                background-color: {self.dark_palette['highlight']};
            }}
            
            /* Title Bar Buttons */
            #minimizeButton, #maximizeButton, #closeButton {{
                color: {self.dark_palette['foreground']};
                background-color: transparent;
                border: none;
                width: 40px;
                height: 40px;
            }}
            
            #minimizeButton:hover, #maximizeButton:hover {{
                background-color: {self.dark_palette['button_hover']};
            }}
            
            #closeButton:hover {{
                background-color: #e81123;
            }}
        """)