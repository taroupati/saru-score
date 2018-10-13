import json
import yaml


class DBManager():
    def __init__(self):
        import mysql.connector
        self.conn = mysql.connector.connect(user='root', password='mysql', host='localhost')
        self.cur = self.conn.cursor()
    
    def set_database(self, db_name):
        self.cur.execute(f"use {db_name};")
        self.conn.commit()
    
    def create_table(self, player_name):
        sql = f"""
            create table {player_name}_SCORE (
                曲名 varchar(200),
                難易度 varchar(20),
                レベル integer,
                スコア integer,
                クリアマーク varchar(10)
            );
        """
        self.cur.execute(sql)
        self.conn.commit()

    def insert_data(self, table_name, data, music_level):
        for score_data in data:
            for music_name, scores in score_data.items():
                # TODO とりあえずシングルに統一（エスケープシーケンス入れる）
                music_name = music_name.replace('"', "'")
                for difficulty, score in scores.items():
                    if score[0] > 0:
                        sql = f"""
                            insert into {table_name} values ("{music_name}", "{difficulty}", {music_level}, {score[0]}, "{score[1]}")
                        """
                        # TODO use multiple insert
                        self.cur.execute(sql)
                        self.conn.commit()


if __name__ == '__main__':
    dbManager = DBManager()
    dbManager.set_database("SARU_SCORE")
    with open("rival_ids.yml", 'r') as f:
        data = yaml.load(f)
        rival_ids = {}
        for k, v in data.items():
            rival_ids[k] = v

    dbManager.create_table("MY")
    # ライバルごとのテーブルを作成
    for rival_name in rival_ids.keys():
        dbManager.create_table(rival_name)
    # import pdb; pdb.set_trace()
    
    for music_level in range(17, 21):
        with open(f'score_data/{music_level}/my_score.json', encoding="utf-8") as f:
            my_data = json.load(f)
        with open(f'score_data/{music_level}/rival_score.json', encoding="utf-8") as f:
            rival_data = json.load(f)
        # TODO レベルが文字列で入っちゃってる問題
        dbManager.insert_data("MY_SCORE", my_data[str(music_level)], music_level)
        for rival_name in rival_ids.keys():
            dbManager.insert_data(f"{rival_name}_SCORE", rival_data[rival_name][str(music_level)], music_level)
            # import pdb; pdb.set_trace()
