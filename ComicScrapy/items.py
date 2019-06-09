# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class ComicImageItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    comic_key = scrapy.Field()
    entry_url = scrapy.Field()
    image_urls = scrapy.Field()
    continuous_work = scrapy.Field()
    num_images = scrapy.Field()
    tags = scrapy.Field()
    category = scrapy.Field()
