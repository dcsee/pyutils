import os
import json

def main():
    targetdir="C:/Users/ravi_/workspace/source/MeniscusTrackingFork/MeniscusTrackingTests/TestData"
    with open(f"./rename.json") as case_file:
        cases = json.load(case_file)

        for case in cases:
            with open(f"{targetdir}/{case}/benchmarks.json") as benchmarks_file:
                benchmarks = json.load(benchmarks_file)
                rotor_top = benchmarks["RotorTopPxPos"]
                print(f"{case}: rotor_top={rotor_top}")
            
main()