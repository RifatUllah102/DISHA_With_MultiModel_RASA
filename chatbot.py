#!/usr/bin/env python
# -*- coding: utf-8 -*- 
from __future__ import unicode_literals, print_function
from distutils.log import Log
#Meet Robo: your friend
import os
import logging
import sys, getopt
from pathlib import Path
from rasa.utils.endpoints import EndpointConfig
from rasa.core.agent import Agent
from collections.abc import Mapping

#import necessary libraries
import io
import random
import string # to process standard python strings
import warnings
import numpy as np
# from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.metrics.pairwise import cosine_similarity
from converter import numberTranslate
#for snips

import io
import json
from snips_nlu import SnipsNLUEngine
from snips_nlu.default_configs import CONFIG_EN

with io.open("dataset.json") as f:
    sample_dataset = json.load(f)

nlu_engine = SnipsNLUEngine(config=CONFIG_EN)
nlu_engine = nlu_engine.fit(sample_dataset)

from utils.bot_factory import BotFactory

import warnings
warnings.filterwarnings('ignore')

import nltk
from nltk.stem import WordNetLemmatizer
nltk.download('popular', quiet=True) # for downloading packages

# uncomment the following only the first time
#nltk.download('punkt') # first-time use only
#nltk.download('wordnet') # first-time use only


#Reading in the corpus
with open('chatbot.txt','r', encoding='utf8', errors ='ignore') as fin:
    raw = fin.read().lower()

#TOkenisation
sent_tokens = nltk.sent_tokenize(raw)# converts to list of sentences 
word_tokens = nltk.word_tokenize(raw)# converts to list of words

# Preprocessing
lemmer = WordNetLemmatizer()
def LemTokens(tokens):
    return [lemmer.lemmatize(token) for token in tokens]
remove_punct_dict = dict((ord(punct), None) for punct in string.punctuation)
def LemNormalize(text):
    return LemTokens(nltk.word_tokenize(text.lower().translate(remove_punct_dict)))


# Keyword Matching
GREETING_INPUTS = ("hello", "hi", "greetings", "sup", "what's up","hey",)
GREETING_RESPONSES = ["hi", "hey", "*nods*", "hi there", "hello", "I am glad! You are talking to me"]

STORY_TRACKER_SESSION=[]
LOGS=[]
SLOTS = {'account_number': None,'PIN': None,'card_number': None,'phone_number': None,'amount': None}
SLOT_VALIDATION={'account_number': 8,'PIN': 4,'card_number': 10,'phone_number': 11}
STORY_TRACKER=[]
CURRENT_STEP=0
RESPONSE_VALIDATION={'account_number': 'ভুল অ্যাকাউন্ট নম্বর, সঠিক অ্যাকাউন্ট নম্বর বলুন','PIN': 'ভুল পিন নম্বর, সঠিক পিন নম্বর বলুন','card_number':'ভুল কার্ড নম্বর, সঠিক কার্ড নম্বর বলুন','phone_number':'ভুল ফোন নম্বর, সঠিক ফোন নম্বর বলুন'}
CONTINUE_UTTER={'check_balance': 'আপনি চেক ব্যালেন্স চালিয়ে যেতে চান','bKash_transfer': 'আপনি বিকাশ চালিয়ে যেতে চান','Credit_Card_Limit': 'আপনি কার্ড লিমিট চালিয়ে যেতে চান'}
RESPONSE_DEFAULT=['আমি আপনার বার্তা টা বুঝতে পারি নি। আপনি কি অন্যভাবে বলতে পারবেন প্লিজ?','কথাটি বুঝতে পারিনি। দয়া করে পুনরায় বলুন','দুঃখিত আপনার কথাটি শুনতে পাইনি','দুঃখিত পুনরাই বলবেন প্লিজ?']
RESPONSE = {'utter_explain': 'এই কাজটি সম্পন্ন করতে আপনার এই তথ্য আমাদের লাগবেই। চিন্তা করবেন না, আপনার তথ্য আমাদের কাছে নিরাপদ থাকবে।','utter_greet': 'হ্যালো, আমি দিশা। আপনার ভার্চুয়াল অ্যাসিস্ট্যান্ট। আমি আপনাকে কিভাবে সহায়তা করতে পারি?','utter_limit': 'আপনার কার্ড এর লিমিট হচ্ছে এক লক্ষ বিশ হাজার টাকা।','utter_confirm_card_number': 'আপনি বলেছেন card_number , আপনার কার্ড নাম্বার । সেটা ঠিক হলে বলুন, হ্যা ঠিক আছে ।','utter_ask_card_number': 'আপনার দশ ডিজিট এর কার্ড নাম্বার বলুন','utter_bkash_done': 'আপনার কাজ সম্পন্ন হয়েছে','utter_confirm_amount': 'আপনি বলেছেন amount । সেটা ঠিক হলে বলুন, হ্যা ঠিক আছে','utter_ask_amount': 'টাকার পরিমাণ বলুন','utter_confirm_phone_number':'আপনি বলেছেন phone_number । সেটা ঠিক হলে বলুন, হ্যা ঠিক আছে','utter_ask_phone_number': 'আপনার এগার সংখ্যার ফোন নাম্বার বলুন','utter_confirm_pin': 'আপনি বলেছেন pin । সেটা ঠিক হলে বলুন, হ্যা ঠিক আছে','utter_confirm_account_number': 'আপনি বলেছেন account_number । সেটা ঠিক হলে বলুন, হ্যা ঠিক আছে','utter_ask_account_number': 'আপনার আট ডিজিট এর একাউন্ট নাম্বার বলুন','utter_ask_pin':'আপনার চার ডিজিটের টি পিন নাম্বার বলুন','utter_balance': 'আপনার অ্যাকাউন্টের ব্যালেন্স হল এক লাখ বিশ হাজার টাকা'}
INTENTS = {'check_balance': 'check_balance','inform': 'inform'}
STORIES={
    'greet': {'1': 'utter_greet'},
    'check_balance': {'1':'utter_ask_account_number', '2': {'inform':{'slot': 'account_number','value': None},'utter': 'utter_confirm_account_number'},'3': {'confirm':{},'utter': 'utter_ask_pin'}, '4': {'inform':{'slot': 'PIN','value': None},'utter': 'utter_confirm_pin'}, '5': {'confirm':{},'utter': 'utter_balance'}},
    'bKash_transfer': {'1':'utter_ask_account_number', '2': {'inform':{'slot': 'account_number','value': None},'utter': 'utter_confirm_account_number'},'3': {'confirm':{},'utter': 'utter_ask_phone_number'}, '4': {'inform':{'slot': 'phone_number','value': None},'utter': 'utter_confirm_phone_number'}, '5': {'confirm':{},'utter': 'utter_ask_pin'}, '6': {'inform':{'slot': 'PIN','value': None},'utter': 'utter_confirm_pin'},'7': {'confirm':{},'utter': 'utter_ask_amount'},'8': {'inform':{'slot': 'amount','value': None},'utter': 'utter_confirm_amount'}, '9': {'confirm':{},'utter': 'utter_bkash_done'}},
    'Credit_Card_Limit': {'1':'utter_ask_card_number', '2': {'inform':{'slot': 'card_number','value': None},'utter': 'utter_confirm_card_number'},'3': {'confirm':{},'utter': 'utter_ask_pin'}, '4': {'inform':{'slot': 'PIN','value': None},'utter': 'utter_confirm_pin'}, '5': {'confirm':{},'utter': 'utter_limit'}},
}

def greeting(sentence):
    """If user's input is a greeting, return a greeting response"""
    for word in sentence.split():
        if word.lower() in GREETING_INPUTS:
            return random.choice(GREETING_RESPONSES)


# Generating response
def response_from_bot(user_response,sender_id):

    print("##################  SENDER ID  ######################")
    print(sender_id)
    print("########################################")

    global STORY_TRACKER
    global SLOTS
    if(sender_id not in STORY_TRACKER_SESSION):
        STORY_TRACKER_SESSION.append(sender_id)
        STORY_TRACKER=[]
        SLOTS={}
    parsing = BotFactory.getOrCreate('bn').parse_message_using_nlu_interpreter(user_response)
    print(parsing)

    # tracker = BotFactory.getOrCreate('bn').tracker_store.get_or_create_tracker(sender_id=sender_id)
    # print(tracker)
    # slots = tracker.slots
    # print(slots)
    
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
                            if(slot_name!=STORIES[intent][str(step)]['inform']['slot']):
                                return 'আপনার তথ্য সঠিক নয়, দয়া করে সঠিক তথ্য দিন'
                            else:
                                if(slot_name in SLOT_VALIDATION):
                                    length = SLOT_VALIDATION[slot_name]
                                    if(len(slot_value)!=length):
                                        step=int(step)-1
                                        STORY_TRACKER[-1]['step']=int(step)
                                        res=RESPONSE_VALIDATION[slot_name]
                                        return res

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

            # new story start
            if(isinstance(STORIES[intentName][str(CURRENT_STEP)], str)):
                res=RESPONSE[STORIES[intentName][str(CURRENT_STEP)]]
                CURRENT_STEP=CURRENT_STEP+1
            STORY_TRACKER.append({'intent': intentName,"step": str(CURRENT_STEP), "stop": len(STORIES[intentName])})
            LOGS.append({'intent': intentName,'CURRENT_STEP': str(CURRENT_STEP),'story': intentName})
            return res
        # for continue ask and explain
        if(len(STORY_TRACKER)>0):
            if(int(STORY_TRACKER[-1]['step'])<=int(STORY_TRACKER[-1]['stop'])):
                if(intentName=='explain'):
                    STORY_TRACKER[-1]['step'] = int(STORY_TRACKER[-1]['step']) - 2
                    res=RESPONSE['utter_explain']
                    return res
                if('continue_ask' in LOGS[-1]):
                    if(intentName=='affirm'):
                        intent = STORY_TRACKER[-1]['intent']
                        step = STORY_TRACKER[-1]['step'] 
                        STORY_TRACKER[-1]['step']='2'
                        return RESPONSE[STORIES[intent][str('1')]]
                    if(intentName=='deny'):
                        STORY_TRACKER.append({'intent': LOGS[-1]['continue_to'],"step": '1', "stop": len(STORIES[LOGS[-1]['continue_to']])})                 
                        pass

        if(len(STORY_TRACKER)>0):
            if(int(STORY_TRACKER[-1]['step'])<=int(STORY_TRACKER[-1]['stop'])):
                res=''
                intent = STORY_TRACKER[-1]['intent']
                step = STORY_TRACKER[-1]['step']                
                if(isinstance(STORIES[intent][str(step)], str)):                    
                    CURRENT_STEP=CURRENT_STEP+1
                    forward_step=int(step)+1
                    res=RESPONSE[STORIES[intent][str(step)]]
                    step=int(step)+1
                    if('inform' in STORIES[intent][str(forward_step)]):
                        slot_name=STORIES[intent][str(forward_step)]['inform']['slot']
                        if(SLOTS[slot_name]!=None):
                            res=RESPONSE[STORIES[intent][str(forward_step)]]
                            step=int(step)+1
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
                print("Updating Story")
                STORY_TRACKER[-1]['step']=str(step)
                LOGS.append({'intent': intentName,'CURRENT_STEP': str(step),'story': intentName})
                return res

        if(intentName in STORIES):
            
            return 'No Story 1'
        else:
            return 'No Story'
        return intentName


flag=True
print("ROBO: My name is Robo. I will answer your queries about Chatbots. If you want to exit, type Bye!")
while(flag==True):
    user_response = input()
    user_response=user_response.lower()
    if(user_response!='bye'):
        if(user_response=='thanks' or user_response=='thank you' ):
            flag=False
            print("ROBO: You are welcome..")
        else:
            if(greeting(user_response)!=None):
                print("ROBO: "+greeting(user_response))
            else:
                print("ROBO: ",end="")
                print(response_from_bot(user_response,'default'))
                #sent_tokens.remove(user_response)
    else:
        flag=False
        print("ROBO: Bye! take care..")    
        
        
