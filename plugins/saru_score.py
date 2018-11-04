# coding: utf-8

import random

from slackbot.bot import respond_to     # @botname: で反応するデコーダ
from slackbot.bot import listen_to      # チャネル内発言で反応するデコーダ
from slackbot.bot import default_reply  # 該当する応答がない場合に反応するデコーダ

from plugins.scrape import Saru
from plugins.create_database import DBManager
from time import sleep

saru = Saru("plugins/config.yml")
saru.set_rival_ids("plugins/rival_ids.yml")
dbManager = DBManager("plugins/rival_ids.yml", "plugins/slack_config.yml")
dbManager.set_database("SARU_SCORE")

@respond_to('ライバル')
def get_rivals(message):
	if saru.is_updating:
		message.send("更新中です")
	else:
		text = ""
		for rival_name, rival_id in saru.rival_ids.items():
			if saru.scrape_rivals[rival_name]:
				text += f"{rival_name}\n"
			else:
				text += f"~{rival_name}~\n"
		message.send(text)


@respond_to('登録')
def set_rival(message):
	if saru.is_updating:
		message.send("更新中です")
	else:
		text = message.body["text"]
		text = text.split(" ")
		try:
			rival_name = text[1]
		except:
			message.send("無効な入力です")
			return
		if rival_name in saru.scrape_rivals:
			saru.set_update_rivals(rival_name, True)
			dbManager.set_update_rivals(rival_name, True)
			message.send(f"{rival_name}さんを登録しました")
		else:
			message.send(f"{rival_name}さんは見つかりませんでした")


@respond_to('削除')
def set_rival(message):
	if saru.is_updating:
		message.send("更新中です")
	else:
		text = message.body["text"]
		text = text.split(" ")
		try:
			rival_name = text[1]
		except:
			message.send("無効な入力です")
			return
		if rival_name in saru.scrape_rivals:
			saru.set_update_rivals(rival_name, False)
			dbManager.set_update_rivals(rival_name, False)
			message.send(f"{rival_name}さんを削除しました")
		else:
			message.send(f"{rival_name}さんは見つかりませんでした")

@respond_to('更新')
def update_score(message):
	if saru.is_updating:
		message.send("更新中です")
	else:
		text = message.body["text"]
		text = text.split(" ")
		if len(text) == 3:
			saru.is_updating = True
			while(True):
				for music_level in range(int(text[1]),int(text[2])+1):
					for i in [0, 2, 5, 7, 9]:
						sleep(i)
						if saru.login():
							break
						else:
							pass
					else:
						break
					# jsonで各プレイヤーのスコアを保存するところまで
					if saru.save_score(music_level):
						dbManager.create_database(music_level)
						dbManager.compare_score(music_level)
					else:
						# コネクションが切れたら
						message.send("コネクションが切断されました")
						saru.is_updating = False
						break
				saru.is_updating = False
				message.send("更新が終了しました")
				break
		else:
			message.send("無効な入力です")