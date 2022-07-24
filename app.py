# -*- coding: utf-8 -*-

import os
import datetime
import logging
import uuid
import socketio
from aiohttp import web
from rasa_sdk.executor import ActionExecutor
from rasa_sdk.interfaces import ActionExecutionRejection

import bangla
from banglanum2words import num_convert

import json
import pprint
import re     

import num_to_int
                                           
import sys
sys.path.append('.')

ASK_PIN='আপনার চার ডিজিটের টি পিন নাম্বার বলুন'
ASK_PHONE ='আপনার এগার সংখ্যার ফোন নাম্বার বলুন'
ASK_MONEY='টাকার পরিমাণ বলুন'
ASK_OK='ঠিক আছে'
ASK_CARD = 'আপনার দশ ডিজিট এর কার্ড নাম্বার বলুন'
ASK_HOME = 'স্যার, আপনার হাউজ নাম্বার, বলুন'
ASK_ROAD = 'স্যার, আপনার রোড নাম্বার, বলুন'
ASK_POST_CODE = 'আপনার, পোস্টাল কোড বলুন'

PHONE_BOOK={
    "102": "মিসটার  শাহাদাত",
    "103": "মিসটার  আনিস",
    "201": " ",
    "202": "মিসটার রিফাত",
    "195": "মিসটার জাহিদ",
    "01713384891": "মিসটার প্রিন্স",
    "01886384891": "মিসটার প্রিন্স",
    "01730796712": "মিসটার তুর্জো",
    "01714020387": "মিসটার উজ্জল",
    "01714016458": "মিসটার ইব্রাহিম"
}
from utils.bot_factory import BotFactory

from utils.converter import BnToEn_Word, BnToEn

logging.basicConfig(level=logging.WARN,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M')


# Action executor config
executor = ActionExecutor()
executor.register_package('actions')


# Load JS File
async def js(request):
    return web.FileResponse('templates/index.js')
    
    
# Home page
async def index(request):
    index_file = open('templates/index.html')
    print(request)
    return web.Response(body=index_file.read().encode('utf-8'), headers={'content-type': 'text/html'})              
        
def isASCII(data):
    try:
        data.encode().decode('ASCII')
    except UnicodeDecodeError:
        return False
    else:
        return True
        
def getNumber(string):
    number=['জিরো','ওয়ান','টু','থ্রি','ফোর','ফাইভ','সিক্স','সেভেন','এইট','নাইন']
    st=string.split(' ')
    wr=''
    #for i,w in enumerate(st):
    #    if(w in number):            
    #        wr=wr+str(number.index(w))
    #else:
    #    wr=wr+' '+w
        
    for i,w in enumerate(st):
            for j, n in enumerate(number):
                if(w==n):
                    if(st[i-1]=='ডাবল' or st[i-1]=='ডবল'):
                        wr=wr+str(j)
                    if(st[i-1]=='ট্রিপল'):
                        wr=wr+str(j)+str(j)
                    wr=wr+str(j)
    print('##############################')
    print(wr)
    if(len(wr)>1):
        #if(len(wr)>4 and len(wr)<=6):
        #    print('########################')
        #    return wr[:4]
        #if(len(wr)>8):
        #    print('########################')
        #    return wr[:8]
        return wr
    else:
      return string
        
# Action endpoint
resposnse_text=['s']
resposnse_text_dict={
    "s": ['s']
}
resposnse_text_dict_web={
    "default": ['s']
}
fallback_counter={}
fallback_response=['আমি আপনার বার্তা টা বুঝতে পারি নি। আপনি কি অন্যভাবে বলতে পারবেন প্লিজ?','স্যার, কী ওয়ার্ড ব্যাবহার করলে আপনাকে সাহায্য করতে আমার জন্য সহজ হবে।','কথাটি বুঝতে পারিনি। দয়া করে পুনরায় বলুন','দুঃখিত আপনার কথাটি শুনতে পায়নি','পুনরায় বলবেন প্লিজ?','আপনার কথাটি বুঝতে পারিনি। পুনরায় বলুন','আপনি প্রাসঙ্গিক কিছু বলুন']
async def webhook(request):
    """Webhook to retrieve action calls."""
    
    try:
    	action_call = await request.json()
    	data = action_call
    except Exception as ex:
    	action_call = await request.post()
    	data = {"sender": '', "message": '', "metadata": ''}
    	for i in action_call:
    		if(i==0):
    			data['sender'] = action_call[i]
    		if(i==1):
    			data['message'] = action_call[i]
    		if(i==2):
    			data['metadata'] = action_call[i]
    	
    print("Request:")
    print(action_call)
    lang='en'
    if(data['metadata']=='en'):
        lang='en'
    else:
        lang='bn'
    

    lang='bn'
    
    original_string=data['message']
    print('original test:'+str(original_string))
    number_string=getNumber(data['message'])
    number_string=" ".join(number_string.split())
    print(number_string)
    #number_string=getAmount(number_string)
    #new_number_string=bangla.convert_english_digit_to_bangla_digit(str(number_string))
    
    global resposnse_text
    global resposnse_text_dict

    if(data['sender'] not in resposnse_text_dict):
        resposnse_text_dict[data['sender']]=['s']
    
    if(data['sender'] not in fallback_counter):
        fallback_counter[data['sender']]=0
    
    if(len(number_string)>0):
        data['message']=number_string
             
    string_to_num=num_to_int.spell_to_int(data['message'])
    tt=data['message'].split()
    if('পয়সা' in tt):
        ind=tt.index('পয়সা')
        float_num=num_to_int.spell_to_int(tt[ind-1])
        string_to_num=str(string_to_num)+'.'+float_num
        
    data['message']=string_to_num
    #for dollar rate manupulation
    if('রেট' in data['message'] or 'ডলার' in data['message'] or 'এক্সচেঞ্জ' in data['message']):
        print('changed text')
        data['message']='আজকে ডলার এর রেট কত'
    #for card limit manupulation
    if('ব্যালেন্স' in data['message'] and 'কার্ড' in data['message']):
        print('changed text')
        data['message']='আমার ক্রেডিট কার্ড এর লিমিট কত টাকা'
    #for OK statement
    # if(ASK_OK in data['message']):
    #     print('changed text')
    #     data['message']=ASK_OK


    # load manupulation
    if(resposnse_text_dict[data['sender']][-1]=='আপনি কি লোন ডিউ, কত টাকা বাকি আছে বা পরবর্তী কিস্তি কত দিবেন তা জানতে চাচ্ছেন।'):
    	print('changed text')
    	data['message']='ঠিক আছে'

    #for PIN manupulation
    if(resposnse_text_dict[data['sender']][-1]=='আপনার চার ডিজিটের টি পিন নাম্বার বলুন' or resposnse_text_dict[data['sender']][-1]=='আপনার টি পিন নম্বরটি বলুন' or resposnse_text_dict[data['sender']][-1]=='স্যার, আপনার চার ডিজিটের টি পিন নম্বরটি বলুন' or resposnse_text_dict[data['sender']][-1]=='ভুল পিন নাম্বার। দয়া করে পুনরায় পিন নাম্বার বলুন'):
        print('changed text')
        num=re.findall('[0-9]+', data['message'])
        if(len(num)>0):
            if(len(data['message'])>4):
                data['message']=data['message'][:4]
            data['message']=data['message']+' পিন'

    if(resposnse_text_dict[data['sender']][-1]==ASK_HOME):
    	print('changed text')
    	data['message']='H'+data['message']
    if(resposnse_text_dict[data['sender']][-1]==ASK_ROAD):
    	print('changed text')
    	data['message']='R'+data['message']
    if(resposnse_text_dict[data['sender']][-1]==ASK_POST_CODE):
    	print('changed text')
    	data['message']='A'+data['message']
    if(resposnse_text_dict[data['sender']][-1]==ASK_PHONE):
        print('changed text')
        if(len(data['message'])>11):
            data['message']=data['message'][:11]
            print(f"Data {data['message']}.")
        # if(len(data['message'])<11):
        #     data['message']=str(data['message']).ljust(11,'0')
        #     print(f"Data {data['message']}.")
        data['message']=data['message']+' ফোন নাম্বার'

    if(resposnse_text_dict[data['sender']][-1]==ASK_MONEY):
        print('changed text')
        data['message']=data['message']+' টাকা'
    
    if(resposnse_text_dict[data['sender']][-1]==ASK_CARD):
        print('changed text')
        if(len(data['message'])>10):
            data['message']=data['message'][:10]
            print(f"Data {data['message']}.")
        data['message']='আমার কার্ড নাম্বার '+data['message']
    osa=original_string.split(' ')
    if('না ঠিক নাই' in osa):
        print('changed text')
        data['message']='ঠিক না'

    if(len(osa)==1):
        if('চাই' in osa):
            print('changed text')
            data['message']=ASK_OK

    # if('না' in osa and ASK_OK not in original_string):
    #      print('changed text')
    #      data['message']='ঠিক না'
    print(data['message'])
    try:
        #response = await executor.run(action_call)
        start_time=datetime.datetime.now()
        response = await BotFactory.getOrCreate(lang).handle_text(data['message'],sender_id=data['sender'])
        intentInfo = await BotFactory.getOrCreate(lang).parse_message_using_nlu_interpreter(data['message'])
        print("#########  Response from RASA ########")
        print(response)
        print("#################")
        print("#################")
        print(intentInfo)
        print("#################")
        
        end_time=datetime.datetime.now()
        if(len(response) > 0):
            f = open("log_voice.txt", "a", encoding='utf-8')
            f.write(str(start_time)+"\t"+str(data['sender'])+"["+data['cli']+"]"+"\t"+str(data['message'])+"[ OT: "+str(original_string)+"["+intentInfo['intent']['name']+" : "+str(intentInfo['intent']['confidence'])+"] \n")
            f.write(str(end_time)+"\t"+"Disha\t"+str(response[0]['text'])+"\n")
            f.close()
            #global resposnse_text
            resposnse_text.append(response[0]['text'])
            resposnse_text_dict[data['sender']].append(response[0]['text'])

            if(data['message']=='হ্যালো'):
                if(response[0]['text']=='হ্যালো, আমি দিশা। আপনার ভার্চুয়াল অ্যাসিস্ট্যান্ট। আমি আপনাকে কিভাবে সহায়তা করতে পারি?'):
                    if(data['cli'] in PHONE_BOOK):
                        response[0]['text']='হ্যালো, '+PHONE_BOOK[data['cli']]+', আমি দিশা। আপনার ভার্চুয়াল অ্যাসিস্ট্যান্ট। আমি আপনাকে কিভাবে সহায়তা করতে পারি?'
                if(response[0]['text']=='হাই, আমি দিশা। আপনার ভার্চুয়াল অ্যাসিস্ট্যান্ট। আমি আপনাকে কিভাবে সহায়তা করতে পারি?'):
                    if(data['cli'] in PHONE_BOOK):
                        response[0]['text']='হাই, '+PHONE_BOOK[data['cli']]+', আমি দিশা। আপনার ভার্চুয়াল অ্যাসিস্ট্যান্ট। আমি আপনাকে কিভাবে সহায়তা করতে পারি?'
                if(response[0]['text']=='শুভ সকাল, আমি দিশা। আপনার ভার্চুয়াল অ্যাসিস্ট্যান্ট। আপনাকে কিভাবে সহায়তা করতে পারি?'):
                    if(data['cli'] in PHONE_BOOK):
                        response[0]['text']='শুভ সকাল, '+PHONE_BOOK[data['cli']]+', আমি দিশা। আপনার ভার্চুয়াল অ্যাসিস্ট্যান্ট। আপনাকে কিভাবে সহায়তা করতে পারি?'
                if(response[0]['text']=='শুভ বিকেল, দিশা বলছি। আপনার ভার্চুয়াল অ্যাসিস্ট্যান্ট। আপনাকে কিভাবে সহায়তা করতে পারি?'):
                    if(data['cli'] in PHONE_BOOK):
                        response[0]['text']='শুভ বিকেল, '+PHONE_BOOK[data['cli']]+', দিশা বলছি। আপনার ভার্চুয়াল অ্যাসিস্ট্যান্ট। আপনাকে কিভাবে সহায়তা করতে পারি?'
                if(response[0]['text']=='শুভ অপরাহ্ন, দিশা বলছি। আপনার ভার্চুয়াল অ্যাসিস্ট্যান্ট। আপনাকে কিভাবে সহায়তা করতে পারি?'):
                    if(data['cli'] in PHONE_BOOK):
                        response[0]['text']='শুভ অপরাহ্ন, '+PHONE_BOOK[data['cli']]+', দিশা বলছি। আপনার ভার্চুয়াল অ্যাসিস্ট্যান্ট। আপনাকে কিভাবে সহায়তা করতে পারি?'
                if(response[0]['text']=='শুভ সন্ধ্যা, দিশা বলছি। আপনার ভার্চুয়াল অ্যাসিস্ট্যান্ট। আপনাকে কিভাবে সহায়তা করতে পারি?'):
                    if(data['cli'] in PHONE_BOOK):
                        response[0]['text']='শুভ সন্ধ্যা, '+PHONE_BOOK[data['cli']]+', দিশা বলছি। আপনার ভার্চুয়াল অ্যাসিস্ট্যান্ট। আপনাকে কিভাবে সহায়তা করতে পারি?'
                if(response[0]['text']=='শুভ রাত্রি, আমি দিশা। আপনার ভার্চুয়াল অ্যাসিস্ট্যান্ট। আপনাকে কিভাবে সহায়তা করতে পারি?'):
                    if(data['cli'] in PHONE_BOOK):
                        response[0]['text']='শুভ রাত্রি, '+PHONE_BOOK[data['cli']]+', আমি দিশা। আপনার ভার্চুয়াল অ্যাসিস্ট্যান্ট। আপনাকে কিভাবে সহায়তা করতে পারি?'
            
            if(response[0]['text']=='আপনার অ্যাকাউন্টের ব্যালেন্স হল এক লক্ষ ছয় হাজার টাকা। আপনাকে কি আর কোন সহায়তা করতে পারি?'):
                if(data['cli']=='201'):
                    response[0]['text']='আপনার অ্যাকাউন্টের ব্যালেন্স হল দুই লক্ষ ছয় হাজার টাকা। আপনাকে কি আর কোন সহায়তা করতে পারি?'
                if(data['cli']=='01713384891'):
                    response[0]['text']='আপনার অ্যাকাউন্টের ব্যালেন্স হল সত্তর লাখ পঁচাশি হাজার টাকা। আপনাকে কি আর কোন সহায়তা করতে পারি?'
                if(data['cli']=='01714020387'):
                    response[0]['text']='আপনার অ্যাকাউন্টের ব্যালেন্স হল পঞ্চাশ লাখ পঁচাত্তর হাজার টাকা। আপনাকে কি আর কোন সহায়তা করতে পারি?'
                if(data['cli']=='102'):
                    response[0]['text']='আপনার অ্যাকাউন্টের ব্যালেন্স হল নব্বই লাখ সাতষট্টি হাজার টাকা। আপনাকে কি আর কোন সহায়তা করতে পারি?'
                if(data['cli']=='103'):
                    response[0]['text']='আপনার অ্যাকাউন্টের ব্যালেন্স হল ত্রিশ লক্ষ বিশ হাজার টাকা। আপনাকে কি আর কোন সহায়তা করতে পারি?'
                

            
            a_dictionary = {"recipient_id" : response[0]['recipient_id'], "text" : response[0]['text'], "cause_code" : ''}
            
            if(response[0]['text'] in fallback_response):
                count=int(fallback_counter[data['sender']])
                count=count+1
                fallback_counter[data['sender']]=count

            
            if(resposnse_text_dict[data['sender']][-1]=='আপনাকেও ধন্যবাদ'):
                a_dictionary['cause_code']='230'
                resposnse_text_dict[data['sender']]=['s']
                fallback_counter[data['sender']]=0
            elif(int(fallback_counter[data['sender']])>=3):
                a_dictionary['cause_code']='231'
                a_dictionary['text']='আপনার কল টি এক জন কাস্টমার কেয়ার প্রতিনিধির কাছে ট্রান্সফার করা হচ্ছে'
                resposnse_text_dict[data['sender']]=['s']
                fallback_counter[data['sender']]=0
            elif(resposnse_text_dict[data['sender']][-1]=='দুঃখিত, আমি আপনাকে এই মুহূর্তে কোন ধরনের সহায়তা করতে পারছি না। আমি কল টি এক জন কাস্টমার কেয়ার প্রতিনিধির কাছে ট্রান্সফার করছি, একটু অপেক্ষা করুন।' or resposnse_text_dict[data['sender']][-1]=='আপনার কল টি এক জন কাস্টমার কেয়ার প্রতিনিধির কাছে ট্রান্সফার করা হচ্ছে' or resposnse_text_dict[data['sender']][-1]=='আপনার কল টি একজন প্রতিনিধির কাছে পাঠানো হচ্ছে, একটু অপেক্ষা করুন' or resposnse_text_dict[data['sender']][-1]=='আপনার কল টি একজন প্রতিনিধির কাছে ট্রান্সফার হচ্ছে, একটু অপেক্ষা করুন'):
                a_dictionary['cause_code']='231'
                resposnse_text_dict[data['sender']]=['s']
                fallback_counter[data['sender']]=0
            else:
                a_dictionary['cause_code']='0'
                
            response[0]=a_dictionary
        
        print("Response:")
        print(type(response))
        print(response)
        print("###############  fallback counter  #############")
        print(str(fallback_counter))
        print("###############  fallback counter  #############")
    except ActionExecutionRejection as e:
        logger.error(str(e))
        response = {"error": str(e), "action_name": e.action_name}
        response.status_code = 400
        return response

    return web.json_response(response)
    
# Web app routing
app = web.Application()
app.add_routes([
    web.get('/', index),
    web.get('/js', js),
    web.post('/webhooks/rest/webhook', webhook),
    web.static('/static', 'static')
])

# Instantiate all bot agents
bots = BotFactory.createAll()

# Websocket through SocketIO with support for regular HTTP endpoints
sio = socketio.AsyncServer(async_mode='aiohttp', cors_allowed_origins='*')
sio.attach(app)

@sio.on('session_request')
async def on_session_request(sid, data):
    if data is None:
        data = {}
    if 'session_id' not in data or data['session_id'] is None:
        data['session_id'] = uuid.uuid4().hex
    await sio.emit('session_confirm', data['session_id'])


def isascii(s):
    """Check if the characters in string s are in ASCII, U+0-U+7F."""
    return len(s) == len(s.encode())
    
@sio.on('user_uttered')
async def on_user_uttered(sid, message):
    print("SID: ")
    print(sid)
    custom_data = message.get('customData', {})
    lang = custom_data.get('lang', 'en')
    campaign = custom_data.get('campaign', False)

    print('campaign: '+str(campaign))
    
    
    user_message = message.get('message', '')
    print(user_message)
    f = open("log.txt", "a")
    f.write(str(sid)+"\t"+str(user_message)+"\n")
    f.close()
    
    
    number_string=getNumber(user_message)
    if(len(number_string)>0):
        user_message=number_string
        
        
    print("user message")
    print(user_message)                                
                                           
    
    global resposnse_text_dict_web
    
    #lang='be'
    lang='bn'
    #isalpha()
    #if isascii(user_message):
    #	lang='be'


    print('lang: '+lang)
    if(user_message=="ha" or user_message=="haa" or user_message=="হ্যাঁ" or user_message=="হ্যা"):
    	user_message='yes'
    	
    numbers = {'০': '0','১': '1','২': '2','৩': '3','৪': '4','৫': '5','৬': '6','৭': '7','৮': '8','৯': '9'}
    output=[]
    for i in user_message:
    	if(i in numbers):
    		output.append(numbers[i])
    
    if(len(output)>0):
    	user_message=''.join(output)
    	
    print('New user message')
    print(user_message)
    
    #for PIN manupulation
    if(resposnse_text_dict_web['default'][-1]=='আপনার চার ডিজিটের টি পিন নাম্বার বলুন' or resposnse_text_dict_web['default'][-1]=='আপনার টি পিন নম্বরটি বলুন' or resposnse_text_dict_web['default'][-1]=='স্যার, আপনার চার ডিজিটের টি পিন নম্বরটি বলুন' or resposnse_text_dict_web['default'][-1]=='ভুল পিন নাম্বার। দয়া করে পুনরায় পিন নাম্বার বলুন'):
        print('changed text')
        user_message=user_message+' পিন'
        
        

    
    bot_responses = await bots[lang].handle_text(user_message,None,None,sid) #await BotFactory.getOrCreate(lang).handle_text(user_message)
    print("Response:")
    print(bot_responses)
    resposnse_text_dict_web['default'].append(bot_responses[0]['text'])
    
    tracker = bots[lang].tracker_store.get_or_create_tracker(sid)
    state = tracker.current_state()
    res={"tracker": state}
    
    pp = pprint.PrettyPrinter(width=41, compact=True)
    pp.pprint(res)
      
    for bot_response in bot_responses:
        json = __parse_bot_response(bot_response)
        print(json)
        await sio.emit('bot_uttered', json, room=sid)


def __parse_bot_response(bot_response):
    # Images require a special schema
    if 'image' in bot_response:
        return { 'attachment': { 'type': 'image', 'payload': { 'src': bot_response['image'] }}}
    else:
        if 'buttons' in bot_response:
            # The JS client only shows the buttons when they arrive as 'quick_replies'
            bot_response['quick_replies'] = bot_response['buttons']
            del bot_response['buttons']

        # Remove the 'recipient_id', because the client can't handle it
        return {k: v for k, v in bot_response.items() if not k.startswith('recipient_id')}

def __create_env_js(host, port):
    f = None
    try:
        f = open("static/js/env.js", "w+")
        server_url=os.getenv('API_SERVER_URL', 'http://' + host + ':' + str(port))
        dict = {'serverUrl': server_url}
        f.write('Env=' + repr(dict))
    finally:
        if f is not None:
            f.close()

if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5004))
    __create_env_js(host, port)
    web.run_app(app, host=host, port=port)
