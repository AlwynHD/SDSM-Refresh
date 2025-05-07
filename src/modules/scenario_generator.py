import sys
import os
import math
import random
import datetime
import statistics  # For mean, stdev if needed, though manual calculation is often used here

from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QGridLayout, QCheckBox, QRadioButton,
                             QButtonGroup, QFileDialog, QGroupBox, QMessageBox, QProgressBar)
from PyQt5.QtCore import Qt, QTimer # QTimer for progress bar updates

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
        self.exp_trend = 1 # VB code defaults ExpTrend to 1
        self.logistic_trend = 1 # VB code defaults LogisticTrend to 1
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
    elif ctx.trend_check and ctx.trend_option == 1 and abs(ctx.exp_trend) < 1e-9 :
        QMessageBox.critical(parent_widget, "Error", "Exponential trend is selected, but the value is zero.")
        all_ok = False
    elif ctx.trend_check and ctx.trend_option == 2 and abs(ctx.logistic_trend) < 1e-9 :
        QMessageBox.critical(parent_widget, "Error", "Logistic trend is selected, but the value is zero.")
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

                for _ in range(days_to_delete):
                    # VB-style random selection using cumulative probability
                    selected_month = -1
                    random_no = Rnd() * cum_prop_sum[11]
                    
                    for i in range(12):
                        if random_no < cum_prop_sum[i]:
                            selected_month = i
                            break
                    
                    if selected_month == -1:
                        selected_month = 11
                    
                    # Make sure we get a month with wet days
                    attempts = 0
                    while wet_count[selected_month] <= 0 and attempts < 12:
                        random_no = Rnd() * cum_prop_sum[11]
                        for i in range(12):
                            if random_no < cum_prop_sum[i]:
                                selected_month = i
                                break
                        attempts += 1
                    
                    if wet_count[selected_month] <= 0:
                        continue # No wet days available
                    
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

                    # Update cumulative probability if month became fully dry
                    if wet_count[selected_month] == 0:
                        if selected_month == 0:
                            cum_prop_sum[0] = 0.0
                        else:
                            cum_prop_sum[selected_month] = cum_prop_sum[selected_month - 1]

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
                if prop_wet_array[0] == GLOBAL_MISSING_CODE or prop_wet_array[0] == 1.0:
                    cum_prop_sum[0] = 0.0
                else:
                    cum_prop_sum[0] = prop_wet_array[0]
                
                for i in range(1, 12):
                    if prop_wet_array[i] == GLOBAL_MISSING_CODE or prop_wet_array[i] == 1.0:
                        cum_prop_sum[i] = cum_prop_sum[i-1]
                    else:
                        cum_prop_sum[i] = cum_prop_sum[i-1] + prop_wet_array[i]

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
                        random_no = Rnd() * cum_prop_sum[11]
                        for i in range(12):
                            if random_no < cum_prop_sum[i]:
                                selected_month = i
                                break
                        attempts += 1
                    
                    if dry_count[selected_month] <= 0:
                        continue # No dry days available
                    
                    # Select a random dry day for that month
                    dry_day_list_index = int(Rnd() * dry_count[selected_month])
                    day_index_to_modify = dry_array[selected_month][dry_day_list_index]

                    # --- Select a wet day value to copy using VB logic ---
                    source_wet_day_value = GLOBAL_MISSING_CODE

                    # VB Logic: Prioritize using a wet day from the *same* month if available (original count)
                    if original_wet_count[selected_month] > 0:
                        # Use wet days from current month
                        if wet_count[selected_month] > 0:
                            source_wet_day_index_in_list = int(Rnd() * wet_count[selected_month])
                            source_day_index = wet_array[selected_month][source_wet_day_index_in_list]
                            source_wet_day_value = ctx.data_array[j][source_day_index]
                    
                    # If no wet day found in the selected month, find nearest month with a wet day
                    if source_wet_day_value == GLOBAL_MISSING_CODE:
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

                        # Update cumulative probability if month became fully wet
                        if dry_count[selected_month] == 0:
                            if selected_month == 0:
                                cum_prop_sum[0] = 0.0
                            else:
                                cum_prop_sum[selected_month] = cum_prop_sum[selected_month - 1]

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
                 current_wet_count = wet_count[m]

                 if current_wet_count > target_wet_count:
                     # --- Remove wet days ---
                     days_to_delete = current_wet_count - target_wet_count
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

                 elif current_wet_count < target_wet_count:
                     # --- Add wet days ---
                     days_to_add = target_wet_count - current_wet_count
                     for _ in range(days_to_add):
                         if dry_count[m] <= 0: break # No space left to add in this month
                         
                         dry_day_list_index = int(Rnd() * dry_count[m])
                         day_index_to_modify = dry_array[m][dry_day_list_index]

                         # --- Select source wet day value (same logic as stochastic add) ---
                         source_wet_day_value = GLOBAL_MISSING_CODE
                         if original_wet_count[m] > 0 and wet_count[m] > 0:
                              source_wet_day_index_in_list = int(Rnd() * wet_count[m])
                              source_day_index = wet_array[m][source_wet_day_index_in_list]
                              source_wet_day_value = ctx.data_array[j][source_day_index]
                         else:
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

            if new_total_rainfall > 1e-9 and total_rainfall > 1e-9: # Avoid division by zero or near-zero
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
            temp_array[idx] = -multiplier * i
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
            if val != GLOBAL_MISSING_CODE and val > ctx.local_thresh and abs(val) > 1e-9:
                try:
                    if abs(k) < 1e-9: # Lambda is zero -> log transform
                        transformed_val = math.log(val)
                    else: # Standard Box-Cox
                        transformed_val = (val ** k - 1) / k
                    temp_array.append(transformed_val)
                except (ValueError, OverflowError): # Handle log(neg) or power errors
                     # Skip this value if transform fails
                     continue

        count = len(temp_array)
        if count > 10: # Need enough points (VB used > 10)
            mean_val = sum(temp_array) / count

            # --- VB used Shell Sort, Python's sort is efficient ---
            temp_array.sort()

            # --- Calculate Median and IQR ---
            median_val = statistics.median(temp_array) # Handles even/odd counts

            # Calculate quartiles (using simple method like VB likely did)
            # Note: Different methods exist (inclusive/exclusive median). Using basic percentile approx.
            lower_idx = int(count / 4) # Index of Q1 approx
            upper_idx = int(3 * count / 4) # Index of Q3 approx

            # Ensure indices are valid
            if lower_idx < 0: lower_idx = 0
            if upper_idx >= count : upper_idx = count - 1
            if lower_idx >= upper_idx and count > 1: # Adjust if indices overlap/invalid
                lower_idx = 0
                upper_idx = count -1

            if lower_idx < upper_idx:
                q1 = temp_array[lower_idx]
                q3 = temp_array[upper_idx]
                iqr = q3 - q1
            elif count > 0: # Handle case with few points where IQR might be 0
                iqr = temp_array[-1] - temp_array[0]
            else:
                 iqr = 0


            # --- Calculate Hinkley's d ---
            d = GLOBAL_MISSING_CODE
            if iqr > 1e-9: # Avoid division by zero
                 d = (mean_val - median_val) / iqr

            if d != GLOBAL_MISSING_CODE:
                 abs_d = abs(d)
                 if abs_d < min_abs_d:
                     min_abs_d = abs_d
                     best_lam = k

        k += step # Increment lambda

    if min_abs_d == float('inf'): # No valid lambda found
        return GLOBAL_MISSING_CODE
    else:
        return best_lam

def unbox_cox(value: float, lamda: float) -> float:
    """Inverse Box-Cox transform. Mirrors VB."""
    if value == GLOBAL_MISSING_CODE:
        return GLOBAL_MISSING_CODE
    try:
        if abs(lamda) < 1e-9: # Lambda is zero -> exp
            # Add check for large values to prevent overflow
            if value > 700: # Approx limit for exp() in standard floats
                return float('inf') # Or handle as error/max value
            return math.exp(value)
        else: # Standard inverse Box-Cox
            base = (value * lamda) + 1
            if base < 0:
                 # Trying to take power of negative number - indicates issue
                 # VB might raise error or return missing code. Let's return missing.
                 return GLOBAL_MISSING_CODE
            # Add check for large exponents if lamda is small
            power = 1.0 / lamda
            return base ** power
    except (ValueError, OverflowError):
        # Handle math errors during inverse transform
        return GLOBAL_MISSING_CODE # Return missing if inverse fails


def calc_variance_after_transform(ctx: SDSMContext, ensemble: int, trans_array, factor: float, mean_trans: float) -> float:
    """Helper for ApplyVariance: Applies factor to transformed data, untransforms, calculates variance. Mirrors VB."""
    temp_untransformed = []
    for i in range(ctx.no_of_days):
        if trans_array[i] != GLOBAL_MISSING_CODE:
            try:
                # Apply factor around the mean of the *transformed* data
                val_trans_adjusted = ((trans_array[i] - mean_trans) * factor) + mean_trans
                # Untransform
                val_untransformed = unbox_cox(val_trans_adjusted, ctx.lamda)

                if val_untransformed != GLOBAL_MISSING_CODE and val_untransformed != float('inf'):
                     # Check if untransformed value falls below threshold - clamp it
                     if ctx.conditional_check and val_untransformed <= ctx.local_thresh:
                         temp_untransformed.append(ctx.local_thresh + 1e-6)
                     else:
                        temp_untransformed.append(val_untransformed)
                # else: Skip if untransform failed

            except (ValueError, OverflowError):
                 continue # Skip if adjustment or untransform fails

    count = len(temp_untransformed)
    if count > 1:
        mean_new = sum(temp_untransformed) / count
        variance = sum([(x - mean_new) ** 2 for x in temp_untransformed]) / count
        return variance
    elif count == 1:
         return 0.0 # Variance is 0 for a single point
    else:
        return GLOBAL_MISSING_CODE # Cannot calculate variance


def apply_variance(ctx: SDSMContext, progress_callback=None):
    """Apply a variance treatment. Handles conditional (Box-Cox) and unconditional."""
    if not ctx.mean_array:
        QMessageBox.critical(None, "Error", "Mean/SD must be calculated before applying variance. Run CalcMeans first.")
        ctx.error_occurred = True
        return

    target_variance_ratio = ctx.variance_factor_percent # e.g., 1.10 for +10%

    for j in range(ctx.ensemble_size): # Loop through ensembles
        if ctx.global_kop_out: return
        if progress_callback:
             progress_callback(int(j / ctx.ensemble_size * 10), f"Applying Variance {j+1} Prep")

        mean_j = ctx.mean_array[j]['mean']
        sd_j = ctx.mean_array[j]['sd']
        original_variance = sd_j ** 2 if sd_j != GLOBAL_MISSING_CODE else GLOBAL_MISSING_CODE

        if mean_j == GLOBAL_MISSING_CODE or sd_j == GLOBAL_MISSING_CODE:
            print(f"Warning: Ensemble {j+1} has missing mean/SD. Skipping variance adjustment.")
            continue
        if original_variance <= 1e-9: # Cannot modify variance if it's already zero or near-zero
             print(f"Warning: Ensemble {j+1} has zero initial variance. Skipping variance adjustment.")
             continue

        # --- Unconditional Process ---
        if not ctx.conditional_check:
            # Simple scaling around the mean
            # Formula: Y = (X - MeanX) * sqrt(TargetVarRatio) + MeanX
            scaling_factor = math.sqrt(target_variance_ratio)
            for i in range(ctx.no_of_days):
                val = ctx.data_array[j][i]
                if val != GLOBAL_MISSING_CODE:
                    ctx.data_array[j][i] = ((val - mean_j) * scaling_factor) + mean_j
            if progress_callback: progress_callback(100, f"Applying Variance {j+1} Complete") # Fast, so jump to 100

        # --- Conditional Process (Box-Cox) ---
        else:
            # 1. Find optimal lambda
            if progress_callback: progress_callback(int(j / ctx.ensemble_size * 10) + 10, f"Variance {j+1} Finding Lambda")
            # VB used 3 steps, refining the range
            lamda = find_min_lambda(ctx, j, -2.0, 2.0, 0.25)
            if lamda != GLOBAL_MISSING_CODE:
                lamda = find_min_lambda(ctx, j, lamda - 0.25, lamda + 0.25, 0.1)
            if lamda != GLOBAL_MISSING_CODE:
                lamda = find_min_lambda(ctx, j, lamda - 0.1, lamda + 0.1, 0.01)

            if lamda == GLOBAL_MISSING_CODE:
                QMessageBox.critical(None, "Error Message", f"Ensemble {j+1}: Could not find suitable lambda for Box-Cox transform. Cannot apply variance.")
                # Don't set ctx.error_occurred, just skip this ensemble's variance adjustment
                continue # Skip to next ensemble

            ctx.lamda = lamda # Store the found lambda

            # 2. Transform the data using optimal lambda
            trans_array = [GLOBAL_MISSING_CODE] * ctx.no_of_days
            valid_transformed_values = []
            for i in range(ctx.no_of_days):
                val = ctx.data_array[j][i]
                # Transform only valid, non-zero, above-threshold values
                if val != GLOBAL_MISSING_CODE and val > ctx.local_thresh and abs(val) > 1e-9:
                    try:
                        if abs(ctx.lamda) < 1e-9: # Log transform
                            transformed_val = math.log(val)
                        else: # Box-Cox
                            transformed_val = (val ** ctx.lamda - 1) / ctx.lamda
                        trans_array[i] = transformed_val
                        valid_transformed_values.append(transformed_val)
                    except (ValueError, OverflowError):
                        trans_array[i] = GLOBAL_MISSING_CODE # Mark as missing if transform fails
                else:
                     trans_array[i] = GLOBAL_MISSING_CODE # Keep non-eligible as missing

            if not valid_transformed_values:
                 print(f"Warning: Ensemble {j+1}: No valid values after Box-Cox transform. Skipping variance adjustment.")
                 continue

            mean_trans = sum(valid_transformed_values) / len(valid_transformed_values)

            # 3. Find the scaling factor for the *transformed* data iteratively
            if progress_callback: progress_callback(int(j / ctx.ensemble_size * 10) + 30, f"Variance {j+1} Finding Factor")

            # VB iterative search for the 'factor'
            lower_f = 0.5 # Initial search range for factor
            higher_f = 1.5 # Broadened range slightly cf VB
            best_factor = 1.0

            # Adjust initial range based on target ratio
            if target_variance_ratio > 1.0:
                lower_f = 1.0
                higher_f = 1.5 # Needs to be > 1
            else:
                 lower_f = 0.5 # Needs to be < 1
                 higher_f = 1.0

            for iter_num in range(10): # VB used 10 iterations
                if ctx.global_kop_out: return
                if progress_callback:
                     prog = int(j / ctx.ensemble_size * 10) + 30 + int(iter_num/10 * 60)
                     progress_callback(prog, f"Variance {j+1} Iteration {iter_num+1}")

                middle_f = (lower_f + higher_f) / 2.0
                if abs(middle_f) < 1e-9: middle_f = 1e-9 # Avoid zero factor

                # Calculate the variance that *results* from applying middle_f
                resulting_variance = calc_variance_after_transform(ctx, j, trans_array, middle_f, mean_trans)

                if resulting_variance == GLOBAL_MISSING_CODE:
                     # If calc fails, we can't proceed with search. Use best guess so far or fail.
                     print(f"Warning: Ensemble {j+1}, Iter {iter_num+1}: Could not calculate resulting variance. Using previous best factor.")
                     if iter_num == 0: best_factor = 1.0 # Default if fails immediately
                     break # Exit iteration loop

                current_variance_ratio = resulting_variance / original_variance

                # Adjust search range
                if current_variance_ratio < target_variance_ratio:
                    lower_f = middle_f # Result too low, need higher factor
                else:
                    higher_f = middle_f # Result too high, need lower factor

                best_factor = (lower_f + higher_f) / 2.0 # Update best guess for next iter or final use

            # 4. Apply the best factor found to the transformed data and untransform
            if progress_callback: progress_callback(int(j / ctx.ensemble_size * 10)+95, f"Variance {j+1} Applying Final")

            for i in range(ctx.no_of_days):
                if trans_array[i] != GLOBAL_MISSING_CODE:
                    try:
                        val_trans_adjusted = ((trans_array[i] - mean_trans) * best_factor) + mean_trans
                        val_untransformed = unbox_cox(val_trans_adjusted, ctx.lamda)

                        if val_untransformed != GLOBAL_MISSING_CODE and val_untransformed != float('inf'):
                            # Check conditional threshold clamp
                            if ctx.conditional_check and val_untransformed <= ctx.local_thresh:
                                ctx.data_array[j][i] = ctx.local_thresh + 1e-6
                            else:
                                ctx.data_array[j][i] = val_untransformed
                        else:
                             # If untransform fails, leave original value? Or set missing?
                             # Let's leave original value as a fallback.
                             pass # Keep original ctx.data_array[j][i]

                    except (ValueError, OverflowError):
                         # Keep original value if adjustment/untransform fails
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
            # VB: IncrementValue = LinearTrend / YearIndicator (or 365.25)
            # VB: IncrementMultiplier = LinearTrend / (YearIndicator * 100)
            if ctx.year_indicator == 366:
                increment_per_day = ctx.linear_trend / 365.25 # VB divided by 365.25 for leap years
                increment_multiplier_per_day = ctx.linear_trend / 36525.0 # VB logic
            else:
                increment_per_day = ctx.linear_trend / ctx.year_indicator
                increment_multiplier_per_day = ctx.linear_trend / (ctx.year_indicator * 100.0)

            for i in range(ctx.no_of_days):
                val = ctx.data_array[j][i]
                if val != GLOBAL_MISSING_CODE:
                    # VB used 1-based index (i in range 1 to NoOfDays)
                    day_index = i + 1 # Convert to 1-based for VB compatibility

                    if not ctx.conditional_check: # Unconditional: Add trend
                         trend_effect = increment_per_day * day_index
                         ctx.data_array[j][i] = val + trend_effect
                    else: # Conditional: Multiply by trend factor if > threshold
                        if val > ctx.local_thresh:
                            trend_multiplier = 1.0 + (increment_multiplier_per_day * day_index)
                            new_val = val * trend_multiplier
                            # Clamp to threshold
                            if new_val <= ctx.local_thresh:
                                ctx.data_array[j][i] = ctx.local_thresh + 1e-6
                            else:
                                ctx.data_array[j][i] = new_val

        # --- Exponential Trend ---
        elif ctx.trend_option == 1:
            exp_trend_val = ctx.exp_trend
            if abs(exp_trend_val) < 1e-9: continue # Skip if zero trend

            add_exp = exp_trend_val > 0
            exp_trend_abs = abs(exp_trend_val)

            # VB: ExpAValue = NoOfDays / (Log(ExpTrendAbs + 1))
            try:
                log_arg = exp_trend_abs + 1.0
                if log_arg <= 1e-9 : continue # Avoid log of zero/negative
                exp_a_value = ctx.no_of_days / math.log(log_arg)
                if abs(exp_a_value) < 1e-9: continue # Avoid division by zero later
            except (ValueError, OverflowError):
                 print(f"Warning: Ensemble {j+1}: Could not calculate ExpAValue for exponential trend.")
                 continue # Skip ensemble

            for i in range(ctx.no_of_days):
                val = ctx.data_array[j][i]
                if val != GLOBAL_MISSING_CODE:
                    # VB used 1-based index
                    day_index = i + 1

                    try:
                        # VB: TrendEffect = Exp( (i / ExpAValue) ) - 1
                        exponent = day_index / exp_a_value
                        # Check for large exponent
                        if exponent > 700: # Prevent overflow
                            trend_effect = float('inf')
                        else:
                            trend_effect = math.exp(exponent) - 1.0
                        if trend_effect == float('inf'): continue # Skip if calc overflows

                    except (ValueError, OverflowError):
                         continue # Skip day if calculation fails

                    if not ctx.conditional_check: # Unconditional: Add/Subtract trend effect
                        if add_exp:
                            ctx.data_array[j][i] = val + trend_effect
                        else:
                            ctx.data_array[j][i] = val - trend_effect
                    else: # Conditional: Multiply by trend factor if > threshold
                        if val > ctx.local_thresh:
                            # VB: ExpMultiplier = (100 +/- TrendEffect) / 100
                            if add_exp:
                                trend_multiplier = (100.0 + trend_effect) / 100.0
                            else:
                                trend_multiplier = (100.0 - trend_effect) / 100.0

                            # Ensure multiplier is positive
                            if trend_multiplier < 0: trend_multiplier = 0

                            new_val = val * trend_multiplier
                            # Clamp to threshold
                            if new_val <= ctx.local_thresh:
                                ctx.data_array[j][i] = ctx.local_thresh + 1e-6
                            else:
                                ctx.data_array[j][i] = new_val

        # --- Logistic Trend ---
        elif ctx.trend_option == 2:
            logistic_trend_val = ctx.logistic_trend
            if abs(logistic_trend_val) < 1e-9: continue # Skip if zero trend

            for i in range(ctx.no_of_days):
                 val = ctx.data_array[j][i]
                 if val != GLOBAL_MISSING_CODE:
                    # VB: XMapping = (((i - 1) / (NoOfDays - 1)) * 12) - 6
                    # Since VB used 1-based index, for 0-based index we just use i
                    if ctx.no_of_days > 1:
                        x_mapping = ((i / (ctx.no_of_days - 1)) * 12.0) - 6.0
                    else:
                         x_mapping = 0.0 # Avoid division by zero if only one day

                    try:
                        # VB: IncrementValue = 1 / (1 + Exp(-XMapping)) -> Sigmoid function [0,1]
                        logistic_base = 1.0 / (1.0 + math.exp(-x_mapping))
                        # VB: IncrementValue = LogisticTrend * IncrementValue
                        trend_effect = logistic_trend_val * logistic_base
                    except OverflowError:
                         # Handle exp overflow if x_mapping is very large negative
                         trend_effect = 0.0 if x_mapping < -700 else logistic_trend_val # Approx limits

                    if not ctx.conditional_check: # Unconditional: Add trend effect
                        ctx.data_array[j][i] = val + trend_effect
                    else: # Conditional: Multiply by trend factor if > threshold
                        if val > ctx.local_thresh:
                            # VB: Multiplier = (100 + IncrementValue) / 100
                            trend_multiplier = (100.0 + trend_effect) / 100.0

                            # Ensure multiplier is positive
                            if trend_multiplier < 0: trend_multiplier = 0

                            new_val = val * trend_multiplier
                            # Clamp to threshold
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
                f.write("".join(line_parts) + "\n") # Join with tabs handled by format_value_output

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

        idx = 0
        ctx.num_predictors = int(lines[idx]); idx += 1
        ctx.num_months = int(lines[idx]); idx += 1 # Should be 12
        ctx.year_length = int(lines[idx]); idx += 1
        ctx.year_indicator = ctx.year_length # Assume they are the same from PAR
        start_date_str = lines[idx]; idx += 1
        ctx.start_date = datetime.datetime.strptime(start_date_str, "%d/%m/%Y").date()
        ctx.no_of_days = int(lines[idx]); idx += 1
        # Skip potential duplicate date/days if present
        if lines[idx] == start_date_str: idx += 1
        if idx < len(lines) and lines[idx].isdigit() and int(lines[idx]) == ctx.no_of_days: idx +=1

        cond_str = lines[idx]; idx += 1
        ctx.conditional_check = (cond_str.upper() == "#TRUE#")
        ensemble_str = lines[idx]; idx += 1
        ctx.ensemble_size = int(ensemble_str)

        # Skip variance factor percent, transform code, bias correction from PAR
        idx += 3 # Skip 3 lines

        # Read Predictor Files (relative paths)
        ctx.predictor_files = []
        par_dir = os.path.dirname(par_path)
        for _ in range(ctx.num_predictors):
            if idx >= len(lines): break
            pfile = lines[idx]
            idx += 1
            abs_pfile = os.path.normpath(os.path.join(par_dir, pfile))
            ctx.predictor_files.append(abs_pfile)

        # Read Data File (relative path)
        if idx < len(lines):
            data_file = lines[idx]
            # Check if it's a coefficient line or the data file name
            if ' ' not in data_file and '.' in data_file: # Likely filename
                idx += 1
                abs_data_file = os.path.normpath(os.path.join(par_dir, data_file))
                ctx.in_file = os.path.basename(abs_data_file)
                ctx.in_root = abs_data_file

        # Read Monthly Coefficients (if present)
        ctx.monthly_coeffs = []
        coeffs_found = False
        while idx < len(lines):
            parts = lines[idx].split()
            try:
                coeffs = [float(x) for x in parts]
                if len(coeffs) == ctx.num_predictors + 1:
                    ctx.monthly_coeffs.append(coeffs)
                    coeffs_found = True
                else:
                    break
            except ValueError:
                 break
            idx += 1

        if coeffs_found:
            print(f"Read {len(ctx.monthly_coeffs)} lines of monthly coefficients from PAR file.")

        return True

    except Exception as e:
        QMessageBox.critical(None, "Error", f"Error parsing .PAR file '{os.path.basename(par_path)}':\n{e}\nLine approx {idx+1}")
        return False

###############################################################################
# 4. PyQt5 User Interface (ScenarioGeneratorWidget)
###############################################################################
class ScenarioGeneratorWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.ctx = SDSMContext()
        self._init_ui()
        self.reset_ui_and_context() # Initialize UI and context state

    def _init_ui(self):
        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(15, 15, 15, 15) # Reduced margins
        mainLayout.setSpacing(10) # Reduced spacing

        # --- File Selection ---
        fileGroup = QGroupBox("Files")
        fileLayout = QGridLayout()
        self.inputFileButton = QPushButton("Input (.par/.txt)")
        self.inputFileLabel = QLabel("No file selected")
        self.inputFileLabel.setWordWrap(True)
        self.outputFileButton = QPushButton("Output (.out)")
        self.outputFileLabel = QLabel("No file selected")
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
        self.startDateInput = QLineEdit()
        self.ensembleSizeInput = QLineEdit()
        self.conditionalCheck = QCheckBox("Conditional Process")
        self.thresholdInput = QLineEdit()
        generalLayout.addWidget(QLabel("Start Date:"), 0, 0)
        generalLayout.addWidget(self.startDateInput, 0, 1)
        generalLayout.addWidget(QLabel("Ensemble Size:"), 0, 2)
        generalLayout.addWidget(self.ensembleSizeInput, 0, 3)
        generalLayout.addWidget(self.conditionalCheck, 1, 0, 1, 2)
        generalLayout.addWidget(QLabel("Threshold:"), 1, 2)
        generalLayout.addWidget(self.thresholdInput, 1, 3)
        generalGroup.setLayout(generalLayout)
        mainLayout.addWidget(generalGroup)

        # --- Treatments ---
        treatmentsGroup = QGroupBox("Treatments")
        treatmentsLayout = QGridLayout()
        treatmentsLayout.setSpacing(5)

        # Occurrence Row
        self.occurrenceCheck = QCheckBox("Occurrence")
        self.occFactorInput = QLineEdit()
        self.occFactorInput.setPlaceholderText("% change")
        self.occOptionGroup = QButtonGroup(self)
        self.occFactorRadio = QRadioButton("Factor") # Stochastic in VB
        self.occForcedRadio = QRadioButton("Forced %") # Needs ZoM input - TBD if needed
        self.occOptionGroup.addButton(self.occFactorRadio, 0)
        self.occOptionGroup.addButton(self.occForcedRadio, 1)
        self.preserveTotalsCheck = QCheckBox("Preserve Totals")
        treatmentsLayout.addWidget(self.occurrenceCheck, 0, 0)
        treatmentsLayout.addWidget(self.occFactorInput, 0, 1)
        treatmentsLayout.addWidget(self.occFactorRadio, 0, 2)
        treatmentsLayout.addWidget(self.occForcedRadio, 0, 3)
        treatmentsLayout.addWidget(self.preserveTotalsCheck, 0, 4, 1, 2) # Span 2 cols

        # Amount Row
        self.amountCheck = QCheckBox("Amount")
        self.amountOptionGroup = QButtonGroup(self)
        self.amountFactorRadio = QRadioButton("Factor:")
        self.amountFactorInput = QLineEdit()
        self.amountFactorInput.setPlaceholderText("% change")
        self.amountAddRadio = QRadioButton("Addition:")
        self.amountAddInput = QLineEdit()
        self.amountAddInput.setPlaceholderText("value")
        self.amountOptionGroup.addButton(self.amountFactorRadio, 0)
        self.amountOptionGroup.addButton(self.amountAddRadio, 1)
        amountFactorLayout = QHBoxLayout()
        amountFactorLayout.setContentsMargins(0,0,0,0)
        amountFactorLayout.addWidget(self.amountFactorRadio)
        amountFactorLayout.addWidget(self.amountFactorInput)
        amountAddLayout = QHBoxLayout()
        amountAddLayout.setContentsMargins(0,0,0,0)
        amountAddLayout.addWidget(self.amountAddRadio)
        amountAddLayout.addWidget(self.amountAddInput)
        treatmentsLayout.addWidget(self.amountCheck, 1, 0)
        treatmentsLayout.addLayout(amountFactorLayout, 1, 1, 1, 2)
        treatmentsLayout.addLayout(amountAddLayout, 1, 3, 1, 2)

        # Variance Row
        self.varianceCheck = QCheckBox("Variance")
        self.varianceFactorInput = QLineEdit()
        self.varianceFactorInput.setPlaceholderText("% change")
        treatmentsLayout.addWidget(self.varianceCheck, 2, 0)
        treatmentsLayout.addWidget(QLabel("Factor:"), 2, 1)
        treatmentsLayout.addWidget(self.varianceFactorInput, 2, 2)

        # Trend Row
        self.trendCheck = QCheckBox("Trend")
        self.trendOptionGroup = QButtonGroup(self)
        self.trendLinearRadio = QRadioButton("Linear:")
        self.trendLinearInput = QLineEdit()
        self.trendLinearInput.setPlaceholderText("/year value")
        self.trendExpRadio = QRadioButton("Exponential:")
        self.trendExpInput = QLineEdit()
        self.trendExpInput.setPlaceholderText("factor")
        self.trendLogRadio = QRadioButton("Logistic:")
        self.trendLogInput = QLineEdit()
        self.trendLogInput.setPlaceholderText("factor")
        self.trendOptionGroup.addButton(self.trendLinearRadio, 0)
        self.trendOptionGroup.addButton(self.trendExpRadio, 1)
        self.trendOptionGroup.addButton(self.trendLogRadio, 2)
        trendLinLayout=QHBoxLayout(); trendLinLayout.setContentsMargins(0,0,0,0); trendLinLayout.addWidget(self.trendLinearRadio); trendLinLayout.addWidget(self.trendLinearInput)
        trendExpLayout=QHBoxLayout(); trendExpLayout.setContentsMargins(0,0,0,0); trendExpLayout.addWidget(self.trendExpRadio); trendExpLayout.addWidget(self.trendExpInput)
        trendLogLayout=QHBoxLayout(); trendLogLayout.setContentsMargins(0,0,0,0); trendLogLayout.addWidget(self.trendLogRadio); trendLogLayout.addWidget(self.trendLogInput)
        treatmentsLayout.addWidget(self.trendCheck, 3, 0)
        treatmentsLayout.addLayout(trendLinLayout, 3, 1, 1, 2)
        treatmentsLayout.addLayout(trendExpLayout, 4, 1, 1, 2)
        treatmentsLayout.addLayout(trendLogLayout, 5, 1, 1, 2)

        treatmentsLayout.setColumnStretch(5, 1) # Allow right side to stretch
        treatmentsGroup.setLayout(treatmentsLayout)
        mainLayout.addWidget(treatmentsGroup)

        # --- Progress Bar ---
        self.progressBar = QProgressBar()
        self.progressBar.setVisible(False) # Initially hidden
        self.progressLabel = QLabel("")
        self.progressLabel.setVisible(False)
        progressLayout = QHBoxLayout()
        progressLayout.addWidget(self.progressLabel)
        progressLayout.addWidget(self.progressBar)
        mainLayout.addLayout(progressLayout)


        # --- Buttons ---
        buttonLayout = QHBoxLayout()
        self.generateButton = QPushButton("Generate Scenario")
        self.generateButton.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.resetButton = QPushButton("Reset Form")
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.resetButton)
        buttonLayout.addWidget(self.generateButton)
        mainLayout.addLayout(buttonLayout)

        mainLayout.addStretch() # Push content upwards

        # --- Connect Signals ---
        self.inputFileButton.clicked.connect(self.select_input_file)
        self.outputFileButton.clicked.connect(self.select_output_file)
        self.generateButton.clicked.connect(self.run_generation)
        self.resetButton.clicked.connect(self.reset_ui_and_context)

        # Connect inputs losing focus to update context (basic validation)
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

        # Connect checks/radios to update context immediately
        self.conditionalCheck.toggled.connect(lambda checked: setattr(self.ctx, 'conditional_check', checked))
        self.occurrenceCheck.toggled.connect(lambda checked: setattr(self.ctx, 'occurrence_check', checked))
        self.preserveTotalsCheck.toggled.connect(lambda checked: setattr(self.ctx, 'preserve_totals_check', checked))
        self.amountCheck.toggled.connect(lambda checked: setattr(self.ctx, 'amount_check', checked))
        self.varianceCheck.toggled.connect(lambda checked: setattr(self.ctx, 'variance_check', checked))
        self.trendCheck.toggled.connect(lambda checked: setattr(self.ctx, 'trend_check', checked))

        self.occOptionGroup.buttonClicked[int].connect(lambda id: setattr(self.ctx, 'occurrence_option', id))
        self.amountOptionGroup.buttonClicked[int].connect(lambda id: setattr(self.ctx, 'amount_option', id))
        self.trendOptionGroup.buttonClicked[int].connect(lambda id: setattr(self.ctx, 'trend_option', id))


    # --- UI Action Methods ---
    def reset_ui_and_context(self):
        """Resets both the UI fields and the context object to defaults."""
        self.ctx.reset() # Reset data context first

        # Reset File Labels
        self.inputFileLabel.setText("No file selected")
        self.outputFileLabel.setText("No file selected")

        # Reset General Settings
        self.startDateInput.setText(self.ctx.start_date.strftime("%d/%m/%Y"))
        self.ensembleSizeInput.setText(str(self.ctx.ensemble_size))
        self.conditionalCheck.setChecked(self.ctx.conditional_check)
        self.thresholdInput.setText(str(self.ctx.local_thresh))

        # Reset Treatments
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
        self.trendExpInput.setText(str(self.ctx.exp_trend))
        self.trendLogRadio.setChecked(self.ctx.trend_option == 2)
        self.trendLogInput.setText(str(self.ctx.logistic_trend))

        # Hide progress bar
        self.progressBar.setVisible(False)
        self.progressLabel.setVisible(False)
        self.progressBar.setValue(0)
        self.progressLabel.setText("")


    def select_input_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Input File", "", "PAR Files (*.par);;Data Files (*.txt *.dat *.csv);;All Files (*.*)")
        if file_path:
            self.ctx.in_root = file_path
            self.ctx.in_file = os.path.basename(file_path)
            self.inputFileLabel.setText(self.ctx.in_file)

            if file_path.lower().endswith(".par"):
                # Attempt to parse PAR and update UI
                if parse_par_file(file_path, self.ctx):
                    QMessageBox.information(self, "PAR Parsed", f"Loaded settings from {self.ctx.in_file}.\nInput data file set to: {self.ctx.in_file}")
                    # Update UI fields based on parsed ctx
                    self.update_ui_from_context()
                else:
                    # Parsing failed, reset relevant fields
                    self.ctx.in_root = ""
                    self.ctx.in_file = ""
                    self.inputFileLabel.setText("No file selected")

    def select_output_file(self):
        default_name = os.path.splitext(self.ctx.in_file)[0] + "_scenario.out" if self.ctx.in_file else "scenario.out"
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Output File", default_name, "OUT Files (*.out);;All Files (*.*)")
        if file_path:
             # Ensure .out extension if not provided
             if not file_path.lower().endswith(".out"):
                 file_path += ".out"
             self.ctx.out_root = file_path
             self.ctx.out_file = os.path.basename(file_path)
             self.outputFileLabel.setText(self.ctx.out_file)

    def update_ui_from_context(self):
        """Updates UI elements based on current ctx values (e.g., after loading PAR)."""
        self.startDateInput.setText(self.ctx.start_date.strftime("%d/%m/%Y"))
        self.ensembleSizeInput.setText(str(self.ctx.ensemble_size))
        self.conditionalCheck.setChecked(self.ctx.conditional_check)
        # Threshold usually not in PAR, keep UI value or default

        # Update input file label if ctx has it (from PAR)
        if self.ctx.in_file:
             self.inputFileLabel.setText(self.ctx.in_file)
        else:
             self.inputFileLabel.setText("No file selected") # Ensure label reset if PAR had no data file

    def update_progress(self, value, text):
        """Slot to update the progress bar and label."""
        self.progressBar.setValue(value)
        self.progressLabel.setText(text)
        QApplication.processEvents() # Keep UI responsive

    # --- Validation Methods (Simplified examples) ---
    def validate_start_date(self):
        try:
            date_obj = datetime.datetime.strptime(self.startDateInput.text(), "%d/%m/%Y").date()
            self.ctx.start_date = date_obj
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Invalid start date format. Use DD/MM/YYYY.")
            self.startDateInput.setText(self.ctx.start_date.strftime("%d/%m/%Y")) # Revert

    def validate_ensemble_size(self):
        try:
            val = int(self.ensembleSizeInput.text())
            if 1 <= val <= 100: # VB limit check
                self.ctx.ensemble_size = val
            else:
                raise ValueError("Value out of range")
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Ensemble size must be an integer between 1 and 100.")
            self.ensembleSizeInput.setText(str(self.ctx.ensemble_size)) # Revert

    def validate_threshold(self):
        try:
            val = float(self.thresholdInput.text())
            # Add range check if needed (VB used -100 to 100)
            self.ctx.local_thresh = val
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Invalid threshold value. Must be a number.")
            self.thresholdInput.setText(str(self.ctx.local_thresh)) # Revert

    def validate_occurrence(self):
        try:
            val = float(self.occFactorInput.text())
            # VB range check: -99 to 100
            if -99.0 <= val <= 100.0:
                self.ctx.occurrence_factor = val
                self.ctx.occurrence_factor_percent = (100.0 + val) / 100.0
            else:
                 raise ValueError("Value out of range")
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Occurrence factor must be a number between -99 and 100.")
            self.occFactorInput.setText(str(self.ctx.occurrence_factor)) # Revert

    def validate_amount(self):
        try: # Factor
            val = float(self.amountFactorInput.text())
            # VB range check: -100 to 100
            if -100.0 <= val <= 100.0:
                self.ctx.amount_factor = val
                self.ctx.amount_factor_percent = (100.0 + val) / 100.0
            else:
                 raise ValueError("Value out of range")
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Amount factor must be a number between -100 and 100.")
            self.amountFactorInput.setText(str(self.ctx.amount_factor)) # Revert
        try: # Addition
            val = float(self.amountAddInput.text())
             # VB range check: -100 to 100
            if -100.0 <= val <= 100.0:
                self.ctx.amount_addition = val
            else:
                 raise ValueError("Value out of range")
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Amount addition must be a number between -100 and 100.")
            self.amountAddInput.setText(str(self.ctx.amount_addition)) # Revert

    def validate_variance(self):
        try:
            val = float(self.varianceFactorInput.text())
             # VB range check: -100000 to 100000 (very wide)
            if -100000.0 <= val <= 100000.0:
                self.ctx.variance_factor = val
                self.ctx.variance_factor_percent = (100.0 + val) / 100.0
                if self.ctx.variance_factor_percent < 0: # Variance ratio cannot be negative
                    raise ValueError("Resulting variance factor cannot be negative")
            else:
                 raise ValueError("Value out of range")
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Variance factor must be a number, resulting in a non-negative variance multiplier (e.g., >= -100).")
            self.varianceFactorInput.setText(str(self.ctx.variance_factor)) # Revert

    def validate_trend(self):
        try: # Linear
            val = float(self.trendLinearInput.text())
             # VB range check: -100 to 100
            if -100.0 <= val <= 100.0:
                self.ctx.linear_trend = val
            else: raise ValueError("Value out of range")
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Linear trend must be a number between -100 and 100.")
            self.trendLinearInput.setText(str(self.ctx.linear_trend)) # Revert
        try: # Exponential
            val = float(self.trendExpInput.text())
            if abs(val) < 1e-9 : # VB check: cannot be zero
                QMessageBox.warning(self, "Input Error", "Exponential trend factor cannot be zero.")
                self.trendExpInput.setText(str(self.ctx.exp_trend)) # Revert
            else:
                 self.ctx.exp_trend = val
                 self.ctx.add_exp_option = val > 0
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Exponential trend must be a non-zero number.")
            self.trendExpInput.setText(str(self.ctx.exp_trend)) # Revert
        try: # Logistic
            val = float(self.trendLogInput.text())
             # VB range check: -100 to 100
            if -100.0 <= val <= 100.0:
                self.ctx.logistic_trend = val
            else: raise ValueError("Value out of range")
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Logistic trend must be a number between -100 and 100.")
            self.trendLogInput.setText(str(self.ctx.logistic_trend)) # Revert


    # --- Main Execution ---
    def run_generation(self):
        """Orchestrates the scenario generation process."""
        # 1. Final validation of all inputs from UI -> context
        self.validate_start_date()
        self.validate_ensemble_size()
        self.validate_threshold()
        self.validate_occurrence()
        self.validate_amount()
        self.validate_variance()
        self.validate_trend()
        # Ensure radio button choices are reflected in ctx (should be via signals)
        self.ctx.occurrence_option = self.occOptionGroup.checkedId()
        self.ctx.amount_option = self.amountOptionGroup.checkedId()
        self.ctx.trend_option = self.trendOptionGroup.checkedId()
        # Ensure checkbox states are reflected
        self.ctx.conditional_check = self.conditionalCheck.isChecked()
        self.ctx.occurrence_check = self.occurrenceCheck.isChecked()
        self.ctx.preserve_totals_check = self.preserveTotalsCheck.isChecked()
        self.ctx.amount_check = self.amountCheck.isChecked()
        self.ctx.variance_check = self.varianceCheck.isChecked()
        self.ctx.trend_check = self.trendCheck.isChecked()


        # 2. Check settings consistency
        if not check_settings(self.ctx, self):
            return # Stop if basic settings are wrong

        # 3. Prepare for processing
        mini_reset(self.ctx) # Reset error flags
        self.progressBar.setVisible(True)
        self.progressLabel.setVisible(True)
        self.update_progress(0, "Starting...")
        self.generateButton.setEnabled(False)
        self.resetButton.setEnabled(False)

        # 4. Read Input Data
        if not read_input_file(self.ctx, self.update_progress):
            self.update_progress(0, "Error during file reading.")
            self.generateButton.setEnabled(True)
            self.resetButton.setEnabled(True)
            return

        # 5. Apply Treatments (check error_occurred after each step)
        if self.ctx.occurrence_check and not self.ctx.error_occurred:
            apply_occurrence(self.ctx, self.update_progress)

        # Variance needs means, calculate them if Variance is checked
        if self.ctx.variance_check and not self.ctx.error_occurred:
            calc_means(self.ctx, self.update_progress)

        if self.ctx.amount_check and not self.ctx.error_occurred:
            apply_amount(self.ctx, self.update_progress)

        if self.ctx.variance_check and not self.ctx.error_occurred:
            if not self.ctx.mean_array: # Ensure means were calculated
                 QMessageBox.critical(self,"Internal Error", "Means not calculated before variance step.")
                 self.ctx.error_occurred = True
            else:
                 apply_variance(self.ctx, self.update_progress)

        if self.ctx.trend_check and not self.ctx.error_occurred:
            apply_trend(self.ctx, self.update_progress)

        # 6. Write Output File
        success = False
        if not self.ctx.error_occurred:
            if write_output_file(self.ctx, self.update_progress):
                success = True

        # 7. Finalize
        self.generateButton.setEnabled(True)
        self.resetButton.setEnabled(True)

        if success:
            self.update_progress(100, "Scenario Generation Complete.")
            msg = f"Scenario Generated.\n{self.ctx.no_of_days} days processed."
            if self.ctx.variance_check and self.ctx.conditional_check and abs(self.ctx.lamda - GLOBAL_MISSING_CODE) > 1e-6 :
                 msg += f"\nLambda for BoxCox transform: {self.ctx.lamda:.3f}"
            QMessageBox.information(self, "Results", msg)
        elif self.ctx.error_occurred:
            self.update_progress(0, "Processing failed.")
        else:
            self.update_progress(0, "Processing cancelled or failed silently.")


###############################################################################
# 5. Main Application Entry Point / Module Export
###############################################################################
ContentWidget = ScenarioGeneratorWidget # Alias for dynamic loading

def main():
    app = QApplication(sys.argv)
    window = ScenarioGeneratorWidget()
    window.setWindowTitle("SDSM Scenario Generator")
    window.setGeometry(100, 100, 750, 650) # Adjusted size
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()