# -*- coding: utf-8 -*-
"""
Created on 2024-03-17 22:37:01
---------
@summary: url http://gys.travelsky.com.cn/travelsky/home
---------
@author: Earth.qi
"""
import configparser
import json
import os
import re
import threading
import time
import datetime
from loguru import logger


import feapder
import requests

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

class GysTravelskyComCn(feapder.AirSpider):
    __custom_setting__ = dict(
        LOG_LEVEL=log_level
    )

    def __init__(self, *args, **kwargs):
        super(GysTravelskyComCn, self).__init__(*args, **kwargs)
        self.url = "http://gys.travelsky.com.cn/"
        self.notice_type = {'1': '招标公告', '2': '非招标公告', '3': '单一来源采购信息公告'}

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
            response = requests.get(url, headers=headers)
        return response

    def create_img(self, path_name, img_list):
        global img_download_num
        global img_not_download_num
        page_path = os.path.join(date_path, path_name)
        img_file_path = os.path.join(page_path, 'image')
        try:
            os.mkdir(img_file_path, exist_ok=True)
        except:
            return

        for img in img_list:
            img_url = self.url + img
            img_name = img.split('/')[-1]
            if not img_name.endswith('.jpg') and not img_name.endswith('.png'):
                img_name = img_name + '.jpg'
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
        global file_download_num
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
        with file_download_lock:
            file_download_num += 1




    def start_requests(self):
        # 首页
        yield feapder.Request("http://gys.travelsky.com.cn/travelsky/home", callback=self.home)
        # 采购公告
        yield feapder.Request("http://gys.travelsky.com.cn/travelsky/noticeTendering/noticeTenderingHtml", callback=self.notice_tendering)
        # 采购结果公告
        yield feapder.Request("http://gys.travelsky.com.cn/travelsky/noticeTenderingResult/noticeTenderingResultHtml", callback=self.notice_tendering_result)
        # 供应商公告
        yield feapder.Request("http://gys.travelsky.com.cn/travelsky/noticeSupplier/noticeSupplierHtml", callback=self.notice_supplier)
        # 其他公告
        yield feapder.Request("http://gys.travelsky.com.cn/travelsky/noticeOther/noticeOtherHtml", callback=self.notice_other)
        # 帮助文档
        yield feapder.Request("http://gys.travelsky.com.cn/travelsky/noticeDoc/noticeDocHtml", callback=self.notice_doc)
        # 登录页面
        yield feapder.Request("http://gys.travelsky.com.cn/travelsky/logi", callback=self.logi)

    # 首页
    def home(self, request, response):
        # print(response.text)
        img_list = ['/themes/sleek-wood/images/bg.png', '/travelsky/images/structure/ray.png', '/themes/sleek-wood/images/logo.png',
               '/travelsky/images/icons/menu/dashboard.png', '/travelsky/images/icons/menu/page.png', '/travelsky/images/icons/menu/asset.png',
               '/travelsky/images/icons/menu/report.png', '/travelsky/images/icons/menu/event.png', '/travelsky/images/icons/menu/task.png',
               '/themes/sleek-wood/images/inner_header.png', '/travelsky/images/demo/login-5.png', '/travelsky/images/demo/bt_ic.png',
               '/themes/sleek-wood/images/footer.png', '/themes/sleek-wood/images/footer_logo.png',
               '/travelsky/css/ui-lightness/images/ui-bg_glass_100_f6f6f6_1x400.png', '/travelsky/themes/sleek-wood/images/menu_active.png']

        txt_data = response.xpath('//title/text()').extract_first() + '\n'
        txt_data = txt_data + response.xpath('//div[@id="top-block-left"]/p/text()').extract_first().replace('\r\n', "").replace(' ', '') + '\n'
        txt_data = txt_data + response.xpath('//a[@id="logo"]/text()').extract_first() + '\n'

        li_list = response.xpath('//ul[@class="topnav"]/li/a/text()').extract()
        txt_data = txt_data + ' '.join(li_list) + ' '

        li_list = response.xpath('//ul[@class="subnav"]/li/a/text()').extract()
        txt_data = txt_data + ' '.join(li_list) + '\n'

        li_list = response.xpath('//div[@id="tabs"]/ul/li/a/text()').extract()
        # 正在招采
        txt_data = txt_data + li_list[0] + '\n'
        txt_data = txt_data + "序号 类别名称 标题名称 报名截止时间\n"
        resp_json = self.get_request('http://gys.travelsky.com.cn/travelsky/noticeTendering/getTenderingPresent').json()
        for i, resp in enumerate(resp_json):
            txt_data = txt_data + f"{i+1} {self.notice_type.get(str(resp.get('notice_type')))} 【{self.notice_type.get(str(resp.get('notice_type')))}】{resp.get('notice_name')} {resp.get('end_time')}\n"

        # 即将开标
        txt_data = txt_data + li_list[1] + '\n'
        txt_data = txt_data + "序号 类别名称 标题名称 报名截止时间\n"
        resp_json = self.get_request('http://gys.travelsky.com.cn/travelsky/noticeTendering/getTenderingFuture').json()
        for i, resp in enumerate(resp_json):
            txt_data = txt_data + f"{i+1} {self.notice_type.get(str(resp.get('notice_type')))} 【{self.notice_type.get(str(resp.get('notice_type')))}】{resp.get('notice_name')} {resp.get('end_time')}\n"

        txt_data = txt_data + response.xpath('//a[@id="moreNotice"]/text()').extract_first() + '\n'
        txt_data = txt_data + response.xpath('//div[@id="tree-panel"]/h3/text()').extract_first() + '\n'
        txt_data = txt_data + response.xpath('//div[@id="tree-panel"]/ul/li/a/text()').extract_first() + '\n'
        span_list = response.xpath('//div[@id="tree-panel"]/div/span/text()').extract()
        a_list = response.xpath('//div[@id="tree-panel"]/div/span/a/text()').extract()
        for i, span in enumerate(span_list):
            txt_data = txt_data + span + a_list[i] + '\n'

        li_list = response.xpath('//div[@id="tabs2"]/ul/li/a/text()').extract()

        # 招标公告
        txt_data = txt_data + li_list[0] + '\n'
        resp_json = self.get_request('http://gys.travelsky.com.cn/travelsky/noticeTendering/findNoticeTenderingAll').json()
        for i, resp in enumerate(resp_json):
            txt_data = txt_data + f"{resp.get('notice_name')} {resp.get('end_time', '')}\n"

        # 非招标公告
        txt_data = txt_data + li_list[1] + '\n'
        resp_json = self.get_request('http://gys.travelsky.com.cn/travelsky/noticeTendering/findUnNoticeTenderingAll').json()
        for i, resp in enumerate(resp_json):
            txt_data = txt_data + f"{resp.get('notice_name')} {resp.get('end_time', '')}\n"

        # 单一来源采购信息公告
        txt_data = txt_data + li_list[2] + '\n'
        resp_json = self.get_request('http://gys.travelsky.com.cn/travelsky/noticeTendering/findSingleNoticeTenderingAll').json()
        for i, resp in enumerate(resp_json):
            txt_data = txt_data + f"{resp.get('notice_name')} {resp.get('end_time', '')}\n"

        # 采购结果公告
        txt_data = txt_data + li_list[3] + '\n'
        resp_json = self.get_request('http://gys.travelsky.com.cn/travelsky/noticeTenderingResult/findAll').json()
        for i, resp in enumerate(resp_json):
            txt_data = txt_data + f"{resp.get('notice_name')} {resp.get('end_time', '')}\n"

        txt_data = txt_data + response.xpath('//ul[@class="ggtz_titbg"]/span/text()').extract_first().strip() + '\n'
        txt_data = txt_data + response.xpath('//ul[@class="ggtz_titbg"]/a/text()').extract_first().strip() + '\n'

        # 系统通知
        resp_json = self.get_request('http://gys.travelsky.com.cn/travelsky/sysNotice/findAll').json()
        for i, resp in enumerate(resp_json):
            txt_data = txt_data + f"{resp.get('notice_name')} {resp.get('end_time', '')}\n"

        txt_data = txt_data + response.xpath('//p[@id="copyright"]/text()').extract_first().strip() + '\n'
        txt_data = txt_data + ' '.join(response.xpath('//div[@id="footer"]/ul/li/a/text()').extract()) + '\n'

        self.create_file('home', txt_data, request.url)
        self.create_img('home', img_list)

    # 采购公告
    def notice_tendering(self, request, response):
        img_list = ['/themes/sleek-wood/images/bg.png', '/travelsky/images/structure/ray.png',
                    '/themes/sleek-wood/images/logo.png',
                    '/travelsky/images/icons/menu/dashboard.png', '/travelsky/images/icons/menu/page.png',
                    '/travelsky/images/icons/menu/asset.png', '/travelsky/images/icons/menu/event.png',
                    '/travelsky/images/icons/menu/task.png', '/travelsky/images/structure/divider.png',
                    '/themes/sleek-wood/images/footer.png', '/themes/sleek-wood/images/footer_logo.png',
                    '/travelsky/themes/sleek-wood/images/inner_header.png', '/travelsky/themes/sleek-wood/images/menu_active.png']

        txt_data = response.xpath('//title/text()').extract_first() + '\n'
        txt_data = txt_data + response.xpath('//div[@id="top-block-left"]/p/text()').extract_first().replace('\r\n', "").replace(' ', '') + '\n'
        txt_data = txt_data + response.xpath('//a[@id="logo"]/text()').extract_first() + '\n'

        li_list = response.xpath('//ul[@class="topnav"]/li/a/text()').extract()
        txt_data = txt_data + ' '.join(li_list) + ' '

        li_list = response.xpath('//ul[@class="subnav"]/li/a/text()').extract()
        txt_data = txt_data + ' '.join(li_list) + '\n'
        # h1
        txt_data = txt_data + response.xpath('//h1/text()').extract_first() + '\n'
        # h2
        txt_data = txt_data + ' '.join(response.xpath('//h2[@class="top-title"]/a/text()').extract()) + '查询 重置' + '\n'

        # list-table
        txt_data = txt_data + ' '.join(response.xpath('//table[@class="list-table"]/thead/tr/th/text()').extract()) + '\n'

        # list_data
        page = 1
        pages = 0
        total = 0
        while True:
            url = 'http://gys.travelsky.com.cn/travelsky/noticeTendering/findAllPage'
            data = {
                "currPage": str(page),
                "pageSize": "15",
                "notice_name": "",
                "start_time": "",
                "end_time": "",
                "dept_name": ""
            }
            data_json = self.get_request(url, data=data).json()
            pages = data_json.get('pages')
            total = data_json.get('total')
            if pages >= page:
                page = page + 1
            else:
                break

            list_data = data_json.get('list')
            for i, data in enumerate(list_data):
                url = 'http://gys.travelsky.com.cn/travelsky/noticeTendering/selectHtml/' + str(data.get('id'))
                yield feapder.Request(url, callback=self.detail_parse)

                end_date = data.get('end_time').strip()
                start_time = data.get('start_time').strip()
                statustime = data.get('statustime')
                if statustime == '1':
                    statustime = "有效"
                else:
                    statustime = "过期"

                item = f"{i+1} 【{self.notice_type.get(str(data.get('notice_type')))}】{data.get('notice_name')} {data.get('dept_name')} {statustime} {start_time} {end_date}"
                txt_data = txt_data + item + '\n'

        # list_end
        page_list = ''
        for i in range(pages+1):
            page_list = page_list + ' ' + str(i+1)

        txt_data = txt_data + '首页 上一页' + page_list + f' 下一页 尾页 5/页 10/页 15/页 20/页 至 跳转 刷新 共 {pages} 页 共 {total} 记录'
        # footer
        txt_data = txt_data + response.xpath('//p[@id="copyright"]/text()').extract_first().strip() + '\n'
        txt_data = txt_data + ' '.join(response.xpath('//div[@id="footer"]/ul/li/a/text()').extract()) + '\n'

        self.create_file('notice_tendering_html', txt_data, request.url)
        self.create_img('notice_tendering_html', img_list)

    # 采购结果公告
    def notice_tendering_result(self, request, response):
        img_list = ['/themes/sleek-wood/images/bg.png', '/travelsky/images/structure/ray.png',
                    '/themes/sleek-wood/images/logo.png',
                    '/travelsky/images/icons/menu/dashboard.png', '/travelsky/images/icons/menu/page.png',
                    '/travelsky/images/icons/menu/asset.png', '/travelsky/images/icons/menu/event.png',
                    '/travelsky/images/icons/menu/task.png', '/travelsky/images/structure/divider.png',
                    '/themes/sleek-wood/images/footer.png', '/themes/sleek-wood/images/footer_logo.png',
                    '/travelsky/themes/sleek-wood/images/inner_header.png', '/travelsky/themes/sleek-wood/images/menu_active.png']

        txt_data = response.xpath('//title/text()').extract_first() + '\n'
        txt_data = txt_data + response.xpath('//div[@id="top-block-left"]/p/text()').extract_first().replace('\r\n', "").replace(' ', '') + '\n'
        txt_data = txt_data + response.xpath('//a[@id="logo"]/text()').extract_first() + '\n'

        li_list = response.xpath('//ul[@class="topnav"]/li/a/text()').extract()
        txt_data = txt_data + ' '.join(li_list) + ' '

        li_list = response.xpath('//ul[@class="subnav"]/li/a/text()').extract()
        txt_data = txt_data + ' '.join(li_list) + '\n'
        # h1
        txt_data = txt_data + response.xpath('//h1/text()').extract_first() + '\n'
        # h2
        txt_data = txt_data + ' '.join(
            response.xpath('//h2[@class="top-title"]/a/text()').extract()) + '查询 重置' + '\n'

        # list-table
        txt_data = txt_data + ' '.join(
            response.xpath('//table[@class="list-table"]/thead/tr/th/text()').extract()) + '\n'

        # list_data
        page = 1
        pages = 0
        total = 0
        while True:
            url = 'http://gys.travelsky.com.cn/travelsky/noticeTenderingResult/findPage'
            data = {
                "currPage": str(page),
                "pageSize": "15",
                "notice_name": "",
                "start_time": "",
                "end_time": "",
                "dept_name": ""
            }
            data_json = self.get_request(url, data=data).json()
            pages = data_json.get('pages')
            total = data_json.get('total')
            if pages >= page:
                page = page + 1
            else:
                break

            list_data = data_json.get('list')
            for i, data in enumerate(list_data):
                url = 'http://gys.travelsky.com.cn/travelsky/noticeTenderingResult/selectHtml/' + str(data.get('id'))
                yield feapder.Request(url, callback=self.detail_parse)

                end_date = data.get('end_time').strip()
                start_time = data.get('start_time').strip()
                statustime = data.get('statustime')
                if statustime == '1':
                    statustime = "有效"
                else:
                    statustime = "过期"

                item = f"{i + 1} {data.get('notice_name')} {data.get('dept_name')} {statustime} {start_time} {end_date}"
                txt_data = txt_data + item + '\n'

        # list_end
        page_list = ''
        for i in range(pages + 1):
            page_list = page_list + ' ' + str(i + 1)

        txt_data = txt_data + '首页 上一页' + page_list + f' 下一页 尾页 5/页 10/页 15/页 20/页 至 跳转 刷新 共 {pages} 页 共 {total} 记录'
        # footer
        txt_data = txt_data + response.xpath('//p[@id="copyright"]/text()').extract_first().strip() + '\n'
        txt_data = txt_data + ' '.join(response.xpath('//div[@id="footer"]/ul/li/a/text()').extract()) + '\n'

        self.create_file('notice_tendering_result_html', txt_data, request.url)
        self.create_img('notice_tendering_result_html', img_list)

    # 供应商公告
    def notice_supplier(self, request, response):
        img_list = ['/themes/sleek-wood/images/bg.png', '/travelsky/images/structure/ray.png',
                    '/themes/sleek-wood/images/logo.png',
                    '/travelsky/images/icons/menu/dashboard.png', '/travelsky/images/icons/menu/page.png',
                    '/travelsky/images/icons/menu/asset.png', '/travelsky/images/icons/menu/event.png',
                    '/travelsky/images/icons/menu/task.png', '/travelsky/images/structure/divider.png',
                    '/themes/sleek-wood/images/footer.png', '/themes/sleek-wood/images/footer_logo.png',
                    '/travelsky/themes/sleek-wood/images/inner_header.png',
                    '/travelsky/themes/sleek-wood/images/menu_active.png']

        txt_data = response.xpath('//title/text()').extract_first() + '\n'
        txt_data = txt_data + response.xpath('//div[@id="top-block-left"]/p/text()').extract_first().replace('\r\n',
                                                                                                             "").replace(
            ' ', '') + '\n'
        txt_data = txt_data + response.xpath('//a[@id="logo"]/text()').extract_first() + '\n'

        li_list = response.xpath('//ul[@class="topnav"]/li/a/text()').extract()
        txt_data = txt_data + ' '.join(li_list) + ' '

        li_list = response.xpath('//ul[@class="subnav"]/li/a/text()').extract()
        txt_data = txt_data + ' '.join(li_list) + '\n'
        # h1
        txt_data = txt_data + response.xpath('//h1/text()').extract_first() + '\n'
        # h2
        txt_data = txt_data + ' '.join(
            response.xpath('//h2[@class="top-title"]/a/text()').extract()) + '查询 重置' + '\n'

        # list-table
        txt_data = txt_data + ' '.join(
            response.xpath('//table[@class="list-table"]/thead/tr/th/text()').extract()) + '\n'

        # list_data
        page = 1
        pages = 0
        total = 0
        while True:
            url = 'http://gys.travelsky.com.cn/travelsky/noticeSupplier/findAllPage'
            data = {
                "currPage": str(page),
                "pageSize": "15",
                "notice_name": "",
                "start_time": "",
                "end_time": "",
                "dept_name": ""
            }
            data_json = self.get_request(url, data=data).json()
            pages = data_json.get('pages')
            total = data_json.get('total')
            if pages >= page:
                page = page + 1
            else:
                break

            list_data = data_json.get('list')
            for i, data in enumerate(list_data):
                url = 'http://gys.travelsky.com.cn/travelsky/noticeSupplier/selectHtml/' + str(data.get('id'))
                yield feapder.Request(url, callback=self.detail_parse)

                end_date = data.get('end_time').strip()
                start_time = data.get('start_time').strip()
                statustime = data.get('statustime')
                if statustime == '1':
                    statustime = "有效"
                else:
                    statustime = "过期"

                item = f"{i + 1} {data.get('notice_name')} {data.get('dept_name')} {statustime} {start_time} {end_date}"
                txt_data = txt_data + item + '\n'

        # list_end
        page_list = ''
        for i in range(pages + 1):
            page_list = page_list + ' ' + str(i + 1)

        txt_data = txt_data + '首页 上一页' + page_list + f' 下一页 尾页 5/页 10/页 15/页 20/页 至 跳转 刷新 共 {pages} 页 共 {total} 记录'
        # footer
        txt_data = txt_data + response.xpath('//p[@id="copyright"]/text()').extract_first().strip() + '\n'
        txt_data = txt_data + ' '.join(response.xpath('//div[@id="footer"]/ul/li/a/text()').extract()) + '\n'

        self.create_file('notice_supplier_html', txt_data, request.url)
        self.create_img('notice_supplier_html', img_list)

    # 其他公告
    def notice_other(self, request, response):
        img_list = ['/themes/sleek-wood/images/bg.png', '/travelsky/images/structure/ray.png',
                    '/themes/sleek-wood/images/logo.png',
                    '/travelsky/images/icons/menu/dashboard.png', '/travelsky/images/icons/menu/page.png',
                    '/travelsky/images/icons/menu/asset.png', '/travelsky/images/icons/menu/event.png',
                    '/travelsky/images/icons/menu/task.png', '/travelsky/images/structure/divider.png',
                    '/themes/sleek-wood/images/footer.png', '/themes/sleek-wood/images/footer_logo.png',
                    '/travelsky/themes/sleek-wood/images/inner_header.png',
                    '/travelsky/themes/sleek-wood/images/menu_active.png']

        txt_data = response.xpath('//title/text()').extract_first() + '\n'
        txt_data = txt_data + response.xpath('//div[@id="top-block-left"]/p/text()').extract_first().replace('\r\n', "").replace(' ', '') + '\n'
        txt_data = txt_data + response.xpath('//a[@id="logo"]/text()').extract_first() + '\n'

        li_list = response.xpath('//ul[@class="topnav"]/li/a/text()').extract()
        txt_data = txt_data + ' '.join(li_list) + ' '

        li_list = response.xpath('//ul[@class="subnav"]/li/a/text()').extract()
        txt_data = txt_data + ' '.join(li_list) + '\n'
        # h1
        txt_data = txt_data + response.xpath('//h1/text()').extract_first() + '\n'
        # h2
        txt_data = txt_data + ' '.join(
            response.xpath('//h2[@class="top-title"]/a/text()').extract()) + '查询 重置' + '\n'

        # list-table
        txt_data = txt_data + ' '.join(
            response.xpath('//table[@class="list-table"]/thead/tr/th/text()').extract()) + '\n'

        # list_data
        page = 1
        pages = 0
        total = 0
        while True:
            url = 'http://gys.travelsky.com.cn/travelsky/noticeOther/findAllPage'
            data = {
                "currPage": str(page),
                "pageSize": "15",
                "notice_name": "",
                "start_time": "",
                "end_time": "",
                "dept_name": ""
            }
            data_json = self.get_request(url, data=data).json()
            pages = data_json.get('pages')
            total = data_json.get('total')
            if pages >= page:
                page = page + 1
            else:
                break

            list_data = data_json.get('list')
            for i, data in enumerate(list_data):
                url = 'http://gys.travelsky.com.cn/travelsky/noticeOther/selectHtml/' + str(data.get('id'))
                yield feapder.Request(url, callback=self.detail_parse)

                end_date = data.get('end_time').strip()
                start_time = data.get('start_time').strip()
                statustime = data.get('statustime')
                if statustime == '1':
                    statustime = "有效"
                else:
                    statustime = "过期"

                item = f"{i + 1} {data.get('notice_name')} {data.get('dept_name')} {statustime} {start_time} {end_date}"
                txt_data = txt_data + item + '\n'

        # list_end
        page_list = ''
        for i in range(pages + 1):
            page_list = page_list + ' ' + str(i + 1)

        txt_data = txt_data + '首页 上一页' + page_list + f' 下一页 尾页 5/页 10/页 15/页 20/页 至 跳转 刷新 共 {pages} 页 共 {total} 记录'
        # footer
        txt_data = txt_data + response.xpath('//p[@id="copyright"]/text()').extract_first().strip() + '\n'
        txt_data = txt_data + ' '.join(response.xpath('//div[@id="footer"]/ul/li/a/text()').extract()) + '\n'

        self.create_file('notice_other_html', txt_data, request.url)
        self.create_img('notice_other_html', img_list)

    # 帮助文档
    def notice_doc(self, request, response):
        img_list = ['/themes/sleek-wood/images/bg.png', '/travelsky/images/structure/ray.png',
                    '/themes/sleek-wood/images/logo.png',
                    '/travelsky/images/icons/menu/dashboard.png', '/travelsky/images/icons/menu/page.png',
                    '/travelsky/images/icons/menu/asset.png', '/travelsky/images/icons/menu/event.png',
                    '/travelsky/images/icons/menu/task.png', '/travelsky/images/structure/divider.png',
                    '/themes/sleek-wood/images/footer.png', '/themes/sleek-wood/images/footer_logo.png',
                    '/travelsky/themes/sleek-wood/images/inner_header.png',
                    '/travelsky/themes/sleek-wood/images/menu_active.png']

        txt_data = response.xpath('//title/text()').extract_first() + '\n'
        txt_data = txt_data + response.xpath('//div[@id="top-block-left"]/p/text()').extract_first().replace('\r\n', "").replace(' ', '') + '\n'
        txt_data = txt_data + response.xpath('//a[@id="logo"]/text()').extract_first() + '\n'

        li_list = response.xpath('//ul[@class="topnav"]/li/a/text()').extract()
        txt_data = txt_data + ' '.join(li_list) + ' '

        li_list = response.xpath('//ul[@class="subnav"]/li/a/text()').extract()
        txt_data = txt_data + ' '.join(li_list) + '\n'
        # h1
        txt_data = txt_data + response.xpath('//h1/text()').extract_first() + '\n'
        # h2
        txt_data = txt_data + ' '.join(
            response.xpath('//h2[@class="top-title"]/a/text()').extract()) + '查询 重置' + '\n'

        # list-table
        txt_data = txt_data + ' '.join(
            response.xpath('//table[@class="list-table"]/thead/tr/th/text()').extract()) + '\n'

        # list_data
        page = 1
        pages = 0
        total = 0
        while True:
            url = 'http://gys.travelsky.com.cn/travelsky/noticeDoc/findAllPage'
            data = {
                "currPage": str(page),
                "pageSize": "15",
                "notice_name": "",
                "start_time": "",
                "end_time": "",
                "dept_name": ""
            }
            data_json = self.get_request(url, data=data).json()
            pages = data_json.get('pages')
            total = data_json.get('total')
            if pages >= page:
                page = page + 1
            else:
                break

            list_data = data_json.get('list')
            for i, data in enumerate(list_data):
                url = 'http://gys.travelsky.com.cn/travelsky/noticeDoc/selectHtml/' + str(data.get('id'))
                yield feapder.Request(url, callback=self.detail_parse)

                end_date = data.get('end_time').strip()
                start_time = data.get('start_time').strip()
                statustime = data.get('statustime')
                if statustime == '1':
                    statustime = "有效"
                else:
                    statustime = "过期"

                item = f"{i + 1} {data.get('notice_name')} {data.get('dept_name')} {statustime} {start_time} {end_date}"
                txt_data = txt_data + item + '\n'

        # list_end
        page_list = ''
        for i in range(pages + 1):
            page_list = page_list + ' ' + str(i + 1)

        txt_data = txt_data + '首页 上一页' + page_list + f' 下一页 尾页 5/页 10/页 15/页 20/页 至 跳转 刷新 共 {pages} 页 共 {total} 记录'
        # footer
        txt_data = txt_data + response.xpath('//p[@id="copyright"]/text()').extract_first().strip() + '\n'
        txt_data = txt_data + ' '.join(response.xpath('//div[@id="footer"]/ul/li/a/text()').extract()) + '\n'

        self.create_file('notice_doc_html', txt_data, request.url)
        self.create_img('notice_doc_html', img_list)

    # 详情页解析
    def detail_parse(self, request, response):
        img_list = ['/themes/sleek-wood/images/bg.png', '/travelsky/images/structure/ray.png',
                    '/themes/sleek-wood/images/logo.png',
                    '/travelsky/images/icons/menu/dashboard.png', '/travelsky/images/icons/menu/page.png',
                    '/travelsky/images/icons/menu/asset.png', '/travelsky/images/icons/menu/event.png',
                    '/travelsky/images/icons/menu/task.png', '/travelsky/images/structure/divider.png',
                    '/themes/sleek-wood/images/footer.png', '/themes/sleek-wood/images/footer_logo.png',
                    '/travelsky/themes/sleek-wood/images/inner_header.png',
                    '/travelsky/themes/sleek-wood/images/menu_active.png']

        txt_data = response.xpath('//title/text()').extract_first() + '\n'
        txt_data = txt_data + response.xpath('//div[@id="top-block-left"]/p/text()').extract_first().replace('\r\n', "").replace(' ', '') + '\n'
        txt_data = txt_data + response.xpath('//a[@id="logo"]/text()').extract_first() + '\n'

        li_list = response.xpath('//ul[@class="topnav"]/li/a/text()').extract()
        txt_data = txt_data + ' '.join(li_list) + ' '

        li_list = response.xpath('//ul[@class="subnav"]/li/a/text()').extract()
        txt_data = txt_data + ' '.join(li_list) + '\n'
        # h1
        txt_data = txt_data + response.xpath('//h1/text()').extract_first() + '\n'

        txt_data = txt_data + response.xpath('//div[@id="content"]/div[2]/input/@value').extract_first() + '\n'

        span_list = response.xpath('//div[@id="content"]/div[3]/span/text()').extract()
        input_list = response.xpath('//div[@id="content"]/div[3]/input/@value').extract()
        select_list = response.xpath('//div[@id="content"]/div[3]/select/option/text()').extract()

        new_list = input_list + select_list

        item = ''
        for i, span in enumerate(span_list):
            item = item + span.strip() + ' ' + new_list[i].strip() + '  '

        txt_data = txt_data + item + '\n'

        # tbody - table
        textarea = response.xpath('//textarea').extract_first()
        if response.xpath('//table'):
            for i in range(len(response.xpath('//table'))):
                textarea = re.sub(r'(<table[\s\S]*?</table>)', '{' + str(i) + '}', textarea, 1)

        new_string = re.sub(r'<!--.*?-->', '', textarea)
        new_string = re.sub(r'<textarea.*?>', '', new_string)
        new_string = re.sub(r'</textarea>', '', new_string)
        new_string = re.sub(r'<h.*?>', '', new_string)
        new_string = re.sub(r'</h.*?>', '', new_string)
        new_string = re.sub(r'<span.*?>', '', new_string)
        new_string = re.sub(r'</span.*?>', '', new_string)
        new_string = re.sub(r'<td.*?>', '', new_string)
        new_string = re.sub(r'</td.*?>', '', new_string)
        new_string = re.sub(r'<tr.*?>', '', new_string)
        new_string = re.sub(r'</tr.*?>', '', new_string)
        new_string = re.sub(r'<div.*?>', '', new_string)
        new_string = re.sub(r'</div.*?>', '', new_string)

        new_string = new_string.replace('<b>', '')
        new_string = new_string.replace('</b>', '')
        new_string = new_string.replace('<br />', '')
        new_string = new_string.replace('<br>', '')
        new_string = new_string.replace('</p>', '')
        new_string = new_string.replace('</tbody>', '')
        new_string = new_string.replace('</table>', '')
        new_string = re.sub(r'<p.*?>', '', new_string)

        new_string = new_string.replace('&nbsp;', '')
        new_string = new_string.replace('\n', '')
        new_string = new_string.replace('\t\t\t\t', '\t')
        new_string = new_string.replace('\t \t \t \t', '\t')
        new_string = new_string.replace('\t\t\t', '\t')
        new_string = new_string.replace('\t \t \t', '\t')
        new_string = new_string.replace('\t\t', '\t')
        new_string = new_string.replace('\t \t', '\t')
        new_string = new_string.replace('\t', '\n').strip() + '\n'

        item_list = []

        if response.xpath('//table'):
            table_list = response.xpath('//table')
            for i, table in enumerate(table_list):
                tr_list = table.xpath('./tbody/tr')
                item = ''
                for tr in tr_list:
                    td_list = tr.xpath('./td')
                    for td in td_list:
                        item = item + ''.join(td.xpath('./p/span/text()').extract()) + ' '

                    item = item + '\n'

                item_list.append(item)

        new_string = new_string.format(*item_list)

        txt_data = txt_data + new_string.replace(' ', '')

        # 附件
        f_ids = response.xpath('//input[@id="f_ids"]/@value').extract_first()
        f_name = ''
        if f_ids:
            ids_list = f_ids.split(',')
            for ids in ids_list:
                ids = ids.strip()
                url = 'http://gys.travelsky.com.cn/travelsky/noticeTendering/uploadByIdOne/' + ids
                f_name = f_name + self.get_request(url).json().get('name') + ' '

        txt_data = txt_data + '下载附件：' + f_name + '\n返回\n'

        # footer
        txt_data = txt_data + response.xpath('//p[@id="copyright"]/text()').extract_first().strip() + '\n'
        txt_data = txt_data + ' '.join(response.xpath('//div[@id="footer"]/ul/li/a/text()').extract()) + '\n'

        def camel_to_snake(s):
            s1 = re.sub('(.)([A-Z][a-z]+)', lambda m: m.group(1) + '_' + m.group(2).lower(), s)
            return re.sub('([a-z0-9])([A-Z])', lambda m: m.group(1) + '_' + m.group(2).lower(), s1)


        url_split = request.url.split("/")
        path_name = camel_to_snake(url_split[-3]) + "_" + url_split[-1]

        self.create_file(path_name, txt_data, request.url)
        self.create_img(path_name, img_list)

    def logi(self, request, response):
        """登录"""
        img_list = ['/themes/sleek-wood/images/bg.png', '/travelsky/images/structure/ray.png',
                    '/themes/sleek-wood/images/logo.png', '/themes/sleek-wood/images/login_bg.png',
                    '/travelsky/images/structure/login_input_bg.png', '/travelsky/images/structure/wrapper.png',
                    '/travelsky/themes/sleek-wood/images/inner_header.png', '/travelsky/images/structure/submit-overlay-sprite.png',
                    '/travelsky/verify/getcode']

        txt_data = response.xpath('//title/text()').extract_first() + '\n'
        txt_data += response.xpath('//div[@id="login-title"]/h1/text()').extract_first() + '\n'
        txt_data += response.xpath('//div[@id="login-title"]/p/text()').extract_first() + '\n'

        txt_data += response.xpath('//div[@id="wrapper"]/p/text()').extract_first() + '\n'
        txt_data += response.xpath('//label[@for="name"]/text()').extract_first() + '\n'
        txt_data += response.xpath('//label[@for="password"]/text()').extract_first() + '\n'
        txt_data += response.xpath('//label[@for="checkcode"]/text()').extract_first() + '\n'

        txt_data += ' '.join(response.xpath('//div[@id="remember-me"]/a/text()').extract()) + ' '

        txt_data += response.xpath('//input[@id="login-button"]/@value').extract_first() + ' '
        txt_data += response.xpath('//input[@id="login-button1"]/@value').extract_first()

        self.create_file('logi', txt_data, request.url)
        self.create_img('logi', img_list)


if __name__ == "__main__":
    start_time = time.time()
    start_time_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))
    logger.debug(f'爬取中 gys_travelsky_com_cn 并行任务 {thread_count} 个')
    GysTravelskyComCn(thread_count=thread_count).start()

    while True:
        if len(threading.enumerate()) == 1:
            meta_json_path = os.path.join(date_path, 'meta.json')
            with open(meta_json_path, 'w', encoding='utf8') as f:
                json.dump(meta_json, f, ensure_ascii=False, indent=4)
            break
        time.sleep(3)

    end_time = time.time()
    end_time_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))
    logger.debug(f'{start_time_date} 开始 - {end_time_date} 结束 耗时{end_time-start_time}秒任务成功')
    logger.debug(f'本次共爬取{img_not_download_num+img_download_num+file_download_num}个元素 其中{file_download_num}个文本数据 {img_not_download_num+img_download_num}个图片数据，压缩重复元素{img_not_download_num}个，本地存储元素{img_download_num+file_download_num}个')


