from clustering import BOWKMedoids, convert_to_bin_feature
from feature_extract import FeatureExtractor
import numpy as np
import pickle


def train():
    fe = FeatureExtractor(feature_type="orb")
    X_train = fe.load_feature("train.csv")
    num_samples, num_dim = X_train.shape
    np.random.seed(46)
    idx = np.random.choice(range(num_samples), 15000, replace=False)
    X_train = X_train[idx, :]
    X_train = convert_to_bin_feature(X_train)

    bowkm = BOWKMedoids(n_clusters=1000)
    bowkm.fit(X_train)
    with open("bowkm", "wb") as obj:
        pickle.dump(bowkm, obj)


if __name__ == "__main__":
    train()
