import os
import math
import matplotlib.pyplot as plt
from datetime import date
from typing import Optional, Callable, List, Tuple
from src.lib.FrequencyAnalysis.frequency_analysis_functions import (
    fsDateOk, feDateOk, ensembleNumberOK,
    increaseObsDate, increaseDate,
    doWeWantThisDatum, dateSerial, getSeason
)

# Fix the global start date to Jan 1, 1948
global_start_date = date(1948, 1, 1)
minDataPoints = 100  # Minimum entries required per series for PDF

def pdfPlot(
    observedFile: str,
    modelledFile: Optional[str],
    fsDate: date,
    feDate: date,
    ensembleOption: str,        # 'all', 'mean', 'member', 'allPlusMean'
    ensembleWanted: Optional[int],
    numPdfCategories: int,
    dataPeriod: str,
    applyThreshold: bool,
    threshold: float,
    missingCode,
    exitAnalyses: Callable[[], bool]
) -> None:
    """
    Generate a PDF plot comparing observed and modelled data.
    """
    # Validate and clamp dates using fixed global start date
    fsOk, corrFs, _ = fsDateOk(global_start_date, fsDate, global_start_date)
    if not fsOk:
        corrFs = global_start_date
        print(f"[warning] fsDate {fsDate} before data start; using {corrFs}")
    feOk, corrFe, _ = feDateOk(corrFs, feDate, feDate)
    if not feOk:
        corrFe = feDate
        print(f"[warning] feDate {feDate} invalid; using {corrFe}")
    fsDate, feDate = corrFs, corrFe

    # Validate ensemble selection
    isMember = (ensembleOption == 'member')
    validEns, _, updWanted = ensembleNumberOK(
        isMember,
        str(ensembleWanted) if ensembleWanted is not None else '',
        ensembleWanted
    )
    if not validEns:
        raise ValueError(f"Invalid ensemble number {ensembleWanted}")
    if isMember:
        ensembleWanted = int(updWanted)

    # Check files
    obsExists = observedFile and os.path.exists(observedFile)
    modExists = modelledFile and os.path.exists(modelledFile)
    if not obsExists and not modExists:
        raise ValueError("At least one data file must be provided.")

    fObs = open(observedFile, 'r') if obsExists else None
    fMod = open(modelledFile, 'r') if modExists else None

    # Determine ensemble structure
    noEnsembles = 1
    ensemblePresent = False
    if fMod:
        header = fMod.readline().rstrip("\n")
        if len(header) > 15:
            ensemblePresent = True
            noEnsembles = len(header) // 14
        fMod.seek(0)

    # Skip up to fsDate in observed file
    if fObs:
        skip_days = (fsDate - global_start_date).days
        for _ in range(skip_days):
            if exitAnalyses(): return
            if not fObs.readline():
                raise ValueError(f"Reached EOF in observed file before {fsDate}")

    # Skip up to fsDate in modelled file (daily increment assumed)
    if fMod:
        skip_days = (fsDate - global_start_date).days
        for _ in range(skip_days):
            if exitAnalyses(): return
            if not fMod.readline():
                raise ValueError(f"Reached EOF in modelled file before {fsDate}")

    # Read data
    observedData: List[float] = []
    modelledData: List[List[float]] = [[] for _ in range(noEnsembles)]
    rdY, rdM, rdD = fsDate.year, fsDate.month, fsDate.day
    obsSeason = getSeason(rdM)
    modSeason = obsSeason
    length, leap = 1, 1

    while True:
        current = dateSerial(rdY, rdM, rdD)
        if current > feDate:
            break
        if exitAnalyses():
            return

        # Read observed
        valObs = math.nan
        if fObs:
            txt = fObs.readline().strip()
            try:
                valObs = float(txt)
                if valObs == missingCode:
                    valObs = math.nan
            except ValueError:
                valObs = math.nan

        # Read modelled
        valsMod: List[float] = []
        if fMod:
            if ensemblePresent:
                line = fMod.readline().rstrip("\n")
                for i in range(noEnsembles):
                    seg = line[i*14:(i+1)*14].strip()
                    try:
                        v = float(seg) if seg else math.nan
                        if v == missingCode:
                            v = math.nan
                    except ValueError:
                        v = math.nan
                    valsMod.append(v)
            else:
                txtm = fMod.readline().strip()
                try:
                    v = float(txtm)
                    if v == missingCode:
                        v = math.nan
                except ValueError:
                    v = math.nan
                valsMod = [v]

        # Filter
        if fObs and not doWeWantThisDatum(dataPeriod, rdM):
            rdD, rdM, rdY, obsSeason = increaseObsDate(rdD, rdM, rdY, obsSeason)
            if fMod:
                rdD, rdM, rdY, modSeason, length, leap = increaseDate(rdD, rdM, rdY, modSeason, length, leap)
            continue
        if fMod and not doWeWantThisDatum(dataPeriod, rdM):
            rdD, rdM, rdY, modSeason, length, leap = increaseDate(rdD, rdM, rdY, modSeason, length, leap)
            continue

        ok = True
        if fObs and math.isnan(valObs): ok = False
        if ok and fObs and applyThreshold and valObs < threshold: ok = False
        if fMod and ok:
            for vv in valsMod:
                if math.isnan(vv) or (applyThreshold and vv < threshold):
                    ok = False
                    break

        if ok:
            if fObs:
                observedData.append(valObs)
            if fMod:
                for idx, vv in enumerate(valsMod):
                    modelledData[idx].append(vv)

        rdD, rdM, rdY, obsSeason = increaseObsDate(rdD, rdM, rdY, obsSeason)
        if fMod:
            rdD, rdM, rdY, modSeason, length, leap = increaseDate(rdD, rdM, rdY, modSeason, length, leap)

    # Close
    if fObs:
        fObs.close()
    if fMod:
        fMod.close()

    # Check and warn
    if fObs and len(observedData) < minDataPoints:
        print(f"[warning] only {len(observedData)} observed records; proceeding")
    if fMod:
        for i, ser in enumerate(modelledData, start=1):
            if len(ser) < minDataPoints:
                print(f"[warning] only {len(ser)} records for ensemble {i}; proceeding")

    # Line plots
    allVals = observedData.copy()
    for ser in modelledData:
        allVals.extend(ser)
    if not allVals:
        print("[error] No data to plot.")
        return

    lo, hi = min(allVals), max(allVals)
    if hi == lo:
        # Single-value data
        obsCounts = [len(observedData)]
        modCounts = [[len(ser)] for ser in modelledData]
        centers = [lo]
    else:
        width = (hi - lo) / numPdfCategories
        centers = [lo + (i + 0.5) * width for i in range(numPdfCategories)]
        obsCounts = [0] * numPdfCategories
        for v in observedData:
            idx = int((v - lo) / width)
            idx = min(idx, numPdfCategories - 1)
            obsCounts[idx] += 1
        modCounts = [[0] * numPdfCategories for _ in range(noEnsembles)]
        for ei, ser in enumerate(modelledData):
            for v in ser:
                idx = int((v - lo) / width)
                idx = min(idx, numPdfCategories - 1)
                modCounts[ei][idx] += 1

    seriesList: List[Tuple[List[int], str]] = [(obsCounts, 'Observed')]
    if modelledFile:
        if ensembleOption == 'member':
            seriesList.append((modCounts[ensembleWanted-1], f'Ensemble{ensembleWanted}'))
        elif ensembleOption == 'mean':
            meanC = [sum(bin_) / noEnsembles for bin_ in zip(*modCounts)]
            seriesList.append((meanC, 'Mean'))
        elif ensembleOption == 'all':
            for i, cnt in enumerate(modCounts, start=1):
                seriesList.append((cnt, f'Ensemble{i}'))
        elif ensembleOption == 'allPlusMean':
            for i, cnt in enumerate(modCounts, start=1):
                seriesList.append((cnt, f'Ensemble{i}'))
            meanC = [sum(bin_) / noEnsembles for bin_ in zip(*modCounts)]
            seriesList.append((meanC, 'Mean'))

    plt.figure()
    for cnt, lbl in seriesList:
        if 'Ensemble' in lbl:
            plt.plot(centers, cnt, label=lbl, color='red', zorder=1)
        elif 'Mean' in lbl:
            plt.plot(centers, cnt, label=lbl, color='lime', zorder=2)
        else:
            plt.plot(centers, cnt, label=lbl, zorder=3)
    plt.xlabel('Value')
    plt.ylabel('Frequency')
    plt.legend()
    plt.tight_layout()
    plt.show()
