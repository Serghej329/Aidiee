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


'''import math
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
        
        self.num_points = 30
        self.time = 0
        self.target_amplitude = 0
        self.current_amplitude = 0
        self.base_amplitude = 10
        self.volume_history = []
        self.history_length = 5
        self.transition_factor = 1.0

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_wave)
        self.timer.start(30)

        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=pyaudio.paFloat32, channels=1, rate=44100, input=True, frames_per_buffer=1024)

        self.audio_timer = QTimer(self)
        self.audio_timer.timeout.connect(self.capture_audio)
        self.audio_timer.start(15)
        
        self.audio_data = np.zeros(1024, dtype=np.float32)
        self.bass_amplitude = 0
        self.high_amplitude = 0

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        wave_gradient = QLinearGradient(0, 0, 0, self.height())
        wave_gradient.setColorAt(0.5, QColor(255, 255, 255, 100))
        wave_gradient.setColorAt(1.0, QColor(132, 90, 191, 50))
        
        path = self.create_wave_path()
        painter.fillPath(path, wave_gradient)

        glow_path = QPainterPath(path)
        glow_gradient = QLinearGradient(0, 0, 0, self.height())
        glow_gradient.setColorAt(0.5, QColor(61, 62, 77, 30))
        glow_gradient.setColorAt(1.0, QColor(132, 90, 191, 20))
        painter.fillPath(glow_path, glow_gradient)

    def create_wave_path(self):
        path = QPainterPath()
        path.moveTo(0, self.height())

        max_amplitude = self.height() * 0.2
        bass_amplitude = (self.base_amplitude + self.bass_amplitude * max_amplitude) * self.transition_factor
        high_amplitude = (self.base_amplitude + self.high_amplitude * max_amplitude) * self.transition_factor
        
        frequency = 0.02
        
        for i in range(self.width() + 1):
            y_bass = self.height() * 0.7 + math.sin(self.time + i * frequency) * bass_amplitude
            y_high = self.height() * 0.7 + math.sin(self.time + i * frequency) * high_amplitude
            
            if i < self.width() / 2:
                path.lineTo(i, y_bass)
            else:
                path.lineTo(i, y_high)

        path.lineTo(self.width(), self.height())
        path.closeSubpath()
        return path

    def update_wave(self):
        self.time += 0.05

        easing_factor = 0.1
        self.current_amplitude += easing_factor * (self.target_amplitude - self.current_amplitude)
        self.current_amplitude = max(0, min(self.current_amplitude, 1))

        if self.target_amplitude == 0:
            self.transition_factor = max(0, self.transition_factor - 0.02)
        else:
            self.transition_factor = min(1, self.transition_factor + 0.05)

        self.update()

    def capture_audio(self):
        data = self.stream.read(1024, exception_on_overflow=False)
        self.audio_data = np.frombuffer(data, dtype=np.float32)

        volume = np.abs(self.audio_data).mean()
        
        noise_threshold = 0.005
        silence_duration = 20

        if volume < noise_threshold:
            self.volume_history.append(0)
        else:
            self.volume_history.append(volume)

        if len(self.volume_history) > self.history_length:
            self.volume_history.pop(0)

        volume_variance = np.var(self.volume_history)
        
        if volume_variance < noise_threshold and len(self.volume_history) >= silence_duration:
            self.target_amplitude = 0
        else:
            smoothed_volume = np.mean(self.volume_history)
            self.target_amplitude = max((smoothed_volume - noise_threshold) * 2, 0)

        # Separazione delle frequenze basse e alte
        fft_data = np.fft.fft(self.audio_data)
        freqs = np.fft.fftfreq(len(fft_data), 1.0 / 44100)
        
        bass_mask = np.abs(freqs) < 200  # Frequenze basse fino a 200 Hz
        high_mask = np.abs(freqs) > 2000  # Frequenze alte sopra 2000 Hz
        
        bass_amplitude = np.abs(fft_data[bass_mask]).mean()
        high_amplitude = np.abs(fft_data[high_mask]).mean()
        
        self.bass_amplitude = bass_amplitude
        self.high_amplitude = high_amplitude

    def closeEvent(self, event):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
        super().closeEvent(event)
'''


'''import math
import pyaudio
import numpy as np
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QLinearGradient, QColor, QPainterPath
from PyQt5.QtWidgets import QWidget

class AnimatedWaveBackground(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Rende il widget trasparente e non interattivo
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)  # Imposta sfondo trasparente
        
        # Inizializza parametri dell'animazione
        self.num_points = 30
        self.time = 0
        self.target_amplitude = 0
        self.current_amplitude = 0
        self.base_amplitude = 10
        self.volume_history = []      # Storico dei volumi catturati
        self.history_length = 5       # Lunghezza dello storico dei volumi
        self.transition_factor = 1.0  # Fattore di transizione dell'animazione

        # Timer per animazione
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_wave)  # Aggiorna l'onda
        self.timer.start(30)  # Aggiorna ogni 30ms

        # Inizializza PyAudio per cattura audio
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=pyaudio.paFloat32, channels=1, rate=44100, input=True, frames_per_buffer=1024)

        # Timer per la cattura dell'audio
        self.audio_timer = QTimer(self)
        self.audio_timer.timeout.connect(self.capture_audio)  # Cattura audio ogni volta che scatta il timer
        self.audio_timer.start(15)  # Ogni 15ms
        
        # Buffer per dati audio
        self.audio_data = np.zeros(1024, dtype=np.float32)

    def paintEvent(self, event):
        # Configura il painter per disegnare il background animato
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)  # Abilita anti-aliasing per disegno più fluido

        # Crea gradiente di colore per l'onda (dal bianco al rosso)
        wave_gradient = QLinearGradient(0, 0, 0, self.height())
        wave_gradient.setColorAt(0.0, QColor(255, 255, 255, 250))  # Bianco semitrasparente
        wave_gradient.setColorAt(1.0, QColor(255, 0, 0, 100))      # Rosso trasparente
        
        # Crea il percorso dell'onda e la riempie con il gradiente
        path = self.create_wave_path()
        painter.fillPath(path, wave_gradient)

        # Aggiunge un effetto glow leggero intorno all'onda
        glow_path = QPainterPath(path)
        glow_gradient = QLinearGradient(0, 0, 0, self.height())
        glow_gradient.setColorAt(0.0, QColor(255, 224, 102, 50))  # Giallo chiaro trasparente
        glow_gradient.setColorAt(1.0, QColor(255, 186, 55, 30))   # Arancione chiaro trasparente
        painter.fillPath(glow_path, glow_gradient)

    def create_wave_path(self):
        # Crea il percorso per il disegno dell'onda
        path = QPainterPath()
        path.moveTo(0, self.height())

        # Imposta l'ampiezza massima per l'onda
        max_amplitude = self.height() * 0.15
        amplitude = (self.base_amplitude + self.current_amplitude * max_amplitude) * self.transition_factor
        
        # Frequenza dell'onda
        frequency = 0.015
        
        # Genera la forma dell'onda riga per riga
        for i in range(self.width() + 1):
            y = self.height() * 0.7 + math.sin(self.time + i * frequency) * amplitude
            path.lineTo(i, y)

        # Chiude il percorso dell'onda
        path.lineTo(self.width(), self.height())
        path.closeSubpath()
        return path

    def update_wave(self):
        # Aggiorna il tempo per l'animazione dell'onda
        self.time += 0.05

        # Rende l'ampiezza corrente più fluida, avvicinandola a quella target
        easing_factor = 0.1
        self.current_amplitude += easing_factor * (self.target_amplitude - self.current_amplitude)
        self.current_amplitude = max(0, min(self.current_amplitude, 1))  # Limita tra 0 e 1

        # Gestisce il fattore di transizione in base all'ampiezza target
        if self.target_amplitude == 0:
            self.transition_factor = max(0, self.transition_factor - 0.02)
        else:
            self.transition_factor = min(1, self.transition_factor + 0.05)

        # Richiede il ridisegno del widget
        self.update()

    def capture_audio(self):
        # Legge i dati audio dal buffer di PyAudio
        data = self.stream.read(1024, exception_on_overflow=False)
        self.audio_data = np.frombuffer(data, dtype=np.float32)

        # Calcola il volume medio del segnale
        volume = np.abs(self.audio_data).mean()
        
        # Soglia di rumore e durata del silenzio per rilevazione
        noise_threshold = 0.005
        silence_duration = 20

        # Aggiunge il volume corrente alla storia del volume
        if volume < noise_threshold:
            self.volume_history.append(0)
        else:
            self.volume_history.append(volume)

        # Mantiene la lunghezza della storia entro un certo limite
        if len(self.volume_history) > self.history_length:
            self.volume_history.pop(0)

        # Calcola la varianza del volume per rilevare silenzio prolungato
        volume_variance = np.var(self.volume_history)
        
        # Aggiorna l'ampiezza target in base alla varianza del volume
        if volume_variance < noise_threshold and len(self.volume_history) >= silence_duration:
            self.target_amplitude = 0  # Riduce l'ampiezza se il rumore è basso
        else:
            # Calcola il volume smussato e imposta l'ampiezza target
            smoothed_volume = np.mean(self.volume_history)
            self.target_amplitude = max((smoothed_volume - noise_threshold) * 2, 0)

    def closeEvent(self, event):
        # Ferma e chiude lo stream audio e termina PyAudio
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
        super().closeEvent(event)
        
        # Debug opzionale per stampa dei valori catturati
        # print(f"Volume: {volume:.4f}, Smoothed Volume: {smoothed_volume:.4f}, Target Amplitude: {self.target_amplitude:.4f}, Current Amplitude: {self.current_amplitude:.4f}")
'''