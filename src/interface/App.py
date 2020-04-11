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
        self.open_DB()
        panel = wx.Panel(self, wx.ID_ANY)
        # Frameは一つ以上のPanelを含む
        # Panelの第一引数には親となるFrameを指定する
        self.entry_panel = EntryListPanel(self, wx.ID_ANY)
        self.search_panel = SearchPanel(self, wx.ID_ANY)
        self.collection_panel = CollectionPanel(self, wx.ID_ANY)

        self.layout = wx.BoxSizer(wx.VERTICAL)
        self.layout.Add(self.collection_panel, flag=wx.EXPAND)
        self.layout.Add(self.search_panel, flag=wx.EXPAND)
        self.layout.Add(self.entry_panel, flag=wx.EXPAND)

        panel.SetSizer(self.layout)
        self.Show(True)

    def click(self, event):
        click = event.GetEventObject()
        print(click)
        click_text = click.GetLabel()
        self.result_text.SetLabel(click_text)

    def open_DB(self):
        """
        ローカルMongoDBに接続し、ScrapedDataを開く
        """
        self.client = MongoClient('localhost', 27017)
        self.db = self.client['ScrapedData']

    def select_collection(self, col):
        """
        DBのコレクションを選択
        """
        self.collection = self.db[col]


class EntryListPanel(wx.Panel):
    """
    ViewFrame内
    エントリ一覧を表示するパネル(ウィンドウ右に配置)
    """

    def __init__(self, parent, id):
        super().__init__(parent, id)
        self.parent = parent


class SearchPanel(wx.Panel):
    """
    ViewFrame内
    エントリー一覧を表示するパネル(ウィンドウ中央に配置)
    """

    def __init__(self, parent, id):
        super().__init__(parent, id)
        self.parent = parent


class CollectionPanel(wx.Panel):
    """
    ViewFrame内
    コレクション一覧を表示するパネル(ウィンドウ左に配置)
    """

    def __init__(self, parent, id):
        super().__init__(parent, id)
        self.parent = parent


if __name__ == "__main__":
    app = wx.App()
    MyFrame(None, -1, 'moveevent.py')
    app.MainLoop()
