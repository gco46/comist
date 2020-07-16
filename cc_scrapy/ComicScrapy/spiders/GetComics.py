# -*- coding: utf-8 -*-
import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.exceptions import CloseSpider
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
    base_url = "https://eromanga-yoru.com/front"
    category_list = [
        "eromanga-night",
        "gyaru",
        "hinnyu",
        "jingai-kemono",
        "jk-jc",
        "jyukujyo-hitozuma",
        "kinshinsoukan",
        "kosupure",
        "kyonyu-binyu",
        "netorare-netori",
        "ol-sister",
        "onesyota",
        "rape",
        "rezu-yuri",
        "front"                 # 最新のエントリから取得
    ]
    # リクエストヘッダ情報
    headers = {
        # "Cache-Control": "max-age=0",
        # "Connection": "keep-alive",
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/80.0.3987.132 Safari/537.36"),
        # "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    }

    def __init__(self, category="", test_crawl=0,
                 init_db=0, end_crawl=0, *args, **kwargs):
        """
        scrapy crawl GetComics 引数
        category: str, カンマ区切りでカテゴリを指定
        test_crawl: int, クロールの機能確認実施フラグ
                         trueの場合、自動で init_db=true となる
        init_db: int, DBの初期化フラグ
        end_crawl: int, 既にDB登録済みのアイテムを取得した際にcrawlを停止する
        """
        super(GetComicsSpider, self).__init__(*args, **kwargs)
        # 引数はstr型となるため、キャストしてメンバ代入
        self.test_crawl = int(test_crawl)
        self.init_db = int(init_db)
        self.end_crawl = int(end_crawl)
        # スクレイピング停止フラグ
        self.end_flag = False

        # 機能確認では指定のエントリーのみクロールする
        if self.test_crawl:
            self.start_urls.append(
                urllib.parse.urljoin(self.base_url, "eromanga-night/68563")
            )
            self.start_urls.append(
                urllib.parse.urljoin(self.base_url, "kinshinsoukan/1992")
            )
            return
        # category引数指定があった場合はリスト化
        if category:
            category = category.split(",")
        else:
            category = []
        # category 引数チェック
        for c in category:
            cat = c.strip()
            if cat not in self.category_list:
                raise ValueError(cat + " is not in category list.")
            if cat == "front":
                self.start_urls.append(self.base_url)
            else:
                self.start_urls.append(
                    urllib.parse.urljoin(self.base_url, "category/" + cat)
                )

    def parse(self, response):
        """
        一覧ページのリクエストを投げる
        """
        # 機能確認時処理(デバッグ用) -------------------
        # 特定エントリーのみリクエスト
        if self.test_crawl:
            yield scrapy.Request(response.url,
                                 callback=self.entry_parse,
                                 headers=self.headers)
        # --------------------------------------------

        # スクレイピング処理停止判定
        self.close_spider_check()

        # 通常時処理 ----------------------------------
        # 詳細ページリクエストのループ
        for entry_url in response.css(Css.to_detail_page).extract():
            yield scrapy.Request(entry_url,
                                 callback=self.entry_parse,
                                 headers=self.headers)

        # 一覧ページに次のページがある場合、リクエストを投げる
        next_link = response.css(Css.to_next_page).extract_first()
        if next_link is None:
            return
        else:
            yield scrapy.Request(next_link,
                                 callback=self.parse,
                                 headers=self.headers)

    def entry_parse(self, response):
        """
        詳細ページからitem情報を取得
        """
        # スクレイピング処理停止判定
        self.close_spider_check()
        # TODO: 空ページの例外処理追加
        item = ComicImageItem()
        item['comic_key'] = self._get_commic_key(response)
        item['entry_url'] = self._get_entry_url(response)
        item['author'], item['title'] = self._get_author_and_title(response)
        item['image_urls'] = self._get_image_urls(response)
        item['num_images'] = len(item['image_urls'])
        item['tags'] = self._get_tags(response)
        item['category'] = self._get_category(response)
        item['continuous_work'] = self._get_continuous_work(response)
        # 初期レートに'unrated'を登録する
        item['rate'] = 'unrated'
        return item

    def stop_crawling(self):
        """
        スクレイピング停止フラグをTrueにする
        (spider側からraiseする必要があるため,フラグで分岐して停止処理をコールする)
        """
        self.end_flag = True

    def close_spider_check(self):
        """
        スクレイピング停止判定、停止処理
        """
        if self.end_flag:
            raise CloseSpider('duplicated item is detected, end crawling')

    def _get_commic_key(self, response):
        """
        itemに追加する漫画の識別子をURLから取得する
        input: response object
        output: str, like 'category/comic_id'
        """
        dir_name = response.url.split("/")[-2:]
        comic_key = "/".join(dir_name)
        return comic_key

    def _get_entry_url(self, response):
        """
        itemに追加する漫画詳細ページのurlを取得する
        """
        return response.url

    def _get_author_and_title(self, response):
        """
        itemに追加するタイトル、作者名を見出しから取得する
        input: response object
        output: list, like [author, title]
        """
        # extract_first()で最初にマッチした要素を取得
        caption = response.css(Css.to_caption).extract_first()
        author_title = re.search(Ptn.author_title, caption).group(0)
        # 全角のコロンを半角へ置換
        author_title = author_title.replace("：", ":")
        # 【(作者):(タイトル)】の文字列から作者とタイトルを抽出
        # 【】を除く文字列を抜き出し、:(コロン)を区切り文字として抽出
        if author_title.count(":") == 1:
            author_title = author_title[1:-1].split(":")
        else:
            # 作品名または作者名にコロンが含まれている場合はどちらか判断できないので、
            # 作品名にコロンが含まれているものとしてタイトル、作者を取得する
            tmp = author_title[1:-1].split(":")
            author_title = [tmp[0], tmp[1] + ":" + tmp[2]]
        return author_title

    def _get_image_urls(self, response):
        """
        itemに追加する漫画画像のurlを取得する
        input: response object
        output: list, it contains urls(str) of comic images
        """
        image_urls = []
        for url in response.css(Css.to_images).extract():
            image_urls.append(url)
        return image_urls

    def _get_tags(self, response):
        """
        itemに追加するタグ情報を取得する
        input: response object
        output: list, contains tags(str)
        """
        tags = response.css(Css.to_tags).extract()
        # ページ上部と下部で二重にtag情報が取得されるため、半分だけitemに追加
        tags = tags[len(tags)//2:]
        return tags

    def _get_category(self, response):
        """
        itemに追加するカテゴリを取得する
        input: response object
        output: str, category (in japanese)
        """
        return response.css(Css.to_category).extract_first()

    def _get_continuous_work(self, response):
        """
        itemに追加する連作情報を取得する
        """
        # ページ上部と下部で二重に連作情報が取得されるため、半分だけitemに追加
        cont_list = response.css(Css.to_continuous).extract()
        cont_list = cont_list[len(cont_list) // 2:]
        # リダイレクトしたURLを取得するために一度リクエストを送り、
        # 返ってきたURLを連作情報として返す
        for idx in range(len(cont_list)):
            response_redirect = requests.get(cont_list[idx])
            cont_list[idx] = response_redirect.url
        return cont_list
