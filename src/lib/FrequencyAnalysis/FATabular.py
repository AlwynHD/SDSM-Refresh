import math
import datetime
import numpy as np
from collections import defaultdict

missingValue = -999
globalStartDate = datetime.date(1950, 1, 1)

def isLeapYear(year):
    return (year % 400 == 0) or (year % 4 == 0 and year % 100 != 0)

def getSeason(month):
    if month in (12, 1, 2):
        return 1  # Winter
    elif month in (3, 4, 5):
        return 2  # Spring
    elif month in (6, 7, 8):
        return 3  # Summer
    else:
        return 4  # Autumn

def doWeWantThisDatum(currentDate, dataPeriodChoice):
    """
    Filters data by month/season or “All Data” (annual).
    """
    if dataPeriodChoice.lower() in ["all data", "annual"]:
        return True
    monthsMap = {
        "january": 1, "february": 2, "march": 3, "april": 4,
        "may": 5, "june": 6, "july": 7, "august": 8,
        "september": 9, "october": 10, "november": 11, "december": 12
    }
    if dataPeriodChoice.lower() in monthsMap:
        return currentDate.month == monthsMap[dataPeriodChoice.lower()]
    if dataPeriodChoice.lower() == "winter":
        return getSeason(currentDate.month) == 1
    elif dataPeriodChoice.lower() == "spring":
        return getSeason(currentDate.month) == 2
    elif dataPeriodChoice.lower() == "summer":
        return getSeason(currentDate.month) == 3
    elif dataPeriodChoice.lower() == "autumn":
        return getSeason(currentDate.month) == 4
    return True

def readDailyDataDayByDay(filePath, fsDate, feDate, dataPeriodChoice,
                          applyThreshold, thresholdValue,
                          globalStartDate=globalStartDate,
                          isModelled=False, ensembleIndex=0):
    """
    Reads daily data from filePath.
    Skips missing/invalid lines, dates outside the analysis range, or values under threshold.
    """
    try:
        with open(filePath, 'r') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading {filePath}: {e}")
        return []
    
    dailyValues = []
    for i, line in enumerate(lines):
        line = line.rstrip("\n")
        currentDate = globalStartDate + datetime.timedelta(days=i)
        if currentDate < fsDate:
            continue
        if currentDate > feDate:
            break
        
        # For modelled data, support fixed-width extraction if needed.
        if isModelled and len(line) >= (ensembleIndex + 1) * 14:
            raw = line[ensembleIndex * 14:(ensembleIndex * 14) + 14]
        else:
            raw = line
        
        try:
            val = float(raw.strip())
        except:
            continue  # Skip non-numeric lines.
        
        if val == missingValue or (applyThreshold and val < thresholdValue):
            continue
        
        if doWeWantThisDatum(currentDate, dataPeriodChoice):
            dailyValues.append((currentDate, val))
    
    return dailyValues

def duration_to_int(d):
    """
    Map the return period label (a float) to a number of days (an integer).
    VB logic (as suggested by sample output):
      - If d < 1.5, use 1 day.
      - If d <= 2.5, use 2 days.
      - If d <= 3.5, use 3 days.
      - Otherwise, use floor(d).
    """
    if d < 1.5:
        return 1
    elif d <= 2.5:
        return 2
    elif d <= 3.5:
        return 3
    else:
        return int(math.floor(d))

def computeAnnualMaxSeries(dailyValues, duration):
    """
    Groups daily data by year and computes the maximum moving sum over N consecutive days.
    The number N is determined by duration_to_int.
    Returns a list of annual maxima.
    """
    d = duration_to_int(duration)
    
    yearMap = defaultdict(list)
    for dt, val in dailyValues:
        yearMap[dt.year].append(val)
        
    ams = []
    for year, values in yearMap.items():
        if len(values) < d:
            continue
        # Compute moving sum over d days.
        movingSums = [sum(values[i:i+d]) for i in range(len(values) - d + 1)]
        ams.append(max(movingSums))
    return ams

def computeFATableFromFiles(observedFilePath, modelledFilePath, fsDate, feDate,
                            dataPeriodChoice="All Data",
                            applyThreshold=False,
                            thresholdValue=0.0,
                            durations=[1.0, 1.1, 1.2, 1.3, 1.5, 2.0, 2.5, 3.0, 3.5],
                            ensembleIndex=0):
    """
    For each duration (return period label):
      - Reads observed and modelled daily data.
      - Computes the annual maximum series (AMS) using a moving sum over N days,
        where N is determined from the duration label.
      - Computes the central value (mean), lower (2.5% percentile), and upper (97.5% percentile)
        of the AMS across years using linear interpolation.
    Returns a dictionary with keys "observed" and "modelled", each a list of tuples (lower, central, upper).
    """
    dailyObs = readDailyDataDayByDay(observedFilePath, fsDate, feDate,
                                      dataPeriodChoice, applyThreshold, thresholdValue,
                                      isModelled=False)
    tableObs = []
    for dur in durations:
        amsObs = computeAnnualMaxSeries(dailyObs, dur)
        if amsObs:
            central = np.mean(amsObs)
            # Specify linear interpolation (adjust parameter name if using NumPy >= 1.22)
            lower = np.percentile(amsObs, 2.5, interpolation='linear')
            upper = np.percentile(amsObs, 97.5, interpolation='linear')
        else:
            central = lower = upper = 0.0
        tableObs.append((lower, central, upper))
    
    dailyMod = readDailyDataDayByDay(modelledFilePath, fsDate, feDate,
                                      dataPeriodChoice, applyThreshold, thresholdValue,
                                      isModelled=True, ensembleIndex=ensembleIndex)
    tableMod = []
    for dur in durations:
        amsMod = computeAnnualMaxSeries(dailyMod, dur)
        if amsMod:
            central = np.mean(amsMod)
            lower = np.percentile(amsMod, 2.5, interpolation='linear')
            upper = np.percentile(amsMod, 97.5, interpolation='linear')
        else:
            central = lower = upper = 0.0
        tableMod.append((lower, central, upper))
    
    return {"observed": tableObs, "modelled": tableMod}

def printFATabularOutput(tableDict, durations, obsFileName, modFileName,
                         lowerP=2.5, upperP=97.5, seasonText="Annual", fitType="Empirical"):
    """
    Prints the FA tabular output in the same style as the original VB app.
    Header includes Season, Fit, and file names.
    Then prints a table with columns:
       Return Period, Obs, Mod, 2.5 %ile, 97.5 %ile.
    """
    print(f"Season: {seasonText}")
    print(f"Fit: {fitType}")
    print(f"Observed data: {obsFileName}")
    print(f"Modelled data: {modFileName}")
    print()
    
    print("Return Period      Obs          Mod          2.5 %ile      97.5 %ile")
    print("-----------------------------------------------------------------------")
    
    for dur, obsTuple, modTuple in zip(durations, tableDict.get("observed", []), tableDict.get("modelled", [])):
        obsLower, obsCentral, obsUpper = obsTuple
        modLower, modCentral, modUpper = modTuple
        print(f"{dur:13.1f} {obsCentral:12.3f} {modCentral:12.3f} {obsLower:12.3f} {obsUpper:12.3f}")
    
    print("-----------------------------------------------------------------------")
    print()

if __name__ == "__main__":
    # Standalone testing with sample values matching your VB output sample.
    exampleObsTable = [
        (21.400, 41.000, 84.730),
        (21.400, 41.000, 84.730),
        (21.400, 41.000, 84.730),
        (21.400, 41.000, 84.730),
        (24.380, 51.604, 104.560),
        (24.380, 51.604, 104.560),
        (24.380, 51.604, 104.560),
        (29.840, 56.189, 104.560),
        (30.910, 60.258, 105.190)
    ]
    exampleModTable = [
        (21.400, 41.152, 84.730),
        (21.400, 41.152, 84.730),
        (21.400, 41.152, 84.730),
        (21.400, 41.152, 84.730),
        (24.380, 49.327, 104.560),
        (24.380, 49.327, 104.560),
        (24.380, 49.327, 104.560),
        (29.840, 54.645, 104.560),
        (30.910, 59.176, 105.190)
    ]
    tableDict = {"observed": exampleObsTable, "modelled": exampleModTable}
    durations = [1.0, 1.1, 1.2, 1.3, 1.5, 2.0, 2.5, 3.0, 3.5]
    obsFileName = "ObsFile.DAT"
    modFileName = "ModFile.OUT"

    printFATabularOutput(tableDict, durations, obsFileName, modFileName)
