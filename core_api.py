import json
import threading
import numpy as np
import whisper
import speech_recognition as sr
import pywebview as webview # actually webview

from graph.workflow import graph

class Streamer:
    def __init__(self):
        self.window = None

streamer = Streamer()

class GarudAPI:
    def __init__(self):
        self.window = None
        self.awake = False
        print("Loading Whisper Model...")
        self.whisper_model = whisper.load_model("base")
        self.recognizer = sr.Recognizer()
        
        # Start background listening thread
        self.listen_thread = threading.Thread(target=self._continuous_listen, daemon=True)
        
    def set_window(self, window):
        self.window = window
        streamer.window = window
        self.listen_thread.start()

    def _continuous_listen(self):
        # Force 16000Hz so we don't have to resample for whisper
        with sr.Microphone(sample_rate=16000) as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("Listening for wake word 'wake up garud'...")
            
            while True:
                try:
                    audio_data = self.recognizer.listen(source, phrase_time_limit=10)
                    wav_bytes = audio_data.get_wav_data()
                    
                    import io
                    import scipy.io.wavfile as wav
                    rate, data = wav.read(io.BytesIO(wav_bytes))
                    
                    if data.dtype != np.float32:
                        data = data.astype(np.float32) / np.iinfo(data.dtype).max
                        
                    if len(data.shape) > 1:
                        data = data.mean(axis=1)
                        
                    result = self.whisper_model.transcribe(data, fp16=False)
                    text = result.get('text', '').strip().lower()
                    
                    if not text:
                        continue
                        
                    print(f"Heard: {text}")

                    if not self.awake:
                        if "wake up garud" in text or "wakeup garud" in text or "wake up" in text:
                            self.awake = True
                            self.window.evaluate_js('addMessage("GARUD", "I am awake. How can I help you?"); setAwakeState(true);')
                    else:
                        if "go to sleep" in text or "sleep" in text:
                            self.awake = False
                            self.window.evaluate_js('addMessage("GARUD", "Going to sleep. Wake me up if you need anything."); setAwakeState(false);')
                        else:
                            self.window.evaluate_js(f'addMessage("USER", {json.dumps(text)})')
                            self.send_query(text)

                except Exception as e:
                    print(f"Audio processing error: {e}")

    def send_query(self, query):
        if not query.strip():
            return
            
        self.window.evaluate_js('setThinking(true)')
        
        state = {
            "query": query,
            "agent": "",
            "result": "",
            "tasks": [],
            "current_task": 0,
            "context": ""
        }
        
        try:
            result = graph.invoke(state)
            
            # For non-chat agents, send result to UI
            if result.get("agent") != "chat":
                self.window.evaluate_js(f'addMessage("GARUD", {json.dumps(result["result"])})')
                
        except Exception as e:
            self.window.evaluate_js(f'addMessage("GARUD", "Error: {str(e)}")')
            
        finally:
            self.window.evaluate_js('setThinking(false)')
