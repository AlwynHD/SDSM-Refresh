import math
import configparser
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from datetime import timedelta
from datetime import datetime
from typing import Tuple
from typing import List


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
    idf_years_to_model = [1, 2, 5, 10, 20]     # Length = 5
    
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
                values = first_line.split(',')
    
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
        # Early in run_idf():
        if not is_ensemble_number_valid(ensemble_option, ensemble_index, num_ensembles,parent):
            print("❌ Invalid ensemble member selected. Exiting.")
            return
        
        print("✔ Input files valid. Proceeding...")
    
        # -------------------------------------
        # Step 2: Read & Preprocess Observed Data
        # Call read_observed_data
        # -------------------------------------
        
        if file1_used:
            print("📥 Reading observed data...")
            config = load_settings("settings.ini")
            global_start_date, _ = get_global_dates(config)
            print(global_start_date)
            threshold = float(config.get("Settings", "thresh", fallback=5.0))  # default fallback
            missing_code = float(config.get("Settings", "globalmissingcode", fallback=-999))
            filter_func = build_data_period_filter(data_period_choice)
            yearindicator = int(config.get("Settings", "yearindicator", fallback=366))
      
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
        
        # -------------------------------------
        # Step 3: Read & Preprocess Modelled Data
        # -------------------------------------
        if file2_used:
            print("📥 Reading modelled data...")
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

        # -------------------------------------
        # Step 4: Perform AMS + Running Sum Analysis
        # -------------------------------------
        
        print("🔄 Calculating running sums and AMS...")
        
        # === For OBSERVED ===
        obs_ams_by_window = {}
        ret_per_obs_by_window = {}
        # === For MODELLED ===
        mod_ams_by_window = {}
        ret_per_mod_by_window = {}

        if file1_used:
            # Step 1: Compute running sums for all window sizes
            obs_running_sums = calc_all_running_sums_yearwise(observed_data, max_window_size, END_OF_SECTION)
            
            for window, series in obs_running_sums.items():
            # Step 2: Extract AMS for the selected running sum window
                ams_obs = extract_ams_by_year(
                data=series,
                END_OF_SECTION=END_OF_SECTION,
                missing_code= missing_code
                )
                obs_ams_by_window[window] = ams_obs
            # Step 3: Compute return periods
                ret_per_obs_by_window[window] = compute_return_periods(ams_obs)
            
        if file2_used:
            # 1. Running sums
            mod_running_sums = calc_running_sums_modelled(modelled_data, running_sum_length, END_OF_SECTION)
            
            for window, ensemble_series in mod_running_sums.items():
                mod_ams_by_window[window]=[]
                ret_per_mod_by_window[window]=[]

                for series in ensemble_series:
            
                    # 2. Extract AMS
                    ams = extract_ams_modelled(mod_running_sums, END_OF_SECTION)
            
                    # 3. Compute RP per ensemble
                    mod_ams_by_window[window].append(ams)
                    ret_per_mod_by_window[window].append(compute_return_periods_modelled(ams))
                    # 4. Optional mean AMS
                    mean_ams = compute_ensemble_mean_ams(ams)
                    mean_rp = compute_return_periods(mean_ams)
        
        # -------------------------------------
        # Step 5: Check for Sufficient Data
        # -------------------------------------
        
        if not has_sufficient_data(observed_data, modelled_data, min_points=100):
            print("❌ Not enough data for IDF analysis.")
            return
        
        # -------------------------------------
        # Step 6: Perform Scaling
        # -------------------------------------
        print("📈 Scaling AMS to IDF table...")
        if idf_method == "Intensity":
            intensity_scaling(
                 file1_used, file2_used,
                 idf_years_to_model,              # e.g. [1, 2, 5, 10, 20]
                 idf_hours_array,                 # e.g. [0.25, 0.5, 1, 2, ..., 360]
                 obs_ams_by_window,               # {window: [max values]}
                 ret_per_obs_by_window,          # {window: [(ret_period, value)]}
                 mod_ams_by_window,         # same as obs, optional
                 ret_per_mod_by_window      # same as obs, optional
             )
        else:
            ParameterScalingStep1()
            if idf_method == "Power":
                ParameterPowerScaling()
            else:
                parameter_linear_scaling_final()
        """
        # -------------------------------------
        # Output Results
        # -------------------------------------
        print("📤 Generating final output...")
        if presentation_type == "Tabular":
            present_results_as_table()
        else:
            present_results_as_graph()

        print("✅ IDF Analysis Complete.")
    """
    except Exception as e:
        handle_error(e)

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

                # Handle section change (new year)
                if current_date.year > last_year and some_data_valid:
                    observed_data.append(end_of_section_marker)
                    total_obs_years += 1

                # Validate data
                if value == missing_code or (use_threshold and value < threshold):
                    pass  # skip
                else:
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
        print(observed_data)
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
    filter_func,
    parent,
    END_OF_SECTION
):
    """
    Reads modelled data from file, supports multi-ensemble selection and filtering.

    Returns:
    - modelled_data: list of lists (each sublist is a time series for one ensemble)
    - total_mod_years: integer count of complete years
    """

    current_date = start_date
    total_days = (end_date - start_date).days + 1
    data_lines = []
    total_mod_years = 1
    end_of_section_marker = END_OF_SECTION

    try:
        with open(file_path, 'r') as f:
            for _ in range(total_days):
                line = f.readline()
                if not line:
                    break
                try:
                    values = [float(val.strip()) for val in line.strip().split(',')]
                    data_lines.append(values)
                except ValueError:
                    continue  # skip non-numeric

                current_date += timedelta(days=1)

        if not data_lines:
            return [], 0

        num_ensembles = len(data_lines[0])
        # Transpose: convert rows per day → list per ensemble
        full_data = [[row[i] for row in data_lines] for i in range(num_ensembles)]

        # Apply threshold/missing filtering
        filtered_data = []
        for ensemble_id, ensemble_series in enumerate(full_data):
            series = []
            some_data_valid = False
            last_year = start_date.year
            current_date = start_date

            for i, value in enumerate(ensemble_series):
                if filter_func and not filter_func(current_date):
                    current_date += timedelta(days=1)
                    continue

                if value == missing_code or (use_threshold and value < threshold):
                    pass
                else:
                    series.append(value)
                    some_data_valid = True

                # Detect year change
                if current_date.year > last_year and some_data_valid:
                    series.append(end_of_section_marker)
                    total_mod_years += 1
                last_year = current_date.year
                current_date += timedelta(days=1)

            series.append(end_of_section_marker)
            filtered_data.append(series)

        # If a specific ensemble is selected
        if ensemble_index is not None:
            if ensemble_index < len(filtered_data):
                return [filtered_data[ensemble_index]], total_mod_years
            else:
                print(f"⚠️ Ensemble {ensemble_index} out of range. Returning first ensemble.")
                return [filtered_data[0]], total_mod_years

        return filtered_data, total_mod_years

    except Exception as e:
        print(f"❌ Error reading modelled data: {e}")
        return [], 0

def calc_all_running_sums_yearwise(observed_data, max_window_size, END_OF_SECTION):
    """
    Calculates N-day running sums for each year block using yearindicator.
    Returns: {window_size: list of running sums}
    """
    all_sums = {1: observed_data[:]}  # 1-day sum is the data itself

    for window in range(2, max_window_size + 1):
        window_sums = []
        for year_start in range(0, len(observed_data), END_OF_SECTION):
            year_data = observed_data[year_start:year_start + END_OF_SECTION]
            for i in range(len(year_data) - window + 1):
                window_sums.append(sum(year_data[i:i+window]))
        all_sums[window] = window_sums

    return all_sums


def extract_ams_by_year(data, END_OF_SECTION, missing_code):
    ams = []
    for i in range(0, len(data), END_OF_SECTION):
        year_block = data[i:i+END_OF_SECTION]
        valid = [v for v in year_block if v != missing_code and isinstance(v, (int, float))]
        if valid:
            ams.append(max(valid))
    return ams

def sort_ams(ams: List[float]) -> List[float]:
    return sorted(ams, reverse=True)

def compute_return_periods(ams: List[float]) -> List[Tuple[float, float]]:
    """
    Computes return periods from the sorted AMS list using Weibull formula:
    Return Period = (n + 1) / rank
    """
    n = len(ams)
    sorted_ams = sort_ams(ams)
    return [( (n + 1) / (i + 1), val) for i, val in enumerate(sorted_ams)]

def calc_running_sums_modelled(data_by_ensemble, window_size, END_OF_SECTION):
    """
    Compute running sum time series for each ensemble member.
    Returns: List of lists (1 list per ensemble)
    """
    all_sums = []

    for series in data_by_ensemble:
        windowed = []
        for i in range(len(series) - window_size + 1):
            block = series[i:i + window_size]
            if all(isinstance(x, (int, float)) for x in block):
                windowed.append(sum(block))
        all_sums.append(windowed)

    return all_sums

            
            # 2. Extract AMS
def extract_ams_modelled(all_sums_by_ensemble, END_OF_SECTION):
    """
    Extract AMS from each ensemble's running sum time series.
    Returns: List of lists (AMS per ensemble)
    """
    return [
        extract_ams_by_year(series, END_OF_SECTION)
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
    mod_ams_by_window=None,         # same as obs, optional
    ret_per_mod_by_window=None      # same as obs, optional
):
    """
    Performs intensity scaling analysis and builds final IDF tables.
    """
    try:
        # ===== OBSERVED SCALING =====
        if file1_used:
            # Step 1: Build ObsScalings table
            obs_scalings = set_obs_scalings(obs_ams_by_window, ret_per_obs_by_window, idf_years_to_model)

            # Step 2: Fit regression for each return period
            obs_idf_params = {
                rp: calc_obs_scalings_linear_regression(obs_scalings[rp])
                for rp in idf_years_to_model
            }

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
        mini_reset()

        return SDSMScaledTableObs, SDSMScaledTableMod

    except Exception as e:
        handle_error(e)
        mini_reset()
        return {}, {}
    
def set_obs_scalings(obs_ams_by_window, ret_periods_by_window, idf_years):
    """
    Constructs the ObsScalings table from AMS and return period data.
    
    obs_ams_by_window: dict {window: [AMS values]}
    ret_periods_by_window: dict {window: [(ret_period, value)]}
    idf_years: list of years to model, e.g., [1, 2, 5, 10, 20]
    
    Returns: obs_scalings[year][window]
    """
    obs_scalings = {}

    for rp in idf_years:
        obs_scalings[rp] = {}

        for window, rp_data in ret_periods_by_window.items():
            # Find value with closest return period
            closest_val = min(rp_data, key=lambda x: abs(x[0] - rp))
            value = closest_val[1]
            intensity = value / (window * 24)
            obs_scalings[rp][window] = intensity

    return obs_scalings

def calc_obs_scalings_linear_regression(obs_scalings_for_rp: dict) -> Tuple[float, float]:
    """
    Performs log-log regression for a specific return period across durations.

    obs_scalings_for_rp: dict {window: intensity}
    
    Returns: intercept, slope
    """
    X = []
    Y = []

    for window, intensity in obs_scalings_for_rp.items():
        hours = window * 24
        if intensity <= 0:
            continue  # skip invalid values

        X.append(math.log10(hours))
        Y.append(math.log10(intensity))

    # Linear regression: Y = a + bX
    n = len(X)
    if n == 0:
        return 0, 0  # fallback for empty set

    sum_x = sum(X)
    sum_y = sum(Y)
    sum_xx = sum(x**2 for x in X)
    sum_xy = sum(x*y for x, y in zip(X, Y))

    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x**2)
    intercept = (sum_y - slope * sum_x) / n

    return intercept, slope

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

    return table

##2. Parameter-Power-Scaling
def ParameterPowerScaling():
    {



    }
##3. Parameter-linear-scaling 
def parameter_linear_scaling_final(
    File1Used, File2Used,
    IDFnoOfYearsToModel, IDFSizeOfHoursArray,
    ObsParmValues, ObsSlopeValues, ModParmValues, ModSlopeValues,
    IDFYearsToModel, IDFHoursArray
):

    """
    try:
        # Create tables to store results
        SDSMScaledTableObs = np.zeros((IDFnoOfYearsToModel, IDFSizeOfHoursArray))
        SDSMScaledTableMod = np.zeros((IDFnoOfYearsToModel, IDFSizeOfHoursArray))

        if File1Used:
            for i in range(IDFnoOfYearsToModel):  # i = 0 to n-1
                for j in range(IDFSizeOfHoursArray):  # j = 0 to n-1
                    firstPart = ObsParmValues[0][1] - ((24 - IDFHoursArray[j]) * ObsSlopeValues[1])
                    secondPart = ObsParmValues[0][0] - ((24 - IDFHoursArray[j]) * ObsSlopeValues[0])

                    if i == 0:
                        log_bit = math.log(-math.log(1 - (1 / 1.01)))
                    else:
                        log_bit = math.log(-math.log(1 - (1 / IDFYearsToModel[i])))

                    value = firstPart - (secondPart * log_bit)
                    SDSMScaledTableObs[i][j] = value / IDFHoursArray[j]

        if File2Used:
            for i in range(IDFnoOfYearsToModel):
                for j in range(IDFSizeOfHoursArray):
                    firstPart = ModParmValues[0][1] - ((24 - IDFHoursArray[j]) * ModSlopeValues[1])
                    secondPart = ModParmValues[0][0] - ((24 - IDFHoursArray[j]) * ModSlopeValues[0])

                    if i == 0:
                        log_bit = math.log(-math.log(1 - (1 / 1.01)))
                    else:
                        log_bit = math.log(-math.log(1 - (1 / IDFYearsToModel[i])))

                    value = firstPart - (secondPart * log_bit)
                    SDSMScaledTableMod[i][j] = value / IDFHoursArray[j]

        # Reset function if needed
        mini_reset()

        return SDSMScaledTableObs, SDSMScaledTableMod

    except Exception as e:
        handle_error(e)
        mini_reset()
        return None, None
    
   ## Check if there's enough AMS data to compute IDF (typically ≥10 years).
   ## For now, check if we have at least `min_years_required` values.
""" 

#print out various arrays used in IntensityScaling for testing purposes only - not to be called in live version
def PrintOutArraysTestIntensity():{


}
    
#print out various arrays used in ParameterScaling for testing purposes only - not to be called in live version   
def PrintOutArraysTestParameter():{

}
#'perform first stages of IDF analysis for a parameter (Gumbel) scaling approach - first steps of parameter power and parameter linear scaling
def ParameterScalingStep1():{

}
    
def StripMissing():{

}

# Dummy placeholders for functions you may already have or need to define
def mini_reset():
    print("Resetting temporary variables or UI elements.")


def handle_error(error):
    print(f"Error occurred: {error}")
