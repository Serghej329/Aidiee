import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QTabWidget, 
                           QPushButton, QHBoxLayout, QMessageBox)
from PyQt5.QtCore import Qt
from terminal_module import Terminal

class TabbedTerminal(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Create header with new tab button
        header = QHBoxLayout()
        
        # Add new tab button
        new_tab_btn = QPushButton("+")
        new_tab_btn.setFixedSize(24, 24)
        new_tab_btn.clicked.connect(self.add_new_tab)
        new_tab_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #D1D5DB;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #374151;
                border-radius: 12px;
            }
        """)
        
        # Add tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.setMovable(True)
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
            }
            QTabBar::tab {
                background-color: #1E1F2A;
                color: #D1D5DB;
                padding: 8px 12px;
                margin-right: 2px;
                border: 1px solid #374151;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #2D2E3B;
            }
            QTabBar::tab:hover {
                background-color: #374151;
            }
            QTabBar::close-button {
                image: url(path_to_close_icon.png);
            }
        """)
        
        header.addStretch()
        header.addWidget(new_tab_btn)
        
        layout.addLayout(header)
        layout.addWidget(self.tab_widget)
        
        self.setLayout(layout)
        
        # Create initial tab
        self.add_new_tab()
        
    def add_new_tab(self):
        """Add a new terminal tab"""
        new_terminal = Terminal()
        index = self.tab_widget.addTab(new_terminal, f"Terminal {self.tab_widget.count() + 1}")
        self.tab_widget.setCurrentIndex(index)
        new_terminal.output_received.connect(lambda text, type: self.update_tab_title(index, text))
        
    def close_tab(self, index):
        """Close the specified tab"""
        if self.tab_widget.count() > 1:
            terminal = self.tab_widget.widget(index)
            terminal.terminal_parser.stop()  # Clean up terminal resources
            self.tab_widget.removeTab(index)
        else:
            QMessageBox.warning(self, "Warning", "Cannot close the last terminal tab")
            
    def update_tab_title(self, index, command_text):
        """Update tab title based on last command"""
        if command_text and isinstance(command_text, str):
            # Extract command name for the title
            command_parts = command_text.strip().split()
            if command_parts:
                title = command_parts[0][:10]  # Truncate to first 10 chars
                self.tab_widget.setTabText(index, title)
    
    def closeEvent(self, event):
        """Clean up all terminals when closing"""
        for i in range(self.tab_widget.count()):
            terminal = self.tab_widget.widget(i)
            terminal.terminal_parser.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    terminal = TabbedTerminal()
    terminal.resize(800, 600)
    terminal.show()
    sys.exit(app.exec_())