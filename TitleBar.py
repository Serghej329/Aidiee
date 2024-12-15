import os,sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMenuBar, QWidget, QMenu, QAction, QLabel
from PyQt5.QtGui import QIcon, QPixmap
from qframelesswindow import StandardTitleBar
from python_highlighter import SyntaxThemes 
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
        default_path = os.path.dirname(__file__)
        print(f"THE DEFAULT PATH IS : {default_path}")
        # Logo
        logo_label = QLabel(self)
        logo_pixmap = QPixmap(f"{default_path}/icons/logo_new.ico")
        logo_label.setPixmap(logo_pixmap.scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        
        # Create and setup menubar
        self.menuBar = QMenuBar(self.ide_instance.titleBar)
        
        # File Menu
        file_menu = self.menuBar.addMenu(QIcon(f"{default_path}/icons/file-menu.svg"), "")
        new_file_action = file_menu.addAction(QIcon(f"{default_path}/icons/new-file.svg"), "New File")
        open_project = file_menu.addAction(QIcon(f"{default_path}/icons/open-project.svg"), "Open Project")
        open_project.triggered.connect(lambda: self.ide_instance.project_manager.open_project(self))
        file_menu.addAction(QIcon(f"{default_path}/icons/save.svg"), "Save")
        file_menu.addSeparator()
        file_menu.addAction("Exit")

        # Edit Menu
        edit_menu = self.menuBar.addMenu(QIcon(f"{default_path}/icons/edit-menu.svg"), "")
        edit_menu.addAction(QIcon(f"{default_path}/icons/undo.svg"), "Undo")
        edit_menu.addAction(QIcon(f"{default_path}/icons/redo.svg"), "Redo")
        edit_menu.addSeparator()
        edit_menu.addAction(QIcon(f"{default_path}/icons/cut.svg"), "Cut")
        edit_menu.addAction(QIcon(f"{default_path}/icons/copy.svg"), "Copy")
        edit_menu.addAction(QIcon(f"{default_path}/icons/paste.svg"), "Paste")

        # View Menu
        view_menu = self.menuBar.addMenu(QIcon(f"{default_path}/icons/view-menu.svg"), "")
        editor_template_menu = view_menu.addMenu("Editor Template")

        styles = ["monokai", "default", "friendly", "fruity", "manni", "paraiso-dark", "solarized-dark"]
        for style_name in styles:
            style_action = QAction(style_name, self)
            style_action.triggered.connect(lambda checked, s=style_name: self.ide_instance.change_style(s))
            editor_template_menu.addAction(style_action)

        dock_widget_action = QAction("Toggle Dock Widget", self)
        dock_widget_action.triggered.connect(lambda: self.ide_instance.voice_assistant_dock.toggle_visibility())
        view_menu.addAction(dock_widget_action)

        # Section Menu
        section_menu = self.menuBar.addMenu(QIcon(f"{default_path}/icons/section-menu.svg"), "")
        section_menu.addAction("Add Section")
        section_menu.addAction("Remove Section")

        # Go Menu
        go_menu = self.menuBar.addMenu(QIcon(f"{default_path}/icons/go-menu.svg"), "")
        go_menu.addAction("Go to Line")
        go_menu.addAction("Go to Definition")

        # Run Menu
        run_menu = self.menuBar.addMenu(QIcon(f"{default_path}/icons/run-menu.svg"), "")
        run_menu.addAction(QIcon(f"{default_path}/icons/run-menu.svg"), "Run Code")
        run_menu.addAction(QIcon(f"{default_path}/icons/run-menu.svg"), "Debug Code")

        # Terminal Menu
        terminal_menu = self.menuBar.addMenu(QIcon(f"{default_path}/icons/terminal-menu.svg"), "")
        terminal_menu.addAction("New Terminal")
        terminal_menu.addAction("Close Terminal")

        # Assistant Menu
        assistant_menu = self.menuBar.addMenu(QIcon(f"{default_path}/icons/assistant-menu.svg"), "")
        assistant_start = assistant_menu.addAction(QIcon(f"{default_path}/icons/start.svg"), "Start Voice detector")
        assistant_stop = assistant_menu.addAction(QIcon(f"{default_path}/icons/stop.svg"), "Stop Voice detector")
        assistant_start.triggered.connect(self.ide_instance.start_detector)
        assistant_stop.triggered.connect(self.ide_instance.stop_detector)

        # Help Menu
        help_menu = self.menuBar.addMenu(QIcon(f"{default_path}/icons/help-menu.svg"), "")
        help_menu.addAction("Documentation")
        help_menu.addAction("About")
        
        # Add logo and menubar to titlebar layout
        self.ide_instance.titleBar.layout().insertWidget(0, logo_label, alignment=Qt.AlignLeft)
        self.ide_instance.titleBar.layout().insertWidget(1, self.menuBar, 1, Qt.AlignCenter)  # Center the menu bar
        self.ide_instance.titleBar.layout().insertStretch(1, 1)
        self.ide_instance.setMenuWidget(self.ide_instance.titleBar)



    def apply_styles(self):
        # Setup Theme
        self.syntax_themes = SyntaxThemes()
        self.current_theme = self.syntax_themes.themes['Tokyo Night']
        background = self.current_theme['main_background']
        foreground = self.current_theme['main_foreground']
        selected_background = self.current_theme['description_background']
        selected_foreground = self.current_theme['description_foreground'] 
        # Set Windows Button Colors
        self.ide_instance.titleBar.minBtn.setNormalColor(foreground)
        self.ide_instance.titleBar.minBtn.setHoverColor(Qt.white)
        self.ide_instance.titleBar.minBtn.setPressedColor(Qt.white)
        self.ide_instance.titleBar.maxBtn.setHoverColor(Qt.white)
        self.ide_instance.titleBar.maxBtn.setNormalColor(foreground)
        self.ide_instance.titleBar.closeBtn.setNormalColor(foreground)
        # Set titlebar theme
        self.ide_instance.titleBar.setStyleSheet(f"""

            /* Title Bar */
            #titleBar {{
                background-color: {background};
            }}
            
            /* Menu Bar */
            QMenuBar {{
                background-color: {background};
                color: {foreground};
                padding: 5px 0;
                font-weight: bold;
                
            }}
            
            QMenuBar::item {{
                background-color: transparent;
                padding: 5px 10px;
                border-radius: 5px;
            }}
            
            QMenuBar::item:selected {{
                background-color: {selected_background};
            }}
            
            /* Menu */
            QMenu {{
                background-color: {background};
                color: {foreground};
                border: 1px solid {foreground};
            }}
            
            QMenu::item {{
                padding: 5px 30px 5px 20px;
            }}
            
            QMenu::item:selected {{
                background-color: {background};
            }}
            
            /* Title Bar Buttons */
            #minimizeButton, #maximizeButton, #closeButton {{
                color: {foreground};
                background-color: transparent;
                border: none;
                width: 40px;
                height: 40px;
            }}
            
            #minimizeButton:hover, #maximizeButton:hover {{
                background-color: {selected_background};
            }}
            
            #closeButton:hover {{
                background-color: #e81123;
            }}
        """)