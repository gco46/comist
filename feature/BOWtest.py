import numpy as np
import pandas as pd
from sklearn.datasets import make_blobs
from sklearn.preprocessing import LabelBinarizer
from scipy.spatial.distance import cdist, pdist, squareform
import matplotlib.pyplot as plt
from joblib import Parallel, delayed
import cv2


class KMedoids(object):
    def __init__(self, n_clusters, max_iter=50, tol=0, init="kmeans++",
                 metric="euclidean", n_jobs=-1, init_search=5, mem_save=False):
        # クラスタ数
        self.n_clusters = n_clusters
        # medoidを更新する最大回数
        self.max_iter = max_iter
        # loop終了フラグ
        self.loop_flag = True
        # one-hot表現のラベル取得に使用
        self.lb = LabelBinarizer()
        # tolerance(未実装、現状medoids群の変化有無で終了判定する)
        self.tol = tol
        # medoidを更新した回数
        self.num_loop = 0
        self.medoids_idx = None
        self.medoids = None
        # 直前のmedoids集合
        self.last_medoids = set([0])
        # medoids初期値をどのように決定するか
        self.init = init
        # サンプル間距離の計算方法
        self.metric = metric
        # 初期値探索のみ並列して行う
        self.n_jobs = n_jobs
        # 初期値探索する回数
        self.init_search = init_search
        # Falseなら行列演算によりmedoids更新を行う(メモリ消費大)
        # Trueならn_clustersについてforループでmedoids更新する
        self.mem_save = mem_save

    def fit(self, X):
        """
        データに対してクラスタリングを実施する
        X : 2D-np.array,  (n_samples, n_dim)
        """
        # 距離行列を指定したmetricで計算
        self.D = squareform(pdist(X, self.metric))
        self.n_samples, n_dim = X.shape
        if self.n_samples < self.n_clusters:
            raise ValueError("number of samples is larger than n_clusters")

        # medoids初期値をinit_search回計算し、最もクラスタ内誤差が
        # 小さいmedoidsを初期値として使用する
        # init : list of tuple, [(score, medoids), ...]
        # length == self.init_search
        print("initialize medoids...")
        # inits = []
        # for i in range(self.init_search):
        #     inits.append(self._init_medoids())
        inits = Parallel(n_jobs=self.n_jobs)(
            [delayed(self._init_medoids)() for i in range(self.init_search)])
        print("initialize done.")
        self.medoids_idx = sorted(inits, key=lambda x: x[0])[0][1]
        self.medoids = X[self.medoids_idx, :]

        # fit完了後に最新のラベルを参照できるようにするため、ループの最後に
        # label更新を入れる
        # 一回目(初期値)のlabel更新はループ前で実施
        tmp_labels = self._make_labels(self.medoids_idx)

        # 終了条件：medoidに変化なし  or  ループ回数がmax_iterに到達
        print("train model...")
        while (self.num_loop <= self.max_iter) and self.loop_flag:
            one_hot_labels = self._encode_labels_to_OneHot(tmp_labels)
            self._update_medoids(one_hot_labels)
            tmp_labels = self._make_labels(self.medoids_idx)
            self.labels = tmp_labels
            self.num_loop += 1
            self.medoids = X[self.medoids_idx, :]
        print("done.")

    def _init_medoids(self):
        """
        medoidの初期値を選択する
        self.init : "random"   -> 乱数で選択
                    "kmeans++" -> 初期medoidが近づきすぎないような
                                  確率分布に従って選択
        """
        if self.init == "kmeans++":
            medoids = []
            for n in range(self.n_clusters):
                if n == 0:
                    # 最初のセントロイドは乱数で決定する
                    medoid = np.random.choice(
                        range(self.n_samples), 1, replace=False)
                    medoids.extend(medoid)
                else:
                    # 2つ目以降はkmeans++の方法で選択

                    # medoidとして選ばれたサンプル以外から次のmedoidを選ぶ
                    remained_samples = set(
                        range(self.n_samples)) - set(medoids)
                    remained_samples = list(remained_samples)

                    # 各サンプルについて最近傍medoidとの距離を計算
                    distance = np.delete(self.D, medoids, axis=0)
                    distance = distance[:, medoids]
                    min_distance = distance.min(axis=1)

                    # d(x_i)^2 / sum(d(x_i)^2) の確率分布に従い、medoidを選ぶ
                    sqrd_min_distance = min_distance * min_distance
                    probs = sqrd_min_distance / sqrd_min_distance.sum()
                    medoid = np.random.choice(remained_samples, 1, p=probs)
                    medoids.extend(medoid)
            medoids = np.array(medoids)
        elif self.init == "random":
            medoids = np.random.choice(
                range(self.n_samples), self.n_clusters, replace=False)

        # 評価を計算
        score_of_init = self._eval_init(medoids)
        return (score_of_init, medoids)

    def _eval_init(self, medoids):
        """
        クラスタ内誤差の総和を計算する
        medoids初期値の評価に使用
        """
        labels = self._make_labels(medoids)
        one_hot_labels = self._encode_labels_to_OneHot(labels)
        if self.mem_save:
            each_sample_D = 0
            for n in range(self.n_clusters):
                label_vec = one_hot_labels[:, n]
                D_in_clusters = label_vec[np.newaxis, :] * \
                    label_vec[:, np.newaxis]
                D_in_clusters = D_in_clusters * self.D
                each_sample_D_clst = D_in_clusters.sum()
                each_sample_D += each_sample_D_clst
        else:
            D_in_clusters = (one_hot_labels[np.newaxis, :, :] *
                             one_hot_labels[:, np.newaxis, :]).swapaxes(0, 2)
            D_in_clusters = D_in_clusters * self.D[np.newaxis, :, :]
            each_sample_D = np.sum(D_in_clusters).sum()
        return each_sample_D

    def _make_labels(self, medoids):
        """
        サンプルがどのクラスタに所属するかのラベルを計算する
        output: np.array,  self.labels  (shape=(n_samples,))
        """
        labels = np.argmin(self.D[:, medoids], axis=1)
        return labels

    def _encode_labels_to_OneHot(self, labels):
        if self.n_clusters == 2:
            result = np.hstack(
                (labels.reshape(-1, 1), 1 - labels.reshape(-1, 1)))
        else:
            result = self.lb.fit_transform(labels)
        return result

    def _update_medoids(self, one_hot_labels):
        """
        1. それぞれのクラスタ内において、クラスタ内の他のすべての点との距離が
           最小になる点をmedoidとする
        2. medoidに変化がなければ終了する(self.loop_flag = False とする)
        """
        if self.mem_save:
            tmp_medoids = []
            for n in range(self.n_clusters):
                label_vec = one_hot_labels[:, n]
                D_in_clusters = label_vec[None, :] * label_vec[:, None]
                D_in_clusters = D_in_clusters * self.D

                each_sample_D = np.sum(D_in_clusters, axis=1)
                if each_sample_D.sum() == 0:
                    tmp_medoids.append(self.medoids_idx[n])
                    continue
                else:
                    np.place(each_sample_D, each_sample_D == 0, float("inf"))
                    tmp_medoids.append(np.argmin(each_sample_D))
            self.medoids_idx = np.array(tmp_medoids)
        else:
            # 各クラスタ内の二点間の距離を計算する
            # D_in_clusters.shape == (n_clusters, n_samples, n_samples), 対象行列
            D_in_clusters = (one_hot_labels[np.newaxis, :, :] *
                             one_hot_labels[:, np.newaxis, :]).swapaxes(0, 2)
            D_in_clusters = D_in_clusters * self.D[np.newaxis, :, :]

            # 各サンプルをmedoidとしたときの距離の総和が最小となる点を
            # 新たなmedoidとする
            each_sample_D = np.sum(D_in_clusters, axis=1)
            # 最近傍として参照されないmedoidはそのまま次のmedoidとして選択
            alone_medoid_mask = (each_sample_D.sum(axis=1) == 0).astype(int)
            np.place(each_sample_D, each_sample_D == 0, float("inf"))
            self.medoids_idx = np.argmin(each_sample_D, axis=1) + \
                (self.medoids_idx * alone_medoid_mask)

        # 終了条件判定
        self._judge_exit_condition()

    def _judge_exit_condition(self):
        unchanged_medoids = self.last_medoids.intersection(
            set(self.medoids_idx))
        if len(unchanged_medoids) == self.n_clusters:
            self.loop_flag = False
        else:
            self.last_medoids = set(self.medoids_idx)


class BOWKMedoids(KMedoids):
    """
    KMediodsを使用したBOW用モデル
    """

    def __init__(self, n_clusters, max_iter=50, init="kmeans++",
                 metric="hamming", n_jobs=1, init_search=5, mem_save=True):
        super(BOWKMedoids, self).__init__(
            n_clusters=n_clusters,
            max_iter=max_iter,
            init=init,
            metric=metric,
            n_jobs=n_jobs,
            init_search=init_search,
            mem_save=mem_save
        )

    def compute(self, X):
        # medoidからの距離を計算
        # shape = (num_cluster, num_dim)
        dist_to_medoids = cdist(X, self.medoids, metric=self.metric)
        count = np.argmin(dist_to_medoids, axis=1)
        hist = np.histogram(count, bins=self.n_clusters)[0]
        hist = hist / X.shape[0]
        return hist


def convert_to_bin_feature(X):
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


def main():
    gray = cv2.imread("test.jpg", 0)

    step_size = 15
    kp = [cv2.KeyPoint(x, y, step_size)
          for y in range(0, gray.shape[0], step_size)
          for x in range(0, gray.shape[1], step_size)]
    # img = cv2.drawKeypoints(gray, kp, img)

    orb = cv2.ORB_create(edgeThreshold=0, patchSize=50)
    print("feature extracting...")
    keypoints, features = orb.compute(gray, kp)
    print("num of features:{0}".format(features.shape[0]))
    print("convert to binary features...")
    X = convert_to_bin_feature(features)

    km = BOWKMedoids(n_clusters=100, n_jobs=1, init_search=5,
                     mem_save=True, init="kmeans++")
    print("KMedoids training...")
    km.fit(X)
    orb = cv2.ORB_create(edgeThreshold=0, patchSize=30, scaleFactor=1.0)
    _, features = orb.compute(gray, kp)
    X_test = convert_to_bin_feature(features)
    hist = km.compute(X_test)


if __name__ == "__main__":
    main()
