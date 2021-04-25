from pathlib import Path
import wx.lib.newevent
import re
import platform
from typing import Dict, Any, Optional

# DBのレコードをdictにキャストした型
ComicDoc = Optional[Dict[str, Any]]

# 漫画保存用のディレクトリパス
COMIC_PATH = Path('data/Comics')
# サムネイル用画像のパス
NO_IMAGE_PATH = Path('data/no_image.png')
# クロール完了通知用のイベント定義
CrawlCompletedEvt, EVT_CRAWL_CMP = wx.lib.newevent.NewEvent()
# 漫画画像 Height
IMAGE_HEIGHT = 1024
# 漫画画像 Width
IMAGE_WIDTH = 712
# 漫画画像サイズ (width, height)
IMAGE_SIZE = (IMAGE_WIDTH, IMAGE_HEIGHT)
if platform.system() == "Darwin":
    # サムネイル Height
    SUMB_HEIGHT = 215
    # サムネイル Width
    SUMB_WIDTH = 150
else:
    # サムネイル Height
    SUMB_HEIGHT = 260
    # サムネイル Width
    SUMB_WIDTH = 180


def atof(text):
    try:
        retval = float(text)
    except ValueError:
        retval = text
    return retval


def natural_keys(text):
    '''
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (See Toothy's implementation in the comments)
    float regex comes from https://stackoverflow.com/a/12643073/190597
    '''
    return [atof(c) for c in re.split(r'[+-]?([0-9]+(?:[.][0-9]*)?|[.][0-9]+)', text)]
