import os
import asyncio
import tempfile
import pygame
from PyQt6.QtCore import QObject, pyqtSignal, QThread

# Initialize pygame mixer once
try:
    pygame.mixer.init()
except Exception:
    pass

class EdgeTTSWorker(QThread):
    finished = pyqtSignal()
    
    def __init__(self, text: str, voice: str = "en-GB-RyanNeural"):
        super().__init__()
        self.text = text
        self.voice = voice
        self._is_stopped = False
        
    def stop(self):
        self._is_stopped = True
        try:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
        except Exception:
            pass
            
    def run(self):
        try:
            import edge_tts
            
            # Create a temporary file
            tmp_fd, tmp_path = tempfile.mkstemp(suffix=".mp3")
            os.close(tmp_fd)
            
            # Generate the audio asynchronously
            communicate = edge_tts.Communicate(self.text, self.voice)
            
            # Run the async code in a synchronous way for this thread
            asyncio.run(communicate.save(tmp_path))
            
            if self._is_stopped:
                return
                
            # Play the audio
            pygame.mixer.music.load(tmp_path)
            pygame.mixer.music.play()
            
            # Wait for playback to finish
            while pygame.mixer.music.get_busy() and not self._is_stopped:
                pygame.time.Clock().tick(10)
                
            # Cleanup
            pygame.mixer.music.unload()
            try:
                os.remove(tmp_path)
            except Exception:
                pass
                
        except Exception as e:
            print(f"[EdgeTTS] Error: {e}")
        finally:
            self.finished.emit()

class EdgeTTSManager(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_worker = None
        self._voice_id = "en-GB-RyanNeural" # Excellent British male JARVIS-like voice

    def say(self, text: str):
        if not text.strip():
            return
            
        self.stop()
        
        self.current_worker = EdgeTTSWorker(text, self._voice_id)
        self.current_worker.finished.connect(self._on_finished)
        self.current_worker.start()

    def stop(self):
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.stop()
            self.current_worker.wait()
            self.current_worker = None
            
    def _on_finished(self):
        # We could cleanup here if needed
        pass
        
    # Compatibility methods to match QTextToSpeech API usage in main.py
    def availableVoices(self):
        # Mock available voices
        class MockVoice:
            def __init__(self, name): self._name = name
            def name(self): return self._name
            
        return [
            MockVoice("JARVIS (British Male)"),
            MockVoice("David (US Male)"), 
            MockVoice("Zira (US Female)")
        ]
        
    def voice(self):
        class MockVoice:
            def __init__(self, name): self._name = name
            def name(self): return self._name
        if "Female" in self._voice_id: return MockVoice("Zira (US Female)")
        return MockVoice("JARVIS (British Male)")
        
    def setVoice(self, voice_obj):
        name = voice_obj.name().lower()
        if "female" in name or "zira" in name or "hazel" in name:
            self._voice_id = "en-US-AriaNeural"
        elif "david" in name:
            self._voice_id = "en-US-GuyNeural"
        else:
            self._voice_id = "en-GB-RyanNeural"
