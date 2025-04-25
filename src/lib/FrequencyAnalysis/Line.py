import os
import math
import matplotlib.pyplot as plt
from datetime import date
from typing import Optional, Callable
from src.lib.FrequencyAnalysis.frequency_analysis_functions import (dateDiff, dateSerial, increaseDate, doWeWantThisDatum, getSeason)

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

    global currentDay, currentMonth, currentYear, currentSeason, yearLength, leapValue

    yearLength = 1
    leapValue = 1

    # 1) check files exist & derive labels
    obsExists = bool(observedFilePath and os.path.exists(observedFilePath))
    modExists = bool(modelledFilePath and os.path.exists(modelledFilePath))
    if not (obsExists or modExists):
        raise ValueError("You must select at least one file before proceeding.")
    obsLabel = os.path.basename(observedFilePath) if obsExists else ""
    modLabel = os.path.basename(modelledFilePath) if modExists else ""

    # 2) determine ensemble structure in the modelled file
    noOfEnsembles = 1
    ensemblePresent = False
    if modExists:
        with open(modelledFilePath, 'r') as f:
            firstLine = f.readline().rstrip("\n")
        if len(firstLine) > 15:
            ensemblePresent = True
            noOfEnsembles = len(firstLine) // 14

        if ensembleMode == 'ensembleMember':
            if ensembleIndex is None or not (1 <= ensembleIndex <= noOfEnsembles):
                raise ValueError(
                    f"You selected ensemble #{ensembleIndex}, but only {noOfEnsembles} exist."
                )

    # 3) open files
    fObs = open(observedFilePath, 'r') if obsExists else None
    fMod = open(modelledFilePath, 'r') if modExists else None

    # 4) skip until analysisStartDate
    currentDay, currentMonth, currentYear = (
        analysisStartDate.day,
        analysisStartDate.month,
        analysisStartDate.year
    )

    while dateDiff(dateSerial(currentYear, currentMonth, currentDay),analysisStartDate) > 0:
        if exitAnalysesFunc():
            return
        if fObs: fObs.readline()
        if fMod: fMod.readline()
        currentDay, currentMonth, currentYear, currentSeason, yearLength, leapValue = increaseDate(currentDay, currentMonth, currentYear, currentSeason, yearLength, leapValue)

    # 5) read & filter between analysisStartDate and analysisEndDate
    observedData = []
    modelledData = [[] for _ in range(noOfEnsembles)]
    # reset cursor
    currentDay, currentMonth, currentYear = (
        analysisStartDate.day,
        analysisStartDate.month,
        analysisStartDate.year
    )
    currentSeason = getSeason(currentMonth)

    while dateDiff(dateSerial(currentYear, currentMonth, currentDay), analysisEndDate) > 0:
        if exitAnalysesFunc():
            return

        # --- read one day’s raw values
        if fObs:
            rawObs = fObs.readline().strip()
            obsRaw = float(rawObs)
            # convert missing‐code sentinel into NaN
            if obsRaw == globalMissingCode:
                obsRaw = math.nan

        if fMod:
            if ensemblePresent:
                rawLine = fMod.readline().rstrip("\n")
            else:
                rawMod = fMod.readline().strip()
                modRaw = float(rawMod)
                if modRaw == globalMissingCode:
                    modRaw = math.nan

        if doWeWantThisDatum(dataPeriod, currentMonth):
            # parse modelled values into a list, handling sentinel
            if fMod:
                if not ensemblePresent:
                    modVals = [modRaw]
                else:
                    modVals = []
                    for i in range(noOfEnsembles):
                        txt = rawLine[i*14:(i+1)*14].strip()
                        val = float(txt) if txt else math.nan
                        if val == globalMissingCode:
                            val = math.nan
                        modVals.append(val)

            # --- threshold & missing‐code logic
            obsVal = obsRaw if fObs else math.nan
            valid = True

            # any NaN in observed = invalid
            if fObs and math.isnan(obsVal):
                valid = False
            # threshold failure
            if fObs and applyThreshold and obsVal < thresholdValue:
                valid = False

            if fMod and valid:
                for m in modVals:
                    # NaN or below threshold → invalid
                    if math.isnan(m) or (applyThreshold and m < thresholdValue):
                        valid = False
                        break

            # replace invalids with NaN
            if not valid:
                obsVal = math.nan
                if fMod:
                    modVals = [math.nan]*noOfEnsembles

            if fObs:
                observedData.append(obsVal)
            if fMod:
                for idx, m in enumerate(modVals):
                    modelledData[idx].append(m)

        currentDay, currentMonth, currentYear, currentSeason, yearLength, leapValue = increaseDate(currentDay, currentMonth, currentYear, currentSeason, yearLength, leapValue)

    # 6) ensure enough data
    if fObs and len(observedData) < 10:
        raise ValueError("Insufficient data to plot—please check your files.")

    # 7) build plotting series
    length = len(observedData) if fObs else len(modelledData[0])
    x = list(range(1, length+1))
    series = []

    if fObs:
        series.append((obsLabel, observedData))

    if fMod:
        if   ensembleMode == 'ensembleMember':
            idx = ensembleIndex - 1
            series.append((f"{modLabel} Ensemble {ensembleIndex}", modelledData[idx]))
        elif ensembleMode == 'allPlusMean':
            for i in range(noOfEnsembles):
                series.append((f"{modLabel} Ensemble {i+1}", modelledData[i]))
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
            for i in range(noOfEnsembles):
                series.append((f"{modLabel} Ensemble {i+1}", modelledData[i]))

    # 8) plot
    for label, y in series:
        plt.plot(x, y, label=label)
    plt.xlabel("Time step")
    plt.ylabel("Value")
    plt.legend()
    plt.tight_layout()
    plt.show()
