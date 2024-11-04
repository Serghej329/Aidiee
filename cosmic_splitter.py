from PyQt5.QtWidgets import QSplitter, QGraphicsDropShadowEffect
from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, QPoint, QByteArray
from PyQt5.QtGui import QColor

class CosmicSplitter(QSplitter):
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.setup_style()
        self.setup_glow()
        self.setup_animations()
        
    def setup_style(self):
        self.setStyleSheet("""
            QSplitter::handle {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0,
                                          stop:0 #2d1b4f,
                                          stop:0.45 #1a0f2e,
                                          stop:0.55 #0b0519,
                                          stop:1 #2d1b4f);
                width: 4px;
                margin: 1px;
                border-radius: 2px;
            }
        """)
        
    def setup_glow(self):
        # Creiamo l'effetto glow base
        self.glow_effect = QGraphicsDropShadowEffect()
        self.glow_effect.setBlurRadius(10)
        self.glow_effect.setColor(QColor(101, 31, 255, 0))  # Viola con alpha 0
        self.glow_effect.setOffset(0, 0)
        
        # Applichiamo l'effetto all'handle
        for i in range(self.count() - 1):
            handle = self.handle(i)
            handle.setGraphicsEffect(self.glow_effect)
            
    def setup_animations(self):
        # Animazione del glow
        self.glow_animation = QPropertyAnimation(self.glow_effect, QByteArray(b"color"))
        self.glow_animation.setDuration(1500)
        self.glow_animation.setLoopCount(-1)  # Loop infinito
        
        # Creiamo i keyframes per l'animazione del glow
        self.glow_animation.setKeyValueAt(0, QColor(101, 31, 255, 0))    # Viola spento
        self.glow_animation.setKeyValueAt(0.5, QColor(41, 121, 255, 180))  # Blu brillante
        self.glow_animation.setKeyValueAt(1, QColor(101, 31, 255, 0))    # Torna viola spento
        
        # Curva di easing per un movimento più fluido
        self.glow_animation.setEasingCurve(QEasingCurve.InOutQuad)
        
    def enterEvent(self, event):
        # Avvia l'animazione quando il mouse entra nell'area dello splitter
        self.glow_animation.start()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        # Ferma l'animazione quando il mouse esce
        self.glow_animation.stop()
        self.glow_effect.setColor(QColor(101, 31, 255, 0))
        super().leaveEvent(event)
