from scrape import Saru
from create_database import DBManager
from time import sleep
import sys


if __name__ == '__main__':
    args = sys.argv
    while(True):
        for music_level in range(int(args[1]),int(args[2])+1):
            saru = Saru("config.yml")
            for i in [0, 2, 5, 7, 9]:
                sleep(i)
                if saru.login():
                    break
                else:
                    pass
            else:
                break
            saru.set_rival_ids("rival_ids.yml")
            # jsonで各プレイヤーのスコアを保存するところまで
            if saru.save_score(music_level):
                dbManager = DBManager("rival_ids.yml", "slack_config.yml")
                dbManager.set_database("SARU_SCORE")
                dbManager.create_database(music_level)
                dbManager.compare_score(music_level)
            else:
                # コネクションが切れたら最初の難易度からやり直し
                break
        print("数時間後また")
        sleep(60*60*6)