import os
import math
import random
import datetime
import calendar
import numpy as np
from scipy.stats import norm as scipy_norm # Use scipy for normal distribution PDF

from PyQt5.QtWidgets import (QVBoxLayout, QWidget, QHBoxLayout, QPushButton,
                             QFrame, QLabel, QLineEdit, QFileDialog, QGroupBox,
                             QGridLayout, QListWidget, QMessageBox, QProgressDialog, QApplication) # Added QProgressDialog
from PyQt5.QtCore import Qt

# --- Define Constants (Replace with actual values from SDSM settings) ---
GLOBAL_MISSING_CODE = -99.0
THRESH = 0.0  # Example threshold, often for rainfall
BIAS_CORRECTION = 1.0 # Example Bias Correction factor
PREC_N = 12 # Example value for number of Rnd calls for normal approximation
ALLOW_NEG = False # Example: Disallow negative predictions for certain variables
CONDITIONAL_SELECTION = 1 # Example: Rob's approach (<= Rnd)
CONDITIONAL_THRESH = 0.5 # Example: Threshold for alternative wet/dry day
RANDOM_SEED_FIXED = True # Example: Use a fixed seed (like VB6 Rnd -1; Randomize 1)
YEAR_INDICATOR = 365 # Example: Common year length (needs to be read/set)
# Define LeapValue if needed for specific 366-day calendar logic (less common with datetime)
# LEAP_VALUE = 1

# --- Helper Functions ---

def normal_pdf(x):
    """Calculates the Probability Density Function (PDF) of the standard normal distribution."""
    return scipy_norm.pdf(x) # More accurate and standard than manual calculation

def get_season(month):
    """Determines the season (1-4) based on the month (1-12) - Northern Hemisphere example."""
    if month in [12, 1, 2]:
        return 1 # Winter
    elif month in [3, 4, 5]:
        return 2 # Spring
    elif month in [6, 7, 8]:
        return 3 # Summer
    elif month in [9, 10, 11]:
        return 4 # Autumn
    else:
        raise ValueError("Invalid month")

def parse_fixed_width(line, width=14):
    """Parses a line with fixed-width floating-point numbers."""
    values = []
    for i in range(0, len(line), width):
        segment = line[i:i+width].strip()
        if segment:
            try:
                values.append(float(segment))
            except ValueError:
                # Handle cases where a segment might be empty or non-numeric if needed
                values.append(GLOBAL_MISSING_CODE) # Or some other indicator
        else:
            # Handle trailing empty segments if necessary
            pass
    return values

def shell_sort(arr):
    """Performs Shell sort on a list (in-place)."""
    n = len(arr)
    gap = n // 2
    while gap > 0:
        for i in range(gap, n):
            temp = arr[i]
            j = i
            while j >= gap and arr[j - gap] > temp:
                arr[j] = arr[j - gap]
                j -= gap
            arr[j] = temp
        gap //= 2
    return arr # Although it sorts in-place, returning is convenient

# --- Main Widget Class ---

class ContentWidget(QWidget):
    """
    A polished and modernized UI for the Weather Generator with an improved structure and user experience.
    """
    def __init__(self):
        super().__init__()
        self.par_file_path = ""
        self.predictor_dir = ""
        self.out_file_path = "" # Store the selected output file path

        # --- Variables to store parsed PAR data ---
        self.n_predictors = 0
        self.season_code = 0
        self.year_length_par = 0 # Year length from PAR file
        self.start_date_par = None
        self.n_days_r_par = 0
        self.cal_fs_date_par = None # Calibration FSDate from PAR
        self.n_days_cal_par = 0 # NDays used during calibration
        self.rain_yes = False
        self.local_model_trans = 0
        self.auto_regression = False
        self.ptand_filename = ""
        self.predictor_filenames = [] # List of predictor filenames from PAR
        self.uncon_parms = None # Use numpy array [month, param_index]
        self.con_parms = None   # Use numpy array [month, param_index]
        self.lamda_array = None # Use numpy array [month, 0=lambda, 1=rightshift]
        self.beta_trend = None  # Use numpy array [season/month, param_index]
        self.de_trend = False
        self.de_trend_type = 0
        self.ptand_file_root = "" # Predictand file root from PAR
        # --- Variables for Inverse Normal Transform ---
        self.rank_data = []
        self.inv_norm_first_value = 0
        self.inv_norm_n_split = 0
        self.inv_norm_limit = 0.0
        self.inv_norm_total_area = 0.0
        # --- Other state ---
        self._cancel_synthesis = False # Flag for cancellation

        # --- UI Setup --- (Your existing UI setup code)
        # Main layout
        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(30, 30, 30, 30)
        mainLayout.setSpacing(20)
        self.setLayout(mainLayout)

        # --- File Selection Section ---
        fileSelectionGroup = QGroupBox("File Selection")
        fileSelectionLayout = QGridLayout()

        self.parFileButton = QPushButton("📂 Select Parameter File")
        self.parFileButton.clicked.connect(self.selectPARFile)
        self.par_file_text = QLabel("Not selected")

        self.outFileButton = QPushButton("💾 Save To .OUT File")
        self.outFileButton.clicked.connect(self.selectOutputFile)
        self.outFileText = QLabel("Not selected")
        self.simLabel = QLabel("(*.SIM also created)")

        fileSelectionLayout.addWidget(self.parFileButton, 0, 0)
        fileSelectionLayout.addWidget(self.par_file_text, 0, 1)
        fileSelectionLayout.addWidget(self.outFileButton, 1, 0)
        fileSelectionLayout.addWidget(self.outFileText, 1, 1)
        fileSelectionLayout.addWidget(self.simLabel, 2, 1)

        fileSelectionGroup.setLayout(fileSelectionLayout)
        mainLayout.addWidget(fileSelectionGroup)

        # --- Predictor Directory Section ---
        predictorDirGroup = QGroupBox("Select Predictor Directory")
        predictorDirLayout = QGridLayout()

        self.dirButton = QPushButton("📁 Select Directory")
        self.dirButton.clicked.connect(self.selectPredictorDirectory)
        self.dirText = QLabel("Not selected")

        predictorDirLayout.addWidget(self.dirButton, 0, 0)
        predictorDirLayout.addWidget(self.dirText, 0, 1)

        predictorDirGroup.setLayout(predictorDirLayout)
        mainLayout.addWidget(predictorDirGroup)

        # --- Data Section (UPDATED to match image) ---
        dataGroup = QGroupBox("Data")
        dataLayout = QGridLayout()

        # View Details button at the top
        self.viewDetailsButton = QPushButton("View Details")
        self.viewDetailsButton.clicked.connect(self.viewPredictors) # Changed from loadPARData to viewPredictors
        dataLayout.addWidget(self.viewDetailsButton, 0, 0, 1, 2, Qt.AlignCenter)

        # Predictor list - keeping original appearance
        self.predictorList = QListWidget()
        # Set a good default height but don't change styling
        self.predictorList.setMinimumHeight(150)
        dataLayout.addWidget(self.predictorList, 1, 0, 1, 2)

        # Predictor information with labels on left, values on right
        dataLayout.addWidget(QLabel("No. of predictors:"), 2, 0, Qt.AlignLeft)
        self.no_of_pred_text = QLabel("0")
        dataLayout.addWidget(self.no_of_pred_text, 2, 1, Qt.AlignLeft)

        dataLayout.addWidget(QLabel("Autoregression:"), 3, 0, Qt.AlignLeft)
        self.auto_regress_label = QLabel("Unknown")
        dataLayout.addWidget(self.auto_regress_label, 3, 1, Qt.AlignLeft)

        dataLayout.addWidget(QLabel("Process:"), 4, 0, Qt.AlignLeft)
        self.process_label = QLabel("Unknown")
        dataLayout.addWidget(self.process_label, 4, 1, Qt.AlignLeft)

        # Add a separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        dataLayout.addWidget(separator, 5, 0, 1, 2)

        # Record and synthesis information
        dataLayout.addWidget(QLabel("Record Start:"), 6, 0, Qt.AlignLeft)
        self.r_start_text = QLabel("unknown")
        dataLayout.addWidget(self.r_start_text, 6, 1, Qt.AlignLeft)

        dataLayout.addWidget(QLabel("Record Length:"), 7, 0, Qt.AlignLeft)
        self.r_length_text = QLabel("unknown")
        dataLayout.addWidget(self.r_length_text, 7, 1, Qt.AlignLeft)

        dataLayout.addWidget(QLabel("Synthesis Start:"), 8, 0, Qt.AlignLeft)
        self.fStartText = QLineEdit("01/01/1948") # Should ideally use QDateEdit
        dataLayout.addWidget(self.fStartText, 8, 1, Qt.AlignLeft)

        dataLayout.addWidget(QLabel("Synthesis Length:"), 9, 0, Qt.AlignLeft)
        self.fLengthText = QLineEdit("365")
        dataLayout.addWidget(self.fLengthText, 9, 1, Qt.AlignLeft)

        dataGroup.setLayout(dataLayout)
        mainLayout.addWidget(dataGroup)

        # --- Ensemble Size Section ---
        ensembleGroup = QGroupBox("Ensemble Size")
        ensembleLayout = QVBoxLayout()

        self.eSize = QLineEdit("20")
        self.eSize.setPlaceholderText("1-100")

        ensembleLayout.addWidget(self.eSize)

        ensembleGroup.setLayout(ensembleLayout)
        mainLayout.addWidget(ensembleGroup)

        # --- Buttons ---
        buttonLayout = QHBoxLayout()

        self.synthesizeButton = QPushButton("🚀 Synthesize Data")
        self.synthesizeButton.clicked.connect(self.synthesizeData)
        self.synthesizeButton.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")

        self.resetButton = QPushButton("🔄 Reset")
        self.resetButton.clicked.connect(self.reset_all)
        self.resetButton.setStyleSheet("background-color: #F44336; color: white; font-weight: bold;")

        buttonLayout.addWidget(self.synthesizeButton)
        buttonLayout.addWidget(self.resetButton)
        mainLayout.addLayout(buttonLayout)
        # --- End UI Setup ---

    def selectPredictorDirectory(self):
        """Opens a directory dialog to select the predictor directory."""
        directory = QFileDialog.getExistingDirectory(self, "Select Predictor Directory", self.predictor_dir or os.path.expanduser("~"))
        if directory:
            self.predictor_dir = directory
            self.dirText.setText(directory)
            # Optionally, you could re-scan the directory or re-validate predictors here
            # self.loadPredictorData(directory) # This function was a bit ambiguous, viewPredictors is better

    # Removed loadPredictorData as it's superseded by loadPARFile and viewPredictors

    def loadPARFile(self, file_path):
        """Loads and parses PAR file data into instance variables."""
        self.par_file_path = file_path
        self.par_file_text.setText(f"{os.path.basename(file_path)}")
        self.predictorList.clear()
        self.predictor_filenames = [] # Clear previous predictor list

        try:
            with open(file_path, 'r') as par_file:
                # --- Read Header ---
                line = par_file.readline().strip()
                n_pred = int(line)
                self.de_trend = False
                if n_pred < 0:
                    self.de_trend = True
                    self.n_predictors = abs(n_pred)
                else:
                     self.n_predictors = n_pred
                self.no_of_pred_text.setText(str(self.n_predictors))

                self.season_code = int(par_file.readline().strip()) # 1=Annual, 4=Seasonal, 12=Monthly
                self.year_length_par = int(par_file.readline().strip()) # 360, 365, 366 - Important for date logic if not using standard calendar
                record_start_str = par_file.readline().strip()
                self.start_date_par = datetime.datetime.strptime(record_start_str, '%d/%m/%Y').date() # Assuming dd/mm/yyyy
                self.r_start_text.setText(record_start_str)
                self.n_days_r_par = int(par_file.readline().strip())
                self.r_length_text.setText(str(self.n_days_r_par))
                cal_fs_date_str = par_file.readline().strip()
                self.cal_fs_date_par = datetime.datetime.strptime(cal_fs_date_str, '%d/%m/%Y').date() # Assuming dd/mm/yyyy
                # Set Synthesis Start/Length defaults from PAR file initially
                self.fStartText.setText(cal_fs_date_str)
                self.n_days_cal_par = int(par_file.readline().strip())
                self.fLengthText.setText(str(self.n_days_cal_par))
                self.rain_yes = par_file.readline().strip().lower() == "true"
                self.process_label.setText("Conditional" if self.rain_yes else "Unconditional")
                self.local_model_trans = int(par_file.readline().strip()) # 1=none, 2=4th, 3=ln, 4=InvNorm, 5=BoxCox
                _ = int(par_file.readline().strip()) # Ensemble size from PAR - unused, we use UI input

                # --- Handle SDSM 3.1 vs 4.2 difference ---
                line = par_file.readline().strip()
                if line.lower() == "true" or line.lower() == "false": # SDSM 4.2+ format
                    self.auto_regression = line.lower() == "true"
                    self.auto_regress_label.setText(str(self.auto_regression))
                    self.ptand_filename = par_file.readline().strip()
                else: # SDSM 3.1 format
                    self.auto_regression = False
                    self.auto_regress_label.setText("False")
                    self.ptand_filename = line

                # --- Read Predictor Filenames ---
                self.predictorList.addItem(self.ptand_filename) # Predictand is listed first
                self.predictor_filenames.append(self.ptand_filename)
                for _ in range(self.n_predictors):
                    pred_fname = par_file.readline().strip()
                    self.predictorList.addItem(pred_fname)
                    self.predictor_filenames.append(pred_fname)

                # --- Read Model Parameters (Unconditional) ---
                n_params_uncon = self.n_predictors + 1 + 1 # Intercept + N predictors + SE
                if self.auto_regression:
                     n_params_uncon += 1 # Add AR coeff

                self.uncon_parms = np.full((12, n_params_uncon), np.nan) # 12 months, N params
                if self.local_model_trans == 5: # Box-Cox needs lambda and rightshift
                    self.lamda_array = np.full((12, 2), np.nan)

                for i in range(12): # 12 months
                    line = par_file.readline() # Read the full line
                    params = parse_fixed_width(line, 14)
                    # Fill parameters (b0, b1..bn, SE, [AR coeff], [lambda, rightshift])
                    self.uncon_parms[i, :len(params[:n_params_uncon])] = params[:n_params_uncon]
                    if self.local_model_trans == 5:
                        if len(params) >= n_params_uncon + 2:
                            self.lamda_array[i, 0] = params[n_params_uncon]     # Lambda
                            self.lamda_array[i, 1] = params[n_params_uncon + 1] # Rightshift
                        else:
                             QMessageBox.warning(self, "PAR Parse Warning", f"Month {i+1}: Not enough Box-Cox parameters found in PAR file.")


                # --- Read Model Parameters (Conditional, if applicable) ---
                if self.rain_yes:
                    n_params_con = self.n_predictors + 1 + 1 # Intercept + VarianceInflation + N Predictors + SE
                    self.con_parms = np.full((12, n_params_con), np.nan)
                    for i in range(12):
                        line = par_file.readline()
                        params = parse_fixed_width(line, 14)
                        if len(params) >= n_params_con:
                             self.con_parms[i, :] = params[:n_params_con] # b0, varinf, b1..bn, SE
                        else:
                            QMessageBox.warning(self, "PAR Parse Warning", f"Month {i+1}: Not enough conditional parameters found in PAR file.")


                # --- Read Predictand File Root (for Inv Normal) ---
                self.ptand_file_root = par_file.readline().strip()


                # --- Read Detrend Parameters (if applicable) ---
                if self.de_trend:
                    self.de_trend_type = int(par_file.readline().strip()) # 1=linear, 2=power
                    n_trend_params = 3 if self.de_trend_type == 2 else 2
                    # Use season_code to determine size (1, 4, or 12)
                    trend_rows = 1 if self.season_code == 1 else (4 if self.season_code == 4 else 12)
                    self.beta_trend = np.full((trend_rows, n_trend_params), np.nan)
                    for i in range(trend_rows):
                         # Read params based on de_trend_type
                         p1 = float(par_file.readline().strip())
                         p2 = float(par_file.readline().strip())
                         self.beta_trend[i, 0] = p1
                         self.beta_trend[i, 1] = p2
                         if self.de_trend_type == 2:
                            p3 = float(par_file.readline().strip()) # Minimum for power
                            self.beta_trend[i, 2] = p3


            QMessageBox.information(self, "PAR File Loaded",
                                f"Successfully loaded parameter file '{os.path.basename(file_path)}'.")

            # Set predictor directory to PAR file directory if not already set by user
            par_dir = os.path.dirname(file_path)
            if not self.predictor_dir:
                self.predictor_dir = par_dir
                self.dirText.setText(par_dir)

        except FileNotFoundError:
            QMessageBox.critical(self, "Error Loading PAR File", f"File not found: {file_path}")
            self.reset_all()
        except Exception as e:
            QMessageBox.critical(self, "Error Loading PAR File", f"Failed to parse the parameter file:\n{str(e)}")
            self.reset_all() # Reset UI if parsing fails

    def selectPARFile(self):
        """Opens a file dialog to select a PAR file."""
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Parameter File", self.predictor_dir or "", "PAR Files (*.par *.PAR);;All Files (*.*)")
        if file_name:
            self.loadPARFile(file_name)

    def selectOutputFile(self):
        """Opens a file dialog to select an output file."""
        # Suggest a default name based on PAR file?
        default_name = ""
        if self.par_file_path:
            base = os.path.splitext(os.path.basename(self.par_file_path))[0]
            default_name = os.path.join(self.predictor_dir or "", f"{base}.OUT")

        file_name, _ = QFileDialog.getSaveFileName(self, "Save To .OUT File", default_name, "OUT Files (*.OUT);;All Files (*.*)")
        if file_name:
            self.out_file_path = file_name # Store the full path
            self.outFileText.setText(os.path.basename(file_name)) # Display only filename

    def viewPredictors(self):
        """Checks existence of predictor files listed in the PAR file."""
        if not self.par_file_path:
            QMessageBox.warning(self, "No PAR file selected", "Please load a parameter file first using 'Select Parameter File'.")
            return
        if not self.predictor_dir:
             QMessageBox.warning(self, "No Predictor Directory", "Please select the directory containing the predictor files.")
             return

        if not self.predictor_filenames:
             QMessageBox.information(self, "No Predictors", "No predictor files listed in the loaded PAR file.")
             return

        missing_files = []
        found_files = []
        self.predictorList.clear() # Clear and re-populate with status

        # First item is predictand, rest are predictors
        for i, filename in enumerate(self.predictor_filenames):
            full_path = os.path.join(self.predictor_dir, filename)
            if not os.path.exists(full_path):
                missing_files.append(filename)
                self.predictorList.addItem(f"⚠️ {filename} (Missing)")
            else:
                found_files.append(filename)
                self.predictorList.addItem(f"{filename}") # No warning needed

        if missing_files:
            missing_list = "\n- ".join(missing_files)
            QMessageBox.warning(self, "Missing Files",
                            f"The following files were not found in '{self.predictor_dir}':\n- {missing_list}\n\nPlease ensure all files are present.")
        else:
            QMessageBox.information(self, "Files Verified",
                                f"All {len(found_files)} required files were found in the selected directory.")

    def _prepare_inverse_normal(self):
        """Reads predictand data, sorts it, and calculates parameters for Inv Normal transform."""
        if not self.ptand_file_root:
             raise ValueError("Predictand file root not specified in PAR file (required for Inverse Normal).")

        # --- Read predictand data used for calibration ---
        ptand_path = self.ptand_file_root # Assuming this is the full path now
        if not os.path.exists(ptand_path):
             # If it's just a root, combine with predictor dir
             ptand_path_alt = os.path.join(self.predictor_dir, os.path.basename(self.ptand_file_root))
             if os.path.exists(ptand_path_alt):
                 ptand_path = ptand_path_alt
             else:
                 raise FileNotFoundError(f"Predictand file for Inverse Normal not found: {self.ptand_file_root} or {ptand_path_alt}")

        self.rank_data = []
        try:
            with open(ptand_path, 'r') as f_ptand:
                # Skip data before the calibration start date (ReSampleFSDate in VB)
                # We use self.cal_fs_date_par as the reference here
                current_date = self.start_date_par
                while current_date < self.cal_fs_date_par:
                     _ = f_ptand.readline() # Skip line
                     current_date += datetime.timedelta(days=1) # Need careful handling for non-standard calendars if year_length_par != 365/366

                # Read the NDays data used in calibration
                for _ in range(self.n_days_cal_par):
                    line = f_ptand.readline()
                    if not line: break # End of file
                    try:
                        self.rank_data.append(float(line.strip()))
                    except ValueError:
                        self.rank_data.append(GLOBAL_MISSING_CODE) # Handle potential missing data

        except Exception as e:
            raise IOError(f"Error reading predictand file {ptand_path}: {e}")

        if not self.rank_data:
             raise ValueError("No data read from predictand file for Inverse Normal.")

        # --- Sort the data ---
        self.rank_data = shell_sort(self.rank_data) # Sorts in place

        # --- Determine number of days greater than threshold ---
        self.inv_norm_first_value = -1 # Use -1 to indicate not found initially
        for i, val in enumerate(self.rank_data):
            if val > THRESH:
                self.inv_norm_first_value = i # 0-based index
                break

        if self.inv_norm_first_value == -1:
            raise ValueError("No data found above the threshold in the predictand file for Inverse Normal.")

        self.inv_norm_n_split = len(self.rank_data) - self.inv_norm_first_value

        if self.inv_norm_n_split <= 0:
             raise ValueError("Inverse Normal nSplit is zero or negative.")


        # --- Locate lower bound (limit) for CDF estimation ---
        z_start = 1.0 / (self.inv_norm_n_split + 1.0)
        delta = 0.0001
        area = 0.5
        fx = 0.0
        fx_old = normal_pdf(fx)
        self.inv_norm_limit = 0.0 # Default

        for _ in range(50000): # Max iterations
            fx -= delta
            fx_new = normal_pdf(fx)
            area -= (delta * 0.5 * (fx_old + fx_new))
            if area <= z_start:
                self.inv_norm_limit = fx
                break
            fx_old = fx_new
        else: # Loop finished without break
            QMessageBox.warning(self, "Inverse Normal Warning", "Could not find lower limit (z_start) within iterations.")
            # Handle this case? Maybe use a default limit or raise error?
            self.inv_norm_limit = -5.0 # Arbitrary fallback

        self.inv_norm_total_area = (1.0 - (2.0 * z_start))
        if self.inv_norm_total_area <= 0:
             raise ValueError("Inverse Normal total area calculation resulted in non-positive value.")

    def _translator_inv_norm(self, passed_value):
        """Inverse Normal Transform: Converts Z-score back to data value."""
        if passed_value <= self.inv_norm_limit:
            return self.rank_data[self.inv_norm_first_value]
        else:
            interval = (passed_value - self.inv_norm_limit) / 100.0
            area = 0.0
            fx_old = normal_pdf(self.inv_norm_limit)
            fx = self.inv_norm_limit
            for _ in range(100):
                fx += interval
                fx_new = normal_pdf(fx)
                area += (interval * 0.5 * (fx_old + fx_new))
                fx_old = fx_new

            if area > self.inv_norm_total_area:
                area = self.inv_norm_total_area

            # Calculate index carefully (0-based)
            locate_value_float = area * self.inv_norm_n_split / self.inv_norm_total_area
            locate_index_offset = int(locate_value_float) # Floor

            locate_index = self.inv_norm_first_value + locate_index_offset

            # Clamp index to valid range
            max_index = self.inv_norm_first_value + self.inv_norm_n_split - 1
            if locate_index >= max_index:
                 locate_index = max_index
            if locate_index < self.inv_norm_first_value: # Should not happen if logic is correct
                 locate_index = self.inv_norm_first_value

            if 0 <= locate_index < len(self.rank_data):
                return self.rank_data[locate_index]
            else:
                # Handle index out of bounds - should ideally not happen
                QMessageBox.warning(self, "Translator Warning", f"Calculated index {locate_index} out of bounds.")
                # Return first or last valid value?
                return self.rank_data[self.inv_norm_first_value] if passed_value <= self.inv_norm_limit else self.rank_data[-1]


    def synthesizeData(self):
        """Performs the main data synthesis based on loaded PAR and UI settings."""
        # --- Initial Validation ---
        if not self.par_file_path or not os.path.exists(self.par_file_path):
            QMessageBox.warning(self, "Missing Input", "You must select a valid parameter file first.")
            return
        if not self.out_file_path:
            QMessageBox.warning(self, "Missing Input", "You must select a suitable output file to save to.")
            return
        if not self.predictor_dir or not os.path.isdir(self.predictor_dir):
            QMessageBox.warning(self, "Missing Input", "You must select a valid predictor directory.")
            return

        try:
            ensemble_size = int(self.eSize.text())
            if not 1 <= ensemble_size <= 100:
                QMessageBox.warning(self, "Invalid Input", "Ensemble size must be between 1 and 100.")
                return

            try:
                 # Use standard date parsing
                 synthesis_start_date = datetime.datetime.strptime(self.fStartText.text(), '%d/%m/%Y').date()
            except ValueError:
                QMessageBox.warning(self, "Invalid Input", "Synthesis start date is invalid (use dd/mm/yyyy format).")
                return

            synthesis_length = int(self.fLengthText.text())
            if synthesis_length < 1:
                QMessageBox.warning(self, "Invalid Input", "Synthesis length must be at least 1 day.")
                return

            # Check dates relative to PAR file dates
            if self.start_date_par and synthesis_start_date < self.start_date_par:
                 QMessageBox.warning(self, "Date Warning", "Synthesis start date should normally be later than or equal to the record start date from the PAR file.")
                 # Allow continuing, but warn user.

        except ValueError:
            QMessageBox.critical(self, "Invalid Input", "Please check Ensemble Size and Synthesis Length are valid integers.")
            return
        except Exception as e:
             QMessageBox.critical(self, "Input Error", f"Error processing inputs: {e}")
             return

        # --- Setup before starting ---
        self._cancel_synthesis = False
        sim_file_path = os.path.splitext(self.out_file_path)[0] + ".SIM"

        # --- Random Seed ---
        if RANDOM_SEED_FIXED:
             random.seed(1) # Mimics Rnd -1; Randomize 1
             np.random.seed(1) # Seed numpy's generator too
        # else: let Python seed based on time/OS sources

        # --- Progress Dialog ---
        progress = QProgressDialog("Synthesizing Data...", "Cancel", 0, synthesis_length, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setWindowTitle("Processing")
        progress.setValue(0)
        progress.show()

        # --- Main Synthesis Logic ---
        predictor_file_handles = []
        out_file_handle = None

        try:
            # --- Prepare Inverse Normal Transform Data (if needed) ---
            if self.local_model_trans == 4:
                 progress.setLabelText("Preparing Inverse Normal data...")
                 QApplication.processEvents() # Update UI
                 self._prepare_inverse_normal()

            # --- Open Predictor Files ---
            progress.setLabelText("Opening predictor files...")
            QApplication.processEvents() # Update UI
            predictor_files_to_open = self.predictor_filenames[1:] # Skip predictand, open only predictors
            if not predictor_files_to_open:
                 raise ValueError("No predictor files listed in PAR file to open.")

            for filename in predictor_files_to_open:
                filepath = os.path.join(self.predictor_dir, filename)
                if not os.path.exists(filepath):
                    raise FileNotFoundError(f"Required predictor file not found: {filepath}")
                try:
                    # Open in text mode, assuming one value per line
                    predictor_file_handles.append(open(filepath, 'r'))
                except Exception as e:
                    raise IOError(f"Could not open predictor file {filepath}: {e}")

            # --- Open Output File ---
            out_file_handle = open(self.out_file_path, 'w')

            # --- Initialize Detrending Variables ---
            days_used_linear = {} # Dict: {period_index: count}
            days_used_power = {}  # Dict: {period_index: count}
            # Baseline calculation needs careful porting of DateDiff and calendar logic
            cal_fs_date_baseline = {} # Dict: {period_index: count}
            fs_date_baseline = {}     # Dict: {period_index: count}

            if self.de_trend:
                progress.setLabelText("Initializing detrend variables...")
                QApplication.processEvents() # Update UI

                # Initialize counts to 0
                trend_rows = 1 if self.season_code == 1 else (4 if self.season_code == 4 else 12)
                for i in range(trend_rows):
                    cal_fs_date_baseline[i] = 0
                    fs_date_baseline[i] = 0
                    days_used_power[i] = 0 # Power trend uses days from start_date_par

                # Calculate baseline for CalFSDate relative to StartDate
                current_d = self.start_date_par
                days_diff_cal = (self.cal_fs_date_par - self.start_date_par).days
                for d_idx in range(days_diff_cal):
                    if progress.wasCanceled(): raise InterruptedError("Synthesis cancelled")
                    month = current_d.month
                    if self.season_code == 1: period_idx = 0
                    elif self.season_code == 4: period_idx = get_season(month) - 1
                    else: period_idx = month - 1 # 0-11

                    if period_idx in cal_fs_date_baseline: # Check if index is valid
                         cal_fs_date_baseline[period_idx] += 1
                    # Increment date (handle calendar specifics if year_length_par != 365/366)
                    current_d += datetime.timedelta(days=1)


            # --- Skip Initial Data in Predictor Files ---
            progress.setLabelText("Skipping initial predictor data...")
            QApplication.processEvents() # Update UI
            days_to_skip = (synthesis_start_date - self.start_date_par).days
            if days_to_skip < 0:
                QMessageBox.warning(self, "Date Warning", "Synthesis start date is before PAR record start date. Skipping cannot be performed correctly.")
                days_to_skip = 0 # Or handle error?

            current_d_skip = self.start_date_par
            for day_skip_idx in range(days_to_skip):
                 if progress.wasCanceled(): raise InterruptedError("Synthesis cancelled")
                 # Update progress less frequently during skip?
                 if day_skip_idx % 100 == 0:
                      progress.setValue(int((day_skip_idx / days_to_skip) * (synthesis_length * 0.1))) # Show some progress during skip
                      QApplication.processEvents()

                 # Read and discard line from each predictor file
                 for f_handle in predictor_file_handles:
                     _ = f_handle.readline()

                 # Update detrend baseline counts if detrending
                 if self.de_trend:
                      month = current_d_skip.month
                      if self.season_code == 1: period_idx = 0
                      elif self.season_code == 4: period_idx = get_season(month) - 1
                      else: period_idx = month - 1 # 0-11

                      if period_idx in fs_date_baseline: # Check if index is valid
                          fs_date_baseline[period_idx] += 1
                          days_used_power[period_idx] += 1 # Power trend uses days from start_date_par

                 current_d_skip += datetime.timedelta(days=1)


            # --- Initialize Simulation State ---
            current_date = synthesis_start_date
            # AR Seed: Initialize with intercept b0 (param index 0) for the starting month
            start_month_idx = synthesis_start_date.month - 1
            initial_intercept = self.uncon_parms[start_month_idx, 0] if not np.isnan(self.uncon_parms[start_month_idx, 0]) else 0.0
            auto_regression_seed = np.full(ensemble_size, initial_intercept)

            if self.de_trend:
                # Initialize linear trend counter based on difference between FSDate and CalFSDate baselines
                for i in range(trend_rows):
                     days_used_linear[i] = fs_date_baseline.get(i, 0) - cal_fs_date_baseline.get(i, 0)


            # --- Main Simulation Loop ---
            progress.setLabelText("Running synthesis...")
            progress.setMaximum(synthesis_length) # Reset max for main loop
            QApplication.processEvents()

            for day_counter in range(synthesis_length):
                progress.setValue(day_counter)
                if progress.wasCanceled():
                    raise InterruptedError("Synthesis cancelled")
                QApplication.processEvents() # Keep UI responsive

                current_month_idx = current_date.month - 1 # 0-11 index for arrays

                # --- Update Detrend Day Counts ---
                period_value_idx = -1 # Index for accessing BetaTrend etc.
                if self.de_trend:
                    month = current_date.month
                    if self.season_code == 1: period_value_idx = 0
                    elif self.season_code == 4: period_value_idx = get_season(month) - 1
                    else: period_value_idx = month - 1 # 0-11

                    if period_value_idx in days_used_linear:
                        days_used_linear[period_value_idx] += 1
                        days_used_power[period_value_idx] += 1
                    else:
                         # This case should ideally not happen if initialized correctly
                         QMessageBox.warning(self, "Detrend Warning", f"Detrend index {period_value_idx} not found for date {current_date}. Trend not applied for this day.")


                # --- Read Predictor Data for the Day ---
                predictor_data = np.full(self.n_predictors, GLOBAL_MISSING_CODE)
                missing_flag = False
                for i, f_handle in enumerate(predictor_file_handles):
                    line = f_handle.readline()
                    if not line:
                        # End of predictor file reached prematurely
                        raise EOFError(f"Predictor file {self.predictor_filenames[i+1]} ended unexpectedly at day {day_counter+1} ({current_date}).")
                    try:
                        val = float(line.strip())
                        predictor_data[i] = val
                        if val == GLOBAL_MISSING_CODE:
                            missing_flag = True
                    except ValueError:
                        predictor_data[i] = GLOBAL_MISSING_CODE
                        missing_flag = True
                        # Maybe warn user about parsing error?

                # --- Downscaling Algorithm ---
                prediction = np.full(ensemble_size, GLOBAL_MISSING_CODE) # Store results for the day

                if not missing_flag:
                    # Get parameters for the current month (0-based index)
                    current_uncon_params = self.uncon_parms[current_month_idx, :]
                    current_con_params = self.con_parms[current_month_idx, :] if self.rain_yes else None
                    if self.local_model_trans == 5:
                        current_lambda_params = self.lamda_array[current_month_idx, :]


                    # Indices for unconditional parameters
                    idx_b0_uncon = 0
                    idx_b1_uncon = 1
                    idx_se_uncon = idx_b1_uncon + self.n_predictors
                    idx_ar_uncon = idx_se_uncon + 1 if self.auto_regression else -1

                    for ensemble_idx in range(ensemble_size):
                        # Base prediction: b0 + b1*x1 + ... + bn*xn
                        pred = current_uncon_params[idx_b0_uncon] + np.sum(current_uncon_params[idx_b1_uncon:idx_se_uncon] * predictor_data)

                        # Add Autoregression term
                        if self.auto_regression:
                            pred += auto_regression_seed[ensemble_idx] * current_uncon_params[idx_ar_uncon]

                        # Calculate Residual (Stochasticity) - Use numpy for normal dist
                        std_err_uncon = current_uncon_params[idx_se_uncon]
                        residual = np.random.normal(loc=0.0, scale=std_err_uncon) if std_err_uncon > 0 else 0.0
                        # --- N(0,1)*SE approach from VB6 (less standard than np.random.normal) ---
                        # if PREC_N > 0 and std_err_uncon > 0:
                        #     sum_rnd = sum(random.random() for _ in range(PREC_N))
                        #     residual = (sum_rnd - (PREC_N / 2.0)) / math.sqrt(PREC_N / 12.0) # Approx N(0,1)
                        #     residual *= std_err_uncon # Scale by SE
                        # else:
                        #     residual = 0.0
                        # ------------------------------------------------------------------------

                        # Add residual ONLY if unconditional process
                        if not self.rain_yes:
                            pred += residual

                        # Apply Detrending ONLY if unconditional process
                        trend_adjustment = 0.0
                        if not self.rain_yes and self.de_trend and period_value_idx != -1:
                             trend_params = self.beta_trend[period_value_idx, :]
                             if self.de_trend_type == 1: # Linear
                                 trend_adjustment = trend_params[1] * days_used_linear[period_value_idx]
                             else: # Power
                                 trend_adjustment = (trend_params[0] * (days_used_power[period_value_idx] ** trend_params[1]))
                                 trend_adjustment -= abs(trend_params[2]) # Subtract minimum
                                 trend_adjustment -= 0.001 # Small offset like VB6?

                             pred += trend_adjustment


                        # Apply constraints (e.g., non-negative) only for unconditional final value
                        if not self.rain_yes and not ALLOW_NEG and pred < 0:
                             pred = 0.0

                        # Store prediction (either intermediate for conditional, or final for unconditional)
                        prediction[ensemble_idx] = pred
                        # Update AR seed for next day (using the value *before* conditional logic/transformation)
                        auto_regression_seed[ensemble_idx] = pred


                    # --- Conditional Process (Rainfall Occurrence & Amount) ---
                    if self.rain_yes:
                        # Determine Wet/Dry Day Status
                        is_wet = np.zeros(ensemble_size, dtype=bool)
                        for ensemble_idx in range(ensemble_size):
                            prob_wet = prediction[ensemble_idx] # This was the unconditional output (often probability)
                            if CONDITIONAL_SELECTION == 1: # Rob's approach
                                is_wet[ensemble_idx] = (random.random() <= prob_wet)
                            else: # Threshold approach
                                is_wet[ensemble_idx] = (prob_wet >= CONDITIONAL_THRESH)
                            # Update AR seed based on wet/dry (0 or 1)
                            auto_regression_seed[ensemble_idx] = 1.0 if is_wet[ensemble_idx] else 0.0


                        # Calculate Amount for Wet Days
                        idx_b0_con = 0
                        idx_varinf_con = 1
                        idx_b1_con = 2
                        idx_se_con = idx_b1_con + self.n_predictors

                        for ensemble_idx in range(ensemble_size):
                             if is_wet[ensemble_idx]:
                                 # Calculate conditional prediction (amount base)
                                 # b0 + b1*x1 + ... + bn*xn (NOTE: indices shifted by varinf)
                                 pred_amount_base = current_con_params[idx_b0_con] + np.sum(current_con_params[idx_b1_con:idx_se_con] * predictor_data)

                                 # Calculate Residual for Amount
                                 std_err_con = current_con_params[idx_se_con]
                                 residual_amount = np.random.normal(loc=0.0, scale=std_err_con) if std_err_con > 0 else 0.0
                                 # --- VB6 N(0,1)*SE approach ---
                                 # if PREC_N > 0 and std_err_con > 0:
                                 #     sum_rnd = sum(random.random() for _ in range(PREC_N))
                                 #     residual_amount = (sum_rnd - (PREC_N / 2.0)) / math.sqrt(PREC_N / 12.0)
                                 #     residual_amount *= std_err_con
                                 # else:
                                 #      residual_amount = 0.0
                                 # ------------------------------

                                 # Combine base prediction and residual BEFORE transformation/detrending
                                 pred_amount_combined = pred_amount_base + residual_amount


                                 # Apply Detrending to the COMBINED value for conditional process
                                 trend_adjustment = 0.0
                                 if self.de_trend and period_value_idx != -1:
                                     trend_params = self.beta_trend[period_value_idx, :]
                                     if self.de_trend_type == 1: # Linear
                                         trend_adjustment = trend_params[1] * days_used_linear[period_value_idx]
                                     else: # Power
                                         trend_adjustment = (trend_params[0] * (days_used_power[period_value_idx] ** trend_params[1]))
                                         trend_adjustment -= abs(trend_params[2]) # Subtract minimum
                                         trend_adjustment -= 0.001
                                     pred_amount_combined += trend_adjustment


                                 # Apply Variance Inflation & Bias Correction & Inverse Transformation
                                 var_inf = current_con_params[idx_varinf_con] # Variance inflation factor
                                 final_pred_amount = 0.0

                                 try:
                                     # ModelTrans 1 (None) or 4 (InvNorm needs special handling)
                                     if self.local_model_trans == 1 or self.local_model_trans == 4:
                                         interim_val = var_inf * pred_amount_combined # Apply VarInf first
                                         if self.local_model_trans == 4:
                                              final_pred_amount = self._translator_inv_norm(interim_val)
                                         else:
                                              final_pred_amount = interim_val # No further transform for type 1

                                     # ModelTrans 2 (Fourth Root)
                                     elif self.local_model_trans == 2:
                                         interim_val = var_inf * pred_amount_combined
                                         # Need to handle potential negative base for even root
                                         if interim_val < 0:
                                              # How was this handled in VB6? Apply root to abs value and keep sign? Or set to 0?
                                              # Assuming set to 0 for rainfall amount. Adjust if needed.
                                              final_pred_amount = 0.0
                                         else:
                                              final_pred_amount = interim_val ** 0.25 # Apply 4th root (power 0.25)

                                     # ModelTrans 3 (Log - Natural Log implied)
                                     elif self.local_model_trans == 3:
                                         interim_val = var_inf * pred_amount_combined
                                         final_pred_amount = math.exp(interim_val) # Inverse is exp()

                                     # ModelTrans 5 (Box-Cox)
                                     elif self.local_model_trans == 5:
                                         interim_val = var_inf * pred_amount_combined
                                         lamda = current_lambda_params[0]
                                         right_shift = current_lambda_params[1]

                                         # Add back right shift before inverse transform
                                         val_to_transform = interim_val + right_shift

                                         if lamda == 0: # Log transform case
                                             if val_to_transform <= 0: # Cannot take log
                                                  final_pred_amount = GLOBAL_MISSING_CODE # Or some indicator of failure
                                             else:
                                                 # Inverse is exp(), then subtract right shift
                                                 final_pred_amount = math.exp(val_to_transform) - right_shift
                                         else: # Power transform case
                                             term = val_to_transform * lamda + 1.0
                                             if term <= 0: # Cannot raise non-positive to fractional power or take log
                                                  final_pred_amount = GLOBAL_MISSING_CODE
                                             else:
                                                  # Using numpy power for potential fractional exponent
                                                  final_pred_amount = np.power(term, 1.0 / lamda) - right_shift
                                                  # VB uses Log(term) / lamda then Exp(). Equivalent to above.
                                                  # final_pred_amount = math.exp(math.log(term) / lamda) - right_shift

                                     else: # Should not happen if PAR is valid
                                          final_pred_amount = pred_amount_combined # Default to no transform? Or error?

                                     # Apply Bias Correction AFTER inverse transform
                                     final_pred_amount *= BIAS_CORRECTION

                                     # Final Threshold Check (e.g., ensure rainfall >= THRESH)
                                     if final_pred_amount != GLOBAL_MISSING_CODE and final_pred_amount < THRESH:
                                          # Add small amount to distinguish from zero/dry day?
                                          final_pred_amount = THRESH + 0.001 if THRESH == 0 else THRESH

                                     # Store final conditional prediction
                                     prediction[ensemble_idx] = final_pred_amount

                                 except (ValueError, OverflowError, TypeError) as transform_err:
                                     # Handle math errors during transformation
                                     QMessageBox.warning(self, "Transform Error", f"Math error on day {day_counter+1}, ensemble {ensemble_idx+1}: {transform_err}. Setting to missing.")
                                     prediction[ensemble_idx] = GLOBAL_MISSING_CODE

                             else: # Dry day
                                 prediction[ensemble_idx] = THRESH # Or 0.0 for rainfall


                # --- Write Results for the Day ---
                output_line = "\t".join([f"{val:.3f}" if val != GLOBAL_MISSING_CODE else f"{GLOBAL_MISSING_CODE:.3f}" for val in prediction])
                out_file_handle.write(output_line + "\n")

                # --- Increment Date ---
                current_date += datetime.timedelta(days=1)
                # Need logic here if self.year_length_par requires non-standard calendar jumps

            # --- End of Main Loop ---

            progress.setValue(synthesis_length) # Ensure progress bar completes

            # --- Create *.SIM File ---
            progress.setLabelText("Creating SIM file...")
            QApplication.processEvents()
            with open(sim_file_path, 'w') as sim_f:
                 sim_f.write(f"{self.n_predictors}\n")
                 sim_f.write(f"{self.season_code}\n")
                 sim_f.write(f"{YEAR_INDICATOR}\n") # Use a defined constant or value from settings
                 sim_f.write(f"{synthesis_start_date.strftime('%d/%m/%Y')}\n") # Use actual synthesis start
                 sim_f.write(f"{synthesis_length}\n") # Use actual synthesis length
                 sim_f.write(f"{self.rain_yes}\n") # Write boolean as string? Or VB uses -1/0? Check SDSM format. Using True/False string here.
                 sim_f.write(f"{ensemble_size}\n") # Actual ensemble size used
                 sim_f.write(f"{PREC_N}\n") # Variance inflation N value
                 sim_f.write(f"{self.local_model_trans}\n")
                 sim_f.write(f"{BIAS_CORRECTION}\n")
                 sim_f.write(f"{self.ptand_filename}\n")
                 # Write predictor filenames (excluding predictand)
                 for fname in self.predictor_filenames[1:]:
                     sim_f.write(f"{fname}\n")

            # --- Success Message ---
            QMessageBox.information(self, "Synthesis Complete",
                                f"Weather data synthesis finished successfully.\nOutput: {self.out_file_path}\nSummary: {sim_file_path}")

        except FileNotFoundError as e:
            QMessageBox.critical(self, "File Error", f"Required file not found:\n{e}")
        except EOFError as e:
             QMessageBox.critical(self, "File Error", f"Error reading predictor data:\n{e}")
        except InterruptedError as e:
             QMessageBox.warning(self, "Cancelled", f"{e}")
        except IOError as e:
            QMessageBox.critical(self, "File I/O Error", f"Error reading or writing file:\n{e}")
        except MemoryError:
             QMessageBox.critical(self, "Memory Error", "Not enough memory to complete the operation. Try a smaller synthesis length or ensemble size.")
        except Exception as e:
            # Catch any other unexpected errors
            import traceback
            QMessageBox.critical(self, "Synthesis Error", f"An unexpected error occurred during synthesis:\n{e}\n\n{traceback.format_exc()}") # Include traceback for debugging
        finally:
            # --- Ensure Files are Closed ---
            if out_file_handle and not out_file_handle.closed:
                out_file_handle.close()
            for f_handle in predictor_file_handles:
                if f_handle and not f_handle.closed:
                    f_handle.close()
            progress.close() # Close progress dialog

    def reset_all(self):
        """Resets the UI fields and internal state."""
        try:
            self.par_file_path = ""
            self.predictor_dir = ""
            self.out_file_path = ""
            self.par_file_text.setText("Not selected")
            self.dirText.setText("Not selected")
            self.outFileText.setText("Not selected")
            self.eSize.setText("20")
            self.predictorList.clear()
            self.no_of_pred_text.setText("0")
            self.auto_regress_label.setText("Unknown")
            self.process_label.setText("Unknown")
            self.r_start_text.setText("unknown")
            self.r_length_text.setText("unknown")
            self.fStartText.setText("01/01/1948") # Reset to a default
            self.fLengthText.setText("365")      # Reset to a default

            # Clear parsed PAR data
            self.n_predictors = 0
            self.season_code = 0
            self.year_length_par = 0
            self.start_date_par = None
            self.n_days_r_par = 0
            self.cal_fs_date_par = None
            self.n_days_cal_par = 0
            self.rain_yes = False
            self.local_model_trans = 0
            self.auto_regression = False
            self.ptand_filename = ""
            self.predictor_filenames = []
            self.uncon_parms = None
            self.con_parms = None
            self.lamda_array = None
            self.beta_trend = None
            self.de_trend = False
            self.de_trend_type = 0
            self.ptand_file_root = ""
            self.rank_data = []
            self.inv_norm_first_value = 0
            self.inv_norm_n_split = 0
            self.inv_norm_limit = 0.0
            self.inv_norm_total_area = 0.0

            QMessageBox.information(self, "Reset Complete", "All fields have been reset.")
        except Exception as e:
            QMessageBox.critical(self, "Reset Error", f"Error during reset: {str(e)}")


# --- Main Application Runner (Example) ---
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication, QMainWindow

    # Set GLOBAL_MISSING_CODE, THRESH etc. here if needed globally
    # GLOBAL_MISSING_CODE = -99.9

    app = QApplication(sys.argv)
    mainWindow = QMainWindow()
    mainWindow.setWindowTitle("SDSM Synthesize Data (Python Demo)")
    contentWidget = ContentWidget()
    mainWindow.setCentralWidget(contentWidget)
    mainWindow.setGeometry(100, 100, 600, 800) # Adjust size as needed
    mainWindow.show()
    sys.exit(app.exec_())