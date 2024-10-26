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
    def __init__(self, rate=16000, chunk_size=1280, silence_threshold=-50, silence_duration=1.2, history_s=0.5, max_buffer_s=300, language = "it", whisper_model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models"), whisper_model_version="medium"):
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

    def start(self):
        self.running = True     #thread running state, change to false to stop execution of the main loop
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
        if self.thread:
            self.thread.join()
        self.reset_buffer()
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
        result = self.whisper_model.transcribe(audio, language=self.transcription_language, fp16=self.device == "cuda")
        return result["text"]

'''
import asyncio
import queue
import speech_recognition as sr
import whisper
import numpy as np
import os
import tempfile
from pydub import AudioSegment
import time
import torch

class VoiceDetector:
    def __init__(self, activation_phrase, whisper_model_dir, whisper_model_version="medium", silence_duration=1, silence_threshold=-50, language="en-US"):
        self.activation_phrase = activation_phrase.lower()
        self.language = language  # Language for Google recognizer
        self.recognizer = sr.Recognizer()
        
        # Determine the device to use (GPU if available, otherwise CPU)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")  # Print the device being used
        self.whisper_model = whisper.load_model(whisper_model_version, download_root=whisper_model_dir, device=self.device, in_memory=True)
        
        self.silence_duration = silence_duration  # in seconds
        self.silence_threshold = silence_threshold  # in dB
        self.transcription_queue = queue.Queue()  # Queue for transcribed text
        self.state_queue = queue.Queue()  # Queue for voice detection state

    async def listen_for_activation(self):
        while True:
            try:
                with sr.Microphone() as source:
                    print("Listening for activation phrase...")
                    self.recognizer.adjust_for_ambient_noise(source)
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                    try:
                        text = self.recognizer.recognize_google(audio, language=self.language).lower() # TO-DO
                        print(f"Heard: {text}")
                        if self.activation_phrase in text:
                            print(f"Activation phrase detected: {text}")
                            self.state_queue.put("active")
                            return True
                    except sr.UnknownValueError:
                        pass  # Speech was unintelligible
            except sr.WaitTimeoutError:
                continue
            except Exception as e:
                print(f"Error in listen_for_activation: {e}")

    async def transcribe_audio(self, audio):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            temp_audio.write(audio.get_wav_data())
            temp_audio_path = temp_audio.name
            print(f"ECCOLOOOO:{temp_audio_path}")
        try:
            result = self.whisper_model.transcribe(temp_audio_path, language=self.language[:2], fp16=self.device == "cuda")  # Use fp16 for GPU
            return result["text"]
        finally:
            os.unlink(temp_audio_path)

    def is_silent(self, audio_segment):
        return audio_segment.dBFS < self.silence_threshold

    async def transcribe_speech(self):
        print(f"Transcribing... (Will stop after {self.silence_duration} seconds of silence)")
        silence_start = None
        
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            while True:
                try:
                    audio = self.recognizer.listen(source, timeout=0.1, phrase_time_limit=10)  # Increased timeout for faster checks
                    audio_segment = AudioSegment(
                        data=audio.get_raw_data(),
                        sample_width=audio.sample_width,
                        frame_rate=audio.sample_rate,
                        channels=1
                    )

                    # Check for silence every 0.1 seconds
                    if self.is_silent(audio_segment):
                        if silence_start is None:
                            silence_start = time.time()
                        elif time.time() - silence_start >= self.silence_duration:
                            print(f"Detected {self.silence_duration} seconds of silence. Stopping transcription.")
                            self.state_queue.put("inactive")
                            return
                    else:
                        silence_start = None  # Reset silence timer on speech detection

                    text = await self.transcribe_audio(audio)
                    self.transcription_queue.put(text.strip())  # Put transcribed text in queue
                    yield text.strip()  # Return the transcribed text
                except sr.WaitTimeoutError:
                    if silence_start is not None and time.time() - silence_start >= self.silence_duration:
                        print(f"Detected {self.silence_duration} seconds of silence. Stopping transcription.")
                        self.state_queue.put("inactive")
                        return
                except Exception as e:
                    print(f"Error in transcribe_speech: {e}")

    async def continuous_transcription(self):
        while True:
            activated = await self.listen_for_activation()
            if activated:
                async for transcribed_text in self.transcribe_speech():
                    yield transcribed_text
'''         
'''
import asyncio
import queue
import speech_recognition as sr
import whisper
import numpy as np
import os
import tempfile
from pydub import AudioSegment
import time

class VoiceDetector:
    def __init__(self, activation_phrase, whisper_model_dir, whisper_model_version="medium", silence_duration=1, silence_threshold=-50, language="en-US"):
        self.activation_phrase = activation_phrase.lower()
        self.language = language  # Language for Google recognizer
        self.recognizer = sr.Recognizer()
        self.whisper_model = whisper.load_model(whisper_model_version, download_root=whisper_model_dir, device="cpu", in_memory=True)
        self.silence_duration = silence_duration  # in seconds
        self.silence_threshold = silence_threshold  # in dB
        self.transcription_queue = queue.Queue()  # Queue for transcribed text
        self.state_queue = queue.Queue()  # Queue for voice detection state

    async def listen_for_activation(self):
        while True:
            try:
                with sr.Microphone() as source:
                    print("Listening for activation phrase...")
                    self.recognizer.adjust_for_ambient_noise(source)
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                    try:
                        text = self.recognizer.recognize_google(audio, language=self.language).lower()
                        print(f"Heard: {text}")
                        if self.activation_phrase in text:
                            print(f"Activation phrase detected: {text}")
                            self.state_queue.put("active")
                            return True
                    except sr.UnknownValueError:
                        pass  # Speech was unintelligible
            except sr.WaitTimeoutError:
                continue
            except Exception as e:
                print(f"Error in listen_for_activation: {e}")

    async def transcribe_audio(self, audio):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            temp_audio.write(audio.get_wav_data())
            temp_audio_path = temp_audio.name

        try:
            result = self.whisper_model.transcribe(temp_audio_path, fp16=False)
            return result["text"]
        finally:
            os.unlink(temp_audio_path)

    def is_silent(self, audio_segment):
        return audio_segment.dBFS < self.silence_threshold

    async def transcribe_speech(self):
        print(f"Transcribing... (Will stop after {self.silence_duration} seconds of silence)")
        silence_start = None
        
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            while True:
                try:
                    audio = self.recognizer.listen(source, timeout=0.5, phrase_time_limit=10)  # Reduced timeout for faster checks
                    audio_segment = AudioSegment(
                        data=audio.get_raw_data(),
                        sample_width=audio.sample_width,
                        frame_rate=audio.sample_rate,
                        channels=1
                    )

                    # Check for silence every 0.5 seconds
                    if self.is_silent(audio_segment):
                        if silence_start is None:
                            silence_start = time.time()
                        elif time.time() - silence_start >= self.silence_duration:
                            print(f"Detected {self.silence_duration} seconds of silence. Stopping transcription.")
                            self.state_queue.put("inactive")
                            return
                    else:
                        silence_start = None  # Reset silence timer on speech detection

                    text = await self.transcribe_audio(audio)
                    self.transcription_queue.put(text.strip())  # Put transcribed text in queue
                    yield text.strip()  # Return the transcribed text
                except sr.WaitTimeoutError:
                    if silence_start is not None and time.time() - silence_start >= self.silence_duration:
                        print(f"Detected {self.silence_duration} seconds of silence. Stopping transcription.")
                        self.state_queue.put("inactive")
                        return
                except Exception as e:
                    print(f"Error in transcribe_speech: {e}")

    async def continuous_transcription(self):
        while True:
            activated = await self.listen_for_activation()
            if activated:
                async for transcribed_text in self.transcribe_speech():
                    yield transcribed_text

async def main():
    activation_phrase = "assistente"
    whisper_model_dir = r"E:/Python/prova1/models"  # Change this to your desired directory
    whisper_model_version = "medium"  # Choose "small", "base", "medium", "large", or "full"
    silence_threshold = -10  # Adjust the silence threshold as needed (lower value = more sensitive)
    language = "it-IT"  # Change language as needed (e.g., "it-IT" for Italian)

    detector = VoiceDetector(activation_phrase, whisper_model_dir, whisper_model_version, silence_duration=1, silence_threshold=silence_threshold, language=language)
    state_queue = detector.state_queue

    async for transcribed_text in detector.continuous_transcription():
        print(f"Transcribed: {transcribed_text}")

    while True:
        state = await state_queue.get()
        print(f"Voice detection state: {state}")

if __name__ == "__main__":
    asyncio.run(main())
'''