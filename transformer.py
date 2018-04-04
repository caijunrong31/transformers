# -*- coding: utf-8 -*-
import scrapy
import redis

from bankDataSpider.items import TransformerItem
from bankDataSpider.tools.commen import BankSpiderLog
from bankDataSpider.tools.transformer_compare import get_series_data, follow_series_data_msg,get_info
from bankDataSpider.tools.transformer_compare import DbOperNoSQL


class TransformerSpider(scrapy.Spider):
    name = 'transformer'
    allowed_domains = ['http://www.actoys.net', 'http://ku.actoys.net']
    start_urls = ['http://www.actoys.net/toys-45-0.html']

    custom_settings = {
        'ITEM_PIPELINES': {
            'bankDataSpider.pipelinesT.MysqlPipeline': 10,
            'bankDataSpider.pipelinesT.TransformerImagePipline': 1
        }
    }

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Host': 'www.actoys.net',
        'Referer': 'http://www.actoys.net/toys-45-0.html',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:51.0) Gecko/20100101 Firefox/51.0'
    }

    headers_ku = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Host': 'ku.actoys.net',
        'Referer': 'http://ku.actoys.net',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:51.0) Gecko/20100101 Firefox/51.0'
    }

    def __init__(self):
        super(TransformerSpider, self).__init__()
        # db_params = {"host_name": "127.0.0.1", "port": 6379}
        # self.dbOper_no = DbOperNoSQL(db_params)
        # index = dbOper.log_already_download_url('http://ku.actoys.net')
        pass


    def parse(self, response):
        self.series_dict_list = []
        BankSpiderLog.log_info2("in first page!")
        parent_series_list = response.css('div.bbs_fath')
        parent_series_count = str(len(parent_series_list))
        # 遍历大系列
        for i, parent_series_item in enumerate(parent_series_list):
            series_dict = {}
            series_dict['sub_series'] = []
            self.series_dict_list.append(series_dict)
            parent_series_name = parent_series_item.css('h2 span.title a::attr(title)').extract_first("").strip()
            # BankSpiderLog.log_info2("{in first page!} (" + str(i+1) + "/" + parent_series_count + ") {parent_series_name: " + parent_series_name + "}")
            parent_series_url = parent_series_item.css('h2 span.title a::attr(href)').extract_first("").strip()
            parent_series_img = parent_series_item.css('h2 span.title img::attr(src)').extract_first("").strip()
            series_dict['parent_series_count'] = parent_series_count
            series_dict['parent_series_id'] = i
            series_dict['parent_series_name'] = parent_series_name
            series_dict['parent_series_url'] = parent_series_url
            series_dict['parent_series_img'] = parent_series_img

            sub_series_list = parent_series_item.xpath('div//dl[@class="bbs_son"]')
            sub_series_count = str(len(sub_series_list))
            series_dict['sub_series_count'] = sub_series_count
            # 遍历子系列
            for j, sub_series_item in enumerate(sub_series_list):
                sub_series_dict = {}
                series_dict['sub_series'].append(sub_series_dict)
                sub_series_url = sub_series_item.xpath('./dd/a[@class="subtitle"]/@href').extract_first("").strip()
                sub_series_name_cn = sub_series_item.xpath('.//a[@class="subtitle"]/strong/text()').extract_first("").strip()
                sub_series_name_en = sub_series_item.xpath('.//a[@class="subtitle"]/p/text()').extract_first("").strip()
                # BankSpiderLog.log_info2("{in first page!} (" + str(
                #     j+1) + "/" + sub_series_count + ") {sub_series_name: " + sub_series_name_en + "}")
                sub_series_dict['sub_series_id'] = j
                sub_series_dict['url'] = sub_series_url
                sub_series_dict['name_cn'] = sub_series_name_cn
                sub_series_dict['name_en'] = sub_series_name_en
                # 遍历版本
                self.series_dict_list[i]['sub_series'][j]['version'] = []
                version_selector = sub_series_item.xpath('.//a[@class="items"]')
                if version_selector:
                    version_selector_count = len(version_selector)
                    sub_series_dict['version_count'] = version_selector_count
                    for k, version_selector_item in enumerate(version_selector):
                        version_dict = {}
                        self.series_dict_list[i]['sub_series'][j]['version'].append(version_dict)
                        version_dict['version_id'] = k
                        version_dict['url'] = version_selector_item.xpath('./@href').extract_first("").strip()
                        version_dict['version_name'] = version_selector_item.xpath('./text()').extract_first("").strip()
                        # BankSpiderLog.log_info2("{in first page!} (" + str(
                        #     k + 1) + "/" + str(version_selector_count) + ") {version_name: " + sub_series_dict['version_name'] + "}")
                        # 进入版本级别页面
                        # self.headers['Referer'] = response.url
                        yield scrapy.Request(
                            url= version_dict['url'],
                            headers=self.headers,
                            meta={
                                'parent_series_id': i,
                                'sub_series_id': j,
                                'version_id': k
                            },
                            callback=self.in_version_level_page,
                            dont_filter=True
                        )
                else:
                    sub_series_dict['version_count'] = 1
                    version_dict = {}
                    if u"日版" in sub_series_name_cn or u"美版" in sub_series_name_cn:
                        version_dict['version_name'] = sub_series_name_cn[sub_series_name_cn.find('(')+1:sub_series_name_cn.find(')')]
                    else:
                        version_dict['version_name'] = ''
                    version_dict['version_id'] = 0
                    version_dict['url'] = ''
                    self.series_dict_list[i]['sub_series'][j]['version'].append(version_dict)
                    # 进入版本级别页面
                    # self.headers['Referer'] = response.url
                    yield scrapy.Request(
                        url=sub_series_url,
                        headers=self.headers,
                        meta={
                            'parent_series_id': i,
                            'sub_series_id': j,
                            'version_id': 0
                        },
                        callback=self.in_version_level_page,
                        dont_filter=True
                    )

    def in_version_level_page(self, response):
        # 获取大系列数据
        parent_series_id = response.meta.get('parent_series_id', '')
        sub_series_id = response.meta.get('sub_series_id', '')
        version_id = response.meta.get('version_id', '')
        parent_series_data = get_series_data(self.series_dict_list, parent_series_id)
        # 获取子系列数据
        sub_series_data = get_series_data(parent_series_data.get('sub_series',[]), sub_series_id)
        if sub_series_data:
            # 获取版本级别数据
            version_series_data = get_series_data(sub_series_data.get('version',[]), version_id)
            if version_series_data:
                follow_series_data_msg(
                    parent_series_id,
                    parent_series_data['parent_series_count'],
                    parent_series_data['parent_series_name'],
                    'parent_series'
                )
                follow_series_data_msg(
                    sub_series_id,
                    parent_series_data['sub_series_count'],
                    sub_series_data['name_cn'],
                    'sub_series'
                )
                follow_series_data_msg(
                    version_id,
                    sub_series_data['version_count'],
                    version_series_data['version_name'],
                    'version'
                )
                # 遍历某子系列下的版本级别数据
                version_series_data['toys'] = []
                table_toys_list = response.xpath('//table[@class="tabletoys"]')
                toy_id_count = 0
                version_series_data['toy_count'] = len(response.xpath('//table[@class="tabletoys"]//li'))
                for i, table_toys_item in enumerate(table_toys_list):
                    title_tr = table_toys_item.xpath('.//th[@class="tthead"]')
                    level_img = title_tr[0].xpath("../@style").extract_first("").strip()
                    level_img = level_img[level_img.find("(")+1:level_img.find(")")]
                    level_name = title_tr[0].xpath("./text()").extract_first("").replace("::", "").strip()
                    print("level_name: " + level_name)
                    # 遍历某版本级别中的玩具数据
                    toys_list = table_toys_item.xpath('.//tr')[1].xpath('.//li')
                    for j, toys_item in enumerate(toys_list):
                        toy = {}
                        version_series_data['toys'].append(toy)
                        toy['id'] = j
                        toy_url = toys_item.xpath('./a/@href').extract_first("").strip()
                        toy['url'] = toy_url
                        toy['head_img'] = toys_item.xpath('./a/img/@src').extract_first("").strip()
                        toy['name'] = toys_item.xpath('./a/@title').extract_first("").strip()
                        toy['level_img'] = level_img
                        toy['level_name'] = level_name
                        # if toy['name'] != u"大黄蜂":
                        print("toy_url: " + toy_url + " head_img: " + toy['head_img'] + 'toy_name: ' + toy['name'])
                        # 进入玩具详情页面
                        # is_download = self.dbOper_no.log_already_download_url(toys_item.xpath('./a/@href').extract_first("").strip())
                        # if is_download:
                        yield scrapy.Request(
                            url=toys_item.xpath('./a/@href').extract_first("").strip(),
                            headers=self.headers_ku,
                            meta={
                                'parent_series_id': parent_series_id,
                                'sub_series_id': sub_series_id,
                                'version_id': version_id,
                                'toy_id': toy_id_count
                            },
                            callback=self.in_toy_detail_page,
                            dont_filter=True
                        )
                        toy_id_count += 1
        else:
            BankSpiderLog.log_info2("{in version level page} no series data")

    def in_toy_detail_page(self, response):
        # 获取大系列数据
        parent_series_id = response.meta.get('parent_series_id', '')
        sub_series_id = response.meta.get('sub_series_id', '')
        version_id = response.meta.get('version_id', '')
        toy_id = response.meta.get('toy_id', '')
        parent_series_data = get_series_data(self.series_dict_list, parent_series_id)
        # 获取子系列数据
        sub_series_data = get_series_data(parent_series_data.get('sub_series', []), sub_series_id)
        if sub_series_data:
            # 获取版本级别数据
            version_series_data = get_series_data(sub_series_data.get('version', []), version_id)
            if version_series_data:
                follow_series_data_msg(
                    parent_series_id,
                    parent_series_data['parent_series_count'],
                    parent_series_data['parent_series_name'],
                    'parent_series'
                )
                follow_series_data_msg(
                    sub_series_id,
                    parent_series_data['sub_series_count'],
                    sub_series_data['name_cn'],
                    'sub_series'
                )
                follow_series_data_msg(
                    version_id,
                    sub_series_data['version_count'],
                    version_series_data['version_name'],
                    'version'
                )
                # 获取模型数据
                toy_data = get_series_data(version_series_data.get('toys', []), toy_id)
                if toy_data:
                    follow_series_data_msg(
                        toy_id,
                        version_series_data['toy_count'],
                        toy_data['name'],
                        'toy'
                    )
                    # 补全模型数据
                    toy_info_list = response.xpath('//table[@class="tf_table_info"]//td/text()').extract()
                    toy_data["classify"] = get_info(toy_info_list[0], u"所属分类")
                    toy_data["limited_mode"] = get_info(toy_info_list[3], u"限定方式")
                    toy_data["release_time"] = get_info(toy_info_list[5], u"发行时间")
                    toy_data["accessories"] = get_info(toy_info_list[7], u"件")
                    toy_data["acoustooptic_effect"] = get_info(toy_info_list[8], u"声光效果")
                    toy_data["sizes"] = get_info(toy_info_list[9], u"寸")
                    toy_data["movable_type"] = get_info(toy_info_list[10], u"可动类型")
                    toy_data["material"] = get_info(toy_info_list[11], u"质")
                    toy_data["product_company"] = get_info(toy_info_list[12], u"出品公司")
                    toy_data["contributor_source"] = get_info(toy_info_list[13], u"贡献人&来源")
                    toy_data["imgs"] = response.xpath('//div[@class="pic"]//img/@src').extract()

                    transformerItem = TransformerItem()
                    transformerItem['parent_series_id'] = parent_series_id
                    transformerItem['sub_series_id'] = sub_series_id
                    transformerItem['version_id'] = version_id
                    transformerItem['toy_id'] = toy_id
                    image_urls = []
                    image_urls.append(parent_series_data['parent_series_img'])
                    image_urls.append(toy_data['level_img'])
                    image_urls.append(toy_data['head_img'])
                    image_urls = image_urls + toy_data["imgs"]
                    transformerItem['front_image_url'] = image_urls
                    yield transformerItem
