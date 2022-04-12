import os
import datetime
import logging
from select import select
import uuid
import socketio
from aiohttp import web
from rasa_sdk.executor import ActionExecutor
from rasa_sdk.interfaces import ActionExecutionRejection

from rasa_sdk.events import SlotSet

import bangla
from banglanum2words import num_convert

from converter import numberTranslate

import json
import pprint
import random

import num_to_int
                                           
import sys
sys.path.append('.')

ASK_EXPLAIN='এই কাজটি সম্পন্ন করতে আপনার এই তথ্য আমাদের লাগবেই। চিন্তা করবেন না, আপনার তথ্য আমাদের কাছে নিরাপদ থাকবে।'
ASK_PIN='আপনার চার ডিজিটের টি পিন নাম্বার বলুন'
ASK_PHONE ='আপনার এগার সংখ্যার ফোন নাম্বার বলুন'
ASK_MONEY='টাকার পরিমাণ বলুন'
ASK_OK='ঠিক আছে'
ASK_CARD = 'আপনার দশ ডিজিট এর কার্ড নাম্বার বলুন'
STORY_TRACKER_SESSION=[]
PHONE_BOOK={
    "201": "মিসটার  নাফিস",
    "202": "মিসটার রিফাত",
    "195": "মিসটার জাহিদ",
    "01713384891": "মিসটার প্রিন্স",
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
                    if(st[i-1]=='ডাবল'):
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

# Keyword Matching
GREETING_INPUTS = ("hello", "hi", "greetings", "sup", "what's up","hey",)
GREETING_RESPONSES = ["hi", "hey", "*nods*", "hi there", "hello", "I am glad! You are talking to me"]
PARSING=[]
LOGS=[]
SLOTS = {'account_number': None,'PIN': None,'card_number': None,'phone_number': None,'amount-of-money': None}
SLOT_VALIDATION={'account_number': 8,'PIN': 4,'card_number': 10,'phone_number': 11}
STORY_TRACKER=[]
CURRENT_STEP=0
RESPONSE_VALIDATION={'account_number': 'ভুল অ্যাকাউন্ট নম্বর, সঠিক অ্যাকাউন্ট নম্বর বলুন','PIN': 'ভুল পিন নম্বর, সঠিক পিন নম্বর বলুন','card_number':'ভুল কার্ড নম্বর, সঠিক কার্ড নম্বর বলুন','phone_number':'ভুল ফোন নম্বর, সঠিক ফোন নম্বর বলুন'}
CONTINUE_UTTER={'check_balance': 'আপনি চেক ব্যালেন্স চালিয়ে যেতে চান','bKash_transfer': 'আপনি বিকাশ চালিয়ে যেতে চান','Credit_Card_Limit': 'আপনি কার্ড লিমিট চালিয়ে যেতে চান'}
RESPONSE_DEFAULT=['আমি আপনার বার্তা টা বুঝতে পারি নি। আপনি কি অন্যভাবে বলতে পারবেন প্লিজ?','কথাটি বুঝতে পারিনি। দয়া করে পুনরায় বলুন','দুঃখিত আপনার কথাটি শুনতে পাইনি','দুঃখিত পুনরাই বলবেন প্লিজ?']
RESPONSE = {
'utter_bank_location_baridhara': 'আমদের বারিধারা শাখার ফোন নাম্বার হচ্ছে জিরো, নাইন, সিক্স, সিক্স, সিক্স, সেভেন, সেভেন, সেভেন, থ্রি, টু, সেভেন।',
'utter_bank_location_Shamoli': 'আমদের শ্যামলী শাখার ফোন নাম্বার হচ্ছে জিরো, নাইন, সিক্স, সিক্স, সিক্স, সেভেন, সেভেন, সেভেন, থ্রি, টু, নাইন।',
'utter_bank_location_banani': 'আমদের বনানী শাখার ফোন নাম্বার হচ্ছে জিরো, নাইন, সিক্স, সিক্স, সিক্স, সেভেন, সেভেন, সেভেন, থ্রি, টু, সিক্স।',
'utter_bank_location_mirpur': 'মিরপুর এগার, এ ব্লক এ অবস্থিত। এবং রাউটিং নাম্বার হচ্ছে জিরো, নাইন, ফাইভ, টু, সিক্স, টু, নাইন, এইট, সেভেন।',
'utter_bank_location_gulshan': 'একশ গুলশান এভিনিউ এ অবস্থিত। এবং ফোন নাম্বার হচ্ছে জিরো, নাইন, সিক্স, সিক্স, সিক্স, সেভেন, সেভেন, সেভেন, থ্রি, টু, ফাইভ।',
'utter_bank_location': 'আমাদের ব্যাংকের হেড অফিস হচ্ছে গুলশান দুই এ। এছাড়া আশুলিয়া, আটি বাজার, পল্টন ও মিরপুরে আমাদের আরোও শাখা আছে।',
'utter_bot': 'আমি দিশা। আপনার ভার্চুয়াল অ্যাসিস্ট্যান্ট। আমাকে তৈরি করেছে জিপ্লেক্স',
'utter_Disha': ['দিশা মানে নির্দেশনা দেয়া এবং যেহেতু আমি আমার কাস্টমার দের সঠিক নিরদেশনা দেয় তাই আমার নাম দিশা।','দিশা মানে দিকনির্দেশ বা নির্দেশনা দেয়া এবং যেহেতু আমি আমার কাস্টমার দের সঠিক নিরদেশনা দেয় তাই আমার নাম দিশা।','আমার নাম দিশা কারণ আমি আমার কাস্টমার দের ব্যাংক সংক্রান্ত সকল ধরনের দিক নিরদেশনা করি।'],
'utter_explain': 'এই কাজটি সম্পন্ন করতে আপনার এই তথ্য আমাদের লাগবেই। চিন্তা করবেন না, আপনার তথ্য আমাদের কাছে নিরাপদ থাকবে।',
'utter_greet': ['হ্যালো, আমি দিশা। আপনার ভার্চুয়াল অ্যাসিস্ট্যান্ট। আমি আপনাকে কিভাবে সহায়তা করতে পারি?','হ্যালো স্যার, আশা করি ভাল অছেন্ । আমি দিশা। আপনার ভার্চুয়াল অ্যাসিস্ট্যান্ট। আমি আপনাকে কিভাবে সহায়তা করতে পারি?'],
'utter_limit': 'আপনার কার্ড এর লিমিট হচ্ছে এক লক্ষ বিশ হাজার টাকা।',
'utter_confirm_phone_number':'আপনি বলেছেন phone_number । সেটা ঠিক হলে বলুন, হ্যা ঠিক আছে',
'utter_confirm_amount': 'স্যার, আপনি বলেছেন amount-of-money । সেটা ঠিক হলে বলুন, হ্যা ঠিক আছে',
'utter_confirm_card_number': 'স্যার, আপনি বলেছেন card_number কার্ড নম্বর, আপনার কার্ড নাম্বার । সেটা ঠিক হলে বলুন, হ্যা ঠিক আছে ।',
'utter_confirm_pin': 'আপনি বলেছেন PIN । সেটা ঠিক হলে বলুন, হ্যা ঠিক আছে',
'utter_confirm_account_number': 'স্যার, আপনি বলেছেন account_number অ্যাকাউন্ট নম্বর । সেটা ঠিক হলে বলুন, হ্যা ঠিক আছে',
'utter_ask_card_number': ['আপনার দশ ডিজিট এর কার্ড নাম্বার বলুন','স্যার, আপনার সঠিক কার্ড নাম্বার টি জানিয়ে সাহায্য করুন','আমি কি আপনার দশ ডিজিট এর কার্ড নম্বর পেতে পারি','আমি কি আপনার দশ ডিজিট এর কার্ড নম্বরটি জানতে পারি','স্যার, আমাকে আপনার দশ ডিজিট এর কার্ড নম্বরটি বলুন'],
'utter_bkash_done': 'আপনার কাজ সম্পন্ন হয়েছে',
'utter_ask_amount': ['টাকার পরিমাণ বলুন','স্যার, টাকার পরিমাণ বলুন'],
'utter_ask_phone_number': ['আপনার এগার সংখ্যার ফোন নাম্বার বলুন','স্যার, আপনার ফোন নম্বর প্রদান করে আমাদের সাহায্য করুন'],
'utter_ask_account_number': ['আপনার আট ডিজিট এর একাউন্ট নাম্বার বলুন','স্যার, আপনার সঠিক একাউন্ট নাম্বার টি জানিয়ে সাহায্য করুন','আমি কি আপনার আট ডিজিট এর অ্যাকাউন্ট নম্বর পেতে পারি','আমি কি আপনার আট ডিজিট এর অ্যাকাউন্ট নম্বরটি জানতে পারি','স্যার, আমাকে আপনার আট ডিজিট এর অ্যাকাউন্ট নম্বরটি বলুন'],
'utter_ask_pin':['আপনার চার ডিজিটের টি পিন নাম্বার বলুন','স্যার, আপনার টি পিন নম্বরটি বলুন','স্যার, আপনার চার ডিজিটের টি পিন নম্বরটি বলুন'],
'utter_balance': 'আপনার অ্যাকাউন্টের ব্যালেন্স হল এক লাখ বিশ হাজার টাকা'}
INTENTS = {'check_balance': 'check_balance','inform': 'inform'}
STORIES={
    'greet': {'1': 'utter_greet'},
    'Name_meaning': {'1': 'utter_Disha'},
    'check_human': {'1': 'utter_bot'},
    'Bank_and_ATM_Location': {'1': {'check_slot':'location','utter':'utter_bank_location'}},
    'check_balance': {'1':'utter_ask_account_number', '2': {'inform':{'slot': 'account_number','value': None},'utter': 'utter_confirm_account_number'},'3': {'confirm':{},'utter': 'utter_ask_pin'}, '4': {'inform':{'slot': 'PIN','value': None},'utter': 'utter_confirm_pin'}, '5': {'confirm':{},'utter': 'utter_balance'}},
    'bKash_transfer': {'1':'utter_ask_account_number', '2': {'inform':{'slot': 'account_number','value': None},'utter': 'utter_confirm_account_number'},'3': {'confirm':{},'utter': 'utter_ask_phone_number'}, '4': {'inform':{'slot': 'phone_number','value': None},'utter': 'utter_confirm_phone_number'}, '5': {'confirm':{},'utter': 'utter_ask_pin'}, '6': {'inform':{'slot': 'PIN','value': None},'utter': 'utter_confirm_pin'},'7': {'confirm':{},'utter': 'utter_ask_amount'},'8': {'inform':{'slot': 'amount-of-money','value': None},'utter': 'utter_confirm_amount'}, '9': {'confirm':{},'utter': 'utter_bkash_done'}},
    'Credit_Card_Limit': {'1':'utter_ask_card_number', '2': {'inform':{'slot': 'card_number','value': None},'utter': 'utter_confirm_card_number'},'3': {'confirm':{},'utter': 'utter_ask_pin'}, '4': {'inform':{'slot': 'PIN','value': None},'utter': 'utter_confirm_pin'}, '5': {'confirm':{},'utter': 'utter_limit'}},
}


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
    
    if(len(number_string)>0):
        data['message']=number_string
             
    string_to_num=num_to_int.spell_to_int(data['message'])
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
    if(ASK_OK in data['message']):
        print('changed text')
        data['message']=ASK_OK
    

    global STORY_TRACKER

    #for PIN manupulation 2
    if(len(resposnse_text_dict[data['sender']])>=3):
        if(resposnse_text_dict[data['sender']][-3]==ASK_PIN or resposnse_text_dict[data['sender']][-3]=='ভুল পিন নম্বর, সঠিক পিন নম্বর বলুন'):
            print('changed text')
            if(len(data['message'])>4):
                data['message']=data['message'][:4]
            data['message']=data['message']+' পিন'

    if(len(resposnse_text_dict[data['sender']])>=2):
        if(resposnse_text_dict[data['sender']][-2]==ASK_PIN or resposnse_text_dict[data['sender']][-2]=='ভুল পিন নম্বর, সঠিক পিন নম্বর বলুন'):
            print('changed text')
            if(len(data['message'])>4):
                data['message']=data['message'][:4]
            data['message']=data['message']+' পিন'
    
    #for PIN manupulation
    if(resposnse_text_dict[data['sender']][-1]==ASK_PIN or resposnse_text_dict[data['sender']][-1]=='ভুল পিন নম্বর, সঠিক পিন নম্বর বলুন'):
        print('changed text')
        if(len(data['message'])>4):
            data['message']=data['message'][:4]
        data['message']=data['message']+' পিন'
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
    # if('চাই' in osa):
    #     print('changed text')
    #     data['message']=ASK_OK
    # if('না' in osa and ASK_OK not in original_string):
    #     print('changed text')
    #     data['message']='ঠিক না'
    print(data['message'])
    try:
        global PARSING
        #response = await executor.run(action_call)
        start_time=datetime.datetime.now()
        res = await response_from_bot(data['message'],data['sender'])
        intentInfo=PARSING
        response = [{'recipient_id': data['sender'],'text': res,'cause_code': ''}]          
        #intentInfo = await BotFactory.getOrCreate(lang).parse_message_using_nlu_interpreter(data['message'])
        
        end_time=datetime.datetime.now()
        if(len(response) > 0):
            f = open("log_voice.txt", "a")
            #f.write(str(start_time)+"\t"+str(data['sender'])+"\t"+str(data['message'])+"\n")
            f.write(str(start_time)+"\t"+str(data['sender'])+"["+data['cli']+"]"+"\t"+str(data['message'])+"["+intentInfo['intent']['name']+" : "+str(intentInfo['intent']['confidence'])+"] \n") 
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
            
            a_dictionary = {"recipient_id" : response[0]['recipient_id'], "text" : response[0]['text'], "cause_code" : ''}
            
            if(resposnse_text_dict[data['sender']][-1]=='আপনাকেও ধন্যবাদ'):
                a_dictionary['cause_code']='230'
                resposnse_text_dict[data['sender']]=['s']
            elif(resposnse_text_dict[data['sender']][-1]=='আপনার কল টি এক জন কাস্টমার কেয়ার প্রতিনিধির কাছে ট্রান্সফার করা হচ্ছে'):
                a_dictionary['cause_code']='231'
                resposnse_text_dict[data['sender']]=['s']
            else:
                a_dictionary['cause_code']='0'
                
            response[0]=a_dictionary
        print("Response:")
        print(type(response))
        print(response)
    except ActionExecutionRejection as e:
        logger.error(str(e))
        response = {"error": str(e), "action_name": e.action_name}
        response.status_code = 400
        return response

    return web.json_response(response)


# Generating response
async def response_from_bot(user_response,sender_id):

    print("##################  SENDER ID  ######################")
    print(sender_id)
    print("########################################")

    global PARSING
    global STORY_TRACKER
    global SLOTS
    if(sender_id not in STORY_TRACKER_SESSION):
        STORY_TRACKER_SESSION.append(sender_id)
        STORY_TRACKER=[]
        for ii in SLOTS:
            SLOTS[ii]=None
    parsing = await BotFactory.getOrCreate('bn').parse_message_using_nlu_interpreter(user_response)
    PARSING = parsing
    print(parsing)

    def update_tracker(intent,step):
        print("Updating Story")
        STORY_TRACKER[-1]['step']=str(step)
        LOGS.append({'intent': intent,'CURRENT_STEP': str(step),'story': intent})
    
    probability=parsing['intent']['confidence']


    if(float(probability)<0.60 and parsing['intent']['name'] not in ['inform','affirm','deny']):
        robo_response=RESPONSE_DEFAULT[random.randint(0,3)]
        return robo_response
    else:
        intentName = parsing['intent']['name']
        user_input = parsing['text']
        global CURRENT_STEP
        #global STORY_TRACKER
        global CONTINUE_UTTER
        if(CURRENT_STEP==0):
                CURRENT_STEP=1
        print(CURRENT_STEP)
        print("########################################")
        print(STORY_TRACKER)
        print("########################################")
        print("##################  SLOTS VALUES  ######################")
        print(SLOTS)
        print("########################################")


        # for single inform intent and validation
        if(len(STORY_TRACKER)>0):
            if(int(STORY_TRACKER[-1]['step'])<=int(STORY_TRACKER[-1]['stop'])):
                if(intentName=='inform'):
                    intent = STORY_TRACKER[-1]['intent']
                    step = STORY_TRACKER[-1]['step']
                    if('inform' in STORIES[intent][str(step)]):
                        # validate
                        if(len(parsing['entities'])>0):
                            slot_name=parsing['entities'][0]['entity']
                            slot_value=parsing['entities'][0]['value']
                            print("###########  INSIDE VLIDATION  ##########")
                            print('slot_name: '+ slot_name)
                            print('slot_value: '+ str(slot_value))
                            print('story slot name: '+ STORIES[intent][str(step)]['inform']['slot'])
                            print("##########################################")
                            if(slot_name!=STORIES[intent][str(step)]['inform']['slot']):
                                return 'আপনার তথ্য সঠিক নয়, দয়া করে সঠিক তথ্য দিন'
                            else:
                                if(slot_name in SLOT_VALIDATION):
                                    length = SLOT_VALIDATION[slot_name]
                                    if(len(slot_value)!=length):
                                        step=int(step)-1
                                        STORY_TRACKER[-1]['step']=int(step)
                                        res=RESPONSE_VALIDATION[slot_name]
                                        if(isinstance(res, list)):
                                            res=res[random.randint(0,len(res)-1)]
                                        return res
        # new story start
        if(intentName in STORIES):
            CURRENT_STEP=1
            print("CURRENT_STEP:"+str(CURRENT_STEP))
            res=''
            # previous story not complete
            if(len(STORY_TRACKER)>0):
                if(int(STORY_TRACKER[-1]['step'])<=int(STORY_TRACKER[-1]['stop'])):
                    res=''
                    intent = STORY_TRACKER[-1]['intent']
                    step = STORY_TRACKER[-1]['step']
                    LOGS.append({'intent': intentName,'CURRENT_STEP': str(step),'story': intentName,'continue_ask': True, 'continue_to': intentName})
                    return CONTINUE_UTTER[intent]

            # new story start inside
            if(isinstance(STORIES[intentName][str(CURRENT_STEP)], dict)):
                if('check_slot' in STORIES[intentName][str(CURRENT_STEP)]):
                    slot_name_story=STORIES[intentName][str(CURRENT_STEP)]['check_slot']
                    if(len(parsing['entities'])>0):
                        slot_name=parsing['entities'][0]['entity']
                        slot_value=parsing['entities'][0]['value']
                        if(slot_name_story==slot_name):
                            if(slot_value == "মিরপুর" or slot_value == "মিরপুরের" or slot_value == "মিরপুরে"):
                                res=RESPONSE['utter_bank_location_mirpur']
                            if(slot_value == "গুলশান" or slot_value == "গুলশানের"):
                                res=RESPONSE['utter_bank_location_gulshan']
                            if(slot_value == "শ্যামলী" or slot_value == "শ্যামলীর"):
                                res=RESPONSE['utter_bank_location_Shamoli']
                            if(slot_value == "বনানী" or slot_value == "বনানীর"):
                                res=RESPONSE['utter_bank_location_banani']
                            if(slot_value == "বারিধারা" or slot_value == "বারিধারার"):
                                res=RESPONSE['utter_bank_location_baridhara']
                    else:
                        res=RESPONSE[STORIES[intentName][str(CURRENT_STEP)]]['utter']




            if(isinstance(STORIES[intentName][str(CURRENT_STEP)], str)):
                res=RESPONSE[STORIES[intentName][str(CURRENT_STEP)]]
                CURRENT_STEP=CURRENT_STEP+1
                stop=len(STORIES[intentName])
                forward_step=int(CURRENT_STEP)
                print("here"+str(forward_step))
                if(forward_step<stop):
                    if('inform' in STORIES[intentName][str(forward_step)]):
                        slot_name=STORIES[intentName][str(forward_step)]['inform']['slot']
                        if(SLOTS[slot_name]!=None):
                            slot_value=SLOTS[slot_name]
                            res=RESPONSE[STORIES[intentName][str(forward_step)]['utter']]
                            num=numberTranslate(slot_value)                            
                            res=res.replace(slot_name, num)                            
                            CURRENT_STEP=CURRENT_STEP+1
                
            STORY_TRACKER.append({'intent': intentName,"step": str(CURRENT_STEP), "stop": len(STORIES[intentName])})
            LOGS.append({'intent': intentName,'CURRENT_STEP': str(CURRENT_STEP),'story': intentName})
            if(isinstance(res, list)):
                res=res[random.randint(0,len(res)-1)]
            return res
        # for continue ask and explain
        if(len(STORY_TRACKER)>0):
            if(int(STORY_TRACKER[-1]['step'])<=int(STORY_TRACKER[-1]['stop'])):
                if(intentName=='explain'):
                    STORY_TRACKER[-1]['step'] = int(STORY_TRACKER[-1]['step']) - 2
                    res=RESPONSE['utter_explain']
                    if(isinstance(res, list)):
                        res=res[random.randint(0,len(res)-1)]
                    return res
                if('continue_ask' in LOGS[-1]):
                    if(intentName=='affirm'):
                        intent = STORY_TRACKER[-1]['intent']
                        step = STORY_TRACKER[-1]['step'] 
                        STORY_TRACKER[-1]['step']='2'
                        res=RESPONSE[STORIES[intent][str('1')]]
                        if(isinstance(res, list)):
                            res=res[random.randint(0,len(res)-1)]
                        return res
                    if(intentName=='deny'):
                        STORY_TRACKER.append({'intent': LOGS[-1]['continue_to'],"step": '1', "stop": len(STORIES[LOGS[-1]['continue_to']])})                 
                        pass
        # continue for all other
        if(len(STORY_TRACKER)>0):
            if(int(STORY_TRACKER[-1]['step'])<=int(STORY_TRACKER[-1]['stop'])):
                res=''
                intent = STORY_TRACKER[-1]['intent']
                step = STORY_TRACKER[-1]['step']
                # for single utter               
                if(isinstance(STORIES[intent][str(step)], str)):                    
                    CURRENT_STEP=CURRENT_STEP+1
                    res=RESPONSE[STORIES[intent][str(step)]]
                    step=int(step)+1
                    forward_step=int(step)
                    print("-------------------------------------HERE"+str(forward_step))
                    if('inform' in STORIES[intent][str(forward_step)]):
                        slot_name=STORIES[intent][str(forward_step)]['inform']['slot']
                        if(SLOTS[slot_name]!=None):
                            print("-------------------------------------HERE2"+str(forward_step))
                            slot_value=SLOTS[slot_name]
                            res=RESPONSE[STORIES[intent][str(forward_step)]['utter']]
                            num=numberTranslate(slot_value)                            
                            res=res.replace(slot_name, num)
                            step=int(step)+1
                    update_tracker(intentName,step)
                    if(isinstance(res, list)):
                        res=res[random.randint(0,len(res)-1)]
                    return res
                # for inform utter
                if(isinstance(STORIES[intent][str(step)], dict)):
                    if('inform' in STORIES[intent][str(step)]):
                        CURRENT_STEP=CURRENT_STEP+1
                        if(len(parsing['entities'])>0):
                            slot_name=parsing['entities'][0]['entity']
                            slot_value=parsing['entities'][0]['value']
                            num=numberTranslate(slot_value)                            
                            res=RESPONSE[STORIES[intent][str(step)]['utter']]
                            res=res.replace(STORIES[intent][str(step)]['inform']['slot'], num)
                            SLOTS[slot_name]=slot_value
                        else:
                            res=RESPONSE[STORIES[intent][str(step)]['utter']]
                        step=int(step)+1
                        update_tracker(intentName,step)
                        if(isinstance(res, list)):
                            res=res[random.randint(0,len(res)-1)]
                        return res
                    if('confirm' in STORIES[intent][str(step)]):
                        if(intentName=='affirm'):
                            CURRENT_STEP=CURRENT_STEP+1
                            res=RESPONSE[STORIES[intent][str(step)]['utter']]
                            step=int(step)+1
                        if(intentName=='deny'):
                            CURRENT_STEP=CURRENT_STEP-1
                            step=int(step)-1
                            if(isinstance(STORIES[intent][str(step-1)], str)):
                                res=RESPONSE[STORIES[intent][str(step-1)]]
                            if(isinstance(STORIES[intent][str(step-1)], dict)):
                                res=RESPONSE[STORIES[intent][str(step-1)]['utter']]
                        update_tracker(intentName,step)
                        if(isinstance(res, list)):
                            res=res[random.randint(0,len(res)-1)]
                        return res
                #print("Updating Story")
                #STORY_TRACKER[-1]['step']=str(step)
                #LOGS.append({'intent': intentName,'CURRENT_STEP': str(step),'story': intentName})
                #return res

        if(intentName in STORIES):
            return 'No Story 1'
        else:
            return 'No Story'
        return intentName


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

@sio.on('user_uttered')
async def on_user_uttered(sid, message):
    print(sid)
    custom_data = message.get('customData', {})
    lang = custom_data.get('lang', 'en')
    campaign = custom_data.get('campaign', False)
    print('lang: '+lang)
    print('campaign: '+str(campaign))
    
    
    user_message = message.get('message', '')
    print(user_message)
    f = open("log.txt", "a")
    f.write(str(sid)+"\t"+str(user_message)+"\n")
    f.close()
    
    
    number_string=getNumber(user_message)
    if(len(number_string)>0):
        user_message=number_string
        
        
    print("new user message")
    print(user_message)                                
                                           

    bot_responses = await bots[lang].handle_text(user_message,None,None,sid) #await BotFactory.getOrCreate(lang).handle_text(user_message)
    print("Response:")
    print(bot_responses)
    
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
