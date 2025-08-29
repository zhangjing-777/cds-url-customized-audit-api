# -*- coding: utf-8 -*-
"""
Created on 2024-03-19 11:43:01
---------
@summary:
---------
@author: Administrator
"""
import base64
import configparser
import datetime
import io
import json
import os
import random
import re
import threading
import time

import feapder
import requests
from PIL import Image
from bs4 import BeautifulSoup
from retrying import retry


config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')

file_path = config.get('info', 'file_path')
thread_count = int(config.get('info', 'thread_count'))
log_level = config.get('info', 'log_level')

file_date = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H_%M_%S')
date_path = os.path.join(file_path, file_date)
os.mkdir(date_path)


meta_json = {"urls": []}
img_url_set = set()

url_set = set()
list_url_set = {'https://www.travelsky.cn/publish/main/1/3/13/index.html',
                'https://www.travelsky.cn/publish/main/1/3/13/index',
                'https://www.travelsky.cn/publish/main/1/3/14/index.html',
                'https://www.travelsky.cn/publish/main/1/3/14/index',
                'https://www.travelsky.cn/publish/main/1/5/777/index.html',
                'https://www.travelsky.cn/publish/main/1/5/777/index',
                'https://www.travelsky.cn/publish/main/1/6/index.html',
                'https://www.travelsky.cn/publish/main/1/6/index',
                'https://www.travelsky.cn/publish/main/17/19/index.html',
                'https://www.travelsky.cn/publish/main/17/19/index',
                'https://www.travelsky.cn/publish/main/17/20/index.html',
                'https://www.travelsky.cn/publish/main/17/20/index',
                'https://www.travelsky.cn/publish/main/17/1069/index.html',
                'https://www.travelsky.cn/publish/main/17/1069/index',
                'https://www.travelsky.cn/publish/main/17/21/index.html',
                'https://www.travelsky.cn/publish/main/17/21/index',
                'https://www.travelsky.cn/publish/main/17/22/index.html',
                'https://www.travelsky.cn/publish/main/17/22/index',
                'https://www.travelsky.cn/publish/main/17/23/index.html',
                'https://www.travelsky.cn/publish/main/17/23/index',
                'https://www.travelsky.cn/publish/main/17/3902/index.html',
                'https://www.travelsky.cn/publish/main/17/3902/index',
                'https://www.travelsky.cn/publish/main/38/64/145/index.html',
                'https://www.travelsky.cn/publish/main/38/64/145/index',
                'https://www.travelsky.cn/publish/english/402/421/index.html',
                'https://www.travelsky.cn/publish/english/402/421/index'
                }


class TravelskyCn(feapder.AirSpider):
    __custom_setting__ = dict(
        LOG_LEVEL=log_level
    )
    def __init__(self, *args, **kwargs):
        super(TravelskyCn, self).__init__(*args, **kwargs)
        self.url = "https://www.travelsky.cn"

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
            response = requests.post(url, headers=headers, data=data, verify=False)
        else:
            try:
                response = requests.get(url, headers=headers)
            except:
                print('访问失败', url)
                return None
        return response

    def create_img(self, path_name, img_list):
        page_path = os.path.join(date_path, path_name)
        img_file_path = os.path.join(page_path, 'image')
        try:
            os.mkdir(img_file_path)
        except:
            return

        for i, img in enumerate(img_list):
            if img.startswith('data:image/png;base64'):
                # 分离出 Base64 编码的部分
                base64_data = img.split(',')[1]
                # 解码 Base64 数据
                decoded_data = base64.b64decode(base64_data)
                # 创建一个 BytesIO 对象
                image_bytes = io.BytesIO(decoded_data)
                # 使用 PIL 打开 BytesIO 对象并保存为 PNG 文件
                image = Image.open(image_bytes)
                img_path = os.path.join(img_file_path, f't_png_{random.randint(1,100)}.png')
                image.save(img_path)
                continue

            if img.startswith('http'):
                img_url = img
            else:
                img_url = self.url + img
            img_name = img.split('/')[-1]
            if img_name.endswith('.jpg') or img_name.endswith('.png') or img_name.endswith('.gif'):
                img_name = img_name
            else:
                img_name += '.jpg'
            img_path = os.path.join(img_file_path, img_name)

            if img_url not in img_url_set:
                img_response = self.get_request(img_url)
                if img_response:
                    img_data = img_response.content
                    with open(img_path, 'wb') as f:
                        f.write(img_data)
                    img_url_set.add(img_url)

    def create_file(self, path_name, file_data, url):
        page_path = os.path.join(date_path, path_name)
        try:
            os.mkdir(page_path)
        except:
            return
        txt_file_path = os.path.join(page_path, 'txt')
        os.mkdir(txt_file_path)
        file_name = os.path.join(txt_file_path, path_name) + '.txt'

        with open(file_name, 'w', encoding='utf8') as f:
            f.write(file_data)

        item = {}
        item['name'] = path_name
        item['url'] = url
        meta_json.get("urls").append(item)

    def get_file_name(self, url):
        if 'travelsky.cn' in url:
            file_name = url.split('travelsky.cn')[-1]
            file_name_list = file_name.split('/')
            name_list = []
            for i in file_name_list:
                if not i:
                    continue
                if i.endswith('.html'):
                    i = i.replace('.html', '')
                name_list.append(i)
            return '_'.join(name_list)
        else:
            print('不是采集域名, ' + url)

    def start_requests(self):
        start_url_list = []
        # 首页
        yield feapder.Request("https://www.travelsky.cn/publish/main/index.html", callback=self.main_index)
        # 关于我们
        start_url_list.append("https://www.travelsky.cn/publish/main/1/index.html")
        # 新闻中心
        start_url_list.append("https://www.travelsky.cn/publish/main/17/index.html")
        # 业务板块
        start_url_list.append("https://www.travelsky.cn/publish/main/27/index.htmll")
        # 服务中心
        start_url_list.append("https://www.travelsky.cn/publish/main/37/index.html")
        # 人力资源
        start_url_list.append("https://www.travelsky.cn/publish/main/38/index.html")
        # 责任与创新
        start_url_list.append("https://www.travelsky.cn/publish/main/40/78/index.html")

        # 关于我们 - 发展历程 - 更多
        start_url_list.append("https://www.travelsky.cn/publish/main/1/5/777/index.html")
        # 新闻中心 - 轮播图
        xw_list = ["https://www.travelsky.cn/publish/main/17/338/2019/03/13/20190313110057467325652/index.html",
                   "https://www.travelsky.cn/publish/main/17/338/2019/03/12/20190312174325561713860/index.html",
                   "https://www.travelsky.cn/publish/main/17/338/2019/05/29/20190529133102343158910/index.html",
                   "https://www.travelsky.cn/publish/main/17/338/2019/05/15/20190515104455157813875/index.html",
                   "https://www.travelsky.cn/publish/main/17/338/2019/05/06/20190506171821411786921/index.html"]
        start_url_list.extend(xw_list)

        for start_url in start_url_list:
            yield feapder.Request(start_url, callback=self.main_1_index)
            url_set.add(start_url)

        # 法律声明
        yield feapder.Request("https://www.travelsky.cn/publish/main/309/index.html", callback=self.main_2_index)
        url_set.add('https://www.travelsky.cn/publish/main/309/index.html')
        # 联系我们
        yield feapder.Request("https://www.travelsky.cn/publish/main/310/index.html", callback=self.main_2_index)
        url_set.add("https://www.travelsky.cn/publish/main/310/index.html")
        # 使用帮助
        yield feapder.Request("https://www.travelsky.cn/publish/main/311/index.html", callback=self.main_2_index)
        url_set.add("https://www.travelsky.cn/publish/main/311/index.html")
        # 网站地图
        yield feapder.Request("https://www.travelsky.cn/publish/main/312/index.html", callback=self.main_2_index)
        url_set.add("https://www.travelsky.cn/publish/main/312/index.html")
        # 集团网群
        yield feapder.Request("https://www.travelsky.cn/publish/main/310/index.html", callback=self.main_2_index, jq='1')
        url_set.add("https://www.travelsky.cn/publish/main/310/index.html")

        # RSS订阅
        yield feapder.Request("https://www.travelsky.cn/publish/main/128/index.html", callback=self.parse)
        url_set.add("https://www.travelsky.cn/publish/main/128/index.html")

        # 学思想
        yield feapder.Request("https://www.travelsky.cn/publish/main/17/24/4481/4482/index.html", callback=self.main_3_index)
        url_set.add("https://www.travelsky.cn/publish/main/17/24/4481/4482/index.html")

        # english
        english_start_url_list = []
        # 首页
        yield feapder.Request("https://www.travelsky.cn/publish/main/index.html", callback=self.english_index)
        # 关于我们
        english_start_url_list.append("https://www.travelsky.cn/publish/main/1/index.html")
        # 新闻中心
        english_start_url_list.append("https://www.travelsky.cn/publish/english/402/index.html")
        # 业务板块
        english_start_url_list.append("https://www.travelsky.cn/publish/english/403/index.html")
        # 服务中心
        english_start_url_list.append("https://www.travelsky.cn/publish/english/404/index.html")
        # 人力资源
        english_start_url_list.append("https://www.travelsky.cn/publish/english/405/index.html")
        # 责任与创新
        english_start_url_list.append("https://www.travelsky.cn/publish/english/407/index.html")

        for start_url in english_start_url_list:
            yield feapder.Request(start_url, callback=self.english_1_index)
            url_set.add(start_url)
        #
        # # 法律声明
        yield feapder.Request("https://www.travelsky.cn/publish/english/2182/2183/index.html", callback=self.english_2_index)
        url_set.add('https://www.travelsky.cn/publish/english/2182/2183/index.html')
        # 联系我们
        yield feapder.Request("https://www.travelsky.cn/publish/english/2182/2184/index.html", callback=self.english_2_index)
        url_set.add("https://www.travelsky.cn/publish/english/2182/2184/index.html")
        # 使用帮助
        yield feapder.Request("https://www.travelsky.cn/publish/english/2182/2186/index.html", callback=self.english_2_index)
        url_set.add("https://www.travelsky.cn/publish/english/2182/2186/index.html")
        # 网站地图
        yield feapder.Request("https://www.travelsky.cn/publish/english/2182/2187/index.html", callback=self.english_2_index)
        url_set.add("https://www.travelsky.cn/publish/english/2182/2187/index.html")

    def english_index(self, request, response):
        if 'www.travelsky.cn' not in request.url:
            return

        main_img_url_list = ['dh_gywm_pic1.gif', 'azswerftgyhu.jpg', 'dh_zrycx_pic2.gif', 'logo.gif', 'search_bt.gif',
                             'xczx_pic.gif', 'jpcx_pic.gif', 'bijibensda.jpg', 'kpjy_pic.gif', 'kpyz_pic.gif',
                             'khfw_icon_new.gif', 'slfw_pic.gif', 'hlzh_icon_new.gif', 'khpx_pic.gif', 'sy_cont_bg.jpg',
                             'qihuan_xz.jpg', 'more.jpg', 'bg001.gif', 'sy_bottom_bg.jpg']
        english_img_url_list = ['banner1.jpg', 'banner2.jpg', 'faq.jpg', 'sendemail.jpg', 'erweima.jpg', 'banner3.jpg',
                                'banner4.jpg', 'english_top_bg.jpg', 'dh_line.gif', 'sy_banner_bg.jpg', 'bottom_line.gif',
                                'xixi.png', 'diqiuyi.jpg', 'application_qh_bg.png', 'ca_hz_002.png', 'pagination_bg.gif',
                                'pagination_xz.png', 'pagination_mr.png','dh_bottom_line.gif', 'dh_jiantou.gif', 'dah_jt.jpg']

        img_url_list = ['/publish/main/images/' + img for img in main_img_url_list]
        img_url_list = img_url_list + ['/publish/english/images/' + img for img in english_img_url_list]

        txt_data = self.get_head(response, is_english=True)

        d11 = response.xpath('//div[@id="divBT11"]/table/tbody/tr/td[1]/a/text()').extract_first() + '\n'
        d11_list = response.xpath('//div[@id="div11"]/table/tbody/tr/td/ul/li/a/@title').extract()
        txt_data += d11 + '\n'.join(d11_list) + '\nmore\n'

        # 轮播
        cnt_list = response.xpath('//div[@id="cnt"]/ul/li')
        for cnt in cnt_list:
            item = ''
            item += cnt.xpath('./p/a/text()').extract_first() + '\n'
            if cnt.xpath('./a/text()').extract():
                if cnt.xpath('./a/@title').extract():
                    item += '\n'.join(cnt.xpath('./a/@title').extract()) + '\n'
                else:
                    item += '\n'.join(cnt.xpath('./a/text()').extract()) + '\n'
            txt_data += item

        # ul
        txt_data += 'Social responsibility' + '\nmore\n'

        # box
        box_list = response.xpath('//div[@class="box"]/p/a/text()').extract()
        txt_data += '  '.join(box_list)

        # end
        txt_data += self.get_english_end()

        url_set.add(request.url)
        file_name = self.get_file_name(request.url)
        self.create_file(file_name, txt_data, request.url)
        self.create_img(file_name, img_url_list)

    def english_1_index(self, request, response):
        if 'www.travelsky.cn' not in request.url:
            return

        main_img_url_list = ['dh_gywm_pic1.gif', 'azswerftgyhu.jpg', '/dh_zrycx_pic2.gif', 'logo.gif', 'search_bt.gif',
                             'more.jpg', 'second_bottom_bg.jpg']
        english_img_url_list = ['english_top_bg.jpg', 'dh_line.gif', 'english_cont_bg.jpg', 'qh_xz.gif', 'bottom_line.gif',
                                'expanded.gif', 'qh_mr.gif', 'en_zzry_title_bg.gif', 'collapsed.gif', 'dah_jt.jpg', 'dh_jiantou.gif']

        if request.url == 'https://www.travelsky.cn/publish/english/401/index.html':
            english_img_url_list += ['btn01.gif', 'btn02.gif', 'bg03.gif', 'dh_bottom_line.gif']

        img_url_list = ['/publish/main/images/' + img for img in main_img_url_list]
        img_url_list = img_url_list + ['/publish/english/images/' + img for img in english_img_url_list]

        if request.url == "https://www.travelsky.cn/publish/english/401/408/413/index.html":
            team = response.xpath(
                '//div[@class="cont_mid"]/div/div/table/tr/td/ul/li/table/tr[2]/td[2]/a/@href').extract()
            for team_url in team:
                if team_url not in url_set and 'www.travelsky.cn' in request.url:
                    print(request.url + '----' + team_url)
                    yield feapder.Request(team_url, callback=self.english_1_index)
                    url_set.add(team_url)

                # 业务板块处理
        yewu_list = ['https://www.travelsky.cn/publish/english/403/432/index.htmll',
                     'https://www.travelsky.cn/publish/english/403/433/index.html',
                     'https://www.travelsky.cn/publish/english/403/434/index.html',
                     'https://www.travelsky.cn/publish/english/403/435/index.html',
                     'https://www.travelsky.cn/publish/english/403/440/index.html',
                     'https://www.travelsky.cn/publish/english/403/437/index.html',
                     'https://www.travelsky.cn/publish/english/403/438/index.html']
        if request.url in yewu_list:
            yw_url_list = response.xpath('//div[@class="ywbk_cp"]/ul/li/a/@href').extract()
            for url in yw_url_list:
                if url not in url_set and 'www.travelsky.cn' in request.url:
                    if 'www.travelsky.cn' in url:
                        print(request.url + '----' + url)
                        yield feapder.Request(url, callback=self.english_1_index)
                        url_set.add(url)

        txt_data = self.get_head(response, is_english=True)

        # left
        left_data, list_url = self.main_left(response)
        for url in list_url:
            if url in url_set:
                continue
            else:
                if url not in url_set and 'www.travelsky.cn' in request.url:
                    if 'www.travelsky.cn' in url:
                        print(request.url + '----' + url)
                        print(url)
                        yield feapder.Request(url, callback=self.english_1_index)
                        url_set.add(url)
        txt_data += left_data

        fy_url = ['https://www.travelsky.cn/publish/english/401/410/index.html']
        if request.url in fy_url:
            # 翻页
            page_max = int(
                re.findall(r'Page (\d+)', response.xpath('//a[@class="xwzx-fenye-jilu"]/text()').extract_first())[0])
            for i in range(page_max):
                if i == 0:
                    continue
                page_url = request.url.replace("index", f"index_{i + 1}")
                if page_url not in url_set and 'www.travelsky.cn' in request.url:
                    print(request.url + '----' + page_url)
                    yield feapder.Request(page_url, callback=self.english_1_index)
                    url_set.add(page_url)

        # 列表页
        if request.url.split('_')[0] in list_url_set:
            # 列表详情
            detail_list = set(response.xpath('//div[@class="cont_mid"]/table/tr/td/ul/li/a/@href').extract())
            for detail in detail_list:
                if detail not in url_set and 'www.travelsky.cn' in request.url:
                    print(request.url + '----' + detail)
                    yield feapder.Request(detail, callback=self.english_1_index)
                    url_set.add(detail)

            if request.url in list_url_set and request.url not in url_set:
                    # 翻页
                    page_max = int(
                        re.findall(r'Page (\d+)', response.xpath('//a[@class="xwzx-fenye-jilu"]/text()').extract_first())[0])
                    for i in range(page_max):
                        if i == 0:
                            continue
                        page_url = request.url.replace("index", f"index_{i + 1}")
                        if (page_url not in url_set) and ('www.travelsky.cn' in request.url):
                            print(request.url + '----' + page_url)
                            yield feapder.Request(page_url, callback=self.english_1_index)
                            url_set.add(page_url)

        mid_data, mid_img_url = self.english_mid(response)
        txt_data += mid_data
        img_url_list += mid_img_url

        right_data, right_img_url = self.english_right(response)
        txt_data += right_data
        img_url_list += right_img_url

        if request.url == 'https://www.travelsky.cn/publish/english/402/index.html':
            if response.xpath('//div[@class="ty"]/div[2]/div[4]'):
                cont_right = response.xpath('//div[@class="ty"]/div[2]/div[4]').extract_first()
                soup = BeautifulSoup(cont_right, 'html.parser')
                tt = soup.get_text().strip().replace('\n', '__psq').replace(' ', '')
                t_data = re.sub(r'(__psq)+', '\n', tt)

                t_url_list = []
                img_tags = soup.find_all('img')
                for img_tag in img_tags:
                    t_url_list.append(img_tag['src'].replace(self.url, ''))

                for td in soup.find_all(name='td'):
                    if td.attrs.get('background'):
                        t_url_list.append(td.attrs.get('background'))
                txt_data += t_data
                img_url_list += t_url_list

        # end
        end = self.get_english_end()
        txt_data += end
        file_name = self.get_file_name(request.url)
        self.create_file(file_name, txt_data, request.url)
        self.create_img(file_name, img_url_list)

    def english_2_index(self, request, response):
        if 'www.travelsky.cn' not in request.url:
            return
        main_img_url_list = ['dh_gywm_pic1.gif', 'azswerftgyhu.jpg', 'dh_zrycx_pic2.gif', 'logo.gif', 'search_bt.gif',
                             'second_bottom_bg.jpg']
        english_img_url_list = ['english_top_bg.jpg', 'dh_line.gif', 'english_cont_bg.jpg']

        img_url_list = ['/publish/main/images/' + img for img in main_img_url_list]
        img_url_list = img_url_list + ['/publish/english/images/' + img for img in english_img_url_list]

        txt_data = self.get_head(response, is_english=True)
        txt = response.xpath('//div[@class="ty"]').extract_first()
        soup = BeautifulSoup(txt, 'html.parser')
        txt_data += soup.get_text().strip()

        txt_data += self.get_english_end()

        file_name = self.get_file_name(request.url)
        self.create_file(file_name, txt_data, request.url)
        self.create_img(file_name, img_url_list)

    # 主体
    def english_mid(self, response):
        cont_mid = response.xpath('//div[@class="cont_mid"]').extract_first()
        if not cont_mid:
            cont_mid = response.xpath('//div[@class="cont_mid2"]').extract_first()

        if not cont_mid and response.xpath('//div[@class="ty"]'):
            cont_mid = response.xpath('//div[@class="ty"]/div[2]').extract_first()

        soup = BeautifulSoup(cont_mid, 'html.parser')
        tt = soup.get_text().strip().replace('\n', '__psq').replace(' ', '').replace('　　', '')
        mid_data = re.sub(r'(__psq)+', '\n', tt)

        img_url_list = []
        img_tags = soup.find_all('img')
        for img_tag in img_tags:
            img_url_list.append(img_tag['src'].replace(self.url, ''))

        for td in soup.find_all(name='td'):
            if td.attrs.get('background'):
                img_url_list.append(td.attrs.get('background'))

        return mid_data, img_url_list

    # 左导航
    def english_left(self, response):
        cont_right = response.xpath('//div[@class="cont_left"]').extract_first()
        # print(next_menu_body)
        soup = BeautifulSoup(cont_right, 'html.parser')
        tt = soup.get_text().strip().replace('\n', '__psq').replace(' ', '')
        left_data = re.sub(r'(__psq)+', '\n', tt)
        list_url = response.xpath('//div[@class="next_menu_body"]//a/@href').extract()
        return left_data, list_url

    # 右导航
    def english_right(self, response):
        if not response.xpath('//div[@class="cont_right"]'):
            return '', []
        cont_right = response.xpath('//div[@class="cont_right"]').extract_first()
        soup = BeautifulSoup(cont_right, 'html.parser')
        tt = soup.get_text().strip().replace('\n', '__psq').replace(' ', '')
        right_data = re.sub(r'(__psq)+', '\n', tt)

        img_url_list = []
        img_tags = soup.find_all('img')
        for img_tag in img_tags:
            img_url_list.append(img_tag['src'].replace(self.url, ''))

        for td in soup.find_all(name='td'):
            if td.attrs.get('background'):
                img_url_list.append(td.attrs.get('background'))

        return right_data, img_url_list

    def get_english_end(self):
        end = "Legal Statement  |  Contact Us  |  Site Map  |  Ticket Verification\n"
        end += "China  Travelsky  Holding  Company  and  China  civil  aviation  information  Network  lnc  ©  copyright  2010"
        return end

    def parse(self, request, response):
        if 'www.travelsky.cn' not in request.url:
            return
        file_name = self.get_file_name(request.url)
        self.create_file(file_name, response.bs4().get_text().strip(), request.url)

    def get_head(self, response, is_home=False, is_english=False):
        txt_data = response.xpath('//title/text()').extract_first() + '\n'
        if is_home:
            # 投资者 （首页）
            txt_data += ' '.join(response.xpath('//select[@id="jumpMenu"]/option/text()').extract()) + '  '

        # head
        txt_data += ' '.join(response.xpath('//div[@class="top_link"]/li/a/text()').extract()) + ' ' + '\n'

        if is_english:
            gy = response.xpath('//div[@class="menu"]').extract_first()
            soup = BeautifulSoup(gy, 'html.parser')
            tt = soup.get_text().strip().replace('\n', '__psq').replace(' ', '').replace(' ', '').replace('\t', '')
            txt_data += re.sub(r'(__psq)+', '\n', tt)
            return txt_data

        # 关于我们
        if not is_home:
            txt_data += response.xpath('//li[@class="menuyiji"][1]/a/text()').extract_first() + '\n'

            txt_data += response.xpath('//li[@class="menuyiji"][2]/a/text()').extract_first() + '\n'
            txt_data += ' '.join(
                response.xpath('//li[@class="menuyiji"][2]/ul/table/tr/td[1]/li/a/text()').extract()) + '\n'
            txt_data += response.xpath('//li[@class="menuyiji"][2]/ul/table/tr/td[2]/p/a/text()').extract_first() + '\n'
            txt_data += response.xpath('//li[@class="menuyiji"][2]/ul/table/tr/td[3]/p/a/text()').extract_first() + '\n'
            # 新闻中心
            txt_data += response.xpath('//li[@class="menuyiji"][3]/a/text()').extract_first() + '\n'
            txt_data += ' '.join(
                response.xpath('//li[@class="menuyiji"][3]/ul/table/tr/td[1]/li/a/text()').extract()) + '\n'
            txt_data += response.xpath('//li[@class="menuyiji"][3]/ul/table/tr/td[2]/p/a/text()').extract_first() + '\n'
            # 业务模块
            txt_data += response.xpath('//li[@class="menuyiji"][4]/a/text()').extract_first() + '\n'
            txt_data += ' '.join(
                response.xpath('//li[@class="menuyiji"][4]/ul/table/tr/td[1]/li/a/text()').extract()) + '\n'
            txt_data += response.xpath('//li[@class="menuyiji"][4]/ul/table/tr/td[2]/p/a/text()').extract_first() + '\n'
            # 服务中心
            txt_data += response.xpath('//li[@class="menuyiji"][5]/a/text()').extract_first() + '\n'
            txt_data += ' '.join(
                response.xpath('//li[@class="menuyiji"][5]/ul/table/tr/td[1]/li/a/text()').extract()) + '\n'
            txt_data += ''.join(
                response.xpath('//li[@class="menuyiji"][5]/ul/table/tr/td[2]/p/a/text()').extract()) + '\n'
            txt_data += response.xpath('//li[@class="menuyiji"][5]/ul/table/tr/td[3]/p/a/text()').extract_first() + '\n'
            # 投资者关系
            txt_data += response.xpath('//li[@class="menuyiji"][6]/a/text()').extract_first() + '\n'
            # 人力资源
            txt_data += response.xpath('//li[@class="menuyiji"][7]/a/text()').extract_first() + '\n'
            txt_data += ' '.join(
                response.xpath('//li[@class="menuyiji"][7]/ul/table/tr/td[1]/li/a/text()').extract()) + '\n'
            txt_data += response.xpath('//li[@class="menuyiji"][7]/ul/table/tr/td[2]/p/a/text()').extract_first() + '\n'
            txt_data += response.xpath('//li[@class="menuyiji"][7]/ul/table/tr/td[3]/p/a/text()').extract_first() + '\n'
            # 责任与创新
            txt_data += response.xpath('//li[@class="menuyiji"][8]/a/text()').extract_first() + '\n'
            txt_data += ' '.join(
                response.xpath('//li[@class="menuyiji"][8]/ul/table/tr/td[1]/li/a/text()').extract()) + '\n'
            txt_data += response.xpath('//li[@class="menuyiji"][8]/ul/table/tr/td[2]/p/a/text()').extract_first() + '\n'
            txt_data += response.xpath('//li[@class="menuyiji"][8]/ul/table/tr/td[3]/p/a/text()').extract_first() + '\n'
        else:
            txt_data += response.xpath('//li[@class="menuyiji"][1]/a/text()').extract_first() + '\n'
            txt_data += ' '.join(
                response.xpath('//li[@class="menuyiji"][1]/ul/table/tr/td[1]/li/a/text()').extract()) + '\n'
            txt_data += response.xpath('//li[@class="menuyiji"][1]/ul/table/tr/td[2]/p/a/text()').extract_first() + '\n'
            txt_data += response.xpath('//li[@class="menuyiji"][1]/ul/table/tr/td[3]/p/a/text()').extract_first() + '\n'
            # 新闻中心
            txt_data += response.xpath('//li[@class="menuyiji"][2]/a/text()').extract_first() + '\n'
            txt_data += ' '.join(
                response.xpath('//li[@class="menuyiji"][2]/ul/table/tr/td[1]/li/a/text()').extract()) + '\n'
            txt_data += response.xpath('//li[@class="menuyiji"][2]/ul/table/tr/td[2]/p/a/text()').extract_first() + '\n'
            # 业务模块
            txt_data += response.xpath('//li[@class="menuyiji"][3]/a/text()').extract_first() + '\n'
            txt_data += ' '.join(
                response.xpath('//li[@class="menuyiji"][3]/ul/table/tr/td[1]/li/a/text()').extract()) + '\n'
            txt_data += response.xpath('//li[@class="menuyiji"][3]/ul/table/tr/td[2]/p/a/text()').extract_first() + '\n'
            # 服务中心
            txt_data += response.xpath('//li[@class="menuyiji"][4]/a/text()').extract_first() + '\n'
            txt_data += ' '.join(
                response.xpath('//li[@class="menuyiji"][4]/ul/table/tr/td[1]/li/a/text()').extract()) + '\n'
            txt_data += ''.join(
                response.xpath('//li[@class="menuyiji"][4]/ul/table/tr/td[2]/p/a/text()').extract()) + '\n'
            txt_data += response.xpath('//li[@class="menuyiji"][4]/ul/table/tr/td[3]/p/a/text()').extract_first() + '\n'
            # 投资者关系
            txt_data += response.xpath('//li[@class="menuyiji"][5]/a/text()').extract_first() + '\n'
            # 人力资源
            txt_data += response.xpath('//li[@class="menuyiji"][6]/a/text()').extract_first() + '\n'
            txt_data += ' '.join(
                response.xpath('//li[@class="menuyiji"][6]/ul/table/tr/td[1]/li/a/text()').extract()) + '\n'
            txt_data += response.xpath('//li[@class="menuyiji"][6]/ul/table/tr/td[2]/p/a/text()').extract_first() + '\n'
            txt_data += response.xpath('//li[@class="menuyiji"][6]/ul/table/tr/td[3]/p/a/text()').extract_first() + '\n'
            # 责任与创新
            txt_data += response.xpath('//li[@class="menuyiji"][7]/a/text()').extract_first() + '\n'
            txt_data += ' '.join(
                response.xpath('//li[@class="menuyiji"][7]/ul/table/tr/td[1]/li/a/text()').extract()) + '\n'
            txt_data += response.xpath('//li[@class="menuyiji"][7]/ul/table/tr/td[2]/p/a/text()').extract_first() + '\n'
            txt_data += response.xpath('//li[@class="menuyiji"][7]/ul/table/tr/td[3]/p/a/text()').extract_first() + '\n'
            # 信息公开
            txt_data += response.xpath('//li[@class="menuyiji"][8]/a/text()').extract_first() + '\n'
            txt_data += ' '.join(
                response.xpath('//li[@class="menuyiji"][8]/ul/table/tr/td[1]/li/a/text()').extract()) + '\n'
            txt_data += response.xpath('//li[@class="menuyiji"][8]/ul/table/tr/td[2]/p/a/text()').extract_first() + '\n'
        return txt_data

    def get_end(self, response):
        # end
        end_div = ' '.join(response.xpath('//div[last()]/p[1]/a/text()').extract()) + ' '
        end_div += ' '.join(response.xpath('//div[last()]/p[1]/span/select/option/text()').extract()) + '\n'
        end_div += response.xpath('//div[last()]/p[2]/text()').extract_first()
        end_div += response.xpath('//div[last()]/p[2]/a/text()').extract_first()
        return end_div

    # 首页
    def main_index(self, request, response):
        if 'www.travelsky.cn' not in request.url:
            return

        publish_images_list = ['dh_gywm_pic1.gif', 'dh_gywm_pic2.gif', 'dh_xwzx_pic.gif', 'ywgl_pic1.gif',
                               'zuosdfjklsd.jpg', 'logo.gif', 'search_bt.gif', 'asdrftgyhujik.jpg', 'azswerftgyhu.jpg',
                               'gyhujio.jpg', 'khfw_icon_new.gif', 'xsx_index.jpg', 'slfw_pic.gif', 'hlzh_icon_new.gif',
                               'khpx_pic.gif', 'xxxjp_logo.png', 'xczx_pic.gif', 'kpyz_pic.gif', 'bijibensda.jpg',
                               'bt_001.gif', 'dh_zrycx_pic1.gif', 'dh_zrycx_pic2.gif', 'fgyuiop.jpg', 'banner1.jpg',
                               'sy_top_bg.jpg', 'sy_banner_bg.jpg', 'sy_cont_bg.jpg', 'qihuan_xz.jpg', 'qihuan_dq.jpg',
                               'bottom_line.gif', 'more.jpg', 'liebiao_icon.gif', 'bg001.gif', 'xixi.png',
                               'icon001.gif',
                               'ca_hz_002.png', 'sy_bottom_bg.jpg', 'bt_002.gif', 'dh_bottom_line.gif',
                               'dh_jiantou.gif']
        img_url_list = ['/publish/main/images/' + img for img in publish_images_list]

        txt_data = self.get_head(response, True)
        # 主体
        # 最新消息
        d11 = response.xpath('//div[@id="divBT11"]/table/tbody/tr/td[1]/a/text()').extract_first() + '\n'
        d11_list = response.xpath('//div[@id="div11"]/table/tbody/tr/td/ul/li/a/@title').extract()
        txt_data += d11 + '\n'.join(d11_list) + '\n'

        # 国资动态
        d12 = response.xpath('//div[@id="divBT11"]/table/tbody/tr/td[2]/a/text()').extract_first() + '\n'
        d12_list = response.xpath('//div[@id="div12"]/table/tbody/tr/td/ul/li/a/@title').extract()
        txt_data += d12 + '\n'.join(d12_list) + '\n' + '更多\n'

        # 轮播
        cnt_list = response.xpath('//div[@id="cnt"]/ul/li')
        for cnt in cnt_list:
            item = ''
            item += cnt.xpath('./p/a/text()').extract_first() + '\n'
            if cnt.xpath('./a/text()').extract():
                if cnt.xpath('./a/@title').extract():
                    item += '\n'.join(cnt.xpath('./a/@title').extract()) + '\n'
                else:
                    item += '\n'.join(cnt.xpath('./a/text()').extract()) + '\n'
            txt_data += item

        # ul
        li_list = re.findall(
            r'<li style="text-overflow: ellipsis;white-space: nowrap;overflow: hidden;text-align:left;"><a href=.*?title="(.*?)">',
            response.text)
        txt_data += '\n'.join(li_list) + '\n更多\n'

        # box
        box_list = response.xpath('//div[@class="box"]/p/a/text()').extract()
        txt_data += ' '.join(box_list)

        # end
        end_div = self.get_end(response)
        txt_data += end_div

        self.create_file("main_index", txt_data, request.url)
        self.create_img("main_index", img_url_list)

    # 关于我们
    def main_1_index(self, request, response):
        if request.url == "https://www.travelsky.cn/publish/main/17/4521/index.html":
            self.xxjxs(request, response)
            return

        if request.url == "https://www.travelsky.cn/publish/main/1/2/8/index.html":
            team = response.xpath(
                '//div[@class="cont_mid"]/div/div/table/tr/td/ul/li/table/tr[2]/td[2]/a/@href').extract()
            for team_url in team:
                if team_url not in url_set and 'www.travelsky.cn' in request.url:
                    print(request.url + '----' + team_url)
                    yield feapder.Request(team_url, callback=self.main_1_index)
                    url_set.add(team_url)

        # 业务板块处理
        yewu_list = ['https://www.travelsky.cn/publish/main/27/29/index.html',
                     'https://www.travelsky.cn/publish/main/27/31/index.html',
                     'https://www.travelsky.cn/publish/main/27/32/index.html',
                     'https://www.travelsky.cn/publish/main/27/30/index.html',
                     'https://www.travelsky.cn/publish/main/27/33/index.html']
        if request.url in yewu_list:
            yw_url_list = response.xpath('//div[@class="ywbk_cp"]/ul/li/a/@href').extract()
            for url in yw_url_list:
                if url not in url_set and 'www.travelsky.cn' in request.url:
                    print(request.url + '----' + url)
                    yield feapder.Request(url, callback=self.main_1_index)
                    url_set.add(url)

        flag = response.xpath('//body/table[1]/tbody[1]/tr[1]/td[3]/a/font/text()').extract_first()
        if flag and flag.strip() == '关闭本页':
            soup = response.bs4()
            tt = soup.get_text().strip().replace('\n', '__psq').replace(' ', '').replace('　　', '').replace('\t', '')
            txt_data = re.sub(r'(__psq)+', '\n', tt)
            img_url_list = []
            img_tags = soup.find_all('img')
            for img_tag in img_tags:
                img_url_list.append(img_tag['src'])

            url_set.add(request.url)
            file_name = self.get_file_name(request.url)
            self.create_file(file_name, txt_data, request.url)
            self.create_img(file_name, img_url_list)
            return

        if response.status_code == 404:
            soup = response.bs4()
            tt = soup.get_text().strip().replace('\n', '__psq').replace(' ', '').replace('　　', '').replace('\t', '')
            txt_data = re.sub(r'(__psq)+', '\n', tt)
            url_set.add(request.url)
            file_name = self.get_file_name(request.url)
            self.create_file(file_name, txt_data, request.url)
            return

        publish_images_list = ['dh_gywm_pic1.gif', 'dh_gywm_pic2.gif', 'dh_xwzx_pic.gif', 'ywgl_pic1.gif',
                               'zuosdfjklsd.jpg', 'logo.gif', 'search_bt.gif', 'asdrftgyhujik.jpg', 'expanded.gif',
                               'expanded.gif', 'azswerftgyhu.jpg', 'gyhujio.jpg', 'dh_zrycx_pic1.gif',
                               'dh_zrycx_pic2.gif', 'gywm_zzjg_pic.gif', 'gszl.png', 'whln.png', 'qyxx_pic.gif',
                               'second_top_bg.jpg',
                               'qh_xz.gif', 'bottom_line.gif', 'qh_mr.gif', 'jtjj_bg.gif', 'more.jpg', 'collapsed.gif', 'second_bottom_bg.jpg']
        img_url_list = ['/publish/main/images/' + img for img in publish_images_list]
        img_url_list.append('/publish/main/1/6/2015/04/20/20150420160115702812962/1512972258978.jpg')

        txt_data = self.get_head(response)

        # left
        left_data, list_url = self.main_left(response)
        for url in list_url:
            if url in url_set:
                continue
            else:
                if url not in url_set and 'www.travelsky.cn' in request.url:
                    if 'www.travelsky.cn' in url:
                        print(request.url + '----' + url)
                        yield feapder.Request(url, callback=self.main_1_index)
                        url_set.add(url)

        txt_data += left_data + '\n'
        # 主体
        # 服务中心 - 常见问题
        # 人力资源 - 招聘帮助
        # 责任与创新 - 实践动态
        # 责任与创新 - 创新动态
        fwzx_list_url = ['https://www.travelsky.cn/publish/main/37/47/58/index.html',
                         'https://www.travelsky.cn/publish/main/37/47/58/index',
                         'https://www.travelsky.cn/publish/main/38/65/index.html',
                         'https://www.travelsky.cn/publish/main/38/65/index',
                         'https://www.travelsky.cn/publish/main/40/78/86/index.html',
                         'https://www.travelsky.cn/publish/main/40/78/86/index',
                         'https://www.travelsky.cn/publish/main/40/80/91/index.html',
                         'https://www.travelsky.cn/publish/main/40/80/91/index']
        if request.url.split('_')[0] in fwzx_list_url:
            # 列表详情
            detail_list = set(response.xpath('//div[@class="cont_mid"]/table/tr/td/ul/li/a/@href').extract())
            for detail in detail_list:
                if detail not in url_set and 'www.travelsky.cn' in request.url:
                    print(request.url + '----' + detail)
                    yield feapder.Request(detail, callback=self.main_1_index)
                    url_set.add(detail)

            if request.url in fwzx_list_url:
                # 翻页
                page_max = int(
                    re.findall(r'共(\d+)页', response.xpath('//a[@class="xwzx-fenye-jilu"]/text()').extract_first())[0])
                for i in range(page_max):
                    if i == 0:
                        continue
                    page_url = request.url.replace("index", f"index_{i + 1}")
                    if page_url not in url_set and 'www.travelsky.cn' in request.url:
                        print(request.url + '----' + page_url)
                        yield feapder.Request(page_url, callback=self.main_1_index)
                        url_set.add(page_url)

        if request.url == 'https://www.travelsky.cn/publish/main/40/78/87/index.html':
            # 翻页
            page_max = int(
                re.findall(r'共(\d+)页', response.xpath('//a[@class="xwzx-fenye-jilu"]/text()').extract_first())[0])
            for i in range(page_max):
                if i == 0:
                    continue
                page_url = request.url.replace("index", f"index_{i + 1}")
                if page_url not in url_set and 'www.travelsky.cn' in request.url:
                    print(request.url + '----' + page_url)
                    yield feapder.Request(page_url, callback=self.main_1_index)
                    url_set.add(page_url)

        # 列表页
        if request.url.split('_')[0] in list_url_set:
            # 列表详情
            detail_list = set(response.xpath('//div[@class="cont_mid"]/div[2]/table/tr/td/a/@href').extract())
            for detail in detail_list:
                if detail not in url_set and 'www.travelsky.cn' in request.url:
                    print(request.url + '----' + detail)
                    yield feapder.Request(detail, callback=self.main_1_index)
                    url_set.add(detail)

            if request.url in list_url_set:
                # 翻页
                page_max = int(
                    re.findall(r'共(\d+)页', response.xpath('//a[@class="xwzx-fenye-jilu"]/text()').extract_first())[0])
                for i in range(page_max):
                    if i == 0:
                        continue
                    page_url = request.url.replace("index", f"index_{i + 1}")
                    if page_url not in url_set and 'www.travelsky.cn' in request.url:
                        print(request.url + '----' + page_url)
                        yield feapder.Request(page_url, callback=self.main_1_index)
                        url_set.add(page_url)
        # 相关阅读
        liebiao_second = response.xpath('//div[@class="cont_mid"]//ul[@class="liebiao_second"]/li/a/@href').extract()
        for lb in liebiao_second:
            if lb not in url_set and 'www.travelsky.cn' in request.url:
                print(request.url + '----' + lb)
                yield feapder.Request(lb, callback=self.main_1_index)
                url_set.add(lb)

        mid_data, mid_img_url_list = self.main_mid(response)
        txt_data += mid_data
        img_url_list.extend(mid_img_url_list)

        # right
        right_data, right_img_url_list = self.main_left(response)
        txt_data += right_data
        img_url_list.extend(right_img_url_list)

        # end
        end_div = self.get_end(response)
        txt_data += end_div

        file_name = self.get_file_name(request.url)
        self.create_file(file_name, txt_data, request.url)
        self.create_img(file_name, img_url_list)

    def main_2_index(self, request, response):
        if 'www.travelsky.cn' not in request.url:
            return

        publish_images_list = ['logo.gif', 'search_bt.gif', 'zuosdfjklsd.jpg', 'asdrftgyhujik.jpg', 'azswerftgyhu.jpg',
                               'gyhujio.jpg', 'dh_zrycx_pic1.gif', 'dh_zrycx_pic2.gif', 'dh_gywm_pic1.gif',
                               'dh_gywm_pic2.gif',
                               'dh_xwzx_pic.gif', 'ywgl_pic1.gif', 'second_top_bg.jpg', 'second_bottom_bg.jpg']

        try:
            jq = request.jq
            if jq == "1":
                publish_images_list.extend(['gwmap.jpg', 'xz_xz.png', 'xz.png', 'vicon.png'])
        except:
            pass

        img_url_list = ['/publish/main/images/' + img for img in publish_images_list]

        txt_data = self.get_head(response)
        txt = response.xpath('//div[@class="cont_bg"]').extract_first()
        soup = BeautifulSoup(txt, 'html.parser')
        txt_data += soup.get_text().strip()

        end = self.get_end(response)
        txt_data += end

        file_name = self.get_file_name(request.url)
        self.create_file(file_name, txt_data, request.url)
        self.create_img(file_name, img_url_list)

    def main_3_index(self, request, response):
        if 'www.travelsky.cn' not in request.url:
            return
        publish_images_list = ['/publish/main/17/24/4481/4482/4490/2023/05/30/20230530162413434108901/1685435080935.jpg',
                               '/publish/main/17/24/4481/4482/4490/2023/05/30/20230530162120622577136/1685434904524.jpg',
                               '/publish/main/images/xsxqdx.png', '/publish/main/images/ico.png', '/publish/main/images/child_title_bg.png']

        txt_data = response.xpath('//title/text()').extract_first() + '\n返回首页\n'
        eighteenthnews1 = BeautifulSoup(response.xpath('//div[@class="eighteenthnews1"]').extract_first(),'html.parser')
        tt = eighteenthnews1.get_text().strip().replace('\n', '__psq').replace(' ', '').replace('　　', '').replace('\t','')
        txt_data += re.sub(r'(__psq)+', '\n', tt) + '\n'

        eighteenthnews_list = response.xpath('//div[@class="eighteenthnews"]').extract()
        for eighteenthnews in eighteenthnews_list:
            eighteenthnews = BeautifulSoup(eighteenthnews, 'html.parser')
            tt = eighteenthnews.get_text().strip().replace('\n', '__psq').replace(' ', '').replace('　　', '').replace(
                '\t', '')
            txt_data += re.sub(r'(__psq)+', '\n', tt) + '\n'

        # end
        end_div = ' '.join(response.xpath('//div[last()-1]/p[1]/a/text()').extract()) + ' '
        end_div += ' '.join(response.xpath('//div[last()-1]/p[1]/span/select/option/text()').extract()) + '\n'
        end_div += response.xpath('//div[last()-1]/p[2]/text()').extract_first()
        end_div += response.xpath('//div[last()-1]/p[2]/a/text()').extract_first()

        txt_data += end_div + '\n'

        ztzl_xdah_list = response.xpath('//div[@class="ztzl_xdah"]/a[1]/@href').extract()
        for ztzl_xdah in ztzl_xdah_list:
            print(request.url + '----' + ztzl_xdah)
            yield feapder.Request(ztzl_xdah, callback=self.main_3_index1)

        file_name = self.get_file_name(request.url)
        self.create_file(file_name, txt_data, request.url)
        self.create_img(file_name, publish_images_list)

    def main_3_index1(self, request, response):
        if 'www.travelsky.cn' not in request.url:
            return
        publish_images_list = ['/publish/main/images/child_title_bg.png', '/publish/main/images/xsxqdx.png']

        txt_data = response.xpath('//title/text()').extract_first() + '\n'
        ztzl_sjjs = response.xpath('//div[@class="ztzl_sjjs"]').extract_first()
        ztzl_sjjs = BeautifulSoup(ztzl_sjjs, 'html.parser')
        tt = ztzl_sjjs.get_text().strip().replace('\n', '__psq').replace(' ', '').replace('　　', '').replace('\t', '')
        txt_data += re.sub(r'(__psq)+', '\n', tt) + '\n'

        # 列表详情
        detail_list = set(response.xpath('//ul[@class="liebiao_second"]/li/a/@href').extract())
        for detail in detail_list:
            if detail not in url_set and 'www.travelsky.cn' in request.url:
                print(request.url + '----' + detail)
                yield feapder.Request(detail, callback=self.main_3_index2)
                url_set.add(detail)

        # 翻页
        page_max = int(
            re.findall(r'共(\d+)页', response.xpath('//a[@class="xwzx-fenye-jilu"]/text()').extract_first())[0])

        page = request.url.split('/')[-1].split('.')[0]

        if page == 'index':
            page = 1
        else:
            page = int(page.split('_')[1])

        if page < page_max:
            if page == 1:
                page_url = request.url.replace("index", f"index_{page + 1}")
            else:
                page_url = request.url.replace(f"index_{page}", f"index_{page + 1}")
            if page_url not in url_set and 'www.travelsky.cn' in request.url:
                print(request.url + '----' + page_url)
                yield feapder.Request(page_url, callback=self.main_3_index1)
                url_set.add(page_url)

        file_name = self.get_file_name(request.url)
        self.create_file(file_name, txt_data, request.url)
        self.create_img(file_name, publish_images_list)

    def main_3_index2(self, request, response):
        if 'www.travelsky.cn' not in request.url:
            return
        img_url_list = ['/publish/main/images/zt_images/logo.gif', '/publish/main/images/zt_images/sjbanner.jpg']
        soup = response.bs4()
        tt = soup.get_text().strip().replace('\n', '__psq').replace(' ', '').replace('　　', '').replace('\t', '')
        txt_data = re.sub(r'(__psq)+', '\n', tt)
        img_tags = soup.find_all('img')
        for img_tag in img_tags:
            img_url_list.append(img_tag['src'])

        url_set.add(request.url)
        file_name = self.get_file_name(request.url)
        self.create_file(file_name, txt_data, request.url)
        self.create_img(file_name, img_url_list)


    # 左导航
    def main_left(self, response):
        cont_right = response.xpath('//div[@class="cont_left"]').extract_first()
        # print(next_menu_body)
        soup = BeautifulSoup(cont_right, 'html.parser')
        tt = soup.get_text().strip().replace('\n', '__psq').replace(' ', '')
        left_data = re.sub(r'(__psq)+', '\n', tt)
        list_url = response.xpath('//div[@class="next_menu_body"]//a/@href').extract()
        return left_data, list_url

    # 右导航 - 管理团队
    def main_right(self, response):
        if not response.xpath('//div[@class="cont_right"]'):
            return '', []
        cont_right = response.xpath('//div[@class="cont_right"]').extract_first()
        soup = BeautifulSoup(cont_right, 'html.parser')
        tt = soup.get_text().strip().replace('\n', '__psq').replace(' ', '')
        right_data = re.sub(r'(__psq)+', '\n', tt)

        img_url_list = []
        img_tags = soup.find_all('img')
        for img_tag in img_tags:
            img_url_list.append(img_tag['src'].replace(self.url, ''))

        for td in soup.find_all(name='td'):
            if td.attrs.get('background'):
                img_url_list.append(td.attrs.get('background'))

        return right_data, img_url_list

    # 主体
    def main_mid(self, response):
        cont_mid = response.xpath('//div[@class="cont_mid"]').extract_first()
        soup = BeautifulSoup(cont_mid, 'html.parser')
        tt = soup.get_text().strip().replace('\n', '__psq').replace(' ', '').replace('　　', '')
        mid_data = re.sub(r'(__psq)+', '\n', tt)

        img_url_list = []
        img_tags = soup.find_all('img')
        for img_tag in img_tags:
            img_url_list.append(img_tag['src'].replace(self.url, ''))

        for td in soup.find_all(name='td'):
            if td.attrs.get('background'):
                img_url_list.append(td.attrs.get('background'))

        return mid_data, img_url_list

    # 学习进行时
    def xxjxs(self, request, response):
        publish_images_list = ['xxxjp.jpg', 'nw_ztzl_06.jpg']
        img_url_list = ['/publish/main/images/' + img for img in publish_images_list]
        txt_data = response.xpath('//title/text()').extract_first() + '\n'
        txt_data += response.xpath('//div[@class="ztzl_xdah"]/a/text()').extract_first() + '\n'

        ul_txt = ''
        ul = response.xpath('//ul[@class="liebiao_second"]/li')
        for li in ul:
            li_title = li.xpath('./a[1]/@title').extract_first() + ' ' + li.xpath(
                './a[2]/text()').extract_first() + '\n'
            li_href = li.xpath('./a[1]/@href').extract_first()
            ul_txt += li_title
            if li_href not in url_set and 'www.travelsky.cn' in request.url:
                print(request.url + '----' + li_href)
                yield feapder.Request(li_href, callback=self.main_1_index)
                url_set.add(li_href)

        txt_data += ul_txt

        soup = BeautifulSoup(response.xpath('//div[@class="fenye"]').extract_first(), 'html.parser')
        fenye_txt = soup.get_text().strip().replace('\n', ' ')
        txt_data += fenye_txt
        page_max = int(re.findall(r'共(\d+)页', fenye_txt)[0])
        for i in range(page_max):
            if i == 0:
                continue
            page_url = request.url.replace("index", f"index_{i + 1}")
            if page_url not in url_set and 'www.travelsky.cn' in request.url:
                print(request.url + '----' + page_url)
                yield feapder.Request(page_url, callback=self.xxjxs)
                url_set.add(page_url)

        end_div = self.get_end(response)
        txt_data += end_div
        file_name = self.get_file_name(request.url)
        self.create_file(file_name, txt_data, request.url)
        self.create_img(file_name, img_url_list)


if __name__ == "__main__":
    TravelskyCn(thread_count=thread_count).start()
    while True:
        if len(threading.enumerate()) == 1:
            meta_json_path = os.path.join(date_path, 'meta.json')
            with open(meta_json_path, 'w', encoding='utf8') as f:
                json.dump(meta_json, f, ensure_ascii=False, indent=4)
            break
        time.sleep(5)
