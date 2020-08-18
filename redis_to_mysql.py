import requests
import lxml.etree
import selenium.webdriver
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import MySQLdb
import cchardet
import json
import configparser
import redis
import time

def insert_to_mysql(data):
    data = json.loads(data)
    tablename = "tbl_news"

    org_url = data["org_url"]
    org_name = data["org_name"]
    exotic = int(data["exotic"])
    source_title = data["source_title"]
    publish_time = data["publish_time"]
    thumbnail_url = data["publish_time"]
    module_code = data["module_code"]

    insertsql = "INSERT INTO " + tablename + "(org_url,org_name,exotic,source_title,publish_time,thumbnail_url,module_code)  " \
                                             "VALUES ('{}','{}',{},'{}','{}','{}','{}')".format(org_url, org_name,
                                                                                                     exotic,
                                                                                                     source_title,
                                                                                                     publish_time,
                                                                                              thumbnail_url,module_code)
    swtich = False
    try:
        print(insertsql)
        cursor.execute(insertsql)
        news_id = db.insert_id()
        db.commit()
        swtich = True
    except:
        print("mysql error 111111111111111111")

    content_data = {}
    if swtich:
        content_data["news_id"] = int(news_id)
        content_data["source_content"] = data["source_content"]
        content_data["source_html"] = data["source_content"]
        insert_content(content_data)


def insert_content(content_data):
    news_id = int(content_data["news_id"])
    source_content = content_data["source_content"]
    source_html = content_data["source_html"]


    tablename = "tbl_news_content"

    insertsql = "INSERT INTO " + tablename + "(news_id,source_content,source_html,target_content)  " \
                                             "VALUES ('{}','{}',{},'123')".format(news_id,source_content,source_html)

    # sql = "INSERT INTO tbl_news_content VALUES (%s, %s, %s,null)"
    # values = (news_id,source_content,source_html)
    #
    # print(insertsql)
    # cursor.execute(sql,values)
    # db.commit()

    try:
        cursor.execute(insertsql)
        db.commit()
    except:
        print("content error 111111111111111111")

def go():
    while True:
        oneData = myRedis.lpop(data_key_name)
        if oneData:
            insert_to_mysql(oneData)
        else:
            print(11111111111111)
            time.sleep(10)


if __name__=="__main__":
    #获取redis
    configPath = "config.ini"
    WebConfig = configparser.ConfigParser()
    WebConfig.read(configPath, encoding='utf-8-sig')
    redisHost = WebConfig.get("redis", "host")
    redisPort = WebConfig.get("redis", "port")
    redisPassword = WebConfig.get("redis", "password")
    redisDb = WebConfig.get("redis", "database")
    redis_platform_address = WebConfig.get("redis", "redis_platform_address")
    data_key_name = redis_platform_address+":temporary"

    myRedis = redis.Redis(host=redisHost, port=redisPort, decode_responses=True, password=redisPassword, db=redisDb)


    datab = {
        "start_url": "http://www.yeeworld.com/article/hangye.html",
        "second_page_value": 2,
        # "end_page_value": 373,#################################################################################
        "end_page_value": 3,
        "url_type": "http://www.yeeworld.com/article/hangye/p/%d.html",
        "lineListXpath": "//h4/../@href",
        "source_titleXpath": "//h1/text()",
        "contentXpath": "//div[@class='syyd_yiwen_info'][1]/p/text()|//div[@class='syyd_yiwen_info'][1]/div/p/text()",
        "imageXpath": "//div[@class='syyd_yiwen_info'][1]/div/img/@src|//div[@class='syyd_yiwen_info'][1]/p/img/@src",
        "sourceXpath": "译世界",
        "dateXpath": "//div[@class='zixun_info_title'][2]/text()[3]",
        "source_htmlXpath":"//div[@class='syyd_yiwen_info']",
        "exotic":0,
    }
    db = MySQLdb.connect(host="192.168.1.250", user="root", passwd="Admin@123!", db="pt_content_db", charset='utf8')
    cursor = db.cursor()

    # id_sql = "max(id)"
    # a = cursor.execute(id_sql)
    # print(a)

    go()
