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
    image_path = Path('../../data/Comics')
    no_image_path = image_path / 'no_image.png'
    img_w = 180
    img_h = 260

    def __init__(self, parent, id):
        super().__init__(parent, id, style=wx.BORDER_SUNKEN)
        self.set_panel_title('Entries')
        self.init_search_layout()
        self.init_thumbnails()
        self.init_paging_button()

        self.layout = wx.BoxSizer(wx.VERTICAL)
        self.layout.Add(self.title_text, flag=wx.ALIGN_CENTER)
        self.layout.Add(
            self.search_layout,
            flag=wx.ALIGN_CENTER | wx.BOTTOM,
            border=20
        )
        self.layout.Add(self.thumbnails, flag=wx.ALIGN_CENTER)
        self.layout.Add(self.btn_layout, flag=wx.ALIGN_CENTER)
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
            self, wx.ID_ANY, "", style=wx.TE_CENTER
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
            self, wx.ID_ANY, "", style=wx.TE_CENTER
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
        img_path = self.no_image_path
        font = wx.Font(
            16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_NORMAL
        )
        self.img_obj_list = []
        self.title_obj_list = []
        for i in range(self.n_item_per_page):
            img_title = wx.BoxSizer(wx.VERTICAL)
            title = wx.StaticText(
                self, wx.ID_ANY, 'title' + str(i), style=wx.TE_CENTER
            )
            title.SetFont(font)
            img = wx.Image(str(img_path))
            img = img.Scale(self.img_w, self.img_h, wx.IMAGE_QUALITY_HIGH)
            bitmap = img.ConvertToBitmap()
            comic_img = wx.StaticBitmap(
                self, wx.ID_ANY, bitmap, size=bitmap.GetSize()
            )
            img_title.Add(
                comic_img,
                flag=wx.ALIGN_CENTER)
            img_title.Add(title, flag=wx.ALIGN_LEFT | wx.BOTTOM, border=10)
            self.thumbnails.Add(
                img_title,
                flag=wx.ALIGN_CENTER | wx.RIGHT | wx.LEFT,
                border=10)
            self.img_obj_list.append(comic_img)
            self.title_obj_list.append(title)

    def init_paging_button(self):
        """
        ページングボタンとページングに使用する変数を初期化
        """
        # エントリリストのページング用インデックスを初期化する
        self.e_list_idx = 0
        # 各ボタンを初期化、配置する
        self.next_button = wx.Button(self, wx.ID_ANY, '次へ')
        self.next_button.Bind(wx.EVT_BUTTON, self.click_next_button)
        self.previous_button = wx.Button(self, wx.ID_ANY, '前へ')
        self.previous_button.Bind(wx.EVT_BUTTON, self.click_previous_button)
        # DB検索されるまでボタンは無効化する
        self.next_button.Disable()
        self.previous_button.Disable()

        self.btn_layout = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_layout.Add(
            self.previous_button,
            flag=wx.ALIGN_CENTER | wx.RIGHT | wx.LEFT,
            border=10
        )
        self.btn_layout.Add(
            self.next_button,
            flag=wx.ALIGN_CENTER | wx.RIGHT | wx.LEFT,
            border=10
        )

    def set_query_text(self, rate_q, ope_q):
        """
        クエリのレート・比較演算子をパネルに反映
        """
        self.operator.SetLabel(ope_q)
        self.selected_rate.SetLabel(rate_q)

    def enable_entry_paging(self):
        """
        エントリリストのページングを有効化する
        """
        # ボタン有効化
        self.next_button.Enable()
        self.previous_button.Enable()
        # インデックスを初期化
        self.idx_max = len(self.s_result) // self.n_item_per_page - 1
        self.idx_min = 0

    def click_next_button(self, event):
        if self.e_list_idx == self.idx_max:
            return
        self.e_list_idx += 1
        self.update_thumbnail_and_title(self.e_list_idx)

    def click_previous_button(self, event):
        if self.e_list_idx == self.idx_min:
            return
        self.e_list_idx -= 1
        self.update_thumbnail_and_title(self.e_list_idx)

    def update_entry_list(self, search_result):
        """
        検索結果からサムネイル情報を更新
        """
        # 検索結果をリスト化
        # No imageで描画用に、エントリの端数は空文字を入れる
        self.s_result = list(search_result)
        tmp = -(-len(self.s_result) // self.n_item_per_page) * \
            self.n_item_per_page
        self.s_result += [""] * (tmp - len(self.s_result))
        # TODO: EntryPanel上部のRate, Categoryのテキストを更新
        # エントリリストの0ページ目を描画
        self.update_thumbnail_and_title(0)
        # entry panelのページング処理を有効化
        self.GetParent().entry_panel.enable_entry_paging()

    def update_thumbnail_and_title(self, idx):
        for i in range(self.n_item_per_page):
            # タイトル設定処理
            try:
                title = self.s_result[idx * self.n_item_per_page + i]["title"]
            except TypeError:
                # 端数のエントリはno image, titleにする
                img = wx.Image(str(self.no_image_path))
                img = img.Scale(self.img_w, self.img_h, wx.IMAGE_QUALITY_HIGH)
                bitmap = img.ConvertToBitmap()
                self.title_obj_list[i].SetLabel("title" + str(i))
                self.img_obj_list[i].SetBitmap(bitmap)
                continue
            # 10文字以上のタイトルは省略
            if len(title) > 9:
                title = title[:8] + "..."
            self.title_obj_list[i].SetLabel(title)

            # サムネイル設定処理
            comic_key = self.s_result[idx *
                                      self.n_item_per_page + i]["comic_key"]
            comic_path = self.image_path / comic_key
            # jpgがなければpngで試す、それでもなければスキップ
            img_pathes = list(comic_path.glob("*.jpg"))
            if len(img_pathes) == 0:
                img_pathes = list(comic_path.glob("*.png"))
                if len(img_pathes) == 0:
                    continue
            # 先頭ページをサムネイル用画像に選択
            tmp_img = wx.Image(str(img_pathes[0]))
            tmp_img = tmp_img.Scale(
                self.img_w, self.img_h, wx.IMAGE_QUALITY_HIGH)
            thumbnail = tmp_img.ConvertToBitmap()
            self.img_obj_list[i].SetBitmap(thumbnail)


class SearchPanel(wx.Panel):
    """
    ViewFrame内
    エントリー一覧を表示するパネル(ウィンドウ中央に配置)
    """
    # TODO: サーチパネルに表示するカテゴリを日本語化する
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
            "ALL": "全て"
        }

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
        self.search_button = wx.Button(self, wx.ID_ANY, 'SEARCH')
        self.search_button.Bind(wx.EVT_BUTTON, self.click_search)

        self.layout = wx.BoxSizer(wx.VERTICAL)
        self.layout.Add(self.title_text, flag=wx.ALIGN_CENTER)
        self.layout.Add(self.rate_layout,
                        flag=wx.ALIGN_CENTER | wx.TOP, border=15)
        self.layout.Add(self.category_rdbox,
                        flag=wx.ALIGN_CENTER | wx.TOP, border=15)
        self.layout.Add(self.search_button,
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
        self.rate_cmbbox = wx.ComboBox(self, wx.ID_ANY, 'choose',
                                       choices=elements, style=wx.CB_READONLY)
        # 比較演算子選択コンボボックス
        operators = ['', '==', '>=', '<=']
        self.operator_cmbbox = wx.ComboBox(
            self, wx.ID_ANY, 'choose', choices=operators, style=wx.CB_READONLY
        )

        # TODO: 'unrated'選択時に比較演算子コンボボックスを無効にする(優先度低)

        self.rate_layout.Add(rate_text, flag=wx.RIGHT, border=30)
        self.rate_layout.Add(self.operator_cmbbox, flag=wx.RIGHT, border=5)
        self.rate_layout.Add(self.rate_cmbbox, flag=wx.RIGHT, border=5)

    def set_categories_rdbtn(self):
        """
        カテゴリ選択のラジオボタンを設定
        """
        # CollectionPanelで設定したコレクションからカテゴリを特定
        selected = self.GetParent().collection_panel.get_selected_col()
        # カテゴリ一覧からキーのリスト取得
        categories = self.category_dict[selected].keys()
        categories = list(categories)
        self.category_rdbox = wx.RadioBox(
            self, wx.ID_ANY, 'categories', choices=categories,
            style=wx.RA_VERTICAL
        )
        self.category_rdbox.SetFont(self.font)

    def click_search(self, event):
        # コンボボックス、ラジオボタンの選択状態を取得
        rate_q = self.rate_cmbbox.GetStringSelection()
        operator_q = self.operator_cmbbox.GetStringSelection()
        category_q = self.category_rdbox.GetStringSelection()
        # 取得した選択状態からでクエリ作成、DB検索
        query = self.make_query(rate_q, operator_q, category_q)
        # rateが選択されていない場合は終了
        if query is None:
            return
        search_result = self.DB_search(query)
        # 検索結果が0件の場合は終了
        if len(search_result) == 0:
            return
        # EntryListPanelのメソッドを呼び出して検索結果を渡す
        self.GetParent().entry_panel.update_entry_list(search_result)

    def make_query(self, rate, operator, category):
        query = []
        if category != "ALL":
            selected = self.GetParent().collection_panel.get_selected_col()
            c_dict = self.category_dict[selected]
            query.append({"category": c_dict[category]})
        if rate == "":
            return
        elif rate == "unrated":
            query.append({'rate': rate})
        else:
            rate = int(rate)
            if operator == ">=":
                query.append({"rate": {"$gte": rate}})
            elif operator == "<=":
                query.append({"rate": {"$lte": rate}})
            else:
                query.append({"rate": rate})
        return {"$and": query}

    def DB_search(self, query):
        selected = self.GetParent().collection_panel.get_selected_col()
        col = self.GetParent().db[selected]
        result = col.find(query)
        return list(result)


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
