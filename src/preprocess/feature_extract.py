from pathlib import Path
import cv2
import numpy as np
import os
import os.path as osp
import pandas as pd


class FeatureExtractor(object):
    def __init__(self):
        pass

    def extract_save(self):
        pass


class ComicFeatureExtractor(FeatureExtractor):
    """
    extract_save:特徴量を漫画単位でnp.saveで保存する
    """

    def __init__(self, comic_root="../../Comics", feature_type="orb",
                 step=50, **kwargs):
        # データが保存してあるrootディレクトリ
        self.comic_root = Path(comic_root)
        # 特徴量の種類(opencv対応のもの)
        self.feature_type = feature_type.lower()
        self.step = step
        self.kwargs = kwargs
        # 特徴量毎のパラメータのデフォルト値を指定
        # ひとまずスケールに関係するパラメータのみデフォルト値を設定
        # gridで抽出するためthresholdは0とする
        self.DEFAULT_PARAMS = {
            "orb": {"patchSize": 31, "scaleFactor": 1.2},
            "brisk": {"octaves": 3, "patternScale": 1.0},
        }
        self._args_check()
        self._set_cv2_instance()

    def _args_check(self):
        """
        指定したfeature_typeとkwargsで与えられたパラメータとの整合性をチェックする
        """
        params = self.DEFAULT_PARAMS[self.feature_type].keys()
        for arg in self.kwargs.keys():
            if arg not in params:
                raise ValueError(
                    self.feature_type + " doesnt take argument " + arg)

    def _set_cv2_instance(self):
        """
        feature_typeに合わせたopencvのインスタンスを生成する
        対応：ORB, BRISK
        """
        params = self.DEFAULT_PARAMS[self.feature_type]
        for param in params.keys():
            if param in self.kwargs:
                params[param] = self.kwargs[param]
        self.cv2_params = params
        if self.feature_type == "orb":
            self.fe = cv2.ORB_create(
                edgeThreshold=0,
                patchSize=params["patchSize"],
                scaleFactor=params["scaleFactor"]
            )
        elif self.feature_type == "brisk":
            self.fe = cv2.BRISK_create(
                thresh=0,
                octaves=params["octaves"],
                patternScale=params["patternScale"]
            )

    def extract_save(self):
        """
        self.comic_root内の画像を読み込み、特徴量をDataFrame pickleで保存する。
        カレントディレクトリ内に　(特徴量名)/(パラメータ) というディレクトリを作成し、
        カテゴリ別に保存する。
        - DataFrame構造
        1列目：comic ID
        2列目以降：１特徴点に対する特徴量(バイナリ未変換、uint8)
        """
        for category_path in self.comic_root.iterdir():
            if category_path.is_dir():
                self._get_category_feature(category_path)

    def load_feature(self, csv_path):
        """
        特徴量をファイルから読み込む
        csv_path: str, 読み込む特徴量のcomic idが書かれたcsvファイルへのパス
        """
        data_ids = pd.read_csv(osp.join(self.feature_type, csv_path))
        data_ids = data_ids["id"]
        data_ids = data_ids.values.reshape(-1).tolist()
        dir = self._make_params_info_str()
        feature_path = Path(osp.join(self.feature_type, dir))
        feature_set = []
        for id in data_ids:
            gen = feature_path.glob(osp.join("**", str(id)+".npy"))
            gen = list(gen)[0]
            feature = np.load(str(gen))
            feature_set += feature.tolist()
        return np.array(feature_set)

    def train_test_split(self, test_size):
        """
        抽出した特徴量ファイル(.npy)からcomic idをtrain用, test用に分割し、
        csvファイルに出力する
        1列目：category
        2列目：comic id
        """
        feature_path = Path(self.feature_type)
        categories = feature_path.iterdir()
        self.test_data = pd.DataFrame()
        self.train_data = pd.DataFrame()
        for cat_path in categories:
            if cat_path.is_dir():
                self._add_DataFrame_in_category(cat_path, test_size)
        # インスタンス生成時のfeature_typeのディレクトリ内にcsvを出力する
        self.train_data.to_csv(
            osp.join(self.feature_type, "train.csv"), index=False)
        self.test_data.to_csv(
            osp.join(self.feature_type, "test.csv"), index=False)

    def _add_DataFrame_in_category(self, cat_path, test_size):
        """
        指定したカテゴリ内でtrain, testを分割し、それぞれのdataframeを返す
        """
        ids = []
        category = str(cat_path).split("/")[-1]
        gen = cat_path.glob("**/*.npy")
        for file_path in gen:
            id = str(file_path).split("/")[-1][:-4]
            ids.append(int(id))
        # 先にtestサンプルを指定し、余ったファイルをtrainに使用する
        num_test_samples = int(len(ids) * test_size)
        test_id = np.random.choice(ids, num_test_samples, replace=False)
        # csvの見やすさのため、idはソートする
        test_id = np.sort(test_id)
        train_id = np.array(list(set(ids) - set(test_id)))
        test_df = self._make_DataFrame(category, test_id)
        train_df = self._make_DataFrame(category, train_id)
        # test, trainを既存のdataに追加する
        self.test_data = pd.concat([self.test_data, test_df], axis=0)
        self.train_data = pd.concat([self.train_data, train_df], axis=0)

    def _make_DataFrame(self, category, id):
        cat_list = [category] * len(id)
        data = pd.DataFrame({"category": cat_list, "id": id})
        return data

    def _get_category_feature(self, cat_p):
        category = cat_p.name
        # COMIC_SET_NUMずつ保存するためのカウンタ
        count = 0
        # pickleファイルに番号を割り付けるためのカウンタ
        comic_set_num = 0
        cat_feature = []
        # カテゴリ内の漫画を一つずつ読み込み、特徴抽出〜保存を行う
        # 1つのpickleファイルにself.NUM_COMIC_SETの漫画の特徴を持たせる
        for comic_path in cat_p.iterdir():
            if comic_path.is_dir():
                comic_feature, comic_id = self._extract_with_cv2(comic_path)
                self._save_ComicSet_feature(comic_feature, category, comic_id)

    def _save_ComicSet_feature(self, feature_set, category, comic_id):
        _, n_dim = feature_set.shape
        params_info = self._make_params_info_str()
        target_path = Path(
            osp.join(self.feature_type, params_info, category))
        npy_name = osp.join(target_path, comic_id+".npy")
        try:
            os.makedirs(str(target_path))
        except FileExistsError:
            pass
        np.save(npy_name, feature_set)

    def _make_params_info_str(self):
        """
        特徴抽出のパラメータ情報を文字列にして返す。(ディレクトリ名用)
        """
        return ""
        # ------- disabled -----------
        # if self.feature_type == "orb":
        #     result = "p" + str(self.patch_size) + "s" + str(self.step)
        # return result
        # ----------------------------

    def _extract_with_cv2(self, comic_path):
        """
        opencvによる特徴抽出を実施する
        compute()メソッドを持つ特徴記述子を想定
        - output
            features: array, (n_samples, n_dims)
            comic_id: str, id number of comic
        """
        comic_id = comic_path.name
        features = []
        for file_path in comic_path.iterdir():
            if file_path.suffix == ".jpg":
                img = cv2.imread(str(file_path), cv2.IMREAD_GRAYSCALE)
                kp = [cv2.KeyPoint(x, y, self.step)
                      for y in range(0, img.shape[0], self.step)
                      for x in range(0, img.shape[1], self.step)]
                _, feature = self.fe.compute(img, kp)
                features += feature.tolist()
        features = np.array(features)
        return features, comic_id


if __name__ == "__main__":
    fe = ComicFeatureExtractor(step=200, patchSize=200)
    fe.extract_save()
    fe.train_test_split(test_size=0.7)
    feature = fe.load_feature("test.csv")
