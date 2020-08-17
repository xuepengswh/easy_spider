import requests
import lxml.etree
import selenium.webdriver
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import MySQLdb
import cchardet

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

def insert_mysql(item):
    db = MySQLdb.connect(host="192.168.1.250", user="root", passwd="Admin@123!", db="pt_information_db", charset='utf8')
    cursor = db.cursor()
    tablename = "tbl_news"

    TITLE = item["TITLE"]
    CONTENT = item["CONTENT"]
    CONTENTABSTRACT = item["CONTENTABSTRACT"]
    LINKURL = item["LINKURL"]
    PUBLISHTIME = item["PUBLISHTIME"]
    FETCHTIME = item["FETCHTIME"]
    DATASOURCE = item["DATASOURCE"]
    TYPE = item["TYPE"]
    EMORATE = item["EMORATE"]


    insertsql = "INSERT INTO " + tablename + "(title,source_title,summary,thumbnail_url,module_code,org_url,org_name,source_code,source_name,source_type_code,status,exotic,important,click_num,remark,publish_time,create_time,update_time)  " \
                                             "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)" % \
                                                (TITLE,)

    cursor.execute(insertsql)
    db.commit()

def trans(trans_json):
    extract_recv = requests.post('http://47.93.50.159:6800/run', json=trans_json).json()
    return extract_recv

def get_summary(extract_send):
    summary = requests.post('http://47.93.220.180:8082/summary', json={'data': extract_send}).text
    return summary


def get_data(data,url):
    org_url = url   #org_url 来源网址
    org_name = data["sourceXpath"]   #org_name   来源网址名称
    exotic=data["exotic"]      #exotic 是否为外语   0默认是中文，1是外语


    ps = requests.get(url).text
    mytree = lxml.etree.HTML(ps)

    source_titleXpath = data["source_titleXpath"]  # 原文标题
    source_title = mytree.xpath(source_titleXpath)
    if source_title:
        source_title = source_title[0]
        source_title = source_title.replace("\r\n", "")
    else:
        source_title = ""

    contentXpath = data["contentXpath"]
    plist = mytree.xpath(contentXpath)  # content
    print(contentXpath)
    print(plist)
    content = " ".join(plist)
    source_content = content.replace("\r", " ").replace("\n", " ")  #原文内容

    #title
    #翻译后的标题
    #target_content 翻译内容

    source_htmlXpath = data["source_htmlXpath"]
    html_content = mytree.xpath(source_htmlXpath)  # html_content
    if html_content:
        html_content = lxml.etree.tostring(html_content[0], pretty_print=True, method='html', encoding='utf-8')
        codeStyle = cchardet.detect(html_content)["encoding"]
        source_html = html_content.decode(codeStyle, errors="ignore")
    else:
        source_html = ""

    #summary
    #摘要（翻译后）
    if exotic == 0: #中文
        title = source_title
        target_content = source_content
        summary = get_summary(target_content)
    else:   #外文
        extract_send = {
            'title': source_title,
            'source_content': source_content,
            'source_html': source_html,
            'type': 1
        }

        trans_json = trans(extract_send)    #掉用翻译接口
        title = trans_json["target_title"]
        target_content = trans_json["target_content"]
        summary = get_summary(target_content)



    imageXpath = data["imageXpath"]  # thumbnail_url缩略图地址
    dateXpath = data["dateXpath"]   # publish_time

    #module_code   模块类型编码：行业资讯、产品动态、翻译学习、NLP...
            #翻译资讯,翻译学习,双语阅读,自然语言处理


    endData = {"org_url":org_url,
               "org_name":org_name,
               "exotic":exotic,
               "source_title":source_title,
               "source_content":source_content,
               "source_html":source_html,
               "title":title,
               "target_content":target_content,
               "summary":summary,
               }

    print(endData)



    #  默认
    #source_code    来源代码
    #source_name    来源名称
    #source_type_code   来源类型编码
    #status 默认1
    #important  是否重点新闻：0.否 1.是
    #click_num  点击次数
    #remark 备注
    #create_time
    #update_time




if __name__=="__main__":
    data = {
        "start_url": "http://www.yeeworld.com/article/hangye.html",
        "second_page_value": 2,
        # "end_page_value": 373,#################################################################################
        "end_page_value": 5,
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
    for url in tt(data):
        get_data(data,url)
        # try:
        #     get_data(url)
        # except:
        #     print(111111111111111111)



