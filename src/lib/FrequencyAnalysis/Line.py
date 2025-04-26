import os
import math
import matplotlib.pyplot as plt
from datetime import date
from typing import Optional, Callable
from src.lib.FrequencyAnalysis.frequency_analysis_functions import (
    increaseDate, doWeWantThisDatum, getSeason
)

def linePlot(
    observedFilePath: str,
    modelledFilePath: Optional[str],
    analysisStartDate: date,
    analysisEndDate: date,
    ensembleMode: str,        # 'allMembers', 'ensembleMean', 'ensembleMember', or 'allPlusMean'
    ensembleIndex: Optional[int],
    dataPeriod: str,          # passed into doWeWantThisDatum(...)
    applyThreshold: bool,
    thresholdValue: float,
    globalMissingCode,
    exitAnalysesFunc: Callable[[], bool]
):
    """
    Parameters mapped to your UI controls:
      - observedFilePath:   path from “Select Observed Data”
      - modelledFilePath:   path from “Select Modelled Data” (or None)
      - analysisStartDate:  date from “Analysis start date”
      - analysisEndDate:    date from “Analysis end date”
      - ensembleMode:       one of 'allMembers', 'ensembleMean',
                            'ensembleMember', 'allPlusMean'
      - ensembleIndex:      the integer if ’ensembleMember’ is chosen
      - dataPeriod:         e.g. 'All Data', 'January only', etc.
      - applyThreshold:     True if “Apply threshold?” is checked
      - thresholdValue:     the numeric threshold
      - globalMissingCode:  missing number from settings
      - exitAnalysesFunc:   returns True if user hit “Cancel”
    """

    # 1) check files exist & derive labels
    obsExists = bool(observedFilePath and os.path.exists(observedFilePath))
    modExists = bool(modelledFilePath and os.path.exists(modelledFilePath))
    if not (obsExists or modExists):
        raise ValueError("You must select at least one file before proceeding.")
    obsLabel = os.path.basename(observedFilePath) if obsExists else ""
    modLabel = os.path.basename(modelledFilePath) if modExists else ""

    # 2) open files
    fObs = open(observedFilePath, 'r') if obsExists else None
    fMod = open(modelledFilePath, 'r') if modExists else None

    # 3) determine ensemble structure
    noOfEnsembles = 1
    ensemblePresent = False
    if fMod:
        firstLine = fMod.readline().rstrip("\n")
        if len(firstLine) > 15:
            ensemblePresent = True
            noOfEnsembles = len(firstLine) // 14
        # rewind
        fMod.seek(0)

        if ensembleMode == 'ensembleMember':
            if ensembleIndex is None or not (1 <= ensembleIndex <= noOfEnsembles):
                raise ValueError(
                    f"You selected ensemble #{ensembleIndex}, but only {noOfEnsembles} exist."
                )

    # 4) skip up to analysisStartDate
    #    seed current to the file’s first date (e.g. 1948-01-01)
    currentDay, currentMonth, currentYear = 1, 1, 1948
    currentSeason = getSeason(currentMonth)
    yearLength, leapValue = 1, 1
    current = date(currentYear, currentMonth, currentDay)

    while current < analysisStartDate:
        if exitAnalysesFunc():
            return
        if fObs: fObs.readline()
        if fMod: fMod.readline()
        currentDay, currentMonth, currentYear, currentSeason, yearLength, leapValue = \
            increaseDate(currentDay, currentMonth, currentYear,
                         currentSeason, yearLength, leapValue)
        current = date(currentYear, currentMonth, currentDay)

    # 5) read & filter between start and end
    observedData = []
    modelledData = [[] for _ in range(noOfEnsembles)]

    counters = {
        'total_days': 0,
        'passed_period_filter': 0,
        'dropped_missing_obs': 0,
        'dropped_thresh_obs': 0,
        'dropped_missing_mod': 0,
        'kept': 0,
    }

    while current < analysisEndDate:
        if exitAnalysesFunc():
            return
        counters['total_days'] += 1

        # read raw
        if fObs:
            rawObs = fObs.readline().strip()
            obsRaw = float(rawObs)
            if obsRaw == globalMissingCode:
                obsRaw = math.nan
        if fMod:
            if ensemblePresent:
                rawLine = fMod.readline().rstrip("\n")
            else:
                rawMod = float(fMod.readline().strip())
                if rawMod == globalMissingCode:
                    rawMod = math.nan

        # period‐filter
        if not doWeWantThisDatum(dataPeriod, currentMonth):
            currentDay, currentMonth, currentYear, currentSeason, yearLength, leapValue = \
                increaseDate(currentDay, currentMonth, currentYear,
                             currentSeason, yearLength, leapValue)
            current = date(currentYear, currentMonth, currentDay)
            continue
        counters['passed_period_filter'] += 1

        # parse modelled
        if fMod:
            if not ensemblePresent:
                modVals = [rawMod]
            else:
                modVals = []
                for i in range(noOfEnsembles):
                    txt = rawLine[i*14:(i+1)*14].strip()
                    val = float(txt) if txt else math.nan
                    if val == globalMissingCode:
                        val = math.nan
                    modVals.append(val)

        # missing‐obs check
        obsVal = obsRaw if fObs else math.nan
        valid = True
        if fObs and math.isnan(obsVal):
            counters['dropped_missing_obs'] += 1
            valid = False

        # threshold
        if fObs and valid and applyThreshold and obsVal < thresholdValue:
            counters['dropped_thresh_obs'] += 1
            valid = False

        # modelled check
        if fMod and valid:
            for m in modVals:
                if math.isnan(m) or (applyThreshold and m < thresholdValue):
                    counters['dropped_missing_mod'] += 1
                    valid = False
                    break

        # append or drop
        if valid:
            counters['kept'] += 1
            if fObs:
                observedData.append(obsVal)
            if fMod:
                for idx, m in enumerate(modVals):
                    modelledData[idx].append(m)

        # advance date
        currentDay, currentMonth, currentYear, currentSeason, yearLength, leapValue = \
            increaseDate(currentDay, currentMonth, currentYear,
                         currentSeason, yearLength, leapValue)
        current = date(currentYear, currentMonth, currentDay)

    # 6) ensure enough data
    if fObs and len(observedData) < 10:
        raise ValueError("Insufficient data to plot, please check your files.")

    # 7) build series
    series = []
    if fObs:
        series.append((obsLabel, observedData))
    if fMod:
        if ensembleMode == 'ensembleMember':
            vals = modelledData[ensembleIndex-1]
            series.append((f"{modLabel} Ensemble {ensembleIndex}", vals))
        elif ensembleMode == 'allPlusMean':
            for i, vals in enumerate(modelledData, start=1):
                series.append((f"{modLabel} Ensemble {i}", vals))
            meanVals = [
                (math.nan if any(math.isnan(v) for v in vals)
                 else sum(vals)/len(vals))
                for vals in zip(*modelledData)
            ]
            series.append((f"{modLabel} Mean", meanVals))
        elif ensembleMode == 'ensembleMean':
            meanVals = [
                (math.nan if any(math.isnan(v) for v in vals)
                 else sum(vals)/len(vals))
                for vals in zip(*modelledData)
            ]
            series.append((f"{modLabel} Mean", meanVals))
        else:  # 'allMembers'
            for i, vals in enumerate(modelledData, start=1):
                series.append((f"{modLabel} Ensemble {i}", vals))

    # 8) print & plot
    length = len(observedData) if fObs else len(modelledData[0])
    x = list(range(1, length+1))

    for label, y in series:
        if 'Mean' in label:
            color = 'limegreen'
            z = 2
        elif 'Ensemble' in label:
            color = 'red'
            z = 1
        else:
            color = 'blue'
            z = 3

        plt.plot(x, y, color=color, label=label, zorder=z)

    plt.xlabel("Time step")
    plt.ylabel("Value")
    plt.legend()
    plt.tight_layout()
    plt.show()

