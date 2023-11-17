# Description: 语音识别主程序

import speech_recognition as sr
r = sr.Recognizer()
with sr.Microphone() as source:
    print("请说话：")
    audio = r.listen(source)
    print("识别结果为："+r.recognize_google(audio, language='zh-CN'))   