from curl_cffi.requests import AsyncSession
import curl_cffi.requests as requests
import undetected_chromedriver as uc 
import asyncio
from bs4 import BeautifulSoup
import re
from urllib.parse import urlencode, quote_plus


class FourKAV(object):

    def __init__(self,url,cur_api_url,db):
        self.url = url
        self.cur_api_url = cur_api_url
        self.name = "fourkav"
        self.db =db
        self.user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15"
        self.cookie = ""
        self.classes=["/","/tv/","/movie/"]
        self.classes_name=["最新视频","电视剧","电影"]
        self.mapping={}
        pass

    async def get_class(self):
        class_list=[]
        video_list=[]
        result = await self.__get_request(f"{self.url}",{})
        if result:
            soup = BeautifulSoup(result, 'html.parser')
            classes = soup.select("div#taglist > ul")[0].select("li")
            for new_class in classes:
                url = new_class.find("a")["href"]
                match = re.search(r"https:\/\/.*\/(.*)\/",url)
                if match:
                    new_class_name=url.split(self.url)[1]
                    name = new_class.find("a").get_text()
                    if new_class_name not in self.classes:
                        self.classes.append(new_class_name)
                        self.classes_name.append(name)
        for i in range(0,len(self.classes)):
            class_list.append({"type_id":i+1,"type_name": self.classes_name[i]})

        if result:
            soup = BeautifulSoup(result, 'html.parser')
            videos = soup.select("div.NTMitem")
            for video in videos:
                url = video.find("a")["href"]
                img = video.find("img")["src"]
                name = video.find(["h1","h2","h3","h4","h5","h6"]).get_text()
                extra = ""
                vod_id = self.__name_to_id(url)
                if not vod_id:
                    print(f"Fail to parse {url} skipped")
                    continue
                video_info = {
                    "vod_id":int(vod_id),
                    "vod_pic":img,
                    "vod_name":name,
                    "vod_remarks":extra
                }
                video_list.append(video_info)
        resp_data ={
            "code":1,
            "msg": "数据列表",
            "page": 1,
            "list": video_list,
            "class":class_list
        }
        return resp_data


    async def get_videos_by_class(self,class_id,page):
        video_list=[]
        url_key_word=""
        if class_id:
            class_id=int(class_id)
            if class_id>len(self.classes):
                class_id=1
                url_key_word=self.classes[class_id-1]
            else:
                url_key_word=self.classes[class_id-1]
        else:
            class_id=1
            url_key_word=self.classes[class_id-1]
        if not page:
            page=1

        last_page_num=1
        if page>1:
            result = await self.__get_request(f"{self.url}{url_key_word}",{})
            if result:
                soup = BeautifulSoup(result, 'html.parser')
            try:
                last_page_num = int(soup.select("span.page-number")[0].get_text().split("/")[1])
            except Exception as e:
                last_page_num = 1


        final_url = f"{self.url}{url_key_word}"
        if page>1:
            if last_page_num>1:
                final_url = f"{self.url}{url_key_word}page-{last_page_num+1-page}.html"

        result = await self.__get_request(final_url,{})
        if result:
            soup = BeautifulSoup(result, 'html.parser')
            videos = soup.select("div.NTMitem")
            for video in videos:
                url = video.find("a")["href"]
                img = video.find("img")["src"]
                name = video.find(["h1","h2","h3","h4","h5","h6"]).get_text()
                extra = ""
                extra = ""
                vod_id = self.__name_to_id(url)
                if not vod_id:
                    print(f"Fail to parse {url} skipped")
                    continue
                video_info = {
                    "vod_id":int(vod_id),
                    "vod_pic":img,
                    "vod_name":name,
                    "vod_remarks":extra
                }
                video_list.append(video_info)
            try:
                last_page_num = int(soup.select("span.page-number")[0].get_text().split("/")[1])
            except Exception as e:
                last_page_num = 1
        resp_data ={
            "code":1,
            "msg": "数据列表",
            "page": page,
            "pagecount": last_page_num,
            "limit": str(len(video_list)),
            "total": len(video_list)*last_page_num,
            "list": video_list,
        }
        return resp_data

    async def search_video(self,keyword,page):
        video_list=[]
        if not page:
            page=1

        result = await self.__get_request(f"{self.url}/search/{keyword}/{page}/",{})
        if result:
            soup = BeautifulSoup(result, 'html.parser')
            videos = soup.select("div.video-img-box")
            for video in videos:
                url = video.find("a")["href"]
                img = video.find("img")["data-src"]
                name = video.find("h6").get_text().strip()
                extra = ""
                vod_id = self.__name_to_id(re.search(r"videos\/(.*)\/",url)[1])
                if not vod_id:
                    print(f"Fail to parse {url} skipped")
                    continue
                video_info = {
                    "vod_id":int(vod_id),
                    "vod_pic":img,
                    "vod_name":name,
                    "vod_remarks":extra
                }
                video_list.append(video_info)
            last_page_link = soup.select("a.page-link")[-1]["href"]
            last_page_num = int(re.search(r"\/(\d+)\/$",last_page_link)[1])
        resp_data ={
            "code":1,
            "msg": "数据列表",
            "page": page,
            "pagecount": last_page_num,
            "limit": str(len(video_list)),
            "total": len(video_list)*last_page_num,
            "list": video_list,
        }
        return resp_data


    async def get_video(self,video_id):
        video_name = self.__id_to_name(video_id)
        result = await self.__get_request(f"{self.url}{video_name}",{})
        vod_play_list=[]
        if result:
            soup = BeautifulSoup(result, 'html.parser')
            all_episodes = soup.select("div.screenshot")
            for episode in all_episodes:
                try:
                    episode_url = episode.find("a")["href"]
                except Exception as e:
                    # This is probably current episode
                    episode_url = video_name
                episode_name = episode.find("span").get_text()
                vod_play_list.append(f'{episode_name}${self.cur_api_url}?{urlencode({"ac":"play","url":episode_url})}.m3u8')
            if len(vod_play_list)==0:
                vod_play_list.append(f'立即播放${self.cur_api_url}?{urlencode({"ac":"play","url":video_name})}.m3u8')
            video_name = "aaa"
            resp = {
                    "code": 1,
                    "msg": '数据列表',
                    "page": 1,
                    "pagecount": 1,
                    "limit": '20',
                    "total": 1,
                    "list": [
                        {
                            "vod_id": video_id,
                            "vod_name": video_name,
                            "vod_pic": '',
                            "vod_remarks": '',
                            "type_name": '',
                            "vod_year": '',
                            "vod_area": '',
                            "vod_actor": '',
                            "vod_director": '',
                            "vod_content": '',
                            "vod_play_from": '',
                            "vod_play_note": '',
                            "vod_play_url": "#".join(vod_play_list),
                        },
                    ]
                    }
            print(resp["list"][0]["vod_play_url"])
            return resp
        return {"code":0}

    async def get_video_play_url(self,url):
        real_url = url.split(".m3u8")[0]
        result = await self.__get_request(f"{self.url}{real_url}",{})
        if result:
            soup = BeautifulSoup(result, 'html.parser')
            play_url = soup.select("source")[0]["src"]
            resp = {"data":play_url}
            return resp
        return {"code":0}


    async def __get_request(self,url,params):
        headers={
            "user-agent": self.user_agent,
            "accept-language": "zh-CN,zh-Hans;q=0.9",
        }
        async with AsyncSession(impersonate="safari",headers=headers) as s:
            r = await s.get(url)
            print(f"{url} -- {r.status_code}")
            if(r.status_code==200):
                return r.text

    def __name_to_id(self,name):
        if not self.mapping:
            try:
                cur = self.db.cursor()
                infos = cur.execute(f"SELECT * FROM {self.name}").fetchall()
                print(infos)
                for info in infos:
                    self.mapping[info[1]]=info[0]
            except Exception as e:
                self.__init_db()
        id = int(re.search(r"\/([0-9]+)-.*\/$",name)[1])
        if self.mapping.get(name) is None:
            self.db.execute(f"INSERT INTO {self.name} VALUES ({id}, '{name}')")
            self.db.commit()
            self.mapping[name]=id
        if self.mapping.get(name) is not None:
            return self.mapping.get(name)
        return None

    def __id_to_name(self,id):
        if not self.mapping:
            try:
                cur = self.db.cursor()
                infos = cur.execute(f"SELECT * FROM {self.name}").fetchall()
                print(infos)
                for info in infos:
                    self.mapping[info[1]]=info[0]
            except Exception as e:
                self.__init_db()
        for pfx,num in self.mapping.items():
            if int(id)==num:
                return pfx
        return None

    def __init_db(self):
        cur = self.db.cursor()
        self.db.execute(f"CREATE TABLE {self.name}(id INT PRIMARY KEY, url VARCHAR(200) NOT NULL);")
        self.db.commit()