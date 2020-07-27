from pathlib import Path
import wx.lib.newevent

# 漫画保存用のディレクトリパス
COMIC_PATH = Path('data/Comics')
# サムネイル用画像のパス
NO_IMAGE_PATH = Path('data/no_image.png')
# クロール完了通知用のイベント定義
CrawlCompletedEvt, EVT_CRAWL_CMP = wx.lib.newevent.NewEvent()
