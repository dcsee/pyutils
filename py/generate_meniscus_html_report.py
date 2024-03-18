import base64
import csv
import os
import statistics

targetdir="C:/Users/ravi_/workspace/source/MeniscusTrackingFork/MeniscusTrackingTests/TestData"

pass_threshold = 5
menisciiFound = 0
menisciiFails = 0
menisciiPctErrs = []
rotorFound = 0
rotorFails = 0
rotorPctErrs = []

def make_instructions():
    return '''
        <div style="clear: both; overflow: auto; margin-bottom: 10px; border: 1px solid black">
            <div style="float: left; padding-left: 10px">
                <h4>Reading the Report</h4>
                <h4>Reading the Illustrations</h4>
                    <p>
                        The green line is the location of the meniscus as calculated by the Meniscus Tracker.<br>
                        The long red dot is the actual location of the meniscus, as measured by hand.<br>
                        The yellow line is the expected location of the rotor, as calculated by the Meniscus Tracker from a given, absolute number of stepper-motor steps.<br>
                        The short red dot is the actual location of the rotor top as measured by hand.<br>
                        In the case titles, "55k" and "68k" refer to the rotor position in stepper-motor steps. 55k is 55,000 steps.
                    </p>
                <h4>Error Reporting</h4>
                <p>
                    Meniscus Percent Error and Rotor Percent Error are both measured as follows:<br>
                    <b>100 * (Actual Location - Calculated Location) / Total Image Height</b><br?
                    Error is measured as a percentage of image height in order to prevent distortions in the error calculation resulting from a pixel position being closer to or further from the top of the image.<br>
                    Thus, the maximum possible error is 100%; this would occur if the meniscus were expected to be at the bottom of the image, but was incorrectly measured to be at the top of the image.<br>
                    An image is considered <i>passing</i> if its Meniscus Percent Error is less than 5%.
                </p>
            </div>
        </div>
    '''

def make_summary():
    mSuccessRate = round(100*float(menisciiFound / (menisciiFound+menisciiFails)))
    mFailRate = round(100.0 - mSuccessRate)
    rSuccessRate = round(100*float(rotorFound / (rotorFound+rotorFails)))
    rFailRate = round(100.0 - rSuccessRate)
    return '''
        <div style="clear: both; overflow: auto; margin-bottom: 10px; border: 1px solid black">
            <div style="float: left; padding-left: 10px">
                <h4>Summary</h4>            
                <ul>
                    <li>{mf} of {mt} meniscii found, {mm} meniscii missed</li>
                    <li>Meniscus success rate: <b>{msr}%</b></li>
                    <li>Meniscus miss rate: <b>{mfr}%</b></li>
                    <li>{rf} of {rt} rotors found, {rm} rotors missed</li>
                    <li>Rotor success rate: <b>{rsr}%</b></li>
                    <li>Rotor miss rate: <b>{rfr}%</b></li>                    
                    <li>Mean meniscus percent error: {mavg}%</li>
                    <li>Mean rotor percent error: {ravg}%</li>
                </ul>
            </div>
        </div>
    '''.format(
            mf=menisciiFound,
            mt=menisciiFound+menisciiFails,
            mm=menisciiFails,
            msr=mSuccessRate,
            mfr=mFailRate,
            rf=rotorFound,
            rt=rotorFound+rotorFails,
            rm=rotorFails,
            rsr=rSuccessRate,
            rfr=rFailRate,
            ravg=round(statistics.mean(rotorPctErrs)),
            mavg=round(statistics.mean(menisciiPctErrs)),
        )

def isPassFail(pct):
    pf = abs(float(pct[:-1]))
    global menisciiPctErrs
    menisciiPctErrs.append(pf)
    
    if pf > pass_threshold:
        global menisciiFails
        menisciiFails = menisciiFails + 1
        return '''
            <span style="color: red"><b>FAIL</b></span>, Meniscus Percent Error >{th}%
        '''.format(th=pass_threshold)
    else:
        global menisciiFound
        menisciiFound = menisciiFound + 1
        return '''<span style="color: green"><b>PASS</b></span>, meniscus found with error <{th}%'''.format(th=pass_threshold)

def isRotorFound(pct):
    pf = abs(float(pct[:-1]))
    global rotorPctErrs
    rotorPctErrs.append(pf)
    
    if pf > pass_threshold:
        global rotorFails
        rotorFails = rotorFails + 1
        return '''
            <span style="color: red"><b>Rotor not found</b></span>, Rotor Percent Error >{th}%
        '''.format(th=pass_threshold)
    else:
        global rotorFound
        rotorFound = rotorFound + 1
        return '''<span style="color: green"><b>Rotor found</b></span>, rotor error <{th}%'''.format(th=pass_threshold)

def read_results_file():
    results_by_title = {}
    with open(f"{targetdir}/TestOutput/allResults.csv") as csvfile:
        reader = csv.reader(csvfile)
        # skip the header
        next(reader, None)
        for row in reader:
            results_by_title[row[0]] = {
                "idMeniscus": row[2],
                "bMeniscus": row[3],
                "mPctErr": row[4],
                "idRotor": row[5],
                "bRotor": row[6],
                "rPctErr": row[7],
            }
    return results_by_title

def make_data(result):
    return '''
        <ul>
            <li>Identified Meniscus: {im} pixels</li>
            <li>Benchmark Meniscus: {bmn} pixels</li>
            <li>Meniscus Percent Error: {mp}</li>
            <li>Identified Rotor Top: {ir} pixels</li>
            <li>Benchmark Rotor Top: {br} pixels</li>
            <li>Rotor Percent Error: {rp}</li>
            <li>{passFail}</li>
            <li>{rotorFound}</li>
        </ul>
    '''.format(
        im=result["idMeniscus"],
        bmn=result["bMeniscus"],
        mp=result["mPctErr"],
        ir=result["idRotor"],
        br=result["bRotor"],
        rp=result["rPctErr"],
        passFail=isPassFail(result["mPctErr"]),
        rotorFound=isRotorFound(result["rPctErr"])
    )
def make_description(case_title, results_by_title):
    return '''
        <div style="float: left; padding-left: 10px">
            <h4>{c}</h4>
            {d}
        </div>
    '''.format(c=case_title, d=make_data(results_by_title[case_title.replace(",","")]))

def make_body_snippet(img_path, case_title, results_by_title):
    img_data = base64.b64encode(open(img_path, 'rb').read()).decode('utf-8')
    return '''
        <div style="clear: both; height: 267px; margin-bottom: 10px; border: 1px solid black">
            <img src="data:image/png;base64,{i}" style="float: left">
            {t}
        </div>
    '''.format(i=img_data, t=make_description(case_title, results_by_title))

def main():
    results_by_title = read_results_file()
    body_snippets = [] 

    for item in os.listdir(f"{targetdir}/TestOutput"):
        p = f"{targetdir}/TestOutput/{item}"
        if os.path.isdir(p):
            with open(f"{p}/note.txt") as case_notes:
                case_title = case_notes.readline()
                body_snippets.append({
                        "title": case_title,
                        "html": make_body_snippet(f"{p}/drawing.jpg", case_title, results_by_title)})

    body_snippets.sort(key = lambda s: s["title"])
    body_str = "\n".join([s["html"] for s in body_snippets])

    report_html = '''
        <html>
            <head></head>
            <body>
                {i}
                {s}
                {b}
            </body>
        </html>
    '''.format(i=make_instructions(), s=make_summary(), b=body_str)
    
    with open(f"{targetdir}/report.html", "w+") as report:
        report.write(report_html)

main()
