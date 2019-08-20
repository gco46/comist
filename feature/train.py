from clustering import BOWKMedoids, convert_to_bin_feature
from feature_extract import FeatureExtractor
import numpy as np
import pickle


def train():
    fe = FeatureExtractor(feature_type="orb")
    X_train = fe.load_feature("train.csv")
    # 全要素が0の特徴を削除する(特徴点が多数重なるため)
    tmp = X_train.sum(axis=1)
    del_idx = np.where(tmp == 0)[0]
    X_train = np.delete(X_train, del_idx, axis=0)
    # randomに特徴を選択して辞書を学習
    # 30000サンプルでメモリ消費のピークが約20GB
    np.random.seed(46)
    idx = np.random.choice(range(X_train.shape[0]), 30000, replace=False)
    X_train = X_train[idx, :]
    X_train = convert_to_bin_feature(X_train)
    bowkm = BOWKMedoids(n_clusters=1000, init_search=5, init="kmeans++")
    bowkm.fit(X_train)
    # 辞書(BOWオブジェクト)を保存
    with open("bowkm", "wb") as obj:
        pickle.dump(bowkm, obj)


if __name__ == "__main__":
    train()
