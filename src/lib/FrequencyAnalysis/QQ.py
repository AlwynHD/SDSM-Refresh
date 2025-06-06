# src/lib/FrequencyAnalysis/QQ.py

import os
import math
import csv
import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication, QFileDialog, QAction
from PyQt5.QtGui import QIcon
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from datetime import date
from typing import Optional, Callable

from src.lib.FrequencyAnalysis.frequency_analysis_functions import (
    doWeWantThisDatum,
    calcPercentile,
    increaseDate,
    getSeason,
    globalMissingCode,export_qq_matrix_to_csv
)


def qqPlot(
    observedFilePath: str,
    modelledFilePath: str,
    analysisStartDate: date,
    analysisEndDate: date,
    globalStartDate: date,
    ensembleMode: str,          # 'allMembers', 'ensembleMean', 'ensembleMember', 'allPlusMean'
    ensembleIndex: Optional[int],
    dataPeriod: int,
    applyThreshold: bool,
    thresholdValue: float,
    exitAnalysesFunc: Callable[[], bool]
):
    """
    Generate a QQ-plot by mirroring the same file-streaming logic as linePlot,
    then computing quantiles of the collected daily pairs.
    """
    # 1) Dates must be in correct order
    if analysisStartDate >= analysisEndDate:
        raise ValueError("Start date must be before end date.")

    # 2) Files must exist
    if not os.path.exists(observedFilePath) or not os.path.exists(modelledFilePath):
        raise ValueError("Both observed and modelled files must exist.")
    obsLabel = os.path.basename(observedFilePath)
    modLabel = os.path.basename(modelledFilePath)

    # 3) Open the two streams
    fObs = open(observedFilePath, 'r')
    fMod = open(modelledFilePath, 'r')

    # 4) Determine ensembles by sampling first model line
    first_line = fMod.readline().rstrip("\n")
    ens_count = len(first_line) // 14 if len(first_line) > 15 else 1
    fMod.seek(0)

    # 5) Initialize date counters exactly as linePlot
    currentDay, currentMonth, currentYear = int(globalStartDate.strftime("%d")), int(globalStartDate.strftime("%m")), int(globalStartDate.strftime("%Y"))
    currentSeason = getSeason(currentMonth)
    yearLength, leapValue = 1, 1
    current = date(currentYear, currentMonth, currentDay)

    # 6) Skip file lines until analysisStartDate
    while current < analysisStartDate:
        if exitAnalysesFunc():
            return
        fObs.readline()
        fMod.readline()
        currentDay, currentMonth, currentYear, currentSeason, yearLength, leapValue = \
            increaseDate(currentDay, currentMonth, currentYear, currentSeason, yearLength, leapValue)
        current = date(currentYear, currentMonth, currentDay)

    # 7) Collect to lists
    obs_vals = []
    mod_vals_list = [[] for _ in range(ens_count)]

    while current <= analysisEndDate:
        if exitAnalysesFunc():
            return
        # Read one day from each file
        try:
            raw_o = float(fObs.readline().strip())
        except:
            raw_o = globalMissingCode

        # read model line
        line_m = fMod.readline().rstrip("\n").ljust(14 * ens_count)
        mods = []
        for i in range(ens_count):
            seg = line_m[i*14:(i+1)*14].strip()
            try:
                v = float(seg) if seg else globalMissingCode
            except:
                v = globalMissingCode
            mods.append(v)

        # Period filter
        if doWeWantThisDatum(dataPeriod, current.month):
            # Check obs and mods
            if raw_o != globalMissingCode and (not applyThreshold or raw_o >= thresholdValue):
                if all(v != globalMissingCode and (not applyThreshold or v >= thresholdValue) for v in mods):
                    obs_vals.append(raw_o)
                    for idx, v in enumerate(mods):
                        mod_vals_list[idx].append(v)

        # Advance the date
        currentDay, currentMonth, currentYear, currentSeason, yearLength, leapValue = \
            increaseDate(currentDay, currentMonth, currentYear, currentSeason, yearLength, leapValue)
        current = date(currentYear, currentMonth, currentDay)

    # 8) Require at least 100 paired values
    if len(obs_vals) < 100 or any(len(m) < 100 for m in mod_vals_list):
        counts = [len(obs_vals)] + [len(m) for m in mod_vals_list]
        raise ValueError(
            f"Insufficient data (<100) to plot (obs={counts[0]}, " +
            ", ".join(f"mod{i+1}={counts[i+1]}" for i in range(ens_count)) + ")"
        )

    # 9) Compute quantiles 1–99%
    obs_q = [calcPercentile(obs_vals, p) for p in range(1,100)]
    ensemble_q = [
        [calcPercentile(mod_vals_list[i], p) for p in range(1,100)]
        for i in range(ens_count)
    ]

    # --- DEBUG: dump quantile arrays ---
    #print(f"\nQQ-Plot Debug: {len(obs_q)} observed quantiles (1–99%):")
    #print(obs_q)
    #for idx, qlist in enumerate(ensemble_q, start=1):
    #    print(f"QQ-Plot Debug: Ensemble #{idx} quantiles:")
    #    print(qlist)

    if ensembleMode in ('ensembleMean', 'allPlusMean'):
        mean_q = [sum(ensemble_q[j][i] for j in range(ens_count)) / ens_count for i in range(99)]
    #    print("QQ-Plot Debug: Ensemble MEAN quantiles:")
    #    print(mean_q)

    # 10) Scatter according to ensembleMode
    plt.figure()
    if ensembleMode == 'allMembers':
        for q in ensemble_q:
            plt.scatter(q, obs_q, s=50, c='k')
    elif ensembleMode == 'ensembleMean':
        plt.scatter(mean_q, obs_q, s=50, c='orange')
    elif ensembleMode == 'ensembleMember':
        if ensembleIndex is None or ensembleIndex < 1 or ensembleIndex > ens_count:
            raise ValueError(f"Invalid ensembleIndex {ensembleIndex!r}")
        plt.scatter(ensemble_q[ensembleIndex-1], obs_q, s=50, c='k')
    else:  # allPlusMean
        for q in ensemble_q:
            plt.scatter(q, obs_q, s=50, c='k')
        plt.scatter(mean_q, obs_q, s=50, c='orange')

    # 11) 1:1 line
    all_mod = [v for q in ensemble_q for v in q]
    if ensembleMode in ('ensembleMean','allPlusMean'):
        all_mod.extend(mean_q)
    M = max(max(obs_q), max(all_mod))
    plt.plot([0, M], [0, M], 'b-', linewidth=2)
    # Add export action to the toolbar (not menu)
    def add_export_to_toolbar(mode, obs_q, ensemble_q, mean_q=None, ensembleIndex=None):
        manager = plt.get_current_fig_manager()
        if hasattr(manager, 'toolbar') and isinstance(manager.toolbar, NavigationToolbar):
            icon_path = 'src/images/exportsvg.svg'
            export_action = QAction(QIcon(icon_path), "", manager.toolbar)
            export_action.setToolTip("Export CSV")
    
            # Hook up the correct export based on mode
            if mode == 'allMembers':
                export_action.triggered.connect(lambda: export_qq_matrix_to_csv(obs_q, ensemble_q))
            elif mode == 'ensembleMean':
                export_action.triggered.connect(lambda: export_qq_matrix_to_csv(obs_q, ensemble_q, mean_q, include_mean=True))
            elif mode == 'ensembleMember':
                export_action.triggered.connect(lambda: export_qq_matrix_to_csv(obs_q, [ensemble_q[ensembleIndex - 1]]))
            else:  # allPlusMean or unknown
                export_action.triggered.connect(lambda: export_qq_matrix_to_csv(obs_q, ensemble_q, mean_q, include_mean=True))
    
            manager.toolbar.addAction(export_action) 

    # Inject before show
    add_export_to_toolbar(ensembleMode, obs_q, ensemble_q, mean_q if 'mean_q' in locals() else None, ensembleIndex)
    plt.title("Quantile-Quantile Plot")
    plt.xlabel(modLabel)
    plt.ylabel(obsLabel)
    plt.grid(True)
    plt.tight_layout()
    plt.show()
