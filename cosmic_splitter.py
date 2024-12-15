from PyQt5.QtWidgets import QSplitter, QSplitterHandle
from PyQt5.QtCore import Qt
from python_highlighter import SyntaxThemes

# CustomHandle: A custom splitter handle with hover effects and enforced size
class CustomHandle(QSplitterHandle):
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        # Initialize themes
        syntax_themes = SyntaxThemes()
        theme = syntax_themes.themes['Tokyo Night']

        # Use colors from the theme
        self.default_color = theme['background']  # Default color (dark gray)
        self.hover_color = theme['highlight']    # Hover color (light blue)

        # Apply the default color
        self.setStyleSheet(f"background-color: {self.default_color};")
        self.setMouseTracking(True)  # Enable mouse tracking for hover effects

    def enterEvent(self, event):
        # Change style to hover color when the mouse enters the handle
        self.setStyleSheet(f"background-color: {self.hover_color};")
        super().enterEvent(event)

    def leaveEvent(self, event):
        # Revert to default style when the mouse leaves the handle
        self.setStyleSheet(f"background-color: {self.default_color};")
        super().leaveEvent(event)

    def resizeEvent(self, event):
        # Enforce the handle size to be 3px wide or tall, depending on orientation
        if self.orientation() == Qt.Horizontal:
            # Horizontal handle: set width to 3px, height to match parent
            self.resize(3, self.parent().height())
        else:
            # Vertical handle: set height to 3px, width to match parent
            self.resize(self.parent().width(), 3)
        super().resizeEvent(event)

# CosmicSplitter: A custom QSplitter using CustomHandle for its handles
class CosmicSplitter(QSplitter):
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.setMouseTracking(True)  # Enable mouse tracking for all handles

    def createHandle(self):
        # Override createHandle to use the custom handle (CustomHandle)
        return CustomHandle(self.orientation(), self)
