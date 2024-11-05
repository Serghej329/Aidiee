import numpy as np
import pyaudio
import threading
from openwakeword.model import Model
import torch
import whisper
import os
import noisereduce as nr
from pydub import AudioSegment
from io import BytesIO

#FIXME - FutureWarning: You are using `torch.load` with `weights_only=False`
#               Refer to : https://github.com/JaidedAI/EasyOCR/issues/1297

class CombinedDetector:
    def __init__(self, rate=16000, chunk_size=1280, silence_threshold=-50, 
                 silence_duration=1.2, history_s=0.5, max_buffer_s=300, 
                 language="it", whisper_model_dir=os.path.join(os.path.dirname(os.path.abspath(__file__)), "models"), 
                 whisper_model_version="base", trim_silence_end=1.0):
        self.rate = rate
        self.chunk_size = chunk_size
        self.silence_threshold = silence_threshold
        self.silence_duration = silence_duration
        self.history_s = history_s
        self.max_buffer_s = max_buffer_s
        self.transcription_language = language
        self.max_buffer_size = int(self.max_buffer_s * self.rate / self.chunk_size)
        self.audio_buffer = []
        self.silent_chunks = 0
        self.voiced_chunks = 0
        self.thread = None
        self.trim_silence_end = trim_silence_end  # seconds of silence to trim from end
        
        # Whisper model initialization
        self.whisper_model_dir = whisper_model_dir
        self.whisper_model_version = whisper_model_version
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")
        self.whisper_model = whisper.load_model(self.whisper_model_version, 
                                              download_root=self.whisper_model_dir, 
                                              device=self.device, 
                                              in_memory=True)
        
        # Get Whisper's maximum input length in seconds
        self.whisper_max_length = 30  # Whisper typically handles 30 seconds segments well
        
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(format=pyaudio.paInt16,
                                    channels=1,
                                    rate=self.rate,
                                    input=True,
                                    frames_per_buffer=self.chunk_size)
        
        self.lock = threading.Lock()
        self.running = False
        self.keyword_detected = threading.Event()
        self.silence_detected = threading.Event()
        
        # Initialize OpenWakeWord model
        self.oww_model = Model(wakeword_models=[os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "alexa_v0.1.onnx")], inference_framework="onnx")    

    
    def get_db(self, audio_data):
        if audio_data.dtype == np.int16:
            #Convert audio from int16 to float32 and normalize to float values between -1.0 and +1.0
            audio_data = audio_data.astype(np.float32) / 32768.0 
        return 20 * np.log10(np.sqrt(np.mean(np.square(audio_data))) + 1e-10)
    
    def is_silent(self, audio_data):
        return self.get_db(audio_data) < self.silence_threshold
        
    def detect_keyword_and_silence(self):
        while self.running:
            try:
                audio_chunk = np.frombuffer(self.stream.read(self.chunk_size), dtype=np.int16)
                if not self.keyword_detected.is_set():
                    prediction = self.oww_model.predict(audio_chunk)
                    for mdl in self.oww_model.prediction_buffer.keys():
                        scores = list(self.oww_model.prediction_buffer[mdl])
                        curr_score = format(scores[-1], '.20f').replace("-", "")
                    if float(curr_score[0:5]) > 0.3:
                        self.keyword_detected.set()
                        self.audio_buffer = [audio_chunk]
                else:
                    self.audio_buffer.append(audio_chunk)
                    
                    if self.is_silent(audio_chunk):
                        self.silent_chunks += 1
                        self.voiced_chunks = 0
                    else:
                        self.silent_chunks = 0
                        self.voiced_chunks += 1
                    
                    if self.silent_chunks > self.silence_duration * self.rate / self.chunk_size:
                        self.silence_detected.set()
                        self.reset_buffer()
            except Exception as e:
                print(f"Error in detect_keyword_and_silence: {e}")
                self.stop()

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.detect_keyword_and_silence)
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(format=pyaudio.paInt16,
                                    channels=1,
                                    rate=self.rate,
                                    input=True,
                                    frames_per_buffer=self.chunk_size)
        self.thread.start()
    
    def stop(self):
        self.running = False
        try:
            self.reset_buffer()
        except Exception as e:
            print(f"Error before stop: {e}")
            
        try:
            self.stream.stop_stream()
            self.stream.close()
            self.audio.terminate()
        except Exception as e:
            print(f"Error during stop: {e}")

    def get_audio_data(self):
        return np.concatenate(self.audio_buffer)
    
    def reset_audio_data(self):
        with self.lock:
            self.audio_buffer = np.zeros((self.max_buffer_size, self.chunk_size), dtype=np.int16)

    def reset_buffer(self):
        self.keyword_detected.clear()
        self.silence_detected.clear()
        self.silent_chunks = 0
        self.voiced_chunks = 0
        self.oww_model.reset()
    def process_audio(self, audio_data):
        """Process audio data with noise reduction and silence trimming."""
        # Convert to float32 if needed
        if audio_data.dtype == np.int16:
            audio_float = audio_data.astype(np.float32) / 32768.0
        else:
            audio_float = audio_data

        # Apply noise reduction
        reduced_noise = nr.reduce_noise(y=audio_float, sr=self.rate)
        
        # Find the end of speech (before last silence)
        if self.trim_silence_end > 0:
            chunk_samples = int(self.rate * 0.1)  # Analysis window size
            chunks = len(reduced_noise) // chunk_samples
            
            # Analyze chunks from end to find last non-silent chunk
            for i in range(chunks - 1, -1, -1):
                chunk = reduced_noise[i * chunk_samples:(i + 1) * chunk_samples]
                if self.get_db(chunk) > self.silence_threshold:
                    # Keep audio up to this point plus a small buffer
                    keep_samples = min(len(reduced_noise),
                                    (i + 1) * chunk_samples + int(self.rate * 0.2))
                    reduced_noise = reduced_noise[:keep_samples]
                    break
        
        return reduced_noise
    def transcribe_audio(self, audio):
        """Transcribe audio with handling for long recordings."""
        # Process audio with noise reduction and silence trimming
        processed_audio = self.process_audio(audio)
        
        # Convert processed audio back to float32 in range [-1.0, 1.0] if needed
        if processed_audio.dtype != np.float32:
            processed_audio = processed_audio.astype(np.float32)
        
        # Calculate duration in seconds
        duration = len(processed_audio) / self.rate
        
        # If audio is longer than whisper_max_length, split and process in chunks
        if duration > self.whisper_max_length:
            chunk_size = int(self.whisper_max_length * self.rate)
            transcriptions = []
            
            for i in range(0, len(processed_audio), chunk_size):
                chunk = processed_audio[i:i + chunk_size]
                result = self.whisper_model.transcribe(
                    chunk,
                    language=self.transcription_language,
                    fp16=self.device == "cuda",
                    #task="translate"
                )
                transcriptions.append(result["text"])
            
            return " ".join(transcriptions)
        else:
            # For shorter audio, process normally
            result = self.whisper_model.transcribe(
                processed_audio,
                language=self.transcription_language,
                fp16=self.device == "cuda",
                #task="translate"
            )
            return result["text"]
