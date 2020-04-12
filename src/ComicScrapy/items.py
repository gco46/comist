# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class ComicImageItem(scrapy.Item):
    comic_key = scrapy.Field()          # 漫画の識別子(カテゴリ/URL末尾6桁)
    entry_url = scrapy.Field()          # 漫画エントリのURL
    title = scrapy.Field()              # 漫画タイトル
    author = scrapy.Field()             # 作者名
    image_urls = scrapy.Field()         # 保存する漫画画像のURL
    continuous_work = scrapy.Field()    # 連作のリンク(シンボリックリンク用)
    num_images = scrapy.Field()         # 漫画のページ数
    tags = scrapy.Field()               # 漫画が持つtag情報
    category = scrapy.Field()           # カテゴリ(日本語)
    rate = scrapy.Field()               # レート
