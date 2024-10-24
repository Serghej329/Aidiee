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