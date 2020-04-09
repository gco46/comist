import wx

# 同windowに再描画するサンプル


class mainFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, wx.ID_ANY, 'Testapp', size=(900, 500),
                         style=wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX | wx.CLIP_CHILDREN)

        # ウィンドウのタイトル設定
        self.CreateStatusBar()
        self.SetStatusText('Testapp')
        self.GetStatusBar().SetBackgroundColour(None)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)

        self.set_screen(Panel_1)

    def set_screen(self, panel):
        """
        パネル毎描画を入れ替える時に使用
        カテゴリ一覧->エントリ一覧の時に使うかも？
        """
        self.sizer.Clear(False)
        self.DestroyChildren()

        self.now_panel = panel(self)
        self.sizer.Add(self.now_panel, 1, wx.EXPAND)
        self.sizer.Layout()


class Panel_1(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent, wx.ID_ANY)
        self.parent = parent
        # 漫画エントリの模擬
        self.num_entries = 25
        self.link_texts_idx = 0
        self.n_item_per_page = 10
        # 再描画用に、エントリの端数は空文字列を入れる
        self.link_texts = ["entry" + str(i) for i in range(self.num_entries)]
        # 切り上げ除算してから乗算
        tmp = -(-self.num_entries // self.n_item_per_page) * \
            self.n_item_per_page
        self.link_texts += [""] * (tmp - self.num_entries)
        self.idx_max = len(self.link_texts) // self.n_item_per_page - 1
        self.idx_min = 0

        self.title_text = wx.StaticText(
            self, wx.ID_ANY, 'タイトル', style=wx.TE_CENTER)
        self.font_Title = wx.Font(24, wx.FONTFAMILY_DEFAULT,
                                  wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.title_text.SetFont(self.font_Title)

        next_button = wx.Button(self, wx.ID_ANY, '次へ')
        next_button.Bind(wx.EVT_BUTTON, self.click_next_button)
        previous_button = wx.Button(self, wx.ID_ANY, '前へ')
        previous_button.Bind(wx.EVT_BUTTON, self.click_previous_button)

        self.layout = wx.BoxSizer(wx.VERTICAL)

        self.layout.Add(self.title_text, flag=wx.ALIGN_CENTER)
        for i in range(self.n_item_per_page):
            item_text = wx.StaticText(self, wx.ID_ANY, self.link_texts[i])
            self.layout.Add(item_text, flag=wx.ALIGN_CENTER)
        button_layout = wx.BoxSizer(wx.HORIZONTAL)
        button_layout.Add(previous_button, flag=wx.ALIGN_CENTER)
        button_layout.Add(next_button, flag=wx.RIGHT | wx.LEFT, border=10)
        self.layout.Add(button_layout, flag=wx.RIGHT | wx.LEFT, border=10)

        self.SetSizer(self.layout)

    def click_next_button(self, event):
        """
        エントリ一覧のページング　次へボタン試作
        """
        if self.link_texts_idx == self.idx_max:
            return
        self.link_texts_idx += 1
        windows_list = self.layout.GetChildren()
        for i in range(self.n_item_per_page):
            window = windows_list[1 + i].GetWindow()
            window.SetLabel(
                self.link_texts[self.link_texts_idx * self.n_item_per_page + i]
            )

        # self.parent.set_screen(Panel_2)

    def click_previous_button(self, event):
        """
        エントリ一覧のページング　前へボタン試作
        """
        if self.link_texts_idx == self.idx_min:
            return
        self.link_texts_idx -= 1
        windows_list = self.layout.GetChildren()
        for i in range(self.n_item_per_page):
            window = windows_list[1 + i].GetWindow()
            window.SetLabel(
                self.link_texts[self.link_texts_idx * self.n_item_per_page + i]
            )


class Panel_2(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent, wx.ID_ANY)
        self.parent = parent

        title_text = wx.StaticText(
            self, wx.ID_ANY, '遷移後画面', style=wx.TE_CENTER)
        font_Title = wx.Font(24, wx.FONTFAMILY_DEFAULT,
                             wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        title_text.SetFont(font_Title)

        start_button = wx.Button(self, wx.ID_ANY, 'スタートに戻る')
        start_button.Bind(wx.EVT_BUTTON, self.click_start_button)

        layout = wx.BoxSizer(wx.VERTICAL)

        layout.Add(title_text, flag=wx.ALIGN_CENTER)
        layout.Add(start_button, flag=wx.ALIGN_CENTER)

        self.SetSizer(layout)

    def click_start_button(self, event):
        self.parent.set_screen(Panel_1)


if __name__ == '__main__':

    application = wx.App()
    frame = mainFrame()
    frame.Show()
    application.MainLoop()
