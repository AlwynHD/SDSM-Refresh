import sys
import os
import math
import random
import datetime
import statistics

from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QGridLayout, QCheckBox, QRadioButton,
                             QButtonGroup, QFileDialog, QGroupBox, QMessageBox, QProgressBar,
                             QStyle) # Added QStyle for icons
from PyQt5.QtCore import Qt, QTimer

# --- Global Constants (Mirroring VB Globals) ---
GLOBAL_MISSING_CODE = -999.0
DEFAULT_THRESHOLD = 0.0
DEFAULT_START_DATE = datetime.date(2000, 1, 1)
DEFAULT_YEAR_INDICATOR = 365

# ... (Keep all your existing global functions and SDSMContext class here) ...
# Rnd(), g_dd, g_mm, g_yyyy, SDSMContext, is_leap, days_in_month, increase_date,
# parse_value, format_value_output, check_settings, mini_reset, read_input_file,
# apply_occurrence, set_random_array, calc_means, apply_amount, find_min_lambda,
# unbox_cox, calc_variance_after_transform, apply_variance, apply_trend,
# write_output_file, parse_par_file
# (These functions are not modified for UI changes, so they are omitted for brevity in this response,
#  but they MUST be present in your actual file.)
# --- Global Constants (Mirroring VB Globals) ---
GLOBAL_MISSING_CODE = -999.0
DEFAULT_THRESHOLD = 0.0
DEFAULT_START_DATE = datetime.date(2000, 1, 1)
DEFAULT_YEAR_INDICATOR = 365

# Simulate VB's Rnd() function
def Rnd():
    """Simulates VB's Rnd() function - returns float between 0 and 1"""
    return random.random()

# Global date variables to match VB's approach
g_dd = 0
g_mm = 0
g_yyyy = 0

###############################################################################
# 1. SDSMContext: Stores parameters and data for scenario generation.
###############################################################################
class SDSMContext:
    def __init__(self):
        self.reset()

    def reset(self):
        # File paths
        self.in_file = ""
        self.in_root = ""
        self.out_file = ""
        self.out_root = ""

        # Basic parameters
        self.start_date = DEFAULT_START_DATE
        self.local_thresh = DEFAULT_THRESHOLD
        self.ensemble_size = 1
        self.no_of_days = 0
        self.year_indicator = DEFAULT_YEAR_INDICATOR # From VB globals (adjust if needed)
        self.year_length = 365 # To match VB's YearLength variable

        # Data array (List of lists: [ensemble][day])
        self.data_array = []
        self.mean_array = []  # list of (mean, sd) for each ensemble

        # Treatment flags and parameters
        self.occurrence_check = False
        self.conditional_check = False # If true, only > threshold values are modified for amount/variance/trend
        self.occurrence_factor = 0.0   # User input value (e.g., 5 for +5%)
        self.occurrence_factor_percent = 1.0 # Multiplier (e.g., 1.05 for +5%)
        self.occurrence_option = 0      # 0 = Stochastic (Factor), 1 = Forced (Percentage)
        self.preserve_totals_check = False # For occurrence

        self.amount_check = False
        self.amount_option = 0          # 0 = factor, 1 = addition
        self.amount_factor = 0.0        # User input value (e.g., 5 for +5%)
        self.amount_factor_percent = 1.0 # Multiplier (e.g., 1.05 for +5%)
        self.amount_addition = 0

        self.variance_check = False
        self.variance_factor = 0.0      # User input value (e.g., 10 for +10%)
        self.variance_factor_percent = 1.0 # Target variance ratio (e.g., 1.10 for +10%)

        self.trend_check = False
        self.linear_trend = 0.0
        self.exp_trend = 1.0 # VB code defaults ExpTrend to 1
        self.logistic_trend = 1.0 # VB code defaults LogisticTrend to 1
        self.trend_option = 0 # 0 = Linear, 1 = Exponential, 2 = Logistic (matching VB OptionButton index)
        self.add_exp_option = True # Derived from ExpTrend sign

        self.lamda = 0.0 # Box-Cox lambda

        # Processing state
        self.error_occurred = False
        self.global_kop_out = False # Flag to stop processing (like VB Escape key)

        # PAR-related (keeping some for potential use)
        self.num_predictors = 0
        self.num_months = 12
        self.monthly_coeffs = []
        self.predictor_files = []
        self.bias_correction = 0.8 # Default
        self.zom = [0.0] * 12 # ZoM array for forced occurrence

###############################################################################
# 2. Helper Functions (Mirroring VB)
###############################################################################

def is_leap(year):
    """Checks if a year is a leap year."""
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

def days_in_month(year, month):
    """Returns the number of days in a specific month of a year."""
    if month == 2:
        return 29 if is_leap(year) else 28
    elif month in [4, 6, 9, 11]:
        return 30
    else:
        return 31

# VB-style date increment using global variables
def increase_date(ctx=None):
    """Increases date by one day using VB approach."""
    global g_dd, g_mm, g_yyyy

    g_dd += 1

    # Get days in current month - match VB logic
    if ctx and ctx.year_length == 1 and g_mm == 2 and is_leap(g_yyyy):
        # VB checks YearLength = 1 for leap year adjustment
        days_current_month = 29
    else:
        days_current_month = days_in_month(g_yyyy, g_mm)

    if g_dd > days_current_month:
        g_mm += 1
        g_dd = 1

    if g_mm == 13:
        g_mm = 1
        g_yyyy += 1

def parse_value(str_val):
    """Parses a string to float, handling missing code."""
    val_str = str_val.strip()
    try:
        val = float(val_str)
        # Handle potential missing codes represented differently
        if abs(val - GLOBAL_MISSING_CODE) < 1e-6:
            return GLOBAL_MISSING_CODE
        return val
    except ValueError:
        return GLOBAL_MISSING_CODE

def format_value_output(value):
    """Formats float for output file, handling missing code."""
    if abs(value - GLOBAL_MISSING_CODE) < 1e-6:
        # Output missing as empty space or a specific string if required
        # VB used Tab, implying empty field for missing
        return "\t"
    else:
        # VB format "#####0.000" -> 8 characters wide, 3 decimal places, right-aligned
        return f"{value:8.3f}\t" # Adjust width (8) if needed

def check_settings(ctx: SDSMContext, parent_widget=None) -> bool:
    """Checks if user has sensible options selected (mirrors VB)."""
    all_ok = True
    if not ctx.in_file or len(ctx.in_file) < 1: # Allow single char names
        QMessageBox.critical(parent_widget, "Error", "You must select an input file first.")
        all_ok = False
    elif not ctx.out_file:
        QMessageBox.critical(parent_widget, "Error", "You must enter a filename to save results to.")
        all_ok = False
    elif not (ctx.occurrence_check or ctx.amount_check or ctx.trend_check or ctx.variance_check):
        QMessageBox.critical(parent_widget, "Error", "You must select at least one treatment.")
        all_ok = False
    elif ctx.occurrence_check and not ctx.conditional_check:
        QMessageBox.critical(parent_widget, "Error", "You cannot perform an occurrence treatment on data that are unconditional.")
        all_ok = False
    # Amount Checks
    elif ctx.amount_check and ctx.amount_option == 0 and abs(ctx.amount_factor_percent - 1.0) < 1e-6:
        QMessageBox.critical(parent_widget, "Error", "You are trying to apply an amount treatment (Factor) but applying no change (0%).")
        all_ok = False
    elif ctx.amount_check and ctx.amount_option == 1 and abs(ctx.amount_addition) < 1e-6:
         QMessageBox.critical(parent_widget, "Error", "You are trying to apply an amount treatment (Addition) but applying no change (0).")
         all_ok = False
    # Occurrence Checks
    elif ctx.occurrence_check and ctx.occurrence_option == 0 and abs(ctx.occurrence_factor_percent - 1.0) < 1e-6:
        QMessageBox.critical(parent_widget, "Error", "You are trying to perform an occurrence treatment (Factor) but applying zero frequency change.")
        all_ok = False
    # Variance Checks
    elif ctx.variance_check and abs(ctx.variance_factor_percent - 1.0) < 1e-6:
         QMessageBox.critical(parent_widget, "Error", "You are trying to apply a variance change but have not entered an amount (0%).")
         all_ok = False
    # Trend Checks (ensure a value is set if checked)
    elif ctx.trend_check and ctx.trend_option == 0 and abs(ctx.linear_trend) < 1e-9 :
        QMessageBox.critical(parent_widget, "Error", "Linear trend is selected, but the value is zero.")
        all_ok = False
    elif ctx.trend_check and ctx.trend_option == 1 and abs(ctx.exp_trend) < 1e-9 : # abs(1.0 - 1.0) is zero, so check against the input value
        QMessageBox.critical(parent_widget, "Error", "Exponential trend is selected, but the value (factor) is effectively 1 (or zero if referring to additive effect).")
        all_ok = False
    elif ctx.trend_check and ctx.trend_option == 2 and abs(ctx.logistic_trend) < 1e-9 : # abs(1.0 - 1.0) is zero.
        QMessageBox.critical(parent_widget, "Error", "Logistic trend is selected, but the value (factor) is effectively 1 (or zero if referring to additive effect).")
        all_ok = False

    return all_ok

def mini_reset(ctx: SDSMContext):
    """Resets flags for a new operation or after error (simpler than VB)."""
    ctx.error_occurred = False
    ctx.global_kop_out = False

###############################################################################
# 3. Core Scenario Generation Functions (Detailed Translation)
###############################################################################

def read_input_file(ctx: SDSMContext, progress_callback=None):
    """Reads data from file, performs basic checks."""
    try:
        with open(ctx.in_root, "r") as f:
            lines = f.readlines()
    except Exception as e:
        QMessageBox.critical(None, "File Read Error", f"Error reading input file:\n{e}")
        ctx.error_occurred = True
        return False

    if not lines:
        QMessageBox.critical(None, "File Read Error", "Input file is empty.")
        ctx.error_occurred = True
        return False

    ctx.no_of_days = len(lines)
    if ctx.no_of_days > 75000: # VB limit check (approx 200 years)
         QMessageBox.warning(None, "Warning", f"Input file has {ctx.no_of_days} days, which exceeds the typical limit (around 75000). Processing will continue, but may be slow or unstable.")

    # Initialize data_array: list of lists [ensemble][day]
    ctx.data_array = [[] for _ in range(ctx.ensemble_size)]
    expected_columns = ctx.ensemble_size

    for i, line in enumerate(lines):
        if ctx.global_kop_out: return False # Check for user cancel
        if progress_callback:
            progress_callback(int(i / ctx.no_of_days * 100), "Reading Data")

        parts = line.split() # Split by whitespace
        actual_columns = len(parts)

        if i == 0 and actual_columns < expected_columns: # Check first line for column count
            QMessageBox.critical(None, "File Format Error",
                                 f"Data file seems to have fewer columns ({actual_columns}) than the specified Ensemble Size ({expected_columns}).\nPlease check the input file and Ensemble Size setting.")
            ctx.error_occurred = True
            return False
        elif actual_columns < expected_columns:
            # Handle lines with fewer columns - treat missing as GLOBAL_MISSING_CODE
            parsed_vals = [parse_value(p) for p in parts]
            parsed_vals.extend([GLOBAL_MISSING_CODE] * (expected_columns - actual_columns))
        else:
             # Take only the first 'expected_columns' values
            parsed_vals = [parse_value(parts[j]) for j in range(expected_columns)]

        # Append parsed values to each ensemble's list
        for ens_j in range(expected_columns):
             ctx.data_array[ens_j].append(parsed_vals[ens_j])

    if progress_callback: progress_callback(100, "Reading Data Complete")
    return True


def apply_occurrence(ctx: SDSMContext, progress_callback=None):
    """Apply an occurrence treatment (add/remove wet days). Mirrors VB logic."""
    global g_dd, g_mm, g_yyyy

    if not ctx.conditional_check: # Should have been caught by check_settings
        QMessageBox.critical(None, "Logic Error", "Occurrence treatment requires conditional process.")
        ctx.error_occurred = True
        return

    random.seed() # Initialize random seed
    given_zero_warning = False

    for j in range(ctx.ensemble_size): # Loop through each ensemble
        if ctx.global_kop_out: return
        if progress_callback:
            progress_callback(int(j / ctx.ensemble_size * 100), f"Applying Occurrence Ensemble {j+1}")

        # --- Initialize monthly counts and arrays for this ensemble ---
        # Use 0-based indexing for months (0-11)
        dry_count = [0] * 12
        wet_count = [0] * 12
        day_count = [0] * 12 # Total non-missing days per month
        wet_array = [[] for _ in range(12)] # Stores indices of wet days for each month
        dry_array = [[] for _ in range(12)] # Stores indices of dry days for each month
        prop_wet_array = [0.0] * 12
        prop_dry_array = [0.0] * 12
        total_rainfall = 0.0
        total_wet_count = 0

        # --- First Pass: Count wet/dry days per month and store indices ---
        g_dd = ctx.start_date.day
        g_mm = ctx.start_date.month
        g_yyyy = ctx.start_date.year

        for i in range(ctx.no_of_days):
            val = ctx.data_array[j][i]
            m = g_mm - 1 # 0-based month index

            if val != GLOBAL_MISSING_CODE:
                day_count[m] += 1
                if val > ctx.local_thresh:
                    wet_count[m] += 1
                    wet_array[m].append(i) # Store the day index 'i'
                    total_rainfall += val
                    total_wet_count += 1
                else:
                    dry_count[m] += 1
                    dry_array[m].append(i) # Store the day index 'i'

            # Increment date using VB-style approach
            increase_date(ctx)

        original_wet_count = wet_count[:] # Keep original count for adding days logic

        # --- Calculate proportions ---
        for m in range(12):
            sum_days = day_count[m] # Use total non-missing days
            if sum_days > 0:
                prop_wet_array[m] = wet_count[m] / sum_days
                prop_dry_array[m] = dry_count[m] / sum_days
            else:
                prop_wet_array[m] = GLOBAL_MISSING_CODE # Indicate no data for month
                prop_dry_array[m] = GLOBAL_MISSING_CODE

        # --- Check if any wet days exist ---
        if total_wet_count <= 0:
            if not given_zero_warning:
                msg = f"Warning - Ensemble {j+1} has zero rainfall days and cannot be manipulated by occurrence treatment."
                if ctx.ensemble_size == 1:
                    msg = "Warning - there are zero rainfall days available so the data cannot be manipulated by occurrence treatment."
                QMessageBox.warning(None, "Results", msg)
                given_zero_warning = True
            continue # Skip to next ensemble

        # --- Perform Occurrence Modification ---

        # Option 0: Stochastic Factor Adjustment
        if ctx.occurrence_option == 0:
            if ctx.occurrence_factor_percent < 1.0:
                # --- Remove wet days ---
                days_to_delete = round(total_wet_count - (total_wet_count * ctx.occurrence_factor_percent))
                if days_to_delete <= 0 : continue # No days to delete

                # Build cumulative probability based on *dryness* (higher chance to remove from drier months)
                # VB uses PropDryArray but excludes fully dry months
                cum_prop_sum = [0.0] * 12
                if prop_dry_array[0] == GLOBAL_MISSING_CODE or prop_dry_array[0] == 1.0:
                    cum_prop_sum[0] = 0.0
                else:
                    cum_prop_sum[0] = prop_dry_array[0]

                for i in range(1, 12):
                    if prop_dry_array[i] == GLOBAL_MISSING_CODE or prop_dry_array[i] == 1.0:
                        cum_prop_sum[i] = cum_prop_sum[i-1]
                    else:
                        cum_prop_sum[i] = cum_prop_sum[i-1] + prop_dry_array[i]
                if cum_prop_sum[11] == 0.0: # All months are fully dry or missing, cannot remove
                    continue

                for _ in range(days_to_delete):
                    # VB-style random selection using cumulative probability
                    selected_month = -1
                    random_no = Rnd() * cum_prop_sum[11]

                    for i in range(12):
                        if random_no < cum_prop_sum[i]:
                            selected_month = i
                            break

                    if selected_month == -1: # Should not happen if cum_prop_sum[11] > 0
                        selected_month = 11


                    # Make sure we get a month with wet days
                    attempts = 0
                    while wet_count[selected_month] <= 0 and attempts < 12:
                        # This logic might be flawed if the month selected based on dryness has no wet days
                        # Fallback: just find any month with wet days if direct selection fails
                        selected_month = (selected_month + 1) % 12 # Simple linear scan
                        attempts += 1

                    if wet_count[selected_month] <= 0:
                        # If still no wet days after attempts, try to find one in any month
                        found_wet_month = False
                        for m_idx in range(12):
                            if wet_count[m_idx] > 0:
                                selected_month = m_idx
                                found_wet_month = True
                                break
                        if not found_wet_month: continue # No wet days available anywhere

                    # Select a random wet day for that month
                    wet_day_list_index = int(Rnd() * wet_count[selected_month])
                    day_index_to_modify = wet_array[selected_month][wet_day_list_index]

                    # Set the day to dry (using local threshold)
                    ctx.data_array[j][day_index_to_modify] = ctx.local_thresh # Or 0.0 if threshold is 0

                    # Remove the day index from wet_array and add to dry_array
                    if wet_day_list_index < wet_count[selected_month] - 1:
                        wet_array[selected_month][wet_day_list_index] = wet_array[selected_month][-1]
                    wet_array[selected_month].pop()

                    # Add to dry array
                    dry_array[selected_month].append(day_index_to_modify)

                    # Update counts
                    wet_count[selected_month] -= 1
                    dry_count[selected_month] += 1
                    total_wet_count -= 1

                    # Update cumulative probability if month became fully dry for selection
                    if wet_count[selected_month] == 0:
                        # Rebuild cum_prop_sum or adjust the specific month's contribution
                        if prop_dry_array[selected_month] != GLOBAL_MISSING_CODE and prop_dry_array[selected_month] != 1.0:
                            # This month was part of cum_prop_sum calculation, if it becomes non-selectable (fully wet/dry)
                            # for removal, its effective prop_dry for selection criteria changes.
                            # Simplified: if this month is no longer a candidate, its cum_prop needs adjustment.
                            # VB's logic seems to allow selection from a month until it has no more wet days.
                            # The cum_prop_sum is based on initial dryness, not dynamically updated based on removed days.
                            pass


            elif ctx.occurrence_factor_percent > 1.0:
                # --- Add wet days ---
                days_to_add = round((total_wet_count * ctx.occurrence_factor_percent) - total_wet_count)
                spaces_available = ctx.no_of_days - total_wet_count # Total non-wet days
                if days_to_add > spaces_available:
                    QMessageBox.critical(None, "Error Message", f"Ensemble {j+1}: You cannot add that many wet days ({days_to_add}) as there are only {spaces_available} dry/missing days available.")
                    ctx.error_occurred = True
                    return # Stop processing

                if days_to_add <= 0: continue # No days to add

                # Build cumulative probability based on *wetness* (higher chance to add to wetter months)
                cum_prop_sum = [0.0] * 12
                if prop_wet_array[0] == GLOBAL_MISSING_CODE or prop_wet_array[0] == 1.0: # If fully wet or no data
                    cum_prop_sum[0] = 0.0
                else:
                    cum_prop_sum[0] = prop_wet_array[0]

                for i in range(1, 12):
                    if prop_wet_array[i] == GLOBAL_MISSING_CODE or prop_wet_array[i] == 1.0:
                        cum_prop_sum[i] = cum_prop_sum[i-1]
                    else:
                        cum_prop_sum[i] = cum_prop_sum[i-1] + prop_wet_array[i]
                if cum_prop_sum[11] == 0.0: # All months are fully dry or missing, cannot add based on wetness
                    # Fallback: could distribute randomly or based on month length if no wetness guidance
                    # For now, if no "wet" months to guide, skip adding based on this logic
                    continue


                for _ in range(days_to_add):
                    # VB-style random selection using cumulative probability
                    selected_month = -1
                    random_no = Rnd() * cum_prop_sum[11]

                    for i in range(12):
                        if random_no < cum_prop_sum[i]:
                            selected_month = i
                            break

                    if selected_month == -1:
                        selected_month = 11

                    # Make sure we get a month with dry days
                    attempts = 0
                    while dry_count[selected_month] <= 0 and attempts < 12:
                        selected_month = (selected_month + 1) % 12 # Linear scan
                        attempts += 1

                    if dry_count[selected_month] <= 0:
                        # If still no dry days, find any month with dry days
                        found_dry_month = False
                        for m_idx in range(12):
                            if dry_count[m_idx] > 0:
                                selected_month = m_idx
                                found_dry_month = True
                                break
                        if not found_dry_month: continue # No dry days available anywhere

                    # Select a random dry day for that month
                    dry_day_list_index = int(Rnd() * dry_count[selected_month])
                    day_index_to_modify = dry_array[selected_month][dry_day_list_index]

                    # --- Select a wet day value to copy using VB logic ---
                    source_wet_day_value = GLOBAL_MISSING_CODE

                    # VB Logic: Prioritize using a wet day from the *same* month if available (original count)
                    # Using current wet_count[selected_month] is more robust if days are added iteratively
                    if wet_count[selected_month] > 0:
                        source_wet_day_index_in_list = int(Rnd() * wet_count[selected_month])
                        source_day_index = wet_array[selected_month][source_wet_day_index_in_list]
                        source_wet_day_value = ctx.data_array[j][source_day_index]
                    # If no wet day found in the selected month, find nearest month with a wet day
                    elif original_wet_count[selected_month] > 0: # Fallback to original if current has none (should not happen if wet_count >0 check fails)
                        # This part might be redundant if the first check on wet_count[selected_month] is sufficient.
                        # Original VB might have used original_wet_count here. Let's assume current wet_count for source.
                        pass


                    if source_wet_day_value == GLOBAL_MISSING_CODE: # If still no value (e.g. selected month had no current wet days)
                        search_order = set_random_array(selected_month)
                        for neighbor_month in search_order:
                            if wet_count[neighbor_month] > 0:
                                source_wet_day_index_in_list = int(Rnd() * wet_count[neighbor_month])
                                source_day_index = wet_array[neighbor_month][source_wet_day_index_in_list]
                                source_wet_day_value = ctx.data_array[j][source_day_index]
                                break # Found wet day in neighbor

                    # Apply the selected wet day value
                    if source_wet_day_value != GLOBAL_MISSING_CODE:
                        ctx.data_array[j][day_index_to_modify] = source_wet_day_value

                        # Remove the day index from dry_array and add to wet_array
                        if dry_day_list_index < dry_count[selected_month] - 1:
                            dry_array[selected_month][dry_day_list_index] = dry_array[selected_month][-1]
                        dry_array[selected_month].pop()

                        # Add to wet array
                        wet_array[selected_month].append(day_index_to_modify)

                        # Update counts
                        dry_count[selected_month] -= 1
                        wet_count[selected_month] += 1
                        total_wet_count += 1
                        # Note: cum_prop_sum for adding is based on initial wetness and not dynamically updated here.

        # Option 1: Forced Percentage (Not fully implemented in provided VB, assuming based on name)
        elif ctx.occurrence_option == 1:
             # This requires ctx.zom to be set, e.g., ctx.zom = [10.0, 12.0, ...] %
             if not hasattr(ctx, 'zom') or len(ctx.zom) != 12:
                 QMessageBox.critical(None,"Error", "Forced occurrence requires target percentages (ZoM) for each month, which are not set.")
                 ctx.error_occurred = True
                 return

             for m in range(12): # Loop through each month
                 if day_count[m] <= 0: continue # Skip months with no data

                 target_percentage = ctx.zom[m] / 100.0
                 target_wet_count = round(target_percentage * day_count[m])
                 current_wet_count_month = wet_count[m] # Use per-month wet_count

                 if current_wet_count_month > target_wet_count:
                     # --- Remove wet days ---
                     days_to_delete = current_wet_count_month - target_wet_count
                     for _ in range(days_to_delete):
                          if wet_count[m] <= 0: break
                          wet_day_list_index = int(Rnd() * wet_count[m])
                          day_index_to_modify = wet_array[m][wet_day_list_index]
                          ctx.data_array[j][day_index_to_modify] = ctx.local_thresh

                          if wet_day_list_index < wet_count[m] - 1:
                              wet_array[m][wet_day_list_index] = wet_array[m][-1]
                          wet_array[m].pop()
                          dry_array[m].append(day_index_to_modify)

                          wet_count[m] -= 1
                          dry_count[m] += 1
                          total_wet_count -= 1 # Keep track of overall total

                 elif current_wet_count_month < target_wet_count:
                     # --- Add wet days ---
                     days_to_add = target_wet_count - current_wet_count_month
                     for _ in range(days_to_add):
                         if dry_count[m] <= 0: break # No space left to add in this month

                         dry_day_list_index = int(Rnd() * dry_count[m])
                         day_index_to_modify = dry_array[m][dry_day_list_index]

                         # --- Select source wet day value (same logic as stochastic add) ---
                         source_wet_day_value = GLOBAL_MISSING_CODE
                         if wet_count[m] > 0: # Use current wet days in the month
                              source_wet_day_index_in_list = int(Rnd() * wet_count[m])
                              source_day_index = wet_array[m][source_wet_day_index_in_list]
                              source_wet_day_value = ctx.data_array[j][source_day_index]
                         else: # If current month has no wet days, look at neighbors
                             search_order = set_random_array(m)
                             for neighbor_month in search_order:
                                 if wet_count[neighbor_month] > 0:
                                     source_wet_day_index_in_list = int(Rnd() * wet_count[neighbor_month])
                                     source_day_index = wet_array[neighbor_month][source_wet_day_index_in_list]
                                     source_wet_day_value = ctx.data_array[j][source_day_index]
                                     break

                         if source_wet_day_value != GLOBAL_MISSING_CODE:
                             ctx.data_array[j][day_index_to_modify] = source_wet_day_value

                             if dry_day_list_index < dry_count[m] - 1:
                                 dry_array[m][dry_day_list_index] = dry_array[m][-1]
                             dry_array[m].pop()
                             wet_array[m].append(day_index_to_modify)

                             dry_count[m] -= 1
                             wet_count[m] += 1
                             total_wet_count += 1

        # --- Preserve Totals (Optional) ---
        if ctx.preserve_totals_check:
            new_total_rainfall = 0.0
            new_total_wet_days = 0
            for i in range(ctx.no_of_days):
                val = ctx.data_array[j][i]
                if val != GLOBAL_MISSING_CODE and val > ctx.local_thresh:
                    new_total_rainfall += val
                    new_total_wet_days += 1

            if new_total_rainfall > 1e-9 and total_rainfall > 1e-9 and new_total_wet_days > 0: # Avoid division by zero or near-zero
                rainfall_multiplier = total_rainfall / new_total_rainfall
                if abs(rainfall_multiplier - 1.0) > 1e-6: # Only apply if change is significant
                    for i in range(ctx.no_of_days):
                        if ctx.data_array[j][i] != GLOBAL_MISSING_CODE and ctx.data_array[j][i] > ctx.local_thresh:
                             # Apply multiplier, but ensure result doesn't go below threshold
                             new_val = ctx.data_array[j][i] * rainfall_multiplier
                             ctx.data_array[j][i] = max(ctx.local_thresh + 1e-6, new_val) # Ensure stays above threshold

    if progress_callback: progress_callback(100, "Applying Occurrence Complete")


def set_random_array(selected_month):
    """Generates a random sequence of months around the selected month (0-11). Mirrors VB."""
    # VB used Rnd < 0.5, Python mimics this
    multiplier = 1 if Rnd() < 0.5 else -1
    temp_array = [0] * 11 # 11 other months
    idx = 0
    for i in range(1, 7): # Offsets 1 to 6
        # Alternate adding +i*mult and -i*mult
        if idx < 11:
            temp_array[idx] = multiplier * i
            idx += 1
        if idx < 11 and i <= 5: # Offsets -1 to -5 (opposite sign)
            temp_array[idx] = -multiplier * i # VB had -i*multiplier, corrected to -multiplier*i or similar
            idx += 1

    random_array = [0] * 11
    for i in range(11):
        month_val = temp_array[i] + (selected_month + 1) # Convert to 1-based for calculation
        # Wrap around using modulo logic
        if month_val > 12:
            month_val -= 12
        elif month_val < 1:
             month_val += 12
        random_array[i] = month_val - 1 # Convert back to 0-based
    return random_array


def calc_means(ctx: SDSMContext, progress_callback=None):
    """Calculates mean and SD for each ensemble. Stores in ctx.mean_array."""
    ctx.mean_array = [] # Reset
    for j in range(ctx.ensemble_size):
        if ctx.global_kop_out: return
        if progress_callback:
             progress_callback(int(j / ctx.ensemble_size * 50), f"Calculating Mean/SD {j+1}") # 50% for means

        values_for_stats = []
        for i in range(ctx.no_of_days):
            val = ctx.data_array[j][i]
            if val != GLOBAL_MISSING_CODE:
                # Check conditional flag
                if not ctx.conditional_check or (ctx.conditional_check and val > ctx.local_thresh):
                    values_for_stats.append(val)

        mean = GLOBAL_MISSING_CODE
        sd = GLOBAL_MISSING_CODE
        count = len(values_for_stats)

        if count > 0:
            mean = sum(values_for_stats) / count
            if count > 1: # Need at least 2 points for standard deviation
                variance = sum([(x - mean) ** 2 for x in values_for_stats]) / count # Population variance (like VB)
                sd = math.sqrt(variance)
            else:
                sd = 0.0 # SD is 0 if only one point

        ctx.mean_array.append({'mean': mean, 'sd': sd})

    if progress_callback: progress_callback(100, "Calculating Mean/SD Complete")


def apply_amount(ctx: SDSMContext, progress_callback=None):
    """Apply an amount factor or addition to data."""
    for j in range(ctx.ensemble_size):
        if ctx.global_kop_out: return
        if progress_callback:
             progress_callback(int(j / ctx.ensemble_size * 100), f"Applying Amount {j+1}")

        if ctx.amount_option == 0:  # Factor
            if abs(ctx.amount_factor_percent - 1.0) < 1e-6: continue # Skip if factor is 1.0
            for i in range(ctx.no_of_days):
                val = ctx.data_array[j][i]
                if val != GLOBAL_MISSING_CODE:
                    if not ctx.conditional_check or (ctx.conditional_check and val > ctx.local_thresh):
                         new_val = val * ctx.amount_factor_percent
                         # Ensure result doesn't go below threshold if it was above
                         if ctx.conditional_check and val > ctx.local_thresh and new_val <= ctx.local_thresh:
                             ctx.data_array[j][i] = ctx.local_thresh + 1e-6 # Set just above
                         elif not ctx.conditional_check and val <= ctx.local_thresh and new_val <= ctx.local_thresh:
                             # For unconditional, if it was dry and becomes "more dry", keep it at original dry value or threshold
                             ctx.data_array[j][i] = val # Or clamp to threshold if that's desired. Original logic for non-conditional is simple multiplication.
                         else:
                             ctx.data_array[j][i] = new_val
        else:  # Addition
            if abs(ctx.amount_addition) < 1e-6: continue # Skip if addition is 0
            for i in range(ctx.no_of_days):
                 val = ctx.data_array[j][i]
                 if val != GLOBAL_MISSING_CODE:
                     if not ctx.conditional_check or (ctx.conditional_check and val > ctx.local_thresh):
                         new_val = val + ctx.amount_addition
                          # Ensure result doesn't go below threshold if it was above
                         if ctx.conditional_check and val > ctx.local_thresh and new_val <= ctx.local_thresh:
                             ctx.data_array[j][i] = ctx.local_thresh + 1e-6 # Set just above
                         elif not ctx.conditional_check and val <= ctx.local_thresh and new_val <= ctx.local_thresh:
                             # Similar to factor, if unconditional and it was dry, adding a negative might make it "more dry"
                             # VB usually applies addition straightforwardly.
                             # If new_val would make a non-conditional value cross threshold downwards, VB might just apply it.
                             # The concern is mainly for conditional cases keeping values > threshold.
                             ctx.data_array[j][i] = new_val
                         else:
                             ctx.data_array[j][i] = new_val

    if progress_callback: progress_callback(100, "Applying Amount Complete")


def find_min_lambda(ctx: SDSMContext, ensemble: int, start: float, finish: float, step: float) -> float:
    """Finds the best lambda for Box-Cox using Hinkley (1977) method. Mirrors VB."""
    best_lam = start
    min_abs_d = float('inf')

    k = start
    while k <= finish + 1e-9: # Add tolerance for float comparison
        temp_array = []
        # Box-Cox transform valid data points
        for i in range(ctx.no_of_days):
            val = ctx.data_array[ensemble][i]
            # VB check: <> GlobalMissingCode AND > LocalThresh AND <> 0
            # The condition for variance usually operates on values > threshold (conditional)
            # and if unconditional, on all non-missing values.
            # The Box-Cox itself is typically for positive data, so > local_thresh implicitly handles > 0 for precip.
            if val != GLOBAL_MISSING_CODE and val > ctx.local_thresh : # Ensure positive for log/power
                if abs(val) < 1e-9: # Skip actual zero values even if above a negative threshold
                    if ctx.local_thresh >= 0: continue # If threshold is non-negative, this implies val is zero, skip.
                                                      # If threshold is negative, a small positive val is fine.
                try:
                    if abs(k) < 1e-9: # Lambda is zero -> log transform
                        transformed_val = math.log(val)
                    else: # Standard Box-Cox
                        transformed_val = (val ** k - 1) / k
                    temp_array.append(transformed_val)
                except (ValueError, OverflowError): # Handle log(neg/zero) or power errors
                     continue

        count = len(temp_array)
        if count > 10: # Need enough points (VB used > 10)
            mean_val = sum(temp_array) / count
            temp_array.sort()
            median_val = statistics.median(temp_array)

            q1_idx = int(count * 0.25)
            q3_idx = int(count * 0.75)
            if q3_idx >= count: q3_idx = count -1 # Ensure valid index

            if q1_idx < q3_idx : # Ensure at least 2 distinct points for Q1 and Q3
                q1 = temp_array[q1_idx]
                q3 = temp_array[q3_idx]
                iqr = q3 - q1
            elif count > 0 :
                iqr = temp_array[-1] - temp_array[0] # Fallback for small N
                if count == 1: iqr = 0.0
            else:
                 iqr = 0.0

            d = GLOBAL_MISSING_CODE
            if abs(iqr) > 1e-9: # Avoid division by zero
                 d = (mean_val - median_val) / iqr

            if d != GLOBAL_MISSING_CODE:
                 abs_d = abs(d)
                 if abs_d < min_abs_d:
                     min_abs_d = abs_d
                     best_lam = k
        k += step
    if min_abs_d == float('inf'): return GLOBAL_MISSING_CODE
    return best_lam

def unbox_cox(value: float, lamda: float) -> float:
    """Inverse Box-Cox transform. Mirrors VB."""
    if value == GLOBAL_MISSING_CODE:
        return GLOBAL_MISSING_CODE
    try:
        if abs(lamda) < 1e-9: # Lambda is zero -> exp
            if value > 700: return float('inf')
            return math.exp(value)
        else: # Standard inverse Box-Cox
            base = (value * lamda) + 1
            if base < 0:
                 # Trying to take power of negative number, e.g. (-2)^0.5.
                 # This often happens if transformed values are pushed too far.
                 # Return missing or a very small positive number if contextually appropriate.
                 return GLOBAL_MISSING_CODE # Safest
            power = 1.0 / lamda
            # Potential for very large numbers if base > 1 and power is large positive,
            # or very small if base is small and power is large positive.
            # Or complex if base < 0 and power is fractional. Python handles base < 0 with fractional power if result is real.
            return base ** power
    except (ValueError, OverflowError):
        return GLOBAL_MISSING_CODE


def calc_variance_after_transform(ctx: SDSMContext, ensemble: int, trans_array, factor: float, mean_trans: float) -> float:
    """Helper for ApplyVariance: Applies factor to transformed data, untransforms, calculates variance. Mirrors VB."""
    temp_untransformed = []
    original_values_for_variance_calc = [] # Store original values that will be transformed

    # First, identify which original values contribute to trans_array
    # This is implicitly done by iterating through trans_array where it's not MISSING_CODE
    # and finding the corresponding original data_array value.

    for i in range(ctx.no_of_days): # Iterate through all days to match trans_array indexing
        if trans_array[i] != GLOBAL_MISSING_CODE: # This day was part of the transform
            # The original value that was transformed corresponds to ctx.data_array[ensemble][i]
            original_val = ctx.data_array[ensemble][i] # Keep for threshold check later

            try:
                val_trans_adjusted = ((trans_array[i] - mean_trans) * factor) + mean_trans
                val_untransformed = unbox_cox(val_trans_adjusted, ctx.lamda)

                if val_untransformed != GLOBAL_MISSING_CODE and val_untransformed != float('inf'):
                     # Conditional check: if original was > thresh, new must also be > thresh
                     if ctx.conditional_check and original_val > ctx.local_thresh:
                         if val_untransformed <= ctx.local_thresh:
                             temp_untransformed.append(ctx.local_thresh + 1e-6) # Clamp
                         else:
                             temp_untransformed.append(val_untransformed)
                     else: # Unconditional, or original was not > thresh (no clamping needed based on original state)
                        temp_untransformed.append(val_untransformed)
            except (ValueError, OverflowError):
                 continue

    count = len(temp_untransformed)
    if count > 1:
        mean_new = sum(temp_untransformed) / count
        variance = sum([(x - mean_new) ** 2 for x in temp_untransformed]) / count # Population variance
        return variance
    elif count == 1:
         return 0.0
    else:
        return GLOBAL_MISSING_CODE


def apply_variance(ctx: SDSMContext, progress_callback=None):
    """Apply a variance treatment. Handles conditional (Box-Cox) and unconditional."""
    if not ctx.mean_array or len(ctx.mean_array) != ctx.ensemble_size : # Check if calc_means was run for all
        QMessageBox.critical(None, "Error", "Mean/SD must be calculated for all ensembles before applying variance.")
        ctx.error_occurred = True
        return

    target_variance_ratio = ctx.variance_factor_percent # e.g., 1.10 for +10%
    if target_variance_ratio < 0:
        QMessageBox.critical(None, "Error", "Target variance factor results in a negative variance ratio, which is not possible.")
        ctx.error_occurred = True
        return


    for j in range(ctx.ensemble_size): # Loop through ensembles
        if ctx.global_kop_out: return
        if progress_callback:
             progress_callback(int(j / ctx.ensemble_size * 10), f"Applying Variance {j+1} Prep")

        mean_j = ctx.mean_array[j]['mean']
        sd_j = ctx.mean_array[j]['sd']

        if mean_j == GLOBAL_MISSING_CODE or sd_j == GLOBAL_MISSING_CODE:
            print(f"Warning: Ensemble {j+1} has missing mean/SD. Skipping variance adjustment.")
            continue

        original_variance = sd_j ** 2
        if original_variance < 1e-9: # Allow near-zero variance to be inflated if target_variance_ratio > 1
             if target_variance_ratio <= 1.0 : # Cannot reduce zero or near-zero variance further meaningfully
                print(f"Warning: Ensemble {j+1} has zero/near-zero initial variance. Skipping variance reduction.")
                continue
             # If inflating, original_variance might be problem if it's the denominator.
             # VB might use a small minimum for original_variance in ratio calculations.
             # For now, proceed if target_variance_ratio > 1, but be wary of division by original_variance if it's ~0.


        # --- Unconditional Process ---
        if not ctx.conditional_check:
            if abs(original_variance) < 1e-9 and target_variance_ratio > 1.0 :
                 # Inflating zero variance: this is tricky.
                 # (X - MeanX) is 0 for all X if variance is 0. So formula Y = MeanX.
                 # VB may have special handling. For now, skip if original_variance is zero.
                 print(f"Warning: Ensemble {j+1} (Unconditional) has zero variance. Cannot scale variance.")
                 continue

            scaling_factor = math.sqrt(target_variance_ratio) if target_variance_ratio >=0 else 0
            for i in range(ctx.no_of_days):
                val = ctx.data_array[j][i]
                if val != GLOBAL_MISSING_CODE:
                    # Apply scaling for all non-missing values
                    ctx.data_array[j][i] = ((val - mean_j) * scaling_factor) + mean_j
            if progress_callback: progress_callback(int((j+1) / ctx.ensemble_size * 100), f"Applying Variance {j+1} Complete")

        # --- Conditional Process (Box-Cox) ---
        else:
            # 1. Find optimal lambda
            if progress_callback: progress_callback(int(j / ctx.ensemble_size * 10) + 10, f"Variance {j+1} Finding Lambda")
            lamda = find_min_lambda(ctx, j, -2.0, 2.0, 0.25)
            if lamda != GLOBAL_MISSING_CODE:
                lamda = find_min_lambda(ctx, j, lamda - 0.25, lamda + 0.25, 0.1)
            if lamda != GLOBAL_MISSING_CODE:
                lamda = find_min_lambda(ctx, j, lamda - 0.1, lamda + 0.1, 0.01)

            if lamda == GLOBAL_MISSING_CODE:
                QMessageBox.warning(None, "Lambda Error", f"Ensemble {j+1}: Could not find suitable lambda for Box-Cox. Skipping variance adjustment for this ensemble.")
                continue

            ctx.lamda = lamda

            # 2. Transform the data (only values > threshold)
            trans_array = [GLOBAL_MISSING_CODE] * ctx.no_of_days
            valid_transformed_values = []
            num_values_for_transform = 0
            for i in range(ctx.no_of_days):
                val = ctx.data_array[j][i]
                if val != GLOBAL_MISSING_CODE and val > ctx.local_thresh: # Key conditional check
                    num_values_for_transform +=1
                    if abs(val) < 1e-9 and ctx.local_thresh >=0 : continue # Skip zero if non-negative threshold
                    try:
                        if abs(ctx.lamda) < 1e-9:
                            transformed_val = math.log(val)
                        else:
                            transformed_val = (val ** ctx.lamda - 1) / ctx.lamda
                        trans_array[i] = transformed_val
                        valid_transformed_values.append(transformed_val)
                    except (ValueError, OverflowError):
                        trans_array[i] = GLOBAL_MISSING_CODE
                # else: value is not > threshold or is missing, so trans_array[i] remains MISSING_CODE

            if not valid_transformed_values or len(valid_transformed_values) < 2: # Need at least 2 points for variance
                 print(f"Warning: Ensemble {j+1}: Insufficient valid values (> threshold) for Box-Cox transform or variance calculation. Skipping variance adjustment.")
                 continue

            mean_trans = sum(valid_transformed_values) / len(valid_transformed_values)

            # 3. Iteratively find scaling factor for transformed data
            if progress_callback: progress_callback(int(j / ctx.ensemble_size * 10) + 30, f"Variance {j+1} Finding Factor")

            # Original variance for conditional is based on values > threshold. Re-calculate if not already done by calc_means
            # calc_means already considers conditional_check, so original_variance is correct.
            if original_variance < 1e-9: # If variance of >thresh values is 0
                 if target_variance_ratio <= 1.0:
                    print(f"Warning: Ensemble {j+1} (Conditional) has zero variance for values > threshold. Skipping variance reduction.")
                    continue
                 # If inflating, this needs care. calc_variance_after_transform should handle.

            lower_f = 0.1  # Start with a wider range, especially if original_variance is small
            higher_f = 2.0
            if target_variance_ratio > 1.0: lower_f = 1.0; higher_f = 3.0 # Increased upper for expansion
            else: lower_f = 0.01; higher_f = 1.0

            best_factor = 1.0

            max_iter = 15 # VB used 10, more might be needed for stability
            for iter_num in range(max_iter):
                if ctx.global_kop_out: return
                if progress_callback:
                     prog = int(j / ctx.ensemble_size * 10) + 30 + int(iter_num/max_iter * 60)
                     progress_callback(prog, f"Variance {j+1} Iter {iter_num+1}")

                middle_f = (lower_f + higher_f) / 2.0
                if abs(middle_f) < 1e-9: middle_f = 1e-9 * (-1 if middle_f < 0 else 1) # Avoid zero factor but keep sign

                resulting_variance = calc_variance_after_transform(ctx, j, trans_array, middle_f, mean_trans)

                if resulting_variance == GLOBAL_MISSING_CODE:
                     print(f"Warning: Ensemble {j+1}, Iter {iter_num+1}: Could not calculate resulting variance. Factor search might be unstable.")
                     # Try to nudge factor based on direction: if middle_f was supposed to increase var, but failed, try smaller increase.
                     if target_variance_ratio > 1.0: higher_f = middle_f # Assume it overshot
                     else: lower_f = middle_f # Assume it overshot
                     if abs(higher_f - lower_f) < 1e-3 : break # Converged or stuck
                     continue


                current_variance_ratio = GLOBAL_MISSING_CODE
                if original_variance > 1e-9: # Avoid division by zero if original variance was tiny
                    current_variance_ratio = resulting_variance / original_variance
                elif resulting_variance > 1e-9: # Original variance was zero, but new one is not
                    current_variance_ratio = float('inf') # Effectively a large ratio
                else: # Both are zero
                    current_variance_ratio = 1.0 # No change from zero

                if current_variance_ratio < target_variance_ratio:
                    lower_f = middle_f
                else:
                    higher_f = middle_f

                best_factor = (lower_f + higher_f) / 2.0
                if abs(higher_f - lower_f) < 1e-4: break # Convergence


            # 4. Apply the best factor and untransform
            if progress_callback: progress_callback(int(j / ctx.ensemble_size * 10)+95, f"Variance {j+1} Applying Final")
            for i in range(ctx.no_of_days):
                original_val = ctx.data_array[j][i] # Get original value for conditional check context
                if trans_array[i] != GLOBAL_MISSING_CODE: # Was part of transform
                    try:
                        val_trans_adjusted = ((trans_array[i] - mean_trans) * best_factor) + mean_trans
                        val_untransformed = unbox_cox(val_trans_adjusted, ctx.lamda)

                        if val_untransformed != GLOBAL_MISSING_CODE and val_untransformed != float('inf'):
                            # Conditional check: if original was > thresh, new must also be > thresh
                            if original_val > ctx.local_thresh: # This implies conditional_check is true
                                if val_untransformed <= ctx.local_thresh:
                                    ctx.data_array[j][i] = ctx.local_thresh + 1e-6 # Clamp
                                else:
                                    ctx.data_array[j][i] = val_untransformed
                            # else: original_val was not > thresh. This state shouldn't occur if trans_array[i] is valid,
                            # as transform only happens for val > local_thresh.
                            # However, if it did, the untransformed value is applied directly.
                            # This path (original_val <= local_thresh but trans_array[i] not missing)
                            # should ideally not be reached if logic is perfectly aligned.
                            # If it means original_val was modified by previous steps like amount,
                            # then the clamping is based on the *new* value vs threshold.
                            # The most robust is just to check the new untransformed value if conditional.
                            # if ctx.conditional_check and val_untransformed <= ctx.local_thresh and original_val > ctx.local_thresh:
                            #    ctx.data_array[j][i] = ctx.local_thresh + 1e-6
                            # else:
                            #    ctx.data_array[j][i] = val_untransformed
                        # else: untransform failed, leave original value data_array[j][i]
                    except (ValueError, OverflowError):
                         pass # Keep original ctx.data_array[j][i]

    if progress_callback: progress_callback(100, "Applying Variance Complete")


def apply_trend(ctx: SDSMContext, progress_callback=None):
    """Apply Linear, Exponential, or Logistic trend."""
    if not ctx.trend_check: return

    for j in range(ctx.ensemble_size): # Loop ensembles
        if ctx.global_kop_out: return
        if progress_callback:
             progress_callback(int(j / ctx.ensemble_size * 100), f"Applying Trend {j+1}")

        # --- Linear Trend ---
        if ctx.trend_option == 0:
            if abs(ctx.linear_trend) < 1e-9: continue # Skip if zero trend
            days_per_year = 365.25 if ctx.year_indicator == 366 else float(ctx.year_indicator) # year_indicator=366 implies calendar with leap
            if days_per_year == 0: days_per_year = 365.25 # Avoid division by zero

            increment_per_day = ctx.linear_trend / days_per_year
            increment_multiplier_per_day_percent = ctx.linear_trend / days_per_year # For conditional, it's a % of value

            for i in range(ctx.no_of_days):
                val = ctx.data_array[j][i]
                if val != GLOBAL_MISSING_CODE:
                    day_index_from_start = i # 0-based index for time progression

                    if not ctx.conditional_check: # Unconditional: Add trend
                         trend_effect = increment_per_day * day_index_from_start
                         ctx.data_array[j][i] = val + trend_effect
                    else: # Conditional: Multiply by trend factor if > threshold
                        if val > ctx.local_thresh:
                            # VB's "LinearTrend / (YearIndicator * 100)" for conditional suggests LinearTrend is a percentage.
                            # If LinearTrend input is absolute units/year, then for conditional % change:
                            # % change for the day = (increment_per_day_absolute / original_value_representative_for_day) * 100
                            # Or, simpler, the daily increment (absolute) is scaled by (value / mean_of_series) for magnitude effect.
                            # The VB code seems to treat LinearTrend as a % value for conditional directly.
                            # Let's assume LinearTrend input itself is a % for conditional.
                            # So, daily_percentage_increment = (LinearTrend_as_percent / days_per_year)
                            # Multiplier = 1 + (daily_percentage_increment / 100) * day_index
                            # Multiplier = 1 + ( (LinearTrend_input / 100) / days_per_year ) * day_index
                            # VB actually used: Multiplier = 1 + (LinearTrend / (YearIndicator * 100)) * DayNo
                            # This implies LinearTrend is an annual percentage.
                            trend_multiplier_increment = (ctx.linear_trend / (days_per_year * 100.0)) * day_index_from_start
                            trend_multiplier = 1.0 + trend_multiplier_increment

                            new_val = val * trend_multiplier
                            if new_val <= ctx.local_thresh: # Clamp
                                ctx.data_array[j][i] = ctx.local_thresh + 1e-6
                            else:
                                ctx.data_array[j][i] = new_val

        # --- Exponential Trend ---
        elif ctx.trend_option == 1:
            exp_trend_factor_input = ctx.exp_trend # This is the target cumulative multiplier by end of series.
            if abs(exp_trend_factor_input - 1.0) < 1e-9 and not ctx.conditional_check : continue # Factor is 1, no change for unconditional
            if abs(exp_trend_factor_input) < 1e-9 and ctx.conditional_check: continue # Additive % is 0 for conditional

            # For UNCONDITIONAL: V_new = V_orig * (Factor_at_time_t)
            # Factor_at_time_t = Initial_Factor ^ (t / T) where Initial_Factor = exp_trend_factor_input
            # Or, if exp_trend_factor_input is additive (VB ExpTrend seems to be additive for conditional):
            # V_new = V_orig + TrendEffect. TrendEffect = (Exp( (i / ExpAValue) ) - 1) * SignOfExpTrendInput
            # ExpAValue = NoOfDays / (Log(Abs(ExpTrendInput) + 1))
            # This implies ExpTrendInput is an additive percentage like 50 (for 50%)

            # Let's follow VB conditional logic structure for ExpTrend meaning "additive percentage by end of series"
            # And for unconditional, it might be a multiplicative factor. The code seems to use same TrendEffect calculation.

            # VB's `ExpTrend` seems to be a percentage value (e.g., 50 for 50% change by end of series)
            # `add_exp` flag indicates if this % is additive or subtractive.
            # `ExpTrendAbs` in VB seems to be `Abs(frmScenarioGenerator.ExpTrend.Text)`
            # `Log(ExpTrendAbs + 1)` in VB. If ExpTrend is 50(%), this is Log(51).
            # This `TrendEffect` is then added/subtracted (unconditional) or used in multiplier (conditional)

            exp_input_val = ctx.exp_trend # User input, e.g. 50 for +50% or -50 for -50%
            if abs(exp_input_val) < 1e-9: continue

            add_effect = exp_input_val > 0
            exp_param_abs = abs(exp_input_val / 100.0) # Convert to fraction, e.g., 0.5 for 50%

            try:
                # Log argument must be > 0.  (exp_param_abs + 1.0) is always > 0.
                log_arg = exp_param_abs + 1.0
                if ctx.no_of_days <=0: continue
                exp_a_value = ctx.no_of_days / math.log(log_arg)
                if abs(exp_a_value) < 1e-9: continue
            except (ValueError, OverflowError): continue

            for i in range(ctx.no_of_days):
                val = ctx.data_array[j][i]
                if val != GLOBAL_MISSING_CODE:
                    day_idx = i # 0-based
                    try:
                        exponent = day_idx / exp_a_value
                        if exponent > 700: trend_effect_magnitude = float('inf')
                        elif exponent < -700: trend_effect_magnitude = 0 # exp(-large) -> 0, so (0-1) = -1
                        else: trend_effect_magnitude = math.exp(exponent) - 1.0
                        if trend_effect_magnitude == float('inf'): continue
                    except (ValueError, OverflowError): continue

                    # This trend_effect_magnitude is a fractional change relative to initial state,
                    # scaled by exp_input_val implicitly through exp_a_value.
                    # The VB code applies `TrendEffect` calculated this way.
                    # If `exp_input_val` was +50, `trend_effect_magnitude` grows towards `exp_param_abs` (0.5).
                    # So, the `trend_effect_magnitude` itself IS the fractional change.

                    if not ctx.conditional_check: # Unconditional: V_new = V_orig * (1 +/- trend_effect_magnitude)
                        # Or is it V_new = V_orig + (V_orig_mean_or_typical * trend_effect_magnitude)?
                        # VB: If AddExp then Value = Value + TrendEffect. This suggests TrendEffect is absolute.
                        # However, TrendEffect from Exp((i/ExpAValue))-1 is fractional.
                        # If ExpTrend is 50(%), TrendEffect grows towards 0.5.
                        # If Value=10, new Value = 10 + 0.5 = 10.5. (small change)
                        # If TrendEffect is meant to be scaled by the value itself for unconditional too:
                        # Value = Value * (1 + TrendEffect if AddExp else 1 - TrendEffect)
                        # This seems more logical for an "exponential" trend.
                        # Let's assume unconditional trend is also multiplicative by (1 + scaled_effect)
                        # where scaled_effect is trend_effect_magnitude * (sign of exp_input_val).
                        # The VB conditional logic: `ExpMultiplier = (100 +/- TrendEffect) / 100` where TrendEffect is `Abs(TrendEffect)`
                        # and +/- depends on `AddExp`. This makes `TrendEffect` itself `Exp((i/A))-1`.
                        # So for conditional, if TrendEffect = 0.2, multiplier is 1.2 or 0.8.
                        # Let's use a consistent interpretation: trend_effect_magnitude is the fractional change.
                        # This means `TrendEffect` in VB was likely the fractional change to be applied.

                        current_fractional_change = trend_effect_magnitude
                        if add_effect:
                            ctx.data_array[j][i] = val * (1 + current_fractional_change)
                        else:
                            ctx.data_array[j][i] = val * (1 - current_fractional_change)

                    else: # Conditional: apply if val > thresh
                        if val > ctx.local_thresh:
                            current_fractional_change = trend_effect_magnitude # Already scaled by ExpAValue
                            if add_effect:
                                trend_multiplier = 1.0 + current_fractional_change
                            else:
                                trend_multiplier = 1.0 - current_fractional_change

                            if trend_multiplier < 0: trend_multiplier = 0 # Avoid negative results for positive data
                            new_val = val * trend_multiplier
                            if new_val <= ctx.local_thresh:
                                ctx.data_array[j][i] = ctx.local_thresh + 1e-6
                            else:
                                ctx.data_array[j][i] = new_val

        # --- Logistic Trend ---
        elif ctx.trend_option == 2:
            logistic_input_val = ctx.logistic_trend # e.g. 10 for +10 units by end, or 10 for +10% by end for conditional
            if abs(logistic_input_val) < 1e-9: continue

            for i in range(ctx.no_of_days):
                 val = ctx.data_array[j][i]
                 if val != GLOBAL_MISSING_CODE:
                    if ctx.no_of_days > 1:
                        x_mapping = ((i / (ctx.no_of_days - 1)) * 12.0) - 6.0 # Scale i to [-6, 6]
                    else: x_mapping = 0.0

                    try:
                        sigmoid_factor = 1.0 / (1.0 + math.exp(-x_mapping)) # Sigmoid output [0, 1]
                    except OverflowError: # x_mapping is very large negative
                         sigmoid_factor = 0.0

                    # `logistic_input_val` is the total change desired by end of series.
                    # `sigmoid_factor` scales this change over time.
                    trend_effect_absolute = logistic_input_val * sigmoid_factor

                    if not ctx.conditional_check: # Unconditional: Add absolute trend effect
                        ctx.data_array[j][i] = val + trend_effect_absolute
                    else: # Conditional: Multiply by factor related to trend effect
                        if val > ctx.local_thresh:
                            # VB: Multiplier = (100 + IncrementValue) / 100. IncrementValue is LogisticTrend * SigmoidFactor
                            # This implies LogisticTrend is an input percentage for conditional.
                            # So, trend_effect_percentage_points = logistic_input_val * sigmoid_factor
                            # trend_multiplier = 1.0 + (trend_effect_percentage_points / 100.0)
                            trend_multiplier = 1.0 + ( (logistic_input_val * sigmoid_factor) / 100.0 )


                            if trend_multiplier < 0: trend_multiplier = 0
                            new_val = val * trend_multiplier
                            if new_val <= ctx.local_thresh:
                                ctx.data_array[j][i] = ctx.local_thresh + 1e-6
                            else:
                                ctx.data_array[j][i] = new_val
    if progress_callback: progress_callback(100, "Applying Trend Complete")


def write_output_file(ctx: SDSMContext, progress_callback=None):
    """Writes the modified data_array to the output file."""
    try:
        with open(ctx.out_root, "w") as f:
            for i in range(ctx.no_of_days):
                if ctx.global_kop_out: return False # Check for user cancel
                if progress_callback:
                    progress_callback(int(i / ctx.no_of_days * 100), "Writing Output File")

                line_parts = [format_value_output(ctx.data_array[j][i]) for j in range(ctx.ensemble_size)]
                f.write("".join(line_parts).rstrip('\t') + "\n") # Rstrip to remove last tab

    except Exception as e:
        QMessageBox.critical(None, "File Write Error", f"Error writing output file:\n{e}")
        ctx.error_occurred = True
        return False

    if progress_callback: progress_callback(100, "Writing Output Complete")
    return True

# --- .PAR file function (keeping minimal functionality needed) ---
def parse_par_file(par_path: str, ctx: SDSMContext):
    lines = []
    try:
        with open(par_path, "r") as f:
            raw_lines = f.readlines()
        # Filter empty lines and strip whitespace
        lines = [line.strip() for line in raw_lines if line.strip()]
        if not lines: return False # Empty file

        idx = 0
        # Helper to safely get next line
        def get_line(current_idx):
            if current_idx < len(lines):
                return lines[current_idx], current_idx + 1
            raise IndexError("Unexpected end of PAR file.")

        line, idx = get_line(idx); ctx.num_predictors = int(line)
        line, idx = get_line(idx); ctx.num_months = int(line) # Should be 12
        line, idx = get_line(idx); ctx.year_length = int(line)
        ctx.year_indicator = ctx.year_length
        line, idx = get_line(idx); start_date_str = line
        try:
            ctx.start_date = datetime.datetime.strptime(start_date_str, "%d/%m/%Y").date()
        except ValueError: # Try another common format if first fails
            ctx.start_date = datetime.datetime.strptime(start_date_str, "%m/%d/%Y").date()

        line, idx = get_line(idx); ctx.no_of_days = int(line)

        # Skip potential duplicate date/days if present (robust check)
        if idx < len(lines) and lines[idx] == start_date_str: idx += 1
        if idx < len(lines) and lines[idx].isdigit() and int(lines[idx]) == ctx.no_of_days: idx +=1

        line, idx = get_line(idx); cond_str = line
        ctx.conditional_check = (cond_str.upper() == "#TRUE#")
        line, idx = get_line(idx); ensemble_str = line
        ctx.ensemble_size = int(ensemble_str)

        # Skip variance factor percent, transform code, bias correction from PAR as they are not directly used
        # or are set by user in this tool.
        idx += 3 # Skip 3 lines (VarPerc, Transform, BiasCorrection)

        # Read Predictor Files (relative paths)
        ctx.predictor_files = []
        par_dir = os.path.dirname(par_path)
        for _ in range(ctx.num_predictors):
            if idx >= len(lines): break # Should not happen if PAR is well-formed
            line, idx = get_line(idx); pfile = line
            abs_pfile = os.path.normpath(os.path.join(par_dir, pfile))
            ctx.predictor_files.append(abs_pfile)

        # Read Data File (relative path) - this is the observed data for SDSM model calibration,
        # for Scenario Generator, this becomes the InFile if not overridden.
        if idx < len(lines):
            line, idx = get_line(idx); data_file = line
            # Check if it's a coefficient line or the data file name
            if ' ' not in data_file and ('.' in data_file or os.sep in data_file or os.altsep in data_file): # Heuristic for filename
                abs_data_file = os.path.normpath(os.path.join(par_dir, data_file))
                ctx.in_file = os.path.basename(abs_data_file) # Store filename part
                ctx.in_root = abs_data_file # Store full path
            else: # Line was not a filename, likely start of coeffs, so put it back conceptually
                idx -=1


        # Read Monthly Coefficients (if present)
        ctx.monthly_coeffs = []
        coeffs_found = False
        while idx < len(lines):
            line, current_idx_plus_1 = get_line(idx)
            parts = line.split()
            try:
                # Ensure all parts are numbers and count matches num_predictors + intercept
                coeffs = [float(x) for x in parts]
                if len(coeffs) == ctx.num_predictors + 1: # Intercept + N predictors
                    ctx.monthly_coeffs.append(coeffs)
                    coeffs_found = True
                    idx = current_idx_plus_1
                else: # Does not look like a coefficient line
                    break
            except ValueError: # Not a float, so not a coefficient line
                 break # Stop trying to read coefficients

        if coeffs_found:
            print(f"Read {len(ctx.monthly_coeffs)} lines of monthly coefficients from PAR file.")
        return True

    except Exception as e:
        QMessageBox.critical(None, "Error", f"Error parsing .PAR file '{os.path.basename(par_path)}':\n{e}\nApproximate line number/block: {idx+1}")
        return False


# --- Stylesheet ---
STYLESHEET = """
    QWidget {
        font-family: 'Segoe UI', 'Helvetica Neue', 'Arial', sans-serif;
        font-size: 9pt; /* Adjusted base font size */
    }
    QGroupBox {
        font-weight: bold;
        font-size: 10pt; /* Slightly larger for group titles */
        border: 1px solid #B0B0B0;
        border-radius: 6px;
        margin-top: 0.6em;
        padding: 10px 5px 5px 5px; /* top, right, bottom, left for content inside groupbox */
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 5px 0 5px;
        left: 10px;
        color: #222222;
    }
    QPushButton {
        background-color: #E8E8E8;
        border: 1px solid #A0A0A0;
        padding: 6px 12px;
        border-radius: 4px;
        min-width: 70px; /* Adjusted min-width */
    }
    QPushButton:hover {
        background-color: #D8D8D8;
        border-color: #909090;
    }
    QPushButton:pressed {
        background-color: #C8C8C8;
    }
    QPushButton#GenerateButton {
        background-color: #4CAF50; /* Green */
        color: white;
        font-weight: bold;
        padding: 7px 15px; /* Slightly larger */
    }
    QPushButton#GenerateButton:hover {
        background-color: #45a049;
    }
    QPushButton#GenerateButton:pressed {
        background-color: #3E8E41;
    }
    QLineEdit {
        padding: 5px;
        border: 1px solid #C0C0C0;
        border-radius: 4px;
        background-color: white; /* Ensure background is white */
    }
    QLineEdit:focus {
        border-color: #0078D7; /* Blue focus border */
    }
    QLabel#FileLabel {
        font-style: italic;
        color: #444444;
        padding: 6px;
        border: 1px dashed #C0C0C0;
        border-radius: 4px;
        background-color: #F5F5F5;
        min-height: 1.5em; /* Ensure it has some height */
    }
    QCheckBox, QRadioButton {
        spacing: 5px; /* Space between checkbox/radio and its text */
        padding: 2px 0; /* Add some vertical padding */
    }
    QProgressBar {
        border: 1px solid #A0A0A0;
        border-radius: 4px;
        text-align: center;
        height: 20px;
        font-weight: bold;
        color: #333;
    }
    QProgressBar::chunk {
        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #66BB6A, stop:1 #4CAF50);
        border-radius: 3px;
        margin: 1px;
    }
    /* Styling for input fields in treatment rows for consistent width */
    QLineEdit#TreatmentInput {
        min-width: 80px; /* Minimum width for these inputs */
        max-width: 120px; /* Maximum width to prevent excessive stretching */
    }
"""

###############################################################################
# 4. PyQt5 User Interface (ScenarioGeneratorWidget)
###############################################################################
class ScenarioGeneratorWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.ctx = SDSMContext()
        self._init_ui()
        self.reset_ui_and_context()

    def _init_ui(self):
        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(12, 12, 12, 12)
        mainLayout.setSpacing(10)

        # --- File Selection ---
        fileGroup = QGroupBox("Files")
        fileLayout = QGridLayout()
        fileLayout.setSpacing(8)
        self.inputFileButton = QPushButton(self.style().standardIcon(QStyle.SP_DirOpenIcon), " Input File")
        self.inputFileLabel = QLabel("No file selected")
        self.inputFileLabel.setObjectName("FileLabel")
        self.inputFileLabel.setWordWrap(True)
        self.outputFileButton = QPushButton(self.style().standardIcon(QStyle.SP_FileDialogNewFolder), " Output File") # Changed icon
        self.outputFileLabel = QLabel("No file selected")
        self.outputFileLabel.setObjectName("FileLabel")
        self.outputFileLabel.setWordWrap(True)
        fileLayout.addWidget(self.inputFileButton, 0, 0)
        fileLayout.addWidget(self.inputFileLabel, 0, 1)
        fileLayout.addWidget(self.outputFileButton, 1, 0)
        fileLayout.addWidget(self.outputFileLabel, 1, 1)
        fileLayout.setColumnStretch(1, 1)
        fileGroup.setLayout(fileLayout)
        mainLayout.addWidget(fileGroup)

        # --- General Parameters ---
        generalGroup = QGroupBox("General Settings")
        generalLayout = QGridLayout()
        generalLayout.setSpacing(8)
        self.startDateInput = QLineEdit()
        self.ensembleSizeInput = QLineEdit()
        self.conditionalCheck = QCheckBox("Conditional Process")
        self.thresholdInput = QLineEdit()
        generalLayout.addWidget(QLabel("Start Date (DD/MM/YY):"), 0, 0)
        generalLayout.addWidget(self.startDateInput, 0, 1)
        generalLayout.addWidget(QLabel("Ensemble Size:"), 0, 2)
        generalLayout.addWidget(self.ensembleSizeInput, 0, 3)
        generalLayout.addWidget(self.conditionalCheck, 1, 0, 1, 2)
        generalLayout.addWidget(QLabel("Threshold:"), 1, 2)
        generalLayout.addWidget(self.thresholdInput, 1, 3)
        generalLayout.setColumnStretch(1,1) # Allow input fields to stretch a bit
        generalLayout.setColumnStretch(3,1)
        generalGroup.setLayout(generalLayout)
        mainLayout.addWidget(generalGroup)

        # --- Treatments ---
        treatmentsGroup = QGroupBox("Treatments")
        treatmentsLayout = QGridLayout() # Main grid for treatments
        treatmentsLayout.setSpacing(10) # Spacing between treatment rows
        treatmentsLayout.setColumnStretch(1, 1) # Allow controls column to stretch

        # Helper for consistent input field styling in treatments
        def create_treatment_input(placeholder=""):
            edit = QLineEdit()
            edit.setPlaceholderText(placeholder)
            edit.setObjectName("TreatmentInput")
            return edit

        # Occurrence Row
        self.occurrenceCheck = QCheckBox("Occurrence")
        self.occFactorInput = create_treatment_input("% change")
        self.occOptionGroup = QButtonGroup(self)
        self.occFactorRadio = QRadioButton("Factor")
        self.occForcedRadio = QRadioButton("Forced")
        self.occOptionGroup.addButton(self.occFactorRadio, 0)
        self.occOptionGroup.addButton(self.occForcedRadio, 1)
        self.preserveTotalsCheck = QCheckBox("Preserve Totals")

        occControlsLayout = QHBoxLayout()
        occControlsLayout.setContentsMargins(0,0,0,0); occControlsLayout.setSpacing(5)
        occControlsLayout.addWidget(QLabel("Factor (%):"))
        occControlsLayout.addWidget(self.occFactorInput)
        occControlsLayout.addSpacing(10)
        occControlsLayout.addWidget(self.occFactorRadio)
        occControlsLayout.addWidget(self.occForcedRadio)
        occControlsLayout.addSpacing(10)
        occControlsLayout.addWidget(self.preserveTotalsCheck)
        occControlsLayout.addStretch(1)
        treatmentsLayout.addWidget(self.occurrenceCheck, 0, 0, Qt.AlignTop)
        treatmentsLayout.addLayout(occControlsLayout, 0, 1)

        # Amount Row
        self.amountCheck = QCheckBox("Amount")
        self.amountOptionGroup = QButtonGroup(self)
        self.amountFactorRadio = QRadioButton("Factor:")
        self.amountFactorInput = create_treatment_input("% change")
        self.amountAddRadio = QRadioButton("Addition:")
        self.amountAddInput = create_treatment_input("value")
        self.amountOptionGroup.addButton(self.amountFactorRadio, 0)
        self.amountOptionGroup.addButton(self.amountAddRadio, 1)

        amountControlsLayout = QHBoxLayout()
        amountControlsLayout.setContentsMargins(0,0,0,0); amountControlsLayout.setSpacing(5)
        amountControlsLayout.addWidget(self.amountFactorRadio)
        amountControlsLayout.addWidget(self.amountFactorInput)
        amountControlsLayout.addSpacing(15)
        amountControlsLayout.addWidget(self.amountAddRadio)
        amountControlsLayout.addWidget(self.amountAddInput)
        amountControlsLayout.addStretch(1)
        treatmentsLayout.addWidget(self.amountCheck, 1, 0, Qt.AlignTop)
        treatmentsLayout.addLayout(amountControlsLayout, 1, 1)

        # Variance Row
        self.varianceCheck = QCheckBox("Variance")
        self.varianceFactorInput = create_treatment_input("% change")
        varianceControlsLayout = QHBoxLayout()
        varianceControlsLayout.setContentsMargins(0,0,0,0); varianceControlsLayout.setSpacing(5)
        varianceControlsLayout.addWidget(QLabel("Factor (%):"))
        varianceControlsLayout.addWidget(self.varianceFactorInput)
        varianceControlsLayout.addStretch(1)
        treatmentsLayout.addWidget(self.varianceCheck, 2, 0, Qt.AlignTop)
        treatmentsLayout.addLayout(varianceControlsLayout, 2, 1)

        # Trend Section
        self.trendCheck = QCheckBox("Trend")
        self.trendOptionGroup = QButtonGroup(self)
        # Linear
        self.trendLinearRadio = QRadioButton("Linear:")
        self.trendLinearInput = create_treatment_input("/year value")
        self.trendOptionGroup.addButton(self.trendLinearRadio, 0)
        trendLinLayout=QHBoxLayout(); trendLinLayout.setContentsMargins(0,0,0,0); trendLinLayout.setSpacing(5)
        trendLinLayout.addWidget(self.trendLinearRadio); trendLinLayout.addWidget(self.trendLinearInput); trendLinLayout.addStretch(1)
        # Exponential
        self.trendExpRadio = QRadioButton("Exponential:")
        self.trendExpInput = create_treatment_input("factor")
        self.trendOptionGroup.addButton(self.trendExpRadio, 1)
        trendExpLayout=QHBoxLayout(); trendExpLayout.setContentsMargins(0,0,0,0); trendExpLayout.setSpacing(5)
        trendExpLayout.addWidget(self.trendExpRadio); trendExpLayout.addWidget(self.trendExpInput); trendExpLayout.addStretch(1)
        # Logistic
        self.trendLogRadio = QRadioButton("Logistic:")
        self.trendLogInput = create_treatment_input("factor")
        self.trendOptionGroup.addButton(self.trendLogRadio, 2)
        trendLogLayout=QHBoxLayout(); trendLogLayout.setContentsMargins(0,0,0,0); trendLogLayout.setSpacing(5)
        trendLogLayout.addWidget(self.trendLogRadio); trendLogLayout.addWidget(self.trendLogInput); trendLogLayout.addStretch(1)

        # Container for all trend options
        trendOptionsContainer = QVBoxLayout()
        trendOptionsContainer.setContentsMargins(0,0,0,0); trendOptionsContainer.setSpacing(4)
        trendOptionsContainer.addLayout(trendLinLayout)
        trendOptionsContainer.addLayout(trendExpLayout)
        trendOptionsContainer.addLayout(trendLogLayout)

        treatmentsLayout.addWidget(self.trendCheck, 3, 0, Qt.AlignTop)
        treatmentsLayout.addLayout(trendOptionsContainer, 3, 1) # All trend options in one cell, stacked vertically
        treatmentsGroup.setLayout(treatmentsLayout)
        mainLayout.addWidget(treatmentsGroup)

        # --- Progress Bar ---
        self.progressBar = QProgressBar()
        self.progressBar.setVisible(False)
        self.progressLabel = QLabel("")
        self.progressLabel.setVisible(False)
        self.progressLabel.setAlignment(Qt.AlignCenter)
        progressLayout = QVBoxLayout() # Changed to QVBoxLayout for label above bar
        progressLayout.setContentsMargins(0,5,0,0)
        progressLayout.addWidget(self.progressLabel)
        progressLayout.addWidget(self.progressBar)
        mainLayout.addLayout(progressLayout)

        # --- Buttons ---
        buttonLayout = QHBoxLayout()
        self.generateButton = QPushButton("Generate Scenario")
        self.generateButton.setObjectName("GenerateButton") # For specific styling
        self.resetButton = QPushButton("Reset Form")
        buttonLayout.addStretch(1)
        buttonLayout.addWidget(self.resetButton)
        buttonLayout.addWidget(self.generateButton)
        mainLayout.addLayout(buttonLayout)

        mainLayout.addStretch(1) # Push content upwards

        self._add_tooltips()
        self._connect_signals()


    def _add_tooltips(self):
        self.inputFileButton.setToolTip("Load parameters from a .PAR file or raw data from .txt/.dat/.csv")
        self.outputFileButton.setToolTip("Specify the output file name for the generated scenario (e.g., scenario.out)")
        self.startDateInput.setToolTip("Start date of the input data series (DD/MM/YYYY)")
        self.ensembleSizeInput.setToolTip("Number of ensemble members (columns) in the input data (1-100)")
        self.conditionalCheck.setToolTip("If checked, Amount, Variance, and Trend treatments only apply to values above the Threshold.\nOccurrence treatment ALWAYS requires this to be checked.")
        self.thresholdInput.setToolTip("Threshold value for conditional processing (e.g., precipitation threshold like 0.1)")

        self.occurrenceCheck.setToolTip("Modify the frequency of wet/dry days (Conditional Process must be checked)")
        self.occFactorInput.setToolTip("Percentage change for 'Factor' occurrence modification (e.g., 5 for +5%, -10 for -10%) [-99 to 100]")
        self.occFactorRadio.setToolTip("Stochastic adjustment of wet/dry days based on the factor")
        self.occForcedRadio.setToolTip("Adjust wet/dry days to meet a forced monthly percentage (ZoM data not loaded via UI)")
        self.preserveTotalsCheck.setToolTip("If checked, scale rainfall amounts after occurrence changes to attempt to preserve original total rainfall")

        self.amountCheck.setToolTip("Modify the magnitude of data values")
        self.amountFactorInput.setToolTip("Percentage change for 'Factor' amount modification (e.g., 10 for +10%) [-100 to 100]")
        self.amountAddInput.setToolTip("Value to add for 'Addition' amount modification [-100 to 100]")

        self.varianceCheck.setToolTip("Modify the variance of the data")
        self.varianceFactorInput.setToolTip("Percentage change in variance (e.g., 20 for +20% variance). Must result in non-negative variance ratio.")

        self.trendCheck.setToolTip("Apply a trend to the data")
        self.trendLinearInput.setToolTip("Linear trend value per year (e.g., 0.1 for +0.1 units/year) [-100 to 100]")
        self.trendExpInput.setToolTip("Exponential trend factor (e.g., 50 for +50% change by end of series, cannot be 0). Affects rate of change.")
        self.trendLogInput.setToolTip("Logistic trend factor (e.g., 10 for +10 units change by end of series) [-100 to 100].")

        self.generateButton.setToolTip("Start the scenario generation process with the current settings")
        self.resetButton.setToolTip("Reset all form fields to their default values")

    def _connect_signals(self):
        self.inputFileButton.clicked.connect(self.select_input_file)
        self.outputFileButton.clicked.connect(self.select_output_file)
        self.generateButton.clicked.connect(self.run_generation)
        self.resetButton.clicked.connect(self.reset_ui_and_context)

        self.startDateInput.editingFinished.connect(self.validate_start_date)
        self.ensembleSizeInput.editingFinished.connect(self.validate_ensemble_size)
        self.thresholdInput.editingFinished.connect(self.validate_threshold)
        self.occFactorInput.editingFinished.connect(self.validate_occurrence)
        self.amountFactorInput.editingFinished.connect(self.validate_amount)
        self.amountAddInput.editingFinished.connect(self.validate_amount)
        self.varianceFactorInput.editingFinished.connect(self.validate_variance)
        self.trendLinearInput.editingFinished.connect(self.validate_trend)
        self.trendExpInput.editingFinished.connect(self.validate_trend)
        self.trendLogInput.editingFinished.connect(self.validate_trend)

        self.conditionalCheck.toggled.connect(lambda checked: setattr(self.ctx, 'conditional_check', checked))
        self.occurrenceCheck.toggled.connect(lambda checked: setattr(self.ctx, 'occurrence_check', checked))
        self.preserveTotalsCheck.toggled.connect(lambda checked: setattr(self.ctx, 'preserve_totals_check', checked))
        self.amountCheck.toggled.connect(lambda checked: setattr(self.ctx, 'amount_check', checked))
        self.varianceCheck.toggled.connect(lambda checked: setattr(self.ctx, 'variance_check', checked))
        self.trendCheck.toggled.connect(lambda checked: setattr(self.ctx, 'trend_check', checked))

        self.occOptionGroup.buttonClicked[int].connect(lambda id: setattr(self.ctx, 'occurrence_option', id))
        self.amountOptionGroup.buttonClicked[int].connect(lambda id: setattr(self.ctx, 'amount_option', id))
        self.trendOptionGroup.buttonClicked[int].connect(lambda id: setattr(self.ctx, 'trend_option', id))


    # --- UI Action Methods (reset_ui_and_context, select_input_file, etc.) ---
    # --- These methods remain largely the same as in your original code ---
    # --- Make sure to include them in your final script. ---
    # --- For brevity, I'm only showing the modified _init_ui, _add_tooltips, _connect_signals ---

    def reset_ui_and_context(self):
        """Resets both the UI fields and the context object to defaults."""
        self.ctx.reset()

        self.inputFileLabel.setText("No file selected")
        self.outputFileLabel.setText("No file selected")

        self.startDateInput.setText(self.ctx.start_date.strftime("%d/%m/%Y"))
        self.ensembleSizeInput.setText(str(self.ctx.ensemble_size))
        self.conditionalCheck.setChecked(self.ctx.conditional_check)
        self.thresholdInput.setText(str(self.ctx.local_thresh))

        self.occurrenceCheck.setChecked(self.ctx.occurrence_check)
        self.occFactorInput.setText(str(self.ctx.occurrence_factor))
        self.occFactorRadio.setChecked(self.ctx.occurrence_option == 0)
        self.occForcedRadio.setChecked(self.ctx.occurrence_option == 1)
        self.preserveTotalsCheck.setChecked(self.ctx.preserve_totals_check)

        self.amountCheck.setChecked(self.ctx.amount_check)
        self.amountFactorRadio.setChecked(self.ctx.amount_option == 0)
        self.amountFactorInput.setText(str(self.ctx.amount_factor))
        self.amountAddRadio.setChecked(self.ctx.amount_option == 1)
        self.amountAddInput.setText(str(self.ctx.amount_addition))

        self.varianceCheck.setChecked(self.ctx.variance_check)
        self.varianceFactorInput.setText(str(self.ctx.variance_factor))

        self.trendCheck.setChecked(self.ctx.trend_check)
        self.trendLinearRadio.setChecked(self.ctx.trend_option == 0)
        self.trendLinearInput.setText(str(self.ctx.linear_trend))
        self.trendExpRadio.setChecked(self.ctx.trend_option == 1)
        self.trendExpInput.setText(str(self.ctx.exp_trend)) # Default was 1, so 1.0
        self.trendLogRadio.setChecked(self.ctx.trend_option == 2)
        self.trendLogInput.setText(str(self.ctx.logistic_trend)) # Default was 1, so 1.0


        self.progressBar.setVisible(False)
        self.progressLabel.setVisible(False)
        self.progressBar.setValue(0)
        self.progressLabel.setText("")


    def select_input_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Input File", "", "PAR Files (*.par);;Data Files (*.txt *.dat *.csv);;All Files (*.*)")
        if file_path:
            self.ctx.in_root = file_path
            self.ctx.in_file = os.path.basename(file_path)
            self.inputFileLabel.setText(f"{self.ctx.in_file} ({os.path.dirname(file_path)})") # Show path too

            if file_path.lower().endswith(".par"):
                if parse_par_file(file_path, self.ctx):
                    QMessageBox.information(self, "PAR Parsed", f"Loaded settings from {os.path.basename(file_path)}.\nInput data file from PAR: {self.ctx.in_file if self.ctx.in_file else 'Not specified in PAR'}")
                    self.update_ui_from_context()
                else:
                    self.ctx.in_root = ""
                    self.ctx.in_file = ""
                    self.inputFileLabel.setText("No file selected")

    def select_output_file(self):
        default_name = ""
        if self.ctx.in_file: # If input file is loaded
            base, ext = os.path.splitext(self.ctx.in_file)
            default_name = base + "_scenario.out"
        else: # Generic default
            default_name = "scenario_output.out"

        # Try to get directory of input file if available
        initial_dir = os.path.dirname(self.ctx.in_root) if self.ctx.in_root else ""
        default_path = os.path.join(initial_dir, default_name)


        file_path, _ = QFileDialog.getSaveFileName(self, "Save Output File", default_path, "OUT Files (*.out);;All Files (*.*)")
        if file_path:
             if not file_path.lower().endswith(".out"):
                 file_path += ".out"
             self.ctx.out_root = file_path
             self.ctx.out_file = os.path.basename(file_path)
             self.outputFileLabel.setText(f"{self.ctx.out_file} ({os.path.dirname(file_path)})")


    def update_ui_from_context(self):
        """Updates UI elements based on current ctx values (e.g., after loading PAR)."""
        self.startDateInput.setText(self.ctx.start_date.strftime("%d/%m/%Y"))
        self.ensembleSizeInput.setText(str(self.ctx.ensemble_size))
        self.conditionalCheck.setChecked(self.ctx.conditional_check)
        # self.thresholdInput.setText(str(self.ctx.local_thresh)) # Threshold not typically in PAR for scenario gen

        if self.ctx.in_file and self.ctx.in_root: # PAR might provide an input data file
             self.inputFileLabel.setText(f"{self.ctx.in_file} ({os.path.dirname(self.ctx.in_root)})")
        elif self.ctx.in_root and not self.ctx.in_file: # PAR file itself was selected, but it didn't specify data file
             self.inputFileLabel.setText(f"PAR: {os.path.basename(self.ctx.in_root)} (Data file not specified in PAR)")
        else:
             self.inputFileLabel.setText("No file selected")

    def update_progress(self, value, text):
        """Slot to update the progress bar and label."""
        self.progressBar.setValue(value)
        self.progressLabel.setText(text)
        QApplication.processEvents()

    # --- Validation Methods ---
    def validate_start_date(self):
        try:
            date_obj = datetime.datetime.strptime(self.startDateInput.text(), "%d/%m/%Y").date()
            self.ctx.start_date = date_obj
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Invalid start date format. Use DD/MM/YYYY.")
            self.startDateInput.setText(self.ctx.start_date.strftime("%d/%m/%Y"))

    def validate_ensemble_size(self):
        try:
            val = int(self.ensembleSizeInput.text())
            if 1 <= val <= 100:
                self.ctx.ensemble_size = val
            else:
                raise ValueError("Value out of range 1-100")
        except ValueError as e:
            QMessageBox.warning(self, "Input Error", f"Ensemble size: {e}")
            self.ensembleSizeInput.setText(str(self.ctx.ensemble_size))

    def validate_threshold(self):
        try:
            val = float(self.thresholdInput.text())
            self.ctx.local_thresh = val
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Invalid threshold value. Must be a number.")
            self.thresholdInput.setText(str(self.ctx.local_thresh))

    def validate_occurrence(self):
        try:
            val = float(self.occFactorInput.text())
            if -99.0 <= val <= 100.0:
                self.ctx.occurrence_factor = val
                self.ctx.occurrence_factor_percent = (100.0 + val) / 100.0
            else:
                 raise ValueError("Value out of range -99 to 100")
        except ValueError as e:
            QMessageBox.warning(self, "Input Error", f"Occurrence factor: {e}")
            self.occFactorInput.setText(str(self.ctx.occurrence_factor))

    def validate_amount(self):
        try:
            val_factor = float(self.amountFactorInput.text())
            if -100.0 <= val_factor <= 100.0:
                self.ctx.amount_factor = val_factor
                self.ctx.amount_factor_percent = (100.0 + val_factor) / 100.0
            else:
                 raise ValueError("Factor out of range -100 to 100")
        except ValueError as e:
            QMessageBox.warning(self, "Input Error", f"Amount factor: {e}")
            self.amountFactorInput.setText(str(self.ctx.amount_factor))
        try:
            val_add = float(self.amountAddInput.text())
            # VB range check: -100 to 100, but can be wider for some variables
            # Let's assume a reasonable range, but this might need adjustment based on typical data magnitudes
            # if -10000.0 <= val_add <= 10000.0:
            self.ctx.amount_addition = val_add
            # else:
            #      raise ValueError("Addition value seems too large/small")
        except ValueError as e:
            QMessageBox.warning(self, "Input Error", f"Amount addition: {e}")
            self.amountAddInput.setText(str(self.ctx.amount_addition))

    def validate_variance(self):
        try:
            val = float(self.varianceFactorInput.text())
            # VB range check: -100000 to 100000 (very wide)
            # The critical part is that (100+val)/100 must be non-negative
            factor_percent = (100.0 + val) / 100.0
            if factor_percent >= 0:
                self.ctx.variance_factor = val
                self.ctx.variance_factor_percent = factor_percent
            else:
                 raise ValueError("Resulting variance multiplier cannot be negative (input >= -100).")
        except ValueError as e:
            QMessageBox.warning(self, "Input Error", f"Variance factor: {e}")
            self.varianceFactorInput.setText(str(self.ctx.variance_factor))

    def validate_trend(self):
        try:
            val_lin = float(self.trendLinearInput.text())
            # if -100.0 <= val_lin <= 100.0: # VB range, could be wider depending on variable
            self.ctx.linear_trend = val_lin
            # else: raise ValueError("Linear trend value seems too large/small")
        except ValueError as e:
            QMessageBox.warning(self, "Input Error", f"Linear trend: {e}")
            self.trendLinearInput.setText(str(self.ctx.linear_trend))
        try:
            val_exp = float(self.trendExpInput.text())
            # VB check: cannot be zero for its formula. If it's a multiplier, cannot be 1 for no effect.
            # The current logic uses it as an additive percentage, so 0 means no effect.
            # if abs(val_exp) < 1e-9 : # If meaning is like "target of 0% change by end"
            #    QMessageBox.warning(self, "Input Error", "Exponential trend factor of 0 means no change.")
            #    # self.trendExpInput.setText(str(self.ctx.exp_trend)) # Revert or allow 0
            self.ctx.exp_trend = val_exp
            self.ctx.add_exp_option = val_exp > 0

        except ValueError as e:
            QMessageBox.warning(self, "Input Error", f"Exponential trend: {e}")
            self.trendExpInput.setText(str(self.ctx.exp_trend))
        try:
            val_log = float(self.trendLogInput.text())
            # if -100.0 <= val_log <= 100.0: # VB range
            self.ctx.logistic_trend = val_log
            # else: raise ValueError("Logistic trend value seems too large/small")
        except ValueError as e:
            QMessageBox.warning(self, "Input Error", f"Logistic trend: {e}")
            self.trendLogInput.setText(str(self.ctx.logistic_trend))


    # --- Main Execution ---
    def run_generation(self):
        """Orchestrates the scenario generation process."""
        # 1. Update context from UI (catches last-minute changes not triggering 'editingFinished')
        self.validate_start_date()
        self.validate_ensemble_size()
        self.validate_threshold()
        self.validate_occurrence()
        self.validate_amount()
        self.validate_variance()
        self.validate_trend()

        self.ctx.conditional_check = self.conditionalCheck.isChecked()
        self.ctx.occurrence_check = self.occurrenceCheck.isChecked()
        self.ctx.preserve_totals_check = self.preserveTotalsCheck.isChecked()
        self.ctx.amount_check = self.amountCheck.isChecked()
        self.ctx.variance_check = self.varianceCheck.isChecked()
        self.ctx.trend_check = self.trendCheck.isChecked()
        self.ctx.occurrence_option = self.occOptionGroup.checkedId()
        self.ctx.amount_option = self.amountOptionGroup.checkedId()
        self.ctx.trend_option = self.trendOptionGroup.checkedId()


        if not check_settings(self.ctx, self):
            return

        mini_reset(self.ctx)
        self.progressBar.setVisible(True)
        self.progressLabel.setVisible(True)
        self.update_progress(0, "Starting...")
        self.generateButton.setEnabled(False)
        self.resetButton.setEnabled(False)
        QApplication.processEvents()


        if not read_input_file(self.ctx, self.update_progress):
            self.update_progress(0, "Error during file reading.")
            self.generateButton.setEnabled(True); self.resetButton.setEnabled(True)
            return

        # Apply Treatments
        if self.ctx.occurrence_check and not self.ctx.error_occurred:
            apply_occurrence(self.ctx, self.update_progress)
            if self.ctx.error_occurred: self._finalize_process(False); return

        # Variance needs means. Amount might change means. If both active, order matters.
        # VB typical order: Occurrence, Amount, Variance, Trend.
        # Means for variance should reflect state *after* Amount, if Amount is applied.
        # Means for Unconditional variance are based on all data.
        # Means for Conditional variance are based on data > threshold.

        if self.ctx.amount_check and not self.ctx.error_occurred:
            apply_amount(self.ctx, self.update_progress)
            if self.ctx.error_occurred: self._finalize_process(False); return

        if self.ctx.variance_check and not self.ctx.error_occurred:
            calc_means(self.ctx, self.update_progress) # Calculate means based on current data state
            if self.ctx.error_occurred: self._finalize_process(False); return
            apply_variance(self.ctx, self.update_progress)
            if self.ctx.error_occurred: self._finalize_process(False); return

        if self.ctx.trend_check and not self.ctx.error_occurred:
            apply_trend(self.ctx, self.update_progress)
            if self.ctx.error_occurred: self._finalize_process(False); return

        success = False
        if not self.ctx.error_occurred:
            if write_output_file(self.ctx, self.update_progress):
                success = True

        self._finalize_process(success)

    def _finalize_process(self, success):
        self.generateButton.setEnabled(True)
        self.resetButton.setEnabled(True)
        QApplication.processEvents()

        if success:
            self.update_progress(100, "Scenario Generation Complete.")
            msg = f"Scenario Generated Successfully.\n{self.ctx.no_of_days} days processed."
            if self.ctx.variance_check and self.ctx.conditional_check and abs(self.ctx.lamda - GLOBAL_MISSING_CODE) > 1e-6 :
                 msg += f"\nLambda for Box-Cox (Variance): {self.ctx.lamda:.3f}"
            QMessageBox.information(self, "Success", msg)
        elif self.ctx.error_occurred:
            self.update_progress(0, "Processing failed. Check messages.")
            # QMessageBox.critical(self, "Processing Error", "An error occurred during scenario generation. Please check console/messages.")
        else: # Not success, not error_occurred -> cancelled or other silent fail
            self.update_progress(0, "Processing did not complete.")


###############################################################################
# 5. Main Application Entry Point / Module Export
###############################################################################
ContentWidget = ScenarioGeneratorWidget

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET) # Apply global stylesheet
    window = ScenarioGeneratorWidget()
    window.setWindowTitle("SDSM Scenario Generator")
    window.setGeometry(100, 100, 720, 700) # Adjusted size slightly
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

