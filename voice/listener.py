"""
Continuous voice listener using SpeechRecognition + Google STT.
No model downloads required — works instantly.

Wake word:  "wake up garud" / "wakeup garud" / "hey garud"
Sleep word: "garud go to sleep" / "go to sleep" / "garud sleep"
"""

import speech_recognition as sr
from PyQt6.QtCore import QObject, pyqtSignal

WAKE_PHRASES = ["wake up garud", "wakeup garud", "hey garud", "wake garud", "wake up"]
SLEEP_PHRASES = ["garud go to sleep", "go to sleep", "garud sleep", "sleep now"]


class VoiceListener(QObject):
    user_spoke   = pyqtSignal(str)   # raw transcript shown in chat
    wake_up      = pyqtSignal()
    go_to_sleep  = pyqtSignal()
    query_ready  = pyqtSignal(str)   # command sent to graph

    def __init__(self, parent=None):
        super().__init__(parent)
        self.awake = False
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.pause_threshold = 0.8
        self.recognizer.dynamic_energy_threshold = True
        self._running = True
        print("Voice listener ready (Google STT).")

    def stop(self):
        self._running = False

    def run(self):
        """Blocking loop — must be called from a QThread."""
        try:
            mic = sr.Microphone()
        except Exception as e:
            print(f"Microphone error: {e}")
            return

        with mic as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("Listening... say 'wake up garud' to activate.")

            while self._running:
                try:
                    audio = self.recognizer.listen(source, phrase_time_limit=8)
                    text = self._transcribe(audio)

                    if not text:
                        continue

                    tl = text.lower().strip()
                    print(f"[STT] {text}")

                    if not self.awake:
                        if any(p in tl for p in WAKE_PHRASES):
                            self.awake = True
                            self.wake_up.emit()
                    else:
                        if any(p in tl for p in SLEEP_PHRASES):
                            self.awake = False
                            self.go_to_sleep.emit()
                        else:
                            self.user_spoke.emit(text)
                            self.query_ready.emit(text)

                except sr.WaitTimeoutError:
                    pass
                except Exception as e:
                    print(f"Listen error: {e}")

    def _transcribe(self, audio: sr.AudioData) -> str:
        try:
            return self.recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            print(f"Google STT error: {e}")
            return ""
