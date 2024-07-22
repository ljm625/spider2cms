from curl_cffi.requests import AsyncSession
import curl_cffi.requests as requests
import undetected_chromedriver as uc 
import asyncio
from bs4 import BeautifulSoup
import re

class Jable(object):

    def __init__(self,url,db):
        self.url = url
        self.db =db
        self.user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        self.cookie = ""
        self.classes=["latest-updates","new-release","hot"]
        self.mapping={}
        pass


    async def bypass_cf_get_cookie(self):
        options = uc.ChromeOptions() 
        options.add_argument("--headless") 
        options.add_argument(f"--user-agent="+self.user_agent)

        driver = uc.Chrome(options=options) 
        driver.get(self.url)
        await asyncio.sleep(1)
        cookie_dict = {}
        count = 0
        while not cookie_dict.get("cf_clearance"):
            cookies = driver.get_cookies()
            for cookie in cookies:
                cookie_dict[cookie['name']]=cookie['value']
            if count>=1:
                await asyncio.sleep(3)
            if count>3:
                driver.quit()
                raise Exception("Failed to retrive cookie, quit")
        
        cookie_header = f'PHPSESSID={cookie_dict["PHPSESSID"]}; kt_tcookie=1; kt_ips={cookie_dict["kt_ips"]}; cf_clearance={cookie_dict["cf_clearance"]}; __cf_bm={cookie_dict["__cf_bm"]}',
        print(cookie_header[0])
        self.cookie = cookie_header[0]
        driver.quit()
        return True




    async def get_class(self):
        class_list=[]
        class_list.append({"type_id": 1, "type_name": '最近更新'})
        class_list.append({"type_id": 2, "type_name": '全新上市'})
        class_list.append({"type_id": 3, "type_name": '最热'})

        result = await self.__get_request(self.url+"/latest-updates/",{})
        if result:
            soup = BeautifulSoup(result, 'html.parser')
            videos = soup.select("div.video-img-box")
            print(videos)
            for video in videos:
                url = video.find("a")["href"]
                img = video.find("img")["data-src"]
                name = video.find("h6").get_text().strip()
                extra = ""
                vod_id = re.search(r"videos\/(.*)\/",url)[1]

                video_info = {}


    async def get_videos_by_class():
        pass

    async def get_video():
        pass

    async def __get_request(self,url,params,retry=False):
        if not self.cookie:
            await self.bypass_cf_get_cookie()
        headers={
            "user-agent": self.user_agent,
            'cookie': self.cookie,
        }
        async with AsyncSession(impersonate="chrome",headers=headers) as s:
            r = await s.get(url)
            if(r.status_code==403) and not retry:
                self.cookie=""
                print("Cookie is invalid, cleared")
                return await self.__get_request(url,params,retry=True)
            print(r.status_code)
            if(r.status_code==200):
                return r.text

    def __name_to_id(self,name):
        if not self.mapping:
            try:
                cur = self.db.cursor()
                infos = cur.execute("SELECT * FROM jable").fetchall()
                print(infos)
                for info in infos:
                    self.mapping[info[1]]=info[0]
            except Exception as e:
                self.__init_db()
        prefix = name.split("-")[0]
        num = name.split("-")[1]
        if not self.mapping.get(prefix):
            max_id=0
            max_id_query = self.db.execute(f"SELECT max(id) FROM jable").fetchone()
            if(max_id_query[0]):
                max_id = int(max_id_query[0])+1
            self.db.execute(f"INSERT INTO jable VALUES ({max_id}, '{prefix}')")
            self.db.commit()
            infos = cur.execute("SELECT * FROM jable").fetchall()
            print(infos)
            for info in infos:
                self.mapping[info[1]]=info[0]
        return self.mapping.get(prefix)

    def __id_to_name(self,id):
        pass

    def __init_db(self):
        cur = self.db.cursor()
        self.db.execute("CREATE TABLE jable(id INT PRIMARY KEY, name VARCHAR(50) NOT NULL);")
        self.db.commit()