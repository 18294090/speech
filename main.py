import websocket
import datetime
import hashlib
import base64
import hmac
import json
from urllib.parse import urlencode
import time
import ssl
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
import _thread as thread
import speech_recognition as sr
import pyttsx3
from api import getAnswer
import unicodedata
import os  

STATUS_FIRST_FRAME = 0  # 第一帧的标识
STATUS_CONTINUE_FRAME = 1  # 中间帧标识
STATUS_LAST_FRAME = 2  # 最后一帧的标识

reply=""
class Ws_Param(object):
    # 初始化
    def __init__(self, APPID, APIKey, APISecret, AudioFile):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.AudioFile = AudioFile
        # 公共参数(common)
        self.CommonArgs = {"app_id": self.APPID}
        # 业务参数(business)，更多个性化参数可在官网查看
        self.BusinessArgs = {"domain": "iat", "language": "zh_cn","dwa":"wpgs","accent": "mandarin", "vinfo":1,"vad_eos":10000}
    # 生成url
    def create_url(self):
        url = 'wss://ws-api.xfyun.cn/v2/iat'
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))
        # 拼接字符串
        signature_origin = "host: " + "ws-api.xfyun.cn" + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + "/v2/iat " + "HTTP/1.1"
        # 进行hmac-sha256进行加密
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()
        signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
            self.APIKey, "hmac-sha256", "host date request-line", signature_sha)
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        # 将请求的鉴权参数组合为字典
        v = {
            "authorization": authorization,
            "date": date,
            "host": "ws-api.xfyun.cn"
        }
        # 拼接鉴权参数，生成url
        url = url + '?' + urlencode(v)
        # print("date: ",date)
        # print("v: ",v)
        # 此处打印出建立连接时候的url,参考本demo的时候可取消上方打印的注释，比对相同参数时生成的url与自己代码生成的url是否一致
        # print('websocket url :', url)
        return url

# 收到websocket消息的处理
def on_message(ws, message):
    global reply
    try:
        code = json.loads(message)["code"]
        sid = json.loads(message)["sid"]
        if code != 0:
            errMsg = json.loads(message)["message"]
            print("sid:%s call error:%s code is:%s" % (sid, errMsg, code))
        else:
            data = json.loads(message)["data"]["result"]["ws"]
            char=data[0]["cw"][0]["w"][0]          
            if not unicodedata.category(char).startswith("P"):
                result = ""
                for i in data:
                    for w in i["cw"]:
                        result += w["w"]
            
                print("sid:%s call success!,data is:%s" % (sid, json.dumps(data, ensure_ascii=False)))
                print(result)
                reply=result
    except Exception as e:
        print("receive msg,but parse exception:", e)

# 收到websocket错误的处理
def on_error(ws, error):
    print("### error:", error)

# 收到websocket关闭的处理
def on_close(ws,a,b):
    print("### closed ###")


# 收到websocket连接建立的处理
def on_open(ws):
    def run(*args):
        frameSize = 8000  # 每一帧的音频大小
        intervel = 0.04  # 发送音频间隔(单位:s)
        status = STATUS_FIRST_FRAME  # 音频的状态信息，标识音频是第一帧，还是中间帧、最后一帧
        with open(wsParam.AudioFile, "rb") as fp:
            while True:
                buf = fp.read(frameSize)
                # 文件结束
                if not buf:
                    status = STATUS_LAST_FRAME
                # 第一帧处理
                # 发送第一帧音频，带business 参数
                # appid 必须带上，只需第一帧发送
                if status == STATUS_FIRST_FRAME:

                    d = {"common": wsParam.CommonArgs,
                         "business": wsParam.BusinessArgs,
                         "data": {"status": 0, "format": "audio/L16;rate=16000",
                                  "audio": str(base64.b64encode(buf), 'utf-8'),
                                  "encoding": "raw"}}
                    d = json.dumps(d)
                    ws.send(d)
                    status = STATUS_CONTINUE_FRAME
                # 中间帧处理
                elif status == STATUS_CONTINUE_FRAME:
                    d = {"data": {"status": 1, "format": "audio/L16;rate=16000",
                                  "audio": str(base64.b64encode(buf), 'utf-8'),
                                  "encoding": "raw"}}
                    ws.send(json.dumps(d))
                # 最后一帧处理
                elif status == STATUS_LAST_FRAME:
                    d = {"data": {"status": 2, "format": "audio/L16;rate=16000",
                                  "audio": str(base64.b64encode(buf), 'utf-8'),
                                  "encoding": "raw"}}
                    ws.send(json.dumps(d))
                    time.sleep(1)
                    fp.close()
                    break
                # 模拟音频采样间隔
                time.sleep(intervel)
        ws.close()
    thread.start_new_thread(run, ())

def listenMicrophone(): #监听麦克风并录音，保存为microphone-results.pcm
    r = sr.Recognizer()
    print("Listening...")
    #若十秒内无输入，则返回False，否则返回True
    with sr.Microphone() as source:
        audio = r.listen(source,phrase_time_limit=10)
    
    # 检查是否有声音输入
    if not audio.frame_data:
        return False

    #将audio数据转化为pcm文件格式
    with open("microphone-results.pcm", "wb") as f:
        f.write(audio.get_raw_data(convert_rate=16000, convert_width=2))
    
    return True

wsParam = Ws_Param(APPID='753802bb', APISecret='NTJlNmEyMWY3ZjQ0NjMwM2VhOTYzYzNm',
                       APIKey='1809a16e0ae7c917882bad17a3d4354b',
                       AudioFile='microphone-results.pcm')

def recognize_xunfei(): #调用讯飞语音识别API，返回识别结果    
    websocket.enableTrace(False)
    wsUrl = wsParam.create_url()
    ws = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error, on_close=on_close)
    ws.on_open = on_open
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
    return reply

engine = pyttsx3.init()

def speak(reply):#将讯飞火星的回复转为语音输出    
    engine.say(reply)
    engine.runAndWait()

def listen_and_recognize():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        audio = r.listen(source)
        try:
            text = r.recognize_sphinx(audio,language="zh-CN")
            print("You said:" + text)
            return text
        except sr.UnknownValueError:
            print("Sphinx could not understand audio")
        except sr.RequestError as e:
            print("Sphinx error; {0}".format(e))

def listen_for_wake_word(wake_word):
    global reply
    while True:
        if listenMicrophone():
            text=recognize_xunfei()
            print(text)
            
        if text == wake_word:
            os.remove("microphone-results.pcm")
            # 设置语速
            rate = engine.getProperty('rate')   # 获取当前的语速
            engine.setProperty('rate', rate-80)  # 将语速减少80
            engine.say("我在")
            engine.runAndWait()
            rate = engine.getProperty('rate')   # 获取当前的语速
            engine.setProperty('rate', rate+80)  
            #开始对话，当说出“再见”时或者超过10秒没有说话时结束对话
            while listenMicrophone():
                reply=""
                try:                        
                    reply=recognize_xunfei()
                    print("1",reply)
                    #删除"microphone-results.pcm文件
                    os.remove("microphone-results.pcm")
                    if '再见' in reply or reply=="":
                        engine.say("再见")
                        engine.runAndWait()
                        break
                    else:
                        text=getAnswer(reply)
                        print(text)
                        text=text[1]["content"]
                        engine.say(text)
                        engine.runAndWait()
                except:
                    print("没有听清楚")
                    break
                    
           
        
    
listen_for_wake_word("小鱼儿")