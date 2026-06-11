"""
Garud AI — Native Desktop Assistant
PyQt6 frameless transparent window with holographic HUD aesthetics.
"""

import sys
import os
import re
import math
import random
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
#  Custom Grid Card (Premium Background)
# ─────────────────────────────────────────
class GridCard(QFrame):
    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w, h = self.width(), self.height()
        
        # Draw tech grid
        p.setPen(QPen(QColor(0, 200, 255, 12), 1))
        step = 25
        for x in range(0, w, step):
            p.drawLine(x, 0, x, h)
        for y in range(0, h, step):
            p.drawLine(0, y, w, y)
            
        # Subtle vignette overlay
        grad = QRadialGradient(w/2, h/2, w/1.2)
        grad.setColorAt(0, QColor(0, 0, 0, 0))
        grad.setColorAt(1, QColor(0, 5, 15, 160))
        p.setBrush(QBrush(grad))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRect(0, 0, w, h)
        p.end()

# ─────────────────────────────────────────
#  Animated Orb Widget (Cinematic HUD)
# ─────────────────────────────────────────
class OrbWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(300, 260)
        self._state = "idle"      # idle | awake | thinking
        self._angle = 0
        self._pulse = 0.0
        self._pulse_dir = 1
        
        # Load the JARVIS Garud logo
        logo_path = os.path.join(os.path.dirname(__file__), "image", "logo_main.png")
        if os.path.exists(logo_path):
            self.logo = QPixmap(logo_path).scaled(140, 140, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        else:
            self.logo = None

        # Particle system
        self.particles = [{"x": random.randint(-100, 100), "y": random.randint(-100, 100), "speed": random.uniform(0.5, 2.0), "angle": random.uniform(0, 360)} for _ in range(30)]

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(30)

    def set_state(self, state: str):
        self._state = state
        self.update()

    def _tick(self):
        speed = 4.5 if self._state == "thinking" else 1.5
        self._angle = (self._angle + speed) % 360
        self._pulse += 0.03 * self._pulse_dir
        if self._pulse >= 1.0 or self._pulse <= 0.0:
            self._pulse_dir *= -1
            
        # Update particles
        for p in self.particles:
            p["x"] += math.cos(math.radians(p["angle"])) * p["speed"]
            p["y"] += math.sin(math.radians(p["angle"])) * p["speed"]
            if abs(p["x"]) > 130 or abs(p["y"]) > 130:
                p["x"] = random.randint(-40, 40)
                p["y"] = random.randint(-40, 40)
                p["angle"] = random.uniform(0, 360)
                
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        cx, cy = self.width() // 2, self.height() // 2

        # Cinematic Colors
        if self._state == "thinking":
            primary = QColor(255, 120, 0)   # Overdrive Amber
            secondary = QColor(255, 30, 30) # Core Red
            glow_opacity = 180
        elif self._state == "awake":
            primary = QColor(0, 220, 255)   # JARVIS Cyan
            secondary = QColor(0, 100, 255) # Deep Blue
            glow_opacity = 140
        else:
            primary = QColor(0, 180, 255, 80)
            secondary = QColor(0, 50, 150, 50)
            glow_opacity = 40

        # ── 1. Deep Background Glow (Aura) ──
        pulse_r = int(70 + 20 * self._pulse)
        grad = QRadialGradient(cx, cy, pulse_r * 1.5)
        c1 = QColor(primary)
        c1.setAlpha(glow_opacity)
        c2 = QColor(secondary)
        c2.setAlpha(0)
        grad.setColorAt(0, c1)
        grad.setColorAt(1, c2)
        p.setBrush(QBrush(grad))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(cx - int(pulse_r * 1.5), cy - int(pulse_r * 1.5), int(pulse_r * 3), int(pulse_r * 3))

        # ── 2. Holographic Rings ──
        p.save()
        p.translate(cx, cy)
        
        # Outer dashed target ring
        p.rotate(self._angle * 0.5)
        pen = QPen(primary, 1.5)
        pen.setStyle(Qt.PenStyle.DashLine)
        p.setPen(pen)
        p.drawEllipse(-110, -110, 220, 220)
        
        # Inner solid tech arcs
        p.rotate(-self._angle * 1.2)
        pen.setStyle(Qt.PenStyle.SolidLine)
        pen.setWidthF(3.0)
        pen.setColor(QColor(primary.red(), primary.green(), primary.blue(), int(255 * (0.5 + 0.5 * self._pulse))))
        p.setPen(pen)
        p.drawArc(-90, -90, 180, 180, 30 * 16, 60 * 16)
        p.drawArc(-90, -90, 180, 180, 150 * 16, 60 * 16)
        p.drawArc(-90, -90, 180, 180, 270 * 16, 60 * 16)
        
        # Hexagonal core lock (only when thinking)
        if self._state == "thinking":
            p.rotate(self._angle * 2)
            from PyQt6.QtGui import QPolygonF
            from PyQt6.QtCore import QPointF
            hex_pts = QPolygonF()
            for i in range(6):
                ang = i * (math.pi / 3)
                hex_pts.append(QPointF(65 * math.cos(ang), 65 * math.sin(ang)))
            pen.setWidthF(1.0)
            pen.setColor(secondary)
            p.setPen(pen)
            p.drawPolygon(hex_pts)
            
        p.restore()

        # ── 3. Particle Field ──
        if self._state != "idle":
            p.save()
            p.translate(cx, cy)
            p.setPen(Qt.PenStyle.NoPen)
            for pt in self.particles:
                alpha = max(0, int(255 * (1.0 - (math.sqrt(pt["x"]**2 + pt["y"]**2) / 130.0))))
                part_col = QColor(primary)
                part_col.setAlpha(alpha)
                p.setBrush(QBrush(part_col))
                size = 2 if self._state == "awake" else 3
                p.drawEllipse(int(pt["x"]), int(pt["y"]), size, size)
            p.restore()

        # ── 4. The Blended Garud Logo ──
        if self.logo is not None:
            # Draw logo
            lw, lh = self.logo.width(), self.logo.height()
            
            # Subtle hover float effect
            float_y = int(math.sin(self._pulse * math.pi * 2) * 4)
            p.drawPixmap(cx - lw // 2, cy - lh // 2 + float_y, self.logo)

            # Eye flare (when thinking)
            if self._state == "thinking":
                flare_grad = QRadialGradient(cx, cy + float_y, 30)
                flare_c = QColor(255, 255, 255, 200)
                flare_grad.setColorAt(0, flare_c)
                flare_c.setAlpha(0)
                flare_grad.setColorAt(1, flare_c)
                p.setBrush(QBrush(flare_grad))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(cx - 20, cy - 20 + float_y, 40, 40)

        # ── 5. Sci-Fi Telemetry & Scanlines ──
        w = self.width()
        h = self.height()
        
        p.setPen(QPen(primary, 1))
        font = p.font()
        font.setPointSize(7)
        font.setFamily("Consolas")
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.0)
        p.setFont(font)
        
        # Left Data Column
        p.drawText(10, 30, f"SYS.MEM  // {int(3400 + self._pulse * 100)} TB")
        p.drawText(10, 45, f"SYS.ROT  // {self._angle:.1f}°")
        p.drawText(10, 60, f"PWR.CORE // {int(self._pulse * 100)}%")
        
        # Right Data Column
        p.drawText(w - 90, 30, f"UPLINK // OK")
        p.drawText(w - 90, 45, f"LATENCY// {int(12 + self._pulse * 5)}ms")
        p.drawText(w - 90, 60, f"NEURAL // {'SYNC' if self._state != 'thinking' else 'PROC'}")

        # Decorative brackets
        p.setPen(QPen(primary, 2))
        p.drawLine(5, cy - 20, 5, cy + 20)
        p.drawLine(5, cy - 20, 15, cy - 20)
        p.drawLine(5, cy + 20, 15, cy + 20)
        
        p.drawLine(w - 5, cy - 20, w - 5, cy + 20)
        p.drawLine(w - 5, cy - 20, w - 15, cy - 20)
        p.drawLine(w - 5, cy + 20, w - 15, cy + 20)

        # Horizontal Scanlines across the widget
        p.setPen(QPen(QColor(0, 200, 255, 10), 1))
        for y in range(0, h, 4):
            p.drawLine(0, y, w, y)

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
#  Chat Message Widget (Premium UI)
# ─────────────────────────────────────────
def make_message(sender: str, text: str) -> QFrame:
    frame = QFrame()
    frame.setObjectName("userMsg" if sender == "YOU" else "garudMsg")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(14, 12, 14, 12)
    layout.setSpacing(4)

    # Simple formatting for code blocks in Qt Rich Text
    formatted_text = text.replace("```python", "<pre style='color:#00e5ff; background:rgba(0,0,0,0.4); padding:8px; border-radius:4px;'>").replace("```", "</pre>")
    formatted_text = formatted_text.replace(chr(10), '<br>')

    label_text = QLabel(f"<span style='font-family: Consolas; font-size: 11px; color: rgba(255,255,255,0.4);'>{sender} //</span><br><br>{formatted_text}")
    label_text.setWordWrap(True)
    label_text.setTextFormat(Qt.TextFormat.RichText)
    
    # Enable text selection
    label_text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.LinksAccessibleByMouse)
    
    layout.addWidget(label_text)

    if sender == "YOU":
        frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:1, y1:0, x2:0, y2:0, stop:0 rgba(255,255,255,0.06), stop:1 rgba(255,255,255,0.01));
                border-right: 2px solid rgba(255,255,255,0.3);
                border-radius: 6px;
                border-bottom: 1px solid rgba(255,255,255,0.02);
            }
            QLabel { color: #eeeeee; font-size: 13px; font-family: 'Segoe UI', Arial, sans-serif; }
        """)
    else:
        frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(0,200,255,0.12), stop:1 rgba(0,200,255,0.02));
                border-left: 3px solid #00ccff;
                border-radius: 6px;
                border-bottom: 1px solid rgba(0,200,255,0.05);
            }
            QLabel { color: #d0f4ff; font-size: 13.5px; font-family: 'Segoe UI', Arial, sans-serif; }
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
        
        # Try to find George (British Male) or David (US Male)
        voices = self.tts.availableVoices()
        chosen_voice = None
        for v in voices:
            if "george" in v.name().lower():
                chosen_voice = v
                break
        if not chosen_voice:
            for v in voices:
                if "david" in v.name().lower() or "mark" in v.name().lower():
                    chosen_voice = v
                    break
        if chosen_voice:
            self.tts.setVoice(chosen_voice)
                
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

    def _add_vision_frame(self, frame_path: str):
        """Display an annotated YOLO frame inline in the chat."""
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background: rgba(0,200,255,0.05);
                border: 1px solid rgba(0,200,255,0.25);
                border-radius: 8px;
                padding: 4px;
            }
        """)
        vlayout = QVBoxLayout(container)
        vlayout.setContentsMargins(6, 6, 6, 6)

        header = QLabel("📷  VISION SCAN")
        header.setStyleSheet("color: #00ccff; font-size: 10px; font-family: Consolas;")
        vlayout.addWidget(header)

        img_label = QLabel()
        pixmap = QPixmap(frame_path)
        if not pixmap.isNull():
            scaled = pixmap.scaledToWidth(460, Qt.TransformationMode.SmoothTransformation)
            img_label.setPixmap(scaled)
            img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vlayout.addWidget(img_label)

        self.chat_layout.addWidget(container)
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
        self.show()
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
        self.hide()
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

        # Voice Protocol Override
        lower_q = query.lower()
        if "change voice" in lower_q:
            voices = self.tts.availableVoices()
            current = self.tts.voice()
            if " to " in lower_q:
                target = lower_q.split(" to ")[-1].strip().strip(".?!")
                
                # Map generic genders to actual voice names
                target_names = [target]
                if target in ["male", "boy", "man", "guy"]:
                    target_names = ["george", "david", "mark"]
                elif target in ["female", "girl", "woman", "lady"]:
                    target_names = ["hazel", "zira", "catherine"]

                chosen = None
                for v in voices:
                    v_name = v.name().lower()
                    if any(t in v_name for t in target_names):
                        chosen = v
                        break
                        
                if chosen:
                    self.tts.setVoice(chosen)
                    msg = f"Voice protocol updated. I am now using the {target} voice profile."
                else:
                    msg = f"Voice protocol error. Could not locate '{target}' in the system registry."
            else:
                idx = 0
                for i, v in enumerate(voices):
                    if v.name() == current.name():
                        idx = i
                        break
                next_idx = (idx + 1) % len(voices)
                self.tts.setVoice(voices[next_idx])
                msg = f"Voice protocol cycled. I am now using {voices[next_idx].name()}."
            
            self._add_message("GARUD", msg)
            self.tts.say(msg)
            return
        self._is_processing = True

        self.orb.set_state("thinking")
        self.status_label.setText("🔴  THINKING...")

        # Use local variables and let Qt handle the cleanup via deleteLater to prevent 
        # "QThread: Destroyed while thread is still running" crashes on rapid queries.
        thread = QThread(self)
        worker = QueryWorker(query)
        worker.moveToThread(thread)
        
        thread.started.connect(worker.run)
        worker.finished.connect(self._on_result)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        
        # Keep a reference to prevent immediate Python GC before it starts
        self._worker_thread = thread
        self._worker = worker
        
        thread.start()

    @pyqtSlot(str, bool)
    def _on_result(self, text: str, is_chat: bool):
        self._is_processing = False

        # Restore orb state
        if self._listener.awake:
            self.orb.set_state("awake")
            self.status_label.setText("🟢  AWAKE  — listening...")
        else:
            self.orb.set_state("idle")
            self.status_label.setText("⚡  OFFLINE  — say 'wake up garud'")

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
    # The window starts hidden; it will only show when "wake up garud" is detected
    sys.exit(app.exec())