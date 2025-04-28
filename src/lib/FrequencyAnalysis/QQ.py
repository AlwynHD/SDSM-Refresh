import os
import numpy as np
import math
from datetime import timedelta
import matplotlib.pyplot as plt
from typing import Optional, Callable

from src.lib.FrequencyAnalysis.frequency_analysis_functions import (
    doWeWantThisDatum,
    calcPercentile,
    fsDateOk,
    feDateOk,
    globalMissingCode
)


def qqPlot(
    observedFilePath: str,
    modelledFilePath: str,
    analysisStartDate,
    analysisEndDate,
    ensembleMode: str,
    ensembleIndex: Optional[int],
    dataPeriod: int,
    applyThreshold: bool,
    thresholdValue: float,
    exitAnalysesFunc: Callable[[], bool]
):
    """
    Generate a Quantile-Quantile plot comparing observed and modelled series.
    """
    # 1) Validate dates
    valid_fs, fs, _ = fsDateOk(analysisStartDate, analysisEndDate, analysisStartDate)
    valid_fe, fe, _ = feDateOk(analysisStartDate, analysisEndDate, analysisEndDate)
    if not valid_fs:
        raise ValueError("Invalid start date.")
    if not valid_fe:
        raise ValueError("Invalid end date.")

    # 2) Check files
    if not os.path.exists(observedFilePath) or not os.path.exists(modelledFilePath):
        raise ValueError("Both observed and modelled files must exist.")
    obsLabel = os.path.basename(observedFilePath)
    modLabel = os.path.basename(modelledFilePath)

    # 3) Read raw lines
    obsLines = open(observedFilePath).read().splitlines()
    modLines = open(modelledFilePath).read().splitlines()
    total_days = (fe - fs).days + 1
    if len(obsLines) < total_days or len(modLines) < total_days:
        raise IOError("Data files shorter than selected date range.")

    # 4) Determine ensemble count
    firstMod = modLines[0]
    ens_count = len(firstMod) // 14 if len(firstMod) > 15 else 1

    # 5) Build date list
    dates = [fs + timedelta(days=i) for i in range(total_days)]

    # 6) Read and filter series
    obs_vals = []
    mod_vals = [[] for _ in range(ens_count)]
    for idx, dt in enumerate(dates):
        if exitAnalysesFunc():
            return
        # period filter
        if not doWeWantThisDatum(dataPeriod, dt.month):
            continue
        # observed
        raw_o = float(obsLines[idx].strip())
        if raw_o == globalMissingCode or (applyThreshold and raw_o < thresholdValue):
            continue
        obs_vals.append(raw_o)
        # modelled
        line = modLines[idx].ljust(14 * ens_count)
        row = []
        for e in range(ens_count):
            seg = line[e*14:(e+1)*14].strip()
            v = float(seg) if seg else globalMissingCode
            if v == globalMissingCode or (applyThreshold and v < thresholdValue):
                row.append(math.nan)
            else:
                row.append(v)
        # ensemble logic
        arr = np.array(row, dtype=float)
        if ensembleMode == 'ensembleMean':
            mean = np.nanmean(arr)
            mod_vals = [mod_vals[0] + [mean]] if ens_count == 1 else [lst + [mean] for lst in mod_vals[:1]]
        elif ensembleMode == 'ensembleMember' and ensembleIndex is not None:
            sel = arr[ensembleIndex-1]
            mod_vals = [[sel] for _ in range(1)]
        elif ensembleMode == 'allPlusMean':
            # each ensemble plus overall mean as last column
            for i, v in enumerate(arr):
                mod_vals[i].append(v)
            mean = np.nanmean(arr)
            mod_vals.append([mean])
        else:  # 'allMembers'
            for i, v in enumerate(arr):
                mod_vals[i].append(v)

    obs = np.array(obs_vals, dtype=float)
    # stack mod_vals into 2D array (time × ensembles)
    mod = np.column_stack(mod_vals)

    # 7) Ensure ≥100 points
    if len(obs) < 100 or any(np.count_nonzero(~np.isnan(mod[:, c])) < 100 for c in range(mod.shape[1])):
        raise ValueError("Insufficient data (<100) to plot.")

    # 8) Compute quantiles (1–99%) via shared calcPercentile
    obs_q = np.array([calcPercentile(obs_vals, p) for p in range(1, 100)])

    # 9) Plot
    plt.figure()
    for c in range(mod.shape[1]):
        col = mod[:, c]
        col = col[~np.isnan(col)]
        mq = [calcPercentile(col.tolist(), p) for p in range(1, 100)]
        plt.scatter(mq, obs_q, s=10, c='k')

    M = max(np.nanmax(obs_q), *(max(mq) for mq in
                                 ([calcPercentile(mod[:, c].tolist(), p) for p in range(1, 100)]
                                  for c in range(mod.shape[1]))))
    plt.plot([0, M], [0, M], 'b-', linewidth=2)

    plt.title("Quantile-Quantile Plot")
    plt.xlabel(modLabel)
    plt.ylabel(obsLabel)
    plt.grid(True)
    plt.tight_layout()
    plt.show()
