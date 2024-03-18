import json
import os

translation = {
    0: "0,0",
    1: "0,5",
    2: "1,0",
    3: "1,5",
    4: "2,0"
}

def main():
    targetdir="C:/Users/ravi_/workspace/source/MeniscusTrackingFork/MeniscusTrackingTests/TestData"
    with open("./rename.json") as casefile:
        cases = json.load(casefile)

        for case in cases:
            count = 0
            casedir = f"{targetdir}/{case}"
            images = [f"{casedir}/{image}" for image in os.listdir(casedir)]
            images.sort(key=os.path.getmtime)
            for image in images:
                os.rename(image, f"{targetdir}/{case}/{translation[count]}ml.bmp")
                count = count + 1

main()