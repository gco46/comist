import pickle
import sqlite3 as sqlite
import feature_extract as fe
import numpy as np
from operator import itemgetter


class Indexer(object):
    def __init__(self, db, voc):
        self.con = sqlite.connect(db)
        self.voc = voc

    def __del__(self):
        self.con.close()

    def db_commit(self):
        self.con.commit()

    def create_tables(self):
        self.con.execute('create table imlist(filename)')
        self.con.execute('create table imwords(imid,wordid,vocname)')
        self.con.execute('create table imhistograms(imid,histogram,vocname)')
        self.con.execute('create index im_idx on imlist(filename)')
        self.con.execute('create index wordid_idx on imwords(wordid)')
        self.con.execute('create index imid_idx on imwords(imid)')
        self.con.execute('create index imidhist_idx on imhistograms(imid)')
        self.db_commit()

    def add_to_index(self, imname, descr):
        if self.is_indexed(imname):
            return
        print('indexing', imname)

        # 画像IDを取得する
        imid = self.get_id(imname)
        # ワードを取得する
        imwords = self.voc.compute(descr)
        wids = imwords.nonzero()[0]
        # 各ワードを画像に関係づける
        for wid in wids:
            word = int(wid)
            self.con.execute("insert into imwords(imid,wordid,vocname) \
                values (?,?,?)", (imid, word, "ukbenchtest"))
        self.con.execute("insert into imhistograms(imid,histogram,vocname) \
            values (?,?,?)", (imid, pickle.dumps(imwords), "ukbenchtest"))

    def is_indexed(self, imname):
        im = self.con.execute("select rowid from imlist where \
            filename='%s'" % imname).fetchone()
        return im != None

    def get_id(self, imname):
        cur = self.con.execute(
            "select rowid from imlist where filename='%s'" % imname)
        res = cur.fetchone()
        if res == None:
            cur = self.con.execute(
                "insert into imlist(filename) values ('%s')" % imname)
            return cur.lastrowid
        else:
            return res[0]


class Searcher(object):
    def __init__(self, db, voc):
        self.con = sqlite.connect(db)
        self.voc = voc

    def __del__(self):
        self.con.close()

    def candidates_from_word(self, imword):
        im_ids = self.con.execute(
            "select distinct imid from imwords where wordid=%d" % imword).fetchall()
        return [i[0] for i in im_ids]

    def candidates_from_histogram(self, imwords):
        """
        ヒストグラムを入力し、
        類似ワードを持つ画像IDのリストを取得する
        """
        # ワードのID(index)を取得する
        words = imwords.nonzero()[0]
        candidates = []
        # 同じワードIDを含む画像をdbから取得する
        for word in words:
            c = self.candidates_from_word(word)
            candidates += c
        # 全ワードを重複なく抽出し、出現回数の大きい順にソート
        tmp = [(w, candidates.count(w)) for w in set(candidates)]
        tmp.sort(key=lambda x: x[1], reverse=True)

        return [w[0] for w in tmp]

    def get_imhistogram(self, imname):
        im_id = self.con.execute(
            "select rowid from imlist where filename=?", imname
        ).fetchone()
        s = self.con.execute(
            "select histogram from imhistograms where rowid=?", im_id
        ).fetchone()
        return pickle.loads(s[0])

    def query(self, imname):
        if not isinstance(imname, tuple):
            raise ValueError("imname must be tuple of str")
        h = self.get_imhistogram(imname)
        candidates = self.candidates_from_histogram(h)
        matchscores = []
        for imid in candidates:
            cand_name = self.con.execute(
                "select filename from imlist where rowid=?", (imid,)
            ).fetchone()
            cand_h = self.get_imhistogram(cand_name)
            cand_dist = np.sqrt(np.sum((h - cand_h)**2))
            matchscores.append((cand_dist, imid))
        matchscores.sort()
        return matchscores


def create_db_test():
    with open("bowkm", "rb") as obj:
        voc = pickle.load(obj)
    idx = Indexer('test.db', voc)
    idx.create_tables()
    imgfe = fe.ImageFeatureExtractor(feature_type="sift", step=10)
    file_feature = []
    for file_path, x in imgfe.load_feature_for_each_file("train.csv", True):
        file_feature.append((file_path, x))
    for file_path, x in imgfe.load_feature_for_each_file("test.csv", True):
        file_feature.append((file_path, x))
    file_feature.sort(key=lambda x: x[0])
    for file_path, x in file_feature:
        idx.add_to_index(file_path, x)
    idx.db_commit()


def search_test():
    with open("bowkm", "rb") as obj:
        voc = pickle.load(obj)
    search = Searcher('test.db', voc)
    imgfe = fe.ImageFeatureExtractor(feature_type="sift", step=20)
    for f_path, x in imgfe.load_feature_for_each_file("train.csv", True):
        print(f_path)
        iw = voc.compute(x)
        break
    print("ask using a histogram...")
    print(search.candidates_from_histogram(iw)[:10])


def search_test_imquery():
    with open("bowkm", "rb") as obj:
        voc = pickle.load(obj)
    search = Searcher('test.db', voc)
    q = '../../data/features/bench/sift/step10/ukbench00052.npy'
    print('try a query...')
    result = search.query((q,))
    for r in result[:20]:
        print(r)


if __name__ == "__main__":
    # create_db_test()
    # search_test()
    search_test_imquery()
