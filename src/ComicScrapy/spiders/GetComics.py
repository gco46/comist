# -*- coding: utf-8 -*-
import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from ComicScrapy.items import ComicImageItem
import urllib
from pymongo import MongoClient
import requests
from ComicScrapy.site_data import CssSelectors as Css


class GetComicsSpider(scrapy.Spider):
    name = 'GetComics'
    allowed_domains = ['eromanga-yoru.com']
    start_urls = []
    base_url = "http://eromanga-yoru.com/main/category/"

    def __init__(self, category="", *args, **kwargs):
        super(GetComicsSpider, self).__init__(*args, **kwargs)
        category = category.split(",")
        # category 引数チェック
        for c in category:
            self.start_urls.append(
                urllib.parse.urljoin(self.base_url, c.strip()))
        if len(self.start_urls) == 0:
            raise ValueError

    def parse(self, response):
        for entry_url in response.css(Css.to_detail_page).extract():
            yield scrapy.Request(entry_url, callback=self.entry_parse)
        next_link = response.css(Css.to_next_page).extract_first()
        if next_link is None:
            return
        yield scrapy.Request(next_link, callback=self.parse)

    def entry_parse(self, response):
        item = ComicImageItem()
        dir_name = response.url.split("/")[-2:]
        item['comic_key'] = "/".join(dir_name)
        item['entry_url'] = response.url
        item['image_urls'] = []
        for img_url in response.css(Css.to_images).extract():
            item['image_urls'].append(img_url)
        item['num_images'] = len(item['image_urls'])
        tags = response.css(Css.to_tags).extract()
        item['tags'] = tags[len(tags)//2:]
        item['category'] = response.css(Css.to_category).extract_first()
        cont_list = response.css(Css.to_continuous).extract()
        cont_list = cont_list[len(cont_list) // 2:]
        for idx in range(len(cont_list)):
            response = requests.get(cont_list[idx])
            cont_list[idx] = response.url
        item['continuous_work'] = cont_list
        return item
