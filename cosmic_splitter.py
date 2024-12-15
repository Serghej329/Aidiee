from PyQt5.QtWidgets import QSplitter, QSplitterHandle
from PyQt5.QtCore import Qt, QEvent, QSize

# CustomHandle: A custom splitter handle with hover effects and enforced size
class CustomHandle(QSplitterHandle):
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        # Default style: dark gray background
        self.setStyleSheet("background-color: #424769;")
        self.setMouseTracking(True)  # Enable mouse tracking for hover effects

    def enterEvent(self, event):
        # Change style to light blue when the mouse enters the handle
        self.setStyleSheet("background-color: #A294F9;")
        super().enterEvent(event)

    def leaveEvent(self, event):
        # Revert to default style (dark gray) when the mouse leaves the handle
        self.setStyleSheet("background-color: #424769;")
        super().leaveEvent(event)

    def resizeEvent(self, event):
        # Enforce the handle size to be 2px wide or tall, depending on orientation
        if self.orientation() == Qt.Horizontal:
            # Horizontal handle: set width to 2px, height to match parent
            self.resize(2, self.parent().height())
        else:
            # Vertical handle: set height to 2px, width to match parent
            self.resize(self.parent().width(), 2)
        super().resizeEvent(event)

# CosmicSplitter: A custom QSplitter using CustomHandle for its handles
class CosmicSplitter(QSplitter):
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.setMouseTracking(True)  # Enable mouse tracking for all handles

    def createHandle(self):
        # Override createHandle to use the custom handle (CustomHandle)
        return CustomHandle(self.orientation(), self)