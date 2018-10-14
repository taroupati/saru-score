import json
import yaml
import pandas as pd


class DBManager():
    def __init__(self, rival_ids):
        with open(rival_ids, 'r') as f:
            data = yaml.load(f)
        self.rival_ids = {}
        for k, v in data.items():
            self.rival_ids[k] = v

        import mysql.connector
        self.conn = mysql.connector.connect(user='root', password='mysql', host='localhost')
        self.cur = self.conn.cursor()
        self.mark_table={
            "NC": 0,
            "C": 1,
            "EX": 2,
            "UC": 3,
            "P": 4
        }
    
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
                クリアマーク varchar(10),
                primary key(曲名, 難易度)
            );
        """
        try:
            self.cur.execute(sql)
        except Exception as e:
            return e
        self.conn.commit()
    
    def reset_database(self, rival_name):
        sql = f"""
            delete from {rival_name}_SCORE;
        """
        try:
            self.cur.execute(sql)
        except Exception as e:
            return e
        self.conn.commit()

    def insert_data(self, table_name, data, music_level):
        # TODO updateの方法
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
        print(f"{table_name} level:{music_level} insert 完了")
    
    def get_compare_table(self, rival_name, music_level):
        # TODO 比較条件の指定
        sql = f"""
            select A.曲名, A.難易度, A.レベル, A.スコア,  A.クリアマーク, B.スコア as スコアB, B.クリアマーク as クリアマークB
            from MY_SCORE as A
            join {rival_name}_SCORE as B
            on A.曲名 = B.曲名 AND A.難易度 = B.難易度;
        """
        # pandas でMySQLテーブルを読む
        df_read = pd.read_sql(sql, self.conn)
        return df_read[((df_read.クリアマーク.map(lambda x:self.mark_table[x]) < df_read.クリアマークB.map(lambda x:self.mark_table[x])) | (df_read.スコア <= df_read.スコアB)) & (df_read.レベル==music_level)]

    def get_updated_score(self, table, rival_name, music_level):
        try:
            pre_table = pd.read_csv(f"score_data/{music_level}/{rival_name}.csv", index_col=False)
        except Exception as e:
            print(e)
            return []
        music_list = pre_table["曲名"].values + "(" + pre_table["難易度"].values + ")"
        table["曲名難易度"] = table["曲名"].values + "(" + table["難易度"].values + ")"
        return table[~table["曲名難易度"].isin(music_list)]



    def create_database(self, music_level):
        # debug tableの初期化 
        # TODO updateにした方が良い
        print(self.reset_database("MY"))
        for rival_name in self.rival_ids.keys():
            print(self.reset_database(rival_name))

        print(self.create_table("MY"))
        # ライバルごとのテーブルを作成
        for rival_name in self.rival_ids.keys():
            print(self.create_table(rival_name))

        # TODO レベルが文字列で入っちゃってる問題
        with open(f'score_data/{music_level}/my_score.json', encoding="utf-8") as f:
            my_data = json.load(f)
        self.insert_data("MY_SCORE", my_data[str(music_level)], music_level)
        for rival_name in self.rival_ids.keys():
            with open(f'score_data/{music_level}/{rival_name}_score.json', encoding="utf-8") as f:
                rival_data = json.load(f)
            self.insert_data(f"{rival_name}_SCORE", rival_data[rival_name][str(music_level)], music_level)

    def compare_score(self, music_level):
        for rival_name in self.rival_ids.keys():
            table = self.get_compare_table(rival_name,music_level)
            new_table = self.get_updated_score(table, rival_name, music_level)
            if len(new_table) > 0:
                print(f"{rival_name}に抜かれました。")
                print(new_table)
            table.to_csv(f"score_data/{music_level}/{rival_name}.csv", index=False)
