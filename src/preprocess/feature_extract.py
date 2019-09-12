from pathlib import Path
import cv2
import numpy as np
import os
import os.path as osp
import pandas as pd


class FeatureExtractor(object):
    """
    cv2 objectを使用して画像から特徴量を抽出する
    """
    # バイナリ特徴のリスト(バイナリ変換時の判定に使用)
    BINARY_FEATS = ["orb", "brisk"]
    # 特徴量毎のパラメータのデフォルト値を指定
    # ひとまずスケールに関係するパラメータのみデフォルト値を設定
    DEFAULT_PARAMS = {
        "orb": {"patchSize": 31, "scaleFactor": 1.2},
        "brisk": {"octaves": 3, "patternScale": 1.0},
        "sift": {"contrastThreshold": 0.04,
                 "edgeThreshold": 10,
                 "sigma": 1.6}
    }

    def __init__(self, root_path, feature_type, step, **kwargs):
        self.root_path = Path(root_path)
        self.feature_type = feature_type.lower()
        self.step = step
        self.kwargs = kwargs
        self.feat_path = Path("../../data/features")
        
        # 特徴抽出に使用するインスタンス生成
        self._args_check()
        self._set_cv2_instance()

    def _get_data_ids(self, path):
        """
        path: str, id情報を含むファイルへのパス
        """
        data_ids = pd.read_csv(osp.join(self.save_feat_path, path))
        data_ids = data_ids["id"]
        data_ids = data_ids.values.reshape(-1).tolist()
        return data_ids

    def load_feature(self, csv_path, convert=False):
        """
        特徴量をファイルから読み込む
        csv_path: str, 読み込む特徴量のcsvファイル
        convert: bool, Trueなら特徴をバイナリ(0 or 1)に変換する(np.uint8)
        """
        data_ids = self._get_data_ids(csv_path)
        feature_set = []
        for id in data_ids:
            feat_path = self._get_loadfile_path(id)
            feature = np.load(str(feat_path))
            feature_set += feature.tolist()
        if convert and self.feature_type in self.BINARY_FEATS:
            return self._convert_to_bin_feature(np.array(feature_set))
        else:
            return np.array(feature_set)

    def load_feature_for_each_file(self, csv_path, convert=False):
        """
        ファイル単位でfeatureを返すiteratorオブジェクト
        """
        data_ids = self._get_data_ids(csv_path)
        for id in data_ids:
            feat_path = self._get_loadfile_path(id)
            feature = np.load(str(feat_path))
            if convert and self.feature_type in self.BINARY_FEATS:
                feature = self._convert_to_bin_feature(feature)
            yield feat_path, feature

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
            # gridで抽出するためthresholdは0とする
            self.fe = cv2.BRISK_create(
                thresh=0,
                octaves=params["octaves"],
                patternScale=params["patternScale"]
            )
        elif self.feature_type == "sift":
            self.fe = cv2.xfeatures2d.SIFT_create(
                contrastThreshold=params["contrastThreshold"],
                edgeThreshold=params["edgeThreshold"],
                sigma=params["sigma"]
            )

    def _convert_to_bin_feature(self, X):
        """
        uint8で表現された特徴をバイナリコードに変換する
        input: shape  = (n_samples, n_dim)
        output: shape = (n_samples, n_dim * 8)
        """
        # arrayの各要素を2進数表記(文字列)へ変換する
        # np.frompyfunc(FuncObj, num of argv, num of outputs)
        b_format = np.frompyfunc(format, 2, 1)
        bin_str_X = b_format(X, "08b")

        # arrayの各要素をlistへ変換する(文字列表記の二進数をlistへ分割する)
        str2list_np = np.frompyfunc(list, 1, 1)
        # サンプルごとにlistを結合する
        # 次の処理でmap関数を使うため、list型に変換する
        # listを要素に持つnp.arrayに対してmapは使えないっぽい
        bin_list_X = str2list_np(bin_str_X).sum(axis=1).tolist()

        # 各要素が文字列となっているため、uint8へ変換
        char2int_np = np.frompyfunc(int, 1, 1)
        result = char2int_np(bin_list_X).astype(np.uint8)

        return result

    def _make_dirs(self, path):
        try:
            os.makedirs(str(path))
        except FileExistsError:
            pass

    def _save_feature(self, feature_set, path):
        np.save(str(path), feature_set)

    def _make_params_info_str(self):
        """
        特徴抽出のパラメータ情報を文字列にして返す。(ディレクトリ名用)
        """
        return "step" + str(self.step)

    def _get_keypoints(self, img):
        kp = [cv2.KeyPoint(x, y, self.step)
              for y in range(0, img.shape[0], self.step)
              for x in range(0, img.shape[1], self.step)]
        return kp

    def _get_loadfile_path(self, id):
        """
        サブクラスで処理定義
        """
        return None


class ImageFeatureExtractor(FeatureExtractor):
    def __init__(self, root_path="../../data/ukbench",
                 feature_type="orb", step=50, **kwargs):
        super(ImageFeatureExtractor, self).__init__(
            root_path,
            feature_type,
            step,
            **kwargs
        )
        step_info = self._make_params_info_str()
        self.save_feat_path = self.feat_path.joinpath(
            "bench", self.feature_type, step_info)

    def extract_save(self):
        self._make_dirs(self.save_feat_path)
        for img_path in self.root_path.iterdir():
            if img_path.suffix == ".jpg":
                feature = self._extract_image_feat(img_path)
                self._save_feature(
                    feature,
                    self.save_feat_path.joinpath(img_path.stem + ".npy")
                )

    def _extract_image_feat(self, img_path):
        img = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
        kp = self._get_keypoints(img)
        _, feature = self.fe.compute(img, kp)
        return feature

    def train_test_split(self, test_size, isUkbench=True):
        feats_path = list(self.save_feat_path.glob("*.npy"))
        if isUkbench:
            # ukbench datasetの場合、画像四枚で一組なので
            # 各クラスでtrain:1, test:3とする
            feats_path.sort()
            train_idx = np.arange(0, len(feats_path), 4)
            test_idx = set(range(len(feats_path))) - set(train_idx)
            test_idx = sorted(np.array(list(test_idx)))
        else:
            num_test = int(len(feats_path) * test_size)
            test_idx = np.random.choice(
                len(feats_path), num_test, replace=False)
            test_idx = sorted(test_idx)
            train_set = set(range(len(feats_path))) - set(test_idx)
            train_idx = sorted(np.array(list(train_set)))

        test_df = pd.DataFrame(test_idx, columns=["id"])
        train_df = pd.DataFrame(train_idx, columns=["id"])
        test_df.to_csv(
            str(self.save_feat_path.joinpath("test.csv")), index=False)
        train_df.to_csv(
            str(self.save_feat_path.joinpath("train.csv")), index=False)

    def load_feature(self, csv_path, convert=False):
        # 特徴量ファイル一覧を先に読み込む
        self.feats_path = list(self.save_feat_path.glob("*.npy"))
        self.feats_path = sorted(self.feats_path)
        feature = super().load_feature(csv_path, convert=convert)
        return feature

    def load_feature_for_each_file(self, csv_path, convert=False):
        self.feats_path = list(self.save_feat_path.glob("*.npy"))
        self.feats_path = sorted(self.feats_path)
        return super().load_feature_for_each_file(csv_path, convert=convert)

    def _get_loadfile_path(self, id):
        """
        idから読み込むファイルのPathオブジェクトを指定して返す。
        """
        return self.feats_path[id]


class ComicFeatureExtractor(FeatureExtractor):
    """
    extract_save:特徴量を漫画単位でnp.saveで保存する
    """

    def __init__(self, root_path="../../data/Comics",
                 feature_type="orb", step=50, **kwargs):
        super(ComicFeatureExtractor, self).__init__(
            root_path,
            feature_type,
            step,
            **kwargs
        )
        self.root_path = Path(root_path)
        step_info = self._make_params_info_str()
        self.save_feat_path = self.feat_path.joinpath(
            self.feature_type, step_info)

    def extract_save(self):
        """
        self.comic_root内の画像を読み込み、特徴量をDataFrame pickleで保存する。
        カレントディレクトリ内に　(特徴量名)/(パラメータ) というディレクトリを作成し、
        カテゴリ別に保存する。
        - DataFrame構造
        1列目：comic ID
        2列目以降：１特徴点に対する特徴量(バイナリ未変換、uint8)
        """
        for category_path in self.root_path.iterdir():
            if category_path.is_dir():
                self._get_category_feature(category_path)

    def load_feature(self, csv_path, convert=False):
        """
        特徴量をファイルから読み込む
        csv_path: str, 読み込む特徴量のcomic idが書かれたcsvファイルへのパス
        """
        data_ids = pd.read_csv(osp.join(self.save_feat_path, csv_path))
        data_ids = data_ids["id"]
        data_ids = data_ids.values.reshape(-1).tolist()
        dir = self._make_params_info_str()
        feature_set = []
        for id in data_ids:
            gen = self.save_feat_path.glob(osp.join("**", str(id)+".npy"))
            gen = list(gen)[0]
            feature = np.load(str(gen))
            feature_set += feature.tolist()
        if convert:
            return self._convert_to_bin_feature(np.array(feature_set))
        else:
            return np.array(feature_set)

    def train_test_split(self, test_size):
        """
        抽出した特徴量ファイル(.npy)からcomic idをtrain用, test用に分割し、
        csvファイルに出力する
        1列目：category
        2列目：comic id
        """
        categories = self.save_feat_path.iterdir()
        self.test_data = pd.DataFrame()
        self.train_data = pd.DataFrame()
        for cat_path in categories:
            if cat_path.is_dir():
                self._add_DataFrame_in_category(cat_path, test_size)
        # インスタンス生成時のfeature_typeのディレクトリ内にcsvを出力する
        self.train_data.to_csv(
            str(self.save_feat_path.joinpath("train.csv")), index=False)
        self.test_data.to_csv(
            str(self.save_feat_path.joinpath("test.csv")), index=False)

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
        target_path = self.save_feat_path.joinpath(category)
        self._make_dirs(target_path)
        # COMIC_SET_NUMずつ保存するためのカウンタ
        count = 0
        # pickleファイルに番号を割り付けるためのカウンタ
        comic_set_num = 0
        cat_feature = []
        # カテゴリ内の漫画を一つずつ読み込み、特徴抽出〜保存を行う
        # 1つのpickleファイルにself.NUM_COMIC_SETの漫画の特徴を持たせる
        for comic_path in cat_p.iterdir():
            if comic_path.is_dir():
                comic_id = comic_path.name
                comic_feature = self._extract_comic_feat(comic_path)
                save_path = target_path.joinpath(comic_id + ".npy")
                self._save_feature(comic_feature, save_path)

    def _extract_comic_feat(self, comic_path):
        """
        opencvによる特徴抽出を実施する
        compute()メソッドを持つ特徴記述子を想定
        - output
            features: array, (n_samples, n_dims)
            comic_id: str, id number of comic
        """
        features = []
        for file_path in comic_path.iterdir():
            if file_path.suffix == ".jpg":
                img = cv2.imread(str(file_path), cv2.IMREAD_GRAYSCALE)
                kp = self._get_keypoints(img)
                _, feature = self.fe.compute(img, kp)
                features += feature.tolist()
        features = np.array(features)
        return features

    def _get_loadfile_path(self, id):
        """
        idから読み込むファイルのPathオブジェクトを指定し、返す
        """
        gen = self.save_feat_path.glob(osp.join("**", str(id)+".npy"))
        result = list(gen)[0]
        return result


if __name__ == "__main__":
    # import pickle
    # with open("bowkm", "rb") as obj:
    #     voc = pickle.load(obj)
    fe = ImageFeatureExtractor(step=10, patchSize=100)
    # for file_path, x in fe.load_feature_for_each_file("train.csv", True):
    #     res = voc.compute(x)
    #     print(file_path, x.shape)
    # fe.extract_save()
    fe.train_test_split(test_size=0.7)
    # feature = fe.load_feature("test.csv")
