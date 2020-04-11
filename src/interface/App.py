import wx
from pymongo import MongoClient


class MyFrame(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title)
        panel = wx.Panel(self, -1)

        vbox = wx.BoxSizer(wx.VERTICAL)

        btn_ViewComics = wx.Button(panel, -1, 'View Comics')
        vbox.Add(btn_ViewComics, 0, wx.ALL, 10)
        btn_Scraping = wx.Button(panel, -1, 'Scraping')
        vbox.Add(btn_Scraping, 0, wx.ALL, 10)

        panel.SetSizer(vbox)

        btn_ViewComics.Bind(wx.EVT_BUTTON, self.OnClickViewComics)
        btn_Scraping.Bind(wx.EVT_BUTTON, self.OnClickScraping)
        self.Centre()
        self.Show(True)

    def OnClickScraping(self, event):
        print("scraping button")

    def OnClickViewComics(self, event):
        print("view comics button")
        view_frame = ViewFrame(self)


class ViewFrame(wx.Frame):
    """
    Viewモード選択後画面
    """

    def __init__(self, parent):
        wx.Frame.__init__(self, parent, wx.ID_ANY, 'view frame')
        # 画面を最大化
        self.Maximize()
        # DB close処理を関連付け
        self.Bind(wx.EVT_CLOSE, self._close_DB)
        self._open_DB()
        self.collection_panel = CollectionPanel(self, wx.ID_ANY)
        self.search_panel = SearchPanel(self, wx.ID_ANY)
        self.entry_panel = EntryListPanel(self, wx.ID_ANY)

        self.layout = wx.BoxSizer(wx.HORIZONTAL)
        self.layout.Add(self.collection_panel, 2,
                        flag=wx.EXPAND | wx.ALL, border=5)
        self.layout.Add(self.search_panel, 2,
                        flag=wx.EXPAND | wx.ALL, border=5)
        self.layout.Add(self.entry_panel, 3,
                        flag=wx.EXPAND | wx.ALL, border=5)

        self.SetSizer(self.layout)
        self.Centre()
        self.Show(True)

    def click(self, event):
        click = event.GetEventObject()
        print(click)
        click_text = click.GetLabel()
        self.result_text.SetLabel(click_text)

    def _open_DB(self):
        """
        ローカルMongoDBに接続し、ScrapedDataを開く
        """
        self.client = MongoClient('localhost', 27017)
        self.db = self.client['ScrapedData']
        # コレクションのリストをメンバに登録
        self._get_collection_list()

    def select_collection(self, col):
        """
        DBのコレクションを選択
        """
        self.collection = self.db[col]

    def _close_DB(self, event):
        """
        ViewFrameが閉じられた時にDBクローズ
        """
        self.client.close()
        self.Destroy()

    def _get_collection_list(self):
        self.col_list = self.db.list_collection_names()


class EntryListPanel(wx.Panel):
    """
    ViewFrame内
    エントリ一覧を表示するパネル(ウィンドウ右に配置)
    """

    def __init__(self, parent, id):
        super().__init__(parent, id, style=wx.BORDER_SUNKEN)
        self.set_panel_title('Entries')

        self.layout = wx.BoxSizer(wx.VERTICAL)
        self.layout.Add(self.title_text, flag=wx.ALIGN_CENTER)

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


class SearchPanel(wx.Panel):
    """
    ViewFrame内
    エントリー一覧を表示するパネル(ウィンドウ中央に配置)
    """
    category_dict = {
        "eromanga_night": [
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
            "rezu-yuri"
        ]
    }

    def __init__(self, parent, id):
        super().__init__(parent, id, style=wx.BORDER_SUNKEN)

        self.set_panel_title('Search')
        # 共通使用するフォント
        self.font = wx.Font(
            18, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_NORMAL
        )
        # レートを選択する為のlayout作成
        self.set_rate_cmbbtn()

        # カテゴリを選択するlayout作成
        self.set_categories_rdbtn()

        # 検索ボタン
        self.search_bottun = wx.Button(self, wx.ID_ANY, 'SEARCH')

        self.layout = wx.BoxSizer(wx.VERTICAL)
        self.layout.Add(self.title_text, flag=wx.ALIGN_CENTER)
        self.layout.Add(self.rate_layout,
                        flag=wx.ALIGN_CENTER | wx.TOP, border=15)
        self.layout.Add(self.category_rdbox,
                        flag=wx.ALIGN_CENTER | wx.TOP, border=15)
        self.layout.Add(self.search_bottun,
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

    def set_rate_cmbbtn(self):
        """
        レート検索用のコンボボックスを設定
        """
        self.rate_layout = wx.BoxSizer(wx.HORIZONTAL)
        # テキスト
        rate_text = wx.StaticText(self, wx.ID_ANY, 'Rate')
        rate_text.SetFont(self.font)
        # レート選択コンボボックス
        elements = ['unrated', '1', '2', '3', '4', '5']
        rate_cmbbox = wx.ComboBox(self, wx.ID_ANY, 'choose',
                                  choices=elements, style=wx.CB_READONLY)
        # 比較演算子選択コンボボックス
        operators = ['', '==', '>=', '<=']
        operator_cmbbox = wx.ComboBox(self, wx.ID_ANY, 'choose',
                                      choices=operators, style=wx.CB_READONLY)

        # TODO: 'unrated'選択時に比較演算子コンボボックスを無効にする

        self.rate_layout.Add(rate_text, flag=wx.RIGHT, border=30)
        self.rate_layout.Add(operator_cmbbox, flag=wx.RIGHT, border=5)
        self.rate_layout.Add(rate_cmbbox, flag=wx.RIGHT, border=5)

    def set_categories_rdbtn(self):
        """
        カテゴリ選択のラジオボタンを設定
        """
        # CollectionPanelで設定したコレクションからカテゴリを特定
        selected = self.GetParent().collection_panel.get_selected_col()
        categories = self.category_dict[selected]
        self.category_rdbox = wx.RadioBox(
            self, wx.ID_ANY, 'categories', choices=categories,
            style=wx.RA_VERTICAL
        )
        self.category_rdbox.SetFont(self.font)


class CollectionPanel(wx.Panel):
    """
    ViewFrame内
    コレクション一覧を表示するパネル(ウィンドウ左に配置)
    """

    def __init__(self, parent, id):
        super().__init__(parent, id, style=wx.BORDER_SUNKEN)

        self.set_panel_title('Collections')
        self.set_radio_buttons()

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

    def set_radio_buttons(self):
        """
        DB内のコレクション数だけラジオボタン追加
        """
        font = wx.Font(
            18, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_NORMAL
        )
        self.radio_box = wx.RadioBox(
            self, wx.ID_ANY, '', choices=self.GetParent().col_list,
            style=wx.RA_VERTICAL
        )
        self.radio_box.SetFont(font)

    def get_selected_col(self):
        """
        ラジオボタンで選択されているコレクションを返す
        """
        return self.radio_box.GetStringSelection()


if __name__ == "__main__":
    app = wx.App()
    MyFrame(None, -1, 'moveevent.py')
    app.MainLoop()
