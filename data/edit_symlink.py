import os
from pathlib import Path


def main():
    replace_from = "ComicCluster/Comics"
    replace_to = "ComicCluster/data/Comics"
    comic_path = Path("Comics")
    for p in comic_path.glob("**/*ext"):
        sym_dst = str(p)
        sym_src = os.readlink(sym_dst)
        sym_src = sym_src.replace(replace_from, replace_to)
        p.unlink()
        os.symlink(sym_src, sym_dst)

    for p in comic_path.glob("**/*rivious"):
        sym_dst = str(p)
        sym_src = os.readlink(sym_dst)
        sym_src = sym_src.replace(replace_from, replace_to)
        p.unlink()
        os.symlink(sym_src, sym_dst)


if __name__ == "__main__":
    main()
