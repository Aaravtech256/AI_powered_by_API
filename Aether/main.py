import sys
import re
import threading

from PyQt6.QtCore import QTimer, pyqtSignal, QObject
from PyQt6.QtWidgets import QApplication

from ui.main_window import MainWindow
from audio.microphone import Microphone
from audio.speaker import Speaker
from ai.gemini_live import GeminiLive
from ai.image_generator import ImageGenerator
from config import GEMINI_API_KEY


class AetherSignals(QObject):

    audio = pyqtSignal(bytes)

    text = pyqtSignal(str, str)

    status = pyqtSignal(str)

    turn_complete = pyqtSignal()

    image_ready = pyqtSignal(str)

    image_error = pyqtSignal(str)


class AetherApp:

    def __init__(self):

        # =================================================
        # QT
        # =================================================

        self.app = QApplication(sys.argv)

        # =================================================
        # MAIN WINDOW
        # =================================================

        self.window = MainWindow()

        # =================================================
        # SIGNALS
        # =================================================

        self.signals = AetherSignals()

        self.signals.audio.connect(
            self.handle_audio
        )

        self.signals.text.connect(
            self.handle_text
        )

        self.signals.status.connect(
            self.handle_status
        )

        self.signals.turn_complete.connect(
            self.handle_turn_complete
        )

        self.signals.image_ready.connect(
            self.handle_image_ready
        )

        self.signals.image_error.connect(
            self.handle_image_error
        )

        # =================================================
        # AUDIO
        # =================================================

        self.microphone = Microphone()

        self.speaker = Speaker()

        # =================================================
        # IMAGE GENERATOR
        # =================================================

        self.image_generator = ImageGenerator(
            GEMINI_API_KEY
        )

        # =================================================
        # STATE
        # =================================================

        self.listening = False

        self.user_text_buffer = ""

        self.ai_text_buffer = ""

        self.shutting_down = False

        self.generating_image = False

        # -------------------------------------------------
        # Prevent duplicate typed messages
        # -------------------------------------------------

        self.last_typed_message = ""

        # =================================================
        # GEMINI LIVE
        # =================================================

        self.ai = GeminiLive(

            on_audio=self.on_audio,

            on_text=self.on_text,

            on_status=self.on_status,

            on_turn_complete=self.on_turn_complete
        )

        # =================================================
        # UI
        # =================================================

        self.window.mic_button.clicked.connect(
            self.toggle_microphone
        )

        self.window.send_button.clicked.connect(
            self.send_typed_message
        )

        self.window.message_input.returnPressed.connect(
            self.send_typed_message
        )

        # =================================================
        # MICROPHONE TIMER
        # =================================================

        self.timer = QTimer()

        self.timer.timeout.connect(
            self.process_microphone
        )

        self.timer.start(10)

        # =================================================
        # SHUTDOWN
        # =================================================

        self.app.aboutToQuit.connect(
            self.shutdown
        )

    # =====================================================
    # START
    # =====================================================

    def start(self):

        self.window.show()

        self.ai.start()

        return self.app.exec()

    # =====================================================
    # MICROPHONE
    # =====================================================

    def toggle_microphone(self):

        if self.shutting_down:

            return

        # =================================================
        # START LISTENING
        # =================================================

        if not self.listening:

            if not self.ai.connected:

                self.window.listenState.setText(
                    "WAITING FOR GEMINI..."
                )

                return

            try:

                self.microphone.start()

                self.listening = True

                self.window.set_listening(
                    True
                )

                self.window.listenState.setText(
                    "LISTENING"
                )

                try:

                    self.window.orb.set_state(
                        "listening"
                    )

                except Exception:

                    pass

            except Exception as e:

                print(
                    "Microphone start error:",
                    repr(e)
                )

                self.listening = False

                self.window.listenState.setText(
                    "MICROPHONE ERROR"
                )

        # =================================================
        # STOP LISTENING
        # =================================================

        else:

            self.listening = False

            try:

                self.microphone.stop()

            except Exception as e:

                print(
                    "Microphone stop error:",
                    repr(e)
                )

            self.window.set_listening(
                False
            )

            self.window.listenState.setText(
                "READY"
            )

            try:

                self.window.orb.set_state(
                    "idle"
                )

            except Exception:

                pass

    # =====================================================
    # MICROPHONE PROCESSING
    # =====================================================

    def process_microphone(self):

        if self.shutting_down:

            return

        if not self.listening:

            return

        if not self.ai.connected:

            return

        try:

            audio = self.microphone.read()

            if audio:

                self.ai.send_audio(
                    audio
                )

        except Exception as e:

            print(
                "Microphone processing error:",
                repr(e)
            )

    # =====================================================
    # GEMINI AUDIO CALLBACK
    # =====================================================

    def on_audio(self, audio):

        if self.shutting_down:

            return

        if not audio:

            return

        self.signals.audio.emit(
            audio
        )

    # =====================================================
    # HANDLE AUDIO
    # =====================================================

    def handle_audio(self, audio):

        if self.shutting_down:

            return

        if not audio:

            return

        try:

            self.speaker.play(
                audio
            )

            try:

                self.window.orb.set_state(
                    "speaking"
                )

            except Exception:

                pass

        except Exception as e:

            print(
                "Audio playback error:",
                repr(e)
            )

    # =====================================================
    # GEMINI TEXT CALLBACK
    # =====================================================

    def on_text(
        self,
        speaker,
        text
    ):

        if self.shutting_down:

            return

        if not text:

            return

        self.signals.text.emit(
            speaker,
            text
        )

    # =====================================================
    # HANDLE TEXT
    # =====================================================

    def handle_text(
        self,
        speaker,
        text
    ):

        if self.shutting_down:

            return

        if not text:

            return

        # =================================================
        # USER
        # =================================================

        if speaker == "YOU":

            # -------------------------------------------------
            # IMPORTANT:
            #
            # DO NOT reset the buffer here.
            #
            # Gemini sends transcription in chunks.
            #
            # Example:
            #
            # "tell"
            # " me"
            # " about"
            # " Python"
            #
            # We append everything.
            # -------------------------------------------------

            self.user_text_buffer += text

            print(
                "USER BUFFER:",
                self.user_text_buffer
            )

            self.window.update_transcript(
                "YOU",
                self.user_text_buffer
            )

            # Don't generate an image from every tiny
            # transcription chunk.
            #
            # Image detection is handled after the
            # complete turn.
            return

        # =================================================
        # AETHER
        # =================================================

        self.ai_text_buffer += text

        self.window.update_transcript(
            "AETHER",
            self.ai_text_buffer
        )

    # =====================================================
    # SEND TYPED MESSAGE
    # =====================================================

    def send_typed_message(self):

        if self.shutting_down:

            return

        text = (
            self.window.message_input
            .text()
            .strip()
        )

        if not text:

            return

        if not self.ai.connected:

            self.window.listenState.setText(
                "GEMINI NOT CONNECTED"
            )

            return

        # =================================================
        # CLEAR INPUT
        # =================================================

        self.window.message_input.clear()

        # =================================================
        # RESET CURRENT UI TURN
        # =================================================

        self.user_text_buffer = text

        self.ai_text_buffer = ""

        self.last_typed_message = text

        # =================================================
        # SHOW USER MESSAGE
        # =================================================

        self.window.update_transcript(
            "YOU",
            text
        )

        # =================================================
        # IMAGE REQUEST
        # =================================================

        if self.is_image_request(text):

            prompt = self.extract_image_prompt(
                text
            )

            if prompt:

                self.start_image_generation(
                    prompt
                )

                return

        # =================================================
        # NORMAL GEMINI MESSAGE
        # =================================================

        self.window.listenState.setText(
            "THINKING..."
        )

        try:

            self.window.orb.set_state(
                "thinking"
            )

        except Exception:

            pass

        self.ai.send_text(
            text
        )

    # =====================================================
    # IMAGE REQUEST DETECTION
    # =====================================================

    def is_image_request(
        self,
        text
    ):

        text = text.lower().strip()

        patterns = [

            r"\bgenerate\s+(an?\s+)?image\b",

            r"\bgenerate\s+(an?\s+)?picture\b",

            r"\bcreate\s+(an?\s+)?image\b",

            r"\bcreate\s+(an?\s+)?picture\b",

            r"\bmake\s+(an?\s+)?image\b",

            r"\bmake\s+(an?\s+)?picture\b",

            r"\bdraw\s+(an?\s+)?image\b",

            r"\bdraw\s+(an?\s+)?picture\b",

            r"\bshow\s+me\s+(an?\s+)?image\b",

            r"\bshow\s+me\s+(an?\s+)?picture\b",

            r"\bmake\s+me\s+(an?\s+)?image\b",

            r"\bmake\s+me\s+(an?\s+)?picture\b",

            r"\bgenerate\s+an?\b",

            r"\bcreate\s+an?\b",

            r"\bmake\s+an?\b",
        ]

        for pattern in patterns:

            if re.search(
                pattern,
                text
            ):

                return True

        return False

    # =====================================================
    # EXTRACT IMAGE PROMPT
    # =====================================================

    def extract_image_prompt(
        self,
        text
    ):

        text = text.strip()

        patterns = [

            r"generate\s+(?:an?\s+)?image\s+(?:of|about)\s+(.+)",

            r"generate\s+(?:an?\s+)?picture\s+(?:of|about)\s+(.+)",

            r"create\s+(?:an?\s+)?image\s+(?:of|about)\s+(.+)",

            r"create\s+(?:an?\s+)?picture\s+(?:of|about)\s+(.+)",

            r"make\s+(?:an?\s+)?image\s+(?:of|about)\s+(.+)",

            r"make\s+(?:an?\s+)?picture\s+(?:of|about)\s+(.+)",

            r"make\s+me\s+(?:an?\s+)?image\s+(?:of|about)\s+(.+)",

            r"make\s+me\s+(?:an?\s+)?picture\s+(?:of|about)\s+(.+)",

            r"draw\s+(?:an?\s+)?image\s+(?:of|about)\s+(.+)",

            r"draw\s+(?:an?\s+)?picture\s+(?:of|about)\s+(.+)",

            r"generate\s+(.+)",

            r"create\s+(.+)",

            r"make\s+(.+)",
        ]

        lower_text = text.lower()

        for pattern in patterns:

            match = re.search(
                pattern,
                lower_text,
                re.IGNORECASE
            )

            if match:

                prompt = text[
                    match.start(1):
                ].strip()

                prompt = prompt.rstrip(
                    ".?!"
                )

                if prompt:

                    return prompt

        return None

    # =====================================================
    # START IMAGE GENERATION
    # =====================================================

    def start_image_generation(
        self,
        prompt
    ):

        if self.shutting_down:

            return

        if self.generating_image:

            return

        self.generating_image = True

        print()
        print(
            "===================================="
        )

        print(
            "IMAGE REQUEST"
        )

        print(
            "Prompt:",
            prompt
        )

        print(
            "===================================="
        )

        try:

            self.window.listenState.setText(
                "GENERATING IMAGE..."
            )

        except Exception:

            pass

        try:

            self.window.update_transcript(
                "AETHER",
                "Generating image..."
            )

        except Exception:

            pass

        thread = threading.Thread(

            target=self._generate_image_worker,

            args=(prompt,),

            daemon=True,

            name="AetherImageGenerator"
        )

        thread.start()

    # =====================================================
    # IMAGE GENERATION WORKER
    # =====================================================

    def _generate_image_worker(
        self,
        prompt
    ):

        try:

            image_path = (
                self.image_generator.generate(
                    prompt
                )
            )

            if image_path:

                self.signals.image_ready.emit(
                    image_path
                )

            else:

                self.signals.image_error.emit(
                    "Gemini did not return an image."
                )

        except Exception as e:

            print(
                "Image generation error:",
                repr(e)
            )

            self.signals.image_error.emit(
                str(e)
            )

    # =====================================================
    # IMAGE READY
    # =====================================================

    def handle_image_ready(
        self,
        image_path
    ):

        if self.shutting_down:

            return

        self.generating_image = False

        print(
            "Image ready:",
            image_path
        )

        try:

            self.window.show_generated_image(
                image_path
            )

            self.window.listenState.setText(
                "IMAGE READY"
            )

        except AttributeError:

            print(
                "MainWindow is missing "
                "show_generated_image()"
            )

            self.window.listenState.setText(
                "IMAGE SAVED"
            )

        except Exception as e:

            print(
                "Image display error:",
                repr(e)
            )

            self.window.listenState.setText(
                "IMAGE READY"
            )

    # =====================================================
    # IMAGE ERROR
    # =====================================================

    def handle_image_error(
        self,
        error
    ):

        self.generating_image = False

        print(
            "Image generation failed:",
            error
        )

        if not self.shutting_down:

            self.window.listenState.setText(
                "IMAGE GENERATION ERROR"
            )

            try:

                self.window.update_transcript(
                    "AETHER",
                    "Sorry, I couldn't generate that image."
                )

            except Exception:

                pass

    # =====================================================
    # GEMINI TURN COMPLETE
    # =====================================================

    def on_turn_complete(self):

        if self.shutting_down:

            return

        self.signals.turn_complete.emit()

    # =====================================================
    # HANDLE TURN COMPLETE
    # =====================================================

    def handle_turn_complete(self):

        if self.shutting_down:

            return

        # =================================================
        # IMAGE DETECTION
        #
        # Only check the complete user message.
        # =================================================

        complete_user_text = (
            self.user_text_buffer.strip()
        )

        if complete_user_text:

            if self.is_image_request(
                complete_user_text
            ):

                prompt = self.extract_image_prompt(
                    complete_user_text
                )

                if prompt and not self.generating_image:

                    self.start_image_generation(
                        prompt
                    )

        # =================================================
        # FINISH TRANSCRIPT
        # =================================================

        try:

            self.window.finish_transcript()

        except Exception:

            pass

        # =================================================
        # RESET DISPLAY BUFFERS
        # =================================================

        self.user_text_buffer = ""

        self.ai_text_buffer = ""

        # =================================================
        # ORB
        # =================================================

        try:

            self.window.orb.set_state(
                "idle"
            )

        except Exception:

            pass

        # =================================================
        # STATUS
        # =================================================

        if self.generating_image:

            self.window.listenState.setText(
                "GENERATING IMAGE..."
            )

        elif self.listening:

            self.window.listenState.setText(
                "LISTENING"
            )

        else:

            self.window.listenState.setText(
                "READY"
            )

    # =====================================================
    # GEMINI STATUS CALLBACK
    # =====================================================

    def on_status(
        self,
        status
    ):

        if self.shutting_down:

            return

        self.signals.status.emit(
            status
        )

    # =====================================================
    # HANDLE STATUS
    # =====================================================

    def handle_status(
        self,
        status
    ):

        if self.shutting_down:

            return

        try:

            self.window.set_status(
                status
            )

        except Exception:

            pass

        if status == "CONNECTED":

            if self.generating_image:

                self.window.listenState.setText(
                    "GENERATING IMAGE..."
                )

            elif self.listening:

                self.window.listenState.setText(
                    "LISTENING"
                )

            else:

                self.window.listenState.setText(
                    "READY"
                )

        elif status == "CONNECTING...":

            self.window.listenState.setText(
                "CONNECTING..."
            )

        elif status == "RECONNECTING...":

            self.window.listenState.setText(
                "RECONNECTING..."
            )

        elif status == "CONNECTION ERROR":

            self.window.listenState.setText(
                "CONNECTION ERROR"
            )

    # =====================================================
    # SHUTDOWN
    # =====================================================

    def shutdown(self):

        if self.shutting_down:

            return

        self.shutting_down = True

        print(
            "Shutting down Aether..."
        )

        # =================================================
        # STOP TIMER
        # =================================================

        try:

            self.timer.stop()

        except Exception:

            pass

        # =================================================
        # STOP MICROPHONE
        # =================================================

        self.listening = False

        try:

            self.microphone.stop()

        except Exception as e:

            print(
                "Microphone shutdown:",
                repr(e)
            )

        # =================================================
        # STOP GEMINI
        # =================================================

        try:

            self.ai.stop()

        except Exception as e:

            print(
                "Gemini shutdown:",
                repr(e)
            )

        # =================================================
        # STOP SPEAKER
        # =================================================

        try:

            self.speaker.close()

        except Exception as e:

            print(
                "Speaker shutdown:",
                repr(e)
            )


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":

    program = AetherApp()

    sys.exit(
        program.start()
    )