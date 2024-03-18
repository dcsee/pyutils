package main

import (
	"bytes"
	"encoding/json"
	"io/fs"

	"github.com/montanaflynn/stats"

	"bufio"
	"fmt"
	"os"
	"strconv"
	"strings"
)

var files = map[int]string{
	0: "C:/Users/ravi_/workspace/Tasks/SW-4_Weight_Cell_Leak_Detection/readings/300mls plus 0, 0, 1.txt",
	1: "C:/Users/ravi_/workspace/Tasks/SW-4_Weight_Cell_Leak_Detection/readings/300mls plus 1, 0, 1.txt",
	2: "C:/Users/ravi_/workspace/Tasks/SW-4_Weight_Cell_Leak_Detection/readings/300mls plus 2, 0, 1.txt",
	5: "C:/Users/ravi_/workspace/Tasks/SW-4_Weight_Cell_Leak_Detection/readings/300mls plus 5, 0, 1.txt",
}

const targetDir = "C:/Users/ravi_/workspace/Tasks/SW-4_Weight_Cell_Leak_Detection/readings/analysis"

func readFileData(path string) []float64 {
	file, err := os.Open(path)
	if err != nil {
		panic(err)
	}
	defer file.Close()

	// iterate over each line of the file
	values := []float64{}
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := scanner.Text()
		if !strings.Contains(line, "Weight= ") {
			continue
		}
		lineSplit := strings.Split(line, " ")
		weight, err := strconv.ParseFloat(strings.TrimSpace(lineSplit[len(lineSplit)-1]), 64)
		if err != nil {
			panic(err)
		}
		values = append(values, weight)
	}

	if err := scanner.Err(); err != nil {
		panic(err)
	}

	return values
}

type Stats struct {
	Drift          float64   `json:"drift"`
	DriftPerMinute float64   `json:"driftPerMinute"`
	FirstMinuteAvg float64   `json:"firstMinuteAvg"`
	LastMinuteAvg  float64   `json:"lastMinuteAvg"`
	MaxValue       float64   `json:"largestValue"`
	Mean           float64   `json:"mean"`
	MinValue       float64   `json:"smallestValue"`
	Name           string    `json:"name"`
	RawData        []float64 `json:"-"`

	// Spread is the difference between the largest and smallest values
	// If positive, this means the spread is bigger than the weight under measure, i.e. the scale's
	// natural fluctuations are larger than the weight we're looking for, and hence the weight
	// cannot be reliably seen.
	// If negative, this means the weight is larger than the spread, and hence the weight can be seen.
	// If it's exactly -1*WeightUnderMeasure, this means the spread is always zero (unlikely) and the
	// weight can be perfectly detected.
	// Smaller is better.
	Spread             float64 `json:"spread"`
	StandardDeviation  float64 `json:"standardDeviation"`
	WeightUnderMeasure int     `json:"weight"`
}

type WeightStats struct {
	Stats
	HalfSpreadPct float64 `json:"halfSpreadPct"`
	// StdWeightPct is the standard deviation as a percent of weight under measure.
	// Smaller is better, 0 is as good as it gets.
	StdWeightPct     float64 `json:"stdWeightPct"`
	ProjectedGain45m float64 `json:"projectedGain"`
	ProjectedGainPct float64 `json:"projectedGainPct"`
}

func (ws *WeightStats) makeName() string {
	return fmt.Sprintf("%dg stats", ws.WeightUnderMeasure)
}

func writeAnalysis(ws any, name string) {
	jsBytes, err := json.MarshalIndent(&ws, "", "    ")
	if err != nil {
		panic(err)
	}

	fmt.Printf("About to write file for: %s\n", name)
	err = os.WriteFile(
		fmt.Sprintf("%s/%s.json", targetDir, name),
		jsBytes,
		fs.FileMode(os.O_CREATE))
	if err != nil {
		panic(err)
	}
}

type DiffStats struct {
	Stats

	// MeanDiffZeroToCurrent is the difference between the mean of the 0g raw stats, and the additional weight
	// associated with this stats object
	MeanDiffZeroToCurrent float64 `json:"differenceInMeans"`
}

func makeStats(rawData []float64, weight int) Stats {
	fma, err := stats.Mean(stats.Float64Data(rawData[0:60]))
	if err != nil {
		panic(err)
	}

	lma, err := stats.Mean(stats.Float64Data(rawData[len(rawData)-61 : len(rawData)-1]))
	if err != nil {
		panic(err)
	}

	stdv, err := stats.StandardDeviation(stats.Float64Data(rawData))
	if err != nil {
		panic(err)
	}

	mean, err := stats.Mean(stats.Float64Data(rawData))
	if err != nil {
		panic(err)
	}

	max, err := stats.Max(stats.Float64Data(rawData))
	if err != nil {
		panic(err)
	}

	min, err := stats.Min(stats.Float64Data(rawData))
	if err != nil {
		panic(err)
	}

	s := Stats{
		Drift:              lma - fma,
		DriftPerMinute:     ((lma - fma) / (float64(len(rawData)))) * 60,
		FirstMinuteAvg:     fma,
		LastMinuteAvg:      lma,
		MaxValue:           max,
		Mean:               mean,
		RawData:            rawData,
		MinValue:           min,
		StandardDeviation:  stdv,
		WeightUnderMeasure: weight,
	}
	s.Spread = s.MaxValue - s.MinValue
	return s
}

func makeWeightStats(rawData []float64, weight int) WeightStats {
	ws := WeightStats{
		Stats: makeStats(rawData, weight),
	}
	ws.Spread = ws.MaxValue - ws.MinValue
	if ws.WeightUnderMeasure != 0 {
		ws.StdWeightPct = 100 * (ws.StandardDeviation / float64(ws.WeightUnderMeasure))
		ws.HalfSpreadPct = 100 * ((ws.Spread / 2) / float64(weight))
		ws.ProjectedGain45m = 45 * ws.DriftPerMinute
		ws.ProjectedGainPct = 100 * (ws.ProjectedGain45m / float64(weight))
	}

	ws.Name = ws.makeName()

	return ws
}

func makeDiffStats(rawData []float64, refMean float64, cmpMean float64, weight int) DiffStats {
	ws := DiffStats{
		Stats: makeStats(rawData, weight),
	}
	ws.MeanDiffZeroToCurrent = cmpMean - refMean

	return ws
}

func writeCsv(title, header string, values []float64) {
	fileName := fmt.Sprintf("%s/%s.csv", targetDir, title)
	buf := bytes.NewBuffer([]byte(fmt.Sprintf("%s,\n", header)))

	for _, val := range values {
		buf.Write([]byte(fmt.Sprintf("%s,\n", strconv.FormatFloat(val, 'f', 4, 64))))
	}

	err := os.WriteFile(fileName, buf.Bytes(), fs.FileMode(os.O_CREATE))
	if err != nil {
		panic(err)
	}
}

func analyzeDifference(ref, cmp WeightStats) {
	smallerLen := len(cmp.RawData)
	if len(ref.RawData) < len(cmp.RawData) {
		smallerLen = len(ref.RawData)
	}

	difference := make([]float64, smallerLen)
	i := 0
	for i < smallerLen {
		difference[i] = cmp.RawData[i] - ref.RawData[i]
		i++
	}

	wsDiff := makeDiffStats(difference, ref.Mean, cmp.Mean, cmp.WeightUnderMeasure)
	wsDiff.Name = fmt.Sprintf("%dg minus %dg difference analysis", cmp.WeightUnderMeasure, ref.WeightUnderMeasure)

	writeAnalysis(wsDiff, wsDiff.Name)
	writeCsv(
		fmt.Sprintf("%dg minus %dg difference data 1 second timesteps 45min", cmp.WeightUnderMeasure, ref.WeightUnderMeasure),
		fmt.Sprintf("%dg-%dg reading difference for same timestep", cmp.WeightUnderMeasure, ref.WeightUnderMeasure),
		difference)
}

func main() {
	weightStats := []WeightStats{}
	weights := []int{0, 1, 2, 5}
	for _, w := range weights {
		contents := readFileData(files[w])
		weightStats = append(weightStats, makeWeightStats(contents, w))
	}

	for _, ws := range weightStats {
		writeAnalysis(ws, ws.Name)
		writeCsv(fmt.Sprintf("%dg data 1 second timesteps 45min", ws.WeightUnderMeasure), "weight", ws.RawData)
	}

	// compare difference between the 0g and 1g, write the difference csv
	analyzeDifference(weightStats[0], weightStats[1])

	// compare difference between the 0g and 2g, write the difference csv
	analyzeDifference(weightStats[0], weightStats[2])

	// compare difference between the 0g and 5g, write the difference csv
	analyzeDifference(weightStats[0], weightStats[3])
}

/*
What do I want to gather?

Per file:
- largest value
- smallest value
- average value
- median value
- standard deviation
- difference between largest and smallest values
- difference between (large - small) and weight under measure
- difference between standard deviation and weight under measure

Between files:
- difference per row (so, 0g at timestamp one - 1g at timestamp one, etc)
- that's it, just write to a csv
- then, for each of those, re-run the above file analysis

How am I representing my data?
- It's one-dimensional and I know the time steps are 1 second each, so I can just use arrays of float64
*/
