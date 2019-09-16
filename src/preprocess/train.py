from clustering import BOWKMedoids, BOWKMeans
from feature_extract import ComicFeatureExtractor, ImageFeatureExtractor
import numpy as np
import pickle


def train():
    fe = ImageFeatureExtractor(step=10, feature_type="sift")
    X_train = fe.load_feature("train.csv")
    # 全要素が0の特徴を削除する(特徴点が多数重なるため)
    tmp = X_train.sum(axis=1)
    del_idx = np.where(tmp == 0)[0]
    X_train = np.delete(X_train, del_idx, axis=0)
    print("number of features is ", X_train.shape[0])
    # randomに特徴を選択して辞書を学習
    np.random.seed(46)
    # idx = np.random.choice(range(X_train.shape[0]), 30000, replace=False)
    # X_train = X_train[idx, :]
    # bowkm = BOWKMedoids(n_clusters=1000, init_search=3, init="kmeans++")
    bowkm = BOWKMeans(n_clusters=1000)
    bowkm.fit(X_train)
    # 辞書(BOWオブジェクト)を保存
    with open("bowkm", "wb") as obj:
        pickle.dump(bowkm, obj)


if __name__ == "__main__":
    train()
