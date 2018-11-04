# coding: utf-8

import random

from slackbot.bot import respond_to     # @botname: で反応するデコーダ
from slackbot.bot import listen_to      # チャネル内発言で反応するデコーダ
from slackbot.bot import default_reply  # 該当する応答がない場合に反応するデコーダ

from plugins.scrape import Scrape




@respond_to('ライバル')
def get_rivals(message):
	text = message.body["text"]
	text = text.split(" ")
	if len(text)<2:
		print("text dame")
	else:
		scrape = Scrape(text[0], text[1], text[2], message.body["channel"])
		scrape.set_schedule()
		scrape.sort_girls()
		scrape.create_girl_info()
		scrape.integrate_images()
		scrape.send_image()
		scrape.delete_tmp()
