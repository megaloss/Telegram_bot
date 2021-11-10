#! /usr/bin/env python
import os
import urllib.request
import telebot
from pydub import AudioSegment
import speech_recognition as sr
import pytesseract
from PIL import Image
from datetime import datetime

ALLOWED_IDS = [1928616895,1968077769]
SUPPORTED_LANGS_TESS = {'en': 'eng',
                        'ru': 'rus',
                        'nl': 'nld'}
SUPPORTED_LANGS_SPEECH = {'en': 'en-GB',
                          'uk': 'en-GB',
                          'us': 'en-US',
                          'ru': 'ru',
                          'nl': 'nl-NL'}

lang = {'1928616895':'en',
        '1968077769':'en'}

API_KEY = os.environ['TELE_API']
if not API_KEY:
    print('No API KEY provided !')
    exit(2)
bot = telebot.TeleBot(API_KEY)
#print(API_KEY)
print (datetime.now(), ' Bot is running... ')

def recognize(file, lang):
    text = pytesseract.image_to_string(Image.open(file), lang=SUPPORTED_LANGS_TESS[lang])
    os.remove(file)
    return text


def transcribe(file, lang='en', chunksize=60000):
    # 0: load
    sound = AudioSegment.from_ogg(file)

    # 1: split file into 60s chunks
    def divide_chunks(sound, chunksize):
        for i in range(0, len(sound), chunksize):
            yield sound[i:i + chunksize]

    chunks = list(divide_chunks(sound, chunksize))

    r = sr.Recognizer()
    # 2: per chunk, save to wav, then read and run through recognize_google()
    string = ''
    for index, chunk in enumerate(chunks):
        # TODO io.BytesIO()
        chunk.export('delete_me.wav', format='wav')
        with sr.AudioFile('delete_me.wav') as source:
            audio = r.record(source)
        # s = r.recognize_sphinx(audio, language=SUPPORTED_LANGS_SPEECH[lang])
        s = r.recognize_google(audio, language=SUPPORTED_LANGS_SPEECH[lang])
        string += s
    os.remove(file)
    return string

@bot.message_handler(commands=['en', 'ru', 'nl', 'us', 'gb', 'En', 'Ru', 'Nl', 'Us','Gb','lng'])
def greet(message):
    global lang
    text = message.text[1:].lower()
    if text in SUPPORTED_LANGS_SPEECH:
        bot.reply_to(message, f"Switching language to {text}. ")
        lang[str(message.from_user.id)] = text
    else:
        bot.reply_to(message, f"Working language is {lang[str(message.from_user.id)]}. ")


@bot.message_handler()  # commands=['Greet','greet','hi','Hi','hello','Hello'])
def greet(message):
    bot.reply_to(message, f"hi, {message.from_user.first_name} ! Your id is: {message.from_user.id}")




@bot.message_handler(content_types=['photo'])
def photo(message):
    #    if message.from_user.id not in ALLOWED_IDS:
    #        return
    bot.reply_to(message, 'Got photo. recognition started...')
    #lang = 'en'
    if message.caption and message.caption.lower() in SUPPORTED_LANGS_TESS:
        lang[str(message.from_user.id)] = message.caption.lower()
    try:
        file_location = message.photo[-1].file_id
        file_info = bot.get_file_url(file_location)
    except Exception as e:
        bot.reply_to(message, e)
        return
    file_name = file_info.split('/')[-1]
    urllib.request.urlretrieve(file_info, file_name)
    text = recognize(file_name, lang[str(message.from_user.id)])
    print (datetime.now(), ' recognizing ', file_name)
    if text:
        bot.reply_to(message, text)
    else:
        bot.reply_to(message, 'Sorry, no text found')


@bot.message_handler(content_types=['audio', 'voice'])
def recording(message):
    #    if message.from_user.id not in ALLOWED_IDS:
    #        return
    bot.reply_to(message, 'Got audio to transcribe. Working... ')

    try:
        file_location = message.audio.file_id if message.content_type == 'audio' else message.voice.file_id
        file_info = bot.get_file_url(file_location)
        print(file_info)
    except Exception as e:
        print(e)
        bot.reply_to(message, e)
        return

    file_name = file_info.split('/')[-1]
    print(datetime.now(), ' transcribing ', file_name)
    urllib.request.urlretrieve(file_info, file_name)

    text = transcribe(file_name,lang=lang[str(message.from_user.id)])
    if text:
        bot.reply_to(message, text)
    else:
        bot.reply_to(message, 'Sorry, no text recognized')


bot.infinity_polling(timeout=20, long_polling_timeout = 5)
#bot.infinity_polling(timeout=10, long_polling_timeout = 5)


