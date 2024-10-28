import math
import pyaudio
import numpy as np
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QLinearGradient, QColor, QPainterPath
from PyQt5.QtWidgets import QWidget

class AnimatedWaveBackground(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.num_points = 300
        self.num_waves = 5
        self.time = 0
        self.target_amplitude = 0
        self.current_amplitude = 0
        self.base_amplitude = 3
        self.volume_history = []
        self.history_length = 30
        self.transition_factor = 1.0

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_wave)
        self.timer.start(16)  # ~60 FPS

        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=pyaudio.paFloat32, channels=1, rate=44100, input=True, frames_per_buffer=1024)

        self.audio_timer = QTimer(self)
        self.audio_timer.timeout.connect(self.capture_audio)
        self.audio_timer.start(20)
        
        self.audio_data = np.zeros(1024, dtype=np.float32)
        self.frequency_amplitudes = [0] * self.num_waves

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Definisci il rettangolo di clipping per limitare il disegno all'interno del contenitore
        painter.setClipRect(self.rect())

        for i in range(self.num_waves):
            wave_path = self.create_wave_path(self.frequency_amplitudes[i], (i + 1) / (self.num_waves + 1))
            
            gradient = QLinearGradient(0, self.height(), 0, 0)
            gradient.setColorAt(0, QColor(0, 51, 102, 100))
            gradient.setColorAt(1, QColor(0, 204, 204, 100))
            
            painter.fillPath(wave_path, gradient)

    def create_wave_path(self, amplitude, vertical_offset):
        path = QPainterPath()
        
        # Inizia dal bordo inferiore sinistro del contenitore
        path.moveTo(0, self.height())

        max_amplitude = self.height() * 0.4
        wave_amplitude = (self.base_amplitude + amplitude * max_amplitude) * self.transition_factor
        
        frequency = 0.01
        phase_offset = self.time * 0.3 * (1 + vertical_offset)

        # Calcola la spaziatura orizzontale basata sulla larghezza effettiva del contenitore
        dx = self.width() / self.num_points

        vertical_spacing = 20
        vertical_position = self.height() * (0.5 + 0.4 * vertical_offset) + vertical_spacing * vertical_offset
        
        # Genera i punti dell'onda usando la larghezza del contenitore
        for i in range(self.num_points + 1):
            x = i * dx  # Usa la spaziatura calcolata
            y = vertical_position + (
                math.sin(phase_offset + i * frequency) * wave_amplitude +
                math.sin(phase_offset * 2 + i * frequency * 2) * wave_amplitude * 0.5 +
                math.sin(phase_offset * 4 + i * frequency * 4) * wave_amplitude * 0.25
            )
            path.lineTo(x, y)

        # Completa il path fino al bordo inferiore destro del contenitore
        path.lineTo(self.width(), self.height())
        path.closeSubpath()
        return path

    def update_wave(self):
        self.time += 0.05
        
        easing_factor = 0.05
        self.current_amplitude += easing_factor * (self.target_amplitude - self.current_amplitude)
        self.current_amplitude = max(0, min(self.current_amplitude, 1))

        self.update()

    def capture_audio(self):
        data = self.stream.read(1024, exception_on_overflow=False)
        self.audio_data = np.frombuffer(data, dtype=np.float32)

        volume = np.abs(self.audio_data).mean()
        
        noise_threshold = 0.002
        self.volume_history.append(volume)
        if len(self.volume_history) > self.history_length:
            self.volume_history.pop(0)

        smoothed_volume = np.mean(self.volume_history)
        self.target_amplitude = max((smoothed_volume - noise_threshold) * 3, 0)

        fft_data = np.fft.fft(self.audio_data)
        freqs = np.fft.fftfreq(len(fft_data), 1.0 / 44100)
        
        freq_bands = np.array_split(np.abs(freqs), self.num_waves)
        for i, band in enumerate(freq_bands):
            mask = (np.abs(freqs) >= band.min()) & (np.abs(freqs) <= band.max())
            target_amplitude = np.abs(fft_data[mask]).mean() * 1.5
            self.frequency_amplitudes[i] += 0.1 * (target_amplitude - self.frequency_amplitudes[i])

    def closeEvent(self, event):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
        super().closeEvent(event)

