import matplotlib.pyplot as plt
import numpy as np
import configparser
import math
from datetime import date
import os
from src.lib.FrequencyAnalysis.frequency_analysis_functions import (
    getSeason,
    increaseDate,
    doWeWantThisDatum,
    empiricalAnalysis,
    gevAnalysis,
    gumbelAnalysis,
    stretchedAnalysis,
    convertValue,
    stripMissing
)

def frequency_analysis(
    presentation: str,
    observedFilePath: str,
    modelledFilePath: str,
    fsDate,
    feDate,
    dataPeriodChoice: int,
    applyThreshold: bool,
    freqThresh: float,
    durations: list,
    percentileWanted: float,
    ensembleIndex: int,
    freqModel: int
) -> bool:
    # --- load settings ---
    config = configparser.ConfigParser()
    config.read("src/lib/settings.ini")
    s = config["Settings"]
    globalStartDate   = convertValue('globalsdate', s['globalsdate'])
    globalMissingCode = convertValue('globalmissingcode', s['globalmissingcode'])
    thresholdValue = float(convertValue('thresh', s['thresh']))

    # --- open files ---
    fObs = open(observedFilePath, 'r') if observedFilePath else None
    fMod = open(modelledFilePath, 'r') if modelledFilePath else None

    # --- detect ensembles ---
    ensemble_present = False
    no_of_ensembles = 1
    if fMod:
        first_line = fMod.readline().rstrip('\n')
        if len(first_line) > 15:
            ensemble_present = True
            no_of_ensembles = len(first_line) // 14
        fMod.seek(0)

    # --- skip to fsDate ---
    cd, cm, cy = map(int, [
        globalStartDate.strftime("%d"),
        globalStartDate.strftime("%m"),
        globalStartDate.strftime("%Y")
    ])
    current = date(cy, cm, cd)
    currentSeason = getSeason(cm)
    yearLength, leapValue = 1, 1
    while current < fsDate:
        if fObs: fObs.readline()
        if fMod: fMod.readline()
        cd, cm, cy, currentSeason, yearLength, leapValue = increaseDate(
            cd, cm, cy, currentSeason, yearLength, leapValue
        )
        current = date(cy, cm, cd)

    # --- read observed ---
    observed_data, observed_dates = [], []
    cd_o, cm_o, cy_o = cd, cm, cy
    current_o = current
    while fObs and current_o <= feDate:
        raw = fObs.readline().strip()
        val = float(raw) if raw else math.nan
        if val == globalMissingCode:
            val = math.nan
        if doWeWantThisDatum(dataPeriodChoice, cm_o):
            if not (math.isnan(val) or (applyThreshold and val < thresholdValue)):
                observed_data.append(val)
                observed_dates.append(current_o)
        cd_o, cm_o, cy_o, currentSeason, yearLength, leapValue = increaseDate(
            cd_o, cm_o, cy_o, currentSeason, yearLength, leapValue
        )
        current_o = date(cy_o, cm_o, cd_o)

    # --- read modelled ---
    modelled_data = [[] for _ in range(no_of_ensembles)]
    mod_dates_list = [[] for _ in range(no_of_ensembles)]
    cd_m, cm_m, cy_m = cd, cm, cy
    current_m = current
    while fMod and current_m <= feDate:
        if ensemble_present:
            line = fMod.readline().rstrip("\n")
            vals = []
            for i in range(no_of_ensembles):
                txt = line[i*14:(i+1)*14].strip()
                v = float(txt) if txt else math.nan
                if v == globalMissingCode:
                    v = math.nan
                vals.append(v)
        else:
            raw = fMod.readline().strip()
            v = float(raw) if raw else math.nan
            if v == globalMissingCode:
                v = math.nan
            vals = [v]

        if doWeWantThisDatum(dataPeriodChoice, cm_m):
            for idx, m in enumerate(vals):
                if not (math.isnan(m) or (applyThreshold and m < thresholdValue)):
                    modelled_data[idx].append(m)
                    mod_dates_list[idx].append(current_m)

        cd_m, cm_m, cy_m, currentSeason, yearLength, leapValue = increaseDate(
            cd_m, cm_m, cy_m, currentSeason, yearLength, leapValue
        )
        current_m = date(cy_m, cm_m, cd_m)

    if fObs: fObs.close()
    if fMod: fMod.close()

    # --- filter to specific ensemble if requested ---
    if ensembleIndex > 0 and ensemble_present:
        sel = ensembleIndex - 1
        modelled_data = [modelled_data[sel]]
        mod_dates_list = [mod_dates_list[sel]]
        no_of_ensembles = 1

    # --- prepare parameters ---
    noOfObserved     = len(observed_data)
    noOfModelledList = [len(lst) for lst in modelled_data]
    file1Used        = bool(observedFilePath)
    file2Used        = bool(modelledFilePath)
    file2ColStart    = 4 if file1Used and file2Used else (2 if file2Used else None)
    noOfXCols        = (
        (8 if no_of_ensembles>1 and durations else 4)
        if file1Used and file2Used else
        (6 if no_of_ensembles>1 and durations else 2)
        if file2Used else 2
    )

    # --- dispatch analysis ---
    if freqModel == 0:
        success, freqAnalData, noOfXDataPoints = empiricalAnalysis(
            observed_dates, observed_data,
            mod_dates_list, modelled_data,
            no_of_ensembles,
            int(applyThreshold), thresholdValue,
            file1Used, file2Used,
            None, noOfXCols, file2ColStart,
            percentileWanted,
            globalMissingCode
        )
    elif freqModel == 1:
        success, freqAnalData, noOfXDataPoints = gevAnalysis(
            observed_dates, observed_data,
            mod_dates_list, modelled_data,
            no_of_ensembles,
            int(applyThreshold), thresholdValue,
            file1Used, file2Used,
            None,
            noOfXCols, file2ColStart,
            percentileWanted,
            globalMissingCode
        )
    elif freqModel == 2:
        success, freqAnalData, noOfXDataPoints = gumbelAnalysis(
            observed_dates, observed_data,
            mod_dates_list, modelled_data,
            no_of_ensembles,
            int(applyThreshold), thresholdValue,
            file1Used, file2Used,
            None,
            noOfXCols, file2ColStart,
            percentileWanted,
            globalMissingCode
        )
    else:
        success, freqAnalData, noOfXDataPoints = stretchedAnalysis(
            observed_dates, observed_data,
            mod_dates_list, modelled_data,
            no_of_ensembles,
            int(applyThreshold), thresholdValue, freqThresh,
            file1Used, file2Used,
            None,
            noOfXCols, file2ColStart,
            percentileWanted,
            globalMissingCode
        )

    if not success:
        return False

    # --- compute obsYears & modYears for stripMissing ---
    obsYearsAvailable = len({d.year for d in observed_dates})
    modYearsAvailable = len({d.year for d in mod_dates_list[0]}) if file2Used else 0

    # --- VB-style StripMissing for empirical/tabular ---
    if freqModel == 0 and file1Used and file2Used:
        freqAnalData, noOfXDataPoints = stripMissing(
            freqAnalData,
            obsYearsAvailable,
            modYearsAvailable,
            noOfXCols
        )

    # --- output ---
    if presentation.lower() == 'graphical':
        arr = np.array(freqAnalData, dtype=float)
        x = arr[:, 0]

        obs_label = os.path.basename(observedFilePath) if file1Used else None
        mod_label = os.path.basename(modelledFilePath) if file2Used else None

        fig, ax = plt.subplots()

        # Observed series
        if file1Used:
            obs_vals = arr[:, 1]
            mask_obs = obs_vals != globalMissingCode
            ax.plot(x[mask_obs], obs_vals[mask_obs], marker='o', linestyle='-', label=obs_label)

        # Modeled series
        if file2Used:
            mod_vals = arr[:, file2ColStart - 1]
            mask_mod = mod_vals != globalMissingCode
            ax.plot(x[mask_mod], mod_vals[mask_mod], marker='s', linestyle='--', label=mod_label)
            # Confidence bounds only for all ensembles
            if ensembleIndex == 0 and no_of_ensembles > 1 and percentileWanted > 0:
                lower = arr[:, file2ColStart + 3]
                upper = arr[:, file2ColStart + 1]
                mask_pct = (lower != globalMissingCode) & (upper != globalMissingCode)
                low_pct = percentileWanted/2
                high_pct = 100 - low_pct
                ax.plot(x[mask_pct], lower[mask_pct], marker='^', linestyle=':', label=f'Low {low_pct:.0f}%')
                ax.plot(x[mask_pct], upper[mask_pct], marker='v', linestyle=':', label=f'High {high_pct:.0f}%')

        ax.set_xlabel('Return period (years)')
        ax.set_ylabel('Value')

        season = 'Annual' if dataPeriodChoice == 0 else durations[dataPeriodChoice]
        fit_map = {0: 'Empirical', 1: 'Generalised Extreme Value', 2: 'Gumbel', 3: 'Stretched Exponential'}
        fit_str = fit_map.get(freqModel, '')
        ax.set_title(f'Period: {season};  Fit: {fit_str}')

        chart_max = x.max() if freqModel == 0 else 100
        ax.set_xlim(0, chart_max)

        ax.legend()
        plt.tight_layout()
        plt.show()

    else:
        headers = ['Return Period']
        if file1Used:
            headers.append('Obs')
        if file2Used:
            headers.append('Mod')
            if ensembleIndex == 0 and no_of_ensembles > 1 and percentileWanted > 0:
                low_pct = percentileWanted/2
                high_pct = 100 - low_pct
                headers.extend([f'Low {low_pct}%', f'High {high_pct}%'])
        print("  ".join(f"{h:>12}" for h in headers))

        for idx in range(noOfXDataPoints - 1, -1, -1):
            row = freqAnalData[idx]
            out = []
            rp = row[0]
            out.append(f"{rp:12.1f}")
            if file1Used:
                v = row[1]
                out.append(f"{v:12.3f}" if (v is not None and v != globalMissingCode) else f"{'-':>12}")
            if file2Used:
                m = row[file2ColStart - 1]
                out.append(f"{m:12.3f}" if (m is not None and m != globalMissingCode) else f"{'-':>12}")
                if ensembleIndex == 0 and no_of_ensembles > 1 and percentileWanted > 0:
                    lo, up = row[file2ColStart+3], row[file2ColStart+1]
                    out.append(f"{lo:12.3f}" if (lo is not None and lo != globalMissingCode) else f"{'-':>12}")
                    out.append(f"{up:12.3f}" if (up is not None and up != globalMissingCode) else f"{'-':>12}")
            print("  ".join(out))

    return True
