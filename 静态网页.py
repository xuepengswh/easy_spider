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

def get_urlList(data):
    url_type = data["url_type"]
    start_url = data["start_url"]
    second_page_value = data["second_page_value"]
    end_page_value = data["end_page_value"]
    urlList = [url_type % x for x in range(second_page_value, end_page_value)]
    urlList.append(start_url)
    return urlList

def tt(data):
    endlist = []
    lineListXpath = data["lineListXpath"]
    if "selenium" in data.keys():
        mydriver = selenium.webdriver.Chrome()
        for url in get_urlList(data):
            # ps = requests.get(url).text
            mydriver.get(url)
            ps = mydriver.page_source
            mytree = lxml.etree.HTML(ps)

            lineList = mytree.xpath(lineListXpath)
            for i in lineList:
                endUrl = urljoin(url,i)
                endlist.append(endUrl)
        return endlist
    else:
        for url in get_urlList(data):
            ps = requests.get(url).text
            mytree = lxml.etree.HTML(ps)
            lineList = mytree.xpath(lineListXpath)
            for i in lineList:
                endUrl = urljoin(url, i)
                endlist.append(endUrl)
        return endlist

def get_data(dataa,url):
    org_url = url   #org_url 来源网址
    org_name = dataa["sourceXpath"]   #org_name   来源网址名称
    exotic=dataa["exotic"]      #exotic 是否为外语   0默认是中文，1是外语
    module_code = dataa["module_code"]

    ps = requests.get(url).text
    mytree = lxml.etree.HTML(ps)

    source_titleXpath = dataa["source_titleXpath"]  # 原文标题
    source_title = mytree.xpath(source_titleXpath)
    if source_title:
        source_title = source_title[0]
        source_title = source_title.replace("\r\n", "")
    else:
        source_title = ""

    contentXpath = dataa["contentXpath"]
    plist = mytree.xpath(contentXpath)
    content = " ".join(plist)
    source_content = content.replace("\r", " ").replace("\n", " ")  #原文内容


    source_htmlXpath = dataa["source_htmlXpath"]
    html_content = mytree.xpath(source_htmlXpath)  # html_content
    if html_content:
        html_content = lxml.etree.tostring(html_content[0], pretty_print=True, method='html', encoding='utf-8')
        codeStyle = cchardet.detect(html_content)["encoding"]
        source_html = html_content.decode(codeStyle, errors="ignore")
    else:
        source_html = ""

    imageXpath = dataa["imageXpath"]  # thumbnail_url缩略图地址
    image = mytree.xpath(imageXpath)
    if image:
        image = image[0]
    else:
        image = ""

    dateXpath = dataa["dateXpath"]   # publish_time
    datee = mytree.xpath(dateXpath)
    if datee:
        datee = datee[0]
    else:
        datee = ""

    #module_code   模块类型编码：行业资讯、产品动态、翻译学习、NLP...
            #翻译资讯,翻译学习,双语阅读,自然语言处理
    endData = {"org_url":org_url,
               "org_name":org_name,
               "exotic":exotic,
               "source_title":source_title,
               "source_content":source_content,
               "source_html":source_html,
               "publish_time":datee,
               "thumbnail_url":image,
               "module_code":module_code,
               }


    insert_data_to_redis(endData)
    #  默认
    #title翻译后的标题
    #target_content 翻译内容
    #summary摘要（翻译后）
    #source_code    来源代码
    #source_name    来源名称
    #source_type_code   来源类型编码
    #status 默认1
    #important  是否重点新闻：0.否 1.是
    #click_num  点击次数
    #remark 备注
    #create_time
    #update_time

def insert_data_to_redis(data):
    data = json.dumps(data)
    print(data)
    tempStore_url_key_name = redis_platform_address+":temporary"  # 暂时的存储
    myRedis.lpush(tempStore_url_key_name, data)


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
    myRedis = redis.Redis(host=redisHost, port=redisPort, decode_responses=True, password=redisPassword, db=redisDb)

    datab = {
    "start_url":"http://www.yeeworld.com/article/hangye.html",
    "second_page_value":2,
    # "end_page_value":373,  ######################################################################
    "end_page_value": 3,
    "url_type":"http://www.yeeworld.com/article/hangye/p/%d.html",
    "lineListXpath":"//h4/../@href",
    "source_titleXpath":"//h1/text()",
    "contentXpath":"//div[@class='syyd_yiwen_info'][1]/p/text()|//div[@class='syyd_yiwen_info'][1]/div/p/text()",
    "imageXpath":"//div[@class='syyd_yiwen_info'][1]/div/img/@src|//div[@class='syyd_yiwen_info'][1]/p/img/@src",
    "sourceXpath":"译世界",
    "dateXpath":"//div[@class='zixun_info_title'][2]/text()[3]",

    "source_htmlXpath":"//div[@class='syyd_yiwen_info']",
    "exotic":0,
    "module_code":"1001",
    }

    db = MySQLdb.connect(host="192.168.1.250", user="root", passwd="Admin@123!", db="pt_information_db", charset='utf8')
    cursor = db.cursor()
    for url in tt(datab):
        get_data(datab,url)
        # try:
        #     get_data(datab,url)
        # except:
        #     print("mysql error",111111111111111111)
