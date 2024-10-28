import numpy as np
import pyaudio
import threading
from openwakeword.model import Model
import torch
import whisper
import os


#FIXME - FutureWarning: You are using `torch.load` with `weights_only=False`
#               Refer to : https://github.com/JaidedAI/EasyOCR/issues/1297

class CombinedDetector:
    def __init__(self, rate=16000, chunk_size=1280, silence_threshold=-50, silence_duration=1.2, history_s=0.5, max_buffer_s=300, language = "it", whisper_model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models"), whisper_model_version="base"):
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

        # Initialize Whisper model
        self.whisper_model_dir = whisper_model_dir
        self.whisper_model_version = whisper_model_version
        self.device = "cuda" if torch.cuda.is_available() else "cpu"        
        print(f"Using device: {self.device}")
        self.whisper_model = whisper.load_model(self.whisper_model_version, download_root=self.whisper_model_dir, device=self.device, in_memory=True)

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
            audio_data = audio_data.astype(np.float32) / 32768.0 #Convert audio from int16 to float32 and normalize to float values between -1.0 and +1.0
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
                        self.audio_buffer = [audio_chunk]  # Start buffering with this chunk
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

#TODO 
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
            
            # if self.thread:
            #     self.thread.join()
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
    
    def transcribe_audio(self, audio):
        # Convert audio to float32 in range [-1.0, 1.0]
        audio = audio.astype(np.float32) / 32768.0
        # Perform transcription
        result = self.whisper_model.transcribe(audio, language=self.transcription_language, fp16=self.device == "cuda", task = "translate")
        return result["text"]
