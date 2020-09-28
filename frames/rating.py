import wx
from pymongo import MongoClient
import pandas as pd
from pathlib import Path


class RatingFrame(wx.Frame):
    """
    Import/Export Rating選択後画面
    """

    def __init__(self, parent):
        wx.Frame.__init__(self, parent, wx.ID_ANY,
                          'rating IO frame')
        # 最大化(Notebookの描画がうまくいかない)
        self.Maximize()
        self._open_DB()
        # DB close処理を閉じるボタンと関連付け
        self.Bind(wx.EVT_CLOSE, self._close_DB)
        self.layout = wx.BoxSizer(wx.VERTICAL)
        # tab表示
        self.notebook = wx.Notebook(self, wx.ID_ANY)
        export_panel = ExportPanel(self.notebook, wx.ID_ANY)
        import_panel = ImportPanel(self.notebook, wx.ID_ANY)
        self.notebook.AddPage(export_panel, "export")
        self.notebook.AddPage(import_panel, "import")

        self.layout.Add(self.notebook, flag=wx.ALL | wx.EXPAND, border=5)
        self.SetSizer(self.layout)
        self.Layout()
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

    def select_collection(self, col):
        """
        DBのコレクションを選択
        """
        self.collection = self.db[col]


class ExportPanel(wx.Panel):
    def __init__(self, parent, id):
        super().__init__(parent, id, style=wx.BORDER_SUNKEN)
        # 保存先フォルダ選択のレイアウト初期化
        self.init_export_layout()
        # コレクション選択のラジオボタン初期化
        self.init_radio_btn()

        # export実行ボタン追加
        self.export_btn = wx.Button(self, wx.ID_ANY, "export")
        self.export_btn.Bind(wx.EVT_BUTTON, self.click_export)

        self.layout = wx.BoxSizer(wx.VERTICAL)

        self.layout.Add(self.export_layout, flag=wx.ALIGN_CENTER)
        self.layout.Add(self.radio_box, flag=wx.ALIGN_CENTER)
        self.layout.Add(self.export_btn, flag=wx.ALIGN_RIGHT |
                        wx.TOP, border=5)
        self.SetSizer(self.layout)

    def init_export_layout(self):
        """
        保存先フォルダ選択
        """
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
        """
        export対象のコレクション選択ラジオボタンの初期化
        """
        font = wx.Font(
            14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_NORMAL
        )
        self.radio_box = wx.RadioBox(
            self, wx.ID_ANY, '', choices=self.GetParent().GetParent().col_list,
            style=wx.RA_VERTICAL
        )
        self.radio_box.SetFont(font)

    def click_choose_export_dir(self, event):
        """
        export結果の保存先をフォルダで指定(
        """
        directory = wx.DirDialog(
            self,
            style=wx.DD_CHANGE_DIR,
            message="保存先フォルダ"
        )
        if directory.ShowModal() == wx.ID_OK:
            self.export_dir_path.SetValue(directory.GetPath())
        directory.Destroy()

    def click_export(self, event):
        """
        export実行
        """
        out_path = Path(self.export_dir_path.GetValue())
        if not out_path.exists() or str(out_path) == ".":
            # 保存先パスが適切でない場合は終了
            dialog = wx.MessageDialog(
                None, 'choose exist path.',
                style=wx.OK
            )
            res = dialog.ShowModal()
            return
        target_cat = self.radio_box.GetStringSelection()
        self.GetParent().GetParent().select_collection(target_cat)
        file_name = target_cat + ".csv"
        save_path = out_path / file_name

        # unrated以外を取得するクエリ
        query = {
            "rate": {"$ne": "unrated"}
        }
        collection = self.GetParent().GetParent().collection

        # 検索結果
        rated_item = collection.find(query)
        # DataFrameに取り込む
        rated_item = pd.DataFrame.from_dict(list(rated_item)).astype(object)
        # comic_key と rateのみ取得
        rated_item = rated_item[["comic_key", "rate"]]
        # comic_keyで昇順ソート
        rated_item = rated_item.sort_values("comic_key")
        # 指定した場所へcsv出力
        rated_item.to_csv(str(save_path), header=False, index=False)

        dialog = wx.MessageDialog(
            None, 'Complete!',
            style=wx.OK
        )
        res = dialog.ShowModal()


class ImportPanel(wx.Panel):
    def __init__(self, parent, id):
        super().__init__(parent, id, style=wx.BORDER_SUNKEN)
        # 入力ファイル選択のレイアウト初期化
        self.init_import_layout()
        # コレクション選択のラジオボタン初期化
        self.init_radio_btn()

        # export実行ボタン追加
        self.import_btn = wx.Button(self, wx.ID_ANY, "import")

        self.layout = wx.BoxSizer(wx.VERTICAL)

        self.layout.Add(self.import_layout, flag=wx.ALIGN_CENTER)
        self.layout.Add(self.radio_box, flag=wx.ALIGN_CENTER)
        self.layout.Add(self.import_btn, flag=wx.ALIGN_RIGHT |
                        wx.TOP, border=5)
        self.SetSizer(self.layout)

    def init_import_layout(self):
        """
        入力ファイル選択
        """
        self.import_layout = wx.BoxSizer(wx.HORIZONTAL)
        self.input_file = wx.StaticText(self, wx.ID_ANY, "input:")
        font = wx.Font(
            13, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_NORMAL
        )
        self.input_file.SetFont(font)
        self.import_file_path = wx.TextCtrl(self, wx.ID_ANY, "")
        self.import_button = wx.Button(self, wx.ID_ANY, "choose")
        self.import_button.Bind(wx.EVT_BUTTON, self.click_choose_import_file)

        self.import_layout.Add(
            self.input_file, proportion=1, flag=wx.ALIGN_CENTER)
        self.import_layout.Add(self.import_file_path, proportion=6)
        self.import_layout.Add(
            self.import_button, proportion=1, flag=wx.ALIGN_CENTER)

    def init_radio_btn(self):
        """
        import対象のコレクション選択ラジオボタンの初期化
        """
        font = wx.Font(
            14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_NORMAL
        )
        self.radio_box = wx.RadioBox(
            self, wx.ID_ANY, '', choices=self.GetParent().GetParent().col_list,
            style=wx.RA_VERTICAL
        )
        self.radio_box.SetFont(font)

    def click_choose_import_file(self, event):
        """
        importするファイルを指定
        """
        file = wx.FileDialog(
            self,
            style=wx.DD_CHANGE_DIR,
            message="保存先フォルダ"
        )
        if file.ShowModal() == wx.ID_OK:
            self.import_file_path.SetValue(file.GetPath())
        file.Destroy()

    def click_import(self, event):
        pass
