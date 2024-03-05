import json
import os
import sys
from pathlib import Path

def shouldCopy(item, files):
    return (len(files) == 1 and files[0] == "*") or (item in files)

def copyAll(source, dest, files):
    for item in os.listdir(source):
        s = f"{source}/{item}"
        if os.path.isfile(s) and shouldCopy(item, files):
            Path(dest).mkdir(exist_ok=True)
            d = f"{dest}/{item}"
            print(f"copying:\n\t{s}\nto\n\t{d}\n")
            os.rename(s, d)

def main(args):
    with open("./master.json") as f:
        configs = json.load(f)
        print(configs)

        for c in configs:
            copyAll(c['source'], c['dest'], c['files'])

main(sys.argv)