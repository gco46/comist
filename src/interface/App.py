import wx
from pymongo import MongoClient
from pathlib import Path


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
        print("close")
        self.client.close()
        self.Destroy()

    def _get_collection_list(self):
        self.col_list = self.db.list_collection_names()


class EntryListPanel(wx.Panel):
    """
    ViewFrame内
    エントリ一覧を表示するパネル(ウィンドウ右に配置)
    """

    grid_row = 3
    grid_col = 4
    n_item_per_page = grid_row * grid_col
    no_image_path = '../../data/Comics/no_image.png'

    def __init__(self, parent, id):
        super().__init__(parent, id, style=wx.BORDER_SUNKEN)
        self.set_panel_title('Entries')
        self.init_search_layout()
        self.init_thumbnails()

        self.layout = wx.BoxSizer(wx.VERTICAL)
        self.layout.Add(self.title_text, flag=wx.ALIGN_CENTER)
        self.layout.Add(
            self.search_layout,
            flag=wx.ALIGN_CENTER | wx.BOTTOM,
            border=20
        )
        self.layout.Add(self.thumbnails, flag=wx.ALIGN_CENTER)

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

    def init_rate_layout(self):
        font = wx.Font(
            18, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_NORMAL
        )
        rate_text = wx.StaticText(
            self, wx.ID_ANY, "Rate : ", style=wx.TE_CENTER
        )
        rate_text.SetFont(font)
        self.operator = wx.StaticText(
            self, wx.ID_ANY, "", style=wx.TE_CENTER
        )
        self.operator.SetFont(font)
        self.selected_rate = wx.StaticText(
            self, wx.ID_ANY, "unrated", style=wx.TE_CENTER
        )
        self.selected_rate.SetFont(font)

        self.rate_layout = wx.BoxSizer(wx.HORIZONTAL)
        self.rate_layout.Add(rate_text, flag=wx.ALIGN_CENTER)
        self.rate_layout.Add(self.operator, flag=wx.ALIGN_CENTER)
        self.rate_layout.Add(self.selected_rate, flag=wx.ALIGN_CENTER)

    def init_category_layout(self):
        font = wx.Font(
            18, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_NORMAL
        )
        category_text = wx.StaticText(
            self, wx.ID_ANY, "Category : ", style=wx.TE_CENTER
        )
        category_text.SetFont(font)
        self.selected_category = wx.StaticText(
            self, wx.ID_ANY, "jyukujo-hitozuma", style=wx.TE_CENTER
        )
        self.selected_category.SetFont(font)
        self.category_layout = wx.BoxSizer(wx.HORIZONTAL)
        self.category_layout.Add(category_text, flag=wx.ALIGN_CENTER)
        self.category_layout.Add(self.selected_category, flag=wx.ALIGN_CENTER)

    def init_search_layout(self):
        """
        panel上部の検索クエリ文字列を初期化
        """
        self.init_rate_layout()
        self.init_category_layout()
        self.search_layout = wx.BoxSizer(wx.HORIZONTAL)
        self.search_layout.Add(
            self.rate_layout,
            flag=wx.ALIGN_CENTER | wx.RIGHT | wx.LEFT,
            border=30
        )
        self.search_layout.Add(
            self.category_layout,
            flag=wx.ALIGN_CENTER | wx.RIGHT | wx.LEFT,
            border=30
        )

    def init_thumbnails(self):
        """
        サムネイル用GridSizerを初期化
        """
        self.thumbnails = wx.GridSizer(
            rows=self.grid_row, cols=self.grid_col, gap=(0, 0))
        img_path = Path(self.no_image_path)
        font = wx.Font(
            16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_NORMAL
        )
        for i in range(self.n_item_per_page):
            img_title = wx.BoxSizer(wx.VERTICAL)
            title = wx.StaticText(
                self, wx.ID_ANY, 'title' + str(i), style=wx.TE_CENTER
            )
            title.SetFont(font)
            img = wx.Image(str(img_path))
            img = img.Scale(180, 260, wx.IMAGE_QUALITY_HIGH)
            bitmap = img.ConvertToBitmap()
            comic_img = wx.StaticBitmap(
                self, wx.ID_ANY, bitmap, size=bitmap.GetSize()
            )
            img_title.Add(
                comic_img,
                flag=wx.ALIGN_CENTER | wx.RIGHT | wx.LEFT,
                border=10)
            img_title.Add(title, flag=wx.ALIGN_CENTER | wx.BOTTOM, border=10)
            self.thumbnails.Add(img_title)


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
