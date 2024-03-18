import csv
import cv2 as cv
import json
import matplotlib.pyplot as plt
import numpy
#import statistics

targetdir = "C:/Users/ravi_/workspace/source/MeniscusTrackingFork/MeniscusTrackingTests/TestData"
IMG_HEIGHT = 267
IMG_WIDTH = 154

class ImgStats:
    def __init__(self, case, sample_vol):
        self.case = case
        self.sample_vol = sample_vol
        self.analyze()
        return

    def make_path(self):
        return f"{targetdir}/{self.case}/{self.sample_vol}.bmp"

    def preprocess(self):
        img = cv.imread(self.make_path())
        img_gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        chamber_roi = img_gray[111:(111+IMG_HEIGHT), 244:(244+IMG_WIDTH)]
        return chamber_roi
    
    def find_row_brightnesses(self, img):
        return [sum(row) for row in img]

    def find_row_stdevs(self, img):
        return [numpy.std(row) for row in img]

    def find_max_min_with_idx(self, items, cmp):
        max_or_min = [0, items[0]]

        for i in range(0, len(items)):
            item = items[i]
            if cmp(item, max_or_min[1]):
                max_or_min[0] = i
                max_or_min[1] = item

        return max_or_min

    def find_pct_of_range(self, item, low_bound, high_bound):
        return round(100*((item - low_bound)/(high_bound - low_bound)), 4)

    def find_devns_from_mean(self, items):
        m = numpy.mean(items)
        stdev = numpy.std(items)
        return [round((item - m) / stdev, 4) for item in items]

    def find_pct_dst(self, items):
        return [10*int(item / 10) for item in items]

    def find_coeff_var(self, img):
        return [round(numpy.std(row) / numpy.mean(row), 5) for row in img]

    def analyze(self):
        self.cropped_img_gray = self.preprocess()

        # total brightness of each row
        # a list of the brightnesses of each row from 0 to 267
        self.sum_btnss_per_row = self.find_row_brightnesses(self.cropped_img_gray)

        # stdv of each row
        self.stdev_per_row = self.find_row_stdevs(self.cropped_img_gray)

        # coefficient of variation
        self.row_cvar = self.find_coeff_var(self.cropped_img_gray)

        # find max and min brightnesses and stdevs
        # each is returned as a tuple of (index, value)
        self.max_btnss = self.find_max_min_with_idx(self.sum_btnss_per_row, lambda x, y: x > y)
        self.min_btnss = self.find_max_min_with_idx(self.sum_btnss_per_row, lambda x, y: x < y)
        self.max_stdev = self.find_max_min_with_idx(self.stdev_per_row, lambda x, y: x > y)
        self.min_stdev = self.find_max_min_with_idx(self.stdev_per_row, lambda x, y: x < y)
        self.max_cvar = self.find_max_min_with_idx(self.row_cvar, lambda x, y: x > y)
        self.min_cvar = self.find_max_min_with_idx(self.row_cvar, lambda x, y: x < y)

        # brightness of each row as % of total brightness range
        self.row_pct_btnss = [self.find_pct_of_range(rsum, self.min_btnss[1], self.max_btnss[1])
                                     for rsum in self.sum_btnss_per_row]

        # stdv of each row as % of total stdev range
        self.row_pct_stdevs = [self.find_pct_of_range(rstdev, self.min_stdev[1], self.max_stdev[1])
                                     for rstdev in self.stdev_per_row]

        # coefficient of variation of each row as % of total coefficient variation range
        self.row_pct_cvar = [self.find_pct_of_range(rcvar, self.min_cvar[1], self.max_cvar[1])
                                     for rcvar in self.row_cvar]
        print(self.row_pct_cvar)
        # deviation from the mean of all row brightnesses of each row's summed brightnes
        self.btnss_devns_from_mean_btnss = self.find_devns_from_mean(self.sum_btnss_per_row)

        # deviation from the mean of all row stdevs of each row's stdev
        self.stdevs_devns_from_mean_stdev = self.find_devns_from_mean(self.stdev_per_row)

        # percentile distribution of all row brightnesses in buckets of 10%
        self.pct_dstbn_btnss = self.find_pct_dst(self.row_pct_btnss)

        # percentile distribution of all row stdvs in buckets of 10%
#        print(self.row_pct_stdevs)
        self.pct_dstbn_stdev = self.find_pct_dst(self.row_pct_stdevs)
#        print(self.pct_dst_stdev)

        self.save_all_plots()

        cv.imshow("Display window", self.cropped_img_gray)
        k = cv.waitKey(2500)
        return

    # plot all stats with row number as Y axis and value as X axis
    def save_all_plots(self):
        sets_to_plot = [
            ("Row Vertical Offset from Img Bottom (px)", "Row Brightness (0-255)", "Brightness per Row", self.sum_btnss_per_row),
            ("Row Vertical Offset from Img Bottom (px)", "Row Brightness Pct (%)", "Row Brightness as Percent of All Row Brightnesses Range", self.row_pct_btnss),
            ("Row Vertical Offset from Img Bottom (px)", "Row Coefficient of Variation", "Coefficient of Variation per Row", self.row_cvar),
            ("Row Vertical Offset from Img Bottom (px)", "Row Coefficient of Variation %", "Row Coefficient of Variation as Percent of Coefficient of Variation Range", self.row_pct_cvar),
#            ("Row Vertical Offset from Img Bottom (px)", "Row Stdev (0-255)", "Standard Deviation per Row", self.stdev_per_row),
#            ("Row Vertical Offset from Img Bottom (px)", "Row Stdev Pct (%)", "Row Standard Deviation as Percent of Standard Deviation Range", self.row_pct_stdevs),
#            ("Row Vertical Offset from Img Bottom (px)", "Row Cvar Pct (%)", "Row Coefficient of Variation as Percent of Coefficient of Variation Range", self.row_pct_cvar),
#            ("Row Vertical Offset from Img Bottom (px)", "Row Brightness Devs (dvs)", "Row Brightness Deviations from Mean of All Row Brightnesses", self.btnss_devns_from_mean_btnss),
#            ("Row Vertical Offset from Img Bottom (px)", "Row Stdev Devs (dvs)", "Row Stdev Deviations from Mean of All Row Stdevs", self.stdevs_devns_from_mean_stdev),
#            ("Row Vertical Offset from Img Bottom (px)", "Row Brightness Percentile", "Row Brightness Percentile in Buckets of 10%", self.pct_dstbn_btnss),
#            ("Row Vertical Offset from Img Bottom (px)", "Row Stdev Percentile", "Row Stdev Percentile in Buckets of 10%", self.pct_dstbn_stdev),
        ]

        img_height = len(self.cropped_img_gray)
        yaxis = [-1*(i-250) for i in range(0, img_height)]
        for s in sets_to_plot:
            figure, axis = plt.subplots()
            axis.scatter(s[3], yaxis)
            axis.set_xlabel(s[1])
            axis.set_ylabel(s[0])
            axis.set_title(s[2])
            figure.tight_layout()
        
        plt.show()
        
        return

class MetaAnalysis:
    def __init__(self, sample):
        self.sample = sample
        self.sum_btnss_per_row_meta = []
        self.stdev_per_row_meta = []
        self.row_pct_btnss_meta = []
        self.row_pct_stdevs_meta = []
        self.btnss_devns_from_mean_btnss_meta = []
        self.stdevs_devns_from_mean_stdev_meta = []
        self.pct_dstbn_btnss_meta = []
        self.pct_dstbn_stdev_meta = []
        return

    def get_name(self):
        return f"meta_analysis_{self.sample}"

    def analyze(self, img_stats):
        for i in range(0,IMG_HEIGHT):
            self.sum_btnss_per_row_meta.append([])
            self.stdev_per_row_meta.append([])
            self.row_pct_btnss_meta.append([])
            self.row_pct_stdevs_meta.append([])
            self.btnss_devns_from_mean_btnss_meta.append([])
            self.stdevs_devns_from_mean_stdev_meta.append([])
            self.pct_dstbn_btnss_meta.append([])
            self.pct_dstbn_stdev_meta.append([])
            
            for stat in img_stats:
                self.sum_btnss_per_row_meta[i].append(stat.sum_btnss_per_row[i])
                self.stdev_per_row_meta[i].append(stat.stdev_per_row[i])
                self.row_pct_btnss_meta[i].append(stat.row_pct_btnss[i])
                self.row_pct_stdevs_meta[i].append(stat.row_pct_stdevs[i])
                self.btnss_devns_from_mean_btnss_meta[i].append(stat.btnss_devns_from_mean_btnss[i])
                self.stdevs_devns_from_mean_stdev_meta[i].append(stat.stdevs_devns_from_mean_stdev[i])
                self.pct_dstbn_btnss_meta[i].append(stat.pct_dstbn_btnss[i])
                self.pct_dstbn_stdev_meta[i].append(stat.pct_dstbn_stdev[i])
        
        with open(f"{targetdir}/{self.get_name()}.csv", "w", newline='') as report:
            fieldnames = [
                'Row Brightness: Stdev',
                'Row Stdev: Stdev',
                'Row Brightness as Pct of All Row Brightnesses Range: Stdev',
                'Row Stdev as Pct of All Row Stdevs Range: Stdev',
                'Row Brightness Devs from Mean of All Row Brightnesses: Stdev',
                'Row Stdev Devs from Mean of All Row Stdevs: Stdev',
                'Row Brightness Percentile Distribution in Buckets of 10%: Stdev',
                'Row Stdev Percentile Distribution in Buckets of 10%: Stdev',
            ]

            writer = csv.writer(report)
            writer.writerow(fieldnames)

            for i in range(0,IMG_HEIGHT):
                writer.writerow([
                    round(numpy.std(self.sum_btnss_per_row_meta[i]), 4),
                    round(numpy.std(self.stdev_per_row_meta[i]), 4),
                    round(numpy.std(self.row_pct_btnss_meta[i]), 4),
                    round(numpy.std(self.row_pct_stdevs_meta[i]), 4),
                    round(numpy.std(self.btnss_devns_from_mean_btnss_meta[i]), 4),
                    round(numpy.std(self.stdevs_devns_from_mean_stdev_meta[i]), 4),
                    round(numpy.std(self.pct_dstbn_btnss_meta[i]), 4),
                    round(numpy.std(self.pct_dstbn_stdev_meta[i]), 4)
                ])


def main():
#    samples = ["0,0ml", "1,0ml", "2,0ml"]
    samples = ["1,0ml"]
    all_stats = {
#        "0,0ml": [],
        "1,0ml": [],
#        "2,0ml": [],
    }
    
    with open("./rename.json") as casefile:
        cases = json.load(casefile)

        for sample in samples:
            for case in cases:
                s = ImgStats(case, sample)
                all_stats[sample].append(s)
                break

    for sample in samples:
        break
        m = MetaAnalysis(sample)
        m.analyze(all_stats[sample])

main()