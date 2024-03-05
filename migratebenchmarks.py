import json

def main():
    targetdir="C:/Users/ravi_/workspace/source/MeniscusTrackingFork/MeniscusTrackingTests/TestData"

    with open("./rename.json") as casefile:
        cases = json.load(casefile)

        for case in cases:
            new_benchmarks = {}
            with open(f"{targetdir}/{case}/benchmarks.json", 'r') as old_benchmarks_file:
                old_benchmarks = json.load(old_benchmarks_file)
                new_benchmarks["RotorSteps"] = old_benchmarks["RotorSteps"]
                new_benchmarks["RotorTopPxPos"] = old_benchmarks["Cases"]["0,0ml-1,0ml"]["Bottom"]
                new_benchmarks["Cases"] = {}

                for key, value in old_benchmarks["Cases"].items():
                    new_benchmarks["Cases"][key] = {
                        "CurrentMeniscus": value["Top"],
                        "FormerMeniscus": 0,
                    }
            with open(f"{targetdir}/{case}/benchmarks.json", 'w') as old_benchmarks_file:
                json.dump(new_benchmarks, old_benchmarks_file)
            
            print(f"done updating benchmarks file for case {case}")

            
main()