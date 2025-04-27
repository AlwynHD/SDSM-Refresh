import os
import math
import matplotlib.pyplot as plt
from datetime import date
import numpy as np
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
):
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
    obsLabel = os.path.basename(observedFile) if obsExists else ""
    modLabel = os.path.basename(modelledFile) if modExists else ""

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

                # 1) Skip days outside the desired period
        if not doWeWantThisDatum(dataPeriod, rdM):
            rdD, rdM, rdY, obsSeason = increaseObsDate(rdD, rdM, rdY, obsSeason)
            if fMod:
                rdD, rdM, rdY, modSeason, length, leap = increaseDate(
                    rdD, rdM, rdY, modSeason, length, leap
                )
            continue

        # 2) Append observed if it passes missing‐code and threshold
        if fObs and not math.isnan(valObs) and (
           not applyThreshold or valObs >= threshold
        ):
            observedData.append(valObs)

        # 3) Append each modelled ensemble value independently
        if fMod:
            if ensemblePresent:
                for idx, vv in enumerate(valsMod):
                    if not math.isnan(vv) and (
                       not applyThreshold or vv >= threshold
                    ):
                        modelledData[idx].append(vv)
            else:
                vv = valsMod[0]
                if not math.isnan(vv) and (
                   not applyThreshold or vv >= threshold
                ):
                    modelledData[0].append(vv)

        # 4) Advance both date counters
        rdD, rdM, rdY, obsSeason = increaseObsDate(rdD, rdM, rdY, obsSeason)
        if fMod:
            rdD, rdM, rdY, modSeason, length, leap = increaseDate(
                rdD, rdM, rdY, modSeason, length, leap
            )


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

    # 1) Determine the exact lo/hi that VB would use
    if fMod:
        if ensembleOption == 'ensembleMember':
            dataToRange = observedData + modelledData[ensembleWanted-1]
        else:
            dataToRange = observedData.copy()
            for vals in modelledData:
                dataToRange.extend(vals)
    else:
        dataToRange = observedData.copy()

    if not dataToRange:
        print("[error] No data to plot.")
        return

    lo = min(dataToRange)
    hi = max(dataToRange)
    # handle the degenerate single-value case
    if hi == lo:
        width = 1e-6
    else:
        width = (hi - lo) / numPdfCategories

    # 2) Build VB-style bin lower-edges
    binEdges = [lo + i * width for i in range(numPdfCategories + 1)]
    xValues  = binEdges[:-1]   # VB plots at each CatMin

    # 3) Count & normalise to get densities
    #    (VB shows count/total → "standardised density")
    obsCounts = [0] * numPdfCategories
    for v in observedData:
        idx = min(int((v - lo) / width), numPdfCategories - 1)
        obsCounts[idx] += 1
    obsDensity = [c / len(observedData) for c in obsCounts]

    modDensity = []
    if fMod:
        # count per ensemble
        modCounts = [[0]*numPdfCategories for _ in range(noEnsembles)]
        for ei, vals in enumerate(modelledData):
            for v in vals:
                idx = min(int((v - lo) / width), numPdfCategories - 1)
                modCounts[ei][idx] += 1
        # normalise
        modDensity = [
            [c / len(modelledData[ei]) for c in modCounts[ei]]
            for ei in range(noEnsembles)
        ]

    # 4) Build your series list
    series = []
    if fObs:
        series.append((obsLabel, obsDensity))

    if fMod:
        if ensembleOption == 'ensembleMember':
            series.append(
                (f"{modLabel} Ensemble {ensembleWanted}",
                modDensity[ensembleWanted-1])
            )
        elif ensembleOption == 'ensembleMean':
            meanVals = [sum(bin_) / noEnsembles for bin_ in zip(*modDensity)]
            series.append((f"{modLabel} Mean", meanVals))
        elif ensembleOption == 'allMembers':
            for i, vals in enumerate(modDensity, start=1):
                series.append((f"{modLabel} Ensemble {i}", vals))
        elif ensembleOption == 'allPlusMean':
            for i, vals in enumerate(modDensity, start=1):
                series.append((f"{modLabel} Ensemble {i}", vals))
            meanVals = [sum(bin_) / noEnsembles for bin_ in zip(*modDensity)]
            series.append((f"{modLabel} Mean", meanVals))

    # 5) Plot VB-style line-PDF
    plt.figure()
    for label, yVals in series:
        plt.plot(xValues, yVals, label=label, linewidth=1.5)
        print(f"{yVals}")

    # only show the first & last bin-edge as X-tick labels
    plt.xticks(
        [xValues[0], xValues[-1]],
        [f"{xValues[0]:.5g}", f"{xValues[-1]:.5g}"]
    )

    plt.xlabel("Value")
    plt.ylabel("Standardised Density")
    plt.legend(loc="best")
    plt.tight_layout()
    plt.show()