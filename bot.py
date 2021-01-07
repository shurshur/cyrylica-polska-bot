#!/usr/bin/env python3
import sys
import re
from time import time, localtime, strftime, sleep
import telebot
import requests
try:
  from Levenshtein import distance as levenshtein_distance
except ImportError:
  from distance import levenshtein as levenshtein_distance
import config

dictmap = {}

def load_dict(code,fn):
  dictmap[code] = [] 
  with open(fn,"r") as f:
    for l in f:
      if l.startswith('#') or l.startswith(' '):
        continue
      m = re.search(r'^(\S+)\s+(\S+)', l)
      if not m:
        print ("ERROR: [%s]" % l)
        continue
      m1 = m.group(1)
      m2 = m.group(2)
      m1 = re.sub(r'_','(\\\\b|[^\\\\w])',m1)
      m2 = re.sub(r'_','\\\\1',m2,1)
      m2 = re.sub(r'_','\\\\2',m2,1)
      m2 = re.sub(r'_','\\\\3',m2,1)
      dictmap[code].append((m1, m2))

def translate(code, text):
  for k,v in dictmap[code]:
    text = re.compile(k, re.U).sub(v, text)
  return text

load_dict("pl_lat2cyr","pl_lat2cyr.tab")

bot = telebot.TeleBot(config.bot_token)

@bot.message_handler(content_types=['text'])
def translate_message(message):
  print ("%s|%s|%s|%s <%s %s> %s" % (message.chat.type, str(message.chat.id), message.chat.title, strftime("%Y-%m-%d %H:%M:%S", localtime(message.date)), message.from_user.first_name, message.from_user.last_name, message.text))
  if time() > message.date+config.max_timediff:
    print (" message time too old :(")
    return
  for code in config.default_tabs:
    msgtr = translate(code, message.text)
    dist = levenshtein_distance(message.text, msgtr)
    ratio = dist/len(message.text)
    if ratio > config.min_levenshtein_ratio:
      print (" code=%s ratio=%lf => %s" % (code, ratio, msgtr))
      try:
        if config.test_mode:
          msgtr = "[TEST MODE] "+msgtr
        bot.send_message(message.chat.id, msgtr, reply_to_message_id=message.message_id)
      except telebot.apihelper.ApiException:
        print (" Exception occured!")
      return

while True:
  try:
    bot.polling()
  except requests.exceptions.ConnectionError:
    print (" ConnectionError exception occured while polling, restart in 1 second...")
    sleep(1)
    continue
  except telebot.apihelper.ApiException:
    print (" ApiException exception occured while polling, restart in 1 second...")
    sleep(1)
    continue
  except requests.exceptions.ReadTimeout:
    print (" ReadTimeout exception occured while polling, restart in 1 second...")
    sleep(1)
    continue
