import wx
from pymongo import MongoClient
from pathlib import Path


class RatingFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, wx.ID_ANY,
                          'rating frame', size=(700, 800))
        self._open_DB()
        self.Bind(wx.EVT_CLOSE, self._close_DB)
        # TODO: DB close処理
        self.layout = wx.BoxSizer(wx.VERTICAL)
        self.export_panel = ExportPanel(self, wx.ID_ANY)
        # TODO:import 用layout

        self.layout.Add(self.export_panel)
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

    def _get_collection_list(self):
        self.col_list = self.db.list_collection_names()

    def _close_DB(self, event):
        """
        ViewFrameが閉じられた時にDBクローズ
        """
        self.client.close()
        self.Destroy()

    def init_export_layout(self):
        self.export_layout = wx.BoxSizer(wx.HORIZONTAL)
        self.save_to = wx.StaticText(self, wx.ID_ANY, "save to:")
        font = wx.Font(
            13, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_NORMAL
        )
        self.save_to.SetFont(font)
        self.export_dir_path = wx.TextCtrl(self, wx.ID_ANY, "")
        self.export_button = wx.Button(self, wx.ID_ANY, "choose")
        self.export_button.Bind(wx.EVT_BUTTON, self.click_choose_export_dir)

        self.export_layout.Add(
            self.save_to, proportion=1, flag=wx.ALIGN_CENTER)
        self.export_layout.Add(self.export_dir_path, proportion=6)
        self.export_layout.Add(
            self.export_button, proportion=1, flag=wx.ALIGN_CENTER)

    def click_choose_export_dir(self, event):
        directory = wx.DirDialog(
            self,
            style=wx.DD_CHANGE_DIR,
            message="保存先フォルダ"
        )
        if directory.ShowModal() == wx.ID_OK:
            self.export_dir_path.SetValue(directory.GetPath())
        directory.Destroy()


class ExportPanel(wx.Panel):
    def __init__(self, parent, id):
        super().__init__(parent, id, style=wx.BORDER_SUNKEN)
        self.init_export_layout()
        self.init_radio_btn()
        self.export_btn = wx.Button(self, wx.ID_ANY, "export")

        self.layout = wx.BoxSizer(wx.VERTICAL)

        self.layout.Add(self.export_layout)
        self.layout.Add(self.radio_box, flag=wx.ALIGN_CENTER)
        self.layout.Add(self.export_btn, flag=wx.ALIGN_RIGHT |
                        wx.TOP, border=5)
        self.SetSizer(self.layout)

    def init_export_layout(self):
        self.export_layout = wx.BoxSizer(wx.HORIZONTAL)
        self.save_to = wx.StaticText(self, wx.ID_ANY, "save to:")
        font = wx.Font(
            13, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_NORMAL
        )
        self.save_to.SetFont(font)
        self.export_dir_path = wx.TextCtrl(self, wx.ID_ANY, "")
        self.export_button = wx.Button(self, wx.ID_ANY, "choose")
        self.export_button.Bind(wx.EVT_BUTTON, self.click_choose_export_dir)

        self.export_layout.Add(
            self.save_to, proportion=1, flag=wx.ALIGN_CENTER)
        self.export_layout.Add(self.export_dir_path, proportion=6)
        self.export_layout.Add(
            self.export_button, proportion=1, flag=wx.ALIGN_CENTER)

    def init_radio_btn(self):
        font = wx.Font(
            14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_NORMAL
        )
        self.radio_box = wx.RadioBox(
            self, wx.ID_ANY, '', choices=self.GetParent().col_list,
            style=wx.RA_VERTICAL
        )
        self.radio_box.SetFont(font)

    def click_choose_export_dir(self, event):
        directory = wx.DirDialog(
            self,
            style=wx.DD_CHANGE_DIR,
            message="保存先フォルダ"
        )
        if directory.ShowModal() == wx.ID_OK:
            self.export_dir_path.SetValue(directory.GetPath())
        directory.Destroy()

    def click_export(self, event):
        pass
