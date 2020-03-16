# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import scrapy
from scrapy.pipelines.images import ImagesPipeline
from scrapy.utils.misc import md5sum
from pymongo import MongoClient
from scrapy.exceptions import DropItem
import os
import os.path as osp
import ComicScrapy.settings as myCfg


class MongoPipeline(object):
    def open_spider(self, spider):
        self.client = MongoClient('localhost', 27017)
        self.db = self.client['ScrapedData']
        self.collection = self.db['eromanga-night']

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        comic_key = item['comic_key']
        comicExists = self.collection.find_one({'comic_key': comic_key})
        if comicExists:
            raise DropItem('key:{0} is already exists.'.format(comic_key))
        self.collection.insert_one(dict(item))
        return item


class SymboliclinkPipeline(object):
    # データ保存先
    DataPath = 'project/ComicCluster/data'
    AbsDataPath = osp.join(osp.expanduser('~'), DataPath)
    ComicDir = myCfg.IMAGES_STORE.split("/")[-1]
    # シンボリックリンク名(次の作品)
    NextSym = "next"
    # シンボリックリンク名(前の作品)
    PreviousSym = "privious"

    def process_item(self, item, spider):
        # 連作ではない場合、処理を終了する
        if not item['continuous_work']:
            return item
        cont_list = item['continuous_work']
        entry_url = item['entry_url']

        # 次の作品のみある場合
        if cont_list.index(entry_url) == 0:
            next_entry_url = cont_list[cont_list.index(entry_url) + 1]
            self.make_symlink(next_entry_url, entry_url, self.NextSym)
        # 前の作品のみある場合
        elif cont_list.index(entry_url) + 1 == len(cont_list):
            previous_entry_url = cont_list[cont_list.index(entry_url) - 1]
            self.make_symlink(previous_entry_url, entry_url, self.PreviousSym)
        # 次の作品、前の作品がある場合
        else:
            previous_entry_url = cont_list[cont_list.index(entry_url) - 1]
            next_entry_url = cont_list[cont_list.index(entry_url) + 1]
            self.make_symlink(next_entry_url, entry_url, self.NextSym)
            self.make_symlink(previous_entry_url, entry_url, self.PreviousSym)
        return item

    def make_symlink(self, target_url, base_url, link_name):
        tgt_cat, tgt_id = target_url.split("/")[-2:]
        base_cat, base_id = base_url.split("/")[-2:]
        sym_src = osp.join(
            self.AbsDataPath, self.ComicDir, tgt_cat, tgt_id
        )
        sym_name = osp.join(
            self.ComicDir, base_cat, base_id, link_name
        )
        os.symlink(sym_src, sym_name)


class SaveComicPipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        for image_url in item['image_urls']:
            yield scrapy.Request(image_url, meta={'comic_key': item["comic_key"]})

    def image_downloaded(self, response, request, info):
        checksum = None
        for path, image, buf in self.get_images(response, request, info):
            if checksum is None:
                buf.seek(0)
                checksum = md5sum(buf)
            width, height = image.size
            filename = request._url.rsplit("/", 1)[1]
            path = '{0}/{1}'.format(response.meta['comic_key'], filename)
            self.store.persist_file(
                path, buf, info,
                meta={'width': width, 'height': height})
        return checksum
