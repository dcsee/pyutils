import json
import shutil

def main():
    targetdir="C:/Users/ravi_/workspace/source/MeniscusTrackingFork/MeniscusTrackingTests/TestData"
    with open("./rename.json") as casefile:
        cases = json.load(casefile)

        for case in cases:
            shutil.copyfile(
                "C:/Users/ravi_/workspace/source/MeniscusTrackingFork/MeniscusTrackingTests/TestData/Eth78kDfCnstOnRotor/benchmarks.json",
                f"{targetdir}/{case}/benchmarks.json")
            
main()