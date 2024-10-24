from PyQt5.QtCore import QPropertyAnimation, Qt, QEasingCurve, QTimer, QRect
from PyQt5.QtGui import QPainter, QRadialGradient, QColor, QPen, QLinearGradient
from PyQt5.QtWidgets import QPushButton
import math
import random

class AIAssistantButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 60)
        self.setStyleSheet("background-color: transparent; border: none;")
        
        self.state = "default"
        self.pulse_animation = QPropertyAnimation(self, b"geometry")
        self.pulse_animation.setDuration(1000)
        self.pulse_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.pulse_animation.setLoopCount(-1)
        
        # Circle animation
        self.circle_animation = QTimer(self)
        self.circle_animation.timeout.connect(self.update_pulse_animation)
        
        self.processing_timer = QTimer(self)
        self.processing_timer.timeout.connect(self.finish_processing)
        
        self.base_color = QColor(255, 165, 0)  # Colore arancione
        self.highlight_color = QColor(255, 255, 0)  # Colore giallo
        
        self.arc_angle = 0
        self.processing_animation_timer = QTimer(self)
        self.processing_animation_timer.timeout.connect(self.update_processing_animation)
        self.radius_multiplier = 0
        
        # Variables for wave animation
        self.wave_phase = 0
        self.wave_speed = 0.18
        self.speaking_animation_timer = QTimer(self)
        self.speaking_animation_timer.timeout.connect(self.update_speaking_animation)
        self.speaking_enabled = True  # Initially disabled
        
        # Wave parameters
        self.wave_amplitude = 5
        self.wave_length = 800
        self.wave_offset = 0  # Offset iniziale dell'onda

        # Start wave animation timer
        self.wave_animation_timer = QTimer(self)
        self.wave_animation_timer.timeout.connect(self.update_wave_animation)
        self.wave_animation_timer.start(10)  # 20 FPS

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        self.draw_background(painter)
        
        if self.state == "default":
            self.draw_default(painter)
        elif self.state == "listening":
            self.draw_listening(painter)
        elif self.state == "processing":
            self.draw_processing(painter)
        elif self.state == "speaking":
            self.draw_speaking(painter)

    def draw_background(self, painter):
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(255, 255, 255, 50))
        gradient.setColorAt(1, QColor(255, 255, 255, 0))
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawRect(self.rect())

    def draw_default(self, painter):
        gradient = QRadialGradient(30, 30, 30)
        gradient.setColorAt(0, self.base_color)
        gradient.setColorAt(1, self.base_color.darker(150))
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(5, 5, 50, 50)

        # Draw Siri icon
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawLine(20, 30, 40, 30)
        painter.drawLine(20, 40, 40, 40)
        painter.drawLine(20, 50, 40, 50)
    
    def draw_listening(self, painter):
        gradient = QRadialGradient(30, 30, 30)
        gradient.setColorAt(0, self.highlight_color)
        gradient.setColorAt(1, self.base_color)
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(5, 5, 50, 50)
        
        # Draw animated circle in slightly transparent white
        pen = QPen(QColor(255, 255, 255, 200), 2)  # Bianco trasparente
        painter.setPen(pen)
        painter.drawEllipse(30 - self.radius_multiplier, 30 - self.radius_multiplier, 
                            2 * self.radius_multiplier, 2 * self.radius_multiplier)

        # Draw microphone icon
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawRoundedRect(25, 25, 10, 20, 5, 5)
        painter.drawLine(30, 45, 30, 55)
        painter.drawLine(25, 55, 35, 55)
    
    def draw_processing(self, painter):
        gradient = QRadialGradient(30, 30, 30)
        gradient.setColorAt(0, self.base_color)
        gradient.setColorAt(1, self.highlight_color)
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(5, 5, 50, 50)
        
        # Draw rotating arc in slightly transparent white
        painter.setPen(QPen(QColor(255, 255, 255, 200), 3))  # Bianco trasparente
        painter.drawArc(10, 10, 40, 40, self.arc_angle * 16, 120 * 16)

        # Draw gear icon
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawEllipse(25, 25, 10, 10)
        for i in range(8):
            angle = i * math.pi / 4
            x1 = int(30 + 10 * math.cos(angle))
            y1 = int(30 + 10 * math.sin(angle))
            x2 = int(30 + 15 * math.cos(angle))
            y2 = int(30 + 15 * math.sin(angle))
            painter.drawLine(x1, y1, x2, y2)
    
    def draw_speaking(self, painter):
        gradient = QRadialGradient(30, 30, 30)
        gradient.setColorAt(0, self.highlight_color)
        gradient.setColorAt(1, self.base_color)
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(5, 5, 50, 50)
        
        if self.speaking_enabled:
            # Draw sound waves in slightly transparent white
            painter.setPen(QPen(QColor(255, 255, 255, 200), 2))  # Bianco trasparente
            for i in range(3):
                # Center the lines vertically within the circle
                offset = int(10 * math.sin(self.wave_phase + i))
                # Adjust the vertical position for centering
                y_position = 30 + (i - 1) * 10  # Aumenta la distanza tra le linee
                painter.drawLine(20 + offset, y_position, 40 + offset, y_position)

        # Draw speaker icon
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawRoundedRect(25, 25, 10, 20, 5, 5)
        painter.drawLine(30, 45, 30, 55)
        painter.drawLine(25, 55, 35, 55)

    def mousePressEvent(self, event):
        if self.state == "default":
            self.start_listening()
        elif self.state == "listening":
            self.start_processing()
        elif self.state == "processing":
            pass
        elif self.state == "speaking":
            self.reset_to_default()
        super().mousePressEvent(event)
    
    def start_listening(self):
        self.state = "listening"
        self.circle_animation.start(50)
        self.update()
    
    def start_processing(self):
        self.state = "processing"
        self.circle_animation.stop()
        self.arc_angle = 0
        self.processing_animation_timer.start(30)
        self.processing_timer.start(3000)
    
    def finish_processing(self):
        self.processing_timer.stop()
        self.processing_animation_timer.stop()
        self.start_speaking()
    
    def start_speaking(self):
        self.state = "speaking"
        self.speaking_animation_timer.start(50)
        self.update()
    
    def reset_to_default(self):
        self.state = "default"
        self.circle_animation.stop()
        self.processing_animation_timer.stop()
        self.speaking_animation_timer.stop()
        self.update()
    
    def update_pulse_animation(self):
        if self.radius_multiplier < 25:
            self.radius_multiplier += 1
        else:
            self.radius_multiplier = 0
        self.update()
    
    def update_processing_animation(self):
        self.arc_angle = (self.arc_angle + 15) % 360
        self.update()

    def update_speaking_animation(self):
        self.wave_phase += self.wave_speed
        self.update()

    def update_wave_animation(self):
        self.wave_offset += 2  # Incrementa l'offset per il movimento dell'onda
        self.update()
        
        
'''
from PyQt5.QtCore import QPropertyAnimation, Qt, QEasingCurve, QTimer, QRect
from PyQt5.QtGui import QPainter, QRadialGradient, QColor, QPen
from PyQt5.QtWidgets import QPushButton
import math
import random

class AIAssistantButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 60)
        self.setStyleSheet("background-color: transparent; border: none;")
        
        self.state = "default"
        self.pulse_animation = QPropertyAnimation(self, b"geometry")
        self.pulse_animation.setDuration(1000)
        self.pulse_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.pulse_animation.setLoopCount(-1)
        
        # Circle animation
        self.circle_animation = QTimer(self)
        self.circle_animation.timeout.connect(self.update_pulse_animation)
        
        self.processing_timer = QTimer(self)
        self.processing_timer.timeout.connect(self.finish_processing)
        
        self.base_color = QColor(255, 165, 0)  # Colore arancione
        self.highlight_color = QColor(255, 255, 0)  # Colore giallo
        
        self.arc_angle = 0
        self.processing_animation_timer = QTimer(self)
        self.processing_animation_timer.timeout.connect(self.update_processing_animation)
        self.radius_multiplier = 0
        
        # Variables for wave animation
        self.wave_phase = 0
        self.wave_speed = 0.18
        self.speaking_animation_timer = QTimer(self)
        self.speaking_animation_timer.timeout.connect(self.update_speaking_animation)
        self.speaking_enabled = True  # Initially disabled
        
        # Wave parameters
        self.wave_amplitude = 5
        self.wave_length = 800
        self.wave_offset = 0  # Offset iniziale dell'onda

        # Start wave animation timer
        self.wave_animation_timer = QTimer(self)
        self.wave_animation_timer.timeout.connect(self.update_wave_animation)
        self.wave_animation_timer.start(10)  # 20 FPS

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        if self.state == "default":
            self.draw_default(painter)
        elif self.state == "listening":
            self.draw_listening(painter)
        elif self.state == "processing":
            self.draw_processing(painter)
        elif self.state == "speaking":
            self.draw_speaking(painter)

        # Draw the wave below the button
        #self.draw_wave(painter)

    def draw_wave(self, painter):
        painter.setPen(QPen(QColor(0, 0, 255, 150), 2))  # Blu trasparente
        for x in range(-self.wave_length, self.width() + self.wave_length, 5):
            # Calcola l'altezza dell'onda usando la funzione seno
            y = int(self.height() + self.wave_amplitude * math.sin((x + self.wave_offset) * self.wave_speed))
            painter.drawPoint(x + self.wave_length, y)

    def draw_default(self, painter):
        gradient = QRadialGradient(30, 30, 30)
        gradient.setColorAt(0, self.base_color)
        gradient.setColorAt(1, self.base_color.darker(150))
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(5, 5, 50, 50)
    
    def draw_listening(self, painter):
        gradient = QRadialGradient(30, 30, 30)
        gradient.setColorAt(0, self.highlight_color)
        gradient.setColorAt(1, self.base_color)
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(5, 5, 50, 50)
        
        # Draw animated circle in slightly transparent white
        pen = QPen(QColor(255, 255, 255, 200), 2)  # Bianco trasparente
        painter.setPen(pen)
        painter.drawEllipse(30 - self.radius_multiplier, 30 - self.radius_multiplier, 
                            2 * self.radius_multiplier, 2 * self.radius_multiplier)
    
    def draw_processing(self, painter):
        gradient = QRadialGradient(30, 30, 30)
        gradient.setColorAt(0, self.base_color)
        gradient.setColorAt(1, self.highlight_color)
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(5, 5, 50, 50)
        
        # Draw rotating arc in slightly transparent white
        painter.setPen(QPen(QColor(255, 255, 255, 200), 3))  # Bianco trasparente
        painter.drawArc(10, 10, 40, 40, self.arc_angle * 16, 120 * 16)
    
    def draw_speaking(self, painter):
        gradient = QRadialGradient(30, 30, 30)
        gradient.setColorAt(0, self.highlight_color)
        gradient.setColorAt(1, self.base_color)
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(5, 5, 50, 50)
        
        if self.speaking_enabled:
            # Draw sound waves in slightly transparent white
            painter.setPen(QPen(QColor(255, 255, 255, 200), 2))  # Bianco trasparente
            for i in range(3):
                # Center the lines vertically within the circle
                offset = int(10 * math.sin(self.wave_phase + i))
                # Adjust the vertical position for centering
                y_position = 30 + (i - 1) * 10  # Aumenta la distanza tra le linee
                painter.drawLine(20 + offset, y_position, 40 + offset, y_position)

    def mousePressEvent(self, event):
        if self.state == "default":
            self.start_listening()
        elif self.state == "listening":
            self.start_processing()
        elif self.state == "processing":
            pass
        elif self.state == "speaking":
            self.reset_to_default()
        super().mousePressEvent(event)
    
    def start_listening(self):
        self.state = "listening"
        self.circle_animation.start(50)
        self.update()
    
    def start_processing(self):
        self.state = "processing"
        self.circle_animation.stop()
        self.arc_angle = 0
        self.processing_animation_timer.start(30)
        self.processing_timer.start(3000)
    
    def finish_processing(self):
        self.processing_timer.stop()
        self.processing_animation_timer.stop()
        self.start_speaking()
    
    def start_speaking(self):
        self.state = "speaking"
        self.speaking_animation_timer.start(50)
        self.update()
    
    def reset_to_default(self):
        self.state = "default"
        self.circle_animation.stop()
        self.processing_animation_timer.stop()
        self.speaking_animation_timer.stop()
        self.update()
    
    def update_pulse_animation(self):
        if self.radius_multiplier < 25:
            self.radius_multiplier += 1
        else:
            self.radius_multiplier = 0
        self.update()
    
    def update_processing_animation(self):
        self.arc_angle = (self.arc_angle + 15) % 360
        self.update()

    def update_speaking_animation(self):
        self.wave_phase += self.wave_speed
        self.update()

    def update_wave_animation(self):
        self.wave_offset += 2  # Incrementa l'offset per il movimento dell'onda
        self.update()'''