import wx


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
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, -1, 'view frame')
        # Frameは一つ以上のPanelを含む
        # Panelの第一引数には親となるFrameを指定する
        panel = wx.Panel(self, -1)

        text1 = wx.StaticText(panel, -1, "category1")
        text2 = wx.StaticText(panel, -1, "category2")
        self.result_text = wx.StaticText(panel, -1, "clicked text is...")

        text1.Bind(wx.EVT_LEFT_DOWN, self.click)
        text2.Bind(wx.EVT_LEFT_DOWN, self.click)

        v_layout = wx.BoxSizer(wx.VERTICAL)
        v_layout.Add(text1, flag=wx.TOP, border=10)
        v_layout.Add(text2, flag=wx.TOP, border=10)
        v_layout.Add(self.result_text, flag=wx.TOP, border=10)

        panel.SetSizer(v_layout)
        self.Show(True)

    def click(self, event):
        click = event.GetEventObject()
        print(click)
        click_text = click.GetLabel()
        self.result_text.SetLabel(click_text)


if __name__ == "__main__":
    app = wx.App()
    MyFrame(None, -1, 'moveevent.py')
    app.MainLoop()
