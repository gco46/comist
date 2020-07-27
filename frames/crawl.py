import wx
import sys
from pathlib import Path
from pymongo import MongoClient
import subprocess
from threading import Thread
import os
import frames.const as c_


class CrawlFrame(wx.Frame):
    def __init__(self, parent):
        super().__init__(parent, wx.ID_ANY, 'crawl frame')
        # 画面を最大化
        self.Maximize()
        # crawl状態フラグ
        self.now_crawling = False
        # DB open
        self._open_DB()

        # CLOSEイベント
        self.Bind(wx.EVT_CLOSE, self.close_frame)

        self.target_web_panel = TargetWebPanel(self)
        self.option_panel = CrawlOptionPanel(self)

        # 標準出力表示用のテキストボックス追加
        style = wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL
        self.log = wx.TextCtrl(self, wx.ID_ANY, style=style)

        self.layout = wx.BoxSizer(wx.HORIZONTAL)
        self.layout.Add(self.target_web_panel, proportion=2,
                        flag=wx.EXPAND | wx.ALL, border=5)
        self.layout.Add(self.option_panel, proportion=2,
                        flag=wx.EXPAND | wx.ALL, border=5)
        self.layout.Add(self.log, proportion=3,
                        flag=wx.EXPAND | wx.ALL, border=5)

        self.SetSizer(self.layout)
        sys.stdout = self.log
        self.Centre()
        self.Show(True)

    def _open_DB(self):
        """
        ローカルMongoDBに接続し、ScrapedDataを開く
        """
        self.client = MongoClient('localhost', 27017)
        self.db = self.client['ScrapedData']

    def _close_DB(self):
        """
        DBクローズ
        """
        self.client.close()

    def close_frame(self, event):
        """
        ウィンドウ閉じる処理
        TODO: crawl中はframeを閉じられないようにする
              (スレッド処理が生き残るため)
        """
        btn_label = self.option_panel.crawl_stop_button.GetLabel()
        # crawling中ならば, 先にSTOPするようにダイアログで表示する
        if self.now_crawling:
            dialog = wx.MessageDialog(
                None,
                'If you want to quit, please press the stop button first.',
                style=wx.OK
            )
            dialog.ShowModal()
        else:
            self._close_DB()
            self.Destroy()


class TargetWebPanel(wx.Panel):
    """
    クロール対象のwebsiteを選択するパネル
    """

    weblist = [
        "eromanga_night"
    ]

    def __init__(self, parent):
        super().__init__(parent, wx.ID_ANY)
        self.set_panel_title('Target Website')
        self.init_radio_buttons()

        self.layout = wx.BoxSizer(wx.VERTICAL)
        self.layout.Add(self.title_text, flag=wx.ALIGN_CENTER)
        self.layout.Add(self.radio_box, flag=wx.ALIGN_CENTER)

        self.SetSizer(self.layout)

    def set_panel_title(self, title):
        """
        パネル上部のタイトル設定
        """
        self.title_text = wx.StaticText(
            self, wx.ID_ANY, title, style=wx.TE_CENTER
        )
        font_Title = wx.Font(
            24, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_NORMAL
        )
        self.title_text.SetFont(font_Title)

    def init_radio_buttons(self):
        """
        DB内のコレクション数だけラジオボタン追加
        """
        font = wx.Font(
            18, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_NORMAL
        )
        self.radio_box = wx.RadioBox(
            self, wx.ID_ANY, '', choices=self.weblist,
            style=wx.RA_VERTICAL
        )
        self.radio_box.SetFont(font)

    def get_selected_col(self):
        """
        ラジオボタンで選択されているコレクションを返す
        """
        return self.radio_box.GetStringSelection()


class CrawlOptionPanel(wx.Panel):
    """
    クロール時のオプションを指定するパネル
    """
    category_dict = {
        "eromanga_night": {
            "eromanga-night": "エロ漫画の夜",
            "gyaru": "ギャル",
            "hinnyu": "貧乳",
            "jingai-kemono": "人外・獣",
            "jk-jc": "JK・JC",
            "jyukujyo-hitozuma": "熟女・人妻",
            "kinshinsoukan": "近親相姦",
            "kosupure": "コスプレ",
            "kyonyu-binyu": "巨乳・美乳",
            "netorare-netori": "寝取られ・寝取り",
            "ol-sister": "OL・お姉さん",
            "onesyota": "おねショタ",
            "rape": "レイプ",
            "rezu-yuri": "レズ・百合",
        }
    }
    image_path = c_.COMIC_PATH

    def __init__(self, parent):
        super().__init__(parent, wx.ID_ANY)
        self.set_panel_title('Target Category')
        # 共通使用するフォント
        self.font = wx.Font(
            18, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_NORMAL
        )

        # カテゴリを選択するlayout作成
        self.set_categories_chkbox()

        # オプションチェックボックス
        self.set_option_chkbox()

        # クロール開始ボタン
        self.crawl_start_button = wx.Button(self, wx.ID_ANY, 'START')
        self.crawl_start_button.Bind(wx.EVT_BUTTON, self.click_start_button)
        # クロール停止ボタン
        # クロール中のみ有効のためボタン無効化
        self.crawl_stop_button = wx.Button(self, wx.ID_ANY, 'STOP')
        self.crawl_stop_button.Bind(wx.EVT_BUTTON, self.click_stop_button)
        self.crawl_stop_button.Disable()
        # クロール完了通知と後処理の紐付け
        self.Bind(c_.EVT_CRAWL_CMP, self.crawl_postprocess)

        self.layout = wx.BoxSizer(wx.VERTICAL)
        self.layout.Add(self.title_text, flag=wx.ALIGN_CENTER)
        self.layout.Add(self.category_chkbox,
                        flag=wx.ALIGN_CENTER | wx.TOP, border=15)
        self.layout.Add(self.option_layout,
                        flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=40)
        self.layout.Add(self.crawl_start_button, flag=wx.ALIGN_RIGHT)
        self.layout.Add(self.crawl_stop_button, flag=wx.ALIGN_RIGHT)

        self.SetSizer(self.layout)

    def set_panel_title(self, title):
        """
        パネル上部のタイトル設定
        """
        self.title_text = wx.StaticText(
            self, wx.ID_ANY, title, style=wx.TE_CENTER
        )
        font_Title = wx.Font(
            24, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_NORMAL
        )
        self.title_text.SetFont(font_Title)

    def set_option_chkbox(self):
        """
        オプション選択のチェックボックス設定
        """
        self.init_DB_chkbox = wx.CheckBox(
            self, wx.ID_ANY, "Initialize DB",
        )
        font = wx.Font(
            16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_NORMAL
        )
        self.end_crawl_chkbox = wx.CheckBox(
            self, wx.ID_ANY, "Early termination"
        )
        self.init_DB_chkbox.SetFont(font)
        self.end_crawl_chkbox.SetFont(font)
        self.option_layout = wx.BoxSizer(wx.VERTICAL)
        self.option_layout.Add(
            self.init_DB_chkbox, flag=wx.ALIGN_CENTER | wx.BOTTOM, border=10
        )
        self.option_layout.Add(
            self.end_crawl_chkbox, flag=wx.ALIGN_CENTER
        )

    def set_categories_chkbox(self):
        """
        対象のカテゴリを設定
        """
        selected = self.GetParent().target_web_panel.get_selected_col()

        categories = self.category_dict[selected].keys()
        categories = list(categories)
        self.category_chkbox = wx.CheckListBox(
            self, wx.ID_ANY, name='categories', choices=categories,
            style=wx.RA_VERTICAL, size=(300, 400)
        )
        self.category_chkbox.SetFont(self.font)

    def click_start_button(self, event):
        """
        クロール開始ボタン
        """
        dialog = wx.MessageDialog(
            None, 'start crawling?',
            style=wx.YES_NO
        )
        res = dialog.ShowModal()
        if res == wx.ID_YES:
            if self.confirm_selected_categories() is None:
                # カテゴリ未選択によりクロール中止
                return
            elif self.confirm_initialization() is None:
                # 初期化キャンセルによりクロール中止
                return
            else:
                # クロール開始前処理
                self.GetParent().now_crawling = True
                self.crawl_start_button.Disable()
                self.crawl_stop_button.Enable()
                # threadに渡す引数準備
                selected_cat = self.category_chkbox.GetCheckedStrings()
                init_db = self.init_DB_chkbox.IsChecked()
                early_term = self.end_crawl_chkbox.IsChecked()
                # クロール処理開始
                self.scrape = ScrapeThread(
                    selected_cat, init_db, early_term, self
                )

        elif res == wx.ID_NO:
            # 処理なし
            return

    def click_stop_button(self, event):
        """
        クロール停止ボタン
        """
        dialog = wx.MessageDialog(
            None,
            'cancel crawling?',
            style=wx.YES_NO
        )
        res = dialog.ShowModal()
        if res == wx.ID_YES:
            # クロール停止処理
            # 予期せぬ操作を防止するため、先にクロール停止ボタンを無効化
            self.crawl_stop_button.Disable()
            print("------ canceling -------")
            self.scrape.stop()
            self.scrape.join()      # thread処理停止まで待機
            print("------ canceled -------")

            # クロール停止完了後処理
            # DL中断されたアイテムはDBから削除する
            self.crawl_start_button.Enable()
            self.remove_canceled_item_from_DB()
            self.GetParent().now_crawling = False

            # TODO: 余力があればストレージからも削除

    def crawl_postprocess(self, event):
        """
        クロール完了後処理
        フラグ管理とボタンの有効・無効化
        """
        self.GetParent().now_crawling = False
        self.crawl_start_button.Enable()
        self.crawl_stop_button.Disable()

    def remove_canceled_item_from_DB(self):
        """
        ダウンロードを中断したアイテムをDBから削除する
        """
        # DB open
        col = self.GetParent().target_web_panel.radio_box.GetStringSelection()
        # 最後にダウンロードされたitemを取得
        # 日付順でソートした結果の先頭のみ取得
        latest_item = self.GetParent().db[col].find().sort([
            {"_id", -1}]).limit(1)
        try:
            # アイテムはdict型であるため、listでキャスト後要素を取り出す
            latest_item = list(latest_item)[0]
        except IndexError:
            # DBにアイテムがない場合は何もせず終了
            return
        # ストレージに保存された画像の枚数を確認
        comic_path = self.image_path / latest_item["comic_key"]
        num_dl_images = len(list(comic_path.glob("*")))
        if latest_item["num_images"] != num_dl_images:
            # 最新アイテムがDL途中で中断された場合、DBから削除
            self.GetParent().db[col].remove(
                {"comic_key": latest_item["comic_key"]})

    def confirm_selected_categories(self):
        """
        カテゴリ選択の確認
        一つも選択されていない場合はクロール中止(Noneを返す)
        """
        if len(self.category_chkbox.GetCheckedStrings()) == 0:
            print("No categories are selected")
            return
        else:
            return True

    def confirm_initialization(self):
        """
        DB初期化の確認
        キャンセルした場合はクロール中止(Noneを返す)
        """
        if self.init_DB_chkbox.IsChecked():
            dialog = wx.MessageDialog(
                None, 'Initialize Database?',
                style=wx.YES_NO
            )
            res = dialog.ShowModal()
            if res == wx.ID_NO:
                print("canceled crawling")
                return
            elif res == wx.ID_YES:
                return True
        else:
            return ""

    def confirm_early_terminate(self):
        """
        クロールの早期終了の確認
        """
        if self.end_crawl_chkbox.IsChecked():
            return " -a end_crawl=1"
        else:
            return ""


class ScrapeThread(Thread):
    """
    Scraping thread
    """

    def __init__(self, selected_cat, init_db, early_terminate, option_panel):
        Thread.__init__(self)
        self.want_stop = False
        # 取得対象カテゴリ(リスト)
        self.category = ",".join(selected_cat)
        # DB初期化フラグ
        self.init_db = init_db
        # 早期終了フラグ(取得済みアイテムヒット時)
        self.early_terminate = early_terminate
        # 呼び出し元のcrawl frame
        self.option_panel = option_panel
        self.start()

    def run(self):
        """
        thread実行
        """
        wx.CallAfter(print, "------------------------")
        wx.CallAfter(print, "---- start crawling ----")
        wx.CallAfter(print, "------------------------")
        wx.CallAfter(print, "")

        self.execute_crawling()

        wx.CallAfter(print, "------------------------")
        wx.CallAfter(print, "----- end crawling -----")
        wx.CallAfter(print, "------------------------")
        wx.CallAfter(print, "")

    def stop(self):
        """
        thread停止要求
        """
        self.want_stop = True

    def stopped(self):
        """
        thread停止要求取得
        """
        return self.want_stop

    def execute_crawling(self):
        """
        クロール開始
        """
        # scrapyに渡すコマンドを作成
        cat_cmd = " -a category=" + self.category

        # DB初期化コマンド
        if self.init_db:
            init_cmd = " -a init_db=1"
        else:
            init_cmd = ""

        # 早期終了コマンド
        if self.early_terminate:
            term_cmd = " -a end_crawl=1"
        else:
            term_cmd = ""

        cmd = "scrapy crawl GetComics" + cat_cmd + init_cmd + term_cmd
        for line in self.get_subprocess_output(cmd):
            if self.stopped():
                # スクレイピング中断処理
                self.proc.kill()
                return
            wx.CallAfter(print, line, end="")

        # クロール完了通知をcrawl option panelに送る
        evt = c_.CrawlCompletedEvt()
        wx.PostEvent(self.option_panel, evt)

    def get_subprocess_output(self, cmd):
        """
        スクレイピングサブプロセスを実行
        """
        # 非同期処理でスクレイピングを実行
        # TODO: Windows用の中断処理追加
        if os.name == "posix":          # UNIX系処理
            # cmdまでkillできるようにするためにexecをつけて実行する
            self.proc = subprocess.Popen(
                "exec " + cmd, cwd="cc_scrapy/",
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                shell=True)
        elif os.name == "nt":           # windows処理
            self.proc = subprocess.Popen(
                cmd, cwd="cc_scrapy/",
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        else:
            raise ValueError
        # 標準出力を一行ずつ取得し、リアルタイム表示するためにループを回す
        while True:
            line = self.proc.stdout.readline()
            if line:
                try:
                    line = line.decode('utf-8')
                except UnicodeDecodeError:
                    continue
                yield line

            # 出力がなくなり、サブプロセス処理が完了したらbreak
            if not line and self.proc.poll() is not None:
                break
