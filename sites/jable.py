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
        video_list=[]
        result = await self.__get_request(self.url+"/latest-updates/",{})
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

        result = await self.__get_request(f"{self.url}/{url_key_word}/{page}/",{})
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
            last_page_num = int(re.search(r"\/(\d+)\/",last_page_link)[1])
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
        result = await self.__get_request(f"{self.url}/videos/{video_name}/",{})
        if result:
            soup = BeautifulSoup(result, 'html.parser')
            all_scripts = soup.select("script")
            video_url=""
            for script in all_scripts:
                if "hls" in str(script):
                    video_url = re.search(r"https:\/\/.*\.m3u8",str(script))[0]
                    break
            video_name = soup.select("title")[0].get_text()
            infos = soup.select("meta")
            for info in infos:
                if info.get("name"):
                    if info["name"]=="description":
                        desc = info["content"]
                    elif info["name"]=="keywords":
                        keywords= info["content"]
                    elif info["name"]=="author":
                        author= info["content"]
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
                            "vod_play_url": f'在线播放${video_url}',
                        },
                    ]
                    }
            return resp
        return {"code":0}

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
        if self.mapping.get(prefix) is None:
            max_id=0
            max_id_query = self.db.execute(f"SELECT max(id) FROM jable").fetchone()
            if(max_id_query[0] is not None):
                max_id = int(max_id_query[0])+1
            self.db.execute(f"INSERT INTO jable VALUES ({max_id}, '{prefix}')")
            self.db.commit()
            self.mapping[prefix]=max_id
        if self.mapping.get(prefix) is not None:
            mapped_id = f"1{str(self.mapping.get(prefix)).rjust(3,'0')}{num}"
            return mapped_id
        return None

    def __id_to_name(self,id):
        if not self.mapping:
            try:
                cur = self.db.cursor()
                infos = cur.execute("SELECT * FROM jable").fetchall()
                print(infos)
                for info in infos:
                    self.mapping[info[1]]=info[0]
            except Exception as e:
                self.__init_db()
        id_tmp=str(id)
        prefix_num=id_tmp[1:4]
        real_num=id_tmp[4:]
        prefix=""
        for pfx,num in self.mapping.items():
            if int(prefix_num)==num:
                prefix=pfx
                break
        int(prefix_num)
        if prefix:
            return f"{prefix}-{real_num}"
        return None

    def __init_db(self):
        cur = self.db.cursor()
        self.db.execute("CREATE TABLE jable(id INT PRIMARY KEY, name VARCHAR(50) NOT NULL);")
        self.db.commit()