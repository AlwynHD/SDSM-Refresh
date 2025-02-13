import sys
import math
import random
import datetime
import matplotlib.pyplot as plt 
import numpy as np
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QGridLayout, QCheckBox, QRadioButton,
                             QButtonGroup, QFileDialog, QGroupBox, QMessageBox)
from PyQt5.QtCore import Qt


class SDSMContext:
    """
    A context for storing parameters and data for scenario generation.
    This will be changed in future to match the other module's data structures.
    """
    def __init__(self):
        # File paths
        self.in_file = ""
        self.in_root = ""
        self.out_file = ""
        self.out_root = ""
        # Date and threshold
        self.start_date = datetime.date(2000, 1, 1)
        self.local_thresh = 0.1
        # Ensemble and data array
        self.ensemble_size = 1
        self.data_array = []   # a list (one per ensemble) of lists (one per day)
        self.no_of_days = 0
        self.mean_array = []   # list of (mean, sd) tuples for each ensemble
        # Occurrence treatment
        self.occurrence_check = False
        self.conditional_check = False
        self.occurrence_factor = 0           # raw percentage value, e.g. 5 means +5%
        self.occurrence_factor_percent = 1.0   # (occurrence_factor + 100)/100
        self.occurrence_option = 0           # 0 = stochastic; 1 = forced
        self.preserve_totals_check = False
        # Amount (or “mean”) treatment – modifies rainfall amounts
        self.amount_check = False
        self.amount_option = 0    # 0 = factor; 1 = addition
        self.amount_factor = 0    # e.g. 5 means +5%
        self.amount_factor_percent = 1.0  # (100 + amount_factor)/100
        self.amount_addition = 0.0
        # Variance treatment
        self.variance_check = False
        self.variance_factor = 0
        self.variance_factor_percent = 1.0  # (100+variance_factor)/100
        # Trend treatment
        self.trend_check = False
        self.linear_trend = 0.0
        self.exp_trend = 0.0
        self.logistic_trend = 0.0
        # Which trend(s) to apply – list of booleans [linear, exponential, logistic]
        self.trend_option = [False, False, False]
        # For Box–Cox transform
        self.lamda = 0.0
        # Global missing code
        self.global_missing_code = -999


def increase_date(date_obj):
    """Increase the date by one day."""
    return date_obj + datetime.timedelta(days=1)


def parse_value(str_val, ctx):
    """
    Parses a string value from the file.
    If the value is "-999", returns the global missing code.
    Otherwise, returns the float value.
    """
    val_str = str_val.strip()
    if val_str == "-999":
        return ctx.global_missing_code
    try:
        return float(val_str)
    except ValueError:
        return ctx.global_missing_code


def check_settings(ctx: SDSMContext) -> bool:
    """Perform basic sanity checks on the context settings."""
    if not ctx.in_file or len(ctx.in_file) < 5:
        QMessageBox.critical(None, "Error", "You must select an input file first.")
        return False
    if not ctx.out_file:
        QMessageBox.critical(None, "Error", "You must select an output file.")
        return False
    if not (ctx.occurrence_check or ctx.amount_check or ctx.trend_check or ctx.variance_check):
        QMessageBox.critical(None, "Error", "You must select at least one treatment.")
        return False
    if ctx.occurrence_check and not ctx.conditional_check:
        QMessageBox.critical(None, "Error", "Occurrence treatment cannot be applied to unconditional data.")
        return False
    return True


def modify_data(ctx: SDSMContext):
    """Main routine: read the input file, apply selected treatments, and write the output file."""
    if not check_settings(ctx):
        return

    # --- Read Data File ---
    try:
        with open(ctx.in_root, "r") as f:
            lines = f.readlines()
    except Exception as e:
        QMessageBox.critical(None, "Error", f"Error reading input file:\n{e}")
        return

    if not lines:
        QMessageBox.critical(None, "Error", "Input file is empty.")
        return

    # Determine if multi-column (by checking length of first line)
    multi_column = len(lines[0]) > 14

    # Prepare data_array: a list of lists, one for each ensemble member.
    ctx.data_array = [[] for _ in range(ctx.ensemble_size)]

    def process_line(line: str):
        if ctx.ensemble_size == 1 and not multi_column:
            num = parse_value(line, ctx)
            ctx.data_array[0].append(num)
        else:
            # Assume fixed-width fields of width 14 per ensemble member.
            for i in range(ctx.ensemble_size):
                start = i * 14
                end = start + 14
                num_str = line[start:end]
                num = parse_value(num_str, ctx)
                ctx.data_array[i].append(num)

    for line in lines:
        process_line(line)
    ctx.no_of_days = len(ctx.data_array[0])
    print(f"Read {ctx.no_of_days} days for {ctx.ensemble_size} ensemble member(s).")

    # --- Apply Treatments in Order ---
    if ctx.occurrence_check:
        apply_occurrence(ctx)
    if ctx.variance_check:
        calc_means(ctx)
    if ctx.amount_check:
        apply_amount(ctx)
    if ctx.variance_check:
        apply_variance(ctx)
    if ctx.trend_check:
        apply_trend(ctx)

    # --- Write Output File (without showing -999 values) ---
    try:
        with open(ctx.out_root, "w") as f:
            for i in range(ctx.no_of_days):
                line_out = ""
                for j in range(ctx.ensemble_size):
                    val = ctx.data_array[j][i]
                    if val == ctx.global_missing_code:
                        line_out += "\t"  # output blank instead of -999
                    else:
                        line_out += f"{val:8.3f}\t"
                f.write(line_out + "\n")
    except Exception as e:
        QMessageBox.critical(None, "Error", f"Error writing output file:\n{e}")
        return

    QMessageBox.information(None, "Success",
                            f"Scenario generated.\n{ctx.no_of_days} days processed.")

    # Plot the final data
    plot_scenario(ctx)


def apply_amount(ctx: SDSMContext):
    """Apply an amount (multiplicative or additive) treatment to data."""
    for j in range(ctx.ensemble_size):
        for i in range(ctx.no_of_days):
            val = ctx.data_array[j][i]
            if val != ctx.global_missing_code:
                if (not ctx.conditional_check) or (ctx.conditional_check and val > ctx.local_thresh):
                    if ctx.amount_option == 0:
                        ctx.data_array[j][i] = val * ctx.amount_factor_percent
                    else:
                        ctx.data_array[j][i] = val + ctx.amount_addition


def apply_occurrence(ctx: SDSMContext):
    """Apply occurrence treatment (adding or removing wet days)."""
    random.seed()
    for j in range(ctx.ensemble_size):
        # Prepare per-month lists (months 1 to 12)
        DryCount = [0] * 12
        WetCount = [0] * 12
        DayCount = [0] * 12
        OrigWetCount = [0] * 12
        WetArray = [[] for _ in range(12)]
        DryArray = [[] for _ in range(12)]
        TotalRainfall = 0.0
        TotalWetCount = 0

        current_date = ctx.start_date
        for i in range(ctx.no_of_days):
            val = ctx.data_array[j][i]
            m = current_date.month - 1
            if val != ctx.global_missing_code:
                DayCount[m] += 1
                if val > ctx.local_thresh:
                    WetCount[m] += 1
                    WetArray[m].append(i)
                    TotalRainfall += val
                    TotalWetCount += 1
                else:
                    DryCount[m] += 1
                    DryArray[m].append(i)
            current_date = increase_date(current_date)
        for m in range(12):
            OrigWetCount[m] = WetCount[m]

        if TotalWetCount <= 0:
            QMessageBox.information(None, "Warning",
                                    f"Ensemble {j+1} has zero wet days; occurrence treatment skipped.")
            continue

        if ctx.occurrence_option == 0:  # stochastic option
            if ctx.occurrence_factor_percent < 1:
                DaysToDelete = int(TotalWetCount - (TotalWetCount * ctx.occurrence_factor_percent))
                for _ in range(DaysToDelete):
                    m = random.choice([ix for ix in range(12) if WetCount[ix] > 0])
                    idx = random.randint(0, WetCount[m] - 1)
                    day = WetArray[m][idx]
                    ctx.data_array[j][day] = ctx.local_thresh  # mark as dry
                    WetArray[m].pop(idx)
                    WetCount[m] -= 1
            elif ctx.occurrence_factor_percent > 1:
                DaysToAdd = int((TotalWetCount * ctx.occurrence_factor_percent) - TotalWetCount)
                available = ctx.no_of_days - TotalWetCount
                if DaysToAdd > available:
                    QMessageBox.critical(None, "Error", "Too many wet days to add (dataset overflow).")
                    return
                for _ in range(DaysToAdd):
                    m = random.choice([ix for ix in range(12) if DryCount[ix] > 0])
                    idx = random.randint(0, DryCount[m] - 1)
                    day = DryArray[m][idx]
                    if OrigWetCount[m] == 0:
                        possible_wet_months = [ix for ix in range(12) if WetCount[ix] > 0]
                        if not possible_wet_months:
                            continue
                        m2 = random.choice(possible_wet_months)
                        wet_day = random.choice(WetArray[m2])
                        ctx.data_array[j][day] = ctx.data_array[j][wet_day]
                    else:
                        wet_day = random.choice(WetArray[m])
                        ctx.data_array[j][day] = ctx.data_array[j][wet_day]
                    DryArray[m].pop(idx)
                    DryCount[m] -= 1
        else:
            QMessageBox.information(None, "Info", "Forced occurrence treatment not implemented in this demo.")


def calc_means(ctx: SDSMContext):
    """Calculate mean and standard deviation for each ensemble member."""
    ctx.mean_array = []
    for j in range(ctx.ensemble_size):
        total = 0.0
        count = 0
        for i in range(ctx.no_of_days):
            val = ctx.data_array[j][i]
            if val != ctx.global_missing_code:
                if (not ctx.conditional_check) or (ctx.conditional_check and val > ctx.local_thresh):
                    total += val
                    count += 1
        mean = total / count if count > 0 else ctx.global_missing_code
        if mean != ctx.global_missing_code:
            ssum = 0.0
            for i in range(ctx.no_of_days):
                val = ctx.data_array[j][i]
                if val != ctx.global_missing_code:
                    if (not ctx.conditional_check) or (ctx.conditional_check and val > ctx.local_thresh):
                        ssum += (val - mean) ** 2
            sd = math.sqrt(ssum / count) if count > 0 else ctx.global_missing_code
        else:
            sd = ctx.global_missing_code
        ctx.mean_array.append((mean, sd))


def unbox_cox(value: float, lamda: float, ctx: SDSMContext) -> float:
    """Un–apply a Box–Cox transformation to a value."""
    if value == ctx.global_missing_code:
        return ctx.global_missing_code
    if lamda == 0:
        return math.exp(value)
    else:
        return ((value * lamda) + 1) ** (1 / lamda)


def calc_variance(trans_array, factor, mean, no_of_days, ctx: SDSMContext) -> float:
    """Calculate the variance after applying a factor to transformed data."""
    temp = []
    for i in range(no_of_days):
        if trans_array[i] != ctx.global_missing_code:
            t = ((trans_array[i] - mean) * factor) + mean
            t = unbox_cox(t, ctx.lamda, ctx)
            temp.append(t)
    if not temp:
        return ctx.global_missing_code
    new_mean = sum(temp) / len(temp)
    var = sum((x - new_mean) ** 2 for x in temp) / len(temp)
    return var


def find_min_lambda(ctx: SDSMContext, ensemble: int, start: float, finish: float, step: float) -> float:
    """Find an optimal lamda for the Box–Cox transformation (a simplified version)."""
    best_lam = start
    min_d = float('inf')
    for k in frange(start, finish, step):
        temp = []
        for i in range(ctx.no_of_days):
            val = ctx.data_array[ensemble][i]
            if val != ctx.global_missing_code and val > ctx.local_thresh and val != 0:
                if k == 0:
                    temp.append(math.log(val))
                else:
                    temp.append((val ** k - 1) / k)
        if len(temp) > 10:
            mean_val = sum(temp) / len(temp)
            temp.sort()
            median = temp[len(temp) // 2]
            lower_index = len(temp) // 4
            upper_index = len(temp) - lower_index
            IQR = temp[upper_index - 1] - temp[lower_index]
            if IQR > 0:
                d = abs((mean_val - median) / IQR)
                if d < min_d:
                    min_d = d
                    best_lam = k
    return best_lam


def frange(start, stop, step):
    """Floating–point range generator."""
    while start <= stop:
        yield start
        start += step


def apply_variance(ctx: SDSMContext):
    """Apply variance treatment (using a Box–Cox transform for conditional processing)."""
    for j in range(ctx.ensemble_size):
        if not ctx.conditional_check:
            for i in range(ctx.no_of_days):
                if ctx.data_array[j][i] != ctx.global_missing_code:
                    ctx.data_array[j][i] = (
                        (ctx.data_array[j][i] - ctx.mean_array[j][0]) *
                        math.sqrt(ctx.variance_factor_percent) +
                        ctx.mean_array[j][0]
                    )
        else:
            lamda = find_min_lambda(ctx, j, -2, 2, 0.25)
            lamda = find_min_lambda(ctx, j, lamda - 0.25, lamda + 0.25, 0.1)
            lamda = find_min_lambda(ctx, j, lamda - 0.1, lamda + 0.1, 0.01)
            ctx.lamda = lamda
            trans_array = [ctx.global_missing_code] * ctx.no_of_days
            mean_trans = 0.0
            count = 0
            for i in range(ctx.no_of_days):
                val = ctx.data_array[j][i]
                if val != ctx.global_missing_code and val > ctx.local_thresh:
                    if lamda == 0:
                        trans_array[i] = math.log(val)
                    else:
                        trans_array[i] = ((val ** lamda) - 1) / lamda
                    mean_trans += trans_array[i]
                    count += 1
            mean_trans = mean_trans / count if count > 0 else ctx.global_missing_code
            if ctx.variance_factor_percent > 1:
                lower, higher = 1.0, 1.3
            else:
                lower, higher = 0.5, 1.0
            middle = (lower + higher) / 2
            for _ in range(10):
                var_mid = calc_variance(trans_array, middle, mean_trans, ctx.no_of_days, ctx)
                orig_var = ctx.mean_array[j][1] ** 2
                if orig_var == 0:
                    break
                if var_mid / orig_var < ctx.variance_factor_percent:
                    lower = middle
                else:
                    higher = middle
                middle = (lower + higher) / 2
            for i in range(ctx.no_of_days):
                if trans_array[i] != ctx.global_missing_code:
                    trans_array[i] = ((trans_array[i] - mean_trans) * middle) + mean_trans
                    ctx.data_array[j][i] = unbox_cox(trans_array[i], lamda, ctx)


def apply_trend(ctx: SDSMContext):
    """Apply trend treatment(s) to the data."""
    for j in range(ctx.ensemble_size):
        if ctx.trend_option[0]:
            year_days = 365
            increment = ctx.linear_trend / year_days
            for i in range(ctx.no_of_days):
                if ctx.data_array[j][i] != ctx.global_missing_code:
                    if not ctx.conditional_check:
                        ctx.data_array[j][i] += increment * i
                    else:
                        if ctx.data_array[j][i] > ctx.local_thresh:
                            ctx.data_array[j][i] *= (1 + (ctx.linear_trend / (year_days * 100)) * i)
        if ctx.trend_option[1]:
            exp_abs = abs(ctx.exp_trend)
            A = ctx.no_of_days / math.log(exp_abs + 1) if exp_abs != 0 else 1
            add_option = ctx.exp_trend > 0
            for i in range(ctx.no_of_days):
                if ctx.data_array[j][i] != ctx.global_missing_code:
                    delta = math.exp(i / A) - 1
                    if not ctx.conditional_check:
                        ctx.data_array[j][i] += delta if add_option else -delta
                    else:
                        if ctx.data_array[j][i] > ctx.local_thresh:
                            factor = (100 + delta) / 100 if add_option else (100 - delta) / 100
                            ctx.data_array[j][i] *= factor
        if ctx.trend_option[2]:
            for i in range(ctx.no_of_days):
                if ctx.no_of_days > 1:
                    x = ((i) / (ctx.no_of_days - 1)) * 12 - 6
                else:
                    x = 0
                logistic = 1 / (1 + math.exp(-x))
                delta = ctx.logistic_trend * logistic
                if ctx.data_array[j][i] != ctx.global_missing_code:
                    if not ctx.conditional_check:
                        ctx.data_array[j][i] += delta
                    else:
                        if ctx.data_array[j][i] > ctx.local_thresh:
                            ctx.data_array[j][i] *= ((100 + delta) / 100)


# =============================================================================
#   Plotting the final data
# =============================================================================

def plot_scenario(ctx: SDSMContext):
    """
    Creates a simple time series plot of the final data in ctx.data_array.
    Missing values (== -999) are converted to NaN so they are not plotted.
    One line per ensemble member.
    """
    if ctx.no_of_days == 0:
        return
    plt.figure(figsize=(10, 5))
    x_values = np.arange(1, ctx.no_of_days + 1)
    for j in range(ctx.ensemble_size):
        y_values = np.array(ctx.data_array[j], dtype=float)
        # Replace missing values (-999) with NaN so matplotlib leaves a gap.
        y_values[y_values == ctx.global_missing_code] = np.nan
        plt.plot(x_values, y_values, label=f"Ensemble {j+1}")
    plt.title("Scenario Output (Final Daily Values)")
    plt.xlabel("Day Index")
    plt.ylabel("Value (e.g., mm)")
    plt.legend()
    plt.tight_layout()
    plt.show()


# =============================================================================
#   PyQt5 User Interface
# =============================================================================

class ContentWidget(QWidget):
    """
    A modernized UI for the SDSM Scenario Generator.
    """
    def __init__(self):
        super().__init__()
        self.ctx = SDSMContext()  # Our processing context
        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(30, 30, 30, 30)
        mainLayout.setSpacing(20)
        self.setLayout(mainLayout)

        # --- File Selection Section ---
        fileSelectionGroup = QGroupBox("File Selection")
        fileSelectionLayout = QHBoxLayout()
        self.inputFileButton = QPushButton("📂 Select Input File")
        self.inputFileButton.clicked.connect(self.selectInputFile)
        self.inputFileLabel = QLabel("No file selected")
        self.outputFileButton = QPushButton("💾 Save To File")
        self.outputFileButton.clicked.connect(self.selectOutputFile)
        self.outputFileLabel = QLabel("No file selected")
        fileSelectionLayout.addWidget(self.inputFileButton)
        fileSelectionLayout.addWidget(self.inputFileLabel)
        fileSelectionLayout.addStretch()
        fileSelectionLayout.addWidget(self.outputFileButton)
        fileSelectionLayout.addWidget(self.outputFileLabel)
        fileSelectionGroup.setLayout(fileSelectionLayout)
        mainLayout.addWidget(fileSelectionGroup)

        # --- General Parameters ---
        generalParamsGroup = QGroupBox("General Parameters")
        generalParamsLayout = QGridLayout()
        self.startDateInput = QLineEdit()
        self.startDateInput.setPlaceholderText("DD/MM/YYYY")
        self.ensembleSizeInput = QLineEdit()
        self.ensembleSizeInput.setPlaceholderText("Enter a number")
        self.conditionalProcessCheck = QCheckBox("Enable Conditional Processing?")
        self.eventThresholdInput = QLineEdit()
        self.eventThresholdInput.setPlaceholderText("Threshold Value")
        generalParamsLayout.addWidget(QLabel("📅 File Start Date:"), 0, 0)
        generalParamsLayout.addWidget(self.startDateInput, 0, 1)
        generalParamsLayout.addWidget(QLabel("📊 Ensemble Size:"), 0, 2)
        generalParamsLayout.addWidget(self.ensembleSizeInput, 0, 3)
        generalParamsLayout.addWidget(self.conditionalProcessCheck, 1, 0, 1, 2)
        generalParamsLayout.addWidget(QLabel("🔢 Event Threshold:"), 1, 2)
        generalParamsLayout.addWidget(self.eventThresholdInput, 1, 3)
        generalParamsGroup.setLayout(generalParamsLayout)
        mainLayout.addWidget(generalParamsGroup)

        # --- Treatments Section ---
        treatmentsGroup = QGroupBox("Treatment Parameters")
        treatmentsLayout = QGridLayout()
        # Occurrence
        self.occurrenceCheck = QCheckBox("⚡ Occurrence")
        self.frequencyChangeInput = QLineEdit()
        self.frequencyChangeInput.setPlaceholderText("e.g. 5 for +5% or -5 for -5%")
        self.stochasticRadio = QRadioButton("Stochastic")
        self.forcedRadio = QRadioButton("Forced")
        self.preserveTotalCheck = QCheckBox("Preserve Total?")
        occurrenceButtonGroup = QButtonGroup()
        occurrenceButtonGroup.addButton(self.stochasticRadio)
        occurrenceButtonGroup.addButton(self.forcedRadio)
        treatmentsLayout.addWidget(self.occurrenceCheck, 0, 0)
        treatmentsLayout.addWidget(QLabel("Frequency change:"), 0, 1)
        treatmentsLayout.addWidget(self.frequencyChangeInput, 0, 2)
        treatmentsLayout.addWidget(self.stochasticRadio, 0, 3)
        treatmentsLayout.addWidget(self.forcedRadio, 0, 4)
        treatmentsLayout.addWidget(self.preserveTotalCheck, 0, 5)
        # Variance
        self.varianceCheck = QCheckBox("📈 Variance")
        self.varianceFactorInput = QLineEdit()
        self.varianceFactorInput.setPlaceholderText("e.g. 10 for +10%")
        treatmentsLayout.addWidget(self.varianceCheck, 1, 0)
        treatmentsLayout.addWidget(QLabel("Factor:"), 1, 1)
        treatmentsLayout.addWidget(self.varianceFactorInput, 1, 2)
        # Amount (Mean) Treatment
        self.meanCheck = QCheckBox("📊 Mean (Amount)")
        self.meanFactorInput = QLineEdit()
        self.meanFactorInput.setPlaceholderText("e.g. 5 for +5%")
        self.meanAdditionInput = QLineEdit()
        self.meanAdditionInput.setPlaceholderText("Addition value")
        treatmentsLayout.addWidget(self.meanCheck, 2, 0)
        treatmentsLayout.addWidget(QLabel("Factor:"), 2, 1)
        treatmentsLayout.addWidget(self.meanFactorInput, 2, 2)
        treatmentsLayout.addWidget(QLabel("Addition:"), 2, 3)
        treatmentsLayout.addWidget(self.meanAdditionInput, 2, 4)
        # Trend
        self.trendCheck = QCheckBox("📉 Trend")
        self.linearInput = QLineEdit()
        self.linearInput.setPlaceholderText("Linear trend (/year)")
        self.exponentialInput = QLineEdit()
        self.exponentialInput.setPlaceholderText("Exponential factor")
        self.logisticInput = QLineEdit()
        self.logisticInput.setPlaceholderText("Logistic factor")
        treatmentsLayout.addWidget(self.trendCheck, 3, 0)
        treatmentsLayout.addWidget(QLabel("Linear:"), 3, 1)
        treatmentsLayout.addWidget(self.linearInput, 3, 2)
        treatmentsLayout.addWidget(QLabel("Exponential:"), 3, 3)
        treatmentsLayout.addWidget(self.exponentialInput, 3, 4)
        treatmentsLayout.addWidget(QLabel("Logistic:"), 3, 5)
        treatmentsLayout.addWidget(self.logisticInput, 3, 6)
        treatmentsGroup.setLayout(treatmentsLayout)
        mainLayout.addWidget(treatmentsGroup)

        # --- Buttons ---
        buttonLayout = QHBoxLayout()
        self.generateButton = QPushButton("🚀 Generate")
        self.generateButton.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.generateButton.clicked.connect(self.generateScenario)
        self.resetButton = QPushButton("🔄 Reset")
        self.resetButton.setStyleSheet("background-color: #F44336; color: white; font-weight: bold;")
        self.resetButton.clicked.connect(self.resetFields)
        buttonLayout.addWidget(self.generateButton)
        buttonLayout.addWidget(self.resetButton)
        mainLayout.addLayout(buttonLayout)

    def selectInputFile(self):
        """Opens a file dialog to select an input file."""
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Input File")
        if file_name:
            self.inputFileLabel.setText(file_name)
            self.ctx.in_file = file_name.split("/")[-1]
            self.ctx.in_root = file_name

    def selectOutputFile(self):
        """Opens a file dialog to select an output file."""
        file_name, _ = QFileDialog.getSaveFileName(self, "Save To File")
        if file_name:
            self.outputFileLabel.setText(file_name)
            self.ctx.out_file = file_name.split("/")[-1]
            self.ctx.out_root = file_name

    def generateScenario(self):
        """Collect parameters from the UI, update the context, and run the scenario generation."""
        try:
            dt = datetime.datetime.strptime(self.startDateInput.text(), "%d/%m/%Y")
            self.ctx.start_date = dt.date()
        except Exception:
            QMessageBox.critical(self, "Error", "Start Date must be in DD/MM/YYYY format.")
            return
        try:
            ens = int(self.ensembleSizeInput.text())
            self.ctx.ensemble_size = ens
        except Exception:
            QMessageBox.critical(self, "Error", "Ensemble Size must be an integer.")
            return
        try:
            thresh = float(self.eventThresholdInput.text())
            self.ctx.local_thresh = thresh
        except Exception:
            self.ctx.local_thresh = 0.1

        self.ctx.conditional_check = self.conditionalProcessCheck.isChecked()

        # Occurrence treatment
        self.ctx.occurrence_check = self.occurrenceCheck.isChecked()
        try:
            freq = float(self.frequencyChangeInput.text())
            self.ctx.occurrence_factor = freq
            self.ctx.occurrence_factor_percent = (100 + freq) / 100
        except Exception:
            self.ctx.occurrence_factor = 0
            self.ctx.occurrence_factor_percent = 1.0
        if self.stochasticRadio.isChecked():
            self.ctx.occurrence_option = 0
        elif self.forcedRadio.isChecked():
            self.ctx.occurrence_option = 1
        self.ctx.preserve_totals_check = self.preserveTotalCheck.isChecked()

        # Amount (Mean) treatment
        self.ctx.amount_check = self.meanCheck.isChecked()
        try:
            factor = float(self.meanFactorInput.text())
            self.ctx.amount_factor = factor
            self.ctx.amount_factor_percent = (100 + factor) / 100
        except Exception:
            self.ctx.amount_factor = 0
            self.ctx.amount_factor_percent = 1.0
        try:
            addition = float(self.meanAdditionInput.text())
            self.ctx.amount_addition = addition
        except Exception:
            self.ctx.amount_addition = 0.0
        if self.ctx.amount_factor != 0:
            self.ctx.amount_option = 0
        elif self.ctx.amount_addition != 0:
            self.ctx.amount_option = 1

        # Variance treatment
        self.ctx.variance_check = self.varianceCheck.isChecked()
        try:
            vfac = float(self.varianceFactorInput.text())
            self.ctx.variance_factor = vfac
            self.ctx.variance_factor_percent = (100 + vfac) / 100
        except Exception:
            self.ctx.variance_factor = 0
            self.ctx.variance_factor_percent = 1.0

        # Trend treatment
        self.ctx.trend_check = self.trendCheck.isChecked()
        try:
            linear = float(self.linearInput.text())
            self.ctx.linear_trend = linear
            self.ctx.trend_option[0] = (linear != 0)
        except Exception:
            self.ctx.linear_trend = 0.0
            self.ctx.trend_option[0] = False
        try:
            exp = float(self.exponentialInput.text())
            self.ctx.exp_trend = exp
            self.ctx.trend_option[1] = (exp != 0)
        except Exception:
            self.ctx.exp_trend = 0.0
            self.ctx.trend_option[1] = False
        try:
            logistic = float(self.logisticInput.text())
            self.ctx.logistic_trend = logistic
            self.ctx.trend_option[2] = (logistic != 0)
        except Exception:
            self.ctx.logistic_trend = 0.0
            self.ctx.trend_option[2] = False

        modify_data(self.ctx)

    def resetFields(self):
        """Reset all input fields to defaults."""
        self.startDateInput.clear()
        self.ensembleSizeInput.clear()
        self.eventThresholdInput.clear()
        self.conditionalProcessCheck.setChecked(False)
        self.inputFileLabel.setText("No file selected")
        self.outputFileLabel.setText("No file selected")
        self.occurrenceCheck.setChecked(False)
        self.frequencyChangeInput.clear()
        self.stochasticRadio.setChecked(False)
        self.forcedRadio.setChecked(False)
        self.preserveTotalCheck.setChecked(False)
        self.varianceCheck.setChecked(False)
        self.varianceFactorInput.clear()
        self.meanCheck.setChecked(False)
        self.meanFactorInput.clear()
        self.meanAdditionInput.clear()
        self.trendCheck.setChecked(False)
        self.linearInput.clear()
        self.exponentialInput.clear()
        self.logisticInput.clear()


# =============================================================================
#   Main Application
# =============================================================================

def main():
    app = QApplication(sys.argv)
    window = ContentWidget()
    window.setWindowTitle("SDSM Scenario Generator")
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
