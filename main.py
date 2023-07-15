from google.cloud import speech
from google.cloud.speech import types
import pyaudio
from six.moves import queue
from pynput.keyboard import Listener, Key
import threading

# Audio recording parameters
STREAMING_LIMIT = 240000  # ~4 minutes
SAMPLE_RATE = 16000
CHUNK_SIZE = int(SAMPLE_RATE / 10)  # 100ms

class MicrophoneStream:
    def __init__(self, rate, chunk):
        self._rate = rate
        self._chunk = chunk
        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self._rate,
            input=True,
            frames_per_buffer=self._chunk,
            stream_callback=self._fill_buffer,
        )
        self.closed = False
        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        self._buff.queue.clear()
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]
            yield b''.join(data)

def listen_print_loop(responses, keyboard):
    for response in responses:
        if not response.results:
            continue
        result = response.results[0]
        if not result.alternatives:
            continue
        transcript = result.alternatives[0].transcript
        keyboard.type(transcript)

def start_streaming():
    client = speech.SpeechClient()
    config = types.RecognitionConfig(
        encoding=speech.enums.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=SAMPLE_RATE,
        language_code='en-US',
    )
    streaming_config = types.StreamingRecognitionConfig(
        config=config,
        interim_results=True,
    )

    with MicrophoneStream(SAMPLE_RATE, CHUNK_SIZE) as stream:
        audio_generator = stream.generator()
        requests = (types.StreamingRecognizeRequest(audio_content=content) for content in audio_generator)
        responses = client.streaming_recognize(streaming_config, requests)

        keyboard = Controller()
        threading.Thread(target=listen_print_loop, args=(responses, keyboard)).start()

def on_press(key):
    if key == Key.ctrl:
        print("Ctrl pressed, start recording.")
        threading.Thread(target=start_streaming).start()

def on_release(key):
    if key == Key.ctrl:
        print("Ctrl released, stop recording.")

with Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()
