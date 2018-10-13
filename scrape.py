import requests
from bs4 import BeautifulSoup

class Saru():
    def __init__(self, config):
        import yaml
        f = open(config, 'r')
        data = yaml.load(f)
        self.post_data = {
            "KID": data["KID"],
            "pass": data["pass"],
            "OTP": ""
        }
        f.close()
        self.LOGIN_URL = "https://p.eagate.573.jp/gate/p/login.html"
        self.RIVAL_URL = "https://p.eagate.573.jp/game/sdvx/iv/p/playdata/rival/score.html"
        self.session = requests.Session()

        # TODO page_numで各難易度のページ数を取得しておく
        self.level_pages = {
            17: 18,
            18: 11,
            19: 3,
            20: 1
        }
    
    def set_rival_ids(self, rival_ids):
        import yaml
        f = open(rival_ids, 'r')
        data = yaml.load(f)
        self.rival_ids = {}
        for k, v in data.items():
            self.rival_ids[k] = v
        f.close()

    def set_queries(self):
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
            urllib.request.urlretrieve(url,"imgs/"+str(i)+".png")
    
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

        target_img_path = "imgs/" + TARGET_FILE
        target_img = cv2.imread(target_img_path)
        target_img = cv2.resize(target_img, IMG_SIZE)
        target_hist = cv2.calcHist([target_img], [0], None, [256], [0, 256])

        print('TARGET_FILE: %s' % (TARGET_FILE))

        scores = {}
        files = os.listdir("imgs")
        for i, file in enumerate(files):
            if file == '.DS_Store' or file == TARGET_FILE:
                continue

            comparing_img_path = "imgs/" + file
            comparing_img = cv2.imread(comparing_img_path)
            comparing_img = cv2.resize(comparing_img, IMG_SIZE)
            comparing_hist = cv2.calcHist([comparing_img], [0], None, [256], [0, 256])

            ret = cv2.compareHist(target_hist, comparing_hist, 0)
            scores[i-1] = ret
            print(file, ret)

        return scores

    def choice_image(self):
        scores = self.get_similarity()
        scores = sorted(scores.items(), key=lambda x: -x[1])
        for i in range(2):
            name = "chk_c" + str(scores[i][0])
            self.post_data[name] = self.image_values[scores[i][0]]
    
    def login(self):
        self.set_queries()
        # from time import sleep
        # sleep(2)
        r = self.session.post(self.LOGIN_URL, data=self.post_data)
        r.encoding = r.apparent_encoding
        # TODO ログインに成功したかどうか確認する
    
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
        return r
    
    def save_my_scores(self):
        pass
    
    def get_rival_scores(self, rival_name, music_level):
        score_data = {}
        score_data[rival_name] = {}
        self.session.post(self.RIVAL_URL, data={"rival_id": self.rival_ids[rival_name]})
        score_data[rival_name][music_level] = []

        for i in range(self.level_pages[music_level]):
            html = self.get_rival_score_page(self.rival_ids[rival_name], music_level, i+1)
            soup = BeautifulSoup(html.text, "html.parser")
            music_list = soup.find_all('span', id="music_name")
            music_names = []
            for name in music_list:
                music_names.append(name.text)
            rival_scores_3 = []
            for score in soup.find_all('td', id="score_col_3"):
                rival_scores_3.append(score.text)
            rival_scores_4 = []
            for score in soup.find_all('td', id="score_col_4"):
                rival_scores_4.append(score.text)
            for i, name in enumerate(music_names):
                rival_score = {name: "0"}
                for j in range(3):
                    if rival_scores_3[i*3+j] != "--0":
                        rival_score[name] = rival_scores_3[i*3+j]
                for j in range(2):
                    if rival_scores_4[i*2+j] != "--0":
                        rival_score[name] = rival_scores_4[i*2+j]
                score_data[rival_name][music_level].append(rival_score)
        return score_data


if __name__ == '__main__':
    saru = Saru("config.yml")
    saru.login()
    saru.set_rival_ids("rival_ids.yml")
    for rival_name in saru.rival_ids.keys():
        score = saru.get_rival_scores(rival_name, 19)
        import pdb; pdb.set_trace()



