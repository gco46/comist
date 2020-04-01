# -*- coding: utf-8 -*-
import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from ComicScrapy.items import ComicImageItem
import urllib
from pymongo import MongoClient
import requests
import re
from ComicScrapy.site_data import CssSelectors as Css
from ComicScrapy.site_data import REpattern as Ptn


class GetComicsSpider(scrapy.Spider):
    name = 'GetComics'
    allowed_domains = ['eromanga-yoru.com']
    start_urls = []
    base_url = "https://eromanga-yoru.com/"
    # リクエストヘッダ情報
    # headers = {
    #     "Cache-Control": "max-age=0",
    #     "Connection": "keep-alive",
    #     "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    #                    "AppleWebKit/537.36 (KHTML, like Gecko) "
    #                    "Chrome/80.0.3987.132 Safari/537.36"),
    #     "Accept-Encoding": "gzip, deflate, br",
    #     "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    # }

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
        """
        一覧ページのリクエストを投げる
        """
        # 詳細ページリクエストのループ
        for entry_url in response.css(Css.to_detail_page).extract():
            yield scrapy.Request(entry_url,
                                 callback=self.entry_parse)
        # 一覧ページに次のページがある場合、リクエストを投げる
        next_link = response.css(Css.to_next_page).extract_first()
        if next_link is None:
            return
        yield scrapy.Request(next_link,
                             callback=self.parse)

    def entry_parse(self, response):
        """
        詳細ページからitem情報を取得
        """
        item = ComicImageItem()
        # category/comic_key をURLから取得してディレクトリに使用
        dir_name = response.url.split("/")[-2:]
        item['comic_key'] = "/".join(dir_name)
        item['entry_url'] = response.url
        # タイトル, 作者名を見出しから取得し、itemに追加
        caption = response.css(Css.to_caption).extract()[0]
        author_title = re.search(Ptn.author_title, caption).group(0)
        # 【(作者):(タイトル)】の文字列から作者とタイトルを抽出
        author_title = author_title[1:-1].split(":")
        item['author'] = author_title[0]
        item['title'] = author_title[1]
        # css selectorで画像を指定してitemに追加
        item['image_urls'] = []
        for img_url in response.css(Css.to_images).extract():
            item['image_urls'].append(img_url)
        item['num_images'] = len(item['image_urls'])
        # tag情報取得
        # ページ上部と下部で二重にtag情報が取得されるため、半分だけitemに追加
        tags = response.css(Css.to_tags).extract()
        item['tags'] = tags[len(tags)//2:]
        # category取得
        item['category'] = response.css(Css.to_category).extract_first()
        # 連作の情報取得
        # ページ上部と下部で二重にtag情報が取得されるため、半分だけitemに追加
        cont_list = response.css(Css.to_continuous).extract()
        cont_list = cont_list[len(cont_list) // 2:]
        # リダイレクトしたURLを取得するために一度リクエストを送り、
        # 返ってきたURLを連作情報としてitemに追加
        for idx in range(len(cont_list)):
            response = requests.get(cont_list[idx])
            cont_list[idx] = response.url
        item['continuous_work'] = cont_list
        return item
