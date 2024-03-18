import os
import time
import webbrowser

def main():
    targetdir="C:/Users/ravi_/workspace/source/MeniscusTrackingFork/MeniscusTrackingTests/TestData/TestOutput"

    for item in os.listdir(targetdir):
        s = f"{targetdir}/{item}"
        if os.path.isdir(s):
            webbrowser.open(f"{s}/drawing.jpg")
            time.sleep(1)

            
main()