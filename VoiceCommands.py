import speech_recognition as sr  # Module for getting microphone audio to text
import pyttsx3  # Module for computer speaking back to user


class CommandInputs:
    def __init__(self, pause_threshold=0.5):
        self.recognizer = sr.Recognizer()
        self.pause_duration = pause_threshold  # Time it gives to register a phrase once completed (in seconds)

    def get_voice_input(self):
        # obtain audio from the microphone
        with sr.Microphone() as source:
            print("Say something!")
            self.recognizer.pause_threshold = self.pause_duration
            audio = self.recognizer.listen(source)
        # recognize speech using Google Speech Recognition
        try:
            return self.recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            return "Audio not understood"
        except sr.RequestError as e:
            return "Could not request results from Google Speech Recognition service; {0}".format(e)


class CommandOutputs:
    def __init__(self):
        self.engine = pyttsx3.init('sapi5')
        self.voices = self.engine.getProperty('voices')
        self.engine.setProperty('voice', self.voices[0].id)

    def speak(self, audio):
        self.engine.say(audio)
        self.engine.runAndWait()

