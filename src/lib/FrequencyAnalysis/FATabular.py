import math
import datetime
import numpy as np
from collections import defaultdict
from scipy.stats import genextreme, gumbel_r, weibull_min  # needed for parametric fits

# Global parameters – adjust to match VB defaults:
# VB default uses dates 01/01/1948 to 31/12/2015.
globalStartDate = datetime.date(1948, 1, 1)
missingValue = -999

### BACKEND FUNCTIONS ###

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
    Returns True if the current date should be used for the analysis.
    DataPeriodChoice can be "All Data", a specific month name, or a season name.
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
    if dataPeriodChoice.lower() in ["winter", "spring", "summer", "autumn"]:
        season = {"winter": 1, "spring": 2, "summer": 3, "autumn": 4}[dataPeriodChoice.lower()]
        return getSeason(currentDate.month) == season
    return True

def readDailyDataDayByDay(filePath, fsDate, feDate, dataPeriodChoice,
                          applyThreshold, thresholdValue,
                          globalStartDate=globalStartDate,
                          isModelled=False, ensembleIndex=0):
    """
    Reads daily data from filePath.
    Assumes that each line in the file corresponds to one day starting at globalStartDate.
    Skips values equal to missingValue or those below thresholdValue if applyThreshold is True.
    Also filters based on dataPeriodChoice.
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
        
        # For modelled data: support fixed-width extraction (each ensemble occupies 14 characters)
        if isModelled and len(line) >= (ensembleIndex + 1) * 14:
            raw = line[ensembleIndex * 14:(ensembleIndex * 14) + 14]
        else:
            raw = line
        
        try:
            val = float(raw.strip())
        except:
            continue  # skip non-numeric lines
        
        if val == missingValue or (applyThreshold and val < thresholdValue):
            continue
        
        if doWeWantThisDatum(currentDate, dataPeriodChoice):
            dailyValues.append((currentDate, val))
    
    return dailyValues

def vb_percentile(sorted_data, p):
    """
    Computes the p-th percentile in a VB-style 1-indexed linear interpolation.
    Position = 1 + (p*(n-1))/100, lower index = int(Position)-1.
    """
    n = len(sorted_data)
    if n == 0:
        return None
    if p <= 0:
        return sorted_data[0]
    if p >= 100:
        return sorted_data[-1]
    pos = 1 + (p * (n - 1)) / 100.0  # VB-style: 1-indexed position
    lower_index = int(pos) - 1  # convert to Python 0-indexed
    upper_index = lower_index + 1
    if upper_index >= n:
        return sorted_data[lower_index]
    fraction = pos - int(pos)
    return sorted_data[lower_index] + fraction * (sorted_data[upper_index] - sorted_data[lower_index])

def computeAnnualMaxSeries(dailyValues, duration):
    """
    Groups daily data by year and calculates the Annual Maximum Series (AMS)
    using a moving sum over N consecutive days.
    Discrete mapping for window length:
      - If duration < 1.5, use a 1-day sum.
      - If 1.5 <= duration <= 2.5, use a 2-day sum.
      - Otherwise (duration >= 3.0), use a 3-day sum.
    """
    if duration < 1.5:
        N = 1
    elif duration <= 2.5:
        N = 2
    else:
        N = 3

    yearMap = defaultdict(list)
    for dt, val in dailyValues:
        yearMap[dt.year].append(val)
        
    ams = []
    for year in sorted(yearMap.keys()):
        values = yearMap[year]
        if len(values) < N:
            continue
        # Compute the moving sum over N days.
        movingSums = [sum(values[i:i+N]) for i in range(len(values) - N + 1)]
        ams.append(max(movingSums))
    return ams

def computeFATableFromFiles(observedFilePath, modelledFilePath, fsDate, feDate,
                            dataPeriodChoice="All Data",
                            applyThreshold=False,
                            thresholdValue=10.0,  # using VB default threshold of 10
                            durations=[1.0, 1.1, 1.2, 1.3, 1.5, 2.0, 2.5, 3.0, 3.5],
                            ensembleIndex=0,
                            freqModel="empirical"):
    """
    For each duration, this function:
      1. Reads observed and modelled daily data.
      2. Computes the Annual Maximum Series (AMS) using a moving sum of length determined 
         by the duration (using a discrete mapping).
      3. Based on freqModel, computes:
           - "empirical": the mean and VB-style percentiles (2.5th and 97.5th).
           - "gev": fits a GEV distribution to the AMS and computes the predicted quantile.
           - "gumbel": fits a Gumbel distribution similarly.
           - "stretched": fits a stretched exponential distribution via weibull_min.
    Returns a dictionary with keys "observed" and "modelled",
    each a list of tuples (lower, central, upper).
    """
    # Process observed data:
    dailyObs = readDailyDataDayByDay(observedFilePath, fsDate, feDate,
                                      dataPeriodChoice, applyThreshold, thresholdValue,
                                      isModelled=False)
    tableObs = []
    for dur in durations:
        amsObs = computeAnnualMaxSeries(dailyObs, dur)
        if not amsObs:
            tableObs.append((0.0, 0.0, 0.0))
            continue

        if freqModel == "empirical":
            central = np.mean(amsObs)
            sorted_ams = sorted(amsObs)
            lower = vb_percentile(sorted_ams, 2.5)
            upper = vb_percentile(sorted_ams, 97.5)
        elif freqModel == "gev":
            try:
                c, loc, scale = genextreme.fit(amsObs)
                central = genextreme.ppf(1 - 1/dur, c, loc=loc, scale=scale)
                delta = 0.1
                lower = genextreme.ppf(1 - 1/(dur + delta), c, loc=loc, scale=scale)
                upper = genextreme.ppf(1 - 1/(dur - delta if dur - delta > 1 else dur), c, loc=loc, scale=scale)
            except Exception as e:
                central = lower = upper = 0.0
        elif freqModel == "gumbel":
            try:
                loc, scale = gumbel_r.fit(amsObs)
                central = gumbel_r.ppf(1 - 1/dur, loc=loc, scale=scale)
                delta = 0.1
                lower = gumbel_r.ppf(1 - 1/(dur + delta), loc=loc, scale=scale)
                upper = gumbel_r.ppf(1 - 1/(dur - delta if dur - delta > 1 else dur), loc=loc, scale=scale)
            except Exception as e:
                central = lower = upper = 0.0
        elif freqModel == "stretched":
            try:
                # Using weibull_min to model a stretched exponential:
                # We force loc=0 if it makes sense for the data.
                c, loc, scale = weibull_min.fit(amsObs, floc=0)
                central = weibull_min.ppf(1 - 1/dur, c, loc=loc, scale=scale)
                delta = 0.1
                lower = weibull_min.ppf(1 - 1/(dur + delta), c, loc=loc, scale=scale)
                upper = weibull_min.ppf(1 - 1/(dur - delta if dur - delta > 1 else dur), c, loc=loc, scale=scale)
            except Exception as e:
                central = lower = upper = 0.0
        else:
            # Default to empirical if unknown option.
            central = np.mean(amsObs)
            sorted_ams = sorted(amsObs)
            lower = vb_percentile(sorted_ams, 2.5)
            upper = vb_percentile(sorted_ams, 97.5)

        tableObs.append((lower, central, upper))
    
    # Process modelled data (similar approach)
    dailyMod = readDailyDataDayByDay(modelledFilePath, fsDate, feDate,
                                      dataPeriodChoice, applyThreshold, thresholdValue,
                                      isModelled=True, ensembleIndex=ensembleIndex)
    tableMod = []
    for dur in durations:
        amsMod = computeAnnualMaxSeries(dailyMod, dur)
        if not amsMod:
            tableMod.append((0.0, 0.0, 0.0))
            continue

        if freqModel == "empirical":
            central = np.mean(amsMod)
            sorted_ams = sorted(amsMod)
            lower = vb_percentile(sorted_ams, 2.5)
            upper = vb_percentile(sorted_ams, 97.5)
        elif freqModel == "gev":
            try:
                c, loc, scale = genextreme.fit(amsMod)
                central = genextreme.ppf(1 - 1/dur, c, loc=loc, scale=scale)
                delta = 0.1
                lower = genextreme.ppf(1 - 1/(dur + delta), c, loc=loc, scale=scale)
                upper = genextreme.ppf(1 - 1/(dur - delta if dur - delta > 1 else dur), c, loc=loc, scale=scale)
            except Exception as e:
                central = lower = upper = 0.0
        elif freqModel == "gumbel":
            try:
                loc, scale = gumbel_r.fit(amsMod)
                central = gumbel_r.ppf(1 - 1/dur, loc=loc, scale=scale)
                delta = 0.1
                lower = gumbel_r.ppf(1 - 1/(dur + delta), loc=loc, scale=scale)
                upper = gumbel_r.ppf(1 - 1/(dur - delta if dur - delta > 1 else dur), loc=loc, scale=scale)
            except Exception as e:
                central = lower = upper = 0.0
        elif freqModel == "stretched":
            try:
                c, loc, scale = weibull_min.fit(amsMod, floc=0)
                central = weibull_min.ppf(1 - 1/dur, c, loc=loc, scale=scale)
                delta = 0.1
                lower = weibull_min.ppf(1 - 1/(dur + delta), c, loc=loc, scale=scale)
                upper = weibull_min.ppf(1 - 1/(dur - delta if dur - delta > 1 else dur), c, loc=loc, scale=scale)
            except Exception as e:
                central = lower = upper = 0.0
        else:
            central = np.mean(amsMod)
            sorted_ams = sorted(amsMod)
            lower = vb_percentile(sorted_ams, 2.5)
            upper = vb_percentile(sorted_ams, 97.5)
        tableMod.append((lower, central, upper))
    
    return {"observed": tableObs, "modelled": tableMod}

def printFATabularOutput(tableDict, durations, obsFileName, modFileName,
                         seasonText="Annual", fitType="Empirical"):
    """
    Prints the FA tabular output, including a header with season and fit type,
    and a table with columns: Return Period, Obs, Mod, 2.5 %ile, 97.5 %ile.
    """
    print(f"Season: {seasonText}")
    print(f"Fit: {fitType}")
    print(f"Observed data: {obsFileName}")
    print(f"Modelled data: {modFileName}\n")
    
    print("Return Period      Obs          Mod          2.5 %ile      97.5 %ile")
    print("-----------------------------------------------------------------------")
    for dur, obsTuple, modTuple in zip(durations, tableDict.get("observed", []), tableDict.get("modelled", [])):
        obsLower, obsCentral, obsUpper = obsTuple
        modLower, modCentral, modUpper = modTuple
        print(f"{dur:13.1f} {obsCentral:12.3f} {modCentral:12.3f} {obsLower:12.3f} {obsUpper:12.3f}")
    print("-----------------------------------------------------------------------\n")
