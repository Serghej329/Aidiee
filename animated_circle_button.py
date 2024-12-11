from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import (QTimer, QPropertyAnimation, QEasingCurve,
                         QPointF, pyqtProperty, QParallelAnimationGroup,
                         Qt, QSequentialAnimationGroup)
from PyQt5.QtGui import QPainter, QColor, QRadialGradient

class SimpleVoiceButton(QWidget):
    def __init__(self, parent=None, ide_instance=None):
        super().__init__(parent)
        self._scale = 1.0
        self._rotation = 0.0
        self._opacity = 1.0
        self.is_active = False
        self.ide_instance = ide_instance

        # Palette colori arancione-giallo
        self.primary_color = QColor(255, 140, 0)    # Arancione intenso
        self.secondary_color = QColor(255, 196, 0)  # Arancione-giallo
        self.accent_color = QColor(255, 215, 0)     # Giallo oro

        # Setup animazioni
        self.setup_animations()

        # Dimensioni
        self.setMinimumSize(100, 100)
        self.setMaximumSize(150, 150)

    def setup_animations(self):
        self.animation_group = QParallelAnimationGroup()

        # Animazione scala con easing curve più fluida
        self.scale_animation = QPropertyAnimation(self, b"scale")
        self.scale_animation.setEasingCurve(QEasingCurve.InOutSine)

        # Animazione rotazione con easing curve personalizzata
        self.rotation_animation = QPropertyAnimation(self, b"rotation")
        self.rotation_animation.setEasingCurve(QEasingCurve.InOutQuad)

        # Nuova animazione per l'opacità
        self.opacity_animation = QPropertyAnimation(self, b"opacity")
        self.opacity_animation.setEasingCurve(QEasingCurve.InOutCubic)

        self.animation_group.addAnimation(self.scale_animation)
        self.animation_group.addAnimation(self.rotation_animation)
        self.animation_group.addAnimation(self.opacity_animation)

        # Avvia l'animazione base
        self.start_idle_animation()

    # Properties
    scale = pyqtProperty(float, lambda self: self._scale,
                        lambda self, v: setattr(self, '_scale', v) or self.update())

    rotation = pyqtProperty(float, lambda self: self._rotation,
                          lambda self, v: setattr(self, '_rotation', v) or self.update())

    opacity = pyqtProperty(float, lambda self: self._opacity,
                          lambda self, v: setattr(self, '_opacity', v) or self.update())

    def create_neon_gradient(self, center, radius, color, opacity_factor=1.0):
        gradient = QRadialGradient(center, radius)

        # Colore centrale intenso con sfumatura migliorata
        center_color = QColor(color)
        center_color.setAlpha(int(255 * opacity_factor))

        # Colore intermedio per transizione più morbida
        mid_color = QColor(color)
        mid_color.setAlpha(int(180 * opacity_factor))

        # Bagliore esterno
        outer_color = QColor(color)
        outer_color.setAlpha(0)

        # Più punti di controllo per una sfumatura più fluida
        gradient.setColorAt(0, center_color)
        gradient.setColorAt(0.3, center_color)
        gradient.setColorAt(0.5, mid_color)
        gradient.setColorAt(0.7, QColor(color.red(),
                                      color.green(),
                                      color.blue(),
                                      int(100 * opacity_factor)))
        gradient.setColorAt(0.9, QColor(color.red(),
                                      color.green(),
                                      color.blue(),
                                      int(50 * opacity_factor)))
        gradient.setColorAt(1, outer_color)

        return gradient

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        center = QPointF(self.width()/2, self.height()/2)
        base_radius = min(self.width(), self.height()) / 3

        # Applica rotazione con transizione fluida
        painter.translate(center)
        painter.rotate(self._rotation)
        painter.translate(-center)

        # Disegna cerchi concentrici con effetto neon migliorato
        colors = [self.primary_color, self.secondary_color, self.accent_color]
        for i in range(3):
            radius = base_radius * (0.8 - i * 0.15) * self._scale
            gradient = self.create_neon_gradient(center, radius, colors[i], self._opacity)
            painter.setBrush(gradient)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(center, radius, radius)

    def start_idle_animation(self):
        self.animation_group.stop()

        # Animazione scala più fluida
        self.scale_animation.setStartValue(1.0)
        self.scale_animation.setEndValue(1.12)
        self.scale_animation.setDuration(2000)
        self.scale_animation.setLoopCount(-1)

        # Rotazione più fluida
        self.rotation_animation.setStartValue(0)
        self.rotation_animation.setEndValue(360)
        self.rotation_animation.setDuration(12000)
        self.rotation_animation.setLoopCount(-1)

        # Animazione opacità pulsante
        self.opacity_animation.setStartValue(0.8)
        self.opacity_animation.setEndValue(1.0)
        self.opacity_animation.setDuration(1500)
        self.opacity_animation.setLoopCount(-1)

        self.animation_group.start()

    def start_active_animation(self):
        self.animation_group.stop()

        # Animazione scala più intensa ma fluida
        self.scale_animation.setStartValue(1.1)
        self.scale_animation.setEndValue(1.25)
        self.scale_animation.setDuration(1000)
        self.scale_animation.setLoopCount(-1)

        # Rotazione più veloce ma fluida
        self.rotation_animation.setStartValue(0)
        self.rotation_animation.setEndValue(360)
        self.rotation_animation.setDuration(6000)
        self.rotation_animation.setLoopCount(-1)

        # Animazione opacità più intensa
        self.opacity_animation.setStartValue(0.9)
        self.opacity_animation.setEndValue(1.0)
        self.opacity_animation.setDuration(800)
        self.opacity_animation.setLoopCount(-1)

        self.animation_group.start()

    def mousePressEvent(self, event):
        self.is_active = not self.is_active
        if self.is_active:
            self.start_active_animation()
            if self.ide_instance:
                self.ide_instance.start_detector()
        else:
            self.start_idle_animation()
            if self.ide_instance:
                self.ide_instance.stop_detector()
