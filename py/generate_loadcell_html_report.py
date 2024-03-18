import base64
import csv
import io
import json
import matplotlib.pyplot as plt
from matplotlib import collections  as mc

target_dir="C:/Users/ravi_/workspace/Tasks/SW-4_Weight_Cell_Leak_Detection/readings/analysis"
raw_stats = [
    {
        "title": "750ml Bottle + 300ml Water + 0g Mass, 45 Minutes",
        "path":    f"{target_dir}/0g stats.json",
        "datapath":    f"{target_dir}/0g data 1 second timesteps 45min.csv",
    },
    {
        "title": "750ml Bottle + 300ml Water + 1g Mass, 45 Minutes",
        "path":    f"{target_dir}/1g stats.json",
        "datapath":    f"{target_dir}/1g data 1 second timesteps 45min.csv",
    },
    {
        "title": "750ml Bottle + 300ml Water + 2g Mass, 45 Minutes",
        "path":    f"{target_dir}/2g stats.json",
        "datapath":    f"{target_dir}/2g data 1 second timesteps 45min.csv",
    },
    {
        "title": "750ml Bottle + 300ml Water + 5g Mass, 45 Minutes",
        "path":    f"{target_dir}/5g stats.json",
        "datapath":    f"{target_dir}/5g data 1 second timesteps 45min.csv",
    },
]
difference_stats = [
    {
        "title": "Per-Timestep Difference: 1g Minus 0g, 45 min",
        "path":    f"{target_dir}/1g minus 0g difference analysis.json",
        "datapath":    f"{target_dir}/1g minus 0g difference data 1 second timesteps 45min.csv",
    },
    {
        "title": "Per-Timestep Difference: 2g Minus 0g, 45 min",
        "path":    f"{target_dir}/2g minus 0g difference analysis.json",
        "datapath":    f"{target_dir}/2g minus 0g difference data 1 second timesteps 45min.csv",
    },
    {
        "title": "Per-Timestep Difference: 5g Minus 0g, 45 min",
        "path":    f"{target_dir}/5g minus 0g difference analysis.json",
        "datapath":    f"{target_dir}/5g minus 0g difference data 1 second timesteps 45min.csv",
    },
]

totalAvgDrift = 0
avgHalfSpreads = 0

'''
What I want to report:
The raw stats of 0, 1, 2, and 5g
Differences in mean value between 0-1, 0-2, and 0-5g
- will require updating the Go code to add this to the diff objects
- also update that struct type, make a new struct for the diff and break out the shared fields into an embeddable struct
Raw stats of each "difference" json excluding weight, SpreadWeightDifference, and stdWeightPct as those are meaningless. Remember these represent the row-wise differences between each dataset at same timestamp.
Graphs of each csv file
'''

def make_instructions():
    return '''
        <div style="clear: both; margin-bottom: 10px; border: 1px solid black">
            <div style="float: left; padding-left: 10px">
                <h4>Overview</h4>
                    <p>
                        A 750ml bottle containing 300mls of water was placed on the Proto6 2kg load cell.<br>
                        Mass measurements were collected once per second over a period of 45 minutes, with no additional mass added. This is referred to as the "0g" dataset.<br>
                        Measurement was repeated using the same bottle with the addition of 1g, 2g, and 5g masses, producing four original datasets.<br>
                        Subsequently, the difference between each of the following datasets was computed: 5g - 0g, 2g - 0g, 1g - 0g. This produced an additional three derived datasets, resulting in seven total datasets.<br>
                        Each of the seven datasets is analyzed below.<br>
                        Note: trendlines are calculated by plotting the line segment connecting the average of the first 60 measurements with the average of the last 60 measurements.<br>
                    </p>
                <h4>Summary</h4>
                    <p>
                        It appears that the 2kg load cell <i>does</i> offer the resolution we need to identify the addition of 1g of fluid.
                        Standard deviation in raw measurement is never more than 7% of added mass and decreases as added mass increases (good!).<br>
                        The scale <i>does also</i> exhibit measurable positive drift over the 45 minute period. However, this drift is small: apparent mass gain is under 9% of added mass over a 45-minute period.<br>
                        "Drift" refers to the slope of the line connecting the average mass of the first 60 measurements to the average mass of the last 60 measurements.<br>
                        Average drift was found to be {d}g/min across the four original datasets. Drift from the three derived datasets was not included.<br>
                        This amounts to a total of {d45}g increase in apparent scale mass over a 45-minute protocol run, or a ~{d450}g increase over ten such runs.<br>
                    </p>
            </div>
        </div>
    '''.format(d=round(totalAvgDrift/4, 4), d45=round(45*(totalAvgDrift/4), 4), d450=round(450*(totalAvgDrift/4), 1))

def make_chart(data_path, data_name, stat):
    img_path = f"{target_dir}/{data_name}_plot.png"
    with open(data_path) as f:
        # read the data out of the csv file, skipping the header
        reader = csv.reader(f)
        next(reader, None)
        data = [float(row[0]) for row in reader]

        # create the plot object
        figure, axis = plt.subplots()

        # add a line segment denoting the average trendline
        trendline = [[(30, stat["firstMinuteAvg"]), (len(data) - 30, stat["lastMinuteAvg"])]]
        lc = mc.LineCollection(trendline, colors=[(0, 0.9, 0.9, 1)], linewidths=2)
        axis.add_collection(lc)

        # add the points as a scatter plot
        xaxis = [i for i in range(0, len(data))]
        axis.scatter(xaxis, data)
        axis.set_xlabel("timesteps (seconds)")
        axis.set_ylabel(data_name)
        axis.set_title(f"{data_name} vs Time (seconds)")
        figure.tight_layout()

        # save the plot to a file
        plt.savefig(img_path, format='png')

    with open(img_path, 'rb') as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

def make_stat_diff(stat):
    return '''
        <p>Ideally, the Max, Min, Mean, and Difference in Means should all be {w}g.</p>
        <ul>
            <li>Drift, per minute: {avgdrift}g/min</li>
            <li>Standard Deviation: {std}g</li>
            <li>Drift, absolute (Mean Val, First Minute - Mean Val, Last Minute): {drift}g</li>
            <li>Mean val, First Minute: {fma}g</li>
            <li>Mean val, Last Minute: {lma}g</li>
            <li>Max Per-Row Difference: {max}g</li>
            <li>Min Per-Row Difference: {min}g</li>
            <li>Mean of Each Per-Row Difference: {mean}g</li>
            <li>Spread (difference between Max and Min): {max} - {min} = {spread}g</li>
            <li>Difference Between {w}g and 0g Means: = {wdff}g</li>
        </ul>
    '''.format(
        w=round(stat["weight"], 4),
        max=round(stat["largestValue"], 4),
        min=round(stat["smallestValue"], 4),
        mean=round(stat["mean"], 4),
        std=round(stat["standardDeviation"], 4),
        spread=round(stat["spread"], 4),
        wdff=round(stat["differenceInMeans"], 4),
        drift=round(stat["drift"], 4),
        avgdrift=round(stat["driftPerMinute"], 4),
        fma=round(stat["firstMinuteAvg"], 4),
        lma=round(stat["lastMinuteAvg"], 4),
    )

def make_stat_raw(stat):
    global totalAvgDrift
    totalAvgDrift = totalAvgDrift + round(stat["driftPerMinute"], 4)
    return '''
        <ul>
            <li>Added Mass Under Measure: {w}g</li>
            <li>Standard Deviation as Pct of Added Mass: {stdff}</li>
            <li>Drift, per minute: {avgdrift}g/min</li>
            <li>Standard Deviation: {std}g</li>
            <li>Drift, absolute (Mean Val, First Minute - Mean Val, Last Minute): {drift}g</li>
            <li>Mean val, First Minute: {fma}g</li>
            <li>Mean val, Last Minute: {lma}g</li>
            <li>Max Value: {max}g</li>
            <li>Min Value: {min}g</li>
            <li>Mean Value: {mean}g</li>
            <li>Spread (difference between Max and Min): {max} - {min} = {spread}g</li>
            <li>1/2 of Spread as Pct of Mass Under Measure: {hsp}</li>
            <li>Projected Apparent Mass Gain after 45m (45*Drift per min): {pg}</li>
            <li>Projected Gain as Percent of Mass: {ppg}</li>
        </ul>
    '''.format(
        w=round(stat["weight"], 4),
        max=round(stat["largestValue"], 4),
        min=round(stat["smallestValue"], 4),
        mean=round(stat["mean"], 4),
        std=round(stat["standardDeviation"], 4),
        spread=round(stat["spread"], 4),
        stdff=str(round(stat["stdWeightPct"], 2)) + "%" if stat["stdWeightPct"] != 0 else "n/a",
        drift=round(stat["drift"], 4),
        avgdrift=round(stat["driftPerMinute"], 4),
        fma=round(stat["firstMinuteAvg"], 4),
        lma=round(stat["lastMinuteAvg"], 4),
        hsp=str(round(stat["halfSpreadPct"], 2)) + "%" if stat["halfSpreadPct"] != 0 else "n/a",
        pg=str(round(stat["projectedGain"], 2)) + "g" if stat["projectedGain"] != 0 else "n/a",
        ppg=str(round(stat["projectedGainPct"], 2)) + "%" if stat["projectedGainPct"] != 0 else "n/a",
    )

def make_body_snippet(case_title, data_path, stat, statfn):
    return '''
        <div style="float: left; clear: both; margin-bottom: 10px; border: 1px solid black">
            <div style="float: left; padding-right: 20px"><img src="data:image/png;base64,{i}"></div>
            <div style="width: 1200px">
                <h4>{c}</h4>
                <div>{d}</div>
            </div>
        </div>
    '''.format(
        i=make_chart(data_path, case_title, stat),
        c=case_title,
        d=statfn(stat))

def main():
    body_snippets = [] 

    for stat in raw_stats:
        with open(stat["path"]) as f:
            body_snippets.append(
                make_body_snippet(stat["title"], stat["datapath"], json.load(f), make_stat_raw))

    for stat in difference_stats:
        with open(stat["path"]) as f:
            body_snippets.append(
                make_body_snippet(stat["title"], stat["datapath"], json.load(f), make_stat_diff))

    body_str = "\n".join(body_snippets)

    report_html = '''
        <html>
            <head></head>
            <body style="overflow-x: scroll">
                {i}
                {b}
            </body>
        </html>
    '''.format(i=make_instructions(), b=body_str)
    
    with open(f"{target_dir}/report.html", "w+") as report:
        report.write(report_html)

main()
