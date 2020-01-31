# 爆搜所有(包括下架)的番剧,并存入mysql

import json
import pymysql
import requests
import threading
import time

class Spider_season:
    cursor = None
    db = None
    results = [] # 所有结果
    failed = [] # 失败的season_id

    def send_request(self, season_id):
        # 获取aid
        url = 'https://api.bilibili.com/pgc/web/season/section?season_id={}'
        result = requests.get(url.format(season_id))
        # print(result)
        # TODO 被封杀
        return json.loads(result.text)

    def get_view(self, aid):
        # 获取番剧名
        url = 'https://api.bilibili.com/x/web-interface/view?aid={}'
        result = requests.get(url.format(aid))
        view = json.loads(result.text)
        item = {
                "title": "NULL",
                "p_year": 0,
                "p_month": 0,
                "p_day": 0,
                "c_year": 0,
                "c_month": 0,
                "c_day": 0
                }
        if 'data' not in view:
            # 异常情况
            item['title'] = "仅限港澳台"
        else:
            pubdate = time.localtime(view['data']['pubdate'])
            ctime = time.localtime(view['data']['ctime'])
            item.update({
                "title": view['data']['title'],
                "p_year": pubdate.tm_year,
                "p_month": pubdate.tm_mon,
                "p_day": pubdate.tm_mday,
                "c_year": ctime.tm_year,
                "c_month": ctime.tm_mon,
                "c_day": ctime.tm_mday
                })
        return item

    def get_detail(self, season_id, num = 1):
        # 获取详细信息
        group = [] # 按组存放结果
        for i in range(num):
            result = self.send_request(season_id + i) # 爆搜season
            if result['code'] == 0: # 获取成功
                aid = 0
                ep_id = 0 # id 是关键字
                if 'main_section' in result['result']:
                    # TODO
                    aid = result['result']['main_section']['episodes'][0]['aid'] 
                    ep_id = result['result']['main_section']['episodes'][0]['id']
                else:
                    # TODO 没有版权
                    print(result, season_id + i)
                    self.failed.append(season_id + i)
                    continue
                item = {
                        "season_id": season_id + i,
                        "aid": aid,
                        "id": ep_id,
                        "title": "没有标题",
                        }
                view = self.get_view(aid) # 刷新aid, title
                item.update(view)
                print(item)
                group.append(item)
        self.results.extend(group)

    def init_sql(self):
        self.db = pymysql.connect(
                host = 'localhost',
                port = 3306, # 端口错误错误代码111
                user = 'niabie',
                passwd = None,
                db = 'bilibili',
                charset = 'utf8'
                )
        self.cursor = self.db.cursor()

    def insert_sql(self, item):
        if self.db == None:
            print("no database")
            return
        # if "'" in item['title']:
        #     # TODO 转义字符
        #     print(item)
        #     return
        cmd = 'insert into season (season_id, aid, id, title, p_year, p_month, p_day, c_year, c_month, c_day) values' + \
                '({}, {}, {}, \'{}\', {}, {}, {}, {}, {}, {});'
        cmd = cmd.format(
            item['season_id'], 
            item['aid'],
            item['id'],
            item['title'].replace("'", "''").replace("\\", ""),
            item['p_year'],
            item['p_month'],
            item['p_day'],
            item['c_year'],
            item['c_month'],
            item['c_day']
            )
        print(cmd)
        self.cursor.execute(cmd)

def test(self, text):
    print(text)

if __name__ == '__main__':
    my_spider = Spider_season()
    my_spider.init_sql()

    threads = []
    group_size = 1 # 每一个线程抓取的数量
    for i in range(3795, 3796):
        t = threading.Thread(
                target = my_spider.get_detail,
                args = (i * group_size, group_size))
        t.start()
        threads.append(t) # 加入线程list
        # 刷新数据库
    for t in threads:
        t.join()
    for item in my_spider.results:
        my_spider.insert_sql(item)

    my_spider.db.commit()
    my_spider.db.close()

    for f in my_spider.failed:
        print(f)
