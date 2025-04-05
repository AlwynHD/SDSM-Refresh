import sys
import os
import math
import random
import datetime
import matplotlib.pyplot as plt 
import numpy as np
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QGridLayout, QCheckBox, QRadioButton,
                             QButtonGroup, QFileDialog, QGroupBox, QMessageBox)
from PyQt5.QtCore import Qt

###############################################################################
# 1. SDSMContext: Stores parameters and data for scenario generation.
###############################################################################
class SDSMContext:
    def __init__(self):
        # File paths
        self.in_file = ""   # data file name (short)
        self.in_root = ""   # data file full path
        self.out_file = ""
        self.out_root = ""

        # Basic parameters
        self.start_date = datetime.date(2000, 1, 1)
        self.local_thresh = 0.1
        self.ensemble_size = 1
        self.no_of_days = 0

        # Data array (size: ensemble_size x no_of_days)
        self.data_array = []
        self.mean_array = []  # list of (mean, sd) for each ensemble

        # Treatment flags and parameters
        self.occurrence_check = False
        self.conditional_check = False
        self.occurrence_factor = 0              # frequency change in percentage points (e.g., 5 or -5)
        self.occurrence_factor_percent = 1.0    # computed as (100+freq)/100 for stochastic use
        self.occurrence_option = 0              # 0 = stochastic, 1 = forced
        self.preserve_totals_check = False

        self.amount_check = False
        self.amount_option = 0                  # 0 = factor, 1 = addition
        self.amount_factor = 0
        self.amount_factor_percent = 1.0
        self.amount_addition = 0.0

        self.variance_check = False
        self.variance_factor = 0
        self.variance_factor_percent = 1.0

        self.trend_check = False
        self.linear_trend = 0.0
        self.exp_trend = 0.0
        self.logistic_trend = 0.0
        self.trend_option = [False, False, False]  # [linear, exponential, logistic]

        self.lamda = 0.0

        # Global missing code
        self.global_missing_code = -999

        # Additional .PAR data
        self.num_predictors = 0
        self.num_months = 12
        self.year_length = 365

        # Monthly regression coefficients, if provided.
        self.monthly_coeffs = []
        # Predictor file paths (if provided)
        self.predictor_files = []

        # Bias Correction Parameter (defaulted here to 0.8)
        self.bias_correction = 0.8


###############################################################################
# 2. PAR File Parsing and SIM File Writing
###############################################################################
def parse_par_file(par_path: str, ctx: SDSMContext):
    lines = []
    with open(par_path, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                lines.append(line)
    idx = 0
    try:
        ctx.num_predictors = int(lines[idx]); idx += 1
        ctx.num_months = int(lines[idx]); idx += 1
        ctx.year_length = int(lines[idx]); idx += 1
        start_date_str = lines[idx]; idx += 1
        ctx.start_date = datetime.datetime.strptime(start_date_str, "%d/%m/%Y").date()
        ctx.no_of_days = int(lines[idx]); idx += 1
        idx += 2  # Skip possibly repeated date and days
        cond_str = lines[idx]; idx += 1
        ctx.conditional_check = (cond_str.upper() == "#TRUE#")
        ensemble_str = lines[idx]; idx += 1
        ctx.ensemble_size = int(ensemble_str)
        idx += 1  # Ignored numeric field
        idx += 1  # Ignored boolean
        ctx.predictor_files = []
        par_dir = os.path.dirname(par_path)
        for _ in range(ctx.num_predictors):
            pfile = lines[idx]
            idx += 1
            abs_pfile = os.path.join(par_dir, pfile)
            ctx.predictor_files.append(abs_pfile)
        if idx < len(lines):
            data_file = lines[idx]
            idx += 1
            abs_data_file = os.path.join(par_dir, data_file)
            ctx.in_file = os.path.basename(abs_data_file)
            ctx.in_root = abs_data_file
        ctx.monthly_coeffs = []
        for m in range(ctx.num_months):
            if idx >= len(lines):
                break
            coeff_strs = lines[idx].split()
            coeffs = [float(x) for x in coeff_strs]
            ctx.monthly_coeffs.append(coeffs)
            idx += 1
        QMessageBox.information(None, "Info", f"Loaded .PAR file:\n"
                                             f"Predictors: {ctx.num_predictors}, "
                                             f"Months: {ctx.num_months}, "
                                             f"Days: {ctx.no_of_days}, "
                                             f"Ensemble: {ctx.ensemble_size}, "
                                             f"Conditional: {ctx.conditional_check}")
    except (IndexError, ValueError) as e:
        QMessageBox.critical(None, "Error", f"Error parsing .PAR file:\n{e}")


def write_sim_file(ctx: SDSMContext):
    """
    Writes a .SIM file corresponding to the input and .OUT file for clarity.
    """
    line1 = str(ctx.num_predictors)
    line2 = str(ctx.num_months)
    line3 = str(ctx.year_length)
    line4 = ctx.start_date.strftime("%d/%m/%Y")
    line5 = str(ctx.no_of_days)
    line6 = "#TRUE#" if ctx.conditional_check else "#FALSE#"
    line7 = str(ctx.ensemble_size)
    line8 = str(ctx.variance_factor_percent)
    if ctx.conditional_check:
        if abs(ctx.lamda - 0.25) < 0.1:
            trans_code = "2"
        elif abs(ctx.lamda) < 0.01:
            trans_code = "3"
        else:
            trans_code = "1"
    else:
        trans_code = "1"
    line9 = trans_code
    line10 = str(ctx.bias_correction)
    line11 = ctx.in_file
    predictor_lines = [os.path.basename(p) for p in ctx.predictor_files]
    sim_lines = [
        line1, line2, line3, line4, line5, 
        line6, line7, line8, line9, line10, 
        line11
    ]
    sim_lines.extend(predictor_lines)
    sim_file_path = os.path.splitext(ctx.out_root)[0] + ".SIM"
    try:
        with open(sim_file_path, "w") as f:
            for line in sim_lines:
                f.write(line + "\n")
    except Exception as e:
        QMessageBox.critical(None, "Error", f"Error writing SIM file:\n{e}")
    print(f"SIM file written to {sim_file_path}")


###############################################################################
# 3. Core Scenario Generation Functions
###############################################################################
def increase_date(date_obj):
    return date_obj + datetime.timedelta(days=1)

def parse_value(str_val, ctx):
    val_str = str_val.strip()
    if val_str == "-999":
        return ctx.global_missing_code
    try:
        return float(val_str)
    except ValueError:
        return ctx.global_missing_code

def check_settings(ctx: SDSMContext) -> bool:
    if not ctx.in_file or len(ctx.in_file) < 5:
        QMessageBox.critical(None, "Error", "You must select an input file first (or a .PAR file).")
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
    # Enforce a max of 100 columns (help file states up to 100)
    if ctx.ensemble_size > 100:
        QMessageBox.critical(
            None, "Error",
            "The help file indicates a maximum of 100 ensemble columns.\n"
            f"You entered {ctx.ensemble_size}."
        )
        return False
    return True


def modify_data(ctx: SDSMContext):
    """
    Reads data from file, checks row/column constraints,
    then applies the chosen treatments and writes results.
    """
    if not check_settings(ctx):
        return

    # Try reading lines from the input file
    try:
        with open(ctx.in_root, "r") as f:
            lines = f.readlines()
    except Exception as e:
        QMessageBox.critical(None, "Error", f"Error reading input file:\n{e}")
        return

    if not lines:
        QMessageBox.critical(None, "Error", "Input file is empty.")
        return

    # 1) Check if we have more than ~73,000 days (200 years).
    #    The help file says up to 200 years, so let's pick 73,000 as a safe upper bound.
    if len(lines) > 73000:
        QMessageBox.critical(
            None, "Error",
            f"The file has {len(lines)} lines (days), exceeding the 200-year (73,000) limit!"
        )
        return

    # 2) Parse each line by splitting into columns
    #    Then check if we have enough columns to satisfy ensemble_size
    #    or if we have more than needed.
    #    We'll only parse up to ensemble_size columns (if more exist).
    #    If fewer columns exist, show an error and stop.
    actual_num_rows = len(lines)

    # Initialize data_array:
    # We will end up with shape [ensemble_size][some_day_count].
    # We'll parse day by day, appending to each ensemble's list.
    ctx.data_array = [[] for _ in range(ctx.ensemble_size)]

    for line_idx, line in enumerate(lines):
        parts = line.split()
        if len(parts) < ctx.ensemble_size:
            # Not enough columns in this row to fill the user-specified ensemble_size
            QMessageBox.critical(
                None, "Error",
                f"Line {line_idx+1} has only {len(parts)} columns, but ensemble_size is {ctx.ensemble_size}.\n"
                "Cannot continue."
            )
            return
        # If we have more columns than ensemble_size, just parse the first ensemble_size
        for ens_i in range(ctx.ensemble_size):
            val = parse_value(parts[ens_i], ctx)
            ctx.data_array[ens_i].append(val)

    # Now we have no_of_days = number of lines read
    ctx.no_of_days = len(ctx.data_array[0])

    # Everything loaded. Now do the transformations:
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

    # Finally, write the results out
    try:
        with open(ctx.out_root, "w") as f:
            for day_i in range(ctx.no_of_days):
                line_out = ""
                for ens_j in range(ctx.ensemble_size):
                    val = ctx.data_array[ens_j][day_i]
                    if val == ctx.global_missing_code:
                        line_out += "\t"
                    else:
                        line_out += f"{val:8.3f}\t"
                f.write(line_out + "\n")
    except Exception as e:
        QMessageBox.critical(None, "Error", f"Error writing output file:\n{e}")
        return

    write_sim_file(ctx)
    QMessageBox.information(None, "Success",
                            f"Scenario generated.\n{ctx.no_of_days} days processed.")


def apply_amount(ctx: SDSMContext):
    for j in range(ctx.ensemble_size):
        for i in range(ctx.no_of_days):
            val = ctx.data_array[j][i]
            if val != ctx.global_missing_code:
                if (not ctx.conditional_check) or (ctx.conditional_check and val > ctx.local_thresh):
                    if ctx.amount_option == 0:
                        # Factor
                        ctx.data_array[j][i] = val * ctx.amount_factor_percent
                    else:
                        # Addition
                        ctx.data_array[j][i] = val + ctx.amount_addition


def apply_occurrence(ctx: SDSMContext):
    random.seed()
    for j in range(ctx.ensemble_size):
        DryCount = [0] * 12
        WetCount = [0] * 12
        DayCount = [0] * 12
        OrigWetCount = [0] * 12
        WetArray = [[] for _ in range(12)]
        DryArray = [[] for _ in range(12)]
        TotalRainfall = 0.0
        TotalWetCount = 0
        current_date = ctx.start_date

        # Count how many wet/dry days per month, and which indices they occupy
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

        OrigWetCount = WetCount.copy()

        if TotalWetCount <= 0:
            QMessageBox.information(None, "Warning",
                                    f"Ensemble {j+1} has zero wet days; occurrence treatment skipped.")
            continue

        if ctx.occurrence_option == 0:
            # Stochastic Occurrence Treatment
            if ctx.occurrence_factor_percent < 1:
                # remove some wet days
                DaysToDelete = int(TotalWetCount - (TotalWetCount * ctx.occurrence_factor_percent))
                for _ in range(DaysToDelete):
                    possible_months = [ix for ix in range(12) if WetCount[ix] > 0]
                    if not possible_months:
                        break
                    m = random.choice(possible_months)
                    idx = random.randint(0, WetCount[m] - 1)
                    day = WetArray[m][idx]
                    ctx.data_array[j][day] = ctx.local_thresh
                    WetArray[m].pop(idx)
                    WetCount[m] -= 1
            elif ctx.occurrence_factor_percent > 1:
                # add some wet days
                DaysToAdd = int((TotalWetCount * ctx.occurrence_factor_percent) - TotalWetCount)
                available = ctx.no_of_days - TotalWetCount
                if DaysToAdd > available:
                    QMessageBox.critical(None, "Error", "Too many wet days to add (dataset overflow).")
                    return
                for _ in range(DaysToAdd):
                    possible_months = [ix for ix in range(12) if DryCount[ix] > 0]
                    if not possible_months:
                        break
                    m = random.choice(possible_months)
                    idx = random.randint(0, DryCount[m] - 1)
                    day = DryArray[m][idx]
                    # if the month had no original wet days, pick a wet day from a neighboring month
                    if OrigWetCount[m] == 0:
                        possible_wet_months = [ix for ix in range(12) if WetCount[ix] > 0]
                        if not possible_wet_months:
                            # no wet days anywhere, can't add
                            continue
                        m2 = random.choice(possible_wet_months)
                        wet_day = random.choice(WetArray[m2])
                        ctx.data_array[j][day] = ctx.data_array[j][wet_day]
                    else:
                        wet_day = random.choice(WetArray[m])
                        ctx.data_array[j][day] = ctx.data_array[j][wet_day]
                    DryArray[m].pop(idx)
                    DryCount[m] -= 1

        elif ctx.occurrence_option == 1:
            # Forced Occurrence Treatment
            for m in range(12):
                if DayCount[m] > 0:
                    current_percentage = (WetCount[m] / DayCount[m]) * 100
                else:
                    current_percentage = 0
                target_percentage = current_percentage + ctx.occurrence_factor
                target_percentage = max(0, min(100, target_percentage))
                target_wet_count = int(round((target_percentage / 100) * DayCount[m]))
                if WetCount[m] > target_wet_count:
                    # remove days
                    days_to_delete = WetCount[m] - target_wet_count
                    for _ in range(days_to_delete):
                        if WetCount[m] > 0:
                            idx = random.randint(0, WetCount[m] - 1)
                            day = WetArray[m][idx]
                            ctx.data_array[j][day] = ctx.local_thresh
                            WetArray[m].pop(idx)
                            WetCount[m] -= 1
                elif WetCount[m] < target_wet_count:
                    # add days
                    days_to_add = target_wet_count - WetCount[m]
                    for _ in range(days_to_add):
                        if DryCount[m] > 0:
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

            # Preserve Totals (optional)
            if ctx.preserve_totals_check:
                NewTotalRainfall = 0.0
                NewTotalWetCount = 0
                for i in range(ctx.no_of_days):
                    val = ctx.data_array[j][i]
                    if val != ctx.global_missing_code and val > ctx.local_thresh:
                        NewTotalRainfall += val
                        NewTotalWetCount += 1
                if NewTotalRainfall > 0:
                    multiplier = TotalRainfall / NewTotalRainfall
                    for i in range(ctx.no_of_days):
                        if (ctx.data_array[j][i] != ctx.global_missing_code and
                                ctx.data_array[j][i] > ctx.local_thresh):
                            ctx.data_array[j][i] *= multiplier
        else:
            QMessageBox.information(None, "Info", "Occurrence treatment option not recognized.")


def calc_means(ctx: SDSMContext):
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


def frange(start, stop, step):
    while start <= stop:
        yield start
        start += step


def find_min_lambda(ctx: SDSMContext, ensemble: int, start: float, finish: float, step: float) -> float:
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


def unbox_cox(value: float, lamda: float, ctx: SDSMContext) -> float:
    if value == ctx.global_missing_code:
        return ctx.global_missing_code
    if lamda == 0:
        return math.exp(value)
    else:
        return ((value * lamda) + 1) ** (1 / lamda)


def calc_variance(trans_array, factor, mean, no_of_days, ctx: SDSMContext) -> float:
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


def apply_variance(ctx: SDSMContext):
    for j in range(ctx.ensemble_size):
        if not ctx.conditional_check:
            # unconditional variance change
            for i in range(ctx.no_of_days):
                if ctx.data_array[j][i] != ctx.global_missing_code:
                    mean_j = ctx.mean_array[j][0]
                    ctx.data_array[j][i] = ((ctx.data_array[j][i] - mean_j) *
                                            math.sqrt(ctx.variance_factor_percent) +
                                            mean_j)
        else:
            # conditional => Box-Cox transform approach
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

            # apply that final middle factor
            for i in range(ctx.no_of_days):
                if trans_array[i] != ctx.global_missing_code:
                    trans_array[i] = ((trans_array[i] - mean_trans) * middle) + mean_trans
                    ctx.data_array[j][i] = unbox_cox(trans_array[i], ctx.lamda, ctx)


def apply_trend(ctx: SDSMContext):
    for j in range(ctx.ensemble_size):
        if ctx.trend_option[0]:
            # Linear
            year_days = 365
            increment = ctx.linear_trend / year_days
            for i in range(ctx.no_of_days):
                if ctx.data_array[j][i] != ctx.global_missing_code:
                    if not ctx.conditional_check:
                        ctx.data_array[j][i] += increment * i
                    else:
                        if ctx.data_array[j][i] > ctx.local_thresh:
                            # multiply by (1 + ???)
                            ctx.data_array[j][i] *= (1 + (ctx.linear_trend / (year_days * 100)) * i)

        if ctx.trend_option[1]:
            # Exponential
            exp_abs = abs(ctx.exp_trend)
            A = ctx.no_of_days / math.log(exp_abs + 1) if exp_abs != 0 else 1
            add_option = ctx.exp_trend > 0
            for i in range(ctx.no_of_days):
                if ctx.data_array[j][i] != ctx.global_missing_code:
                    delta = math.exp(i / A) - 1
                    if not ctx.conditional_check:
                        if add_option:
                            ctx.data_array[j][i] += delta
                        else:
                            ctx.data_array[j][i] -= delta
                    else:
                        if ctx.data_array[j][i] > ctx.local_thresh:
                            factor = (100 + delta) / 100 if add_option else (100 - delta) / 100
                            ctx.data_array[j][i] *= factor

        if ctx.trend_option[2]:
            # Logistic
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


###############################################################################
# 4. PyQt5 User Interface (ScenarioGeneratorWidget)
###############################################################################
class ScenarioGeneratorWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.ctx = SDSMContext()
        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(30, 30, 30, 30)
        mainLayout.setSpacing(20)
        self.setLayout(mainLayout)

        # File Selection Section
        fileSelectionGroup = QGroupBox("File Selection")
        fileSelectionLayout = QHBoxLayout()
        self.inputFileButton = QPushButton("📂 Select Input (.PAR or Data) File")
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

        # General Parameters Section
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

        # Treatment Parameters Section
        treatmentsGroup = QGroupBox("Treatment Parameters")
        treatmentsLayout = QGridLayout()
        # Occurrence
        self.occurrenceCheck = QCheckBox("⚡ Occurrence")
        self.frequencyChangeInput = QLineEdit()
        self.frequencyChangeInput.setPlaceholderText("e.g. 5 for +5 or -5 for -5")
        self.stochasticRadio = QRadioButton("Stochastic")
        self.forcedRadio = QRadioButton("Forced")
        self.preserveTotalCheck = QCheckBox("Preserve Total?")
        occButtonGroup = QButtonGroup()
        occButtonGroup.addButton(self.stochasticRadio)
        occButtonGroup.addButton(self.forcedRadio)
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
        # Amount Treatment
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
        # Trend Treatment
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

        # Buttons
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
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Input (.PAR or Data) File")
        if file_name:
            self.inputFileLabel.setText(file_name)
            if file_name.lower().endswith(".par"):
                parse_par_file(file_name, self.ctx)
            else:
                self.ctx.in_file = os.path.basename(file_name)
                self.ctx.in_root = file_name

    def selectOutputFile(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Save To File", "", "OUT Files (*.OUT);;All Files (*.*)")
        if file_name:
            if not file_name.lower().endswith(".out"):
                file_name += ".OUT"
            self.outputFileLabel.setText(file_name)
            self.ctx.out_file = os.path.basename(file_name)
            self.ctx.out_root = file_name

    def generateScenario(self):
        # Read the user inputs from the GUI
        if self.startDateInput.text():
            try:
                dt = datetime.datetime.strptime(self.startDateInput.text(), "%d/%m/%Y")
                self.ctx.start_date = dt.date()
            except Exception:
                QMessageBox.critical(self, "Error", "Start Date must be in DD/MM/YYYY format.")
                return
        if self.ensembleSizeInput.text():
            try:
                ens = int(self.ensembleSizeInput.text())
                self.ctx.ensemble_size = ens
            except Exception:
                QMessageBox.critical(self, "Error", "Ensemble Size must be an integer.")
                return
        if self.eventThresholdInput.text():
            try:
                thresh_val = float(self.eventThresholdInput.text())
                self.ctx.local_thresh = thresh_val
            except Exception:
                self.ctx.local_thresh = 0.1

        self.ctx.conditional_check = self.conditionalProcessCheck.isChecked()
        self.ctx.occurrence_check = self.occurrenceCheck.isChecked()
        if self.frequencyChangeInput.text():
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

        self.ctx.variance_check = self.varianceCheck.isChecked()
        if self.varianceFactorInput.text():
            try:
                vfac = float(self.varianceFactorInput.text())
                self.ctx.variance_factor = vfac
                self.ctx.variance_factor_percent = (100 + vfac) / 100
            except Exception:
                self.ctx.variance_factor = 0
                self.ctx.variance_factor_percent = 1.0

        self.ctx.trend_check = self.trendCheck.isChecked()

        try:
            linear = float(self.linearInput.text()) if self.linearInput.text() else 0.0
            self.ctx.linear_trend = linear
            self.ctx.trend_option[0] = (linear != 0)
        except Exception:
            self.ctx.linear_trend = 0.0
            self.ctx.trend_option[0] = False

        try:
            exp = float(self.exponentialInput.text()) if self.exponentialInput.text() else 0.0
            self.ctx.exp_trend = exp
            self.ctx.trend_option[1] = (exp != 0)
        except Exception:
            self.ctx.exp_trend = 0.0
            self.ctx.trend_option[1] = False

        try:
            logistic = float(self.logisticInput.text()) if self.logisticInput.text() else 0.0
            self.ctx.logistic_trend = logistic
            self.ctx.trend_option[2] = (logistic != 0)
        except Exception:
            self.ctx.logistic_trend = 0.0
            self.ctx.trend_option[2] = False

        # Now run the main scenario generation
        modify_data(self.ctx)

    def resetFields(self):
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


###############################################################################
# 5. Main Application Entry Point
###############################################################################
def main():
    app = QApplication(sys.argv)
    window = ScenarioGeneratorWidget()
    window.setWindowTitle("SDSM Scenario Generator (with .PAR support)")
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

# Alias for dynamic module loading:
ContentWidget = ScenarioGeneratorWidget
