import wx
from pymongo import MongoClient
from pathlib import Path


class RatingFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, wx.ID_ANY,
                          'rating frame', size=(700, 400))
        self.layout = wx.BoxSizer(wx.VERTICAL)
        self.export_panel = ExportPanel(self, wx.ID_ANY)
        # TODO:import 用layout

        self.layout.Add(self.export_panel)
        self.SetSizer(self.layout)
        self.Centre()
        self.Show(True)

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
        self.export_button.Bind(wx.EVT_BUTTON, self.click_export)

        self.export_layout.Add(
            self.save_to, proportion=1, flag=wx.ALIGN_CENTER)
        self.export_layout.Add(self.export_dir_path, proportion=6)
        self.export_layout.Add(
            self.export_button, proportion=1, flag=wx.ALIGN_CENTER)

    def click_export(self, event):
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

        self.layout = wx.BoxSizer(wx.HORIZONTAL)

        self.layout.Add(self.export_layout)
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
        self.export_button.Bind(wx.EVT_BUTTON, self.click_export)

        self.export_layout.Add(
            self.save_to, proportion=1, flag=wx.ALIGN_CENTER)
        self.export_layout.Add(self.export_dir_path, proportion=6)
        self.export_layout.Add(
            self.export_button, proportion=1, flag=wx.ALIGN_CENTER)

    def click_export(self, event):
        directory = wx.DirDialog(
            self,
            style=wx.DD_CHANGE_DIR,
            message="保存先フォルダ"
        )
        if directory.ShowModal() == wx.ID_OK:
            self.export_dir_path.SetValue(directory.GetPath())
        directory.Destroy()
