# -*- coding: utf-8 -*-
"""
Created on 2024-03-21 16:54:16
---------
@summary:
---------
@author: Administrator
"""
import configparser
import datetime
import json
import os
import re
import time
import threading

import feapder
import requests
from loguru import logger
from retrying import retry

logger.add('logs.log', format="{time} {level} {message}", level="DEBUG", retention="5 days")
logger.add("sys.stdout", format="{time} {level} {message}", level="DEBUG", encoding="utf-8")

# config = configparser.ConfigParser()
# config.read('config.ini', encoding='utf-8')
current_directory = os.path.dirname(os.path.abspath(__file__))
config = configparser.ConfigParser()
config.read(current_directory + '/config.ini', encoding='utf-8')

file_path = config.get('info', 'file_path')
thread_count = int(config.get('info', 'thread_count'))
log_level = config.get('info', 'log_level')
proxies = json.loads(config.get('info', 'proxies'))

file_date = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H_%M_%S')
date_path = os.path.join(file_path, file_date)
os.mkdir(date_path, exist_ok=True)

meta_json = {"urls": []}
img_url_set = set()

# 图片下载
img_download_num = 0
img_not_download_num = 0
img_download_lock = threading.RLock()
img_not_download_lock = threading.RLock()
# 文件下载
file_download_num = 0
file_download_lock = threading.RLock()


class TravelskyirCom(feapder.AirSpider):
    __custom_setting__ = dict(
        LOG_LEVEL=log_level
    )
    def __init__(self, *args, **kwargs):
        super(TravelskyirCom, self).__init__(*args, **kwargs)
        self.url = 'https://www.travelskyir.com'

    def download_midware(self, request):
        # 这里使用代理使用即可
        request.proxies = proxies
        return request

    @retry(stop_max_attempt_number=3)
    def get_request(self, url, data=None):
        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Pragma": "no-cache",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            "X-Requested-With": "XMLHttpRequest"
        }
        if data:
            response = requests.post(url, headers=headers, data=data, verify=False, proxies=proxies)
        else:
            response = requests.get(url, headers=headers, proxies=proxies)
        return response

    def create_img(self, path_name, img_list):
        page_path = os.path.join(date_path, path_name)
        img_file_path = os.path.join(page_path, 'image')
        try:
            os.mkdir(img_file_path, exist_ok=True)
        except:
            return

        for img in img_list:
            if img.startswith('http'):
                img_url = img
            else:
                img_url = self.url + img
            img_name = img.split('/')[-1]
            if img_name.endswith('.jpg') or img_name.endswith('.png') or img_name.endswith('.gif'):
                img_name = img_name
            elif '?' in img_name:
                img_name = img_name.split('?')[0]
            else:
                img_name += '.jpg'
            global img_download_num, img_not_download_num
            img_path = os.path.join(img_file_path, img_name)
            if img_url not in img_url_set:
                img_data = self.get_request(img_url).content
                with open(img_path, 'wb') as f:
                    f.write(img_data)
                img_url_set.add(img_url)
                with img_download_lock:
                    img_download_num += 1
            else:
                with img_not_download_lock:
                    img_not_download_num += 1

    def create_file(self, path_name, file_data, url):
        page_path = os.path.join(date_path, path_name)
        try:
            os.mkdir(page_path, exist_ok=True)
        except:
            return
        txt_file_path = os.path.join(page_path, 'txt')
        os.mkdir(txt_file_path, exist_ok=True)
        file_name = os.path.join(txt_file_path, path_name) + '.txt'

        with open(file_name, 'w', encoding='utf8') as f:
            f.write(file_data)

        item = {}
        item['name'] = path_name
        item['url'] = url
        meta_json.get("urls").append(item)
        global file_download_num
        with file_download_lock:
            file_download_num += 1

    def get_file_name(self, url):
        if 'travelskyir.com' in url:
            file_name = url.split('travelskyir.com')[-1]
            file_name_list = file_name.split('/')
            name_list = []
            for i in file_name_list:
                if not i:
                    continue
                i = i.replace('.php', '').replace('?', '_').replace('=', '_')
                name_list.append(i)
            return '_'.join(name_list)
        else:
            print('不是采集域名, ' + url)

    def start_requests(self):
        url_list = ['https://www.travelskyir.com/{fl}/index.php', 'https://www.travelskyir.com/{fl}/about_profile.php',
                    'https://www.travelskyir.com/{fl}/about_development.php', 'https://www.travelskyir.com/{fl}/about_biz.php',
                    'https://www.travelskyir.com/{fl}/about_structure.php', 'https://www.travelskyir.com/{fl}/about_links.php',
                    'https://www.travelskyir.com/{fl}/ir_highlights.php', 'https://www.travelskyir.com/{fl}/ir_highlights_ir.php',
                    'https://www.travelskyir.com/{fl}/ir_report.php', 'https://www.travelskyir.com/{fl}/ir_info.php',
                    'https://www.travelskyir.com/{fl}/ir_alert.php', 'https://www.travelskyir.com/{fl}/ir_analyst.php',
                    'https://www.travelskyir.com/{fl}/news_media.php', 'https://www.travelskyir.com/{fl}/contact.php',
                    'https://www.travelskyir.com/{fl}/sitemap.php']

        date_url_list = ['https://www.travelskyir.com/{fl}/ir_report.php', 'https://www.travelskyir.com/{fl}/ir_circulars.php',
                         'https://www.travelskyir.com/{fl}/ir_operation.php', 'https://www.travelskyir.com/{fl}/ir_presentation.php',
                         'https://www.travelskyir.com/{fl}/ir_calendar.php', 'https://www.travelskyir.com/{fl}/news_press.php']

        # 免责声明
        sl_url = 'https://www.travelskyir.com/{fl}/disclaimer.php'

        # s 简中 c 繁中 html 英文
        fl_list = ['s', 'c', 'html']
        for fl in fl_list:
            for url in url_list:
                yield feapder.Request(url.format(fl=fl), callback=self.parse,  is_year='0')
            for date_url in date_url_list:
                yield feapder.Request(date_url.format(fl=fl), callback=self.parse, is_year='1')

            yield feapder.Request(sl_url.format(fl=fl), callback=self.parse1)

    def parse(self, request, response):
        if request.is_year == '1':
            texts_list = response.xpath('//select[@class="texts"]/option/text()').extract()[2:]
            for text in texts_list:
                url = request.url + '?year=' + str(text)
                yield feapder.Request(url, callback=self.parse, is_year='0')

        tt = response.bs4().get_text().strip().replace('\n', '__psq').replace(' ', '').replace('　　', '').replace('\t','').replace(' ', '')
        txt_data = re.sub(r'(__psq)+', '\n', tt)

        img_url_list = []
        img_tags = response.bs4().find_all('img')
        for img_tag in img_tags:
            img_url_list.append(img_tag['src'])
        img_url_list.append('https://www.travelskyir.com/img/menu/overbg.gif')
        if request.url in ['https://www.travelskyir.com/c/index.php', 'https://www.travelskyir.com/s/index.php',
                           'https://www.travelskyir.com/html/index.php']:
            img_url_list.append('https://www.travelskyir.com/img/banner.jpg')

        td_img_list = response.xpath("//td/@background").extract()
        for td in td_img_list:
            url = self.url + td[2:]
            img_url_list.append(url)

        img_url_list = set(img_url_list)
        file_name = self.get_file_name(request.url)
        self.create_file(file_name, txt_data, request.url)
        self.create_img(file_name, img_url_list)


    def parse1(self, request, response):
        tt = response.bs4().get_text().strip().replace('\n', '__psq').replace(' ', '').replace('　　', '').replace('\t','').replace(' ', '')
        txt_data = re.sub(r'(__psq)+', '\n', tt)

        img_url_list = ['https://www.travelskyir.com/s/img/hd/hd_disclaimer.gif', 'https://www.travelskyir.com/img/spacer.gif']
        file_name = self.get_file_name(request.url)
        self.create_file(file_name, txt_data, request.url)
        self.create_img(file_name, img_url_list)


if __name__ == "__main__":
    start_time = time.time()
    start_time_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))
    logger.debug(f'爬取中 gys_travelsky_com_cn 并行任务 {thread_count} 个')
    TravelskyirCom(thread_count=thread_count).start()

    while True:
        if len(threading.enumerate()) == 1:
            meta_json_path = os.path.join(date_path, 'meta.json')
            with open(meta_json_path, 'w', encoding='utf8') as f:
                json.dump(meta_json, f, ensure_ascii=False, indent=4)
            break
        time.sleep(3)

    end_time = time.time()
    end_time_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))
    logger.debug(f'{start_time_date} 开始 - {end_time_date} 结束 耗时{end_time - start_time}秒任务成功')
    logger.debug(
        f'本次共爬取{img_not_download_num + img_download_num + file_download_num}个元素 其中{file_download_num}个文本数据 {img_not_download_num + img_download_num}个图片数据，压缩重复元素{img_not_download_num}个，本地存储元素{img_download_num + file_download_num}个')
