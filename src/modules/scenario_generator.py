import sys
import os
import math
import random
import datetime
import statistics

from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QGridLayout, QCheckBox, QRadioButton,
                             QButtonGroup, QFileDialog, QGroupBox, QMessageBox, QProgressBar,
                             QStyle) # Import QStyle for icons
from PyQt5.QtCore import Qt, QTimer

# --- Default Values ---
# Used when no specific values are provided by the user
GLOBAL_MISSING_CODE = -999.0  # Value that indicates missing data
DEFAULT_THRESHOLD = 0.0       # Default threshold for wet/dry day separation
DEFAULT_START_DATE = datetime.date(2000, 1, 1)  # Default starting date
DEFAULT_YEAR_INDICATOR = 365  # Default days in year (non-leap year)

# Random number generator that mimics VB's Rnd() function
# Returns a random number between 0 and 1
def Rnd():
    return random.random()

# Global date variables for tracking current date during processing
g_dd = 0   # Day
g_mm = 0   # Month
g_yyyy = 0 # Year

#############################################################
# Main class to store all parameters and data for processing
#############################################################
class SDSMContext:
    def __init__(self):
        self.reset()

    def reset(self):
        # File paths
        self.in_file = ""     # Input filename (without path)
        self.in_root = ""     # Full path to input file
        self.out_file = ""    # Output filename (without path)
        self.out_root = ""    # Full path to output file

        # Basic parameters
        self.start_date = DEFAULT_START_DATE  # Starting date of data series
        self.local_thresh = DEFAULT_THRESHOLD # Threshold for wet/dry day separation
        self.ensemble_size = 1                # Number of data columns (scenarios)
        self.no_of_days = 0                   # Total number of days in the data
        self.year_indicator = DEFAULT_YEAR_INDICATOR # Days in a year setting
        self.year_length = 365                # Standard year length

        # Data storage
        self.data_array = []   # Main array to store data [ensemble][day]
        self.mean_array = []   # Stores mean and SD values for each ensemble

        # Treatment options
        # Occurrence settings (frequency of wet/dry days)
        self.occurrence_check = False         # Whether to apply occurrence treatment
        self.conditional_check = False        # If true, only values > threshold are modified
        self.occurrence_factor = 0.0          # User input value (e.g., 5 for +5%)
        self.occurrence_factor_percent = 1.0  # Actual multiplier (e.g., 1.05 for +5%)
        self.occurrence_option = 0            # 0 = Stochastic, 1 = Forced
        self.preserve_totals_check = False    # Whether to maintain total rainfall

        # Amount settings (magnitude of values)
        self.amount_check = False             # Whether to apply amount treatment
        self.amount_option = 0                # 0 = factor (multiply), 1 = addition (add)
        self.amount_factor = 0.0              # User input value (e.g., 5 for +5%)
        self.amount_factor_percent = 1.0      # Actual multiplier (e.g., 1.05 for +5%)
        self.amount_addition = 0              # Amount to add (if using addition option)

        # Variance settings (spread of values)
        self.variance_check = False           # Whether to apply variance treatment
        self.variance_factor = 0.0            # User input value (e.g., 10 for +10%)
        self.variance_factor_percent = 1.0    # Target variance ratio (e.g., 1.10 for +10%)

        # Trend settings (changes over time)
        self.trend_check = False              # Whether to apply trend treatment
        self.linear_trend = 0.0               # Linear trend amount
        self.exp_trend = 1.0                  # Exponential trend factor
        self.logistic_trend = 1.0             # Logistic trend factor
        self.trend_option = 0                 # 0 = Linear, 1 = Exponential, 2 = Logistic
        self.add_exp_option = True            # Whether trend is positive or negative

        self.lamda = 0.0                      # Box-Cox transform parameter

        # Processing state
        self.error_occurred = False           # Flag for error handling
        self.global_kop_out = False           # Flag to stop processing (like Escape key)

        # PAR-file related settings
        self.num_predictors = 0               # Number of predictors in PAR file
        self.num_months = 12                  # Number of months (usually 12)
        self.monthly_coeffs = []              # Monthly coefficients from PAR file
        self.predictor_files = []             # Predictor files from PAR file
        self.bias_correction = 0.8            # Default bias correction factor
        self.zom = [0.0] * 12                 # Monthly occurrence percentages for forced mode

#############################################################
# Helper Functions
#############################################################

# Check if a year is a leap year
def is_leap(year):
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

# Get the number of days in a specific month
def days_in_month(year, month):
    if month == 2:
        return 29 if is_leap(year) else 28
    elif month in [4, 6, 9, 11]:
        return 30
    else:
        return 31

# Move the global date forward by one day
def increase_date(ctx=None):
    global g_dd, g_mm, g_yyyy
    
    g_dd += 1  # Increase day

    # Check if we need to move to next month
    if ctx and ctx.year_length == 1 and g_mm == 2 and is_leap(g_yyyy):
        days_current_month = 29  # Special case for leap year February
    else:
        days_current_month = days_in_month(g_yyyy, g_mm)

    if g_dd > days_current_month:
        g_mm += 1  # Move to next month
        g_dd = 1   # Reset day to 1

    if g_mm == 13:
        g_mm = 1       # Reset to January
        g_yyyy += 1    # Increase year

# Convert a string to a floating-point value
# Returns GLOBAL_MISSING_CODE for invalid or missing values
def parse_value(str_val):
    val_str = str_val.strip()
    try:
        val = float(val_str)
        # Check if the value represents a missing code
        if abs(val - GLOBAL_MISSING_CODE) < 1e-6:
            return GLOBAL_MISSING_CODE
        return val
    except ValueError:
        return GLOBAL_MISSING_CODE

# Format a value for writing to output file
# Handles missing values and formatting
def format_value_output(value):
    if abs(value - GLOBAL_MISSING_CODE) < 1e-6:
        # Output tab for missing values
        return "\t"
    else:
        # Format with 3 decimal places, 8 characters wide, right-aligned
        return f"{value:8.3f}\t"

# Check if user settings are valid
# Returns True if all settings are acceptable, False otherwise
def check_settings(ctx: SDSMContext, parent_widget=None) -> bool:
    all_ok = True
    
    # Check if input file is selected
    if not ctx.in_file or len(ctx.in_file) < 1:
        QMessageBox.critical(parent_widget, "Error", "You must select an input file first.")
        all_ok = False
    
    # Check if output file is specified
    elif not ctx.out_file:
        QMessageBox.critical(parent_widget, "Error", "You must enter a filename to save results to.")
        all_ok = False
    
    # Check if at least one treatment is selected
    elif not (ctx.occurrence_check or ctx.amount_check or ctx.trend_check or ctx.variance_check):
        QMessageBox.critical(parent_widget, "Error", "You must select at least one treatment.")
        all_ok = False
    
    # Check if occurrence treatment has conditional processing enabled
    elif ctx.occurrence_check and not ctx.conditional_check:
        QMessageBox.critical(parent_widget, "Error", "You cannot perform an occurrence treatment on data that are unconditional.")
        all_ok = False
    
    # Check amount settings
    elif ctx.amount_check and ctx.amount_option == 0 and abs(ctx.amount_factor_percent - 1.0) < 1e-6:
        QMessageBox.critical(parent_widget, "Error", "You are trying to apply an amount treatment (Factor) but applying no change (0%).")
        all_ok = False
    elif ctx.amount_check and ctx.amount_option == 1 and abs(ctx.amount_addition) < 1e-6:
         QMessageBox.critical(parent_widget, "Error", "You are trying to apply an amount treatment (Addition) but applying no change (0).")
         all_ok = False
    
    # Check occurrence settings
    elif ctx.occurrence_check and ctx.occurrence_option == 0 and abs(ctx.occurrence_factor_percent - 1.0) < 1e-6:
        QMessageBox.critical(parent_widget, "Error", "You are trying to perform an occurrence treatment (Factor) but applying zero frequency change.")
        all_ok = False
    
    # Check variance settings
    elif ctx.variance_check and abs(ctx.variance_factor_percent - 1.0) < 1e-6:
         QMessageBox.critical(parent_widget, "Error", "You are trying to apply a variance change but have not entered an amount (0%).")
         all_ok = False
    
    # Check trend settings
    elif ctx.trend_check and ctx.trend_option == 0 and abs(ctx.linear_trend) < 1e-9:
        QMessageBox.critical(parent_widget, "Error", "Linear trend is selected, but the value is zero.")
        all_ok = False
    elif ctx.trend_check and ctx.trend_option == 1 and abs(ctx.exp_trend) < 1e-9:
        QMessageBox.critical(parent_widget, "Error", "Exponential trend is selected, but the value (factor) is effectively 1 (or zero if referring to additive effect).")
        all_ok = False
    elif ctx.trend_check and ctx.trend_option == 2 and abs(ctx.logistic_trend) < 1e-9:
        QMessageBox.critical(parent_widget, "Error", "Logistic trend is selected, but the value (factor) is effectively 1 (or zero if referring to additive effect).")
        all_ok = False

    return all_ok

# Reset error flags before starting a new operation
def mini_reset(ctx: SDSMContext):
    ctx.error_occurred = False
    ctx.global_kop_out = False

#############################################################
# Core Functions for Scenario Generation
#############################################################

# Read and parse the input data file
def read_input_file(ctx: SDSMContext, progress_callback=None):
    try:
        # Open and read the file
        with open(ctx.in_root, "r") as f:
            lines = f.readlines()
    except Exception as e:
        QMessageBox.critical(None, "File Read Error", f"Error reading input file:\n{e}")
        ctx.error_occurred = True
        return False

    # Check if file is empty
    if not lines:
        QMessageBox.critical(None, "File Read Error", "Input file is empty.")
        ctx.error_occurred = True
        return False

    # Set number of days from file length
    ctx.no_of_days = len(lines)
    
    # Warn if file is very large
    if ctx.no_of_days > 75000:
         QMessageBox.warning(None, "Warning", f"Input file has {ctx.no_of_days} days, which exceeds the typical limit (around 75000). Processing will continue, but may be slow or unstable.")

    # Initialize data array for each ensemble
    ctx.data_array = [[] for _ in range(ctx.ensemble_size)]
    expected_columns = ctx.ensemble_size

    # Process each line in the file
    for i, line in enumerate(lines):
        # Check for user cancellation
        if ctx.global_kop_out: 
            return False
        
        # Update progress if callback provided
        if progress_callback:
            progress_callback(int(i / ctx.no_of_days * 100), "Reading Data")

        # Split line into columns
        parts = line.split()
        actual_columns = len(parts)

        # Check if first line has enough columns
        if i == 0 and actual_columns < expected_columns:
            QMessageBox.critical(None, "File Format Error",
                                 f"Data file seems to have fewer columns ({actual_columns}) than the specified Ensemble Size ({expected_columns}).\nPlease check the input file and Ensemble Size setting.")
            ctx.error_occurred = True
            return False
        # Handle lines with fewer columns
        elif actual_columns < expected_columns:
            parsed_vals = [parse_value(p) for p in parts]
            parsed_vals.extend([GLOBAL_MISSING_CODE] * (expected_columns - actual_columns))
        else:
            # Parse values from the line
            parsed_vals = [parse_value(parts[j]) for j in range(expected_columns)]

        # Store values in data array
        for ens_j in range(expected_columns):
             ctx.data_array[ens_j].append(parsed_vals[ens_j])

    # Update progress to complete
    if progress_callback: 
        progress_callback(100, "Reading Data Complete")
    
    return True


# Apply occurrence treatment to modify frequency of wet days
def apply_occurrence(ctx: SDSMContext, progress_callback=None):
    global g_dd, g_mm, g_yyyy

    # Verify conditional processing is enabled (required for occurrence)
    if not ctx.conditional_check:
        QMessageBox.critical(None, "Logic Error", "Occurrence treatment requires conditional process.")
        ctx.error_occurred = True
        return

    # Initialize random seed for reproducibility
    random.seed()
    given_zero_warning = False

    # Process each ensemble
    for j in range(ctx.ensemble_size):
        # Check for user cancellation
        if ctx.global_kop_out: 
            return
        
        # Update progress
        if progress_callback:
            progress_callback(int(j / ctx.ensemble_size * 100), f"Applying Occurrence Ensemble {j+1}")

        # Initialize monthly counts and arrays
        dry_count = [0] * 12         # Count of dry days per month
        wet_count = [0] * 12         # Count of wet days per month
        day_count = [0] * 12         # Total non-missing days per month
        wet_array = [[] for _ in range(12)]  # Indices of wet days for each month
        dry_array = [[] for _ in range(12)]  # Indices of dry days for each month
        prop_wet_array = [0.0] * 12  # Proportion of wet days per month
        prop_dry_array = [0.0] * 12  # Proportion of dry days per month
        total_rainfall = 0.0         # Sum of rainfall values
        total_wet_count = 0          # Total wet days across all months

        # First pass: count wet/dry days and collect their indices
        g_dd = ctx.start_date.day
        g_mm = ctx.start_date.month
        g_yyyy = ctx.start_date.year

        for i in range(ctx.no_of_days):
            val = ctx.data_array[j][i]
            m = g_mm - 1  # Convert to 0-based month index

            # Process non-missing values
            if val != GLOBAL_MISSING_CODE:
                day_count[m] += 1
                
                # Check if day is wet (above threshold)
                if val > ctx.local_thresh:
                    wet_count[m] += 1
                    wet_array[m].append(i)  # Store day index
                    total_rainfall += val
                    total_wet_count += 1
                else:
                    dry_count[m] += 1
                    dry_array[m].append(i)  # Store day index

            # Move to next day
            increase_date(ctx)

        # Save original wet count for reference
        original_wet_count = wet_count[:]

        # Calculate wet and dry proportions for each month
        for m in range(12):
            sum_days = day_count[m]
            if sum_days > 0:
                prop_wet_array[m] = wet_count[m] / sum_days
                prop_dry_array[m] = dry_count[m] / sum_days
            else:
                # Mark as missing if no days in this month
                prop_wet_array[m] = GLOBAL_MISSING_CODE
                prop_dry_array[m] = GLOBAL_MISSING_CODE

        # Check if data contains any wet days
        if total_wet_count <= 0:
            if not given_zero_warning:
                msg = f"Warning - Ensemble {j+1} has zero rainfall days and cannot be manipulated by occurrence treatment."
                if ctx.ensemble_size == 1:
                    msg = "Warning - there are zero rainfall days available so the data cannot be manipulated by occurrence treatment."
                QMessageBox.warning(None, "Results", msg)
                given_zero_warning = True
            continue  # Skip to next ensemble

        # Apply occurrence modification based on selected option
        # Option 0: Stochastic Factor Adjustment
        if ctx.occurrence_option == 0:
            if ctx.occurrence_factor_percent < 1.0:
                # REMOVING WET DAYS
                days_to_delete = round(total_wet_count - (total_wet_count * ctx.occurrence_factor_percent))
                if days_to_delete <= 0:
                    continue  # No days to delete

                # Build probability distribution based on dryness
                # (higher probability to remove from drier months)
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
                        
                # Skip if no months available for selection
                if cum_prop_sum[11] == 0.0:
                    continue

                # Delete the required number of wet days
                for _ in range(days_to_delete):
                    # Select a month based on dryness probability
                    selected_month = -1
                    random_no = Rnd() * cum_prop_sum[11]

                    for i in range(12):
                        if random_no < cum_prop_sum[i]:
                            selected_month = i
                            break

                    if selected_month == -1:
                        selected_month = 11

                    # Find a month with wet days (if selected has none)
                    attempts = 0
                    while wet_count[selected_month] <= 0 and attempts < 12:
                        selected_month = (selected_month + 1) % 12
                        attempts += 1

                    if wet_count[selected_month] <= 0:
                        # Try to find any month with wet days
                        found_wet_month = False
                        for m_idx in range(12):
                            if wet_count[m_idx] > 0:
                                selected_month = m_idx
                                found_wet_month = True
                                break
                        if not found_wet_month:
                            continue  # No wet days left anywhere

                    # Select a random wet day from the chosen month
                    wet_day_list_index = int(Rnd() * wet_count[selected_month])
                    day_index_to_modify = wet_array[selected_month][wet_day_list_index]

                    # Set the day to dry (threshold value)
                    ctx.data_array[j][day_index_to_modify] = ctx.local_thresh

                    # Update the wet and dry arrays
                    if wet_day_list_index < wet_count[selected_month] - 1:
                        wet_array[selected_month][wet_day_list_index] = wet_array[selected_month][-1]
                    wet_array[selected_month].pop()
                    dry_array[selected_month].append(day_index_to_modify)

                    # Update counts
                    wet_count[selected_month] -= 1
                    dry_count[selected_month] += 1
                    total_wet_count -= 1

            elif ctx.occurrence_factor_percent > 1.0:
                # ADDING WET DAYS
                days_to_add = round((total_wet_count * ctx.occurrence_factor_percent) - total_wet_count)
                spaces_available = ctx.no_of_days - total_wet_count
                
                # Check if we have enough dry days to convert
                if days_to_add > spaces_available:
                    QMessageBox.critical(None, "Error Message", 
                                        f"Ensemble {j+1}: You cannot add that many wet days ({days_to_add}) as there are only {spaces_available} dry/missing days available.")
                    ctx.error_occurred = True
                    return

                if days_to_add <= 0:
                    continue  # No days to add

                # Build probability distribution based on wetness
                # (higher probability to add to wetter months)
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
                        
                # Skip if no months available for selection
                if cum_prop_sum[11] == 0.0:
                    continue

                # Add the required number of wet days
                for _ in range(days_to_add):
                    # Select a month based on wetness probability
                    selected_month = -1
                    random_no = Rnd() * cum_prop_sum[11]

                    for i in range(12):
                        if random_no < cum_prop_sum[i]:
                            selected_month = i
                            break

                    if selected_month == -1:
                        selected_month = 11

                    # Find a month with dry days (if selected has none)
                    attempts = 0
                    while dry_count[selected_month] <= 0 and attempts < 12:
                        selected_month = (selected_month + 1) % 12
                        attempts += 1

                    if dry_count[selected_month] <= 0:
                        # Try to find any month with dry days
                        found_dry_month = False
                        for m_idx in range(12):
                            if dry_count[m_idx] > 0:
                                selected_month = m_idx
                                found_dry_month = True
                                break
                        if not found_dry_month:
                            continue  # No dry days left anywhere

                    # Select a random dry day to convert to wet
                    dry_day_list_index = int(Rnd() * dry_count[selected_month])
                    day_index_to_modify = dry_array[selected_month][dry_day_list_index]

                    # Find a wet day value to use as template
                    source_wet_day_value = GLOBAL_MISSING_CODE

                    # Try to use a wet day from the same month if available
                    if wet_count[selected_month] > 0:
                        source_wet_day_index_in_list = int(Rnd() * wet_count[selected_month])
                        source_day_index = wet_array[selected_month][source_wet_day_index_in_list]
                        source_wet_day_value = ctx.data_array[j][source_day_index]
                    # If no wet day in this month, search nearby months
                    elif original_wet_count[selected_month] > 0:
                        pass  # This branch is likely redundant

                    # If still no wet day found, search other months
                    if source_wet_day_value == GLOBAL_MISSING_CODE:
                        search_order = set_random_array(selected_month)
                        for neighbor_month in search_order:
                            if wet_count[neighbor_month] > 0:
                                source_wet_day_index_in_list = int(Rnd() * wet_count[neighbor_month])
                                source_day_index = wet_array[neighbor_month][source_wet_day_index_in_list]
                                source_wet_day_value = ctx.data_array[j][source_day_index]
                                break

                    # Apply the wet day value if we found one
                    if source_wet_day_value != GLOBAL_MISSING_CODE:
                        ctx.data_array[j][day_index_to_modify] = source_wet_day_value

                        # Update arrays
                        if dry_day_list_index < dry_count[selected_month] - 1:
                            dry_array[selected_month][dry_day_list_index] = dry_array[selected_month][-1]
                        dry_array[selected_month].pop()
                        wet_array[selected_month].append(day_index_to_modify)

                        # Update counts
                        dry_count[selected_month] -= 1
                        wet_count[selected_month] += 1
                        total_wet_count += 1

        # Option 1: Forced Percentage
        elif ctx.occurrence_option == 1:
            # Check if target percentages are set
            if not hasattr(ctx, 'zom') or len(ctx.zom) != 12:
                QMessageBox.critical(None, "Error", "Forced occurrence requires target percentages (ZoM) for each month, which are not set.")
                ctx.error_occurred = True
                return

            # Process each month
            for m in range(12):
                if day_count[m] <= 0:
                    continue  # Skip months with no data

                # Calculate target number of wet days
                target_percentage = ctx.zom[m] / 100.0
                target_wet_count = round(target_percentage * day_count[m])
                current_wet_count_month = wet_count[m]

                if current_wet_count_month > target_wet_count:
                    # REMOVING WET DAYS
                    days_to_delete = current_wet_count_month - target_wet_count
                    for _ in range(days_to_delete):
                        if wet_count[m] <= 0:
                            break
                        # Select random wet day to convert to dry
                        wet_day_list_index = int(Rnd() * wet_count[m])
                        day_index_to_modify = wet_array[m][wet_day_list_index]
                        ctx.data_array[j][day_index_to_modify] = ctx.local_thresh

                        # Update arrays
                        if wet_day_list_index < wet_count[m] - 1:
                            wet_array[m][wet_day_list_index] = wet_array[m][-1]
                        wet_array[m].pop()
                        dry_array[m].append(day_index_to_modify)

                        # Update counts
                        wet_count[m] -= 1
                        dry_count[m] += 1
                        total_wet_count -= 1

                elif current_wet_count_month < target_wet_count:
                    # ADDING WET DAYS
                    days_to_add = target_wet_count - current_wet_count_month
                    for _ in range(days_to_add):
                        if dry_count[m] <= 0:
                            break  # No more dry days to convert
                            
                        # Select random dry day to convert to wet
                        dry_day_list_index = int(Rnd() * dry_count[m])
                        day_index_to_modify = dry_array[m][dry_day_list_index]

                        # Find a wet day value to use as template
                        source_wet_day_value = GLOBAL_MISSING_CODE
                        
                        # Try to use a wet day from the same month if available
                        if wet_count[m] > 0:
                            source_wet_day_index_in_list = int(Rnd() * wet_count[m])
                            source_day_index = wet_array[m][source_wet_day_index_in_list]
                            source_wet_day_value = ctx.data_array[j][source_day_index]
                        # If no wet day in this month, search nearby months
                        else:
                            search_order = set_random_array(m)
                            for neighbor_month in search_order:
                                if wet_count[neighbor_month] > 0:
                                    source_wet_day_index_in_list = int(Rnd() * wet_count[neighbor_month])
                                    source_day_index = wet_array[neighbor_month][source_wet_day_index_in_list]
                                    source_wet_day_value = ctx.data_array[j][source_day_index]
                                    break

                        # Apply the wet day value if we found one
                        if source_wet_day_value != GLOBAL_MISSING_CODE:
                            ctx.data_array[j][day_index_to_modify] = source_wet_day_value

                            # Update arrays
                            if dry_day_list_index < dry_count[m] - 1:
                                dry_array[m][dry_day_list_index] = dry_array[m][-1]
                            dry_array[m].pop()
                            wet_array[m].append(day_index_to_modify)

                            # Update counts
                            dry_count[m] -= 1
                            wet_count[m] += 1
                            total_wet_count += 1

        # Preserve totals if requested
        if ctx.preserve_totals_check:
            # Calculate new total rainfall
            new_total_rainfall = 0.0
            new_total_wet_days = 0
            for i in range(ctx.no_of_days):
                val = ctx.data_array[j][i]
                if val != GLOBAL_MISSING_CODE and val > ctx.local_thresh:
                    new_total_rainfall += val
                    new_total_wet_days += 1

            # Scale rainfall to match original total
            if new_total_rainfall > 1e-9 and total_rainfall > 1e-9 and new_total_wet_days > 0:
                rainfall_multiplier = total_rainfall / new_total_rainfall
                if abs(rainfall_multiplier - 1.0) > 1e-6:  # Only apply if change is significant
                    for i in range(ctx.no_of_days):
                        if ctx.data_array[j][i] != GLOBAL_MISSING_CODE and ctx.data_array[j][i] > ctx.local_thresh:
                            # Apply multiplier but keep values above threshold
                            new_val = ctx.data_array[j][i] * rainfall_multiplier
                            ctx.data_array[j][i] = max(ctx.local_thresh + 1e-6, new_val)

    # Update progress to complete
    if progress_callback:
        progress_callback(100, "Applying Occurrence Complete")


# Generate a random sequence of months around a selected month
def set_random_array(selected_month):
    # Randomly decide direction of search (forward or backward)
    multiplier = 1 if Rnd() < 0.5 else -1
    temp_array = [0] * 11  # For 11 other months
    idx = 0
    
    # Create offsets from the selected month
    for i in range(1, 7):  # Offsets 1 to 6
        # Add months in alternating directions
        if idx < 11:
            temp_array[idx] = multiplier * i
            idx += 1
        if idx < 11 and i <= 5:  # Offsets in opposite direction
            temp_array[idx] = -multiplier * i
            idx += 1

    # Convert offsets to actual month indices (0-11)
    random_array = [0] * 11
    for i in range(11):
        month_val = temp_array[i] + (selected_month + 1)  # Convert to 1-based
        # Wrap around the year
        if month_val > 12:
            month_val -= 12
        elif month_val < 1:
             month_val += 12
        random_array[i] = month_val - 1  # Convert back to 0-based
    
    return random_array


# Calculate mean and standard deviation for each ensemble
def calc_means(ctx: SDSMContext, progress_callback=None):
    ctx.mean_array = []  # Reset array
    
    # Process each ensemble
    for j in range(ctx.ensemble_size):
        # Check for user cancellation
        if ctx.global_kop_out:
            return
            
        # Update progress
        if progress_callback:
             progress_callback(int(j / ctx.ensemble_size * 50), f"Calculating Mean/SD {j+1}")

        # Collect valid values for statistics
        values_for_stats = []
        for i in range(ctx.no_of_days):
            val = ctx.data_array[j][i]
            if val != GLOBAL_MISSING_CODE:
                # If conditional, only include values above threshold
                if not ctx.conditional_check or (ctx.conditional_check and val > ctx.local_thresh):
                    values_for_stats.append(val)

        # Calculate statistics
        mean = GLOBAL_MISSING_CODE
        sd = GLOBAL_MISSING_CODE
        count = len(values_for_stats)

        if count > 0:
            # Calculate mean
            mean = sum(values_for_stats) / count
            
            # Calculate standard deviation
            if count > 1:  # Need at least 2 points for SD
                variance = sum([(x - mean) ** 2 for x in values_for_stats]) / count
                sd = math.sqrt(variance)
            else:
                sd = 0.0  # SD is 0 if only one point

        # Store results
        ctx.mean_array.append({'mean': mean, 'sd': sd})

    # Update progress to complete
    if progress_callback:
        progress_callback(100, "Calculating Mean/SD Complete")


# Apply amount treatment to modify the magnitude of values
def apply_amount(ctx: SDSMContext, progress_callback=None):
    # Process each ensemble
    for j in range(ctx.ensemble_size):
        # Check for user cancellation
        if ctx.global_kop_out:
            return
            
        # Update progress
        if progress_callback:
             progress_callback(int(j / ctx.ensemble_size * 100), f"Applying Amount {j+1}")

        # Option 0: Apply factor (multiply by percentage)
        if ctx.amount_option == 0:
            # Skip if factor is 1.0 (no change)
            if abs(ctx.amount_factor_percent - 1.0) < 1e-6:
                continue
                
            # Process each day
            for i in range(ctx.no_of_days):
                val = ctx.data_array[j][i]
                if val != GLOBAL_MISSING_CODE:
                    # Check if value should be modified (conditional)
                    if not ctx.conditional_check or (ctx.conditional_check and val > ctx.local_thresh):
                        # Apply factor
                        new_val = val * ctx.amount_factor_percent
                        
                        # Handle threshold for conditional processing
                        if ctx.conditional_check and val > ctx.local_thresh and new_val <= ctx.local_thresh:
                            # Keep values above threshold if they started that way
                            ctx.data_array[j][i] = ctx.local_thresh + 1e-6
                        elif not ctx.conditional_check and val <= ctx.local_thresh and new_val <= ctx.local_thresh:
                            # For unconditional, if dry day becomes "more dry", keep original
                            ctx.data_array[j][i] = val
                        else:
                            ctx.data_array[j][i] = new_val
        
        # Option 1: Apply addition (add value)
        else:
            # Skip if addition is 0
            if abs(ctx.amount_addition) < 1e-6:
                continue
                
            # Process each day
            for i in range(ctx.no_of_days):
                val = ctx.data_array[j][i]
                if val != GLOBAL_MISSING_CODE:
                    # Check if value should be modified (conditional)
                    if not ctx.conditional_check or (ctx.conditional_check and val > ctx.local_thresh):
                        # Apply addition
                        new_val = val + ctx.amount_addition
                        
                        # Handle threshold for conditional processing
                        if ctx.conditional_check and val > ctx.local_thresh and new_val <= ctx.local_thresh:
                            # Keep values above threshold if they started that way
                            ctx.data_array[j][i] = ctx.local_thresh + 1e-6
                        elif not ctx.conditional_check and val <= ctx.local_thresh and new_val <= ctx.local_thresh:
                            # Apply addition even if it makes dry days "more dry"
                            ctx.data_array[j][i] = new_val
                        else:
                            ctx.data_array[j][i] = new_val

    # Update progress to complete
    if progress_callback:
        progress_callback(100, "Applying Amount Complete")


# Find the optimal lambda value for Box-Cox transformation
def find_min_lambda(ctx: SDSMContext, ensemble: int, start: float, finish: float, step: float) -> float:
    best_lam = start
    min_abs_d = float('inf')

    # Try different lambda values
    k = start
    while k <= finish + 1e-9:  # Add tolerance for float comparison
        temp_array = []
        
        # Apply Box-Cox transform to valid data points
        for i in range(ctx.no_of_days):
            val = ctx.data_array[ensemble][i]
            
            # Only transform valid values above threshold
            if val != GLOBAL_MISSING_CODE and val > ctx.local_thresh:
                # Skip zero values even if above a negative threshold
                if abs(val) < 1e-9:
                    if ctx.local_thresh >= 0:
                        continue
                
                try:
                    # Apply Box-Cox transform
                    if abs(k) < 1e-9:  # Lambda is zero -> log transform
                        transformed_val = math.log(val)
                    else:  # Standard Box-Cox
                        transformed_val = (val ** k - 1) / k
                    temp_array.append(transformed_val)
                except (ValueError, OverflowError):
                    continue

        # Need enough points for meaningful statistics
        count = len(temp_array)
        if count > 10:
            # Calculate mean and median
            mean_val = sum(temp_array) / count
            temp_array.sort()
            median_val = statistics.median(temp_array)

            # Calculate quartiles and IQR
            q1_idx = int(count * 0.25)
            q3_idx = int(count * 0.75)
            if q3_idx >= count:
                q3_idx = count - 1  # Ensure valid index

            if q1_idx < q3_idx:  # Ensure at least 2 distinct points for Q1 and Q3
                q1 = temp_array[q1_idx]
                q3 = temp_array[q3_idx]
                iqr = q3 - q1
            elif count > 0:
                iqr = temp_array[-1] - temp_array[0]  # Fallback for small N
                if count == 1:
                    iqr = 0.0
            else:
                iqr = 0.0

            # Calculate d statistic (measure of symmetry)
            d = GLOBAL_MISSING_CODE
            if abs(iqr) > 1e-9:  # Avoid division by zero
                d = (mean_val - median_val) / iqr

            # Find lambda that minimizes |d| (most symmetric)
            if d != GLOBAL_MISSING_CODE:
                abs_d = abs(d)
                if abs_d < min_abs_d:
                    min_abs_d = abs_d
                    best_lam = k
        
        # Move to next lambda value
        k += step
    
    # Return best lambda or missing code if none found
    if min_abs_d == float('inf'):
        return GLOBAL_MISSING_CODE
    return best_lam

# Inverse Box-Cox transform
def unbox_cox(value: float, lamda: float) -> float:
    if value == GLOBAL_MISSING_CODE:
        return GLOBAL_MISSING_CODE
    
    try:
        if abs(lamda) < 1e-9:  # Lambda is zero -> exp
            if value > 700:
                return float('inf')  # Avoid overflow
            return math.exp(value)
        else:  # Standard inverse Box-Cox
            base = (value * lamda) + 1
            if base < 0:
                # Cannot take power of negative number
                return GLOBAL_MISSING_CODE
            power = 1.0 / lamda
            return base ** power
    except (ValueError, OverflowError):
        return GLOBAL_MISSING_CODE


# Helper function for variance adjustment
# Applies factor to transformed data, then calculates variance after untransforming
def calc_variance_after_transform(ctx: SDSMContext, ensemble: int, trans_array, factor: float, mean_trans: float) -> float:
    temp_untransformed = []

    # Process each day that was part of the transformation
    for i in range(ctx.no_of_days):
        if trans_array[i] != GLOBAL_MISSING_CODE:
            original_val = ctx.data_array[ensemble][i]

            try:
                # Apply adjustment to transformed value
                val_trans_adjusted = ((trans_array[i] - mean_trans) * factor) + mean_trans
                
                # Untransform back to original scale
                val_untransformed = unbox_cox(val_trans_adjusted, ctx.lamda)

                if val_untransformed != GLOBAL_MISSING_CODE and val_untransformed != float('inf'):
                    # Ensure conditional values stay above threshold
                    if ctx.conditional_check and original_val > ctx.local_thresh:
                        if val_untransformed <= ctx.local_thresh:
                            temp_untransformed.append(ctx.local_thresh + 1e-6)
                        else:
                            temp_untransformed.append(val_untransformed)
                    else:
                        temp_untransformed.append(val_untransformed)
            except (ValueError, OverflowError):
                continue

    # Calculate variance of untransformed values
    count = len(temp_untransformed)
    if count > 1:
        mean_new = sum(temp_untransformed) / count
        variance = sum([(x - mean_new) ** 2 for x in temp_untransformed]) / count
        return variance
    elif count == 1:
        return 0.0  # Variance is 0 with only one point
    else:
        return GLOBAL_MISSING_CODE


# Apply variance treatment to change spread of values
def apply_variance(ctx: SDSMContext, progress_callback=None):
    # Check if means have been calculated
    if not ctx.mean_array or len(ctx.mean_array) != ctx.ensemble_size:
        QMessageBox.critical(None, "Error", "Mean/SD must be calculated for all ensembles before applying variance.")
        ctx.error_occurred = True
        return

    # Get target variance ratio (e.g., 1.10 for +10%)
    target_variance_ratio = ctx.variance_factor_percent
    
    # Check for negative variance ratio
    if target_variance_ratio < 0:
        QMessageBox.critical(None, "Error", "Target variance factor results in a negative variance ratio, which is not possible.")
        ctx.error_occurred = True
        return

    # Process each ensemble
    for j in range(ctx.ensemble_size):
        # Check for user cancellation
        if ctx.global_kop_out:
            return
            
        # Update progress
        if progress_callback:
            progress_callback(int(j / ctx.ensemble_size * 10), f"Applying Variance {j+1} Prep")

        # Get current mean and standard deviation
        mean_j = ctx.mean_array[j]['mean']
        sd_j = ctx.mean_array[j]['sd']

        # Skip if mean or SD is missing
        if mean_j == GLOBAL_MISSING_CODE or sd_j == GLOBAL_MISSING_CODE:
            print(f"Warning: Ensemble {j+1} has missing mean/SD. Skipping variance adjustment.")
            continue

        # Calculate original variance
        original_variance = sd_j ** 2
        
        # Check for near-zero variance
        if original_variance < 1e-9:
            if target_variance_ratio <= 1.0:
                print(f"Warning: Ensemble {j+1} has zero/near-zero initial variance. Skipping variance reduction.")
                continue

        # UNCONDITIONAL PROCESS
        if not ctx.conditional_check:
            # Handle zero variance case
            if abs(original_variance) < 1e-9 and target_variance_ratio > 1.0:
                print(f"Warning: Ensemble {j+1} (Unconditional) has zero variance. Cannot scale variance.")
                continue

            # Calculate scaling factor for variance adjustment
            scaling_factor = math.sqrt(target_variance_ratio) if target_variance_ratio >= 0 else 0
            
            # Apply scaling to all non-missing values
            for i in range(ctx.no_of_days):
                val = ctx.data_array[j][i]
                if val != GLOBAL_MISSING_CODE:
                    # Apply formula: new_value = (old_value - mean) * scaling_factor + mean
                    ctx.data_array[j][i] = ((val - mean_j) * scaling_factor) + mean_j
                    
            # Update progress
            if progress_callback:
                progress_callback(int((j+1) / ctx.ensemble_size * 100), f"Applying Variance {j+1} Complete")

        # CONDITIONAL PROCESS (Box-Cox)
        else:
            # 1. Find optimal lambda for Box-Cox transformation
            if progress_callback:
                progress_callback(int(j / ctx.ensemble_size * 10) + 10, f"Variance {j+1} Finding Lambda")
                
            # Search in progressively narrower ranges
            lamda = find_min_lambda(ctx, j, -2.0, 2.0, 0.25)
            if lamda != GLOBAL_MISSING_CODE:
                lamda = find_min_lambda(ctx, j, lamda - 0.25, lamda + 0.25, 0.1)
            if lamda != GLOBAL_MISSING_CODE:
                lamda = find_min_lambda(ctx, j, lamda - 0.1, lamda + 0.1, 0.01)

            # Check if lambda was found
            if lamda == GLOBAL_MISSING_CODE:
                QMessageBox.warning(None, "Lambda Error", 
                                   f"Ensemble {j+1}: Could not find suitable lambda for Box-Cox. Skipping variance adjustment for this ensemble.")
                continue

            ctx.lamda = lamda

            # 2. Transform the data (only values > threshold)
            trans_array = [GLOBAL_MISSING_CODE] * ctx.no_of_days
            valid_transformed_values = []
            num_values_for_transform = 0
            
            for i in range(ctx.no_of_days):
                val = ctx.data_array[j][i]
                if val != GLOBAL_MISSING_CODE and val > ctx.local_thresh:
                    num_values_for_transform += 1
                    # Skip zero values
                    if abs(val) < 1e-9 and ctx.local_thresh >= 0:
                        continue
                        
                    try:
                        # Apply Box-Cox transform
                        if abs(ctx.lamda) < 1e-9:
                            transformed_val = math.log(val)
                        else:
                            transformed_val = (val ** ctx.lamda - 1) / ctx.lamda
                        trans_array[i] = transformed_val
                        valid_transformed_values.append(transformed_val)
                    except (ValueError, OverflowError):
                        trans_array[i] = GLOBAL_MISSING_CODE

            # Check if we have enough values
            if not valid_transformed_values or len(valid_transformed_values) < 2:
                print(f"Warning: Ensemble {j+1}: Insufficient valid values (> threshold) for Box-Cox transform or variance calculation.")
                continue

            # Calculate mean of transformed values
            mean_trans = sum(valid_transformed_values) / len(valid_transformed_values)

            # 3. Iteratively find scaling factor for transformed data
            if progress_callback:
                progress_callback(int(j / ctx.ensemble_size * 10) + 30, f"Variance {j+1} Finding Factor")

            # Set initial search range
            lower_f = 0.1
            higher_f = 2.0
            
            # Adjust range based on target (increase or decrease)
            if target_variance_ratio > 1.0:
                lower_f = 1.0
                higher_f = 3.0  # Increased upper for expansion
            else:
                lower_f = 0.01
                higher_f = 1.0

            best_factor = 1.0

            # Binary search for optimal factor
            max_iter = 15
            for iter_num in range(max_iter):
                # Check for user cancellation
                if ctx.global_kop_out:
                    return
                    
                # Update progress
                if progress_callback:
                    prog = int(j / ctx.ensemble_size * 10) + 30 + int(iter_num/max_iter * 60)
                    progress_callback(prog, f"Variance {j+1} Iter {iter_num+1}")

                # Try middle point of current range
                middle_f = (lower_f + higher_f) / 2.0
                if abs(middle_f) < 1e-9:
                    middle_f = 1e-9 * (-1 if middle_f < 0 else 1)  # Avoid zero factor but keep sign

                # Calculate resulting variance with this factor
                resulting_variance = calc_variance_after_transform(ctx, j, trans_array, middle_f, mean_trans)

                # Check if calculation failed
                if resulting_variance == GLOBAL_MISSING_CODE:
                    print(f"Warning: Ensemble {j+1}, Iter {iter_num+1}: Could not calculate resulting variance.")
                    # Adjust search range based on direction
                    if target_variance_ratio > 1.0:
                        higher_f = middle_f  # Assume it overshot
                    else:
                        lower_f = middle_f  # Assume it overshot
                    if abs(higher_f - lower_f) < 1e-3:
                        break  # Converged or stuck
                    continue

                # Calculate current variance ratio
                current_variance_ratio = GLOBAL_MISSING_CODE
                if original_variance > 1e-9:  # Normal case
                    current_variance_ratio = resulting_variance / original_variance
                elif resulting_variance > 1e-9:  # Original variance was zero
                    current_variance_ratio = float('inf')
                else:  # Both are zero
                    current_variance_ratio = 1.0

                # Adjust search range based on current ratio
                if current_variance_ratio < target_variance_ratio:
                    lower_f = middle_f  # Need to increase factor
                else:
                    higher_f = middle_f  # Need to decrease factor

                # Update best factor
                best_factor = (lower_f + higher_f) / 2.0
                
                # Check for convergence
                if abs(higher_f - lower_f) < 1e-4:
                    break

            # 4. Apply the best factor and untransform
            if progress_callback:
                progress_callback(int(j / ctx.ensemble_size * 10)+95, f"Variance {j+1} Applying Final")
                
            # Process each day
            for i in range(ctx.no_of_days):
                original_val = ctx.data_array[j][i]
                
                # Only process days that were transformed
                if trans_array[i] != GLOBAL_MISSING_CODE:
                    try:
                        # Apply adjustment and untransform
                        val_trans_adjusted = ((trans_array[i] - mean_trans) * best_factor) + mean_trans
                        val_untransformed = unbox_cox(val_trans_adjusted, ctx.lamda)

                        if val_untransformed != GLOBAL_MISSING_CODE and val_untransformed != float('inf'):
                            # Ensure conditional values stay above threshold
                            if original_val > ctx.local_thresh:
                                if val_untransformed <= ctx.local_thresh:
                                    ctx.data_array[j][i] = ctx.local_thresh + 1e-6  # Keep above threshold
                                else:
                                    ctx.data_array[j][i] = val_untransformed
                    except (ValueError, OverflowError):
                        pass  # Keep original value

    # Update progress to complete
    if progress_callback:
        progress_callback(100, "Applying Variance Complete")


# Apply trend to add time-based changes to values
def apply_trend(ctx: SDSMContext, progress_callback=None):
    if not ctx.trend_check:
        return

    # Process each ensemble
    for j in range(ctx.ensemble_size):
        # Check for user cancellation
        if ctx.global_kop_out:
            return
            
        # Update progress
        if progress_callback:
            progress_callback(int(j / ctx.ensemble_size * 100), f"Applying Trend {j+1}")

        # LINEAR TREND
        if ctx.trend_option == 0:
            # Skip if trend is zero
            if abs(ctx.linear_trend) < 1e-9:
                continue
                
            # Calculate days per year (for annual rate conversion)
            days_per_year = 365.25 if ctx.year_indicator == 366 else float(ctx.year_indicator)
            if days_per_year == 0:
                days_per_year = 365.25  # Avoid division by zero

            # Calculate daily increment
            increment_per_day = ctx.linear_trend / days_per_year
            increment_multiplier_per_day_percent = ctx.linear_trend / days_per_year

            # Apply to each day
            for i in range(ctx.no_of_days):
                val = ctx.data_array[j][i]
                if val != GLOBAL_MISSING_CODE:
                    day_index_from_start = i  # 0-based index

                    if not ctx.conditional_check:
                        # Unconditional: Add trend value
                        trend_effect = increment_per_day * day_index_from_start
                        ctx.data_array[j][i] = val + trend_effect
                    else:
                        # Conditional: Multiply by trend factor if > threshold
                        if val > ctx.local_thresh:
                            # Calculate trend multiplier (as percentage)
                            # For annual percentage trend of ctx.linear_trend,
                            # daily percentage increment is (linear_trend / (days_per_year * 100))
                            trend_multiplier_increment = (ctx.linear_trend / (days_per_year * 100.0)) * day_index_from_start
                            trend_multiplier = 1.0 + trend_multiplier_increment

                            # Apply trend multiplier
                            new_val = val * trend_multiplier
                            
                            # Keep values above threshold
                            if new_val <= ctx.local_thresh:
                                ctx.data_array[j][i] = ctx.local_thresh + 1e-6
                            else:
                                ctx.data_array[j][i] = new_val

        # EXPONENTIAL TREND
        elif ctx.trend_option == 1:
            exp_trend_factor_input = ctx.exp_trend
            
            # Skip if no change
            if abs(exp_trend_factor_input - 1.0) < 1e-9 and not ctx.conditional_check:
                continue
            if abs(exp_trend_factor_input) < 1e-9 and ctx.conditional_check:
                continue

            # Parse input trend value (as percentage)
            exp_input_val = ctx.exp_trend
            if abs(exp_input_val) < 1e-9:
                continue

            # Determine if trend is positive or negative
            add_effect = exp_input_val > 0
            exp_param_abs = abs(exp_input_val / 100.0)  # Convert to fraction, e.g., 0.5 for 50%

            try:
                # Calculate exp_a_value for scaling trend over time
                log_arg = exp_param_abs + 1.0
                if ctx.no_of_days <= 0:
                    continue
                exp_a_value = ctx.no_of_days / math.log(log_arg)
                if abs(exp_a_value) < 1e-9:
                    continue
            except (ValueError, OverflowError):
                continue

            # Apply to each day
            for i in range(ctx.no_of_days):
                val = ctx.data_array[j][i]
                if val != GLOBAL_MISSING_CODE:
                    day_idx = i  # 0-based
                    
                    try:
                        # Calculate exponential trend effect
                        exponent = day_idx / exp_a_value
                        if exponent > 700:
                            trend_effect_magnitude = float('inf')
                        elif exponent < -700:
                            trend_effect_magnitude = 0
                        else:
                            trend_effect_magnitude = math.exp(exponent) - 1.0
                            
                        if trend_effect_magnitude == float('inf'):
                            continue
                    except (ValueError, OverflowError):
                        continue

                    if not ctx.conditional_check:
                        # Unconditional: Apply multiplicative factor
                        current_fractional_change = trend_effect_magnitude
                        if add_effect:
                            ctx.data_array[j][i] = val * (1 + current_fractional_change)
                        else:
                            ctx.data_array[j][i] = val * (1 - current_fractional_change)
                    else:
                        # Conditional: Apply only to values > threshold
                        if val > ctx.local_thresh:
                            current_fractional_change = trend_effect_magnitude
                            if add_effect:
                                trend_multiplier = 1.0 + current_fractional_change
                            else:
                                trend_multiplier = 1.0 - current_fractional_change

                            # Avoid negative values
                            if trend_multiplier < 0:
                                trend_multiplier = 0
                                
                            # Apply trend multiplier
                            new_val = val * trend_multiplier
                            
                            # Keep values above threshold
                            if new_val <= ctx.local_thresh:
                                ctx.data_array[j][i] = ctx.local_thresh + 1e-6
                            else:
                                ctx.data_array[j][i] = new_val

        # LOGISTIC TREND
        elif ctx.trend_option == 2:
            logistic_input_val = ctx.logistic_trend
            
            # Skip if no change
            if abs(logistic_input_val) < 1e-9:
                continue

            # Apply to each day
            for i in range(ctx.no_of_days):
                val = ctx.data_array[j][i]
                if val != GLOBAL_MISSING_CODE:
                    # Map day index to range [-6, 6] for sigmoid function
                    if ctx.no_of_days > 1:
                        x_mapping = ((i / (ctx.no_of_days - 1)) * 12.0) - 6.0
                    else:
                        x_mapping = 0.0

                    try:
                        # Calculate sigmoid factor [0, 1]
                        sigmoid_factor = 1.0 / (1.0 + math.exp(-x_mapping))
                    except OverflowError:
                        sigmoid_factor = 0.0

                    # Calculate trend effect based on sigmoid
                    trend_effect_absolute = logistic_input_val * sigmoid_factor

                    if not ctx.conditional_check:
                        # Unconditional: Add absolute trend effect
                        ctx.data_array[j][i] = val + trend_effect_absolute
                    else:
                        # Conditional: Apply only to values > threshold
                        if val > ctx.local_thresh:
                            # Calculate multiplier based on percentage
                            trend_multiplier = 1.0 + ((logistic_input_val * sigmoid_factor) / 100.0)

                            # Avoid negative values
                            if trend_multiplier < 0:
                                trend_multiplier = 0
                                
                            # Apply trend multiplier
                            new_val = val * trend_multiplier
                            
                            # Keep values above threshold
                            if new_val <= ctx.local_thresh:
                                ctx.data_array[j][i] = ctx.local_thresh + 1e-6
                            else:
                                ctx.data_array[j][i] = new_val
                                
    # Update progress to complete
    if progress_callback:
        progress_callback(100, "Applying Trend Complete")


# Write the modified data to the output file
def write_output_file(ctx: SDSMContext, progress_callback=None):
    try:
        with open(ctx.out_root, "w") as f:
            # Write each day's data
            for i in range(ctx.no_of_days):
                # Check for user cancellation
                if ctx.global_kop_out:
                    return False
                    
                # Update progress
                if progress_callback:
                    progress_callback(int(i / ctx.no_of_days * 100), "Writing Output File")

                # Format line with values for each ensemble
                line_parts = [format_value_output(ctx.data_array[j][i]) for j in range(ctx.ensemble_size)]
                f.write("".join(line_parts).rstrip('\t') + "\n")  # Remove trailing tab

    except Exception as e:
        QMessageBox.critical(None, "File Write Error", f"Error writing output file:\n{e}")
        ctx.error_occurred = True
        return False

    # Update progress to complete
    if progress_callback:
        progress_callback(100, "Writing Output Complete")
    return True

# Parse PAR file to set model parameters
def parse_par_file(par_path: str, ctx: SDSMContext):
    lines = []
    try:
        # Read the file
        with open(par_path, "r") as f:
            raw_lines = f.readlines()
            
        # Clean up lines (remove empty lines and whitespace)
        lines = [line.strip() for line in raw_lines if line.strip()]
        if not lines:
            return False  # Empty file

        idx = 0
        # Helper function to safely get next line
        def get_line(current_idx):
            if current_idx < len(lines):
                return lines[current_idx], current_idx + 1
            raise IndexError("Unexpected end of PAR file.")

        # Read basic parameters
        line, idx = get_line(idx); ctx.num_predictors = int(line)
        line, idx = get_line(idx); ctx.num_months = int(line)  # Should be 12
        line, idx = get_line(idx); ctx.year_length = int(line)
        ctx.year_indicator = ctx.year_length
        
        # Parse start date
        line, idx = get_line(idx); start_date_str = line
        try:
            ctx.start_date = datetime.datetime.strptime(start_date_str, "%d/%m/%Y").date()
        except ValueError:  # Try alternative format
            ctx.start_date = datetime.datetime.strptime(start_date_str, "%m/%d/%Y").date()

        # Number of days
        line, idx = get_line(idx); ctx.no_of_days = int(line)

        # Skip potential duplicate date/days if present
        if idx < len(lines) and lines[idx] == start_date_str:
            idx += 1
        if idx < len(lines) and lines[idx].isdigit() and int(lines[idx]) == ctx.no_of_days:
            idx += 1

        # Read conditional flag
        line, idx = get_line(idx); cond_str = line
        ctx.conditional_check = (cond_str.upper() == "#TRUE#")
        
        # Read ensemble size
        line, idx = get_line(idx); ensemble_str = line
        ctx.ensemble_size = int(ensemble_str)

        # Skip variance factor, transform code, bias correction
        idx += 3

        # Read predictor files
        ctx.predictor_files = []
        par_dir = os.path.dirname(par_path)
        for _ in range(ctx.num_predictors):
            if idx >= len(lines):
                break
            line, idx = get_line(idx); pfile = line
            abs_pfile = os.path.normpath(os.path.join(par_dir, pfile))
            ctx.predictor_files.append(abs_pfile)

        # Read data file path
        if idx < len(lines):
            line, idx = get_line(idx); data_file = line
            # Check if it's a coefficient line or data file name
            if ' ' not in data_file and ('.' in data_file or os.sep in data_file or os.altsep in data_file):
                abs_data_file = os.path.normpath(os.path.join(par_dir, data_file))
                ctx.in_file = os.path.basename(abs_data_file)
                ctx.in_root = abs_data_file
            else:
                # Line was not a filename, put it back
                idx -= 1

        # Read monthly coefficients if present
        ctx.monthly_coeffs = []
        coeffs_found = False
        while idx < len(lines):
            line, current_idx_plus_1 = get_line(idx)
            parts = line.split()
            try:
                # Check if line contains coefficient values
                coeffs = [float(x) for x in parts]
                if len(coeffs) == ctx.num_predictors + 1:  # Intercept + predictors
                    ctx.monthly_coeffs.append(coeffs)
                    coeffs_found = True
                    idx = current_idx_plus_1
                else:
                    break
            except ValueError:
                break  # Not coefficient values

        if coeffs_found:
            print(f"Read {len(ctx.monthly_coeffs)} lines of monthly coefficients from PAR file.")
        return True

    except Exception as e:
        QMessageBox.critical(None, "Error", f"Error parsing .PAR file '{os.path.basename(par_path)}':\n{e}\nApproximate line number/block: {idx+1}")
        return False


# --- CSS Stylesheet for UI ---
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

#############################################################
# User Interface Using PyQt5
#############################################################
class ScenarioGeneratorWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.ctx = SDSMContext()
        self._init_ui()
        self.reset_ui_and_context()

    def _init_ui(self):
        # Main layout container
        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(12, 12, 12, 12)
        mainLayout.setSpacing(10)

        # --- File Selection Section ---
        fileGroup = QGroupBox("Files")
        fileLayout = QGridLayout()
        fileLayout.setSpacing(8)
        
        # Input file controls
        self.inputFileButton = QPushButton(self.style().standardIcon(QStyle.SP_DirOpenIcon), " Input File")
        self.inputFileLabel = QLabel("No file selected")
        self.inputFileLabel.setObjectName("FileLabel")
        self.inputFileLabel.setWordWrap(True)
        
        # Output file controls
        self.outputFileButton = QPushButton(self.style().standardIcon(QStyle.SP_FileDialogNewFolder), " Output File")
        self.outputFileLabel = QLabel("No file selected")
        self.outputFileLabel.setObjectName("FileLabel")
        self.outputFileLabel.setWordWrap(True)
        
        # Add widgets to layout
        fileLayout.addWidget(self.inputFileButton, 0, 0)
        fileLayout.addWidget(self.inputFileLabel, 0, 1)
        fileLayout.addWidget(self.outputFileButton, 1, 0)
        fileLayout.addWidget(self.outputFileLabel, 1, 1)
        fileLayout.setColumnStretch(1, 1)  # Allow filename labels to stretch
        
        fileGroup.setLayout(fileLayout)
        mainLayout.addWidget(fileGroup)

        # --- General Parameters Section ---
        generalGroup = QGroupBox("General Settings")
        generalLayout = QGridLayout()
        generalLayout.setSpacing(8)
        
        # Create input fields
        self.startDateInput = QLineEdit()
        self.ensembleSizeInput = QLineEdit()
        self.conditionalCheck = QCheckBox("Conditional Process")
        self.thresholdInput = QLineEdit()
        
        # Add widgets to layout
        generalLayout.addWidget(QLabel("Start Date (DD/MM/YY):"), 0, 0)
        generalLayout.addWidget(self.startDateInput, 0, 1)
        generalLayout.addWidget(QLabel("Ensemble Size:"), 0, 2)
        generalLayout.addWidget(self.ensembleSizeInput, 0, 3)
        generalLayout.addWidget(self.conditionalCheck, 1, 0, 1, 2)
        generalLayout.addWidget(QLabel("Threshold:"), 1, 2)
        generalLayout.addWidget(self.thresholdInput, 1, 3)
        
        # Allow input fields to stretch
        generalLayout.setColumnStretch(1,1)
        generalLayout.setColumnStretch(3,1)
        
        generalGroup.setLayout(generalLayout)
        mainLayout.addWidget(generalGroup)

        # --- Treatments Section ---
        treatmentsGroup = QGroupBox("Treatments")
        treatmentsLayout = QGridLayout()
        treatmentsLayout.setSpacing(10)
        treatmentsLayout.setColumnStretch(1, 1)  # Allow controls column to stretch

        # Helper function for consistent input field styling
        def create_treatment_input(placeholder=""):
            edit = QLineEdit()
            edit.setPlaceholderText(placeholder)
            edit.setObjectName("TreatmentInput")
            return edit

        # Occurrence Treatment Row
        self.occurrenceCheck = QCheckBox("Occurrence")
        self.occFactorInput = create_treatment_input("% change")
        self.occOptionGroup = QButtonGroup(self)
        self.occFactorRadio = QRadioButton("Factor")
        self.occForcedRadio = QRadioButton("Forced")
        self.occOptionGroup.addButton(self.occFactorRadio, 0)
        self.occOptionGroup.addButton(self.occForcedRadio, 1)
        self.preserveTotalsCheck = QCheckBox("Preserve Totals")

        # Layout for occurrence controls
        occControlsLayout = QHBoxLayout()
        occControlsLayout.setContentsMargins(0,0,0,0)
        occControlsLayout.setSpacing(5)
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

        # Amount Treatment Row
        self.amountCheck = QCheckBox("Amount")
        self.amountOptionGroup = QButtonGroup(self)
        self.amountFactorRadio = QRadioButton("Factor:")
        self.amountFactorInput = create_treatment_input("% change")
        self.amountAddRadio = QRadioButton("Addition:")
        self.amountAddInput = create_treatment_input("value")
        self.amountOptionGroup.addButton(self.amountFactorRadio, 0)
        self.amountOptionGroup.addButton(self.amountAddRadio, 1)

        # Layout for amount controls
        amountControlsLayout = QHBoxLayout()
        amountControlsLayout.setContentsMargins(0,0,0,0)
        amountControlsLayout.setSpacing(5)
        amountControlsLayout.addWidget(self.amountFactorRadio)
        amountControlsLayout.addWidget(self.amountFactorInput)
        amountControlsLayout.addSpacing(15)
        amountControlsLayout.addWidget(self.amountAddRadio)
        amountControlsLayout.addWidget(self.amountAddInput)
        amountControlsLayout.addStretch(1)
        
        treatmentsLayout.addWidget(self.amountCheck, 1, 0, Qt.AlignTop)
        treatmentsLayout.addLayout(amountControlsLayout, 1, 1)

        # Variance Treatment Row
        self.varianceCheck = QCheckBox("Variance")
        self.varianceFactorInput = create_treatment_input("% change")
        
        # Layout for variance controls
        varianceControlsLayout = QHBoxLayout()
        varianceControlsLayout.setContentsMargins(0,0,0,0)
        varianceControlsLayout.setSpacing(5)
        varianceControlsLayout.addWidget(QLabel("Factor (%):"))
        varianceControlsLayout.addWidget(self.varianceFactorInput)
        varianceControlsLayout.addStretch(1)
        
        treatmentsLayout.addWidget(self.varianceCheck, 2, 0, Qt.AlignTop)
        treatmentsLayout.addLayout(varianceControlsLayout, 2, 1)

        # Trend Treatment Section
        self.trendCheck = QCheckBox("Trend")
        self.trendOptionGroup = QButtonGroup(self)
        
        # Linear trend option
        self.trendLinearRadio = QRadioButton("Linear:")
        self.trendLinearInput = create_treatment_input("/year value")
        self.trendOptionGroup.addButton(self.trendLinearRadio, 0)
        trendLinLayout = QHBoxLayout()
        trendLinLayout.setContentsMargins(0,0,0,0)
        trendLinLayout.setSpacing(5)
        trendLinLayout.addWidget(self.trendLinearRadio)
        trendLinLayout.addWidget(self.trendLinearInput)
        trendLinLayout.addStretch(1)
        
        # Exponential trend option
        self.trendExpRadio = QRadioButton("Exponential:")
        self.trendExpInput = create_treatment_input("factor")
        self.trendOptionGroup.addButton(self.trendExpRadio, 1)
        trendExpLayout = QHBoxLayout()
        trendExpLayout.setContentsMargins(0,0,0,0)
        trendExpLayout.setSpacing(5)
        trendExpLayout.addWidget(self.trendExpRadio)
        trendExpLayout.addWidget(self.trendExpInput)
        trendExpLayout.addStretch(1)
        
        # Logistic trend option
        self.trendLogRadio = QRadioButton("Logistic:")
        self.trendLogInput = create_treatment_input("factor")
        self.trendOptionGroup.addButton(self.trendLogRadio, 2)
        trendLogLayout = QHBoxLayout()
        trendLogLayout.setContentsMargins(0,0,0,0)
        trendLogLayout.setSpacing(5)
        trendLogLayout.addWidget(self.trendLogRadio)
        trendLogLayout.addWidget(self.trendLogInput)
        trendLogLayout.addStretch(1)

        # Container for all trend options
        trendOptionsContainer = QVBoxLayout()
        trendOptionsContainer.setContentsMargins(0,0,0,0)
        trendOptionsContainer.setSpacing(4)
        trendOptionsContainer.addLayout(trendLinLayout)
        trendOptionsContainer.addLayout(trendExpLayout)
        trendOptionsContainer.addLayout(trendLogLayout)

        treatmentsLayout.addWidget(self.trendCheck, 3, 0, Qt.AlignTop)
        treatmentsLayout.addLayout(trendOptionsContainer, 3, 1)
        
        treatmentsGroup.setLayout(treatmentsLayout)
        mainLayout.addWidget(treatmentsGroup)

        # --- Progress Bar ---
        self.progressBar = QProgressBar()
        self.progressBar.setVisible(False)
        self.progressLabel = QLabel("")
        self.progressLabel.setVisible(False)
        self.progressLabel.setAlignment(Qt.AlignCenter)
        
        progressLayout = QVBoxLayout()
        progressLayout.setContentsMargins(0,5,0,0)
        progressLayout.addWidget(self.progressLabel)
        progressLayout.addWidget(self.progressBar)
        
        mainLayout.addLayout(progressLayout)

        # --- Action Buttons ---
        buttonLayout = QHBoxLayout()
        self.generateButton = QPushButton("Generate Scenario")
        self.generateButton.setObjectName("GenerateButton")  # For specific styling
        self.resetButton = QPushButton("Reset Form")
        
        buttonLayout.addStretch(1)
        buttonLayout.addWidget(self.resetButton)
        buttonLayout.addWidget(self.generateButton)
        
        mainLayout.addLayout(buttonLayout)

        # Push content upwards
        mainLayout.addStretch(1)

        # Add tooltips and connect signals
        self._add_tooltips()
        self._connect_signals()


    def _add_tooltips(self):
        # File section tooltips
        self.inputFileButton.setToolTip("Load parameters from a .PAR file or raw data from .txt/.dat/.csv")
        self.outputFileButton.setToolTip("Specify the output file name for the generated scenario (e.g., scenario.out)")
        
        # General settings tooltips
        self.startDateInput.setToolTip("Start date of the input data series (DD/MM/YYYY)")
        self.ensembleSizeInput.setToolTip("Number of ensemble members (columns) in the input data (1-100)")
        self.conditionalCheck.setToolTip("If checked, Amount, Variance, and Trend treatments only apply to values above the Threshold.\nOccurrence treatment ALWAYS requires this to be checked.")
        self.thresholdInput.setToolTip("Threshold value for conditional processing (e.g., precipitation threshold like 0.1)")

        # Occurrence tooltips
        self.occurrenceCheck.setToolTip("Modify the frequency of wet/dry days (Conditional Process must be checked)")
        self.occFactorInput.setToolTip("Percentage change for 'Factor' occurrence modification (e.g., 5 for +5%, -10 for -10%) [-99 to 100]")
        self.occFactorRadio.setToolTip("Stochastic adjustment of wet/dry days based on the factor")
        self.occForcedRadio.setToolTip("Adjust wet/dry days to meet a forced monthly percentage (ZoM data not loaded via UI)")
        self.preserveTotalsCheck.setToolTip("If checked, scale rainfall amounts after occurrence changes to attempt to preserve original total rainfall")

        # Amount tooltips
        self.amountCheck.setToolTip("Modify the magnitude of data values")
        self.amountFactorInput.setToolTip("Percentage change for 'Factor' amount modification (e.g., 10 for +10%) [-100 to 100]")
        self.amountAddInput.setToolTip("Value to add for 'Addition' amount modification [-100 to 100]")

        # Variance tooltips
        self.varianceCheck.setToolTip("Modify the variance of the data")
        self.varianceFactorInput.setToolTip("Percentage change in variance (e.g., 20 for +20% variance). Must result in non-negative variance ratio.")

        # Trend tooltips
        self.trendCheck.setToolTip("Apply a trend to the data")
        self.trendLinearInput.setToolTip("Linear trend value per year (e.g., 0.1 for +0.1 units/year) [-100 to 100]")
        self.trendExpInput.setToolTip("Exponential trend factor (e.g., 50 for +50% change by end of series, cannot be 0). Affects rate of change.")
        self.trendLogInput.setToolTip("Logistic trend factor (e.g., 10 for +10 units change by end of series) [-100 to 100].")

        # Button tooltips
        self.generateButton.setToolTip("Start the scenario generation process with the current settings")
        self.resetButton.setToolTip("Reset all form fields to their default values")

    def _connect_signals(self):
        # Connect file buttons to methods
        self.inputFileButton.clicked.connect(self.select_input_file)
        self.outputFileButton.clicked.connect(self.select_output_file)
        self.generateButton.clicked.connect(self.run_generation)
        self.resetButton.clicked.connect(self.reset_ui_and_context)

        # Connect validation methods to input fields
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

        # Connect checkboxes to context attributes
        self.conditionalCheck.toggled.connect(lambda checked: setattr(self.ctx, 'conditional_check', checked))
        self.occurrenceCheck.toggled.connect(lambda checked: setattr(self.ctx, 'occurrence_check', checked))
        self.preserveTotalsCheck.toggled.connect(lambda checked: setattr(self.ctx, 'preserve_totals_check', checked))
        self.amountCheck.toggled.connect(lambda checked: setattr(self.ctx, 'amount_check', checked))
        self.varianceCheck.toggled.connect(lambda checked: setattr(self.ctx, 'variance_check', checked))
        self.trendCheck.toggled.connect(lambda checked: setattr(self.ctx, 'trend_check', checked))

        # Connect radio button groups to context attributes
        self.occOptionGroup.buttonClicked[int].connect(lambda id: setattr(self.ctx, 'occurrence_option', id))
        self.amountOptionGroup.buttonClicked[int].connect(lambda id: setattr(self.ctx, 'amount_option', id))
        self.trendOptionGroup.buttonClicked[int].connect(lambda id: setattr(self.ctx, 'trend_option', id))


    # Reset the UI and context to default values
    def reset_ui_and_context(self):
        # Reset the context object
        self.ctx.reset()

        # Reset file section
        self.inputFileLabel.setText("No file selected")
        self.outputFileLabel.setText("No file selected")

        # Reset general settings
        self.startDateInput.setText(self.ctx.start_date.strftime("%d/%m/%Y"))
        self.ensembleSizeInput.setText(str(self.ctx.ensemble_size))
        self.conditionalCheck.setChecked(self.ctx.conditional_check)
        self.thresholdInput.setText(str(self.ctx.local_thresh))

        # Reset occurrence section
        self.occurrenceCheck.setChecked(self.ctx.occurrence_check)
        self.occFactorInput.setText(str(self.ctx.occurrence_factor))
        self.occFactorRadio.setChecked(self.ctx.occurrence_option == 0)
        self.occForcedRadio.setChecked(self.ctx.occurrence_option == 1)
        self.preserveTotalsCheck.setChecked(self.ctx.preserve_totals_check)

        # Reset amount section
        self.amountCheck.setChecked(self.ctx.amount_check)
        self.amountFactorRadio.setChecked(self.ctx.amount_option == 0)
        self.amountFactorInput.setText(str(self.ctx.amount_factor))
        self.amountAddRadio.setChecked(self.ctx.amount_option == 1)
        self.amountAddInput.setText(str(self.ctx.amount_addition))

        # Reset variance section
        self.varianceCheck.setChecked(self.ctx.variance_check)
        self.varianceFactorInput.setText(str(self.ctx.variance_factor))

        # Reset trend section
        self.trendCheck.setChecked(self.ctx.trend_check)
        self.trendLinearRadio.setChecked(self.ctx.trend_option == 0)
        self.trendLinearInput.setText(str(self.ctx.linear_trend))
        self.trendExpRadio.setChecked(self.ctx.trend_option == 1)
        self.trendExpInput.setText(str(self.ctx.exp_trend))
        self.trendLogRadio.setChecked(self.ctx.trend_option == 2)
        self.trendLogInput.setText(str(self.ctx.logistic_trend))

        # Reset progress indicators
        self.progressBar.setVisible(False)
        self.progressLabel.setVisible(False)
        self.progressBar.setValue(0)
        self.progressLabel.setText("")


    # Open file dialog to select input file
    def select_input_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Input File", "", 
            "PAR Files (*.par);;Data Files (*.txt *.dat *.csv);;All Files (*.*)"
        )
        
        if file_path:
            # Store file paths
            self.ctx.in_root = file_path
            self.ctx.in_file = os.path.basename(file_path)
# Update the UI with file information
            self.inputFileLabel.setText(f"{self.ctx.in_file} ({os.path.dirname(file_path)})")

            # If it's a PAR file, try to parse it
            if file_path.lower().endswith(".par"):
                if parse_par_file(file_path, self.ctx):
                    QMessageBox.information(
                        self, "PAR Parsed", 
                        f"Loaded settings from {os.path.basename(file_path)}.\n"
                        f"Input data file from PAR: {self.ctx.in_file if self.ctx.in_file else 'Not specified in PAR'}"
                    )
                    # Update UI with loaded settings
                    self.update_ui_from_context()
                else:
                    # Reset if parsing failed
                    self.ctx.in_root = ""
                    self.ctx.in_file = ""
                    self.inputFileLabel.setText("No file selected")

    # Open file dialog to select output file
    def select_output_file(self):
        # Generate default filename based on input file if possible
        default_name = ""
        if self.ctx.in_file:
            base, ext = os.path.splitext(self.ctx.in_file)
            default_name = base + "_scenario.out"
        else:
            default_name = "scenario_output.out"

        # Use input file directory as default location
        initial_dir = os.path.dirname(self.ctx.in_root) if self.ctx.in_root else ""
        default_path = os.path.join(initial_dir, default_name)

        # Open save dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Output File", default_path, 
            "OUT Files (*.out);;All Files (*.*)"
        )
        
        if file_path:
            # Add .out extension if missing
            if not file_path.lower().endswith(".out"):
                file_path += ".out"
                
            # Store file paths
            self.ctx.out_root = file_path
            self.ctx.out_file = os.path.basename(file_path)
            
            # Update UI
            self.outputFileLabel.setText(f"{self.ctx.out_file} ({os.path.dirname(file_path)})")


    # Update UI elements based on context values (after loading PAR file)
    def update_ui_from_context(self):
        # Update date, ensemble size, and conditional flag
        self.startDateInput.setText(self.ctx.start_date.strftime("%d/%m/%Y"))
        self.ensembleSizeInput.setText(str(self.ctx.ensemble_size))
        self.conditionalCheck.setChecked(self.ctx.conditional_check)
        
        # Update input file information
        if self.ctx.in_file and self.ctx.in_root:
            # PAR specified a data file
            self.inputFileLabel.setText(f"{self.ctx.in_file} ({os.path.dirname(self.ctx.in_root)})")
        elif self.ctx.in_root and not self.ctx.in_file:
            # PAR file was selected but didn't specify data file
            self.inputFileLabel.setText(f"PAR: {os.path.basename(self.ctx.in_root)} (Data file not specified in PAR)")
        else:
            # No file selected
            self.inputFileLabel.setText("No file selected")

    # Update progress bar and text during processing
    def update_progress(self, value, text):
        self.progressBar.setValue(value)
        self.progressLabel.setText(text)
        # Process UI events to keep interface responsive
        QApplication.processEvents()

    # Validate date format in start date field
    def validate_start_date(self):
        try:
            # Parse date from text field
            date_obj = datetime.datetime.strptime(self.startDateInput.text(), "%d/%m/%Y").date()
            self.ctx.start_date = date_obj
        except ValueError:
            # Show error and reset to previous value
            QMessageBox.warning(self, "Input Error", "Invalid start date format. Use DD/MM/YYYY.")
            self.startDateInput.setText(self.ctx.start_date.strftime("%d/%m/%Y"))

    # Validate ensemble size input
    def validate_ensemble_size(self):
        try:
            val = int(self.ensembleSizeInput.text())
            # Check range (1-100)
            if 1 <= val <= 100:
                self.ctx.ensemble_size = val
            else:
                raise ValueError("Value out of range 1-100")
        except ValueError as e:
            # Show error and reset to previous value
            QMessageBox.warning(self, "Input Error", f"Ensemble size: {e}")
            self.ensembleSizeInput.setText(str(self.ctx.ensemble_size))

    # Validate threshold value
    def validate_threshold(self):
        try:
            val = float(self.thresholdInput.text())
            self.ctx.local_thresh = val
        except ValueError:
            # Show error and reset to previous value
            QMessageBox.warning(self, "Input Error", "Invalid threshold value. Must be a number.")
            self.thresholdInput.setText(str(self.ctx.local_thresh))

    # Validate occurrence factor input
    def validate_occurrence(self):
        try:
            val = float(self.occFactorInput.text())
            # Check range (-99 to 100)
            if -99.0 <= val <= 100.0:
                self.ctx.occurrence_factor = val
                # Convert to percentage multiplier (e.g., 5% -> 1.05)
                self.ctx.occurrence_factor_percent = (100.0 + val) / 100.0
            else:
                raise ValueError("Value out of range -99 to 100")
        except ValueError as e:
            # Show error and reset to previous value
            QMessageBox.warning(self, "Input Error", f"Occurrence factor: {e}")
            self.occFactorInput.setText(str(self.ctx.occurrence_factor))

    # Validate amount factor and addition inputs
    def validate_amount(self):
        try:
            # Check factor input
            val_factor = float(self.amountFactorInput.text())
            if -100.0 <= val_factor <= 100.0:
                self.ctx.amount_factor = val_factor
                # Convert to percentage multiplier (e.g., 5% -> 1.05)
                self.ctx.amount_factor_percent = (100.0 + val_factor) / 100.0
            else:
                raise ValueError("Factor out of range -100 to 100")
        except ValueError as e:
            # Show error and reset to previous value
            QMessageBox.warning(self, "Input Error", f"Amount factor: {e}")
            self.amountFactorInput.setText(str(self.ctx.amount_factor))
            
        try:
            # Check addition input
            val_add = float(self.amountAddInput.text())
            self.ctx.amount_addition = val_add
        except ValueError as e:
            # Show error and reset to previous value
            QMessageBox.warning(self, "Input Error", f"Amount addition: {e}")
            self.amountAddInput.setText(str(self.ctx.amount_addition))

    # Validate variance factor input
    def validate_variance(self):
        try:
            val = float(self.varianceFactorInput.text())
            # Calculate actual multiplier
            factor_percent = (100.0 + val) / 100.0
            
            # Check that result is non-negative
            if factor_percent >= 0:
                self.ctx.variance_factor = val
                self.ctx.variance_factor_percent = factor_percent
            else:
                raise ValueError("Resulting variance multiplier cannot be negative (input >= -100).")
        except ValueError as e:
            # Show error and reset to previous value
            QMessageBox.warning(self, "Input Error", f"Variance factor: {e}")
            self.varianceFactorInput.setText(str(self.ctx.variance_factor))

    # Validate trend inputs (linear, exponential, logistic)
    def validate_trend(self):
        try:
            # Check linear trend input
            val_lin = float(self.trendLinearInput.text())
            self.ctx.linear_trend = val_lin
        except ValueError as e:
            # Show error and reset to previous value
            QMessageBox.warning(self, "Input Error", f"Linear trend: {e}")
            self.trendLinearInput.setText(str(self.ctx.linear_trend))
            
        try:
            # Check exponential trend input
            val_exp = float(self.trendExpInput.text())
            self.ctx.exp_trend = val_exp
            self.ctx.add_exp_option = val_exp > 0  # Whether trend is additive (positive)
        except ValueError as e:
            # Show error and reset to previous value
            QMessageBox.warning(self, "Input Error", f"Exponential trend: {e}")
            self.trendExpInput.setText(str(self.ctx.exp_trend))
            
        try:
            # Check logistic trend input
            val_log = float(self.trendLogInput.text())
            self.ctx.logistic_trend = val_log
        except ValueError as e:
            # Show error and reset to previous value
            QMessageBox.warning(self, "Input Error", f"Logistic trend: {e}")
            self.trendLogInput.setText(str(self.ctx.logistic_trend))


    # Main scenario generation function
    def run_generation(self):
        # 1. Update context from UI (catches last-minute changes)
        self.validate_start_date()
        self.validate_ensemble_size()
        self.validate_threshold()
        self.validate_occurrence()
        self.validate_amount()
        self.validate_variance()
        self.validate_trend()

        # Update treatment options from UI
        self.ctx.conditional_check = self.conditionalCheck.isChecked()
        self.ctx.occurrence_check = self.occurrenceCheck.isChecked()
        self.ctx.preserve_totals_check = self.preserveTotalsCheck.isChecked()
        self.ctx.amount_check = self.amountCheck.isChecked()
        self.ctx.variance_check = self.varianceCheck.isChecked()
        self.ctx.trend_check = self.trendCheck.isChecked()
        self.ctx.occurrence_option = self.occOptionGroup.checkedId()
        self.ctx.amount_option = self.amountOptionGroup.checkedId()
        self.ctx.trend_option = self.trendOptionGroup.checkedId()

        # 2. Validate settings before proceeding
        if not check_settings(self.ctx, self):
            return

        # 3. Reset error flags and prepare UI
        mini_reset(self.ctx)
        self.progressBar.setVisible(True)
        self.progressLabel.setVisible(True)
        self.update_progress(0, "Starting...")
        self.generateButton.setEnabled(False)
        self.resetButton.setEnabled(False)
        QApplication.processEvents()

        # 4. Read input file
        if not read_input_file(self.ctx, self.update_progress):
            self.update_progress(0, "Error during file reading.")
            self.generateButton.setEnabled(True)
            self.resetButton.setEnabled(True)
            return

        # 5. Apply treatments in sequence: Occurrence, Amount, Variance, Trend
        # Apply Occurrence (if selected)
        if self.ctx.occurrence_check and not self.ctx.error_occurred:
            apply_occurrence(self.ctx, self.update_progress)
            if self.ctx.error_occurred:
                self._finalize_process(False)
                return

        # Apply Amount (if selected)
        if self.ctx.amount_check and not self.ctx.error_occurred:
            apply_amount(self.ctx, self.update_progress)
            if self.ctx.error_occurred:
                self._finalize_process(False)
                return

        # Apply Variance (if selected)
        if self.ctx.variance_check and not self.ctx.error_occurred:
            # Calculate means before variance adjustment
            calc_means(self.ctx, self.update_progress)
            if self.ctx.error_occurred:
                self._finalize_process(False)
                return
                
            # Apply variance treatment
            apply_variance(self.ctx, self.update_progress)
            if self.ctx.error_occurred:
                self._finalize_process(False)
                return

        # Apply Trend (if selected)
        if self.ctx.trend_check and not self.ctx.error_occurred:
            apply_trend(self.ctx, self.update_progress)
            if self.ctx.error_occurred:
                self._finalize_process(False)
                return

        # 6. Write output file
        success = False
        if not self.ctx.error_occurred:
            if write_output_file(self.ctx, self.update_progress):
                success = True

        # 7. Show completion status
        self._finalize_process(success)

    # Helper to finalize processing and update UI
    def _finalize_process(self, success):
        # Re-enable buttons
        self.generateButton.setEnabled(True)
        self.resetButton.setEnabled(True)
        QApplication.processEvents()

        if success:
            # Show success message
            self.update_progress(100, "Scenario Generation Complete.")
            msg = f"Scenario Generated Successfully.\n{self.ctx.no_of_days} days processed."
            
            # Include Box-Cox lambda if used
            if self.ctx.variance_check and self.ctx.conditional_check and abs(self.ctx.lamda - GLOBAL_MISSING_CODE) > 1e-6:
                msg += f"\nLambda for Box-Cox (Variance): {self.ctx.lamda:.3f}"
                
            QMessageBox.information(self, "Success", msg)
        elif self.ctx.error_occurred:
            # Show error message
            self.update_progress(0, "Processing failed. Check messages.")
        else:
            # Process did not complete (cancelled or other silent fail)
            self.update_progress(0, "Processing did not complete.")


#############################################################
# Main Application Entry Point / Module Export
#############################################################
# Export the main widget class for use in other modules
ContentWidget = ScenarioGeneratorWidget

# Main function to run the application standalone
def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)  # Apply global stylesheet
    
    window = ScenarioGeneratorWidget()
    window.setWindowTitle("SDSM Scenario Generator")
    window.setGeometry(100, 100, 720, 700)  # Set window size and position
    window.show()
    
    sys.exit(app.exec_())

# Run the app if this module is executed directly
if __name__ == "__main__":
    main()