import asyncio
import threading

from google import genai
from google.genai import types

from config import (
    GEMINI_API_KEY,
    MODEL,
    VOICE_NAME,
    SYSTEM_PROMPT
)


class GeminiLive:

    def __init__(
        self,
        on_audio=None,
        on_text=None,
        on_status=None,
        on_turn_complete=None
    ):

        # =================================================
        # CALLBACKS
        # =================================================

        self.on_audio = on_audio
        self.on_text = on_text
        self.on_status = on_status
        self.on_turn_complete = on_turn_complete

        # =================================================
        # GEMINI CLIENT
        # =================================================

        self.client = genai.Client(
            api_key=GEMINI_API_KEY
        )

        # =================================================
        # ASYNC STATE
        # =================================================

        self.loop = None
        self.session = None
        self.thread = None

        # =================================================
        # CONNECTION STATE
        # =================================================

        self.running = False
        self.connected = False

        self.connection_lock = threading.Lock()

        self.connecting = False

        # =================================================
        # CONVERSATION MEMORY
        # =================================================
        #
        # This stores completed conversation turns.
        #
        # Example:
        #
        # user  -> Tell me about Python
        # model -> Python is a programming language...
        # user  -> Explain it briefly
        #
        # Gemini can therefore understand "it".
        # =================================================

        self.history = []

        # Maximum number of messages kept in active context.
        # 20 messages = roughly 10 user/model exchanges.
        self.max_history = 20

        # =================================================
        # CURRENT TURN BUFFERS
        # =================================================

        self.current_user_text = ""
        self.current_model_text = ""

    # =====================================================
    # START
    # =====================================================

    def start(self):

        if self.thread:

            if self.thread.is_alive():

                return

        self.running = True

        self.thread = threading.Thread(
            target=self._thread_main,
            daemon=True,
            name="GeminiLive"
        )

        self.thread.start()

    # =====================================================
    # THREAD MAIN
    # =====================================================

    def _thread_main(self):

        self.loop = asyncio.new_event_loop()

        asyncio.set_event_loop(
            self.loop
        )

        try:

            self.loop.run_until_complete(
                self.connection_loop()
            )

        except Exception as e:

            if self.running:

                print(
                    "Gemini thread error:",
                    repr(e)
                )

        finally:

            try:

                pending = asyncio.all_tasks(
                    self.loop
                )

                for task in pending:

                    task.cancel()

            except Exception:
                pass

            try:

                self.loop.close()

            except Exception:
                pass

            self.loop = None

    # =====================================================
    # CONNECTION LOOP
    # =====================================================

    async def connection_loop(self):

        while self.running:

            try:

                self.connecting = True

                await self.connect_session()

            except asyncio.CancelledError:

                break

            except Exception as e:

                self.connected = False
                self.session = None

                print(
                    "Gemini connection error:",
                    repr(e)
                )

                self.status(
                    "CONNECTION ERROR"
                )

            finally:

                self.connecting = False
                self.connected = False
                self.session = None

            if not self.running:

                break

            self.status(
                "RECONNECTING..."
            )

            await asyncio.sleep(2)

    # =====================================================
    # CONNECT SESSION
    # =====================================================

    async def connect_session(self):

        self.status(
            "CONNECTING..."
        )

        config = types.LiveConnectConfig(

            # Gemini sends audio back
            response_modalities=[
                "AUDIO"
            ],

            # Aether personality
            system_instruction=SYSTEM_PROMPT,

            # Voice
            speech_config=types.SpeechConfig(

                voice_config=types.VoiceConfig(

                    prebuilt_voice_config=
                    types.PrebuiltVoiceConfig(

                        voice_name=VOICE_NAME
                    )
                )
            ),

            # User speech -> text
            input_audio_transcription=(
                types.AudioTranscriptionConfig()
            ),

            # Aether speech -> text
            output_audio_transcription=(
                types.AudioTranscriptionConfig()
            )
        )

        print(
            "Connecting to Gemini Live..."
        )

        async with self.client.aio.live.connect(

            model=MODEL,

            config=config

        ) as session:

            self.session = session

            self.connected = True

            print(
                "Gemini Live connected"
            )

            self.status(
                "CONNECTED"
            )

            # =================================================
            # RESTORE PREVIOUS CONTEXT
            # =================================================

            await self.restore_context()

            try:

                await self.receive_loop()

            except asyncio.CancelledError:

                pass

            except Exception as e:

                if self.running:

                    print(
                        "Gemini receive error:",
                        repr(e)
                    )

            finally:

                self.connected = False

                self.session = None

                print(
                    "Gemini Live session closed"
                )

    # =====================================================
    # RESTORE CONTEXT
    # =====================================================

    async def restore_context(self):

        if not self.session:

            return

        if not self.history:

            print(
                "No previous conversation context."
            )

            return

        try:

            turns = []

            for message in self.history:

                role = message.get(
                    "role"
                )

                text = message.get(
                    "text"
                )

                if not text:

                    continue

                if role == "user":

                    turns.append(
                        types.Content(
                            role="user",
                            parts=[
                                types.Part(
                                    text=text
                                )
                            ]
                        )
                    )

                elif role == "model":

                    turns.append(
                        types.Content(
                            role="model",
                            parts=[
                                types.Part(
                                    text=text
                                )
                            ]
                        )
                    )

            if not turns:

                return

            print(
                f"Restoring {len(turns)} conversation messages..."
            )

            # Add history without asking Gemini
            # to generate a response yet.
            await self.session.send_client_content(

                turns=turns,

                turn_complete=False
            )

            print(
                "Conversation context restored."
            )

        except Exception as e:

            print(
                "Context restore error:",
                repr(e)
            )

    # =====================================================
    # RECEIVE LOOP
    # =====================================================

    async def receive_loop(self):

        if not self.session:

            return

        async for response in self.session.receive():

            if not self.running:

                break

            if response is None:

                continue

            server_content = (
                response.server_content
            )

            if server_content is None:

                continue

            # =================================================
            # MODEL TURN
            # =================================================

            model_turn = (
                server_content.model_turn
            )

            if model_turn:

                for part in model_turn.parts:

                    # =========================================
                    # AUDIO
                    # =========================================

                    if part.inline_data:

                        audio_data = (
                            part.inline_data.data
                        )

                        if audio_data:

                            self.audio(
                                audio_data
                            )

            # =================================================
            # USER TRANSCRIPTION
            # =================================================

            input_transcription = (
                server_content.input_transcription
            )

            if input_transcription:

                text = (
                    input_transcription.text
                )

                if text:

                    # -----------------------------------------
                    # IMPORTANT
                    #
                    # Transcription arrives in chunks.
                    # Don't treat every chunk as a new message.
                    # -----------------------------------------

                    self.current_user_text += text

                    print(
                        "YOU:",
                        text
                    )

                    # UI still receives streaming text
                    self.text(
                        "YOU",
                        text
                    )

            # =================================================
            # AETHER TRANSCRIPTION
            # =================================================

            output_transcription = (
                server_content.output_transcription
            )

            if output_transcription:

                text = (
                    output_transcription.text
                )

                if text:

                    # -----------------------------------------
                    # Same thing for Aether.
                    # Gemini may send multiple chunks.
                    # -----------------------------------------

                    self.current_model_text += text

                    print(
                        "AETHER:",
                        text
                    )

                    self.text(
                        "AETHER",
                        text
                    )

            # =================================================
            # TURN COMPLETE
            # =================================================

            if server_content.turn_complete:

                self.commit_turn()

                self.turn_complete()

                self.status(
                    "LISTENING"
                )

    # =====================================================
    # COMMIT COMPLETED TURN
    # =====================================================

    def commit_turn(self):

        user_text = (
            self.current_user_text.strip()
        )

        model_text = (
            self.current_model_text.strip()
        )

        # =================================================
        # SAVE USER MESSAGE
        # =================================================

        if user_text:

            self.history.append({

                "role": "user",

                "text": user_text

            })

        # =================================================
        # SAVE AETHER RESPONSE
        # =================================================

        if model_text:

            self.history.append({

                "role": "model",

                "text": model_text

            })

        # =================================================
        # LIMIT HISTORY
        # =================================================

        if len(self.history) > self.max_history:

            self.history = (
                self.history[-self.max_history:]
            )

        print(
            "Conversation context:",
            len(self.history),
            "messages"
        )

        # =================================================
        # RESET TURN BUFFERS
        # =================================================

        self.current_user_text = ""

        self.current_model_text = ""

    # =====================================================
    # SEND AUDIO
    # =====================================================

    def send_audio(self, audio_bytes):

        if not audio_bytes:

            return

        if not self.running:

            return

        if not self.connected:

            return

        if not self.session:

            return

        if not self.loop:

            return

        try:

            asyncio.run_coroutine_threadsafe(

                self._send_audio(
                    audio_bytes
                ),

                self.loop
            )

        except Exception as e:

            if self.running:

                print(
                    "Audio scheduling error:",
                    repr(e)
                )

    # =====================================================
    # SEND AUDIO ASYNC
    # =====================================================

    async def _send_audio(
        self,
        audio_bytes
    ):

        session = self.session

        if session is None:

            return

        if not self.connected:

            return

        try:

            await session.send_realtime_input(

                audio=types.Blob(

                    data=audio_bytes,

                    mime_type="audio/pcm;rate=16000"
                )
            )

        except asyncio.CancelledError:

            pass

        except Exception as e:

            if self.running:

                print(
                    "Audio send error:",
                    repr(e)
                )

                self.connected = False

    # =====================================================
    # SEND TEXT
    # =====================================================

    def send_text(self, text):

        if not text:

            return

        text = text.strip()

        if not text:

            return

        if not self.running:

            return

        if not self.connected:

            return

        if not self.session:

            return

        if not self.loop:

            return

        try:

            asyncio.run_coroutine_threadsafe(

                self._send_text(
                    text
                ),

                self.loop
            )

        except Exception as e:

            print(
                "Text scheduling error:",
                repr(e)
            )

    # =====================================================
    # SEND TEXT ASYNC
    # =====================================================

    async def _send_text(
        self,
        text
    ):

        session = self.session

        if session is None:

            return

        try:

            # =================================================
            # IMPORTANT
            #
            # Use send_client_content instead of
            # send_realtime_input for typed messages.
            #
            # This explicitly creates a user turn and
            # preserves deterministic conversation order.
            # =================================================

            await session.send_client_content(

                turns=types.Content(

                    role="user",

                    parts=[
                        types.Part(
                            text=text
                        )
                    ]
                ),

                turn_complete=True
            )

            print(
                "TEXT SENT:",
                text
            )

        except asyncio.CancelledError:

            pass

        except Exception as e:

            if self.running:

                print(
                    "Text send error:",
                    repr(e)
                )

    # =====================================================
    # AUDIO CALLBACK
    # =====================================================

    def audio(
        self,
        audio_data
    ):

        if not self.running:

            return

        if not audio_data:

            return

        if self.on_audio:

            try:

                self.on_audio(
                    audio_data
                )

            except Exception as e:

                print(
                    "Audio callback error:",
                    repr(e)
                )

    # =====================================================
    # TEXT CALLBACK
    # =====================================================

    def text(
        self,
        speaker,
        text
    ):

        if not self.running:

            return

        if not text:

            return

        if self.on_text:

            try:

                self.on_text(
                    speaker,
                    text
                )

            except Exception as e:

                print(
                    "Text callback error:",
                    repr(e)
                )

    # =====================================================
    # STATUS CALLBACK
    # =====================================================

    def status(
        self,
        message
    ):

        if self.on_status:

            try:

                self.on_status(
                    message
                )

            except Exception as e:

                print(
                    "Status callback error:",
                    repr(e)
                )

    # =====================================================
    # TURN COMPLETE CALLBACK
    # =====================================================

    def turn_complete(self):

        if self.on_turn_complete:

            try:

                self.on_turn_complete()

            except Exception as e:

                print(
                    "Turn callback error:",
                    repr(e)
                )

    # =====================================================
    # CLEAR CONVERSATION
    # =====================================================

    def clear_history(self):

        self.history.clear()

        self.current_user_text = ""

        self.current_model_text = ""

        print(
            "Aether conversation memory cleared."
        )

    # =====================================================
    # STOP
    # =====================================================

    def stop(self):

        self.running = False

        self.connected = False

        self.session = None

        print(
            "Gemini Live stopped"
        )