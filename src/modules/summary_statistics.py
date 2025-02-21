import sys
import csv
from datetime import datetime
import numpy as np
from scipy import stats
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QRadioButton,
    QCheckBox, QSizePolicy, QFrame, QFileDialog, QApplication, QTextEdit
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# ---------------- Global Constants ----------------
GLOBAL_MISSING = np.nan
N_DAY_TOTAL = 3  # You can change this value as needed

# ---------------- Utility Functions ----------------

def get_season(month):
    """Return season code (1: Winter, 2: Spring, 3: Summer, 4: Autumn) based on month."""
    if month in [12, 1, 2]:
        return 1  # Winter
    elif month in [3, 4, 5]:
        return 2  # Spring
    elif month in [6, 7, 8]:
        return 3  # Summer
    elif month in [9, 10, 11]:
        return 4  # Autumn

def read_sim_file(sim_filepath):
    """
    Reads the SIM file (metadata) and returns a dictionary.
    Expected lines (in order):
      NPredictors, SeasonCode, LocalYearIndicator, DataSDate, NDaysR, RainYes, EnsembleSize, ...
    """
    meta = {}
    try:
        with open(sim_filepath, 'r') as f:
            meta['NPredictors'] = int(f.readline().strip())
            meta['SeasonCode'] = int(f.readline().strip())
            meta['LocalYearIndicator'] = int(f.readline().strip())
            meta['DataSDate'] = datetime.strptime(f.readline().strip(), "%d/%m/%Y")
            meta['NDaysR'] = int(f.readline().strip())
            meta['RainYes'] = f.readline().strip().upper() in ['TRUE', '1']
            meta['EnsembleSize'] = int(f.readline().strip())
            # Additional parameters can be read as needed...
    except Exception as e:
        print("Error reading SIM file:", e)
    return meta

def read_scenario_file(filepath, analysis_start):
    """
    Reads the scenario (*.OUT) file into a list of dictionaries.
    Assumes the file is a CSV with headers: "date", "value", and optionally "ensemble".
    Dates are assumed to be in "dd/mm/yyyy" format.
    Only rows with a date >= analysis_start are returned.
    """
    data = []
    try:
        with open(filepath, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            start_dt = datetime.strptime(analysis_start, "%d/%m/%Y")
            for row in reader:
                try:
                    date_val = datetime.strptime(row['date'], "%d/%m/%Y")
                except Exception as e:
                    continue
                if date_val >= start_dt:
                    try:
                        value = float(row['value'])
                    except:
                        value = GLOBAL_MISSING
                    ensemble = int(row['ensemble']) if 'ensemble' in row and row['ensemble'].strip() != "" else 1
                    data.append({"date": date_val, "value": value, "ensemble": ensemble})
    except Exception as e:
        print("Error reading scenario file:", e)
    return data

def bin_data_by_period(data):
    """
    Bins the input data (a list of dicts with keys 'date', 'value', 'ensemble')
    into 17 periods:
      1-12: months,
      13-16: seasons (season code + 12),
      17: annual.
    Returns a dictionary: bins[period][ensemble] = numpy array of values.
    """
    bins = {period: {} for period in range(1, 18)}
    for entry in data:
        ens = entry.get("ensemble", 1)
        date_obj = entry["date"]
        value = entry["value"]
        month = date_obj.month
        season = get_season(month)
        # Bin by month:
        if ens not in bins[month]:
            bins[month][ens] = []
        bins[month][ens].append(value)
        # Bin by season (offset by 12):
        if ens not in bins[season + 12]:
            bins[season + 12][ens] = []
        bins[season + 12][ens].append(value)
        # Bin by annual:
        if ens not in bins[17]:
            bins[17][ens] = []
        bins[17][ens].append(value)
    for period in bins:
        for ens in bins[period]:
            bins[period][ens] = np.array(bins[period][ens])
    return bins

def compute_basic_stats(values, thresh=None, rain_mode=False):
    """
    Computes basic statistics: mean, min, max, sum, count and percentage wet (if rain_mode is True).
    """
    if values.size == 0:
        return { 'mean': GLOBAL_MISSING, 'min': GLOBAL_MISSING, 'max': GLOBAL_MISSING, 'sum': GLOBAL_MISSING, 'count': 0 }
    if rain_mode and thresh is not None:
        valid = values[values > thresh]
        dry = values[values <= thresh]
    else:
        valid = values
        dry = np.array([])
    stats_dict = {
        'mean': np.mean(valid),
        'min': np.min(valid),
        'max': np.max(valid),
        'sum': np.sum(valid),
        'count': valid.size,
        'pct_wet': valid.size / (valid.size + dry.size) if (valid.size + dry.size) > 0 else GLOBAL_MISSING
    }
    return stats_dict

def compute_acf(values):
    """Computes lag-1 autocorrelation of the values."""
    if len(values) < 2:
        return GLOBAL_MISSING
    return np.corrcoef(values[:-1], values[1:])[0, 1]

def compute_percentiles(values, percentiles=[25, 50, 75, 95]):
    """
    Computes requested percentiles and returns a dictionary, plus IQR.
    """
    result = {}
    for p in percentiles:
        result[f'p{p}'] = np.percentile(values, p)
    result['iqr'] = result['p75'] - result['p25']
    return result

def compute_moments(values):
    """Compute variance and skewness for an array of values."""
    count = values.size
    if count < 2:
        return GLOBAL_MISSING, GLOBAL_MISSING
    mean_val = np.mean(values)
    variance = np.sum((values - mean_val) ** 2) / (count - 1)
    std_val = np.sqrt(variance)
    if std_val == 0:
        skewness = 0
    else:
        skewness = np.sum((values - mean_val) ** 3) / (count * (std_val ** 3))
    return variance, skewness

def compute_N_day_total(values, N):
    """
    Computes the maximum sum over any consecutive N days.
    """
    if values.size < N:
        return 0
    max_sum = 0
    for i in range(values.size - N + 1):
        window_sum = np.sum(values[i:i+N])
        if window_sum > max_sum:
            max_sum = window_sum
    return max_sum

def compute_spell_statistics(values, thresh):
    """
    Computes wet and dry spell statistics.
    Returns a dictionary with mean, max, std, and median for wet and dry spells.
    A spell is defined as a consecutive run of values > thresh (wet) or <= thresh (dry).
    """
    wet_spells = []
    dry_spells = []
    current_wet = 0
    current_dry = 0
    for v in values:
        if v > thresh:
            if current_dry > 0:
                dry_spells.append(current_dry)
                current_dry = 0
            current_wet += 1
        else:
            if current_wet > 0:
                wet_spells.append(current_wet)
                current_wet = 0
            current_dry += 1
    if current_wet > 0:
        wet_spells.append(current_wet)
    if current_dry > 0:
        dry_spells.append(current_dry)
    def spell_stats(spells):
        if len(spells) == 0:
            return GLOBAL_MISSING, GLOBAL_MISSING, GLOBAL_MISSING, GLOBAL_MISSING
        return (np.mean(spells),
                np.max(spells),
                np.std(spells, ddof=1) if len(spells) > 1 else 0,
                np.median(spells))
    mean_wet, max_wet, std_wet, median_wet = spell_stats(wet_spells)
    mean_dry, max_dry, std_dry, median_dry = spell_stats(dry_spells)
    return {
        'mean_wet_spell': mean_wet,
        'max_wet_spell': max_wet,
        'std_wet_spell': std_wet,
        'median_wet_spell': median_wet,
        'mean_dry_spell': mean_dry,
        'max_dry_spell': max_dry,
        'std_dry_spell': std_dry,
        'median_dry_spell': median_dry,
    }

def compute_t_test_custom(base_values, future_values):
    """
    Performs a custom independent t-test using the formula:
      t = |mean1 - mean2| / sqrt(var1/n1 + var2/n2)
    and computes degrees of freedom via:
      df = ((var1/n1 + var2/n2)**2) / ((var1**2)/(n1**2*(n1-1)) + (var2**2)/(n2**2*(n2-1)))
    """
    n1 = base_values.size
    n2 = future_values.size
    if n1 < 2 or n2 < 2:
        return GLOBAL_MISSING, GLOBAL_MISSING
    mean1 = np.mean(base_values)
    mean2 = np.mean(future_values)
    var1 = np.var(base_values, ddof=1)
    var2 = np.var(future_values, ddof=1)
    denom = np.sqrt(var1/n1 + var2/n2)
    if denom < 1e-6:
        return GLOBAL_MISSING, GLOBAL_MISSING
    t_stat = abs(mean1 - mean2) / denom
    df = ((var1/n1 + var2/n2)**2) / (((var1**2)/(n1**2*(n1-1))) + ((var2**2)/(n2**2*(n2-1))))
    return t_stat, df

def compute_advanced_stats(bins, meta, thresh=5.0):
    """
    For each period (1..17) and each ensemble in bins, compute basic stats plus:
      - Variance and skewness (moments)
      - Maximum N-day total (using N_DAY_TOTAL)
      - If rain mode is enabled (meta['RainYes'] True), compute wet/dry spell statistics.
    Returns a nested dictionary: advanced[period][ensemble] = dict of stats.
    """
    advanced = {}
    rain_mode = meta.get('RainYes', False)
    for period, ens_data in bins.items():
        advanced[period] = {}
        for ens, values in ens_data.items():
            stats_basic = compute_basic_stats(values, thresh=thresh, rain_mode=rain_mode)
            acf_val = compute_acf(values)
            percentiles = compute_percentiles(values)
            variance, skewness = compute_moments(values)
            n_day_total = compute_N_day_total(values, N_DAY_TOTAL)
            # For precipitation, compute spell stats
            spell_stats = {}
            if rain_mode:
                spell_stats = compute_spell_statistics(values, thresh)
            # Combine all advanced stats:
            combined = {}
            combined.update(stats_basic)
            combined.update(percentiles)
            combined['acf'] = acf_val
            combined['variance'] = variance
            combined['skewness'] = skewness
            combined['N_day_total'] = n_day_total
            if rain_mode:
                combined.update(spell_stats)
            advanced[period][ens] = combined
    return advanced

def compute_delta_between_periods(base_stats, future_stats, delta_mode='percentage'):
    """
    Given two dictionaries of stats (for one period), compute delta values.
    Returns a new dictionary with the delta for each stat.
    """
    delta = {}
    for key in base_stats:
        base_val = base_stats[key]
        fut_val = future_stats.get(key, GLOBAL_MISSING)
        if np.isnan(base_val) or np.isnan(fut_val):
            delta[key] = GLOBAL_MISSING
        else:
            if delta_mode == 'absolute':
                delta[key] = fut_val - base_val
            else:
                # Avoid division by zero
                if abs(base_val) < 1e-6:
                    delta[key] = GLOBAL_MISSING
                else:
                    delta[key] = 100 * (fut_val - base_val) / abs(base_val)
    return delta

# ---------------- PyQt5 UI Integration ----------------

class ContentWidget(QWidget):
    """
    Summary Statistics UI replicating the legacy layout and functionality.
    This version integrates basic and advanced analysis (moments, N-day totals,
    spell statistics, and a custom t-test routine) without using pandas.
    """
    def __init__(self):
        super().__init__()

        # Instance variables to store file paths and settings
        self.inputFilePath = ""
        self.outputFilePath = ""
        self.simFilePath = ""  # Derived from input file (.OUT --> .SIM)
        self.meta = {}
        self.analysisResults = None
        self.deltaResults = None

        # --- Main Layout ---
        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(10, 10, 10, 10)
        mainLayout.setSpacing(10)
        self.setLayout(mainLayout)

        # --- Toolbar ---
        toolbarLayout = QHBoxLayout()
        toolbarLayout.setSpacing(10)
        toolbarLayout.setContentsMargins(0, 0, 0, 0)

        self.resetButton = QPushButton("Reset")
        self.statsButton = QPushButton("Statistics")
        self.analyseButton = QPushButton("Analyse")
        self.deltaStatsButton = QPushButton("Delta Stats")
        self.settingsButton = QPushButton("Settings")
        for button in [self.resetButton, self.statsButton, self.analyseButton, self.deltaStatsButton, self.settingsButton]:
            button.setFixedSize(90, 40)
            toolbarLayout.addWidget(button)
        toolbarFrame = QFrame()
        toolbarFrame.setLayout(toolbarLayout)
        toolbarFrame.setStyleSheet("background-color: #A9A9A9;")
        mainLayout.addWidget(toolbarFrame)

        # --- Content Area Layout ---
        contentAreaLayout = QHBoxLayout()
        contentAreaLayout.setSpacing(20)

        # --- Left Panel ---
        leftPanelLayout = QVBoxLayout()
        leftPanelLayout.setSpacing(20)

        # Data Source
        dataSourceLabel = QLabel("Data Source")
        dataSourceLabel.setFont(QFont("Arial", 12, QFont.Bold))
        self.modelledButton = QRadioButton("Modelled")
        self.observedButton = QRadioButton("Observed")
        self.modelledButton.setChecked(True)
        dataSourceLayout = QVBoxLayout()
        dataSourceLayout.addWidget(dataSourceLabel)
        dataSourceLayout.addWidget(self.modelledButton)
        dataSourceLayout.addWidget(self.observedButton)
        dataSourceFrame = QFrame()
        dataSourceFrame.setLayout(dataSourceLayout)
        leftPanelLayout.addWidget(dataSourceFrame)

        # Input File
        inputFileLayout = QVBoxLayout()
        inputFileLayout.setSpacing(5)
        inputFileLabel = QLabel("Select Input File")
        self.inputFileButton = QPushButton("Select File")
        self.fileStatusLabel = QLabel("File: Not selected")
        inputFileLayout.addWidget(inputFileLabel)
        inputFileLayout.addWidget(self.inputFileButton)
        inputFileLayout.addWidget(self.fileStatusLabel)
        inputFileFrame = QFrame()
        inputFileFrame.setLayout(inputFileLayout)
        leftPanelLayout.addWidget(inputFileFrame)

        # Output File
        outputFileLayout = QVBoxLayout()
        outputFileLayout.setSpacing(5)
        outputFileLabel = QLabel("Select Output File")
        self.saveStatisticsButton = QPushButton("Save Statistics To")
        self.outputStatusLabel = QLabel("File: Not selected")
        outputFileLayout.addWidget(outputFileLabel)
        outputFileLayout.addWidget(self.saveStatisticsButton)
        outputFileLayout.addWidget(self.outputStatusLabel)
        outputFileFrame = QFrame()
        outputFileFrame.setLayout(outputFileLayout)
        leftPanelLayout.addWidget(outputFileFrame)

        # Analysis Period
        analysisPeriodLayout = QVBoxLayout()
        analysisPeriodLayout.setSpacing(5)
        analysisPeriodLabel = QLabel("Analysis Period")
        startDateLabel = QLabel("Analysis start date:")
        self.startDateInput = QLineEdit("01/01/1948")
        endDateLabel = QLabel("Analysis end date:")
        self.endDateInput = QLineEdit("31/12/2017")
        analysisPeriodLayout.addWidget(analysisPeriodLabel)
        analysisPeriodLayout.addWidget(startDateLabel)
        analysisPeriodLayout.addWidget(self.startDateInput)
        analysisPeriodLayout.addWidget(endDateLabel)
        analysisPeriodLayout.addWidget(self.endDateInput)
        analysisPeriodFrame = QFrame()
        analysisPeriodFrame.setLayout(analysisPeriodLayout)
        leftPanelLayout.addWidget(analysisPeriodFrame)

        contentAreaLayout.addLayout(leftPanelLayout)

        # --- Right Panel ---
        rightPanelLayout = QVBoxLayout()
        rightPanelLayout.setSpacing(20)

        # Modelled Scenario
        modelledScenarioLayout = QVBoxLayout()
        modelledScenarioLayout.setSpacing(5)
        modelledScenarioLabel = QLabel("Modelled Scenario")
        modelledScenarioLabel.setFont(QFont("Arial", 12, QFont.Bold))
        modelDetailsLabel = QLabel("Model Details")
        self.modelDetails = [
            QLabel("Predictors: unknown"),
            QLabel("Season code: unknown"),
            QLabel("Year length: unknown"),
            QLabel("Scenario start: unknown"),
            QLabel("No. of days: unknown"),
            QLabel("Ensemble size: unknown")
        ]
        self.viewDetailsButton = QPushButton("View Details")
        modelledScenarioLayout.addWidget(modelledScenarioLabel)
        modelledScenarioLayout.addWidget(modelDetailsLabel)
        for widget in self.modelDetails:
            modelledScenarioLayout.addWidget(widget)
        modelledScenarioLayout.addWidget(self.viewDetailsButton)
        modelledScenarioFrame = QFrame()
        modelledScenarioFrame.setLayout(modelledScenarioLayout)
        rightPanelLayout.addWidget(modelledScenarioFrame)

        # Ensemble Size
        ensembleSizeLayout = QVBoxLayout()
        ensembleSizeLayout.setSpacing(5)
        ensembleSizeLabel = QLabel("Ensemble Size")
        self.ensembleMeanCheckbox = QCheckBox("Use Ensemble Mean?")
        self.ensembleMeanCheckbox.setChecked(True)
        ensembleMemberLabel = QLabel("Ensemble Member:")
        self.ensembleMemberInput = QLineEdit("0")
        ensembleSizeLayout.addWidget(ensembleSizeLabel)
        ensembleSizeLayout.addWidget(self.ensembleMeanCheckbox)
        ensembleSizeLayout.addWidget(ensembleMemberLabel)
        ensembleSizeLayout.addWidget(self.ensembleMemberInput)
        ensembleSizeFrame = QFrame()
        ensembleSizeFrame.setLayout(ensembleSizeLayout)
        rightPanelLayout.addWidget(ensembleSizeFrame)

        contentAreaLayout.addLayout(rightPanelLayout)
        mainLayout.addLayout(contentAreaLayout)

        # Results Display Area
        self.resultsDisplay = QTextEdit()
        self.resultsDisplay.setReadOnly(True)
        mainLayout.addWidget(self.resultsDisplay)

        # Auto-resizing setup
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # --- Connect Signals ---
        self.inputFileButton.clicked.connect(self.select_input_file)
        self.saveStatisticsButton.clicked.connect(self.select_output_file)
        self.resetButton.clicked.connect(self.reset_fields)
        self.analyseButton.clicked.connect(self.analyse_data)
        self.deltaStatsButton.clicked.connect(self.compute_delta_stats)
        self.viewDetailsButton.clicked.connect(self.view_details)
        self.statsButton.clicked.connect(self.show_statistics)
        self.settingsButton.clicked.connect(self.open_settings)

    # ---------------- UI Event Handlers ----------------

    def reset_fields(self):
        """Reset all fields to default values."""
        self.modelledButton.setChecked(True)
        self.observedButton.setChecked(False)
        self.inputFilePath = ""
        self.fileStatusLabel.setText("File: Not selected")
        self.outputFilePath = ""
        self.outputStatusLabel.setText("File: Not selected")
        self.startDateInput.setText("01/01/1948")
        self.endDateInput.setText("31/12/2017")
        self.ensembleMeanCheckbox.setChecked(True)
        self.ensembleMemberInput.setText("0")
        self.resultsDisplay.clear()
        for detail in self.modelDetails:
            detail.setText("unknown")
        self.meta = {}
        print("Fields reset.")

    def select_input_file(self):
        """Open a file dialog to select the input scenario (*.OUT) file."""
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Select Input Scenario File", "", "OUT Files (*.OUT);;All Files (*)", options=options)
        if fileName:
            self.inputFilePath = fileName
            self.fileStatusLabel.setText(f"File: {fileName}")
            # Derive the SIM file name (assumes .OUT to .SIM conversion)
            if fileName.lower().endswith(".out"):
                self.simFilePath = fileName[:-4] + ".SIM"
            else:
                self.simFilePath = ""
            print("Selected input file:", self.inputFilePath)

    def select_output_file(self):
        """Open a file dialog to select the output file for saving statistics."""
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getSaveFileName(self, "Select Output File", "", "TXT Files (*.txt);;All Files (*)", options=options)
        if fileName:
            self.outputFilePath = fileName
            self.outputStatusLabel.setText(f"File: {fileName}")
            print("Selected output file:", self.outputFilePath)

    def view_details(self):
        """Read the SIM file (if available) and display model details."""
        if self.simFilePath:
            self.meta = read_sim_file(self.simFilePath)
            details = [
                f"Predictors: {self.meta.get('NPredictors', 'unknown')}",
                f"Season code: {self.meta.get('SeasonCode', 'unknown')}",
                f"Year length: {self.meta.get('LocalYearIndicator', 'unknown')}",
                f"Scenario start: {self.meta.get('DataSDate', 'unknown'):%d/%m/%Y}" if 'DataSDate' in self.meta else "Scenario start: unknown",
                f"No. of days: {self.meta.get('NDaysR', 'unknown')}",
                f"Ensemble size: {self.meta.get('EnsembleSize', 'unknown')}"
            ]
            for widget, detail in zip(self.modelDetails, details):
                widget.setText(detail)
            print("Displayed model details.")
        else:
            print("SIM file not selected.")

    def show_statistics(self):
        """Stub for statistics selection functionality."""
        self.resultsDisplay.append("Statistics selection not fully implemented yet.")
        print("Statistics button clicked.")

    def open_settings(self):
        """Stub for opening settings dialog."""
        self.resultsDisplay.append("Settings dialog not implemented.")
        print("Settings button clicked.")

    def analyse_data(self):
        """
        Implements the 'Analyse' functionality:
          1. Reads the scenario file (skipping to analysis start date),
          2. Bins data by period (months, seasons, annual),
          3. Computes basic and advanced statistics.
        """
        start_date = self.startDateInput.text()
        if not self.inputFilePath:
            self.resultsDisplay.append("No input file selected.")
            return
        data = read_scenario_file(self.inputFilePath, start_date)
        if not data:
            self.resultsDisplay.append("No data read from scenario file.")
            return
        bins = bin_data_by_period(data)
        rain_mode = self.modelledButton.isChecked()
        # Basic analysis:
        basic_results = analyze_periods(bins, thresh=5.0, rain_mode=rain_mode)
        # Advanced analysis:
        self.analysisResults = compute_advanced_stats(bins, self.meta, thresh=5.0)
        # Display the advanced results:
        self.display_results(self.analysisResults, title="Advanced Analysis Results")
        if self.outputFilePath:
            self.save_results_to_file(self.analysisResults, self.outputFilePath)
        print("Analysis complete.")

    def compute_delta_stats(self):
        """
        Implements the 'Delta Stats' functionality.
        For demonstration, we compare the advanced stats for two different periods (e.g., period 1 vs. period 17).
        (In the legacy code, there are distinct base and future periods; here we simulate by using two bins.)
        """
        if self.analysisResults is None:
            self.resultsDisplay.append("Please run Analyse first.")
            return
        # For example, compare Month 1 (January) as base with Annual (period 17) as future:
        base = self.analysisResults.get(1, {})
        future = self.analysisResults.get(17, {})
        # For simplicity, if multiple ensembles exist, compare ensemble 1
        if 1 not in base or 1 not in future:
            self.resultsDisplay.append("Not enough ensemble data for delta calculation.")
            return
        delta = compute_delta_between_periods(base[1], future[1], delta_mode='percentage')
        self.resultsDisplay.append("----- Delta Statistics (Annual vs January) -----")
        for stat, d_val in delta.items():
            if np.isnan(d_val):
                self.resultsDisplay.append(f"{stat}: N/A")
            else:
                self.resultsDisplay.append(f"{stat}: {d_val:.3f}")
        self.resultsDisplay.append("----------------------------------------------")
        print("Delta statistics computed.")

    def display_results(self, results, title="Results"):
        """
        Displays the results (a nested dictionary of period and ensemble stats)
        in the resultsDisplay text area.
        """
        self.resultsDisplay.append(f"----- {title} -----")
        for period in sorted(results.keys()):
            self.resultsDisplay.append(f"Period {period}:")
            for ens, stats in results[period].items():
                line = f"  Ensemble {ens}: " + ", ".join(
                    f"{k}={v:.3f}" if isinstance(v, (int, float)) and not np.isnan(v) else f"{k}=N/A"
                    for k, v in stats.items()
                )
                self.resultsDisplay.append(line)
        self.resultsDisplay.append("---------------------")

    def save_results_to_file(self, results, file_path):
        """Saves the results to the specified output file."""
        try:
            with open(file_path, 'w') as f:
                f.write("Summary Statistics Results\n")
                for period in sorted(results.keys()):
                    f.write(f"Period {period}:\n")
                    for ens, stats in results[period].items():
                        line = f"  Ensemble {ens}: " + ", ".join(
                            f"{k}={v:.3f}" if isinstance(v, (int, float)) and not np.isnan(v) else f"{k}=N/A"
                            for k, v in stats.items()
                        )
                        f.write(line + "\n")
            print("Results saved to file.")
        except Exception as e:
            print("Error saving results:", e)

# ---------------- Main Application ----------------

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ContentWidget()
    window.setWindowTitle("Summary Statistics")
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec_())
