import speech_recognition as sr
from pynput.keyboard import Controller, Key, Listener
import keyboard
import threading

keyboard_controller = Controller()
rec = sr.Recognizer()

def listen_and_convert():
    with sr.Microphone() as source:
        print("Recording...")
        audio = rec.listen(source)

    try:
        text = rec.recognize_google(audio)
        print("Converting speech to text...")
        keyboard_controller.type(text)
    except Exception as e:
        print("Couldn't process the audio. Error: ", str(e))

def on_key_release(key):
    if key == Key.ctrl:
        print("Ctrl released, stop recording.")
        listen_and_convert()

def record_audio():
    while True:
        if keyboard.is_pressed('ctrl'):
            print("Ctrl pressed, start recording.")
            threading.Thread(target=listen_and_convert).start()
        while keyboard.is_pressed('ctrl'):
            pass

record_audio()