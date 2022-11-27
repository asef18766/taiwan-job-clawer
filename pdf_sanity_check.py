from os import listdir
from os.path import isdir
from typing import List
import argparse

def dfs_listdir(path:str)->List[str]:
    res = []
    for p in listdir(path):
        target = f"{path}/{p}"
        if isdir(target):
            res += dfs_listdir(target)
        else:
            if p.endswith(".pdf"):
                res.append(target)
    return res
            
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("work_dir", help="working directory, usually the month folder")
    args = parser.parse_args()
    for i in dfs_listdir(args.work_dir):
        with open(i, "rb") as fp:
            if fp.read(4) != b"%PDF":
                print(f"detect invailed pdf {i}")

if __name__ == "__main__":
    main()