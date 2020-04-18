import wx
import sys
from pathlib import Path
import subprocess


class CrawlFrame(wx.Frame):
    def __init__(self, parent):
        super().__init__(parent, wx.ID_ANY, 'crawl frame')
        # 画面を最大化
        self.Maximize()

        self.target_website = TargetWebPanel(self)
        self.target_category = CrawlOptionPanel(self)

        # 標準出力表示用のテキストボックス追加
        style = wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL
        self.log = wx.TextCtrl(self, wx.ID_ANY, style=style)

        self.layout = wx.BoxSizer(wx.HORIZONTAL)
        self.layout.Add(self.target_website, proportion=2,
                        flag=wx.EXPAND | wx.ALL, border=5)
        self.layout.Add(self.target_category, proportion=2,
                        flag=wx.EXPAND | wx.ALL, border=5)
        self.layout.Add(self.log, proportion=3,
                        flag=wx.EXPAND | wx.ALL, border=5)

        self.SetSizer(self.layout)
        sys.stdout = self.log
        self.Centre()
        self.Show(True)


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
        self.start_crawl_btn = wx.Button(self, wx.ID_ANY, 'START')
        self.start_crawl_btn.Bind(wx.EVT_BUTTON, self.click_start_crawl)

        self.layout = wx.BoxSizer(wx.VERTICAL)
        self.layout.Add(self.title_text, flag=wx.ALIGN_CENTER)
        self.layout.Add(self.category_chkbox,
                        flag=wx.ALIGN_CENTER | wx.TOP, border=15)
        self.layout.Add(self.option_layout,
                        flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=40)
        self.layout.Add(self.start_crawl_btn,
                        flag=wx.ALIGN_RIGHT)

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
        selected = self.GetParent().target_website.get_selected_col()

        categories = self.category_dict[selected].keys()
        categories = list(categories)
        self.category_chkbox = wx.CheckListBox(
            self, wx.ID_ANY, name='categories', choices=categories,
            style=wx.RA_VERTICAL, size=(300, 400)
        )
        self.category_chkbox.SetFont(self.font)

    def click_start_crawl(self, event):
        """
        クロール開始ボタン
        """
        dialog = wx.MessageDialog(
            None, 'start crawling?',
            style=wx.YES_NO
        )
        res = dialog.ShowModal()
        if res == wx.ID_YES:
            print("------------------------")
            print("---- start crawling ----")
            print("------------------------")
            print("")
            self.crawl_command()
        elif res == wx.ID_NO:
            pass

        dialog.Destroy()

    def crawl_command(self):
        """
        クロールコマンド実行処理
        """
        selected = self.category_chkbox.GetCheckedStrings()
        category = ",".join(selected)
        # scrapyに渡すコマンドを作成
        cat_cmd = " -a category=" + category
        init_cmd = self.confirm_initialization()
        end_cmd = self.confirm_early_terminate()
        # DB初期化確認にてキャンセルされた場合、クロールを中止する
        if init_cmd is None:
            return
        if len(selected) == 0:
            print("no categories are checked")
            return

        cmd = "scrapy crawl GetComics" + cat_cmd + init_cmd + end_cmd
        for line in self.get_lines(cmd):
            print(line, end="")
        print("------------------------")
        print("----- end crawling -----")
        print("------------------------")
        print("")

    def confirm_initialization(self):
        """
        DB初期化の確認
        キャンセルした場合はクロール中止(Noneを返す)
        """
        if self.init_DB_chkbox.IsChecked():
            dialog = wx.MessageDialog(
                None, 'Initialize Database?',
                style=wx.YES_NO | wx.ICON_INFORMATION
            )
            res = dialog.ShowModal()
            if res == wx.ID_NO:
                print("canceled crawling")
                return
            elif res == wx.ID_YES:
                return " -a init_db=1"
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

    def get_lines(self, cmd):
        """
        コマンド実行後、標準出力を一行ずつ取得
        """
        self.proc = subprocess.Popen(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        while True:
            line = self.proc.stdout.readline()
            if line:
                try:
                    line = line.decode('utf-8')
                except UnicodeDecodeError:
                    continue
                yield line

            if not line and self.proc.poll() is not None:
                break
