# -*- coding: utf-8 -*-
import time
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from model import GenericAssistant
import requests
import webbrowser
import wikipedia
import pyttsx3
import speech_recognition as sr
import datetime
import os
import io
import sys

#set the encoding utf-8 instead of cp1252, because with cp1252 python cannot print text from wikipedia
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')


#set browser to open
opera = "C:\\Users\\Max\\AppData\\Local\\Programs\\Opera GX\\launcher.exe"
webbrowser.register("opera", None, webbrowser.BackgroundBrowser(opera))


#formatting output
ITALIC = '\033[3m'
END = '\033[0m'

#setup up stop words (words to remove from command)
stop_words = set(stopwords.words("english"))


def recognize_audio():
    """voice to text, after transcribing passes the result to "execute_command" function
    """
    #setup speech recognition
    r = sr.Recognizer()
    mic = sr.Microphone(sample_rate=48000, chunk_size=2048)
    try:
        with mic as source:
            print(f"\nlistening...")
            # r.energy_threshold = 100
            # r.speech_threshold = 0.5
            r.adjust_for_ambient_noise(source)
            r.pause_threshold = 0.6
            voice = r.listen(source)
            try:
                command = r.recognize_google(voice, language="en-us")
                print(f"[+] User: {command}")
                execute_command(command)
            except Exception as e:
                # print(e)
                print(f"[-] I cannot recognize")
    except Exception as e:
        print(e)
        print("[-] Error in recognize_audio") #if error with unavailable device reload audio services


def speak(text, language="en", sleep=0):
    """text to voice

    Args:
        text (str): text to say
        language (str, optional): choose the voice language. Defaults to "en".
    """
    #set up text to speech
    engine = pyttsx3.init()
    engine. setProperty("rate", 150)  # set the speed
    voices = engine.getProperty('voices')  # get all possible voices
    if language == "ru":  # jokes are in russian, so we need russian voice
        engine.setProperty('voice', voices[4].id)
    else:
        engine.setProperty('voice', voices[2].id)
    time.sleep(sleep)
    engine.say(text)
    engine.runAndWait()
    engine.stop()


def greeting(greeting_text):
    return greeting_text


def find_info(info):
    """find information in wikipedia

    Args:
        info (str): text from which stop words were removed

    Returns:
        str: one or two sentences from the wikipedia
    """
    try:
        text = wikipedia.summary(info, sentences=1, auto_suggest=False)
        if len(text) <= 60:
            text = wikipedia.summary(info, sentences=2, auto_suggest=False)
            return text
        return text
    except Exception as e:
        print(e)
        print("[-] Error in wikipedia")


def find_wiki_page(info):
    """sometimes python cannot print result from "find_info" function due to encoding,
        so it is necessary to open a page of wikipedia

    Args:
        info (str): text from which stop words were removed

    Returns:
        str: url of wikipedia page
    """
    result = wikipedia.page(info, auto_suggest=False)
    return result.url


def open_browser():
    """simply open browser
    """
    webbrowser.get("opera").open_new("google.com")


def open_webpage(page):
    """opens a given webpage

    Args:
        page (str): url of page
    """
    webbrowser.get("opera").open_new(page)


def get_joke():
    """simply getting a joke from websites with jokes
    """
    r = requests.get("http://rzhunemogu.ru/RandJSON.aspx?CType=1")
    # return r.text[12:-3] #such a strange return format because of json decode error, so we cut unnecessary symbols
    # print(r.text[12:-3])
    return r.text[12:-3].replace("\n", "")


def get_time():
    return datetime.datetime.now().strftime("%I. %M %p")


def get_date():
    return datetime.datetime.now().strftime("Today is %A, %d of %B, %Y")


def set_timer():
    pass


def execute_command(text=None):
    mappings = {"greeting": greeting, "search_in_google": find_info, # mapping are used to execute a function based on result of the chatbot.
                "browser": open_webpage, "youtube": open_webpage, 
                "joke": get_joke, "time":get_time, "date": get_date,
                "timer": set_timer}  #Pairs are tag*:function *tags are stored in intents.json file
    
    assistant = GenericAssistant(os.path.join(
        "intents.json"), intent_methods=mappings) #create an instance of the class

    try:
      assistant.load_model(model_name="model") #load model
    except:
        assistant.train_model() #if model not found create a new one
        assistant.save_model("model")

    function_to_exec = assistant.get_intent_method_name(text) # get a name of function to execute and tag
    print(f"def name:{function_to_exec[0]}, tag:{function_to_exec[1]}")

    match function_to_exec[0]: #based on the function name decide; do we want to execute it with/without command and etc
        case "find_info":
            word_tokens = word_tokenize(text) #split string to array of words
            filtered_list = [
                w for w in word_tokens if not w.lower() in stop_words] #delete stop words from the array
            filtered_sentence = ''.join(str(e+" ") for e in filtered_list) #create a string from array
            print(filtered_sentence[:-1])
            try:
                result = assistant.request_function_with_command(text, filtered_sentence[:-1]) #call the function with proper command 
                                                                                                #([:-1] is used because we have and extra space at the end)
                speak(result[1])
            except Exception as e: #sometime python gets error due to encoding, if so do not pring the text, just open the webpage
                print(e)
                print("[-] Error in encoding wikipedia text")
                open_webpage(find_wiki_page(filtered_sentence[:-1]))
        case "greeting":
            result = assistant.request_function_with_response(text) #call the function and pass as an argument to the function return of chatbot
            speak(result[0]) #speak return from chatbot
        case "open_webpage":
            match function_to_exec[1]: #based on tag open required webpages
                case 'youtube':
                    assistant.request_function_with_command(text, "youtube.com")
                case _: #case default
                    assistant.request_function_with_command(text, "google.com")
        case "get_joke":
            result = assistant.request_function_without_params(text)
            speak(result, "ru")
        case "get_time":
            result = assistant.request_function_without_params(text)
            speak(result)
        case "get_date":
            result = assistant.request_function_without_params(text)
            speak(result)

def main():
    # execute_command()
    speak("Setting up Jarvis")
    while True:
        recognize_audio()


if __name__ == '__main__':
    main()
