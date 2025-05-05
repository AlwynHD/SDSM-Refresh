import math
import configparser
from PyQt5.QtWidgets import QWidget,QMessageBox, QVBoxLayout, QTableWidget, QTableWidgetItem, QLabel, QTextEdit
from datetime import timedelta
from datetime import datetime
from typing import Tuple

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
    ensemble_index=ensemble_index -1
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
        sdsm_scaled_table_obs = None
        sdsm_scaled_table_mod = None
        
        if idf_method == "Intensity":

            sdsm_scaled_table_obs, sdsm_scaled_table_mod = intensity_scaling(
                file1_used, file2_used,
                idf_years_to_model,
                idf_hours_array,
                obs_ams_by_window=obs_ams,
                ret_per_obs_by_window=ret_per_obs_for_intensity,
                mod_ams_by_window=mod_ams_by_window,
                ret_per_mod_by_window=ret_per_mod_by_window
            )
            print(sdsm_scaled_table_obs)
        
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
        if presentation_type == "Tabular":
           result_window = present_results_as_table(
        idf_hours_array,
        idf_years_to_model,
        sdsm_scaled_table_obs,
        sdsm_scaled_table_mod # ← this is optional and will be None if not used
        )
        
        else:
            present_results_as_graph()
        
        print("✅ IDF Analysis Complete.")

    except Exception as e:
        handle_error(e)
        mini_reset()
        return None
        
def load_settings(settings_path='src\lib\settings.ini'):
    config = configparser.ConfigParser()
    config.read("src/lib/settings.ini")  # use full or relative path to your actual file
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
            return False
        
        # Ensure range is at least 10 years
        if (end.year - start.year) < 10:
            print("❌ You must select at least ten years of data for IDF analysis.")
            return False 

        # Check for excessively long date ranges
        if (end.year - start.year) > 150:
            print("❌ Analysis period must not exceed 150 years.")
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

            
            # 2. Extract AMS
def extract_ams_modelled(all_sums_by_ensemble, END_OF_SECTION,missing_code):
    """
    Extract AMS from each ensemble's running sum time series.
    Returns: List of lists (AMS per ensemble)
    """
    return [
        extract_ams_by_year(series, END_OF_SECTION, missing_code)
        for series in all_sums_by_ensemble
    ]

            
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

##1. Intensity Scaling
def intensity_scaling(
    file1_used, file2_used,
    idf_years_to_model,              # e.g. [1, 2, 5, 10, 20]
    idf_hours_array,                 # e.g. [0.25, 0.5, 1, 2, ..., 360]
    obs_ams_by_window,               # {window: [max values]}
    ret_per_obs_by_window,          # {window: [(ret_period, value)]}
    mod_ams_by_window,         # same as obs, optional
    ret_per_mod_by_window      # same as obs, optional
):
    print(idf_years_to_model)
    print(obs_ams_by_window)
              # {window: [(ret_period, value)]}
    print(ret_per_obs_by_window)
    """
    Performs intensity scaling analysis and builds final IDF tables.
    """
    try:
        # ===== OBSERVED SCALING =====
        if file1_used:
            # Step 1: Build ObsScalings table
            obs_scalings = set_obs_scalings(obs_ams_by_window, ret_per_obs_by_window, idf_years_to_model)
        
            print("\n🔍 Checking return period coverage:")
            for window, rp_vals in ret_per_obs_by_window.items():
                rps = [round(x[0]) for x in rp_vals]
                print(f"Window {window}: Return Periods = {rps}")
        
            print("\n🔍 Debugging Intensity Scaling Setup")
            for rp in idf_years_to_model:
                print(f"\n🎯 Return Period: {rp} years")
                print("Window | RP Matched | Type      | Value | Intensity (mm/hr)")
                for window in sorted(obs_scalings[rp].keys()):
                    intensity = obs_scalings[rp][window]
                    rp_list = ret_per_obs_by_window[window]
                    exact_matches = [x for x in rp_list if round(x[0]) == rp]
                    if exact_matches:
                        matched = exact_matches[0]
                        match_type = "Exact"
                    else:
                        matched = min(rp_list, key=lambda x: abs(x[0] - rp))
                        match_type = "Closest"
                    print(f"{window:>6} | {matched[0]:>10.2f} | {match_type:<9} | {matched[1]:>6.2f} | {intensity:>8.2f}")
        
            # Step 2: Fit regression for each return period
            obs_idf_params = {}
            for rp in idf_years_to_model:
                a, b = calc_obs_scalings_linear_regression(obs_scalings[rp])
                print(f"\n📈 Regression for RP={rp}: Intercept a={a:.6f}, Slope b={b:.6f}")
                obs_idf_params[rp] = (a, b)
        
            # Step 3: Build final SDSMScaledTable
            SDSMScaledTableObs = calc_sdsm_scaled_table(idf_years_to_model, idf_hours_array, obs_idf_params)
        else:
            SDSMScaledTableObs = {}

    # ===== MODELLED SCALING =====
        if file2_used and mod_ams_by_window and ret_per_mod_by_window:
           mod_scalings = set_obs_scalings(mod_ams_by_window, ret_per_mod_by_window, idf_years_to_model)
           
           mod_idf_params = {
               rp: calc_obs_scalings_linear_regression(mod_scalings[rp])
               for rp in idf_years_to_model
           }
       
           SDSMScaledTableMod = calc_sdsm_scaled_table(idf_years_to_model, idf_hours_array, mod_idf_params)
        else:
            SDSMScaledTableMod = {}
        
        print("✅ Intensity scaling completed.")
        return SDSMScaledTableObs, SDSMScaledTableMod
    
    except Exception as e:
        handle_error(e)
        mini_reset()
        return {}, {}

def debug_intensity_regression(obs_scalings, rp_target):
    print("\n🔬 Debugging Intensity Scaling Regression")
    print(f"🎯 Return Period: {rp_target} years")
    print("Window | Hours | AMS Intensity | log10(Hours) | log10(Intensity)")

    X = []
    Y = []

    for window, intensity in obs_scalings[rp_target].items():
        hours = window * 24
        if intensity <= 0:
            continue

        x_val = round(math.log10(hours), 14)
        y_val = round(math.log10(intensity), 14)

        X.append(x_val)
        Y.append(y_val)

        print(f"{window:>6} | {hours:>5}h | {intensity:>13.4f} | {x_val:>13.8f} | {y_val:>15.8f}")

    # Do regression again for comparison
    n = len(X)
    sum_x = sum(X)
    sum_y = sum(Y)
    sum_xx = sum(x**2 for x in X)
    sum_xy = sum(x*y for x, y in zip(X, Y))

    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x**2)
    intercept = (sum_y - slope * sum_x) / n

    print(f"\n📈 Recomputed Regression:")
    print(f"  Intercept (a): {intercept:.10f}")
    print(f"  Slope     (b): {slope:.10f}")

    # Show final intensities from the formula
    print("\n📊 Final Intensities (10^a * D^b):")
    for duration in [0.25, 0.5, 1, 2, 3, 6, 24, 48, 120, 240, 360]:
        pred = (10 ** intercept) * (duration ** slope)
        print(f"  {duration:>6.2f}h: {pred:.2f} mm/h")   

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

##2. Parameter-Power-Scaling
def ParameterPowerScaling():
    {



    }
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
    output = "Rainfall Intensities (mm/h) for Return Periods and Durations\n\n"
    
    # === Observed Table ===
    if sdsm_scaled_table_obs:
        output += "📊 Observed\n"
        output += f"{'Duration (Hours)':<15}" + "".join([f"{rp:<8}" for rp in return_periods]) + "\n"
        for duration in hours_array:
            row = f"{duration:<15.2f}"
            for rp in return_periods:
                try:
                    value = sdsm_scaled_table_obs[rp][duration]
                    temp = "NA" if value < 0 else f"{value:.1f}"
                except:
                    temp = "NA"
                row += f"{temp:<8}"
            output += row + "\n"
        output += "\n"

    # === Modelled Table ===
    if sdsm_scaled_table_mod:
        output += "📊 Modelled\n"
        output += f"{'Duration (Hours)':<15}" + "".join([f"{rp:<8}" for rp in return_periods]) + "\n"
        for duration in hours_array:
            row = f"{duration:<15.2f}"
            for rp in return_periods:
                try:
                    value = sdsm_scaled_table_mod[rp][duration]
                    temp = "NA" if value < 0 else f"{value:.1f}"
                except:
                    temp = "NA"
                row += f"{temp:<8}"
            output += row + "\n"
        print(sdsm_scaled_table_mod)
    if not sdsm_scaled_table_obs and not sdsm_scaled_table_mod:
        output += "⚠️ No intensity data available to display.\n"

    # === Show in PyQt Window ===
    window = QWidget()
    window.setWindowTitle("IDF Intensity Table")
    layout = QVBoxLayout()
    label = QLabel("📊 Final Results")
    text_edit = QTextEdit()
    text_edit.setPlainText(output)
    text_edit.setReadOnly(True)
    layout.addWidget(label)
    layout.addWidget(text_edit)
    window.setLayout(layout)
    window.resize(700, 600)
    window.show()

    
    active_windows.append(window)
    

# Dummy placeholders for functions you may already have or need to define
def mini_reset():
    print("Resetting temporary variables or UI elements.")


def handle_error(error):
    print(f"Error occurred: {error}")
