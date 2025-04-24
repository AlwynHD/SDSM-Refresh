import math
from PyQt5.QtWidgets import QMessageBox

def run_idf(
    file1_used, file2_used,
    file1_name, file2_name,
    start_date, end_date,
    presentation_type,   # "Tabular" or "Graphical"
    idf_method,          # "Intensity", "Power", or "Linear"
    running_sum_length,
    ensemble_option,
    ensemble_index
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
    parent=None
    """
    Main function to run the IDF analysis.
    presentation_type: "Tabular" or "Graphical"
    """
    num_ensembles = 1  # Default assumption (if only one column)

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
        # Initial Validation and Setup
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
        
        # Early in run_idf():
        if not is_ensemble_number_valid(ensemble_option, ensemble_index, num_ensembles,parent):
            print("❌ Invalid ensemble member selected. Exiting.")
            return
        
        print("✔ Input files valid. Proceeding...")
        """
        # -------------------------------------
        # Read & Preprocess Observed Data
        # Call read_observed_data
        # -------------------------------------
        if file1_used:
            print("📥 Reading observed data...")
            skip_unwanted_observed_data()
            read_observed_data()

        # -------------------------------------
        # Read & Preprocess Modelled Data
        # -------------------------------------
        if file2_used:
            print("📥 Reading modelled data...")
            skip_unwanted_modelled_data()
            read_modelled_data()

        # -------------------------------------
        # Perform AMS + Running Sum Analysis
        # -------------------------------------
        print("🔄 Calculating running sums and AMS...")
        if file1_used:
            CalcRunningSumObserved()
            CalcAMSObserved()
            SortAMSObserved()
            SetRetPerObs()

        if file2_used:
            CalcRunningSumModelled()
            CalcAMSModelled()
            SortAMSModelled()
            CalcAMSModelledAvg()
            SetRetPerMod()

        # -------------------------------------
        # Check for Sufficient Data
        # -------------------------------------
        if not SufficientData():
            print("❌ Not enough data for IDF analysis.")
            return

        # -------------------------------------
        # Perform Scaling
        # -------------------------------------
        print("📈 Scaling AMS to IDF table...")
        if idf_method == "Intensity":
            IntensityScaling()
        else:
            ParameterScalingStep1()
            if idf_method == "Power":
                ParameterPowerScaling()
            else:
                parameter_linear_scaling_final()

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

def SufficientData(min_years_required=10):
    """

    try:
        if file1_used:
            if len(observed_data) < (min_years_required * 365):
                print("❌ Not enough observed data.")
                return False

        if file2_used:
            if not modelled_data:
                print("❌ Modelled data is empty.")
                return False
            for ensemble in modelled_data:
                if len(ensemble) < (min_years_required * 365):
                    print("❌ Not enough modelled data in one or more ensembles.")
                    return False

        return True
    except Exception as e:
        handle_error(e)
        return False
        """

#perform next stages of IDF analysis for an intensity scaling approach
def IntensityScaling(): {


}
#print out various arrays used in IntensityScaling for testing purposes only - not to be called in live version
def PrintOutArraysTestIntensity():{


}
    
#print out various arrays used in ParameterScaling for testing purposes only - not to be called in live version   
def PrintOutArraysTestParameter():{

}
#'perform first stages of IDF analysis for a parameter (Gumbel) scaling approach - first steps of parameter power and parameter linear scaling
def ParameterScalingStep1():{

}
    
def CalcSlopesObsValues():{

}

def CalcSlopesModValues():{

}
def CalcSDSMScaledTable():{

}

def CalcModScalings():{

}
def CalcObsScalings() :{

}
def SetModScalings():{

}
def SetObsScalings():{

}
def SetRetPerMod():{

}
def SetRetPerObs():{

}
def CalcAMSModelledAvg():{

}
def SortAMSModelled():{

}
def SortAMSObserved():{

}
def CalcAMSModelled():{

}
def CalcAMSObserved():{

}
def CalcRunningSumObserved():{

}
def CalcRunningSumModelled():{

}
def StripMissing():{

}


def read_observed_data():
    """
    global observed_data

    try:
        with open(file1_name, 'r') as f:
            observed_data = []
            for line in f:
                try:
                    value = float(line.strip())
                    observed_data.append(value)
                except ValueError:
                    continue  # Skip non-numeric lines
        print(f"...Read {len(observed_data)} observed data points.")

    except FileNotFoundError:
        print(f"❌ Observed file {file1_name} not found.")
        raise
"""

def read_modelled_data():
    """
    global modelled_data, num_ensembles

    try:
        with open(file2_name, 'r') as f:
            modelled_data = []
            for line in f:
                parts = line.strip().split(',')
                if len(parts) < 2:
                    continue
                try:
                    row = [float(x) for x in parts]
                    modelled_data.append(row)
                except ValueError:
                    continue

        # Transpose rows to columns per ensemble
        if modelled_data:
            num_ensembles = len(modelled_data[0])
            modelled_data = [[row[i] for row in modelled_data] for i in range(num_ensembles)]
            print(f"...Loaded {num_ensembles} model ensembles.")

    except FileNotFoundError:
        print(f"❌ Modelled file {file2_name} not found.")
        raise
"""

# Dummy placeholders for functions you may already have or need to define
def mini_reset():
    print("Resetting temporary variables or UI elements.")


def handle_error(error):
    print(f"Error occurred: {error}")
