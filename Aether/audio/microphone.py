import queue
import threading

import numpy as np
import sounddevice as sd


class Microphone:

    def __init__(self, sample_rate=16000, channels=1):
        self.sample_rate = sample_rate
        self.channels = channels

        self.audio_queue = queue.Queue()

        self.running = False
        self.stream = None

    def _callback(self, indata, frames, time, status):

        if status:
            print("Microphone:", status)

        if self.running:
            audio = indata.copy()

            self.audio_queue.put(
                audio.astype(np.int16).tobytes()
            )

    def start(self):

        if self.running:
            return

        self.running = True

        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="int16",
            blocksize=1600,
            callback=self._callback
        )

        self.stream.start()

        print("Microphone started")

    def read(self):

        try:
            return self.audio_queue.get(
                timeout=0.1
            )

        except queue.Empty:
            return None

    def stop(self):

        self.running = False

        if self.stream:

            self.stream.stop()
            self.stream.close()

            self.stream = None

        print("Microphone stopped")