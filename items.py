# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy

class BankdataspiderItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class CitidirectItem(scrapy.Item):
    file_name = scrapy.Field()
    sub_dir = scrapy.Field()
    issuer = scrapy.Field()
    in_dir = scrapy.Field()
    res_text = scrapy.Field()


class UsBankItem(scrapy.Item):
    source_file_name = scrapy.Field()
    file_name = scrapy.Field()
    issuer = scrapy.Field()
    deal = scrapy.Field()
    file_type = scrapy.Field()
    download_type = scrapy.Field()
    report_date = scrapy.Field()
    res_text = scrapy.Field()
    # file_urls = scrapy.Field()
    # headers = scrapy.Field()


class CtslinkItem(scrapy.Item):
    # file_urls = scrapy.Field()
    url = scrapy.Field()
    issuer = scrapy.Field()
    deal = scrapy.Field()
    file_type= scrapy.Field()
    # shelfId = scrapy.Field()
    # seriesId = scrapy.Field()
    # tab =  scrapy.Field()
    # documentChkBx = scrapy.Field()
    # zip = scrapy.Field()
    # headers = scrapy.Field()
    file_all_name = scrapy.Field()
    file_all_name_zip = scrapy.Field()
    link_condition = scrapy.Field()
    file_name = scrapy.Field()
    revised = scrapy.Field()
    res_text = scrapy.Field()


class CitimortgageItem(scrapy.Item):
    shelf_name = scrapy.Field()
    row_name = scrapy.Field()
    file_urls = scrapy.Field()
    file_name = scrapy.Field()
    #files = scrapy.Field()
    file_type = scrapy.Field()
    res_text = scrapy.Field()
    headers = scrapy.Field()


class FreddiemacItem(scrapy.Item):
    content = scrapy.Field()
    # file_url = scrapy.Field()
    # headers = scrapy.Field()
    file_name = scrapy.Field()
    file_style = scrapy.Field()
    pass


class DbIRItem(scrapy.Item):
    # file_url = scrapy.Field()
    file_name = scrapy.Field()
    file_type = scrapy.Field()
    file_path = scrapy.Field()
    report_type = scrapy.Field()
    deal_name = scrapy.Field()
    deal_info = scrapy.Field()
    download_type = scrapy.Field()
    report_date = scrapy.Field()
    res_text = scrapy.Field()
    # headers = scrapy.Field()


class BnyItem(scrapy.Item):
    content = scrapy.Field()
    issuer_name = scrapy.Field()
    deal_name = scrapy.Field()
    file_type = scrapy.Field()
    file_name = scrapy.Field()
    file_path_zip = scrapy.Field()
    product_type = scrapy.Field()
    report_date = scrapy.Field()
    revised_date = scrapy.Field()
    report_text = scrapy.Field()


class OcwenItem(scrapy.Item):
    content = scrapy.Field()
    out_dir = scrapy.Field()
    file_name = scrapy.Field()


#
class TransformerItem(scrapy.Item):
    parent_series_id = scrapy.Field()
    sub_series_id = scrapy.Field()
    version_id = scrapy.Field()
    toy_id = scrapy.Field()
    front_image_url = scrapy.Field()
    front_image_path = scrapy.Field()
