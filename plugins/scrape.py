import requests
from bs4 import BeautifulSoup
import json
import yaml

class Saru():
    def __init__(self, config):
        self.config = config
        self.LOGIN_URL = "https://p.eagate.573.jp/gate/p/login.html"
        self.RIVAL_URL = "https://p.eagate.573.jp/game/sdvx/iv/p/playdata/rival/score.html"
        self.session = requests.Session()

        self.clear_mark = {
            "mark_per.png": "P",
            "mark_uc.png": "UC",
            "mark_comp_ex.png": "EX",
            "mark_comp.png": "C",
            "mark_play.png": "NC"
        }

        self.difficulty = {
            "NOV": "NOV",
            "ADV": "ADV",
            "EXH": "EXH",
            "MXM": "MXM",
            "HVN": "INF-GRV-HVN"
        }
        self.is_updating = False
    
    def set_rival_ids(self, rival_ids):
        with open(rival_ids, 'r') as f:
            data = yaml.load(f)
        self.rival_ids = {}
        self.scrape_rivals = {}
        for k, v in data.items():
            self.rival_ids[k] = v
            self.scrape_rivals[k] = True
    
    def set_update_rivals(self, rival_name, flag):
        self.scrape_rivals[rival_name] = flag

    def set_queries(self):
        with open(self.config, 'r') as f:
            data = yaml.load(f)
        self.post_data = {
            "KID": data["KID"],
            "pass": data["pass"],
            "OTP": ""
        }
        response = requests.get(self.LOGIN_URL)
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text)
        kcsess = soup.find(attrs={'name': 'kcsess'}).get('value')
        self.post_data["kcsess"] = kcsess
        self.download_images(soup)
        self.image_values = self.get_image_values(soup)
        self.choice_image()
    
    def download_images(self, soup):
        div = soup.find('div', style="height:112px;")
        img = div.find('img')
        image_urls = []
        image_urls.append(img["src"])
        
        divs = soup.find_all('img', style="width:100%;vertical-align:bottom")
        for img in divs:
            image_urls.append(img["src"])
        
        import urllib.request
        for i, url in enumerate(image_urls):
            urllib.request.urlretrieve(url,"plugins/imgs/"+str(i)+".png")
    
    def get_image_values(self, soup):
        divs = soup.find_all("input", style="position:absolute;top:2px;left:2px;width:initial;" )
        image_values = {}
        for i, div in enumerate(divs):
            image_values[i] = div["value"]
        return image_values
    
    def get_similarity(self):
        # https://qiita.com/best_not_best/items/c9497ffb5240622ede01
        import cv2
        import os

        TARGET_FILE = '0.png'
        IMG_SIZE = (100, 100)

        target_img_path = "plugins/imgs/" + TARGET_FILE
        target_img = cv2.imread(target_img_path)
        target_img = cv2.resize(target_img, IMG_SIZE)
        target_hist = cv2.calcHist([target_img], [0], None, [256], [0, 256])

        # print('TARGET_FILE: %s' % (TARGET_FILE))

        scores = {}
        files = os.listdir("plugins/imgs")
        for i, file in enumerate(files):
            if file == '.DS_Store' or file == TARGET_FILE:
                continue

            comparing_img_path = "plugins/imgs/" + file
            comparing_img = cv2.imread(comparing_img_path)
            comparing_img = cv2.resize(comparing_img, IMG_SIZE)
            comparing_hist = cv2.calcHist([comparing_img], [0], None, [256], [0, 256])

            ret = cv2.compareHist(target_hist, comparing_hist, 0)
            scores[i-1] = ret
            # print(file, ret)

        return scores

    def choice_image(self):
        scores = self.get_similarity()
        scores = sorted(scores.items(), key=lambda x: -x[1])
        for i in range(2):
            name = "chk_c" + str(scores[i][0])
            self.post_data[name] = self.image_values[scores[i][0]]
    
    def login(self):
        self.set_queries()
        r = self.session.post(self.LOGIN_URL, data=self.post_data)
        r.encoding = r.apparent_encoding
        soup = BeautifulSoup(r.text)
        div = soup.find('a', href="https://p.eagate.573.jp/gate/p/logout.html")
        if div is None:
            print("ログインに失敗しました。")
            return False
        print("ログインに成功しました。")
        return True
    
    def get_rival_score_page(self, rival_id, level, page):
        post_data = {
            "rival_id": rival_id,
            "sort_id": 0,
            "chkLv"+str(level): "on",
            "Submit": "",
            "page": page
        }
        r = self.session.post(self.RIVAL_URL, data=post_data)
        r.encoding = r.apparent_encoding
        # # debug
        # with open("test.html", mode='w') as f:
        #     f.write(r.text)
        # import pdb; pdb.set_trace()

        return r
    
    def get_player_score(self, rival_name, music_level, my_score):
        score_data = {}
        if my_score:
            score_data[music_level] = []
        else:
            score_data[music_level] = []
        self.session.post(self.RIVAL_URL, data={"rival_id": self.rival_ids[rival_name]})
        page_num = 0
        while(True):
            page_num += 1
            html = self.get_rival_score_page(self.rival_ids[rival_name], music_level, page_num)
            soup = BeautifulSoup(html.text, "html.parser")
            music_list = soup.find_all('span', id="music_name")
            # 存在しないページに飛んだら楽曲データなし
            if len(music_list) == 0:
                break
            music_names = []
            for name in music_list:
                music_names.append(name.text)
            if my_score:
                player_scores_1 = soup.find_all('td', id="score_col_1")
                player_scores_2 = soup.find_all('td', id="score_col_2")
            else:
                player_scores_1 = soup.find_all('td', id="score_col_3")
                player_scores_2 = soup.find_all('td', id="score_col_4")

            for i, name in enumerate(music_names):
                player_score = {
                    name: {
                        "NOV": [0, "NP"],
                        "ADV": [0, "NP"],
                        "EXH": [0, "NP"],
                        "MXM": [0, "NP"],
                        "INF-GRV-HVN": [0, "NP"]
                    }
                }
                for j in range(3):
                    score = player_scores_1[i*3+j]
                    if score.text != "--0":
                        difficulty = self.difficulty[score.findPrevious().text]
                        player_score[name][difficulty] = [int(score.text), self.clear_mark[score.find("img")["src"][37:]]]
                for j in range(2):
                    score = player_scores_2[i*2+j]
                    if score.text != "--0":
                        difficulty = self.difficulty[score.findPrevious().text]
                        player_score[name][difficulty] = [int(score.text), self.clear_mark[score.find("img")["src"][37:]]]
                score_data[music_level].append(player_score)
            if my_score:
                print(f"MY_SCORE:{music_level}-{page_num} 取得完了")
            else:
                print(f"{rival_name}:{music_level}-{page_num} 取得完了")
        if my_score:
            print(f"MY score level:{music_level} 取得完了")
        else:
            print(f"{rival_name} score level:{music_level} 取得完了")
            
        return score_data

    def save_score(self, music_level):
        rival_score = {}
        my_score = {}
        
        for i, rival_name in enumerate(self.rival_ids.keys()):
            if i == 0:
                try:
                    my_score = self.get_player_score(rival_name, music_level, True)
                except Exception as e:
                    print(e)
                    return False
                text = json.dumps(my_score, ensure_ascii=False, indent=2)
                with open("plugins/score_data/"+str(music_level)+"/my_score.json", "w", encoding="utf-8") as f:
                    f.write(text)
            try:
                rival_score = self.get_player_score(rival_name, music_level, False)
            except Exception as e:
                print(e)
                return False
            text = json.dumps(rival_score, ensure_ascii=False, indent=2)
            with open("plugins/score_data/"+str(music_level)+f"/{rival_name}_score.json", "w", encoding="utf-8") as f:
                f.write(text)

        return True

