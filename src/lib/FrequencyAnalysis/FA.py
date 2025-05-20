import matplotlib.pyplot as plt
import csv
import numpy as np
import configparser
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QMessageBox, QFileDialog, QPushButton
import math
from PyQt5.QtCore import Qt
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
    stripMissing,
    get_seasonal_value,
    export_table_to_csv
)
active_windows = []
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
        success, freqAnalData, noOfXDataPoints, beta, eta, kay = gevAnalysis(
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
            globalMissingCode, True
        )

    if not success:
        return False

    # --- compute obsYears & modYears for stripMissing ---
    obsYearsAvailable = len({d.year for d in observed_dates})
    modYearsAvailable = len({d.year for d in mod_dates_list[0]}) if file2Used else 0

    # --- output mean aboslute error (MAE) ---
    if success and file1Used and file2Used:
        # collect only valid (non‐missing) obs/mod pairs
        errors = []
        for i in range(noOfXDataPoints):
            obs = freqAnalData[i][1]    # column 2 in VB
            mod = freqAnalData[i][3]    # column 4 in VB
            if obs != globalMissingCode and mod != globalMissingCode:
                errors.append(abs(obs - mod))

        if errors:
            mae = sum(errors) / len(errors)
            mae_str = f"{mae:.3f}"
            QMessageBox.information(
                None,
                "Information",
                f"MAE:  {mae_str}"
            )

    # --- output beta, eta and kay ---
    if success and freqModel == 1:
        QMessageBox.information(
            None,
            "GEV Parameters",
            f"β = {beta:.3f}\nη = {eta:.3f}\nk = {kay:.3f}"
        )

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
            ax.plot(x[mask_obs], obs_vals[mask_obs], marker='o', linestyle='-', label=obs_label, color='black')

        # Modeled series
        if file2Used:
            mod_vals = arr[:, file2ColStart - 1]
            mask_mod = mod_vals != globalMissingCode
            ax.plot(x[mask_mod], mod_vals[mask_mod], marker='s', linestyle='--', label=mod_label, color='darkred')
            # Confidence bounds only for all ensembles
            if ensembleIndex == 0 and no_of_ensembles > 1 and percentileWanted > 0:
                lower = arr[:, file2ColStart + 3]
                upper = arr[:, file2ColStart + 1]
                mask_pct = (lower != globalMissingCode) & (upper != globalMissingCode)
                low_pct = percentileWanted/2
                high_pct = 100 - low_pct
                ax.plot(x[mask_pct], lower[mask_pct], marker='^', linestyle=':', label=f'Low {low_pct}%', color='darkred')
                ax.plot(x[mask_pct], upper[mask_pct], marker='v', linestyle=':', label=f'High {high_pct}%', color='darkred')

        ax.set_xlabel('Return period (years)')
        ax.set_ylabel('Value')

        season = 'Annual' if dataPeriodChoice == 0 else durations[dataPeriodChoice]
        fit_map = {0: 'Empirical', 1: 'Generalised Extreme Value', 2: 'Gumbel', 3: 'Stretched Exponential'}
        fit_str = fit_map.get(freqModel, '')
        ax.set_title(f'Period: {season};  Fit: {fit_str}')

        chart_max = x.max() if freqModel == 0 else 100
        ax.set_xlim(0, chart_max)

        # Reorder legend: Observed, Modelled, High %, Low %
        handles, labels = ax.get_legend_handles_labels()
        desired_order = [
            obs_label if obs_label else 'Observed',
            mod_label if mod_label else 'Modelled',
            f'High {100 - percentileWanted/2}%',
            f'Low {percentileWanted/2}%'
        ]
        label_to_handle = dict(zip(labels, handles))
        ordered_handles = [label_to_handle[lbl] for lbl in desired_order if lbl in label_to_handle]
        ordered_labels = [lbl for lbl in desired_order if lbl in label_to_handle]
        ax.legend(ordered_handles, ordered_labels)

        plt.tight_layout()
        plt.show()

    else:
        # --- Create heading text ---
        fit_map = {
            0: 'Empirical',
            1: 'Generalised Extreme Value',
            2: 'Gumbel',
            3: 'Stretched Exponential'
        }
        fit_str = fit_map.get(freqModel, '')
        season=dataPeriodChoice
        seasonal_value=get_seasonal_value(season)
        season_label = f"Season: {seasonal_value}" if currentSeason else "Season: Unknown"
        
        fit_label = f"Fit: {fit_str}" if fit_str else "Fit: Not specified"
        obs_label = f"Observed data: {os.path.basename(observedFilePath)}" if observedFilePath else ""
        mod_label = f"Modelled data: {os.path.basename(modelledFilePath)}" if modelledFilePath else ""
        
        # --- Create heading label ---
        info_text = "\n".join(filter(None, [season_label, fit_label, obs_label, mod_label]))
        info_label = QLabel(info_text)
        info_label.setAlignment(Qt.AlignLeft)        # --- Build headers ---
        headers = ['Return Period']
        if file1Used:
            headers.append('Obs')
        if file2Used:
            headers.append('Mod')
            if ensembleIndex == 0 and no_of_ensembles > 1 and percentileWanted > 0:
                low_pct = percentileWanted / 2
                high_pct = 100 - low_pct
                headers.extend([f'Low {low_pct}%', f'High {high_pct}%'])
        
        # --- Create table ---
        num_cols = len(headers)
        num_rows = noOfXDataPoints
        
        table = QTableWidget()
        table.setColumnCount(num_cols)
        table.setRowCount(num_rows)
        table.setHorizontalHeaderLabels(headers)
        
        # --- Fill table ---
        for row_idx in range(noOfXDataPoints - 1, -1, -1):
            row_data = freqAnalData[row_idx]
            col = 0
            actual_row = noOfXDataPoints - 1 - row_idx
        
            # Return period
            table.setItem(actual_row, col, QTableWidgetItem(f"{row_data[0]:.1f}"))
            col += 1
        
            # Observed
            if file1Used:
                val = row_data[1]
                text = f"{val:.3f}" if val is not None and val != globalMissingCode else "-"
                table.setItem(actual_row, col, QTableWidgetItem(text))
                col += 1
        
            # Modelled
            if file2Used:
                mod = row_data[file2ColStart - 1]
                text = f"{mod:.3f}" if mod is not None and mod != globalMissingCode else "-"
                table.setItem(actual_row, col, QTableWidgetItem(text))
                col += 1
        
                if ensembleIndex == 0 and no_of_ensembles > 1 and percentileWanted > 0:
                    lo = row_data[file2ColStart + 3]
                    hi = row_data[file2ColStart + 1]
                    lo_text = f"{lo:.3f}" if lo is not None and lo != globalMissingCode else "-"
                    hi_text = f"{hi:.3f}" if hi is not None and hi != globalMissingCode else "-"
                    table.setItem(actual_row, col, QTableWidgetItem(lo_text))
                    col += 1
                    table.setItem(actual_row, col, QTableWidgetItem(hi_text))
        
        # --- Table settings ---
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        
        # --- Show in a new PyQt window ---
        window = QWidget()
        window.setWindowTitle("Frequency Analysis Table")
        layout = QVBoxLayout()
        layout.addWidget(QLabel("📊 Frequency Analysis Results"))
        layout.addWidget(info_label)
        layout.addWidget(table)
        export_btn = QPushButton("Export Table to CSV")
        export_btn.clicked.connect(lambda: export_table_to_csv(table))
        layout.addWidget(export_btn)
        window.setLayout(layout)
        window.resize(700, 500)
        window.show()
        active_windows.append(window)
        
    return True
