import math
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import (QTimer, QPropertyAnimation, QEasingCurve, 
                         QPoint, pyqtProperty, QPointF, Qt)
from PyQt5.QtGui import (QPainter, QColor, QRadialGradient, 
                        QLinearGradient)

class AnimatedCircleButton(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.state = "idle"  # Stato iniziale del pulsante
        self._scale = 1.0  # Scala del pulsante
        self._pulse = 0.0  # Per l'effetto pulsante
        
        # Colori principali
        self.primary_color = QColor(255, 140, 0)  # Arancione
        self.secondary_color = QColor(255, 215, 0)  # Giallo oro
        
        # Setup animazioni
        self.setup_animations()
        
        # Timer per la transizione thinking -> speaking
        self.state_timer = QTimer()
        self.state_timer.setSingleShot(True)
        self.state_timer.timeout.connect(self.transition_to_speaking)
        
        # Impostazione delle dimensioni minime e massime
        self.setMinimumSize(40, 40)  # Dimensioni minime
        self.setMaximumSize(80, 80)  # Dimensioni massime

    def setup_animations(self):
        # Animazione principale della scala
        self.scale_animation = QPropertyAnimation(self, b"scale")
        self.scale_animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        # Animazione dell'effetto pulsante
        self.pulse_animation = QPropertyAnimation(self, b"pulse")
        self.pulse_animation.setDuration(1500)
        self.pulse_animation.setStartValue(0.0)
        self.pulse_animation.setEndValue(1.0)
        self.pulse_animation.setLoopCount(-1)
        self.pulse_animation.setEasingCurve(QEasingCurve.InOutSine)

    # Property per la scala
    def get_scale(self):
        return self._scale
        
    def set_scale(self, value):
        self._scale = value
        self.update()  # Aggiorna la visualizzazione
        
    scale = pyqtProperty(float, get_scale, set_scale)

    # Property per l'effetto pulsante
    def get_pulse(self):
        return self._pulse
        
    def set_pulse(self, value):
        self._pulse = value
        self.update()  # Aggiorna la visualizzazione
        
    pulse = pyqtProperty(float, get_pulse, set_pulse)

    def create_gradient(self, center, radius, start_color, end_color, pulse_factor=0):
        # Crea un gradiente radiale
        gradient = QRadialGradient(center, radius)
        gradient.setColorAt(0, start_color)
        mid_color = QColor(
            int((start_color.red() + end_color.red()) / 2),
            int((start_color.green() + end_color.green()) / 2),
            int((start_color.blue() + end_color.blue()) / 2),
            int((start_color.alpha() + end_color.alpha()) / 2)
        )
        gradient.setColorAt(0.5 + pulse_factor * 0.1, mid_color)
        gradient.setColorAt(1, end_color)
        
        return gradient

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)  # Abilita l'anti-aliasing
        
        center = QPointF(self.width() / 2, self.height() / 2)
        base_radius = min(self.width(), self.height()) / 2

        # Disegna i cerchi concentrici per tutti gli stati
        sizes = [50, 35, 25]  # Dimensioni dei cerchi concentrici
        opacities = [80, 120, 160]

        for i, (size, opacity) in enumerate(zip(sizes, opacities)):
            radius = size / 2
            pulse_offset = abs(math.sin(self._pulse * math.pi + i * math.pi / 3)) * 0.2
            
            # Colore esterno più trasparente
            outer_color = QColor(self.primary_color)
            outer_color.setAlpha(int(opacity * (1 - pulse_offset)))
            
            # Colore interno più vivido
            inner_color = QColor(self.secondary_color)
            inner_color.setAlpha(int(opacity * (1 + pulse_offset)))
            
            gradient = self.create_gradient(center, radius, inner_color, outer_color, pulse_offset)
            painter.setBrush(gradient)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(center, radius * (1 + pulse_offset), radius * (1 + pulse_offset))

        # Disegna il cerchio principale in base allo stato
        if self.state in ["listening", "speaking", "idle"]:
            scaled_radius = min(self.width(), self.height()) / 2 * self._scale
            
            # Gradiente principale
            main_gradient = QLinearGradient(
                QPointF(center.x() - scaled_radius, center.y() - scaled_radius),
                QPointF(center.x() + scaled_radius, center.y() + scaled_radius)
            )
            main_gradient.setColorAt(0, self.primary_color)
            main_gradient.setColorAt(1, self.secondary_color)
            
            # Disegna il cerchio principale
            painter.setBrush(main_gradient)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(center, scaled_radius, scaled_radius)

    def start_animation(self, state):
        self.scale_animation.stop()
        self.pulse_animation.stop()
        
        if state == "listening":
            self.scale_animation.setStartValue(1.0)
            self.scale_animation.setEndValue(1.1)
            self.scale_animation.setDuration(1500)
            self.scale_animation.setLoopCount(-1)
            self.pulse_animation.start()
            self.scale_animation.start()
            
        elif state == "speaking":
            self.scale_animation.setStartValue(1.0)
            self.scale_animation.setEndValue(1.1)
            self.scale_animation.setDuration(800)
            self.scale_animation.setLoopCount(-1)
            self.pulse_animation.setDuration(1000)
            self.pulse_animation.start()
            self.scale_animation.start()
            
        elif state == "thinking":
            self.scale_animation.stop()
            self._scale = 1.0
            self.pulse_animation.setDuration(2000)
            self.pulse_animation.start()
            
        elif state == "idle":
            self._scale = 1.0
            self.pulse_animation.stop()
            self.update()  # Aggiorna la visualizzazione
    
    def transition_to_speaking(self):
        self.state = "speaking"
        self.start_animation("speaking")
    
    def mousePressEvent(self, event):
        if self.state == "idle":
            self.state = "listening"
            self.start_animation("listening")
            
        elif self.state == "listening":
            self.state = "thinking"
            self.start_animation("thinking")
            self.state_timer.start(4000)  # Attende 4 secondi prima di passare a speaking
            
        elif self.state == "speaking":
            self.state = "idle"
            self.start_animation("idle")
