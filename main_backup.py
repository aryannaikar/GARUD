"""
Garud AI — Native Desktop Assistant
PyQt6 frameless transparent window with holographic HUD aesthetics.
"""

import sys
import threading

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QLabel, QScrollArea,
    QFrame, QSizeGrip
)
from PyQt6.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QObject, QPropertyAnimation,
    QEasingCurve, QRect, pyqtSlot
)
from PyQt6.QtGui import (
    QColor, QPainter, QPen, QBrush, QFont, QFontDatabase,
    QLinearGradient, QRadialGradient, QConicalGradient, QPalette, QIcon, QPixmap
)

from tools.file_tools import build_file_cache
from voice.listener import VoiceListener
from PyQt6.QtTextToSpeech import QTextToSpeech


# ─────────────────────────────────────────
#  Worker: runs graph.invoke off the main thread
# ─────────────────────────────────────────
class QueryWorker(QObject):
    finished = pyqtSignal(str, bool)   # (result_text, is_chat)
    task_started = pyqtSignal(int, int, str, str)  # task_idx, total, agent, task

    def __init__(self, query: str):
        super().__init__()
        self.query = query

    def run(self):
        from graph.workflow import graph
        state = {
            "query": self.query,
            "agent": "",
            "result": "",
            "tasks": [],
            "current_task": 0,
            "context": "",
        }
        try:
            result = graph.invoke(state)
            is_chat = result.get("agent") == "chat"
            final_text = result.get("result", "")
            
            # Inject context globally so follow-up questions work seamlessly
            try:
                from agents.chat_agent import add_to_memory
                add_to_memory(self.query, final_text)
            except Exception as e:
                print(f"Memory update error: {e}")

            self.finished.emit(final_text, is_chat)
        except Exception as e:
            self.finished.emit(f"Error: {e}", False)

# ─────────────────────────────────────────
#  Custom Grid Card
# ─────────────────────────────────────────
class GridCard(QFrame):
    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw tech grid
        p.setPen(QPen(QColor(0, 200, 255, 12), 1))
        step = 25
        w, h = self.width(), self.height()
        
        for x in range(0, w, step):
            p.drawLine(x, 0, x, h)
        for y in range(0, h, step):
            p.drawLine(0, y, w, y)
        p.end()

# ─────────────────────────────────────────
#  Animated Orb Widget
# ─────────────────────────────────────────
class OrbWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(200, 200)
        self._state = "idle"      # idle | awake | thinking
        self._angle = 0
        self._pulse = 0.0
        self._pulse_dir = 1
        
        # Load the newly extracted JARVIS Garud logo
        import os
        logo_path = os.path.join(os.path.dirname(__file__), "image", "logo_main.png")
        if os.path.exists(logo_path):
            self.logo = QPixmap(logo_path).scaled(56, 56, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        else:
            self.logo = None

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(30)

    def set_state(self, state: str):
        self._state = state
        self.update()

    def _tick(self):
        speed = 3 if self._state == "thinking" else 1
        self._angle = (self._angle + speed) % 360
        self._pulse += 0.05 * self._pulse_dir
        if self._pulse >= 1.0 or self._pulse <= 0.0:
            self._pulse_dir *= -1
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy = self.width() // 2, self.height() // 2

        # Colors by state (JARVIS + Garud)
        if self._state == "thinking":
            primary = QColor(255, 170, 0)   # Gold/Amber
            secondary = QColor(255, 50, 50) # Red
        elif self._state == "awake":
            primary = QColor(0, 200, 255)   # Electric Blue (JARVIS)
            secondary = QColor(255, 180, 0) # Gold (Garud/Eagle)
        else:
            primary = QColor(0, 180, 255, 140)
            secondary = QColor(255, 180, 0, 80)

        # ── Rotating HUD Arcs ──
        p.save()
        p.translate(cx, cy)
        p.rotate(self._angle)
        
        pen = QPen(primary, 2.0)
        p.setPen(pen)
        p.drawArc(-70, -70, 140, 140, 0 * 16, 120 * 16)
        p.drawArc(-70, -70, 140, 140, 140 * 16, 80 * 16)
        p.drawArc(-70, -70, 140, 140, 240 * 16, 100 * 16)
        
        # Inner reverse rotating dashed ring
        p.rotate(-self._angle * 2.5)
        pen.setStyle(Qt.PenStyle.DashLine)
        pen.setColor(secondary)
        pen.setWidthF(1.5)
        p.setPen(pen)
        p.drawEllipse(-55, -55, 110, 110)
        
        # Central spinning targeting triangle
        p.rotate(self._angle * 4)
        from PyQt6.QtGui import QPolygonF
        from PyQt6.QtCore import QPointF
        import math
        tri_size = 15
        triangle = QPolygonF([
            QPointF(0, -tri_size),
            QPointF(tri_size * math.cos(math.pi/6), tri_size * math.sin(math.pi/6)),
            QPointF(-tri_size * math.cos(math.pi/6), tri_size * math.sin(math.pi/6))
        ])
        p.setPen(QPen(primary, 1.0))
        p.drawPolygon(triangle)
        p.restore()
        
        # ── Concentric Compass Tick Marks ──
        p.save()
        p.translate(cx, cy)
        p.setPen(QPen(QColor(0, 200, 255, 60), 1.0))
        for i in range(0, 360, 15):
            p.rotate(15)
            p.drawLine(85, 0, 92, 0)
        p.restore()

        # ── Garud Eagle Wings (Geometric) ──
        p.save()
        p.translate(cx, cy)
        wing_pen = QPen(primary, 2.0)
        p.setPen(wing_pen)
        
        wing_pulse = int(5 * self._pulse)
        
        # Left wing
        p.drawLine(-35 - wing_pulse, -20, -55 - wing_pulse, -40)
        p.drawLine(-35 - wing_pulse, 0,   -65 - wing_pulse, -15)
        p.drawLine(-35 - wing_pulse, 20,  -55 - wing_pulse, 40)
        
        # Right wing
        p.drawLine(35 + wing_pulse, -20, 55 + wing_pulse, -40)
        p.drawLine(35 + wing_pulse, 0,   65 + wing_pulse, -15)
        p.drawLine(35 + wing_pulse, 20,  55 + wing_pulse, 40)
        p.restore()

        # ── Glowing Core (Eagle Eye) ──
        pulse_r = int(12 + 4 * self._pulse)
        grad = QRadialGradient(cx, cy, pulse_r * 2.5)
        c1 = QColor(secondary)
        c1.setAlpha(200 if self._state != "idle" else 50)
        c2 = QColor(secondary)
        c2.setAlpha(0)
        grad.setColorAt(0, c1)
        grad.setColorAt(1, c2)
        p.setBrush(QBrush(grad))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(cx - pulse_r * 2, cy - pulse_r * 2, pulse_r * 4, pulse_r * 4)

        # ── Radar Sweep ──
        if self._state != "idle":
            p.save()
            p.translate(cx, cy)
            p.rotate(self._angle * 2)
            radar_grad = QConicalGradient(0, 0, 0)
            radar_c = QColor(primary)
            radar_c.setAlpha(100)
            radar_grad.setColorAt(0, radar_c)
            radar_c.setAlpha(0)
            radar_grad.setColorAt(0.1, radar_c)
            radar_grad.setColorAt(1, radar_c)
            p.setBrush(QBrush(radar_grad))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawPie(-80, -80, 160, 160, 0, 36 * 16)
            p.restore()

        # Solid core background
        core_color = secondary if self._state != "idle" else primary
        p.setBrush(QBrush(core_color))
        p.drawEllipse(cx - pulse_r, cy - pulse_r, pulse_r * 2, pulse_r * 2)

        # Draw the Garud logo inside the core
        if self.logo is not None:
            lw, lh = self.logo.width(), self.logo.height()
            p.drawPixmap(cx - lw // 2, cy - lh // 2, self.logo)

        # ── Tech Brackets ──
        p.setPen(QPen(primary, 1.5))
        p.setBrush(Qt.BrushStyle.NoBrush)
        
        # Left bracket
        p.drawLine(10, cy - 20, 10, cy + 20)
        p.drawLine(10, cy - 20, 15, cy - 20)
        p.drawLine(10, cy + 20, 15, cy + 20)
        
        # Right bracket
        w = self.width()
        p.drawLine(w - 10, cy - 20, w - 10, cy + 20)
        p.drawLine(w - 10, cy - 20, w - 15, cy - 20)
        p.drawLine(w - 10, cy + 20, w - 15, cy + 20)
        
        # Micro-text telemetry
        p.setPen(QPen(primary, 1))
        font = p.font()
        font.setPointSize(6)
        font.setFamily("Consolas")
        p.setFont(font)
        p.drawText(20, 20, f"SYS.ANGLE: {int(self._angle)}°")
        p.drawText(20, 30, f"SYS.PULSE: {self._pulse:.2f}")
        p.drawText(w - 75, self.height() - 20, "SECURE // OK")
        
        p.end()


# ─────────────────────────────────────────
#  Voice Wave Bar Widget
# ─────────────────────────────────────────
class WaveWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(40)
        self._active = False
        self._heights = [0.2, 0.4, 0.6, 0.4, 0.2, 0.4, 0.6]
        self._dirs = [1, -1, 1, -1, 1, -1, 1]
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(60)

    def set_active(self, val: bool):
        self._active = val
        self.update()

    def _tick(self):
        if not self._active:
            return
        import random
        for i in range(len(self._heights)):
            self._heights[i] += self._dirs[i] * 0.1
            if self._heights[i] >= 1.0 or self._heights[i] <= 0.1:
                self._dirs[i] *= -1
        self.update()

    def paintEvent(self, event):
        if not self._active:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor(0, 200, 255)  # Electric Blue
        p.setBrush(QBrush(color))
        p.setPen(Qt.PenStyle.NoPen)
        n = len(self._heights)
        w = self.width()
        bar_w = 5
        gap = (w - n * bar_w) // (n + 1)
        for i, h in enumerate(self._heights):
            bar_h = int(h * self.height())
            x = gap + i * (bar_w + gap)
            y = (self.height() - bar_h) // 2
            p.drawRoundedRect(x, y, bar_w, bar_h, 2, 2)
        p.end()


# ─────────────────────────────────────────
#  Chat Message Widget
# ─────────────────────────────────────────
def make_message(sender: str, text: str) -> QFrame:
    frame = QFrame()
    frame.setObjectName("userMsg" if sender == "YOU" else "garudMsg")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(10, 8, 10, 8)
    layout.setSpacing(3)

    label_text = QLabel(f"<b>{sender} //</b>  {text.replace(chr(10), '<br>')}")
    label_text.setWordWrap(True)
    label_text.setTextFormat(Qt.TextFormat.RichText)
    layout.addWidget(label_text)

    if sender == "YOU":
        frame.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.03);
                border-right: 3px solid #888888;
                border-radius: 8px;
            }
            QLabel { color: #dddddd; font-size: 13px; }
        """)
    else:
        frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(0,200,255,0.1), stop:1 rgba(0,200,255,0.02));
                border-left: 3px solid #00ccff;
                border-radius: 8px;
            }
            QLabel { color: #00ccff; font-size: 13px; }
        """)
    return frame


# ─────────────────────────────────────────
#  Main Window
# ─────────────────────────────────────────
class GarudWindow(QWidget):
    _query_signal = pyqtSignal(str)   # thread-safe query trigger

    def __init__(self):
        super().__init__()
        self._drag_pos = None
        self._is_processing = False
        
        # Initialize native Qt TTS
        self.tts = QTextToSpeech(self)
        self.tts.setRate(0.0)  # 0.0 is normal speed (previously 0.3 was too fast)
        self.tts.setPitch(0.0)
        
        # Try to find a male English voice
        for voice in self.tts.availableVoices():
            name = voice.name().lower()
            if "david" in name or "mark" in name:
                self.tts.setVoice(voice)
                break
                
        self._build_ui()
        self._start_voice()
        self._query_signal.connect(self._run_query)

    def closeEvent(self, event):
        if hasattr(self, "_listener") and self._listener:
            self._listener.stop()
        if hasattr(self, "_voice_thread") and self._voice_thread.isRunning():
            self._voice_thread.quit()
            self._voice_thread.wait(1000)
        event.accept()

    # ── UI Construction ──────────────────
    def _build_ui(self):
        self.setWindowTitle("Garud AI")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(520, 700)
        self.resize(540, 740)

        # Root layout
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        # Glass card with grid
        card = GridCard(self)
        card.setObjectName("card")
        card.setStyleSheet("""
            #card {
                background: rgba(8, 12, 22, 0.88);
                border: 1px solid rgba(0,200,255,0.25);
                border-radius: 18px;
            }
        """)
        root.addWidget(card)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 20, 24, 20)
        card_layout.setSpacing(14)

        # ── Top Bar ──────────────────────
        top_bar = QHBoxLayout()
        top_bar.setSpacing(12)
        top_bar.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Logo Badge
        import os
        logo_path = os.path.join(os.path.dirname(__file__), "image", "logo_main.png")
        if os.path.exists(logo_path):
            logo_label = QLabel()
            badge = QPixmap(logo_path).scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(badge)
            top_bar.addWidget(logo_label)

        # Status label
        self.status_label = QLabel("⚡  OFFLINE  —  say 'wake up garud'")
        self.status_label.setStyleSheet(
            "color: rgba(0,200,255,0.6); font-size: 11px; font-family: Consolas;"
        )
        top_bar.addWidget(self.status_label)
        top_bar.addStretch()

        # Close button
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,60,100,0.15);
                color: rgba(255,60,100,0.8);
                border: 1px solid rgba(255,60,100,0.3);
                border-radius: 14px;
                font-size: 12px;
            }
            QPushButton:hover { background: rgba(255,60,100,0.35); }
        """)
        close_btn.clicked.connect(self.close)
        top_bar.addWidget(close_btn)
        card_layout.addLayout(top_bar)

        # ── Orb + Waves ──────────────────
        orb_row = QHBoxLayout()
        orb_row.addStretch()
        self.orb = OrbWidget()
        orb_row.addWidget(self.orb)
        orb_row.addStretch()
        card_layout.addLayout(orb_row)

        self.wave = WaveWidget()
        card_layout.addWidget(self.wave)

        # ── Chat Log ─────────────────────
        self.chat_area = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_area)
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chat_layout.setSpacing(10)
        self.chat_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidget(self.chat_area)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea { background: transparent; }
            QScrollBar:vertical {
                background: transparent; width: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(0,200,255,0.3);
                border-radius: 2px;
            }
        """)
        self._scroll = scroll
        card_layout.addWidget(scroll, stretch=1)

        # Welcome message
        self._add_message("GARUD", "System online. Say 'wake up garud' to activate.")

        # ── Input Bar ────────────────────
        input_row = QHBoxLayout()
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Type a command or speak...")
        self.text_input.setStyleSheet("""
            QLineEdit {
                background: rgba(0,200,255,0.05);
                border: 1px solid rgba(0,200,255,0.2);
                border-radius: 10px;
                color: #00ccff;
                font-size: 13px;
                padding: 10px 14px;
            }
            QLineEdit:focus { border-color: rgba(0,200,255,0.6); }
        """)
        self.text_input.returnPressed.connect(self._on_text_enter)
        input_row.addWidget(self.text_input)
        card_layout.addLayout(input_row)

    # ── Message helpers ──────────────────
    def _add_message(self, sender: str, text: str):
        msg = make_message(sender, text)
        self.chat_layout.addWidget(msg)
        QTimer.singleShot(50, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        sb = self._scroll.verticalScrollBar()
        sb.setValue(sb.maximum())

    # ── Voice Setup ──────────────────────
    def _start_voice(self):
        self._voice_thread = QThread(self)
        self._listener = VoiceListener()
        self._listener.moveToThread(self._voice_thread)

        self._voice_thread.started.connect(self._listener.run)
        self._listener.wake_up.connect(self._on_wake_up)
        self._listener.go_to_sleep.connect(self._on_sleep)
        self._listener.user_spoke.connect(self._on_user_spoke)
        self._listener.query_ready.connect(self._run_query)

        self._voice_thread.start()

    # ── Voice Event Handlers ─────────────
    @pyqtSlot()
    def _on_wake_up(self):
        self.orb.set_state("awake")
        self.wave.set_active(True)
        self.status_label.setText("🟢  AWAKE  —  listening...")
        self.status_label.setStyleSheet(
            "color: #00ccff; font-size: 11px; font-family: Consolas;"
        )
        self._add_message("GARUD", "I'm awake. How can I help you?")
        self.tts.say("I'm awake. How can I help you?")

    @pyqtSlot()
    def _on_sleep(self):
        self.orb.set_state("idle")
        self.wave.set_active(False)
        self.status_label.setText("⚡  OFFLINE  —  say 'wake up garud'")
        self.status_label.setStyleSheet(
            "color: rgba(0,200,255,0.5); font-size: 11px; font-family: Consolas;"
        )
        self._add_message("GARUD", "Going to sleep. Say 'wake up garud' to activate again.")
        self.tts.say("Going to sleep. Say wake up garud to activate again.")

    @pyqtSlot(str)
    def _on_user_spoke(self, text: str):
        self._add_message("YOU", text)

    # ── Query Execution ──────────────────
    def _on_text_enter(self):
        query = self.text_input.text().strip()
        if not query:
            return
        self.text_input.clear()
        self._add_message("YOU", query)
        self._run_query(query)

    @pyqtSlot(str)
    def _run_query(self, query: str):
        # Drop new commands while already processing
        if self._is_processing:
            print(f"[Dropped — busy] {query}")
            return
        self._is_processing = True

        self.orb.set_state("thinking")
        self.status_label.setText("🔴  THINKING...")

        self._worker_thread = QThread(self)
        self._worker = QueryWorker(query)
        self._worker.moveToThread(self._worker_thread)
        self._worker_thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_result)
        self._worker.finished.connect(self._worker_thread.quit)
        self._worker_thread.start()

    @pyqtSlot(str, bool)
    def _on_result(self, text: str, is_chat: bool):
        self._is_processing = False

        # Restore orb state
        if self._listener.awake:
            self.orb.set_state("awake")
            self.status_label.setText("🟢  AWAKE  —  listening...")
        else:
            self.orb.set_state("idle")
            self.status_label.setText("⚡  OFFLINE  —  say 'wake up garud'")

        if text:
            self._add_message("GARUD", text)
            clean_text = text.replace("*", "").replace("#", "").replace("`", "")
            self.tts.say(clean_text)

    # ── Window Dragging ──────────────────
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() == Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self.move(self.pos() + delta)
            self._drag_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None


# ─────────────────────────────────────────
#  Entry Point
# ─────────────────────────────────────────
if __name__ == "__main__":
    print("Garud AI starting...")
    build_file_cache()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Dark palette
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(8, 12, 22))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 200, 255))
    app.setPalette(palette)

    window = GarudWindow()
    window.show()
    sys.exit(app.exec())