# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import scrapy
from scrapy.pipelines.images import ImagesPipeline
from scrapy.utils.misc import md5sum
from pymongo import MongoClient
from scrapy.exceptions import DropItem, CloseSpider
import os
import os.path as osp
import platform
from pathlib import Path
import ComicScrapy.settings as myCfg


class MongoPipeline(object):
    """
    MongoDB登録用パイプライン
    """
    # 重複itemを許容する数
    MAX_DUP = 10
    # 重複itemカウント用変数
    duplicate_count = 0

    def open_spider(self, spider):
        self.client = MongoClient('localhost', 27017)
        # scrapy crawl GetComics で init_db 指定の場合
        # DBを初期化する
        if spider.init_db:
            print("----- initialized DB -----")
            self.client.drop_database('ScrapedData')
        self.db = self.client['ScrapedData']
        self.collection = self.db['eromanga_night']

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        comic_key = item['comic_key']
        # image_urlが取得できなかったitemはスキップする。
        image_urls = item['image_urls']
        if len(image_urls) == 0:
            raise DropItem('key:{0} contains no image urls.'.format(comic_key))
        # 既にDB登録されたitemはスキップする。
        # DB登録の有無はcomic_keyを使用して判断
        comicExists = self.collection.find_one({'comic_key': comic_key})
        if comicExists:
            if spider.end_crawl:
                print("----- detected duplicated item -----")
                self.duplicate_count += 1
            if self.duplicate_count >= self.MAX_DUP:
                print("----- end crawling -----")
                spider.stop_crawling()
            raise DropItem('key:{0} is already exists.'.format(comic_key))
        self.collection.insert_one(dict(item))
        return item


class SaveComicPipeline(ImagesPipeline):

    def get_media_requests(self, item, info):
        for image_url in item['image_urls']:
            yield scrapy.Request(image_url, meta={'comic_key': item["comic_key"]})

    def image_downloaded(self, response, request, info):
        checksum = None
        if "eromanga-yoru.com" in request._url:
            save_dir = "eromanga_night"
        else:
            raise DropItem("unknown domain")
        for path, image, buf in self.get_images(response, request, info):
            if checksum is None:
                buf.seek(0)
                checksum = md5sum(buf)
            width, height = image.size
            filename = request._url.rsplit("/", 1)[1]
            path = '{0}/{1}/{2}'.format(save_dir,
                                        response.meta['comic_key'], filename)
            self.store.persist_file(
                path, buf, info,
                meta={'width': width, 'height': height})
        return checksum
