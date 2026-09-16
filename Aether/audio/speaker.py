import threading

import numpy as np
import sounddevice as sd


class Speaker:

    def __init__(self, sample_rate=24000):

        self.sample_rate = sample_rate

        self.running = True

        self.lock = threading.Lock()

        # Continuous PCM buffer
        self.buffer = bytearray()

        self.stream = sd.OutputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="int16",
            blocksize=960,
            callback=self._callback
        )

        self.stream.start()

        print("Speaker started")

    # =====================================================
    # AUDIO CALLBACK
    # =====================================================

    def _callback(
        self,
        outdata,
        frames,
        time_info,
        status
    ):

        if status:

            print(
                "Speaker:",
                status
            )

        outdata.fill(0)

        if not self.running:

            return

        required_bytes = frames * 2

        with self.lock:

            available = len(self.buffer)

            if available == 0:

                return

            amount = min(
                required_bytes,
                available
            )

            audio_bytes = self.buffer[
                :amount
            ]

            del self.buffer[
                :amount
            ]

        try:

            audio = np.frombuffer(
                audio_bytes,
                dtype=np.int16
            )

            samples = min(
                len(audio),
                frames
            )

            outdata[
                :samples,
                0
            ] = audio[
                :samples
            ]

        except Exception as e:

            print(
                "Speaker callback error:",
                repr(e)
            )

    # =====================================================
    # PLAY AUDIO
    # =====================================================

    def play(self, audio_bytes):

        if not self.running:

            return

        if not audio_bytes:

            return

        with self.lock:

            self.buffer.extend(
                audio_bytes
            )

    # =====================================================
    # CLEAR AUDIO
    # =====================================================

    def clear(self):

        with self.lock:

            self.buffer.clear()

    # =====================================================
    # CLOSE
    # =====================================================

    def close(self):

        with self.lock:

            if not self.running:

                return

            self.running = False

            self.buffer.clear()

        try:

            self.stream.stop()

        except Exception:
            pass

        try:

            self.stream.close()

        except Exception:
            pass

        self.stream = None

        print(
            "Speaker stopped"
        )