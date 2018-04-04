# -*- coding: utf-8 -*-
import MySQLdb
import datetime

from scrapy.pipelines.images import ImagesPipeline
# adbapi 可以将mysql的操作变成非同步操作
# from twisted.enterprise import adbapi

from bankDataSpider.tools.transformer_compare import get_series_data


class TransformerPipeline(object):
    def process_item(self, item, spider):
        pass


class TransformerImagePipline(ImagesPipeline):
    def item_completed(self, results, item, info):
        item["front_image_path"] = []
        if "front_image_url" in item:
            for ok, value in results:
                image_file_path = value["path"]
                item["front_image_path"].append(image_file_path)

        return item


class MysqlPipeline(object):
    def __init__(self, conn, cursor):
        self.conn = conn
        self.cursor = cursor

    # 重写这个方法可以获取settings中的值
    @classmethod
    def from_settings(cls, settings):
        conn = MySQLdb.connect(
            settings["MYSQL_HOST"],
            settings["MYSQL_USER"],
            settings["MYSQL_PASSWORD"],
            settings["MYSQL_DBNAME"], charset="utf8", use_unicode=True)
        cursor = conn.cursor()

        return cls(conn,cursor)


    def process_item(self, item, spider):
        # 获取item中传递的参数
        parent_series_id = item['parent_series_id']
        sub_series_id = item['sub_series_id']
        version_id = item['version_id']
        toy_id = item['toy_id']
        image_paths = item['front_image_path']
        # 获取大系列数据
        parent_series_data = get_series_data(spider.series_dict_list, parent_series_id)
        # 获取子系列数据
        sub_series_data = get_series_data(parent_series_data.get('sub_series', []), sub_series_id)
        if sub_series_data:
            # 获取版本级别数据
            version_level_data = get_series_data(sub_series_data.get('version', []), version_id)
            # 获取模型数据
            toy_data = get_series_data(version_level_data.get('toys', []), toy_id)
            # 插入或更新parent_series表数据
            parent_series_data_id = self.get_data_id(toy_data['classify'], "parent")
            if parent_series_data_id == -1:
                parent_series_insert_sql = self.get_insert_sql("parent")
                parent_series_data_id = self.do_execute(
                    parent_series_insert_sql,
                    (
                        toy_data['classify'],
                        parent_series_data['parent_series_url']
                    )
                )
            else:
                self.updata_parent_data(
                    {
                        "name": parent_series_data["parent_series_name"],
                        "url": parent_series_data["parent_series_url"]
                     },
                    parent_series_data_id,
                    'parent_series'
                )
            # 输入或更新ohter_imgs表数据（parent_series）
            other_imgs_data_id = self.get_data_id(parent_series_data_id, "other_imgs", 0)
            if other_imgs_data_id == -1:
                other_imgs_insert_sql = self.get_insert_sql("other_imgs")
                self.do_execute(
                    other_imgs_insert_sql,
                    (
                        parent_series_data_id,
                        0,
                        0,
                        image_paths[0]
                    )
                )
            else:
                self.updata_img_data(
                    {
                        'master_id': parent_series_data_id,
                        'type': 0,
                        'paths': [image_paths[0]]
                    },
                    other_imgs_data_id,
                    'other_imgs'
                )
            # 插入或更新sub_series表数据
            sub_series_data_id = self.get_data_id(sub_series_data['name_cn'], "sub")
            if sub_series_data_id == -1:
                sub_series_insert_sql = self.get_insert_sql("sub")
                sub_series_data_id = self.do_execute(
                    sub_series_insert_sql,
                    (
                        parent_series_data_id,
                        sub_series_data['name_cn'],
                        sub_series_data['name_en'],
                        sub_series_data['url']
                    )
                )
            else:
                self.updata_sub_data(
                    {
                        "parent_id": parent_series_data_id,
                        "name_cn": sub_series_data["name_cn"],
                        "name_en": sub_series_data["name_en"],
                        "url": sub_series_data["url"]
                    },
                    sub_series_data_id,
                    'sub_series'
                )
            # 输入或更新ohter_imgs表数据（sub_series）
            other_imgs_data_id = self.get_data_id(sub_series_data_id, "other_imgs", 1)
            if other_imgs_data_id == -1:
                other_imgs_insert_sql = self.get_insert_sql("other_imgs")
                self.do_execute(
                    other_imgs_insert_sql,
                    (
                        sub_series_data_id,
                        0,
                        1,
                        image_paths[1]
                    )
                )
            else:
                self.updata_img_data(
                    {
                        'master_id': sub_series_data_id,
                        'type': 1,
                        'paths': [image_paths[1]]
                    },
                    other_imgs_data_id,
                    'other_imgs'
                )
            # 输入或更新version_level表数据
            version_level_data_id = self.get_data_id(toy_data['level_name'], "version_level")
            if version_level_data_id == -1:
                version_level_insert_sql = self.get_insert_sql("version_level")
                version_level_data_id = self.do_execute(
                    version_level_insert_sql,
                    (
                        sub_series_data_id,
                        version_level_data['version_name'],
                        toy_data['level_name'],
                        version_level_data['url']
                    )
                )
            else:
                self.updata_version_level_data(
                    {
                        "sub_series_id": sub_series_data_id,
                        "name": version_level_data['version_name'],
                        "level_name": toy_data['level_name'],
                        "url": version_level_data['url'],
                    },
                    version_level_data_id,
                    'version_level'
                )
            # 输入或更新toy表数据
            toy_data_id = self.get_data_id(toy_data['name'], "toy")
            if toy_data_id == -1:
                toy_insert_sql = self.get_insert_sql("toy")
                toy_data_id = self.do_execute(
                    toy_insert_sql,
                    (
                        version_level_data_id,
                        toy_data['name'],
                        image_paths[2],
                        toy_data['url'],
                        toy_data['limited_mode'],
                        toy_data['release_time'],
                        toy_data['accessories'],
                        toy_data['acoustooptic_effect'],
                        toy_data['sizes'],
                        toy_data['movable_type'],
                        toy_data['material'],
                        toy_data['product_company'],
                        toy_data['contributor_source']
                    )
                )
            else:
                self.updata_toy_data(
                    {
                        'version_level_data_id': version_level_data_id,
                        'name': toy_data['name'],
                        'head_img': image_paths[2],
                        'url': toy_data['url'],
                        'limited_mode': toy_data['limited_mode'],
                        'release_time': toy_data['release_time'],
                        'accessories': toy_data['accessories'],
                        'acoustooptic_effect': toy_data['acoustooptic_effect'],
                        'sizes': toy_data['sizes'],
                        'movable_type': toy_data['movable_type'],
                        'material': toy_data['material'],
                        'product_company': toy_data['product_company'],
                        'contributor_source': toy_data['contributor_source']
                    },
                    toy_data_id,
                    'toy'
                )
            # 输入或更新ohter_imgs表数据（toy）
            toy_order_imgs = image_paths[2:]
            for i, img_path in enumerate(toy_order_imgs):
                other_imgs_data_id = self.get_data_id(toy_data_id, "other_imgs", 2, i)
                if other_imgs_data_id == -1:
                    other_imgs_insert_sql = self.get_insert_sql("other_imgs")
                    self.do_execute(
                        other_imgs_insert_sql,
                        (
                            toy_data_id,
                            i,
                            2,
                            toy_order_imgs[i]
                        )
                    )
                else:
                    self.updata_img_data(
                        {
                            'master_id': toy_data_id,
                            'type': 2,
                            'paths': toy_order_imgs
                        },
                        other_imgs_data_id,
                        'other_imgs'
                    )


    def get_update_sql(self, update_field, table_name, type=0):
        update_sql = ''
        if type == 0:
            update_sql = """
                  update """ + table_name + """ set """ + update_field + """=%s where id=%s
              """
        elif type == 1:
            update_sql = """
                             update """ + table_name + """ set """ + update_field + """=%s where id=%s and order_num=%s
                         """
        return update_sql


    def updata_toy_data(self, data, where_field, type):
        update_sql = self.get_update_sql('version_level_data_id', type)
        self.do_execute(
            update_sql,
            (
                data['version_level_data_id'],
                where_field
            )
        )
        update_sql = self.get_update_sql('name', type)
        self.do_execute(
            update_sql,
            (
                data['name'],
                where_field
            )
        )
        update_sql = self.get_update_sql('head_img', type)
        self.do_execute(
            update_sql,
            (
                data['head_img'],
                where_field
            )
        )
        update_sql = self.get_update_sql('url', type)
        self.do_execute(
            update_sql,
            (
                data['url'],
                where_field
            )
        )
        update_sql = self.get_update_sql('limited_mode', type)
        self.do_execute(
            update_sql,
            (
                data['limited_mode'],
                where_field
            )
        )
        update_sql = self.get_update_sql('release_time', type)
        self.do_execute(
            update_sql,
            (
                data['release_time'],
                where_field
            )
        )
        update_sql = self.get_update_sql('accessories', type)
        self.do_execute(
            update_sql,
            (
                data['accessories'],
                where_field
            )
        )
        update_sql = self.get_update_sql('acoustooptic_effect', type)
        self.do_execute(
            update_sql,
            (
                data['acoustooptic_effect'],
                where_field
            )
        )
        update_sql = self.get_update_sql('sizes', type)
        self.do_execute(
            update_sql,
            (
                data['sizes'],
                where_field
            )
        )
        update_sql = self.get_update_sql('movable_type', type)
        self.do_execute(
            update_sql,
            (
                data['movable_type'],
                where_field
            )
        )
        update_sql = self.get_update_sql('material', type)
        self.do_execute(
            update_sql,
            (
                data['material'],
                where_field
            )
        )
        update_sql = self.get_update_sql('product_company', type)
        self.do_execute(
            update_sql,
            (
                data['product_company'],
                where_field
            )
        )
        update_sql = self.get_update_sql('contributor_source', type)
        self.do_execute(
            update_sql,
            (
                data['contributor_source'],
                where_field
            )
        )
        update_sql = self.get_update_sql('crawl_date', type)
        self.do_execute(
            update_sql,
            (
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                where_field
            )
        )


    def updata_version_level_data(self, data, where_field, type):
        update_sql = self.get_update_sql('sub_series_id', type)
        self.do_execute(
            update_sql,
            (
                data['sub_series_id'],
                where_field
            )
        )
        update_sql = self.get_update_sql('name', type)
        self.do_execute(
            update_sql,
            (
                data['name'],
                where_field
            )
        )
        update_sql = self.get_update_sql('level_name', type)
        self.do_execute(
            update_sql,
            (
                data['level_name'],
                where_field
            )
        )
        update_sql = self.get_update_sql('url', type)
        self.do_execute(
            update_sql,
            (
                data['url'],
                where_field
            )
        )
        update_sql = self.get_update_sql('crawl_date', type)
        self.do_execute(
            update_sql,
            (
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                where_field
            )
        )


    def updata_img_data(self, data, where_field, type):
        for i, img_path in enumerate(data['paths']):
            update_sql = self.get_update_sql('master_id', type, 1)
            self.do_execute(
                update_sql,
                (
                    data['master_id'],
                    where_field,
                    i
                )
            )
            update_sql = self.get_update_sql('path', type, 1)
            self.do_execute(
                update_sql,
                (
                    img_path,
                    where_field,
                    i
                )
            )
            update_sql = self.get_update_sql('crawl_date', type, 1)
            self.do_execute(
                update_sql,
                (
                    datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    where_field,
                    i
                )
            )


    def updata_sub_data(self, data, where_field, type):
        update_sql = self.get_update_sql('parent_id', type)
        self.do_execute(
            update_sql,
            (
                data['parent_id'],
                where_field
            )
        )
        update_sql = self.get_update_sql('name_cn', type)
        self.do_execute(
            update_sql,
            (
                data['name_cn'],
                where_field
            )
        )
        update_sql = self.get_update_sql('name_en', type)
        self.do_execute(
            update_sql,
            (
                data['name_en'],
                where_field
            )
        )
        update_sql = self.get_update_sql('url', type)
        self.do_execute(
            update_sql,
            (
                data['url'],
                where_field
            )
        )
        update_sql = self.get_update_sql('crawl_date', type)
        self.do_execute(
            update_sql,
            (
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                where_field
            )
        )
        pass


    def updata_parent_data(self, data, where_field, type):
        update_sql = self.get_update_sql('name', type)
        self.do_execute(
            update_sql,
            (
                data['name'],
                where_field
            )
        )
        update_sql = self.get_update_sql('url', type)
        self.do_execute(
            update_sql,
            (
                data['url'],
                where_field
            )
        )
        update_sql = self.get_update_sql('crawl_date', type)
        self.do_execute(
            update_sql,
            (
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                where_field
            )
        )


    def do_execute(self, sql, params):
        result = self.cursor.execute(sql, params)
        self.conn.commit()
        return result


    def get_data_id(self, where_field, type, img_type=0, img_order_num=0):
        data_id = -1
        select_sql = ''
        if type == 'parent':
            select_sql = "select id from parent_series where name = '" + where_field +"'"
        elif type == 'sub':
            select_sql = "select id from sub_series where name_cn = '" + where_field + "'"
        elif type == 'version_level':
            select_sql = "select id from version_level where level_name = '" + where_field + "'"
        elif type == 'other_imgs':
            if img_type != 2:
                select_sql = "select id from other_imgs where master_id = '" + str(where_field) + "' and type= '" + str(img_type) + "'"
            else:
                select_sql = "select id from other_imgs where master_id = '" + str(where_field) + "' and type= '" + str(img_type) + "' and '" + str(img_order_num) + "'"
        elif type == 'toy':
            select_sql = "select id from toy where name = '" + where_field + "'"
        self.cursor.execute(select_sql)
        result = self.cursor.fetchone()
        if result:
            data_id = int(result[0])
        return data_id


    def get_insert_sql(self, type):
        insert_sql = ''
        if type == 'parent':
            insert_sql = """
                insert into parent_series(name, url)
                VALUES (%s, %s)
            """
        elif type == 'sub':
            insert_sql = """
                  insert into sub_series(parent_id, name_cn, name_en, url)
                  VALUES (%s, %s, %s, %s)
              """
        elif type == 'version_level':
            insert_sql = """
                  insert into version_level(sub_series_id, name, level_name, url)
                  VALUES (%s, %s, %s, %s)
              """
        elif type == 'toy':
            insert_sql = """
                insert into toy(verison_level_id, name, head_img, url, limited_mode, release_time, 
                accessories, acoustooptic_effect, sizes, movable_type, material, product_company, 
                contributor_source)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
        elif type == 'other_imgs':
            insert_sql = """
                 insert into other_imgs(master_id, order_num, type, path)
                 VALUES (%s, %s, %s, %s)
             """
        return insert_sql