import wx
from frames.view import ViewFrame
from frames.crawl import CrawlFrame
from frames.rating import RatingFrame


class MyFrame(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title)
        panel = wx.Panel(self, -1)

        vbox = wx.BoxSizer(wx.VERTICAL)

        btn_ReadComics = wx.Button(panel, -1, 'Read Comics')
        vbox.Add(btn_ReadComics, 0, wx.ALL, 10)
        btn_Scrape = wx.Button(panel, -1, 'Scrape')
        vbox.Add(btn_Scrape, 0, wx.ALL, 10)
        btn_IO_Rating = wx.Button(panel, -1, "Import/Export Rating")
        vbox.Add(btn_IO_Rating, 0, wx.ALL, 10)

        panel.SetSizer(vbox)

        btn_ReadComics.Bind(wx.EVT_BUTTON, self.OnClickReadComics)
        btn_Scrape.Bind(wx.EVT_BUTTON, self.OnClickScrape)
        btn_IO_Rating.Bind(wx.EVT_BUTTON, self.OnClickIORating)
        self.Centre()
        self.Show(True)

    def OnClickScrape(self, event):
        scrape = CrawlFrame(self)

    def OnClickReadComics(self, event):
        view_frame = ViewFrame(self)

    def OnClickIORating(self, event):
        rating_frame = RatingFrame(self)


if __name__ == "__main__":
    app = wx.App()
    MyFrame(None, -1, 'ComicCluster')
    app.MainLoop()
