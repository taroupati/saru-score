import json
import yaml
import pandas as pd
import requests


class DBManager():
    def __init__(self, rival_ids, slack_config):
        with open(rival_ids, 'r') as f:
            data = yaml.load(f)
        self.rival_ids = {}
        self.update_rivals = {}
        for k, v in data.items():
            self.rival_ids[k] = v
            self.update_rivals[k] = True

        import mysql.connector
        self.conn = mysql.connector.connect(user='root', password='mysql', host='localhost', port=3306)
        self.cur = self.conn.cursor()
        self.mark_table={
            "NC": 0,
            "C": 1,
            "EX": 2,
            "UC": 3,
            "P": 4
        }
        with open(slack_config, 'r') as f:
            data = yaml.load(f)
            self.slack_token = data["token"]
            self.slack_channel = data["channel"]
            self.slack_channel2 = data["channel2"]

    def set_update_rivals(self, rival_name, flag):
        self.update_rivals[rival_name] = flag
    
    def set_database(self, db_name):
        self.cur.execute(f"use {db_name};")
        self.conn.commit()
    
    def create_table(self, player_name, music_level):
        sql = f"""
            create table {player_name}_SCORE_{music_level} (
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
    
    def reset_database(self, rival_name, music_level):
        sql = f"""
            delete from {rival_name}_SCORE_{music_level};
        """
        try:
            self.cur.execute(sql)
        except Exception as e:
            return e
        self.conn.commit()
    
    def update_score(self, table_name, data, music_level):
        text = None
        for score_data in data:
            for music_name, scores in score_data.items():
                # TODO とりあえずシングルに統一（エスケープシーケンス入れる）
                music_name = music_name.replace('"', "'")
                for difficulty, score in scores.items():
                    if score[0] > 0:
                        sql = f"""
                            update {table_name}
                            set スコア = {score[0]}
                            where 曲名 = "{music_name}" and 難易度 = "{difficulty}"
                            and (スコア < {score[0]} OR クリアマーク <> "{score[1]}");
                        """
                        self.cur.execute(sql)
                        self.conn.commit()
                        # updateされなかったらinsert を試みる
                        if self.cur.rowcount == 0:
                            sql = f"""
                                insert into {table_name}
                                select "{music_name}", "{difficulty}", {music_level}, {score[0]}, "{score[1]}"
                                where not exists (
                                    select 曲名, 難易度 from {table_name} where 曲名 = "{music_name}" and 難易度 = "{difficulty}"
                                );
                            """
                            # TODO use multiple insert
                            self.cur.execute(sql)
                            self.conn.commit()
                            if self.cur.rowcount != 0:
                                # 新曲のスコア
                                if text is None:
                                    text = f"{table_name}が更新されました。\n ``` "
                                text += f"{music_name} : {difficulty} : {score[0]} ({score[1]})\n"
                        else:
                            # スコアが更新された
                            if text is None:
                                text = f"{table_name}が更新されました。\n ``` "
                            text += f"{music_name} : {difficulty} : {score[0]} ({score[1]})\n"
        print(f"{table_name} level:{music_level} update 完了")
        if text is not None:
            text += " ``` "
            self.send_message_to_slack(text)

    
    def get_compare_table(self, rival_name, music_level):
        # TODO 比較条件の指定
        sql = f"""
            select A.曲名, A.難易度, A.レベル, A.スコア,  A.クリアマーク, B.スコア as スコアB, B.クリアマーク as クリアマークB
            from MY_SCORE_{music_level} as A
            join {rival_name}_SCORE_{music_level} as B
            on A.曲名 = B.曲名 AND A.難易度 = B.難易度;
        """
        # pandas でMySQLテーブルを読む
        df_read = pd.read_sql(sql, self.conn)
        return df_read[(df_read.クリアマーク.map(lambda x:self.mark_table[x]) < df_read.クリアマークB.map(lambda x:self.mark_table[x])) | (df_read.スコア <= df_read.スコアB)]

    def get_updated_score(self, table, rival_name, music_level):
        try:
            pre_table = pd.read_csv(f"plugins/score_data/{music_level}/{rival_name}.csv", index_col=False)
        except Exception as e:
            print(e)
            return []
        music_list = pre_table["曲名"].values + "(" + pre_table["難易度"].values + ")"
        table["曲名難易度"] = table["曲名"].values + "(" + table["難易度"].values + ")"
        return table[~table["曲名難易度"].isin(music_list)]



    def create_database(self, music_level):
        # テーブルの作成
        print(self.create_table("MY", music_level))
        for rival_name in self.rival_ids.keys():
            print(self.create_table(rival_name, music_level))

        # TODO レベルが文字列で入っちゃってる問題
        with open(f'plugins/score_data/{music_level}/my_score.json', encoding="utf-8") as f:
            my_data = json.load(f)
        self.update_score(f"MY_SCORE_{music_level}", my_data[str(music_level)], music_level)
        for rival_name in self.rival_ids.keys():
            with open(f'plugins/score_data/{music_level}/{rival_name}_score.json', encoding="utf-8") as f:
                rival_data = json.load(f)
            self.update_score(f"{rival_name}_SCORE_{music_level}", rival_data[str(music_level)], music_level)

    def compare_score(self, music_level):
        for rival_name in self.rival_ids.keys():
            table = self.get_compare_table(rival_name,music_level)
            new_table = self.get_updated_score(table, rival_name, music_level)
            if len(new_table) > 0:
                text = f"{rival_name}に抜かれました。\n ``` "
                for index, row in new_table.iterrows():
                    text += "・" + row[0] + " (" + row[1] + ", " + str(row[2]) + ")\n" + str(row[5]) + " : " + row[6] + "\n"
                text += " ``` "
                self.send_message_to_slack(text)
            table.to_csv(f"plugins/score_data/{music_level}/{rival_name}.csv", index=False)

    def send_message_to_slack(self, text):
        url = "https://slack.com/api/chat.postMessage"
        post_data = {
            "token": self.slack_token,
            "channel": self.slack_channel,
            "text": text
        } 
        response = requests.post(url, data=post_data)
        post_data = {
            "token": self.slack_token,
            "channel": self.slack_channel2,
            "text": text
        } 
        response = requests.post(url, data=post_data)