import wx
from wx import Window, StaticBitmap, StaticText, BoxSizer, Button, Image
import frames.const as c_
from pathlib import Path


class ComicViewFrame(wx.Frame):
    """
    漫画選択後Frame
    """

    def __init__(self, parent: Window, entry_info: dict, target_site: str) -> None:
        super().__init__(parent, wx.ID_ANY)
        self.Maximize()
        self.Bind(wx.EVT_CLOSE, self.close_frame)
        self.target_site: str = target_site
        self.entry_info: dict = entry_info

        self._init_artribute()
        # ViewFrame内のPanel objectを取得
        self._get_view_frame_obj()

        # パネル上部の漫画情報を更新
        self._init_info_text()

        # レート登録用ラジオボタン追加
        self._init_rate_rdbtn()

        # 連作のnext/previous ボタン追加
        self._init_cont_work_btn()

        # ページ送りボタン
        self._init_paging_button()

        # 画像表示
        self._init_comic_img()

        # キーイベントの紐付け
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key)

        # 左側に操作パネル、右側に画像を配置
        # 要調整
        self.layout: BoxSizer = wx.BoxSizer(wx.HORIZONTAL)
        left_layout = wx.BoxSizer(wx.VERTICAL)
        left_layout.Add(self.info_layout, flag=wx.ALIGN_CENTER)
        left_layout.Add(self.radio_box, flag=wx.ALIGN_CENTER |
                        wx.TOP | wx.BOTTOM, border=20)
        left_layout.Add(self.cont_layout, flag=wx.ALIGN_CENTER |
                        wx.TOP | wx.BOTTOM, border=20)
        left_layout.Add(self.button_layout,
                        flag=wx.ALL,
                        border=20
                        )

        self.layout.Add(left_layout, proportion=1, flag=wx.EXPAND)
        self.layout.Add(self.comic_img, proportion=1)

        self.SetSizer(self.layout)
        self.Centre()
        self.Show(True)

    def _init_artribute(self) -> None:
        self.image_path: Path = c_.COMIC_PATH / self.target_site
        self.image_size: tuple = c_.IMAGE_SIZE
        self.image_height: int = c_.IMAGE_HEIGHT
        self.image_width: int = c_.IMAGE_WIDTH
        # 画像サイズ超過の許容量
        self.size_capacity: int = 15

    def close_frame(self, event) -> None:
        """
        Frameを閉じた時にentry list panelを更新
        """
        # search panelからクエリを取得し、再検索と画面更新
        query = self.search_panel.query
        search_result = self.search_panel.DB_search(query)
        # 再検索後のエントリ数から表示するページ数を算出
        n_item_per_page: int = self.entry_panel.n_item_per_page
        max_idx: int = -(-len(search_result) // n_item_per_page) - 1
        n_page: int = self.entry_panel.e_list_idx
        n_page = min(max_idx, n_page)
        self.entry_panel.update_entry_list(search_result, n_page)
        # 画面を閉じる
        self.Destroy()

    def on_key(self, event) -> None:
        """
        キーイベント
        左右の矢印キーが押されたときにページ送り処理をする
        """
        code = event.GetKeyCode()
        if code == wx.WXK_RIGHT:
            # ページ終端でなければ次ページへ
            if self.next_page_btn_is_enabled:
                self.draw_next_page()
        elif code == wx.WXK_LEFT:
            # ページ終端でなければ前ページへ
            if self.prev_page_btn_is_enabled:
                self.draw_prev_page()

    def _get_view_frame_obj(self) -> None:
        # CollectionPanel取得
        self.col_panel: Window = self.GetParent().GetParent().collection_panel
        # EntryListPanel取得
        self.entry_panel: Window = self.GetParent()
        # SearchPanel取得
        self.search_panel: Window = self.GetParent().GetParent().search_panel
        # ViewFrame取得
        self.view_frame: Window = self.GetParent().GetParent()

    def _init_info_text(self) -> None:
        """
        エントリのタイトル、作者、カテゴリの情報を初期化
        """
        font = wx.Font(24, wx.FONTFAMILY_DEFAULT,
                       wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.title_text: StaticText = wx.StaticText(
            self, wx.ID_ANY, self.entry_info["title"], style=wx.TE_CENTER)
        self.title_text.SetFont(font)
        self.author_text: StaticText = wx.StaticText(
            self, wx.ID_ANY, self.entry_info["author"], style=wx.TE_CENTER)
        self.author_text.SetFont(font)
        self.category_text: StaticText = wx.StaticText(
            self, wx.ID_ANY, self.entry_info["comic_key"], style=wx.TE_CENTER)
        self.category_text.SetFont(font)
        category_t = wx.StaticText(
            self, wx.ID_ANY, "Comic ID : ", style=wx.TE_CENTER
        )
        category_t.SetFont(font)
        cat_set = wx.BoxSizer(wx.HORIZONTAL)
        cat_set.Add(category_t, flag=wx.RIGHT, border=10)
        cat_set.Add(self.category_text, flag=wx.LEFT)

        self.info_layout: BoxSizer = wx.BoxSizer(wx.VERTICAL)
        self.info_layout.Add(
            self.title_text, flag=wx.ALIGN_CENTER | wx.BOTTOM, border=7
        )
        self.info_layout.Add(
            self.author_text, flag=wx.ALIGN_CENTER | wx.BOTTOM, border=7
        )
        self.info_layout.Add(
            cat_set, flag=wx.ALIGN_CENTER | wx.BOTTOM, border=7
        )

    def _init_paging_button(self) -> None:
        """
        ページングボタンを初期化
        """
        font = wx.Font(20, wx.FONTFAMILY_DEFAULT,
                       wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.next_page: Button = wx.Button(self, wx.ID_ANY, "→", size=(400, 100))
        self.next_page.SetFont(font)
        self.prev_page: Button = wx.Button(self, wx.ID_ANY, "←", size=(400, 100))
        self.prev_page.SetFont(font)
        self.next_page.Bind(wx.EVT_BUTTON, self.click_next_page_btn)
        self.prev_page.Bind(wx.EVT_BUTTON, self.click_prev_page_btn)

        # 最初に前ページボタンのみ無効化
        self.enable_page_btn("next")
        self.disable_page_btn("prev")

        self.button_layout: BoxSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.button_layout.Add(
            self.prev_page, flag=wx.ALIGN_CENTER | wx.LEFT, border=20
        )
        self.button_layout.Add(
            self.next_page, flag=wx.ALIGN_CENTER | wx.LEFT, border=10
        )

    def _init_comic_img(self) -> None:
        """
        漫画の画像表示を初期化
        """
        self._init_imglist_and_idxs()
        # 描画のためにBitmapオブジェクトに変換する必要あり
        image = wx.Image(str(self.image_list[0]))
        image = self.scale_bitmap_image(image)
        bitmap = image.ConvertToBitmap()
        self.comic_img: StaticBitmap = wx.StaticBitmap(
            self, wx.ID_ANY, bitmap, size=self.image_size)

    def _init_imglist_and_idxs(self) -> None:
        """
        漫画画像のリストとページングに使用するインデックスを初期化
        """
        entry_path = self.image_path / self.entry_info["comic_key"]
        self.image_list = list(entry_path.glob("*"))
        self.image_list = list(map(str, self.image_list))
        # 画像をソート
        self.image_list.sort(key=c_.natural_keys)
        self.comic_idx = 0
        self.idx_max = len(self.image_list) - 1
        self.idx_min = 0

    def _init_rate_rdbtn(self) -> None:
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

    def scale_bitmap_image(self, img_obj: Image) -> Image:
        """
        標準サイズより大きい画像を縮小する
        input
          img_obj: wx.Image object

        output
          image: wx.Image object, scale処理後
        """
        if img_obj.Width > self.image_width + self.size_capacity and \
                img_obj.Height > self.image_height + self.size_capacity:
            scale_width = self.image_width
            scale_height = self.image_height
        else:
            scale_width = img_obj.Width
            scale_height = img_obj.Height
        scaled_img = img_obj.Scale(scale_width, scale_height, wx.IMAGE_QUALITY_HIGH)
        return(scaled_img)

    def register_rate(self, event):
        """
        レートをDBに登録する
        """
        selected = self.radio_box.GetStringSelection()
        col = self.view_frame.collection
        key = self.entry_info["comic_key"]
        target = {"comic_key": key}
        if selected == "unrated":
            command = {"$set": {"rate": selected}}
        else:
            command = {"$set": {"rate": int(selected)}}
        col.update_one(target, command)

    def _init_cont_work_btn(self):
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
        col = self.view_frame.collection
        c_lst = self.entry_info["continuous_work"]
        e_url = self.entry_info["entry_url"]
        prev_url = c_lst[c_lst.index(e_url) - 1]
        comic_key = self.extract_comic_key(prev_url)

        query = {"comic_key": comic_key}
        prev_entry = col.find_one(query)
        # 前の作品が未ダウンロードの場合はdialog表示
        if prev_entry is None:
            category, id = comic_key.split("/")
            dialog = wx.MessageDialog(
                None,
                'The comic has not downloaded yet.\n \
                category: {0}\n \
                id: {1}'.format(category, id),
                style=wx.OK | wx.ALIGN_LEFT
            )
            dialog.ShowModal()
            dialog.Destroy()
            return
        self.entry_info = prev_entry
        # --- 再描画処理 ---
        self.update_view_page()

    def click_next_btn(self, event):
        """
        次の作品を描画
        """
        col = self.view_frame.collection
        c_lst = self.entry_info["continuous_work"]
        e_url = self.entry_info["entry_url"]
        next_url = c_lst[c_lst.index(e_url) + 1]
        comic_key = self.extract_comic_key(next_url)

        query = {"comic_key": comic_key}
        next_entry = col.find_one(query)
        # 次の作品が未ダウンロードの場合はdialog表示
        if next_entry is None:
            category, id = comic_key.split("/")
            dialog = wx.MessageDialog(
                None,
                'The comic has not downloaded yet.\n \
                category: {0}\n \
                id: {1}'.format(category, id),
                style=wx.OK | wx.ALIGN_LEFT
            )
            dialog.ShowModal()
            dialog.Destroy()
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
        comic_key = self.entry_info["comic_key"]
        self.title_text.SetLabel(title)
        self.author_text.SetLabel(author)
        self.category_text.SetLabel(comic_key)

    def update_comic_img(self):
        """
        漫画画像とインデックスを更新
        """
        self._init_imglist_and_idxs()
        image = wx.Image(str(self.image_list[0]))
        image = image.Scale(
            self.image_width, self.image_height, wx.IMAGE_QUALITY_HIGH)
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

    def enable_page_btn(self, direction):
        """
        ページ送り/戻りボタンの有効化
        directionで送り/戻りを指定
        """
        assert direction in ["next", "prev"]

        if direction == "prev":
            self.prev_page.Enable()
            self.prev_page_btn_is_enabled = True
        else:
            self.next_page.Enable()
            self.next_page_btn_is_enabled = True

    def disable_page_btn(self, direction):
        """
        ページ送り/戻りボタンの無効化
        directionで送り/戻りを指定
        """
        assert direction in ["next", "prev"]

        if direction == "prev":
            self.prev_page.Disable()
            self.prev_page_btn_is_enabled = False
        else:
            self.next_page.Disable()
            self.next_page_btn_is_enabled = False

    def extract_comic_key(self, url):
        """
        urlからcomic_keyを抽出
        """
        tmp = url.split("/")
        return "/".join(tmp[-2:])

    def click_next_page_btn(self, event):
        """
        ページ送りボタン
        """
        self.draw_next_page()

    def click_prev_page_btn(self, event):
        """
        ページ戻しボタン
        """
        self.draw_prev_page()

    def draw_next_page(self):
        """
        ページ送り処理
        """
        self.comic_idx += 1
        # 1ページ進んだため　前ページボタンは有効化
        self.enable_page_btn("prev")
        # ページ終端なら次ページボタンを無効化
        if self.comic_idx >= self.idx_max:
            self.disable_page_btn("next")
        window_list = self.layout.GetChildren()
        comic_window = window_list[1].GetWindow()
        image = wx.Image(str(self.image_list[self.comic_idx]))
        image = self.scale_bitmap_image(image)
        bitmap = image.ConvertToBitmap()
        comic_window.SetBitmap(bitmap)
        # 再描画時に画像がずれるので、Layout()をコール
        self.Layout()

    def draw_prev_page(self):
        """
        ページ戻し処理
        """
        self.comic_idx -= 1
        # 1ページ戻ったため　次ページボタンは有効化
        self.enable_page_btn("next")
        # ページ終端なら前ページボタンを無効化
        if self.comic_idx == self.idx_min:
            self.disable_page_btn("prev")
        window_list = self.layout.GetChildren()
        comic_window = window_list[1].GetWindow()
        image = wx.Image(str(self.image_list[self.comic_idx]))
        image = self.scale_bitmap_image(image)
        bitmap = image.ConvertToBitmap()
        comic_window.SetBitmap(bitmap)
        # 再描画時に画像がずれるので、Layout()をコール
        self.Layout()
