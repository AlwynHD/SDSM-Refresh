import os
import math
import matplotlib.pyplot as plt
from datetime import date
from typing import Optional, Callable, List, Tuple
from PyQt5.QtWidgets import QApplication, QFileDialog, QAction
from PyQt5.QtGui import QIcon
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from src.lib.FrequencyAnalysis.frequency_analysis_functions import (
    fsDateOk, feDateOk, ensembleNumberOK,
    increaseObsDate, increaseDate,
    doWeWantThisDatum, dateSerial, getSeason,export_series_to_csv
)

minDataPoints = 100  # Minimum entries required per series for PDF

def pdfPlot(
    observedFile: str,
    modelledFile: Optional[str],
    fsDate: date,
    feDate: date,
    globalStartDate: date,
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
    # --- Date validation ---
    fsOk, corrFs, _ = fsDateOk(globalStartDate, fsDate, globalStartDate)
    if not fsOk:
        corrFs = globalStartDate
        print(f"[warning] fsDate {fsDate} before data start; using {corrFs}")
    feOk, corrFe, _ = feDateOk(corrFs, feDate, feDate)
    if not feOk:
        corrFe = feDate
        print(f"[warning] feDate {feDate} invalid; using {corrFe}")
    fsDate, feDate = corrFs, corrFe

    # --- Ensemble validation ---
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

    # --- File setup ---
    obsExists = bool(observedFile and os.path.exists(observedFile))
    modExists = bool(modelledFile and os.path.exists(modelledFile))
    if not obsExists and not modExists:
        raise ValueError("At least one data file must be provided.")
    obsLabel = os.path.basename(observedFile) if obsExists else None
    modLabel = os.path.basename(modelledFile) if modExists else None

    fObs = open(observedFile, 'r') if obsExists else None
    fMod = open(modelledFile, 'r') if modExists else None

    # Determine ensemble count
    noEnsembles = 1
    ensemblePresent = False
    if fMod:
        first_line = fMod.readline().rstrip("\n")
        if len(first_line) > 15:
            ensemblePresent = True
            noEnsembles = len(first_line) // 14
        fMod.seek(0)

    # Skip to fsDate in files
    for fh in (fObs, fMod):
        if fh:
            skip_days = (fsDate - globalStartDate).days
            for _ in range(skip_days):
                if exitAnalyses(): return
                if not fh.readline():
                    raise ValueError(f"Reached EOF before {fsDate}")

    # Read and filter data
    observedData: List[float] = []
    modelledData: List[List[float]] = [[] for _ in range(noEnsembles)]

    obs_d, obs_m, obs_y = fsDate.day, fsDate.month, fsDate.year
    mod_d, mod_m, mod_y = obs_d, obs_m, obs_y
    obsSeason = getSeason(obs_m)
    modSeason = obsSeason
    length, leap = 1, 1

    while True:
        current_obs = dateSerial(obs_y, obs_m, obs_d)
        if current_obs > feDate or exitAnalyses():
            break

        # Read one day value(s)
        valObs = (lambda txt: float(txt) if txt and float(txt)!=missingCode else math.nan)(fObs.readline().strip()) if fObs else math.nan
        valsMod = []
        if fMod:
            if ensemblePresent:
                line = fMod.readline().rstrip("\n")
                for i in range(noEnsembles):
                    part = line[i*14:(i+1)*14].strip()
                    valsMod.append(float(part) if part and float(part)!=missingCode else math.nan)
            else:
                txtm = fMod.readline().strip()
                valsMod = [float(txtm) if txtm and float(txtm)!=missingCode else math.nan]

        # Skip outside period
        if not doWeWantThisDatum(dataPeriod, obs_m):
            obs_d, obs_m, obs_y, obsSeason = increaseObsDate(obs_d, obs_m, obs_y, obsSeason)
            if fMod:
                mod_d, mod_m, mod_y, modSeason, length, leap = increaseDate(mod_d, mod_m, mod_y, modSeason, length, leap)
            continue

        # Append valid
        if fObs and not math.isnan(valObs) and (not applyThreshold or valObs>=threshold):
            observedData.append(valObs)
        if fMod:
            for idx, v in enumerate(valsMod):
                if not math.isnan(v) and (not applyThreshold or v>=threshold):
                    modelledData[idx].append(v)

        # Advance one day each
        obs_d, obs_m, obs_y, obsSeason = increaseObsDate(obs_d, obs_m, obs_y, obsSeason)
        if fMod:
            mod_d, mod_m, mod_y, modSeason, length, leap = increaseDate(mod_d, mod_m, mod_y, modSeason, length, leap)

    # Close files
    for fh in (fObs, fMod):
        if fh: fh.close()

    # Debug counts
    print(f"Loaded {len(observedData)} observed records")
    if fMod:
        print(f"Loaded {len(modelledData[0])} modelled records")

    # Combine for range
    dataToRange = observedData.copy()
    if fMod and ensembleOption!='member':
        for series in modelledData:
            dataToRange.extend(series)
    elif fMod and ensembleOption=='member':
        dataToRange.extend(modelledData[ensembleWanted-1])

    if not dataToRange:
        print("[error] No data to plot.")
        return

    lo, hi = min(dataToRange), max(dataToRange)
    width = (hi-lo)/numPdfCategories if hi!=lo else 1e-6
    binEdges = [lo + i*width for i in range(numPdfCategories+1)]
    xValues = binEdges[:-1]

    print("Bin edges (xValues):", xValues)

    # Count & standardise per series
    def compute_density(data_series):
        counts = [0]*numPdfCategories
        for v in data_series:
            if lo <= v < hi:
                counts[int((v-lo)/width)] += 1
        maxc = max(counts) if counts else 1
        return [c / maxc for c in counts]

    obsDensity = compute_density(observedData)
    modDensities = [compute_density(series) for series in modelledData] if fMod else []

    # ▶ DEBUG: display densities in terminal
    print("Observed densities:", obsDensity)
    if fMod:
        for idx, dens in enumerate(modDensities, start=1):
            print(f"Ensemble {idx} densities:", dens)

    # 4) Build legend series
    series = [(obsLabel, obsDensity)] if fObs else []
    if fMod:
        if ensembleOption == 'member':
            series.append((f"{modLabel} Ensemble {ensembleWanted}", modDensities[ensembleWanted-1]))
        elif ensembleOption in ('all', 'allMembers'):
            for i, dens in enumerate(modDensities, start=1):
                series.append((f"{modLabel} Ensemble {i}", dens))
        elif ensembleOption == 'mean':
            mean_vals = [sum(vals[i] for vals in modDensities)/len(modDensities) for i in range(numPdfCategories)]
            series.append((f"{modLabel} Mean", mean_vals))
        elif ensembleOption == 'allPlusMean':
            for i, dens in enumerate(modDensities, start=1):
                series.append((f"{modLabel} Ensemble {i}", dens))
            mean_vals = [sum(vals[i] for vals in modDensities)/len(modDensities) for i in range(numPdfCategories)]
            series.append((f"{modLabel} Mean", mean_vals))

    print(applyThreshold, threshold)

    # Plot
    plt.figure()
    for label, y in series:
        if label == obsLabel:
            col = 'blue'
        elif 'Mean' in label:
            col = 'limegreen'
        else:
            col = 'red'
        plt.plot(xValues, y, label=label, color=col, linewidth=1.5)
        # Add export action to the toolbar (not menu)
    def add_export_to_toolbar():
        manager = plt.get_current_fig_manager()
        if hasattr(manager, 'toolbar') and isinstance(manager.toolbar, NavigationToolbar):
            # Set icon path (you can use your own icon here)
            icon_path = 'src/images/exportsvg.svg'  # replace with a valid PNG/SVG path on your system
    
            export_action = QAction(QIcon(icon_path), "", manager.toolbar)
            export_action.setToolTip("Export CSV")  # ✅ Hover text
            export_action.triggered.connect(lambda: export_series_to_csv(xValues, series))
            manager.toolbar.addAction(export_action)  # ✅ this puts it directly on the toolbar
    
    # Inject before show
    add_export_to_toolbar()
    plt.xlabel('Value')
    plt.ylabel('Standardised Density')
    plt.legend(loc='best')
    plt.tight_layout()
    plt.show()
