import wx
from pymongo import MongoClient
from pathlib import Path


class ComicViewFrame(wx.Frame):
    """
    漫画選択後Frame
    """
    image_path = Path('../../data/Comics')

    def __init__(self, parent, entry_info):
        super().__init__(parent, wx.ID_ANY)
        self.Maximize()

        title_text = wx.StaticText(
            self, wx.ID_ANY, 'Entry', style=wx.TE_CENTER)
        font_Title = wx.Font(24, wx.FONTFAMILY_DEFAULT,
                             wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        title_text.SetFont(font_Title)

        # ページ送りボタン
        next_page = wx.Button(self, wx.ID_ANY, "=>")
        prev_page = wx.Button(self, wx.ID_ANY, "<=")
        next_page.Bind(wx.EVT_BUTTON, self.draw_next_page)
        prev_page.Bind(wx.EVT_BUTTON, self.draw_prev_page)

        # DBからの取得した画像パスの模擬
        entry_path = self.image_path / entry_info["comic_key"]
        self.image_list = list(entry_path.glob("*.jpg"))
        if len(self.image_list) == 0:
            self.image_list = list(entry_path.glob("*.png"))
        self.comic_idx = 0
        self.idx_max = len(self.image_list) - 1
        self.idx_min = 0

        # 描画のためにBitmapオブジェクトに変換する必要あり
        image = wx.Image(str(self.image_list[0]))
        bitmap = image.ConvertToBitmap()
        comic_img = wx.StaticBitmap(
            self, wx.ID_ANY, bitmap, size=bitmap.GetSize())

        # 左側に操作パネル、右側に画像を配置
        # 要調整
        self.layout = wx.BoxSizer(wx.HORIZONTAL)
        left_layout = wx.BoxSizer(wx.VERTICAL)
        left_layout.Add(title_text, flag=wx.ALIGN_CENTER)
        button_layout = wx.BoxSizer(wx.HORIZONTAL)
        button_layout.Add(prev_page, flag=wx.ALL, border=10)
        button_layout.Add(next_page, flag=wx.ALL, border=10)
        left_layout.Add(button_layout, flag=wx.ALIGN_CENTER)

        self.layout.Add(left_layout, proportion=1, flag=wx.ALIGN_LEFT)
        self.layout.Add(comic_img, proportion=1, flag=wx.ALIGN_RIGHT)

        self.SetSizer(self.layout)
        self.Centre()
        self.Show(True)

    def draw_next_page(self, event):
        """
        ページ送り試作
        """
        if self.comic_idx >= self.idx_max:
            return
        self.comic_idx += 1
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
        if self.comic_idx <= self.idx_min:
            return
        self.comic_idx -= 1
        window_list = self.layout.GetChildren()
        comic_window = window_list[1].GetWindow()
        image = wx.Image(str(self.image_list[self.comic_idx]))
        bitmap = image.ConvertToBitmap()
        comic_window.SetBitmap(bitmap)
        # 再描画時に画像がずれるので、Layout()をコール
        self.Layout()
