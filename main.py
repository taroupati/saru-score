from scrape import Saru
from create_database import DBManager
from time import sleep



if __name__ == '__main__':
    while(True):
        for music_level in range(20, 21):
            saru = Saru("config.yml")
            for i in [0, 2, 5]:
                sleep(i)
                if saru.login():
                    break
                else:
                    import pdb; pdb.set_trace()
                    pass
            else:
                break
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
            import pdb; pdb.set_trace()
        import pdb; pdb.set_trace()
        sleep(60*60*2)