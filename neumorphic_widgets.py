from PyQt5.QtWidgets import QWidget, QComboBox, QTextEdit
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPainter, QPen, QColor, QLinearGradient

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
        


class NeumorphicComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QComboBox {
                background-color: #2C2D3A;
                border: none;
                border-radius: 10px;
                padding: 5px;
                color: #E0E0E0;
            }
            QComboBox::drop-down {
                width: 30px;
                border: none;
                background: #3D3E4D;
                border-top-right-radius: 10px;
                border-bottom-right-radius: 10px;
            }
        """)

class NeumorphicTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QTextEdit {
                background-color: #1E1F2B;
                border: none;
                
                padding: 10px;
                color: #E0E0E0;
            }
        """)


