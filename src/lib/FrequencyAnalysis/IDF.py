import math
import csv 
import matplotlib.pyplot as plt
import configparser
from statistics import mean, stdev
from collections import defaultdict
from PyQt5.QtWidgets import QPushButton, QFileDialog, QWidget,QMessageBox, QVBoxLayout, QTableWidget, QTableWidgetItem, QLabel, QTextEdit,QApplication, QHeaderView,QTabWidget
from datetime import timedelta
from datetime import datetime
from typing import Tuple
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from typing import List

active_windows = []
def run_idf(
    file1_used, file2_used,
    file1_name, file2_name,
    start_date, end_date,
    presentation_type,   # "Tabular" or "Graphical"
    idf_method,          # "Intensity", "Power", or "Linear"
    running_sum_length,
    ensemble_option,
    ensemble_index,
    use_threshold,
    data_period_choice
):
    print(file1_used)
    print(file2_used)
    print(file1_name)
    print(file2_name)
    print (start_date)
    print(end_date)
    print(presentation_type)
    print(idf_method)
    print(running_sum_length)
    print(ensemble_option)
    print(ensemble_index)
    
    print(use_threshold)
    print(data_period_choice)
    parent=None
    # === Constants ===
    END_OF_SECTION = -12345
    
    # === Return periods to model (years) ===
    idf_years_to_model = [1,2,5,10,20]     # Length = 5
    
    # === Durations in hours ===
    idf_hours_array = [0.25, 0.5, 1, 2, 3, 6, 24, 48, 120, 240, 360]  # Length = 11
    IDF_SIZE_OF_HOURS_ARRAY = len(idf_hours_array)
    
    """
    Main function to run the IDF analysis.
    presentation_type: "Tabular" or "Graphical"
    """
    num_ensembles = 1  # Default assumption (if only one column)
    max_window_size=running_sum_length

    if file2_used:
        try:
            with open(file2_name, 'r') as f:
                first_line = f.readline().strip()
    
                # Split line by commas
                values = first_line.split()
    
                # Number of values in the first line = number of ensemble members
                num_ensembles = len(values)
    
            print(f"✅ Detected {num_ensembles} ensemble member(s) in the modelled file.")
    
        except Exception as e:
            print(f"⚠️ Could not read modelled file: {e}")
            num_ensembles = 1  # Fallback to 1 to avoid crashes

    try:
        # -------------------------------------
        # Step 1: Initial Validation and Setup ( Date Validation, Ensemble number validation, Input validation)
        # Call validate_user_inputs 
        # Call Date valid check
        # -------------------------------------
        print("▶ Validating input files and settings...")
        if not validate_user_inputs(file1_used, file2_used, file1_name, file2_name, start_date, end_date):
            #print("❌ Validation failed. Exiting...")
            QMessageBox.critical(
                          parent,
                          "Validation Error",
                          "Validation failed. Please check your input settings and try again."
                      )
            return
        
        if not are_dates_valid(start_date, end_date):
            print("❌ Date range invalid. Exiting IDF analysis.")
            return
        
        if not is_valid_running_sum_length(running_sum_length,parent):
            print("❌ Running Sum length invalid. Exiting IDF analysis.")
            return
        if not validate_ensemble_option(ensemble_option, parent=None):
            print("❌ Ensemble Option invalid. Exiting IDF analysis.")
            return
        # Early in run_idf():
        if not is_ensemble_number_valid(ensemble_option, ensemble_index, num_ensembles,parent):
            print("❌ Invalid ensemble member selected. Exiting.")
            return
        
        if ensemble_option == "Single Member":
           ensemble_index=ensemble_index-1
           print(ensemble_index)
        else:
            ensemble_index=None
        print("✔ Input files valid. Proceeding...")
    
        # -------------------------------------
        # Step 2: Read & Preprocess Observed Data
        # Call read_observed_data
        # -------------------------------------
        config = load_settings("settings.ini")
        global_start_date, _= get_global_dates(config)
        print(global_start_date)
        threshold = float(config.get("Settings", "thresh", fallback=5.0))  # default fallback
        missing_code = float(config.get("Settings", "globalmissingcode", fallback=-999))
        filter_func = build_data_period_filter(data_period_choice)
        yearindicator = int(config.get("Settings", "yearindicator", fallback=366))

        if file1_used:
            print("📥 Reading observed data...")
            
      
            skip_unwanted_observed_data(
                file_path=file1_name,
                global_start_date=global_start_date,
                analysis_start_date=start_date,  # This comes from the run_idf args
                parent=parent
            )
            
            observed_data=read_observed_data(
                 file_path=file1_name, start_date=start_date, end_date=end_date,
                 missing_code=missing_code,
                 use_threshold=use_threshold,
                 threshold=threshold,
                 filter_func=filter_func,
                 parent=None,
                 END_OF_SECTION=END_OF_SECTION
            )
            print(observed_data)
            print(len(observed_data))
        
        # -------------------------------------
        # Step 3: Read & Preprocess Modelled Data
        # -------------------------------------
        if file2_used:
            print("📥 Reading modelled data...")
            print(f"Using ensemble_index = {ensemble_index}")
            skip_unwanted_modelled_data(file_path=file2_name, global_start_date=global_start_date, analysis_start_date=start_date, parent=parent)
            modelled_data, total_mod_years= read_modelled_data(
                    file_path=file2_name,
                    start_date=start_date,
                    end_date=end_date,
                    missing_code=missing_code,
                    use_threshold=use_threshold,
                    threshold=threshold,
                    ensemble_index= ensemble_index,
                    filter_func=filter_func,
                    parent=None,
                    END_OF_SECTION=END_OF_SECTION
                )
            #print(modelled_data)
            #print(total_mod_years)

        # -------------------------------------
        # Step 4: Perform AMS + Running Sum Analysis
        # -------------------------------------
        
        print("🔄 Calculating running sums and AMS...")
        print(f"Using ensemble_index = {ensemble_index}")
        # === For OBSERVED ===
        obs_ams_by_window = {}
        ret_per_obs_by_window = {}

        # === For MODELLED ===
        mod_ams_by_window = {}
        ret_per_mod_by_window = {}

        if file1_used:
                        # -------------------------------------
            # 1. Generate Running Sums
            # -------------------------------------
            obs_running_sums, no_of_obs_sums = calc_running_sums_observed(
                observed_data,
                max_window_size=max_window_size,    # e.g., 8
                END_OF_SECTION=-12345
            )
            
            # -------------------------------------
            # 2. Extract AMS points
            # -------------------------------------
            obs_ams_by_window = calc_ams_observed(
                obs_running_sums,
                no_of_obs_sums,
                max_window_size=max_window_size,
                END_OF_SECTION=-12345
            )
            
            print("Annual Mean Calculations:")
            print(obs_ams_by_window)
            # -------------------------------------
            # 3. Compute Return Periods
            # -------------------------------------
            ret_per_obs_by_window = {}
            
            for window, ams_obs in obs_ams_by_window.items():
                ret_per_obs_by_window[window] = compute_return_periods(ams_obs)
                print(f"✅ Window {window}: {len(ams_obs)} AMS points extracted.")
                print(f"Return periods for window {window}: {ret_per_obs_by_window[window]}")
                print("AMS by window:", obs_ams_by_window)
                print("Return periods by window:", ret_per_obs_by_window)
                N = running_sum_length
                # assume you've already built the full dicts for all windows
            obs_ams = {w: obs_ams_by_window[w] for w in range(1, N+1)}
            ret_per_obs = {w: ret_per_obs_by_window[w] for w in range(1, N+1)}
            ret_per_obs_for_intensity = {
            window: compute_return_periods(values)
            for window, values in obs_ams.items()
            if values  # skip empty
            }
            print("Observation Ams")
            print(obs_ams)
            print("Return Per Obs:")
            print(ret_per_obs)
    
        if file2_used:
            # Step 1: Calculate running sums for each ensemble
            print("Calculating Running sums for Modelled")
            mod_running_sums_by_ensemble = []
            #for ensemble_index, ensemble_series in enumerate(modelled_data):
              #  print(f"\nEnsemble {ensemble_index + 1} - First 375 values:")
                #print(ensemble_series[:375])
            for ensemble_series in modelled_data:
                running_sums, no_of_sums = calc_running_sums_observed(
                    ensemble_series,  # reusing same function
                    max_window_size=max_window_size,
                    END_OF_SECTION=-12345
                )
                mod_running_sums_by_ensemble.append(running_sums)
                 # 📌 Print results per ensemble
                #print(f"\n📊 Running Sum values (first 750 entries per window) - Ensemble {ensemble_index + 1}:")
                #for window in range(1, max_window_size + 1):
                 #   print(f"  Window {window}: {running_sums[window][:750]}")
                
            # Step 2: Extract AMS from each ensemble's running sums
            print("\n📈 Extracting AMS from Running Sums")
            ams_by_ensemble = []
            
            for ensemble_index, running_sums in enumerate(mod_running_sums_by_ensemble):
                ams = calc_ams_observed(
                    running_sums,
                    no_of_obs_sums=None,  # not needed
                    max_window_size=max_window_size,
                    END_OF_SECTION=-12345
                )
                ams_by_ensemble.append(ams)
            print("After Running Sums")
            print(f"Using ensemble_index = {ensemble_index}")
                # 🔍 Print per ensemble
               # print(f"\n📊 AMS values - Ensemble {ensemble_index + 1}:")
               # for window in range(1, max_window_size + 1):
                #    print(f"  Window {window}: {ams[window]}")

            # 🧮 Step 2.5: Sort each ensemble's AMS (mimicking VBA)
            for ensemble in ams_by_ensemble:
                for window in ensemble:
                    ensemble[window] = sorted(ensemble[window], reverse=True)

            # Step 3: Compute mean AMS across ensembles
            mod_ams_by_window = {}
            for window in range(1, max_window_size + 1):
                window_ams_all_ensembles = [ams[window] for ams in ams_by_ensemble if window in ams]
                mod_ams_by_window[window] = compute_ensemble_mean_ams(window_ams_all_ensembles)
        
            #print("Printing output after sorting and ams mean calcs")
           # print(mod_ams_by_window)
            # Step 4: Compute return periods for mean AMS
            ret_per_mod_by_window = {
                window: compute_return_periods(mod_ams_by_window[window])
                for window in mod_ams_by_window
            }
        
            print("Modelled AMS:")
            #print(mod_ams_by_window)
            print("Return Periods Modelled:")
            #print(ret_per_mod_by_window)
            

        
        # -------------------------------------
        # Step 6: Perform Scaling
        # -------------------------------------
        print("📈 Scaling AMS to IDF table...")
        sdsm_scaled_table_obs = {}
        sdsm_scaled_table_mod = {}

        beta_obs = None
        beta_mod = None

        if idf_method == "Intensity":
           
            
            if file1_used:
                sdsm_scaled_table_obs, beta_obs = intensity_scaling_observed_moments(obs_ams_by_window, idf_years_to_model)
        
            if file2_used:
                sdsm_scaled_table_mod,beta_mod = intensity_scaling_modelled(mod_ams_by_window,idf_years_to_model,idf_hours_array)

            print(sdsm_scaled_table_obs)
            print(sdsm_scaled_table_mod)
        
        elif idf_method == "Power":
            
            if file1_used:
            
                print("🔢 Performing Parameter Power Scaling...")
                # Step 1
                obs_mean, obs_sd, obs_parm_values = parameter_scaling_step1(
                    obs_ams_by_window=obs_ams, 
                    global_missing_code=missing_code,
                    max_window_size=running_sum_length
                )
            
                # Step 2
                slope_values = calc_slopes_obs_values(
                    obs_parm_values=obs_parm_values, 
                    global_missing_code=missing_code
                )
                ObsSlopeValues = [slope_values["beta_power"], slope_values["mu_power"]]
            
                # Step 3
                sdsm_scaled_table_obs = parameter_power_scaling(
                    idf_years_to_model=idf_years_to_model,
                    idf_hours_array=idf_hours_array,
                    obs_parm_values=obs_parm_values,
                    mu_slope=slope_values["mu_power"],
                    beta_slope=slope_values["beta_power"],
                    global_missing_code=missing_code
                )
                  # Not using modelled yet
            if file2_used:
                sdsm_scaled_table_mod = {}
                print("🔢 Performing Parameter Power Scaling for Modelled...")

                mod_mean, mod_sd, mod_parm_values = parameter_scaling_step1(
                    obs_ams_by_window=mod_ams_by_window,
                    global_missing_code=missing_code,
                    max_window_size=running_sum_length
                )
             
                mod_slope_values = calc_slopes_obs_values(   # Same function reused
                    obs_parm_values=mod_parm_values,
                    global_missing_code=missing_code
                )
                
                ModSlopeValues = [mod_slope_values["beta_power"], mod_slope_values["mu_power"]]
             
                sdsm_scaled_table_mod = parameter_power_scaling(
                    idf_years_to_model=idf_years_to_model,
                    idf_hours_array=idf_hours_array,
                    obs_parm_values=mod_parm_values,  # same parameter name, reused for modelled
                    mu_slope=mod_slope_values["mu_power"],
                    beta_slope=mod_slope_values["beta_power"],
                    global_missing_code=missing_code
                )
            print("✅ Parameter Power Scaling completed.")
        
        else:

            if file1_used:
                obs_mean, obs_sd, obs_parm_values = parameter_scaling_step1(
                    obs_ams_by_window=obs_ams, 
                    global_missing_code=missing_code,
                    max_window_size=running_sum_length
                )
            
                # Step 2
                slope_values = calc_slopes_obs_values(
                    obs_parm_values=obs_parm_values, 
                    global_missing_code=missing_code
                )
                ObsSlopeValues = [slope_values["beta_linear"], slope_values["mu_linear"]]
            
            
                print("🔢 Performing Parameter Linear Scaling...")
                sdsm_scaled_table_obs = parameter_linear_scaling_final(
                 file1_used, file2_used,
                 IDFYearsToModel=idf_years_to_model, IDFHoursArray=idf_hours_array,
                 ObsParmValues=obs_parm_values, ObsSlopeValues=ObsSlopeValues,
                 ModParmValues=None, ModSlopeValues=None
                )    
                sdsm_scaled_table_mod = {}  # Not yet implemented for modelled
            
            if file2_used:
                sdsm_scaled_table_mod = {}
                print("🔢 Performing Parameter Linear Scaling for Modelled...")
            
                # Reuse existing step 1: extract modelled parameters
                mod_mean, mod_sd, mod_parm_values = parameter_scaling_step1(
                    obs_ams_by_window=mod_ams_by_window,
                    global_missing_code=missing_code,
                    max_window_size=running_sum_length
                )
            
                # Reuse existing slope calc logic
                mod_slope_values = calc_slopes_obs_values(
                    obs_parm_values=mod_parm_values,
                    global_missing_code=missing_code
                )
            
                # Store for later if needed
                ModSlopeValues = [mod_slope_values["beta_linear"], mod_slope_values["mu_linear"]]
                #print("mod_parm_values[1] =", mod_parm_values.get(1))
                # Final linear scaling table
                for rp in idf_years_to_model:
                    sdsm_scaled_table_mod[rp] = {}
                    for h in idf_hours_array:
                        # Base values at 24h (day 1 = index 1)
                        
                        mu_base = mod_parm_values[1]['mu']
                        beta_base = mod_parm_values[1]['beta']

            
                        mu_slope = ModSlopeValues[1]  # from beta, mu order
                        beta_slope = ModSlopeValues[0]
            
                        first_part = mu_base - ((24 - h) * mu_slope)
                        second_part = beta_base - ((24 - h) * beta_slope)
                        

                        if rp == 1:
                            logbit = math.log(-math.log(1 - 1 / 1.01))
                        else:
                            logbit = math.log(-math.log(1 - 1 / rp))
            
                        intensity = (first_part - (second_part * logbit)) / h
                        sdsm_scaled_table_mod[rp][h] = intensity
                        #print(f"Hours={h}, RP={rp} ⇒ μ={first_part:.2f}, β={second_part:.2f}, LogBit={logbit:.4f}, Intensity={intensity:.2f}")

                print("✅ Parameter Linear Scaling completed.")

        print(ensemble_option)
        print(ensemble_index)
        print("📤 Generating final output...")
        show_beta_values(beta_obs, beta_mod)
        if presentation_type == "Tabular":
           result_window = present_results_as_table(
        idf_hours_array,
        idf_years_to_model,
        sdsm_scaled_table_obs,
        sdsm_scaled_table_mod # ← this is optional and will be None if not used
        )
        
        else:
            present_results_as_graph(idf_hours_array,
        idf_years_to_model,
        sdsm_scaled_table_obs,
        sdsm_scaled_table_mod)
        
        print("✅ IDF Analysis Complete.")

    except Exception as e:
        handle_error(e)
        mini_reset()
        return None
        
def load_settings(settings_path='src\lib\settings.ini'):
    config = configparser.ConfigParser()
    config.read("settings.ini")  # use full or relative path to your actual file
    return config

def has_sufficient_data(observed_data, modelled_data, min_points=100):
    """
    Validates that observed and modelled data have enough values to proceed.
    
    Args:
        observed_data: list of floats
        modelled_data: list of lists (optional)
        min_points: minimum values required per source (default 100)
    
    Returns:
        bool: True if all conditions are satisfied, else False
    """
    if observed_data and len(observed_data) < min_points:
        return False

    if modelled_data:
        for i, ensemble in enumerate(modelled_data):
            if len(ensemble) < min_points:
                return False

    return True


def get_global_dates(config):
    try:
        # Parse as DD/MM/YYYY (from your settings)
        global_start = datetime.strptime(config['Settings']['globalsdate'], '%d/%m/%Y').date()
        global_end = datetime.strptime(config['Settings']['globaledate'], '%d/%m/%Y').date()
        return global_start, global_end
    except Exception as e:
        raise ValueError(f"Error reading global dates: {e}")

def is_valid_running_sum_length(value: int, parent=None) -> bool:
    """
    Validates that the running sum length is an integer between 2 and 15.
    Shows a QMessageBox if invalid.
    """
    if not isinstance(value, int):
        QMessageBox.critical(parent, "Invalid Input", "Running sum value must be a whole number.")
        return False

    if value < 2 or value > 15:
        QMessageBox.critical(parent, "Invalid Input", "Running sum must be between 2 and 15 days.")
        return False

    return True

def validate_ensemble_option(option, parent=None) -> bool:
    """
    Ensures ensemble selection is either 'Single Member' or 'All Members'.
    """
    if option not in ["Single Member", "All Members"]:
        QMessageBox.critical(
            parent,
            "Error Message",
            "❌ You can only select All Ensembles or One Ensemble for this analysis."
        )
        return False
    return True

def is_ensemble_number_valid(ensemble_option, ensemble_index, num_ensembles, parent=None):
    """
    Validates that the selected ensemble index is valid if 'Single Member' is chosen.

    Parameters:
    - ensemble_option: String ("Single Member", "All Members", etc.)
    - ensemble_index: Integer from the SpinBox (0-based index).
    - num_ensembles: Number of ensemble columns found in the modelled file.
    - parent: QWidget (used for QMessageBox display).

    Returns:
    - True if valid or not needed; False if invalid and error shown.
    """
    if ensemble_option == "Single Member":
        
        if not isinstance(ensemble_index, int):
            
            QMessageBox.critical(
                parent,
                "Invalid Input",
                "Ensemble index must be an integer."
            )
            return False

        if ensemble_index < 0 or ensemble_index >= num_ensembles:
            QMessageBox.critical(
                parent,
                "Ensemble Selection Error",
                f"The selected ensemble member index ({ensemble_index}) is invalid.\n"
                f"Available indices: 0 to {num_ensembles - 1}."
            )
            return False

    return True

def validate_user_inputs(file1_used, file2_used, file1_name, file2_name, start_date, end_date, parent=None):
    """
    Ensures necessary files, parameters, and flags are set.
    Returns True if all inputs are valid, else False.

    Parameters:
    - file1_used (bool): Whether observed file is used
    - file2_used (bool): Whether modelled file is used
    - file1_name (str): Observed file path
    - file2_name (str): Modelled file path
    - start_date (datetime.date or QDate): Start of analysis
    - end_date (datetime.date or QDate): End of analysis
    - parent (QWidget): Parent widget for error message popups
    """

    # At least one file must be used
    if not file1_used and not file2_used:
        QMessageBox.critical(parent, "Validation Error", "❗ At least one data file (observed or modelled) must be selected.")
        return False

    # Observed file check
    if file1_used:
        if not file1_name or len(file1_name.strip()) < 5:
            QMessageBox.critical(parent, "File Error", "❗ Observed data file is missing or the filename is too short.")
            return False

    # Modelled file check
    if file2_used:
        if not file2_name or len(file2_name.strip()) < 5:
            QMessageBox.critical(parent, "File Error", "❗ Modelled data file is missing or the filename is too short.")
            return False

    # Date check
    if start_date is None or end_date is None:
        QMessageBox.critical(parent, "Date Error", "❗ Start and End dates must be defined.")
        return False

    return True

def are_dates_valid(start_date_raw, end_date_raw):
    """
    Validate the analysis date range based on the following rules:
    1. Both start and end dates must be valid QDate objects.
    2. The start date must not be later than the end date.
    3. The range between start and end must not exceed 150 years.

    Parameters:
    - start_qdate (QDate): Start date selected in the UI.
    - end_qdate (QDate): End date selected in the UI.

    Returns:
    - bool: True if the dates are valid, False otherwise.
    """
    try:
        # Convert QDate to Python date objects
        start = ensure_pydate(start_date_raw)
        end = ensure_pydate(end_date_raw)

        # Check chronological order
        if start > end:
            print("❌ Start date must be before or equal to the end date.")
            QMessageBox.critical(None, "Invalid Date Range", "❌ Start date must be before or equal to the end date.")
            return False
        
        # Ensure range is at least 10 years
        if (end.year - start.year) < 10:
            print("❌ You must select at least ten years of data for IDF analysis.")
            QMessageBox.warning(None, "Invalid Date Range", "❌ You must select at least ten years of data for IDF analysis.")
            return False 

        # Check for excessively long date ranges
        if (end.year - start.year) > 150:
            print("❌ Analysis period must not exceed 150 years.")
            QMessageBox.warning(None, "Invalid Date Range", "❌ Analysis period must not exceed 150 years.")
            return False

        # If all checks pass
        return True

    except Exception as e:
        print(f"❌ Date validation failed due to an exception: {e}")
        return False
    
def ensure_pydate(qdate_or_date):
    """
    Convert QDate to Python date, or return it directly if it's already a date.
    """
    if hasattr(qdate_or_date, 'toPyDate'):
        return qdate_or_date.toPyDate()
    return qdate_or_date

def skip_unwanted_observed_data(file_path, global_start_date, analysis_start_date, parent=None):
    """
        Skips lines in the observed data file until the current date matches the user-selected analysis start date.
    
        Parameters:
        - file_path: Path to the observed data file
        - global_start_date: The start date of the file data (datetime.date)
        - analysis_start_date: User's selected start date (datetime.date)
        - parent: Optional widget for UI feedback
        """
    
    try:
        current_date = global_start_date
        total_to_skip = (analysis_start_date - global_start_date).days
        lines_skipped = 0

        skipped_lines = []  # Store skipped values if needed (optional)

        with open(file_path, 'r') as f:
            while current_date < analysis_start_date:
                line = f.readline()
                if not line:
                    break  # End of file before expected
                lines_skipped += 1
                current_date += timedelta(days=1)

                # Optional: update a progress bar here using parent or console
                percent = int((lines_skipped / total_to_skip) * 100)
                print(f"Skipping observed data: {percent}%")

        print(f"✅ Skipped {lines_skipped} lines before {analysis_start_date}")
        return lines_skipped

    except Exception as e:
        print(f"❌ Error while skipping observed data: {e}")
        return 0



def read_observed_data(
                 file_path, start_date, end_date,
                 missing_code,
                 use_threshold,
                 threshold,
                 filter_func,
                 parent,
                 END_OF_SECTION,
                     ):
    
    observed_data = []
    current_date = start_date
    total_days = (end_date - start_date).days + 1
    total_numbers = 0
    last_year = current_date.year
    total_obs_years = 1
    some_data_valid = False
    end_of_section_marker = END_OF_SECTION

    try:
        with open(file_path, 'r') as f:
            for _ in range(total_days):
                line = f.readline()
                if not line:
                    break

                try:
                    value = float(line.strip())
                except ValueError:
                    continue  # skip non-numeric

                if filter_func and not filter_func(current_date):
                    current_date += timedelta(days=1)
                    continue
                
                valid_value = not (value == missing_code or (use_threshold and value < threshold))
                
                # Handle section change (new year)
                if current_date.year > last_year and some_data_valid:
                    observed_data.append(end_of_section_marker)
                    total_obs_years += 1

                    # Validate data
                    
                if valid_value:
                   some_data_valid = True
                   observed_data.append(value)

                last_year = current_date.year
                current_date += timedelta(days=1)
                total_numbers += 1

                percent = int((total_numbers / total_days) * 100)
                print(f"Reading Observed Data: {percent}%")

        # Final end marker
        observed_data.append(end_of_section_marker)
        print("✅ Finished reading observed data.")
        
        return observed_data

    except Exception as e:
        print(f"❌ Error reading observed data: {e}")
        return []

def build_data_period_filter(choice: str):
    """
    Returns a function that checks if a date is allowed based on the dataPeriodChoice.
    """
    choice = choice.strip().title()

    if choice == "All Data":
        return lambda date: True
    elif choice == "Winter":
        return lambda date: date.month in [12, 1, 2]
    elif choice == "Spring":
        return lambda date: date.month in [3, 4, 5]
    elif choice == "Summer":
        return lambda date: date.month in [6, 7, 8]
    elif choice == "Autumn":
        return lambda date: date.month in [9, 10, 11]
    else:
        # Assume it's a month like "January"
        month_lookup = {
            "January": 1, "February": 2, "March": 3, "April": 4,
            "May": 5, "June": 6, "July": 7, "August": 8,
            "September": 9, "October": 10, "November": 11, "December": 12
        }
        month = month_lookup.get(choice, None)
        if month is None:
            return lambda date: True  # fallback: allow all
        return lambda date: date.month == month

def skip_unwanted_modelled_data(file_path, global_start_date, analysis_start_date, parent=None):
    """
    Skips lines in a modelled data file before the analysis start date.
    Returns number of lines skipped.
    """
    try:
        print(f"global_start_date: {global_start_date} ({type(global_start_date)})")
        print(f"analysis_start_date: {analysis_start_date} ({type(analysis_start_date)})") 
        current_date = global_start_date
        total_to_skip = (analysis_start_date - global_start_date).days
        lines_skipped = 0
        
        with open(file_path, 'r') as f:
            while current_date < analysis_start_date:
                line = f.readline()
                if not line:
                    break
                lines_skipped += 1
                current_date += timedelta(days=1)
                percent = int((lines_skipped / total_to_skip) * 100)
                print(f"Skipping modelled data: {percent}%")
            # ✅ Ensure 100% is printed at the end
        if lines_skipped == total_to_skip:
            print(lines_skipped)
            print("Skipping modelled data: 100%")
        return lines_skipped

    except Exception as e:
        print(f"❌ Error skipping modelled data: {e}")
        return 0



def read_modelled_data(
    file_path,
    start_date,
    end_date,
    missing_code,
    use_threshold,
    threshold,
    ensemble_index,
    filter_func,         # e.g., seasonal/month selector, or None
    parent=None,         # for QMessageBox (optional)
    END_OF_SECTION=-12345
):
    """
    Reads and filters modelled data from file.

    Returns:
    - filtered_data: list of lists (each sublist is a time series for one ensemble)
    - total_mod_years: number of complete years detected based on date
    """
    current_date = start_date
    total_days = (end_date - start_date).days + 1
    full_rows = []
    total_mod_years = 0
    days_in_year = 0
    last_year = start_date.year

    with open(file_path, 'r') as f:
        for _ in range(total_days):
            line = f.readline()
            if not line:
                break

            try:
                values = [float(val.strip()) for val in line.strip().split()]
            except ValueError:
                continue  # skip malformed lines

            if filter_func is None or filter_func(current_date):
                full_rows.append(values)
            
            current_date += timedelta(days=1)
            days_in_year += 1

            # Insert end-of-section marker for all ensembles at year end
            if current_date.year > last_year:
                full_rows.append([END_OF_SECTION] * len(values))
                total_mod_years += 1
                days_in_year = 0
                last_year = current_date.year

        # Always finish last year with section marker
        if days_in_year > 0:
            full_rows.append([END_OF_SECTION] * len(full_rows[0]))
            total_mod_years += 1

    # Transpose to get per-ensemble series
        transposed = [[row[i] for row in full_rows] for i in range(len(full_rows[0]))]

        # ✅ If a single ensemble index is selected, return only that one
        if ensemble_index is not None:
            if 0 <= ensemble_index < len(transposed):
                return [transposed[ensemble_index]], total_mod_years
            else:
                print(f"⚠️ Ensemble index {ensemble_index} out of range. Returning first ensemble.")
                return [transposed[0]], total_mod_years
        
        return transposed, total_mod_years
            
    #except Exception as e:
        #print(f"❌ Error reading modelled data: {e}")
        #return [], 0

# ✅ Utility: Split data year-wise
def split_into_years(observed_data, END_OF_SECTION):
    years = []
    current_year = []

    for val in observed_data:
        if val == END_OF_SECTION:
            if current_year:
                years.append(current_year)
                current_year = []
        else:
            current_year.append(val)

    if current_year:
        years.append(current_year)

    return years

def calc_running_sums_observed(observed_data, max_window_size, END_OF_SECTION):
    """
    observed_data: list of floats _including_ one END_OF_SECTION sentinel at the end of each year
    returns: 
      obs_running_sums:  dict[window] = flat list of sums _and_ sentinels
      no_of_obs_sums:      dict[window] = len(obs_running_sums[window])
    """
    obs_running_sums = {}
    no_of_obs_sums = {}

    # first, split your flat array into per‐year chunks
    years = []
    current = []
    for v in observed_data:
        if v == END_OF_SECTION:
            years.append(current)
            current = []
        else:
            current.append(v)
    # (ignore any trailing incomplete year)

    for window in range(1, max_window_size + 1):
        series = []
        for year in years:
            # 1) for each valid slide in this year
            for i in range(len(year) - window + 1):
                series.append(sum(year[i : i + window]))
            # 2) then one sentinel
            series.append(END_OF_SECTION)

        obs_running_sums[window] = series
        no_of_obs_sums[window] = len(series)

    return obs_running_sums, no_of_obs_sums



def calc_ams_observed(obs_running_sums, no_of_obs_sums, max_window_size, END_OF_SECTION):
    obs_ams_by_window = {}

    for window in range(1, max_window_size + 1):
        series = obs_running_sums[window]
        ams = []
        max_so_far = float('-inf')

        for val in series:
            if val == END_OF_SECTION:
                #print(f"End of year. Max was: {max_so_far}")
                if max_so_far > float('-inf'):
                    ams.append(max_so_far)
                max_so_far = float('-inf')
            else:
                if val > max_so_far:
                   # print(f"New max: {val}")
                    max_so_far = val

        if max_so_far > float('-inf'):
            ams.append(max_so_far)

        obs_ams_by_window[window] = ams

    return obs_ams_by_window


def compute_return_periods(ams_series):
    sorted_data = sorted(ams_series, reverse=True)
    n = len(sorted_data)
    ret_periods = []
    for rank, value in enumerate(sorted_data, start=1):
        rp = n / rank           # <-- VB does N / rank
        ret_periods.append((rp, value))

    return ret_periods

            
            # 3. Compute RP per ensemble
def compute_return_periods_modelled(ams_lists):
    """
    Compute return periods for each ensemble's AMS list.
    Returns: List of lists of (RP, Value) tuples.
    """
    return [
        compute_return_periods(ams)
        for ams in ams_lists
    ]

            
def compute_ensemble_mean_ams(ams_lists):
    """
    Calculates the mean AMS per year across all ensemble members.
    """
    transposed = zip(*ams_lists)
    return [sum(year) / len(year) for year in transposed]


def intensity_scaling_observed_moments(ams_by_window, idf_years):
    print("\n🔎 Step 1: AMS by window")
    for window, values in ams_by_window.items():
        print(f"Window {window}: {values}")

    # Step 2: Normalize AMS by window size
    normalized = {
        window: [v / window for v in values]
        for window, values in ams_by_window.items()
    }
    print("\n🔎 Step 2: Normalized AMS")
    for window, values in normalized.items():
        print(f"Window {window}: {values[:10]} ...")

    # Step 3: Calculate NCMs (non-central moments) for powers q
    powers_q = [0.5, 1, 1.5, 2, 2.5, 3]
    moments_table = defaultdict(list)

    for window in sorted(normalized):
        for q in powers_q:
            powered = [v**q for v in normalized[window]]
            m_q = mean(powered)
            print(m_q)
            moments_table[q].append(math.log(m_q))  # Step 4: log

    print("\n🔎 Step 3 & 4: Log Moments Table")
    for q in powers_q:
        print(f"q={q}: {moments_table[q]}")

    # Step 5: Compute slope (k-values) for each q
    x_vals = [math.log(window * 24) for window in sorted(normalized)]
    k_values = []
    for q in powers_q:
        y_vals = moments_table[q]
        n = len(x_vals)
        sum_x = sum(x_vals)
        sum_y = sum(y_vals)
        sum_xx = sum(x**2 for x in x_vals)
        sum_xy = sum(x*y for x, y in zip(x_vals, y_vals))
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x**2)
        k_values.append(slope)

    print("\n🔎 Step 5: Slopes (k-values) for each q")
    for q, k in zip(powers_q, k_values):
        print(f"q={q:.1f}, k={k:.6f}")

    # Step 6: Regression of k vs q to get Beta
    sum_q = sum(powers_q)
    sum_k = sum(k_values)
    sum_qq = sum(q**2 for q in powers_q)
    sum_qk = sum(q*k for q, k in zip(powers_q, k_values))
    n = len(powers_q)
    beta = (n * sum_qk - sum_q * sum_k) / (n * sum_qq - sum_q**2)

    print(f"\n📐 Step 6: Final Beta = {beta:.6f}")

    # Step 7: Gumbel Parameters
    day1 = normalized[1]  # Use 1-day normalized AMS
    mu = mean(day1) / 24
    sigma = stdev(day1) / 24
    gumbel_mu = mu - 0.45 * sigma
    gumbel_beta = sigma * 0.7797

    print(f"\n📐 Step 7: Gumbel Params -> mu={gumbel_mu:.6f}, beta={gumbel_beta:.6f}")

    # Step 8: Estimate 24h intensities for return periods
    idf_table = defaultdict(dict)
    for T in idf_years:
        T_for_calc = 1.01 if T == 1 else T  # 🛠 Adjust T=1 to 1.01 internally
        try:
            xt = gumbel_mu - gumbel_beta * math.log(-math.log(1 - 1 / T_for_calc))
        except:
            continue
        idf_table[T][24.0] = xt

    # Step 9: Extrapolate to other durations
    for T in idf_years:
        if T not in idf_table:
            continue
        x_24 = idf_table[T][24.0]
        for h in [0.25, 0.5, 1, 2, 3, 6, 24, 48, 120, 240, 360]:
            if h == 24:
                continue
            intensity = x_24 * (h / 24)**beta
            idf_table[T][h] = intensity
        

    print("\n📊 Final IDF Table")
    for T in idf_years:
        print(f"Return Period {T} years:")
        for h in sorted(idf_table[T]):
            print(f"  {h} hours -> {idf_table[T][h]:.2f} mm/hr")

    return idf_table, beta

def build_year_array(observed_data, start_date, END_OF_SECTION, timestep_hours=1):
    """
    Build a list of years corresponding to each observation point.
    
    Parameters:
        observed_data: list of values (may contain END_OF_SECTION)
        start_date: datetime.datetime object
        END_OF_SECTION: value marking end of a section
        timestep_hours: time between data points (default = 1 hour)
    
    Returns:
        years list corresponding to each value
    """
    years = []
    current_date = start_date

    for value in observed_data:
        if value == END_OF_SECTION:
            # End of year (or end of a block)
            # Let's assume after END_OF_SECTION, we start a new year
            current_date = datetime(current_date.year + 1, 1, 1)
            continue

        years.append(current_date.year)
        current_date += timedelta(hours=timestep_hours)
    
    return years
# Modelled Intensity Scaling Workflow (replicating Observed steps)

def intensity_scaling_modelled(
    modelled_ams_by_window: dict,
    idf_years_to_model: list,
    idf_hours_array: list,
):
    import math
    from collections import defaultdict
    import numpy as np

    print("\n🔍 Step 1: Received AMS for modelled data")
    for w, vals in modelled_ams_by_window.items():
        print(f"Window {w}: {vals[:5]} ... total {len(vals)}")

    # --- Step 2: Normalize AMS by dividing by window (running sum length) ---
    print("\n🔍 Step 2: Normalized AMS by window")
    normalized = {}
    for w, vals in modelled_ams_by_window.items():
        normed = [round(v / w, 1) for v in vals]
        normalized[w] = normed
        print(f"Window {w}: {normed[:5]} ...")

    # --- Step 3: Compute means of NCMs for q = 0.5 to 3 ---
    print("\n🔍 Step 3: Non-central moments")
    q_values = [0.5, 1, 1.5, 2, 2.5, 3]
    moments_table = defaultdict(list)

    for q in q_values:
        for w in sorted(normalized):
            ncm = np.mean([val ** q for val in normalized[w]])
            log_ncm = math.log10(ncm)
            moments_table[q].append((w, log_ncm))
        print(f"q = {q}: {[f'{x[1]:.2f}' for x in moments_table[q]]}")

    # --- Step 4: Regress each q column against log(window) ---
    print("\n🔍 Step 4: Slopes (k values)")
    k_values = {}
    for q in q_values:
        x = [math.log10(w * 24) for w, _ in moments_table[q]]
        y = [v for _, v in moments_table[q]]
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xx = sum([xi**2 for xi in x])
        sum_xy = sum([xi * yi for xi, yi in zip(x, y)])
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x**2)
        k_values[q] = slope
        print(f"k({q}) = {slope:.4f}")

    # --- Step 5: Fit beta using linear regression on (q, k) ---
    print("\n🔍 Step 5: Final regression for Beta")
    q_list = q_values
    k_list = [k_values[q] for q in q_list]
    q_mean = sum(q_list) / len(q_list)
    k_mean = sum(k_list) / len(k_list)
    num = sum((q - q_mean) * (k - k_mean) for q, k in zip(q_list, k_list))
    den = sum((q - q_mean)**2 for q in q_list)
    beta = num / den
    print(f"✅ Beta = {beta:.4f}")

    # --- Step 6: Gumbel fitting using mean/sd of 1-day AMS ---
    print("\n🔍 Step 6: Gumbel Fit (mu, beta) for T")
    from statistics import mean, stdev
    ams_1day = modelled_ams_by_window[1]
    mu = mean(ams_1day) / 24
    sd = stdev(ams_1day) / 24
    gumbel_mu = mu - 0.45 * sd
    gumbel_beta = sd * 0.7797
    print(f"Mu = {gumbel_mu:.4f}, Beta = {gumbel_beta:.4f}")

    # --- Step 7: Build modelled IDF table ---
    idf_table = defaultdict(dict)
    for T in idf_years_to_model:
        T_adj = T if T > 1 else 1.01
        try:
            xt = gumbel_mu - gumbel_beta * math.log(-math.log(1 - 1 / T_adj))
        except:
            continue
        idf_table[T][24.0] = xt

    for T in idf_years_to_model:
        if T not in idf_table:
            continue
        x_24 = idf_table[T][24.0]
        for h in idf_hours_array:
            if h == 24:
                continue
            intensity = x_24 * (h / 24)**beta
            idf_table[T][h] = intensity


    print("\n📊 Final IDF Table (Modelled)")
    for T in idf_years_to_model:
        print(f"Return Period {T} years:")
        for h in sorted(idf_table[T]):
            print(f"  {h} hrs -> {idf_table[T][h]:.2f} mm/hr")

    return idf_table, beta

    
def extract_ams_by_year_fullseries(data, years, END_OF_SECTION, missing_code):
    """
    Extracts AMS (Annual Maximum Series) points from full series, splitting per year.
    
    Arguments:
    - data: list of rainfall values (flat list for entire timespan)
    - years: list of corresponding years for each data point (must be same length as data)
    - END_OF_SECTION: marker for missing/broken data sections
    - missing_code: value to use for missing data

    Returns:
    - ams_points: dict {year: max value}
    """
    ams_per_year = {}
    temp_values = []
    current_year = years[0]
    if len(data) != len(years):
       print(f"❌ Length mismatch: data has {len(data)} points, years has {len(years)} points.")
       raise ValueError("Data and Years array must have the same length.")
    
    for idx, value in enumerate(data):
        year = years[idx]

        # New year detected
        if year != current_year:
            if temp_values:
                max_val = max(temp_values)
                ams_per_year[current_year] = max_val
            else:
                ams_per_year[current_year] = missing_code

            temp_values = []
            current_year = year

        # If valid data
        if value != END_OF_SECTION:
            temp_values.append(value)

    # Final year catch
    if temp_values:
        max_val = max(temp_values)
        ams_per_year[current_year] = max_val

    return ams_per_year
    
def calculate_ams_per_window(obs_running_sums_by_window, end_of_section_value=-12345):
    """
    Given the running sum arrays, extract Annual Maximum Series (AMS) points for each window (duration).

    obs_running_sums_by_window: dict {running_sum_window: [values]} 
    end_of_section_value: marker for missing data (default = -12345)

    Returns: ams_points_by_window: dict {running_sum_window: [AMS points]}
    """

    ams_points_by_window = {}

    for window, values in obs_running_sums_by_window.items():
        ams_points_by_window[window] = []
        current_max = -float('inf')

        for val in values:
            if val == end_of_section_value:
                # End of section -> store the maximum if valid
                if current_max != -float('inf'):
                    ams_points_by_window[window].append(current_max)
                current_max = -float('inf')  # reset for next section
            else:
                if val > current_max:
                    current_max = val

        # Edge case: if there was no end marker at the very end
        if current_max != -float('inf'):
            ams_points_by_window[window].append(current_max)

    return ams_points_by_window

    
def set_obs_scalings(obs_ams_by_window, ret_periods_by_window, idf_years):
    """
    Constructs the ObsScalings table from AMS and return period data.
    
    obs_ams_by_window: dict {window: [AMS values]}
    ret_periods_by_window: dict {window: [(ret_period, value)]}
    idf_years: list of years to model, e.g., [1, 2, 5, 10, 20]
    
    Returns: obs_scalings[year][window]
    """
    obs_scalings = {}

    valid_window_found = False

    for rp in idf_years:
        obs_scalings[rp] = {}
    
        for window, rp_data in ret_periods_by_window.items():
            if not rp_data:
                print(f"⚠️ No return period data for window {window} and RP {rp}")
                continue
    
            valid_window_found = True
    
            # Find value with minimum absolute diff from return period
            #closest_val = min(rp_data, key=lambda x: abs(x[0] - rp))
            #value = closest_val[1]
            value = find_best_rp_match(rp_data, rp)

            intensity = round(value / (window * 24), 14)  # simulate VBA precision
            obs_scalings[rp][window] = intensity
    
    # Abort if nothing was calculated
    if not valid_window_found:
        raise ValueError("No valid return period data found for any window.")
    
    
    
    return obs_scalings

def find_best_rp_match(rp_data, target_rp):
    # Simulate VB's reverse loop: from end to start
    best_so_far = float("inf")
    best_val = None
    for rp, val in reversed(rp_data):
        diff = abs(rp - target_rp)
        if diff < best_so_far:
            best_so_far = diff
            best_val = val
    return best_val


def safe_log10(x):
    """ Simulate VBA's limited precision during log10 """
    return round(math.log10(x), 14)

def calc_obs_scalings_linear_regression(obs_scalings_for_rp: dict) -> Tuple[float, float]:
    """
    Performs log-log regression for a specific return period across durations,
    simulating VBA float rounding.
    """
    X = []
    Y = []

    for window, intensity in obs_scalings_for_rp.items():
        hours = window * 24
        if intensity <= 0:
            continue  # skip invalid values

        x = round(math.log10(hours), 14)      # VBA: Log(24*i)/Log(10#)
        y = round(math.log10(intensity), 14)  # VBA: Log(intensity)/Log(10#)  # <- limited precision

        X.append(x)
        Y.append(y)

    n = len(X)
    if n < 2:
        return 0, 0

    sum_x = sum(X)
    sum_y = sum(Y)
    sum_xx = sum(x**2 for x in X)
    sum_xy = sum(x*y for x, y in zip(X, Y))

    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x**2)
    intercept = (sum_y - slope * sum_x) / n

    return round(intercept, 14), round(slope, 14)


def calc_sdsm_scaled_table(idf_years, idf_hours_array, idf_params):
    """
    Generates the final IDF intensity table using the fitted parameters.
    
    idf_params: dict {year: (intercept, slope)}
    Returns: table[year][duration] as nested dict
    """
    table = {}

    for year in idf_years:
        intercept, slope = idf_params.get(year, (0, 0))
        table[year] = {}

        for duration in idf_hours_array:
            intensity = (10 ** intercept) * (duration ** slope)
            table[year][duration] = intensity
    print(table)
    return table


def parameter_scaling_step1(obs_ams_by_window, global_missing_code, max_window_size):
    """
    Step 1 of Parameter Scaling: compute mean, SD, beta, mu, logs, and log(hours).
    Returns:
        obs_mean: {window: mean}
        obs_sd: {window: sd}
        obs_parm_values: {window: {"beta": , "mu": , "log_beta": , "log_mu": , "hours": , "log_hours": }}
    """
    obs_mean = {}
    obs_sd = {}
    obs_parm_values = {}

    for window in range(1, max_window_size + 1):
        data = obs_ams_by_window.get(window, [])
        valid_data = [x for x in data if x != global_missing_code]

        if not valid_data:
            obs_mean[window] = global_missing_code
            obs_sd[window] = global_missing_code
            continue

        # Mean
        mean_val = sum(valid_data) / len(valid_data)
        obs_mean[window] = mean_val

        # Standard Deviation
        if len(valid_data) < 2:
            sd_val = global_missing_code
        else:
            variance = sum((x - mean_val) ** 2 for x in valid_data) / (len(valid_data) - 1)
            sd_val = math.sqrt(variance)

        obs_sd[window] = sd_val

        # Beta, Mu, and Logs
        parm = {}
        if sd_val != global_missing_code and sd_val > 0:
            beta = sd_val * 0.7797
            parm["beta"] = beta
            parm["log_beta"] = math.log(beta)
        else:
            parm["beta"] = parm["log_beta"] = global_missing_code

        if mean_val != global_missing_code and sd_val != global_missing_code:
            mu = mean_val - 0.45 * sd_val
            parm["mu"] = mu
            parm["log_mu"] = math.log(mu) if mu > 0 else global_missing_code
        else:
            parm["mu"] = parm["log_mu"] = global_missing_code

        hours = window * 24
        parm["hours"] = hours
        parm["log_hours"] = math.log(hours)

        obs_parm_values[window] = parm
        
    return obs_mean, obs_sd, obs_parm_values

def calc_slopes_obs_values(obs_parm_values, global_missing_code):
    """Returns 4 slopes: mu_linear, beta_linear, mu_power, beta_power"""
    raw_x, log_x = [], []
    raw_mu, raw_beta = [], []
    log_mu, log_beta = [], []

    for values in obs_parm_values.values():
        h = values.get("hours")
        lh = values.get("log_hours")
        mu = values.get("mu")
        beta = values.get("beta")
        log_mu_val = values.get("log_mu")
        log_beta_val = values.get("log_beta")

        if h is not None and mu not in [None, global_missing_code] and beta not in [None, global_missing_code]:
            raw_x.append(h)
            raw_mu.append(mu)
            raw_beta.append(beta)

        if lh is not None and log_mu_val not in [None, global_missing_code] and log_beta_val not in [None, global_missing_code]:
            log_x.append(lh)
            log_mu.append(log_mu_val)
            log_beta.append(log_beta_val)

    def slope(x, y):
        if len(x) < 2:
            return 0
        mean_x = sum(x) / len(x)
        mean_y = sum(y) / len(y)
        num = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
        den = sum((xi - mean_x) ** 2 for xi in x)
        return num / den

    return {
        "mu_linear": slope(raw_x, raw_mu),
        "beta_linear": slope(raw_x, raw_beta),
        "mu_power": slope(log_x, log_mu),
        "beta_power": slope(log_x, log_beta)
    }


def parameter_power_scaling(
    idf_years_to_model,
    idf_hours_array,
    obs_parm_values,
    mu_slope,
    beta_slope,
    global_missing_code
):
    scaled_table = {}

    if 1 not in obs_parm_values:
        print(f"❌ obs_parm_values keys: {list(obs_parm_values.keys())}")
        raise ValueError("Missing window=1 in obs_parm_values")

    # Find the lowest valid window
    base_window = min(obs_parm_values.keys())
    mu_base = obs_parm_values[base_window].get("mu")
    beta_base = obs_parm_values[base_window].get("beta")

    if mu_base in [None, global_missing_code] or beta_base in [None, global_missing_code]:
        print(f"⚠️ mu_base={mu_base}, beta_base={beta_base}")
        raise ValueError("Invalid mu/beta values for window=1")

    for rp in idf_years_to_model:
        scaled_table[rp] = {} 
        for duration in idf_hours_array:
            try:
                if duration <= 0:
                    scaled_table[rp].append(None)
                    continue

                mu = mu_base * (duration / 24) ** mu_slope
                beta = beta_base * (duration / 24) ** beta_slope

                if rp == 1:
                    logbit = math.log(-math.log(1 - (1 / 1.01)))
                else:
                    logbit = math.log(-math.log(1 - (1 / rp)))

                intensity = (mu - beta * logbit) / duration
                scaled_table[rp][duration] = intensity if intensity >= 0 else None

                     # Assume `beta` is your calculated slope value (float)
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setWindowTitle("β Slope Value")
                msg.setText(f"The β value (slope) used for intensity scaling is:\n\nβ = {beta:.4f}")
                msg.exec_()
            except Exception as e:
                print(f"❌ Failed at RP={rp}, duration={duration}: {e}")
                scaled_table[rp][duration] = None

    print (scaled_table)
    return scaled_table

def parameter_linear_scaling_final(
    file1_used, file2_used,
    IDFYearsToModel, IDFHoursArray,
    ObsParmValues, ObsSlopeValues,
    ModParmValues=None, ModSlopeValues=None
):
    """
    Final stage for linear scaling. Returns two dicts:
    - SDSMScaledTableObs
    - SDSMScaledTableMod
    """
    try:
        SDSMScaledTableObs = {}
        SDSMScaledTableMod = {}

        if file1_used:
            mu_base = ObsParmValues[1]["mu"]
            beta_base = ObsParmValues[1]["beta"]
            mu_slope = ObsSlopeValues[1]  # slope w.r.t. mu
            beta_slope = ObsSlopeValues[0]  # slope w.r.t. beta

            for rp in IDFYearsToModel:
                SDSMScaledTableObs[rp] = {}
                for duration in IDFHoursArray:
                    first_part = mu_base - ((24 - duration) * mu_slope)
                    second_part = beta_base - ((24 - duration) * beta_slope)

                    if rp == 1:
                        log_bit = math.log(-math.log(1 - (1 / 1.01)))
                    else:
                        log_bit = math.log(-math.log(1 - (1 / rp)))

                    intensity = (first_part - second_part * log_bit) / duration
                    SDSMScaledTableObs[rp][duration] = intensity if intensity >= 0 else None

        if file2_used and ModParmValues and ModSlopeValues:
            mu_base = ModParmValues[1]["mu"]
            beta_base = ModParmValues[1]["beta"]
            mu_slope = ModSlopeValues[1]
            beta_slope = ModSlopeValues[0]

            for rp in IDFYearsToModel:
                SDSMScaledTableMod[rp] = []
                for duration in IDFHoursArray:
                    first_part = mu_base - ((24 - duration) * mu_slope)
                    second_part = beta_base - ((24 - duration) * beta_slope)

                    if rp == 1:
                        log_bit = math.log(-math.log(1 - (1 / 1.01)))
                    else:
                        log_bit = math.log(-math.log(1 - (1 / rp)))

                    intensity = (first_part - second_part * log_bit) / duration
                    SDSMScaledTableMod[rp].append(intensity if intensity >= 0 else None)
 
        mini_reset()
        return SDSMScaledTableObs

    except Exception as e:
        handle_error(e)
        mini_reset()
        return {}, {}


def present_results_as_table(hours_array, return_periods, sdsm_scaled_table_obs=None,sdsm_scaled_table_mod=None):
   
    def create_table(data: dict, title: str):
        table = QTableWidget()
        table.setColumnCount(len(return_periods) + 1)
        table.setRowCount(len(hours_array))
        headers = ["Duration (h) ⬇️/ Return Periods(yr)➡️"] + [f"{rp} yr" for rp in return_periods]
        table.setHorizontalHeaderLabels(headers)
        font = QFont()
        font.setBold(True)
        for col in range(table.columnCount()):
            header_item = table.horizontalHeaderItem(col)
            if header_item:
                header_item.setFont(font)
        for row_idx, duration in enumerate(hours_array):
            # Set duration in first column
            table.setItem(row_idx, 0, QTableWidgetItem(f"{duration:.2f}"))
            table.item(row_idx, 0).setTextAlignment(Qt.AlignCenter) 
            for col_idx, rp in enumerate(return_periods, start=1):
                try:
                    val = data[rp][duration]
                    item = QTableWidgetItem(f"{val:.1f}" if val >= 0 else "NA")
                    item.setTextAlignment(Qt.AlignCenter)
                except:
                    item = QTableWidgetItem("NA")
                    item.setTextAlignment(Qt.AlignCenter)
                table.setItem(row_idx, col_idx, item)

        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        
        return table
    def export_current_tab_to_csv():
        current_widget = tabs.currentWidget()
        if isinstance(current_widget, QTableWidget):
            path, _ = QFileDialog.getSaveFileName(window, "Export Table to CSV", "", "CSV Files (*.csv)")
            if path:
                with open(path, 'w', newline='', encoding='utf-8') as file: 
                    writer = csv.writer(file)
                    headers = [current_widget.horizontalHeaderItem(i).text() for i in range(current_widget.columnCount())]
                    writer.writerow(headers)
                    for row in range(current_widget.rowCount()):
                        row_data = []
                        for col in range(current_widget.columnCount()):
                            item = current_widget.item(row, col)
                            row_data.append(item.text() if item else "")
                        writer.writerow(row_data)
    window = QWidget()
    window.setWindowTitle("IDF Intensity Tables")
    layout = QVBoxLayout()
    label = QLabel("📊 Rainfall Intensities (mm/h) for Return Periods and Durations")
    layout.addWidget(label)
 
    tabs = QTabWidget()
    has_data = False

    if sdsm_scaled_table_obs:
        tabs.addTab(create_table(sdsm_scaled_table_obs, "Observed"), "Observed")
        has_data = True
    if sdsm_scaled_table_mod:
        tabs.addTab(create_table(sdsm_scaled_table_mod, "Modelled"), "Modelled")
        has_data = True
    if not has_data:
        layout.addWidget(QLabel("⚠️ No intensity data available to display."))
    else:
        layout.addWidget(tabs)

    # Add export button below the tabs
        export_button = QPushButton("Export Current Table to CSV")
        export_button.clicked.connect(export_current_tab_to_csv)
        layout.addWidget(export_button)

    window.setLayout(layout)
    window.resize(1700, 600)
    window.show()
     
    active_windows.append(window)
    
def present_results_as_graph(hours_array, return_periods, sdsm_scaled_table_obs=None,sdsm_scaled_table_mod=None):
    
    """
    Replicates VBA's log-log plot for IDF data using matplotlib.
    - hours_array: list of durations (e.g., [0.25, 0.5, 1, 2, ..., 360])
    - return_periods: list of return periods (e.g., [1, 2, 5, 10, 20])
    - sdsm_scaled_table_obs/mod: dict[rp][hours] = value
    """
    fig, ax = plt.subplots()
    
    # Define 5 consistent colors (extendable if needed)
    base_colors = ['tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple']
    
    # Skip the first two hours (0.25 and 0.5), starting at index 2
    for i, rp in enumerate(return_periods):
        color = base_colors[i % len(base_colors)]  # Ensure looping if more than 5 RPs

        if sdsm_scaled_table_obs:
            x_obs = [math.log10(h) for h in hours_array[2:] if h > 0]
            y_obs = [math.log10(sdsm_scaled_table_obs[rp][h]) for h in hours_array[2:] if sdsm_scaled_table_obs[rp][h] > 0]
            ax.plot(x_obs, y_obs, label=f'Obs {rp} yr', linewidth=2, color=color, linestyle='-')

        if sdsm_scaled_table_mod:
            x_mod = [math.log10(h) for h in hours_array[2:] if h > 0]
            y_mod = [math.log10(sdsm_scaled_table_mod[rp][h]) for h in hours_array[2:] if sdsm_scaled_table_mod[rp][h] > 0]
            ax.plot(x_mod, y_mod, label=f'Mod {rp} yr', linewidth=2, color=color, linestyle='--')

    ax.set_title("Log-Log IDF Plot")
    ax.set_xlabel("Log Hours")
    ax.set_ylabel("Log Intensity (mm/hr)")
    ax.legend()
    ax.grid(True)
    plt.tight_layout()
    plt.show()

def show_beta_values(beta_obs, beta_mod):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Information)
    msg.setWindowTitle("β Slope Values")

    text = "The β values (slope) used for intensity scaling:\n"
    if beta_obs is not None:
        text += f"\n• Observed β = {beta_obs:.3f}"
    if beta_mod is not None:
        text += f"\n• Modelled β = {beta_mod:.3f}"
    if beta_obs is None and beta_mod is None:
        text += "\nNo β values available."

    msg.setText(text)
    msg.exec_()

# Dummy placeholders for functions you may already have or need to define
def mini_reset():
    print("Resetting temporary variables or UI elements.")


def handle_error(error):
    print(f"Error occurred: {error}")
