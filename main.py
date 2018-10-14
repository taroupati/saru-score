from scrape import Saru
from create_database import DBManager
from time import sleep



if __name__ == '__main__':
    while(True):
        for music_level in range(17, 21):
            saru = Saru("config.yml")
            saru.set_rival_ids("rival_ids.yml")
            # jsonで各プレイヤーのスコアを保存するところまで
            if saru.save_score(music_level):
                dbManager = DBManager("rival_ids.yml")
                dbManager.set_database("SARU_SCORE")
                dbManager.create_database(music_level)
                dbManager.compare_score(music_level)
            else:
                # コネクションが切れたら最初の難易度からやり直し
                break
        sleep(60*60*2)