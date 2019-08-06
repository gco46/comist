from pathlib import Path
import cv2
import numpy as np
import os
import os.path as osp
import pandas as pd


class FeatureExtractor(object):
    def __init__(self, comic_root="../Comics", feature="orb", patch_size=50,
                 step=50):
        self.comic_root = Path(comic_root)
        self.feature = feature
        self.patch_size = patch_size
        self.step = step
        if self.feature == "orb":
            self.fe = cv2.ORB_create(
                edgeThreshold=0,
                patchSize=self.patch_size
            )
        self.NUM_COMIC_SET = 50

    def extract_save(self):
        for category_path in self.comic_root.iterdir():
            if category_path.is_dir():
                self._get_category_feature(category_path)

    def _get_category_feature(self, cat_p):
        category = cat_p.name
        count = 0
        comic_set_num = 0
        cat_feature = []
        for comic_path in cat_p.iterdir():
            if comic_path.is_dir():
                comic_feature = self._extract_with_cv2(comic_path)
                cat_feature += comic_feature.tolist()
                count += 1
            if count % self.NUM_COMIC_SET == (self.NUM_COMIC_SET - 1):
                cat_feature = np.array(cat_feature)
                self._save_ComicSet_feature(
                    cat_feature, category, comic_set_num)
                cat_feature = []
                comic_set_num += 1

    def _save_ComicSet_feature(self, feature_set, category, c_set_num):
        _, n_dim = feature_set.shape
        col_name = ["x" + str(i) for i in range(n_dim-1)]
        col_name = ["comic_id"] + col_name
        ComicSet = pd.DataFrame(feature_set, columns=col_name)
        params_info = self._make_params_info_str()
        target_path = Path(osp.join(self.feature, params_info, category))
        try:
            os.makedirs(str(target_path))
        except FileExistsError:
            pass
        ComicSet.to_pickle(str(target_path / str(c_set_num)))

    def _make_params_info_str(self):
        result = "p" + str(self.patch_size) + "s" + str(self.step)
        return result

    def _extract_with_cv2(self, comic_path):
        comic_id = int(comic_path.name)
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
        num_f, num_dim = features.shape
        ids = np.ones((num_f, 1), dtype=np.uint32) * comic_id
        features = np.hstack((ids, features))
        return features


if __name__ == "__main__":
    fe = FeatureExtractor()
    fe.extract_save()
