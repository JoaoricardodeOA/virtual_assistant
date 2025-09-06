# ===== imports =====
import os
from datetime import datetime
import webbrowser
import pyjokes
import wikipedia
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import speech_recognition as sr
from gtts import gTTS
from pygame import mixer
from send2trash import send2trash
import time
import psutil
import requests


# ===== constants =====
FS = 16000
DURATION = 5
MIC_DEVICE = "sof-hda-dsp: - (hw:1,7)"  

# ===== speak function =====
def speak(text):
    tts = gTTS(text=text, lang='en')
    filename = "voice.mp3"
    try:
        os.remove(filename)
    except OSError:
        pass
    tts.save(filename)
    mixer.init()
    mixer.music.load(filename)
    mixer.music.play()
    while mixer.music.get_busy():
        time.sleep(0.1)

# ===== real-time listening function =====
def listen_and_respond():
    r = sr.Recognizer()

    while True:
        print("Listening...")
        audio = sd.rec(int(DURATION*FS), samplerate=FS, channels=1, device=MIC_DEVICE)
        sd.wait()
        audio_int16 = np.int16(audio * 32767)
        wav.write("audio.wav", FS, audio_int16)

        # reproduzir a gravação imediatamente
        mixer.init()
        mixer.music.load("audio.wav")
        mixer.music.play()
        while mixer.music.get_busy():
            time.sleep(0.1)

        # reconhecer comandos
        with sr.AudioFile("audio.wav") as source:
            audio_data = r.record(source)
            try:
                text = r.recognize_google(audio_data).lower()
                print("Heard:", text)
                respond(text)
            except sr.UnknownValueError:
                print("Could not understand audio")
            except sr.RequestError:
                print("Speech service unavailable")


# ===== respond function =====
def respond(text):
    if 'youtube' in text:
        speak("What do you want to search for?")
        keyword = listen_once()
        if keyword:
            url = f"https://www.youtube.com/results?search_query={keyword}"
            webbrowser.get().open(url)
            speak(f"Here is what I found for {keyword} on YouTube.")
    
    elif 'open browser' in text:
        speak("Opening your default web browser")
        webbrowser.get().open("https://www.google.com")

    elif 'open notepad' in text:
        speak("Opening a text editor")
        os.system("gedit &") 

    elif 'calculator' in text:
        speak("Opening calculator")
        os.system("gnome-calculator &")

    elif 'battery' in text:
        battery = psutil.sensors_battery()
        if battery is None:
            speak("Battery information is not available on this system.")
            return

        percent = round(battery.percent,2)
        plugged = round(battery.power_plugged,2)
        if plugged:
            speak(f"The battery is at {percent}% and charging.")
        else:
            speak(f"The battery is at {percent}% and not charging.")

    elif 'fact' in text:
        try:
            response = requests.get("https://uselessfacts.jsph.pl/random.json?language=en")
            response.raise_for_status() 
            fact = response.json().get("text", "No fact found.")
            speak(f"Here's a fun fact: {fact}")
        except requests.exceptions.RequestException as e:
            speak("Sorry, I don´t have a fun fact at the moment.")
            print(f"Error: {e}")

    elif 'find file' in text or 'search file' in text:
        speak("What is the name of the file you want to find?")
        file_name = listen_once()
        if file_name:
            search_path = os.path.expanduser("~")  # User folder
            matches = []
            for root, dirs, files in os.walk(search_path):
                for f in files:
                    if file_name.lower() in f.lower():
                        matches.append(os.path.join(root, f))
            
            if matches:
                speak(f"I found {len(matches)} file(s) named {file_name}. Here are the first 5:")
                for path in matches[:5]:  # Only speak first 5 results
                    print(path)
                    speak(path)
            else:
                speak(f"No files named {file_name} were found.")

    elif 'search' in text:
        speak("What do you want to search for?")
        query = listen_once()
        if query:
            try:
                result = wikipedia.summary(query, sentences=3)
                speak("According to Wikipedia")
                print(result)
                speak(result)
            except wikipedia.exceptions.DisambiguationError:
                speak("Your query is ambiguous. Please be more specific.")
            except wikipedia.exceptions.PageError:
                speak("Sorry, I could not find anything on Wikipedia.")

    elif 'joke' in text:
        speak(pyjokes.get_joke())

    elif 'empty recycle bin' in text:
        recycle_bin_path = os.path.expanduser("~/.local/share/Trash/files")
        for item in os.listdir(recycle_bin_path):
            send2trash(os.path.join(recycle_bin_path, item))
        speak("Recycle bin emptied.")

    elif 'what time' in text:
        strTime = datetime.now().strftime("%H:%M %p")
        print(strTime)
        speak(strTime)


    elif 'exit' in text:
        speak("Goodbye, till next time!")
        exit()

# ===== helper: single short listen =====
def listen_once(duration=DURATION):
    r = sr.Recognizer()
    audio = sd.rec(int(duration*FS), samplerate=FS, channels=1, device=MIC_DEVICE)
    sd.wait()
    audio_int16 = np.int16(audio * 32767)
    wav.write("audio.wav", FS, audio_int16)

    # reproduzir o áudio capturado
    mixer.init()
    mixer.music.load("audio.wav")
    mixer.music.play()
    while mixer.music.get_busy():
        time.sleep(0.1)

    with sr.AudioFile("audio.wav") as source:
        audio_data = r.record(source)
        try:
            return r.recognize_google(audio_data).lower()
        except:
            return ""

# ===== main loop =====
if __name__ == "__main__":
    listen_and_respond()
