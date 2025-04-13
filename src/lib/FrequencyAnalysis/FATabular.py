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

    dailyValues = []

    try:
        with open(filePath, 'r') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading {filePath}: {e}")
        return dailyValues

    currentDate = globalStartDate

    for line in lines:
        if currentDate < fsDate:
            currentDate += datetime.timedelta(days=1)
            continue
        if currentDate > feDate:
            break

        if isModelled:
            start_pos = ensembleIndex * 14
            end_pos = start_pos + 14
            if len(line) >= end_pos:
                raw = line[start_pos:end_pos]
            else:
                currentDate += datetime.timedelta(days=1)
                continue  # VB skips short lines entirely for modelled data
        else:
            raw = line.strip()

        try:
            val = float(raw)
        except:
            currentDate += datetime.timedelta(days=1)
            continue  # VB skips lines that don't parse as numbers

        if val == missingValue or (applyThreshold and val < thresholdValue):
            currentDate += datetime.timedelta(days=1)
            continue

        if doWeWantThisDatum(currentDate, dataPeriodChoice):
            dailyValues.append((currentDate, val))

        currentDate += datetime.timedelta(days=1)

    return dailyValues

def vb_percentile(sorted_data, p):
    n = len(sorted_data)
    if n == 0:
        return None
    pos = 1 + (p * (n - 1)) / 100.0
    lower_index = int(pos) - 1
    upper_index = lower_index + 1
    fraction = pos - int(pos)
    if upper_index >= n:
        return sorted_data[lower_index]
    return sorted_data[lower_index] + fraction * (sorted_data[upper_index] - sorted_data[lower_index])

def computeAnnualMaxSeries(dailyValues, duration):
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
    for year, values in yearMap.items():
        if len(values) < N:
            continue
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

        if freqModel == "Empirical":
            central = np.mean(amsObs)
            sorted_ams = sorted(amsObs)
            lower = vb_percentile(sorted_ams, 2.5)
            upper = vb_percentile(sorted_ams, 97.5)
        elif freqModel == "GEV":
            try:
                c, loc, scale = genextreme.fit(amsObs)
                central = genextreme.ppf(1 - 1/dur, c, loc=loc, scale=scale)
                delta = 0.1
                lower = genextreme.ppf(1 - 1/(dur + delta), c, loc=loc, scale=scale)
                upper = genextreme.ppf(1 - 1/(dur - delta if dur - delta > 1 else dur), c, loc=loc, scale=scale)
            except Exception as e:
                central = lower = upper = 0.0
        elif freqModel == "Gumbel":
            try:
                loc, scale = gumbel_r.fit(amsObs)
                central = gumbel_r.ppf(1 - 1/dur, loc=loc, scale=scale)
                delta = 0.1
                lower = gumbel_r.ppf(1 - 1/(dur + delta), loc=loc, scale=scale)
                upper = gumbel_r.ppf(1 - 1/(dur - delta if dur - delta > 1 else dur), loc=loc, scale=scale)
            except Exception as e:
                central = lower = upper = 0.0
        elif freqModel == "Stretched Exponential":
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
