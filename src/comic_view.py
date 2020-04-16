import wx
from pymongo import MongoClient
from pathlib import Path


class ComicViewFrame(wx.Frame):
    """
    漫画選択後Frame
    """
    image_path = Path('../data/Comics')

    def __init__(self, parent, entry_info):
        super().__init__(parent, wx.ID_ANY)
        self.Maximize()
        self.entry_info = entry_info

        # パネル上部の漫画情報を更新
        self.init_info_text()

        # レート登録用ラジオボタン追加
        self.init_rate_rdbtn()

        # 連作のnext/previous ボタン追加
        self.init_cont_work_btn()

        # ページ送りボタン
        self.init_paging_button()

        self.init_comic_img()

        # 左側に操作パネル、右側に画像を配置
        # 要調整
        self.layout = wx.BoxSizer(wx.HORIZONTAL)
        left_layout = wx.BoxSizer(wx.VERTICAL)
        left_layout.Add(self.info_layout, flag=wx.ALIGN_CENTER | wx.EXPAND)
        left_layout.Add(self.radio_box, flag=wx.ALIGN_CENTER |
                        wx.TOP | wx.BOTTOM, border=20)
        left_layout.Add(self.cont_layout, flag=wx.ALIGN_CENTER |
                        wx.TOP | wx.BOTTOM, border=20)
        left_layout.Add(self.button_layout,
                        flag=wx.EXPAND | wx.ALIGN_BOTTOM | wx.ALL,
                        border=20
                        )

        self.layout.Add(left_layout, proportion=1, flag=wx.EXPAND)
        self.layout.Add(self.comic_img, proportion=1, flag=wx.ALIGN_RIGHT)

        self.SetSizer(self.layout)
        self.Centre()
        self.Show(True)

    def init_info_text(self):
        """
        エントリのタイトル、作者、カテゴリの情報を初期化
        """
        font = wx.Font(24, wx.FONTFAMILY_DEFAULT,
                       wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.title_text = wx.StaticText(
            self, wx.ID_ANY, self.entry_info["title"], style=wx.TE_CENTER)
        self.title_text.SetFont(font)
        self.author_text = wx.StaticText(
            self, wx.ID_ANY, self.entry_info["author"], style=wx.TE_CENTER)
        self.author_text.SetFont(font)
        self.category_text = wx.StaticText(
            self, wx.ID_ANY, self.entry_info["category"], style=wx.TE_CENTER)
        self.category_text.SetFont(font)
        category_t = wx.StaticText(
            self, wx.ID_ANY, "Category : ", style=wx.TE_CENTER
        )
        category_t.SetFont(font)
        cat_set = wx.BoxSizer(wx.HORIZONTAL)
        cat_set.Add(category_t, flag=wx.RIGHT, border=10)
        cat_set.Add(self.category_text, flag=wx.LEFT)

        self.info_layout = wx.BoxSizer(wx.VERTICAL)
        self.info_layout.Add(
            self.title_text, flag=wx.ALIGN_CENTER | wx.BOTTOM, border=7
        )
        self.info_layout.Add(
            self.author_text, flag=wx.ALIGN_CENTER | wx.BOTTOM, border=7
        )
        self.info_layout.Add(
            cat_set, flag=wx.ALIGN_CENTER | wx.BOTTOM, border=7
        )

    def init_paging_button(self):
        """
        ページングボタンを初期化
        """
        self.next_page = wx.Button(self, wx.ID_ANY, "=>")
        self.prev_page = wx.Button(self, wx.ID_ANY, "<=")
        self.next_page.Bind(wx.EVT_BUTTON, self.draw_next_page)
        self.prev_page.Bind(wx.EVT_BUTTON, self.draw_prev_page)

        # 最初に前ページボタンを無効化
        self.prev_page.Disable()

        self.button_layout = wx.BoxSizer(wx.HORIZONTAL)
        self.button_layout.Add(
            self.prev_page, 200, wx.EXPAND | wx.RIGHT, border=10
        )
        self.button_layout.Add(
            self.next_page, 200, wx.EXPAND | wx.RIGHT, border=10
        )

    def init_comic_img(self):
        """
        漫画の画像表示を初期化
        """
        self.init_imglist_and_idxs()

        # 描画のためにBitmapオブジェクトに変換する必要あり
        image = wx.Image(str(self.image_list[0]))
        bitmap = image.ConvertToBitmap()
        self.comic_img = wx.StaticBitmap(
            self, wx.ID_ANY, bitmap, size=bitmap.GetSize())

    def init_imglist_and_idxs(self):
        """
        漫画画像のリストとページングに使用するインデックスを初期化
        """
        entry_path = self.image_path / self.entry_info["comic_key"]
        self.image_list = list(entry_path.glob("*.jpg"))
        if len(self.image_list) == 0:
            self.image_list = list(entry_path.glob("*.png"))
        self.comic_idx = 0
        self.idx_max = len(self.image_list) - 1
        self.idx_min = 0

    def init_rate_rdbtn(self):
        """
        レート登録用ラジオボタンを初期化
        """
        rate = self.entry_info["rate"]
        self.radio_box = wx.RadioBox(
            self, wx.ID_ANY,
            "rate",
            choices=["unrated", "1", "2", "3", "4", "5"],
            style=wx.RA_HORIZONTAL
        )
        self.radio_box.Bind(wx.EVT_RADIOBOX, self.register_rate)
        self.radio_box.SetStringSelection(str(rate))

    def register_rate(self, event):
        """
        レートをDBに登録する
        """
        selected = self.radio_box.GetStringSelection()
        col = self.GetParent().GetParent().collection
        key = self.entry_info["comic_key"]
        target = {"comic_key": key}
        if selected == "unrated":
            command = {"$set": {"rate": selected}}
        else:
            command = {"$set": {"rate": int(selected)}}
        col.update(target, command)

    def init_cont_work_btn(self):
        """
        連作の次回作、前回作を切り替えるボタンの初期化
        """
        cont_work = self.entry_info["continuous_work"]
        entry_url = self.entry_info["entry_url"]
        self.prev_btn = wx.Button(self, wx.ID_ANY, "previous")
        self.next_btn = wx.Button(self, wx.ID_ANY, "next")
        self.prev_btn.Bind(wx.EVT_BUTTON, self.click_prev_btn)
        self.next_btn.Bind(wx.EVT_BUTTON, self.click_next_btn)

        self.cont_layout = wx.BoxSizer(wx.HORIZONTAL)
        self.cont_layout.Add(
            self.prev_btn, flag=wx.ALIGN_CENTER | wx.RIGHT, border=5
        )
        self.cont_layout.Add(
            self.next_btn, flag=wx.ALIGN_CENTER | wx.LEFT, border=5
        )

        # 連作がない場合はボタンを無効化
        if len(cont_work) == 0:
            self.prev_btn.Disable()
            self.next_btn.Disable()
        # 次の作品のみある場合は prev ボタンを無効化
        elif cont_work.index(entry_url) == 0:
            self.prev_btn.Disable()
        # 前の作品のみある場合は next ボタンを無効化
        elif cont_work.index(entry_url) + 1 == len(cont_work):
            self.next_btn.Disable()

    def click_prev_btn(self, event):
        """
        前の作品を描画
        """
        col = self.GetParent().GetParent().collection
        c_lst = self.entry_info["continuous_work"]
        e_url = self.entry_info["entry_url"]
        prev_url = c_lst[c_lst.index(e_url) - 1]
        comic_key = self.extract_comic_key(prev_url)

        query = {"comic_key": comic_key}
        prev_entry = col.find_one(query)
        if prev_entry is None:
            print("queried entry has not downloaded")
            return
        self.entry_info = prev_entry
        # --- 再描画処理 ---
        self.update_view_page()

    def click_next_btn(self, event):
        """
        次の作品を描画
        """
        col = self.GetParent().GetParent().collection
        c_lst = self.entry_info["continuous_work"]
        e_url = self.entry_info["entry_url"]
        next_url = c_lst[c_lst.index(e_url) + 1]
        comic_key = self.extract_comic_key(next_url)

        query = {"comic_key": comic_key}
        next_entry = col.find_one(query)
        if next_entry is None:
            print("queried entry has not downloaded")
            return
        self.entry_info = next_entry
        # --- 再描画処理 ---
        self.update_view_page()

    def update_view_page(self):
        self.update_info_text()
        self.update_comic_img()
        self.update_rate_rdbtn()
        self.update_paging_button()
        self.update_cont_work_btn()
        self.Layout()

    def update_info_text(self):
        """
        漫画情報を更新
        """
        title = self.entry_info["title"]
        author = self.entry_info["author"]
        category = self.entry_info["category"]
        self.title_text.SetLabel(title)
        self.author_text.SetLabel(author)
        self.category_text.SetLabel(category)

    def update_comic_img(self):
        """
        漫画画像とインデックスを更新
        """
        self.init_imglist_and_idxs()
        image = wx.Image(str(self.image_list[0]))
        bitmap = image.ConvertToBitmap()
        self.comic_img.SetBitmap(bitmap)

    def update_rate_rdbtn(self):
        """
        レートのラジオボタンを更新
        """
        rate = self.entry_info["rate"]
        if rate == "unrated":
            self.radio_box.SetStringSelection(rate)
        else:
            self.radio_box.SetStringSelection(str(rate))

    def update_paging_button(self):
        """
        ページ送りボタンを更新
        """
        self.next_page.Enable()
        self.prev_page.Disable()

    def update_cont_work_btn(self):
        """
        連作のボタン有効化、無効化を更新
        """
        cont_work = self.entry_info["continuous_work"]
        entry_url = self.entry_info["entry_url"]

        # 最初に両方のボタンを有効化
        self.prev_btn.Enable()
        self.next_btn.Enable()

        # 連作がない場合はボタンを無効化
        if len(cont_work) == 0:
            self.prev_btn.Disable()
            self.next_btn.Disable()
        # 次の作品のみある場合は prev ボタンを無効化
        elif cont_work.index(entry_url) == 0:
            self.prev_btn.Disable()
        # 前の作品のみある場合は next ボタンを無効化
        elif cont_work.index(entry_url) + 1 == len(cont_work):
            self.next_btn.Disable()

    def extract_comic_key(self, url):
        """
        urlからcomic_keyを抽出
        """
        tmp = url.split("/")
        return "/".join(tmp[-2:])

    def draw_next_page(self, event):
        """
        ページ送り試作
        """
        self.comic_idx += 1
        # 1ページ進んだため　前ページボタンは有効化
        self.prev_page.Enable()
        # ページ終端なら次ページボタンを無効化
        if self.comic_idx >= self.idx_max:
            self.next_page.Disable()
        window_list = self.layout.GetChildren()
        comic_window = window_list[1].GetWindow()
        image = wx.Image(str(self.image_list[self.comic_idx]))
        bitmap = image.ConvertToBitmap()
        comic_window.SetBitmap(bitmap)
        # 再描画時に画像がずれるので、Layout()をコール
        self.Layout()

    def draw_prev_page(self, event):
        """
        ページ戻し試作
        """
        self.comic_idx -= 1
        # 1ページ戻ったため　次ページボタンは有効化
        self.next_page.Enable()
        # ページ終端なら前ページボタンを無効化
        if self.comic_idx == self.idx_min:
            self.prev_page.Disable()
        window_list = self.layout.GetChildren()
        comic_window = window_list[1].GetWindow()
        image = wx.Image(str(self.image_list[self.comic_idx]))
        bitmap = image.ConvertToBitmap()
        comic_window.SetBitmap(bitmap)
        # 再描画時に画像がずれるので、Layout()をコール
        self.Layout()
