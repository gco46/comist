import wx
from pymongo import MongoClient
from frames.comic_view import ComicViewFrame
from pathlib import Path
import frames.const as c_
from wx import Window, StaticBitmap, StaticText, BoxSizer, Button, Image

from typing import List, Dict


class ViewFrame(wx.Frame):
    """
    Viewモード選択後画面
    """

    def __init__(self, parent: Window):
        wx.Frame.__init__(self, parent, wx.ID_ANY, 'view frame')
        # 画面を最大化
        self.Maximize()
        # DB close処理を関連付け
        self.Bind(wx.EVT_CLOSE, self._close_DB)
        self._open_DB()
        if len(self.col_list) == 0:
            # 未スクレイピングの場合は終了
            # TODO: my collection機能追加
            dialog = wx.MessageDialog(
                None, 'There are no collections. Scraping first.',
                style=wx.OK
            )
            dialog.ShowModal()
            self.Destroy()
            return
        self.collection_panel = CollectionPanel(self, wx.ID_ANY)
        self.search_panel = SearchPanel(self, wx.ID_ANY)
        self.entry_panel = EntryListPanel(self, wx.ID_ANY)

        self.layout: BoxSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.layout.Add(self.collection_panel, 2,
                        flag=wx.EXPAND | wx.ALL, border=5)
        self.layout.Add(self.search_panel, 2,
                        flag=wx.EXPAND | wx.ALL, border=5)
        self.layout.Add(self.entry_panel, 3,
                        flag=wx.EXPAND | wx.ALL, border=5)

        self.SetSizer(self.layout)
        self.Centre()
        self.Show(True)

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

    grid_row: int = 3
    grid_col: int = 4
    n_item_per_page: int = grid_row * grid_col
    image_path: Path = c_.COMIC_PATH
    no_image_path: Path = c_.NO_IMAGE_PATH
    img_w: int = c_.SUMB_WIDTH
    img_h: int = c_.SUMB_HEIGHT
    hdlr: str = "self.click_comic_"

    def __init__(self, parent: Window, id: int):
        super().__init__(parent, id, style=wx.BORDER_SUNKEN)
        self._init_panel()
        self._draw_panel()

    def _init_panel(self):
        """
        パネル初期化
        """
        # 変数初期化
        self._init_attributes()
        # Ctrl objectを初期化して配置
        self._init_panel_title()
        self._init_search_layout()
        self._init_thumbnails()
        self._init_paging_button()
        self._init_page_num()

    def _init_panel_title(self):
        """
        パネル上部のタイトル設定
        """
        self.title_text: StaticText = wx.StaticText(
            self, wx.ID_ANY, 'Entries', style=wx.TE_CENTER
        )
        font_Title = wx.Font(
            24, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_NORMAL
        )
        self.title_text.SetFont(font_Title)

    def _init_attributes(self):
        """
        ページングに使用するメンバ変数を初期化する
        """
        # エントリリストのページング用インデックス
        self.e_list_idx: int = 0
        # DB検索結果格納用リスト
        # 1ページのエントリ数の空文字要素で初期化
        self.s_result: List[c_.ComicDocs] = [None] * self.n_item_per_page
        # 選択中のtarget site(暫定で設定)
        self.target_site: str = "eromanga_night"

    def _init_rate_layout(self):
        """
        検索対象のレート表示部を初期化
        """
        font = wx.Font(
            18, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_NORMAL
        )
        rate_text = wx.StaticText(
            self, wx.ID_ANY, "Rate : ", style=wx.TE_CENTER
        )
        rate_text.SetFont(font)

        self.rate_layout: BoxSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.rate_layout.Add(rate_text, flag=wx.ALIGN_CENTER)

    def _init_category_layout(self):
        """
        検索対象のカテゴリ表示部を初期化
        """
        font = wx.Font(
            18, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_NORMAL
        )
        category_text = wx.StaticText(
            self, wx.ID_ANY, "Category : ", style=wx.TE_CENTER
        )
        category_text.SetFont(font)
        self.selected_category: StaticText = wx.StaticText(
            self, wx.ID_ANY, "", style=wx.TE_CENTER
        )
        self.selected_category.SetFont(font)
        self.category_layout: BoxSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.category_layout.Add(category_text, flag=wx.ALIGN_CENTER)
        self.category_layout.Add(self.selected_category, flag=wx.ALIGN_CENTER)

    def _init_search_layout(self):
        """
        panel上部の検索クエリ文字列を初期化
        """
        # search_layoutはパネル上部のレート, カテゴリ表示も含むため
        # 先にrate_layout, category_layoutを初期化する
        self._init_rate_layout()
        self._init_category_layout()

        self.search_layout: BoxSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.search_layout.Add(
            self.rate_layout,
            flag=wx.ALIGN_CENTER | wx.RIGHT | wx.LEFT,
            border=60
        )
        self.search_layout.Add(
            self.category_layout,
            flag=wx.ALIGN_CENTER | wx.RIGHT | wx.LEFT,
            border=60
        )

    def _init_thumbnails(self):
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
        self.img_obj_list: List[StaticBitmap] = []
        self.title_obj_list: List[StaticText] = []
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
            # サムネイル、タイトルにハンドラを関連付け
            comic_img.Bind(wx.EVT_LEFT_DOWN, eval(self.hdlr + str(i)))
            title.Bind(wx.EVT_LEFT_DOWN, eval(self.hdlr + str(i)))

    def _init_paging_button(self):
        """
        ページングボタンを初期化
        """
        # 各ボタンを初期化、配置する
        self.next_button: Button = wx.Button(self, wx.ID_ANY, '次へ')
        self.next_button.Bind(wx.EVT_BUTTON, self.click_next_button)
        self.previous_button: Button = wx.Button(self, wx.ID_ANY, '前へ')
        self.previous_button.Bind(wx.EVT_BUTTON, self.click_previous_button)
        # DB検索されるまでボタンは無効化する
        self.next_button.Disable()
        self.previous_button.Disable()

        self.btn_layout: BoxSizer = wx.BoxSizer(wx.HORIZONTAL)
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

    def _init_page_num(self):
        """
        エントリリストのページ数を初期化
        """
        self.n_page_layout: BoxSizer = wx.BoxSizer(wx.HORIZONTAL)
        # page数　分子
        self.p_numerator: StaticText = wx.StaticText(
            self, wx.ID_ANY, '', style=wx.TE_CENTER
        )
        slash = wx.StaticText(
            self, wx.ID_ANY, '/', style=wx.TE_CENTER
        )
        # page数　分母
        self.p_denominator: StaticText = wx.StaticText(
            self, wx.ID_ANY, '', style=wx.TE_CENTER
        )
        # 桁数が増えるとずれるため、分子側のみ余白を多めに取る
        self.n_page_layout.Add(
            self.p_numerator, flag=wx.ALIGN_LEFT | wx.RIGHT, border=25
        )
        self.n_page_layout.Add(
            slash, flag=wx.ALIGN_CENTER | wx.RIGHT, border=8)
        self.n_page_layout.Add(
            self.p_denominator, flag=wx.ALIGN_CENTER | wx.RIGHT, border=8
        )

    def _draw_panel(self):
        """
        レイアウトの描画
        """
        # 初期化した各レイアウトを
        # 最上位のレイアウトに入れて描画
        self.layout: BoxSizer = wx.BoxSizer(wx.VERTICAL)
        self.layout.Add(self.title_text, flag=wx.ALIGN_CENTER)
        self.layout.Add(
            self.search_layout,
            flag=wx.ALIGN_CENTER | wx.BOTTOM,
            border=20
        )
        self.layout.Add(self.thumbnails, flag=wx.ALIGN_CENTER)
        self.layout.Add(self.btn_layout, flag=wx.ALIGN_CENTER)
        self.layout.Add(self.n_page_layout,
                        flag=wx.ALIGN_CENTER | wx.TOP, border=5)
        self.SetSizer(self.layout)

    def _update_entry_paging(self, idx: int):
        """
        エントリリストのページングを有効化・更新する
        """
        # ボタン有効化
        self.next_button.Enable()
        self.previous_button.Enable()
        # インデックスを更新
        self.e_list_idx = idx
        self.idx_max: int = len(self.s_result) // self.n_item_per_page - 1
        self.idx_min: int = 0
        # エントリリストのページ数を設定
        self.p_numerator.SetLabel(str(self.e_list_idx + 1))
        self.p_denominator.SetLabel(str(self.idx_max + 1))

    def click_next_button(self, event):
        if self.e_list_idx == self.idx_max:
            return
        self.e_list_idx += 1
        # ページ数更新
        self.p_numerator.SetLabel(str(self.e_list_idx + 1))
        # サムネイル、タイトル更新
        self._update_thumbnail_and_title(self.e_list_idx)

    def click_previous_button(self, event):
        if self.e_list_idx == self.idx_min:
            return
        self.e_list_idx -= 1
        # ページ数更新
        self.p_numerator.SetLabel(str(self.e_list_idx + 1))
        # サムネイル、タイトル更新
        self._update_thumbnail_and_title(self.e_list_idx)

    def click_comic_0(self, event):
        entry = self.s_result[self.e_list_idx * self.n_item_per_page + 0]
        # 空のエントリを選択した場合は何もしない
        if entry is None:
            return
        ComicViewFrame(self, entry, self.target_site)

    def click_comic_1(self, event):
        entry = self.s_result[self.e_list_idx * self.n_item_per_page + 1]
        # 空のエントリを選択した場合は何もしない
        if entry is None:
            return
        ComicViewFrame(self, entry, self.target_site)

    def click_comic_2(self, event):
        entry = self.s_result[self.e_list_idx * self.n_item_per_page + 2]
        # 空のエントリを選択した場合は何もしない
        if entry is None:
            return
        ComicViewFrame(self, entry, self.target_site)

    def click_comic_3(self, event):
        entry = self.s_result[self.e_list_idx * self.n_item_per_page + 3]
        # 空のエントリを選択した場合は何もしない
        if entry is None:
            return
        ComicViewFrame(self, entry, self.target_site)

    def click_comic_4(self, event):
        entry = self.s_result[self.e_list_idx * self.n_item_per_page + 4]
        # 空のエントリを選択した場合は何もしない
        if entry is None:
            return
        ComicViewFrame(self, entry, self.target_site)

    def click_comic_5(self, event):
        entry = self.s_result[self.e_list_idx * self.n_item_per_page + 5]
        # 空のエントリを選択した場合は何もしない
        if entry is None:
            return
        ComicViewFrame(self, entry, self.target_site)

    def click_comic_6(self, event):
        entry = self.s_result[self.e_list_idx * self.n_item_per_page + 6]
        # 空のエントリを選択した場合は何もしない
        if entry is None:
            return
        ComicViewFrame(self, entry, self.target_site)

    def click_comic_7(self, event):
        entry = self.s_result[self.e_list_idx * self.n_item_per_page + 7]
        # 空のエントリを選択した場合は何もしない
        if entry is None:
            return
        ComicViewFrame(self, entry, self.target_site)

    def click_comic_8(self, event):
        entry = self.s_result[self.e_list_idx * self.n_item_per_page + 8]
        # 空のエントリを選択した場合は何もしない
        if entry is None:
            return
        ComicViewFrame(self, entry, self.target_site)

    def click_comic_9(self, event):
        entry = self.s_result[self.e_list_idx * self.n_item_per_page + 9]
        # 空のエントリを選択した場合は何もしない
        if entry is None:
            return
        ComicViewFrame(self, entry, self.target_site)

    def click_comic_10(self, event):
        entry = self.s_result[self.e_list_idx * self.n_item_per_page + 10]
        # 空のエントリを選択した場合は何もしない
        if entry is None:
            return
        ComicViewFrame(self, entry, self.target_site)

    def click_comic_11(self, event):
        entry = self.s_result[self.e_list_idx * self.n_item_per_page + 11]
        # 空のエントリを選択した場合は何もしない
        if entry is None:
            return
        ComicViewFrame(self, entry, self.target_site)

    def update_entry_list(self, search_result: List[c_.ComicDoc], page: int = 0):
        """
        検索結果からサムネイル情報を更新
        """
        # 検索結果を更新
        self.s_result = search_result
        # No imageで描画用に、エントリの端数は空文字を入れる
        tmp = -(-len(self.s_result) // self.n_item_per_page) * \
            self.n_item_per_page
        self.s_result += [None] * (tmp - len(self.s_result))
        # エントリリストの指定ページを描画
        self._update_thumbnail_and_title(page)
        # entry panelのページング処理を有効化
        self._update_entry_paging(page)

    def update_query_text(self, operator: str, rate: str, category: str):
        """
        パネル上部のクエリ情報を更新
        """
        # レート, 比較演算子を反映
        rate_text = self.rate_layout.GetChildren()[0]
        rate_text = rate_text.GetWindow()
        rate_text.SetLabel("Rate : " + operator + rate)
        # カテゴリ表示を反映
        cat_text = self.category_layout.GetChildren()[1]
        cat_text = cat_text.GetWindow()
        cat_text.SetLabel(category)

    def _update_thumbnail_and_title(self, idx: int):
        """
        漫画のサムネイルとタイトルを更新する
        空白の欄は'no image'を使用する
        """
        for i in range(self.n_item_per_page):
            # タイトル設定処理
            try:
                title = self.s_result[idx * self.n_item_per_page + i]["title"]
            except (TypeError, IndexError):
                # 端数のエントリはno imageにする(TypeError)
                # 検索結果0件の場合はすべてno imageにする(IndexError)
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
            # target siteの取得
            target_site = self.GetParent().collection_panel.radio_box.GetStringSelection()
            # 漫画の保存パス作成
            comic_path = self.image_path / target_site / comic_key

            # ファイル数が0ならばスキップ
            tmp = list(comic_path.glob("*"))
            if len(tmp) == 0:
                continue
            else:
                # ファイルがあれば拡張子を取得
                tmp_path = tmp[0]
                suffix = tmp_path.suffix

            img_pathes = list(comic_path.glob("*" + suffix))
            # 画像をソートし、先頭ページをサムネイルに使用する
            img_pathes.sort()
            # 先頭ページをサムネイル用画像に選択
            tmp_img = wx.Image(str(img_pathes[0]))
            tmp_img = tmp_img.Scale(
                self.img_w, self.img_h, wx.IMAGE_QUALITY_HIGH)
            thumbnail = tmp_img.ConvertToBitmap()
            self.img_obj_list[i].SetBitmap(thumbnail)

    def set_choosed_target_site(self, target_site):
        self.target_site = target_site


class SearchPanel(wx.Panel):
    """
    ViewFrame内
    エントリー一覧を表示するパネル(ウィンドウ中央に配置)
    """
    category_dict = {
        "eromanga_night": [
            "エロ漫画の夜",
            "ギャル",
            "貧乳",
            "人外・獣",
            "JK・JC",
            "熟女・人妻",
            "近親相姦",
            "コスプレ",
            "巨乳・美乳",
            "寝取られ・寝取り",
            "OL・お姉さん",
            "おねショタ",
            "レイプ",
            "レズ・百合",
            "ALL"
        ]
    }
    # eromanga_night コレクション　全カテゴリ指定時のインデックス
    COL1_ALL_CAT_INDEX = 14

    def __init__(self, parent, id):
        super().__init__(parent, id, style=wx.BORDER_SUNKEN)

        self.init_panel_title('Search')
        # 共通使用するフォント
        self.font = wx.Font(
            18, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_NORMAL
        )
        # レートを選択する為のlayout作成
        self.init_rate_cmbbtn()

        # カテゴリを選択するlayout作成
        self.init_categories_rdbtn()

        # フリーワード検索のlayout作成
        self.init_freeword_box()

        # 検索ボタン
        self.search_button = wx.Button(self, wx.ID_ANY, 'SEARCH')
        self.search_button.Bind(wx.EVT_BUTTON, self.click_search)

        self.layout = wx.BoxSizer(wx.VERTICAL)
        self.layout.Add(self.title_text, flag=wx.EXPAND | wx.BOTTOM, border=15)
        self.layout.Add(self.rate_layout,
                        flag=wx.EXPAND | wx.LEFT, border=150)
        self.layout.Add(self.category_rdbox,
                        flag=wx.EXPAND | wx.RIGHT | wx.LEFT, border=50)
        self.layout.Add(self.freeword_layout,
                        flag=wx.EXPAND | wx.RIGHT | wx.LEFT | wx.TOP, border=30)
        self.layout.Add(self.search_button,
                        flag=wx.ALIGN_RIGHT | wx.TOP, border=30)

        self.SetSizer(self.layout)

    def init_panel_title(self, title):
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

    def init_rate_cmbbtn(self):
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
        # 'unrated'を選択
        self.rate_cmbbox.SetSelection(0)

        # 比較演算子選択コンボボックス
        operators = ['', '>=', '<=']
        self.operator_cmbbox = wx.ComboBox(
            self, wx.ID_ANY, 'choose', choices=operators, style=wx.CB_READONLY
        )

        # 'unrated'選択時に比較演算子コンボボックスを空にする
        self.rate_cmbbox.Bind(wx.EVT_COMBOBOX, self.reset_operator_cmbbox)

        self.rate_layout.Add(rate_text, flag=wx.RIGHT, border=30)
        self.rate_layout.Add(self.operator_cmbbox, flag=wx.RIGHT, border=5)
        self.rate_layout.Add(self.rate_cmbbox, flag=wx.RIGHT, border=5)

    def init_categories_rdbtn(self):
        """
        カテゴリ選択のラジオボタンを設定
        """
        # CollectionPanelで設定したコレクションからカテゴリを特定
        selected = self.GetParent().collection_panel.get_selected_col()
        # カテゴリ一覧からキーのリスト取得
        categories = self.category_dict[selected]
        categories = list(categories)
        self.category_rdbox = wx.RadioBox(
            self, wx.ID_ANY, 'categories', choices=categories,
            style=wx.RA_VERTICAL
        )
        self.category_rdbox.SetFont(self.font)

    def init_freeword_box(self):
        self.freeword_layout = wx.BoxSizer(wx.VERTICAL)

        freeword_text = wx.StaticText(
            self, wx.ID_ANY, "free word:")
        font = wx.Font(
            13, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_NORMAL
        )
        freeword_text.SetFont(font)
        self.freeword_box = wx.TextCtrl(self, wx.ID_ANY)

        self.freeword_layout.Add(freeword_text)
        self.freeword_layout.Add(self.freeword_box, flag=wx.EXPAND)

    def reset_operator_cmbbox(self, event):
        """
        レートのコンボボックスにunratedが選択された時、比較演算子をクリア
        """
        selected_rate = self.rate_cmbbox.GetStringSelection()
        # unratedが選択された時は比較演算子を空にする
        if selected_rate == "unrated":
            self.operator_cmbbox.SetStringSelection('')

    def click_search(self, event):
        # コンボボックス、ラジオボタンの選択状態を取得
        rate_q: str = self.rate_cmbbox.GetStringSelection()
        operator_q: str = self.operator_cmbbox.GetStringSelection()
        # カテゴリのクエリを取得
        category_q_idx: int = self.category_rdbox.GetSelection()
        selected: str = self.GetParent().collection_panel.get_selected_col()
        category_q: str = self.category_dict[selected][category_q_idx]
        # フリーワードのクエリを取得
        freeword_q: str = self.freeword_box.GetValue()

        # 取得した選択状態からクエリ作成、DB検索
        self.query: Dict = self._make_query(
            rate_q, operator_q, category_q, freeword_q)
        # rateが選択されていない場合は終了
        if self.query is None:
            return
        search_result: List[c_.ComicDoc] = self.DB_search(self.query)
        # 検索結果が0件の場合はダイアログを表示して終了
        if len(search_result) == 0:
            dialog = wx.MessageDialog(
                None, 'There are 0 results.',
                style=wx.OK
            )
            dialog.ShowModal()
            dialog.Destroy()
            return
        # EntryListPanelの検索クエリを更新
        self.GetParent().entry_panel.update_query_text(operator_q, rate_q, category_q)
        # EntryListPanelのエントリー一覧を更新
        self.GetParent().entry_panel.update_entry_list(search_result)

    def _make_query(self,
                    rate: str, operator: str, category: str, freeword: str):
        """
        Mongo DBに投げる検索クエリを作成する
        """
        query = []
        query += self._make_category_query(category)
        query += self._make_rate_query(rate, operator)
        query += self._make_freeword_query(freeword)
        return {"$and": query}

    def _make_category_query(self, category: str) -> List[Dict]:
        query = []
        if category != "ALL":
            query.append({"category": category})
        return query

    def _make_rate_query(self, rate: str, operator: str) -> List[Dict]:
        query: List = []
        if rate == "":
            return query
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
        return query

    def _make_freeword_query(self, freeword: str) -> List[Dict]:
        """
        フリーワード検索のクエリ作成
        tags, title, authorでOR検索する
        複数単語を指定した場合は、OR検索の結果をAND検索する
        """
        if freeword == "":
            return []
        # 全角スペースを半角スペースに置換
        freewords = freeword.replace("　", " ")
        word_l = freewords.split()
        freeword_q = []
        for word in word_l:
            tags_q = {"tags": {"$regex": word}}
            title_q = {"title": {"$regex": word}}
            author_q = {"author": {"$regex": word}}
            freeword_q.append({"$or": [tags_q, title_q, author_q]})

        return [{"$and": freeword_q}]

    def DB_search(self, query: c_.ComicDoc) -> List[c_.ComicDoc]:
        col = self.GetParent().collection
        result = col.find(query)
        return list(result)


class CollectionPanel(wx.Panel):
    """
    ViewFrame内
    コレクション一覧を表示するパネル(ウィンドウ左に配置)
    """

    def __init__(self, parent, id):
        super().__init__(parent, id, style=wx.BORDER_SUNKEN)
        self._init_panel()
        self._draw_panel()

        self.SetSizer(self.layout)

    def _init_panel(self):
        """
        パネル初期化
        """
        self._init_panel_title()
        self._init_radio_buttons()
        self._init_selected_col()

    def _init_panel_title(self):
        """
        パネル上部のタイトル設定
        """
        self.title_text = wx.StaticText(
            self, wx.ID_ANY, 'Collections', style=wx.TE_CENTER
        )
        font_Title = wx.Font(
            24, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_NORMAL
        )
        self.title_text.SetFont(font_Title)

    def _init_radio_buttons(self):
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

    def _init_selected_col(self):
        """
        初期選択collectionをDBで開く (eromanga_night)
        """
        self.GetParent().select_collection("eromanga_night")

    def _draw_panel(self):
        self.layout = wx.BoxSizer(wx.VERTICAL)
        self.layout.Add(self.title_text, flag=wx.ALIGN_CENTER)
        self.layout.Add(self.radio_box, flag=wx.ALIGN_CENTER)

    def get_selected_col(self):
        """
        ラジオボタンで選択されているコレクションを返す
        """
        return self.radio_box.GetStringSelection()

    def click_rd_box(self, event):
        target_site = self.radio_box.GetStringSelection()
        self.GetParent().entry_panel.set_choosed_target_site(target_site)
