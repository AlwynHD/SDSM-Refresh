import os
import math
import random
import datetime
import calendar # Keep for potential future non-Gregorian logic if needed
import numpy as np
from scipy.stats import norm as scipy_norm # Use scipy for normal distribution PDF
import traceback # For detailed error reporting

from PyQt5.QtWidgets import (QVBoxLayout, QWidget, QHBoxLayout, QPushButton,
                             QFrame, QLabel, QLineEdit, QFileDialog, QGroupBox,
                             QGridLayout, QListWidget, QMessageBox, QProgressDialog, QApplication, QMainWindow)
from PyQt5.QtCore import Qt, QCoreApplication # Added QCoreApplication

# --- Helper Functions ---
def normal_pdf(x):
    """Probability Density Function of the standard normal distribution."""
    # Using scipy's implementation is generally robust
    try:
        return scipy_norm.pdf(x)
    except Exception:
         # Handle potential issues with extreme values if scipy raises an error
         return 0.0

def get_season(month):
    """Returns season index (0-3 for Winter, Spring, Summer, Autumn)."""
    # Assuming Northern Hemisphere seasons matching VB GetSeason logic implicitly
    # VB GetSeason likely maps Dec/Jan/Feb->1, Mar/Apr/May->2, Jun/Jul/Aug->3, Sep/Oct/Nov->4
    # Python indices will be 0-based.
    if month in [12, 1, 2]: return 0 # Winter
    elif month in [3, 4, 5]: return 1 # Spring
    elif month in [6, 7, 8]: return 2 # Summer
    elif month in [9, 10, 11]: return 3 # Autumn
    else: raise ValueError(f"Invalid month: {month}")

def parse_fixed_width(line, width=14):
    """Parses a line with fixed-width floating point numbers."""
    values = []
    line_stripped = line.rstrip() # Handle potential trailing whitespace once
    line_len = len(line_stripped)
    for i in range(0, line_len, width):
        # Ensure segment doesn't exceed actual stripped line length
        segment = line_stripped[i:min(i + width, line_len)].strip()
        if segment: # Only process non-empty segments
            try:
                values.append(float(segment))
            except ValueError:
                # Handle segments that are not valid floats (e.g., "---")
                values.append(np.nan) # Use NaN for parsing errors
        # Do not append if segment is empty (e.g., caused by trailing spaces within width)
    return values

def shell_sort(arr):
    """Sorts a list using Shell's method (as in VB6 example)."""
    # Convert to numpy array for potential efficiency if large, but work with list copy
    arr_copy = list(arr) # Work on a copy
    n = len(arr_copy)
    gap = n // 2
    while gap > 0:
        for i in range(gap, n):
            temp = arr_copy[i]
            j = i
            # Use while loop condition similar to VB GOTO structure
            while j >= gap and arr_copy[j - gap] > temp:
                arr_copy[j] = arr_copy[j - gap]
                j -= gap
            arr_copy[j] = temp
        gap //= 2
    return arr_copy

# --- Main Widget Class ---
class ContentWidget(QWidget):
    def __init__(self, settings=None):
        super().__init__()

        # --- Load Settings ---
        default_settings = {
            'allowNeg': True, 'randomSeed': False, 'thresh': 0.0,
            'globalMissingCode': -999.0, 'varianceInflation': 12,
            'biasCorrection': 1.0, 'fixedThreshold': 0.5,
            'conditionalSelection': 'Stochastic', # 'Stochastic' or 'Fixed'
            'yearIndicator': 365, 'globalSDate': "01/01/1961",
            'defaultDir': os.path.expanduser("~")
        }
        self.settings = settings if settings else default_settings

        # Get values from settings, ensuring correct types
        self.allow_neg = bool(self.settings.get('allowNeg', True))
        self.use_random_seed = bool(self.settings.get('randomSeed', False))
        self.thresh = float(self.settings.get('thresh', 0.0))
        self.global_missing_code = float(self.settings.get('globalMissingCode', -999.0))
        # *** CRITICAL: Variance Inflation is PrecN in VB6 ***
        self.prec_n = int(self.settings.get('varianceInflation', 12))
        self.bias_correction = float(self.settings.get('biasCorrection', 1.0))
        self.conditional_thresh = float(self.settings.get('fixedThreshold', 0.5))
        cond_sel_str = str(self.settings.get('conditionalSelection', 'Stochastic')).lower()
        # Use 1 for Stochastic (VB Rnd <= Pred), 2 for Fixed (VB Pred >= Thresh)
        self.conditional_selection = 1 if cond_sel_str == 'stochastic' else 2
        self.year_indicator = int(self.settings.get('yearIndicator', 365)) # Note: VB PAR reads 'DummyYearLength', SIM writes 'YearIndicator' from settings
        self.default_dir = self.settings.get('defaultDir', os.path.expanduser("~"))
        # --- End Settings ---

        self.par_file_path = ""
        self.predictor_dir = self.default_dir # Start with default predictor dir
        self.out_file_path = ""

        # --- Variables to store parsed PAR data ---
        self.n_predictors = 0
        self.season_code = 0 # 1=Ann, 4=Seas, 12=Mon
        self.year_length_par = 0 # 360, 365, 366 read from PAR (VB DummyYearLength)
        self.start_date_par = None # datetime.date (Record Start Date)
        self.n_days_r_par = 0
        self.cal_fs_date_par = None # datetime.date (Calibration Fit Start Date)
        self.n_days_cal_par = 0
        self.rain_yes = False # Is conditional process?
        self.local_model_trans = 0 # 1=none, 2=4th, 3=ln, 4=InvNorm, 5=BoxCox
        self.auto_regression = False
        self.ptand_filename = ""
        self.predictor_filenames = [] # Includes predictand at index 0
        self.uncon_parms = None # Numpy array [month_idx (0-11), param_idx]
        self.con_parms = None   # Numpy array [month_idx (0-11), param_idx]
        self.lamda_array = None # Numpy array [month_idx (0-11), 0=lambda, 1=rightshift]
        self.beta_trend = None  # Numpy array [period_idx (0-seasoncode-1), param_idx]
        self.de_trend = False   # Was detrending applied during calibration?
        self.de_trend_type = 0  # 1=linear, 2=power
        self.ptand_file_root = "" # Path to predictand file for Inv Norm or general reference
        # --- Variables for Inverse Normal Transform ---
        self.rank_data = []
        self.inv_norm_first_value_idx = -1 # 0-based Index in sorted rank_data >= thresh
        self.inv_norm_n_split = 0 # Count of values >= thresh
        self.inv_norm_limit = 0.0 # Lower z-score bound
        self.inv_norm_total_area = 0.0 # Area between lower/upper bounds
        # --- Parameter Indices (will be set after parsing PAR) ---
        self.idx_b0_uncon = -1 # Intercept (B0)
        self.idx_b1_uncon = -1 # First predictor coeff (B1)
        self.idx_se_uncon = -1 # Standard Error
        self.idx_ar_uncon = -1 # Autoregression coeff
        self.idx_lambda = -1   # BoxCox Lambda (stored with Uncon params if present)
        self.idx_rshift = -1   # BoxCox RightShift (stored with Uncon params if present)

        self.idx_b0_con = -1     # Intercept (C0)
        self.idx_varinf_con = -1 # Variance Inflation (C1 in VB comments, Parm(2) in code)
        self.idx_b1_con = -1     # First predictor coeff (C2)
        self.idx_se_con = -1     # Standard Error
        # --- Other state ---
        self._cancel_synthesis = False

        # --- UI Setup ---
        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(10, 10, 10, 10) # Further reduced margins
        mainLayout.setSpacing(10) # Further reduced spacing
        self.setLayout(mainLayout)

        # --- File Selection Section ---
        fileSelectionGroup = QGroupBox("File Selection")
        fileSelectionLayout = QGridLayout()
        fileSelectionGroup.setLayout(fileSelectionLayout)
        mainLayout.addWidget(fileSelectionGroup)

        self.parFileButton = QPushButton("📂 Select Parameter File (.PAR)")
        self.parFileButton.clicked.connect(self.selectPARFile)
        self.par_file_text = QLabel("Not selected")
        self.par_file_text.setWordWrap(True)

        self.outFileButton = QPushButton("💾 Save To Output File (.OUT)")
        self.outFileButton.clicked.connect(self.selectOutputFile)
        self.outFileText = QLabel("Not selected")
        self.outFileText.setWordWrap(True)
        self.simLabel = QLabel("(*.SIM summary file will also be created)")

        fileSelectionLayout.addWidget(self.parFileButton, 0, 0)
        fileSelectionLayout.addWidget(self.par_file_text, 0, 1, 1, 2) # Span 2 cols
        fileSelectionLayout.addWidget(self.outFileButton, 1, 0)
        fileSelectionLayout.addWidget(self.outFileText, 1, 1, 1, 2) # Span 2 cols
        fileSelectionLayout.addWidget(self.simLabel, 2, 1, 1, 2)

        # --- Predictor Directory Section ---
        predictorDirGroup = QGroupBox("Predictor Data Directory")
        predictorDirLayout = QGridLayout()
        predictorDirGroup.setLayout(predictorDirLayout)
        mainLayout.addWidget(predictorDirGroup)

        self.dirButton = QPushButton("📁 Select Directory Containing Predictor Files")
        self.dirButton.clicked.connect(self.selectPredictorDirectory)
        self.dirText = QLabel(self.predictor_dir) # Show initial default
        self.dirText.setWordWrap(True)

        predictorDirLayout.addWidget(self.dirButton, 0, 0)
        predictorDirLayout.addWidget(self.dirText, 0, 1)

        # --- Data Section ---
        dataGroup = QGroupBox("Model & Data Specification (from PAR)")
        dataLayout = QGridLayout()
        dataGroup.setLayout(dataLayout)
        mainLayout.addWidget(dataGroup)

        self.viewDetailsButton = QPushButton("View/Verify Predictor Files")
        self.viewDetailsButton.setToolTip("Check if predictor files listed in the PAR exist in the selected directory")
        self.viewDetailsButton.clicked.connect(self.viewPredictors)
        dataLayout.addWidget(self.viewDetailsButton, 0, 0, 1, 2)

        self.predictorList = QListWidget()
        self.predictorList.setToolTip("Predictand (first) and Predictor files read from PAR")
        self.predictorList.setMaximumHeight(150) # Reduced height further
        dataLayout.addWidget(self.predictorList, 1, 0, 1, 2)

        def add_info_row(layout, row, label_text, value_widget):
            label = QLabel(label_text)
            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            layout.addWidget(label, row, 0)
            layout.addWidget(value_widget, row, 1)

        self.no_of_pred_text = QLabel("0")
        add_info_row(dataLayout, 2, "No. of predictors:", self.no_of_pred_text)

        self.auto_regress_label = QLabel("Unknown")
        add_info_row(dataLayout, 3, "Autoregression:", self.auto_regress_label)

        self.process_label = QLabel("Unknown")
        add_info_row(dataLayout, 4, "Process:", self.process_label)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine); separator.setFrameShadow(QFrame.Sunken)
        dataLayout.addWidget(separator, 5, 0, 1, 2)

        self.r_start_text = QLabel("unknown")
        add_info_row(dataLayout, 6, "Record Start:", self.r_start_text)
        self.r_length_text = QLabel("unknown")
        add_info_row(dataLayout, 7, "Record Length:", self.r_length_text)
        self.fStartText = QLineEdit(self.settings.get('globalSDate', "01/01/1961"))
        self.fStartText.setToolTip("Enter synthesis start date (dd/mm/yyyy or mm/dd/yyyy)")
        add_info_row(dataLayout, 8, "Synthesis Start:", self.fStartText)
        self.fLengthText = QLineEdit("365")
        self.fLengthText.setToolTip("Enter number of days to synthesize")
        add_info_row(dataLayout, 9, "Synthesis Length:", self.fLengthText)

        # --- Ensemble Size Section ---
        ensembleGroup = QGroupBox("Ensemble Size")
        ensembleLayout = QHBoxLayout()
        ensembleGroup.setLayout(ensembleLayout)
        mainLayout.addWidget(ensembleGroup)
        ensembleLayout.addWidget(QLabel("Number of ensemble members:"))
        self.eSize = QLineEdit("20")
        self.eSize.setToolTip("Enter number of simulations (1-100)")
        self.eSize.setMaximumWidth(80)
        ensembleLayout.addWidget(self.eSize)
        ensembleLayout.addStretch(1)

        # --- Buttons ---
        buttonLayout = QHBoxLayout()
        mainLayout.addLayout(buttonLayout)
        self.synthesizeButton = QPushButton("🚀 Synthesize Data")
        self.synthesizeButton.clicked.connect(self.synthesizeData)
        self.synthesizeButton.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 5px;")
        self.synthesizeButton.setMinimumHeight(35)
        self.resetButton = QPushButton("🔄 Reset")
        self.resetButton.clicked.connect(self.reset_all)
        self.resetButton.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; padding: 5px;")
        self.resetButton.setMinimumHeight(35)
        buttonLayout.addStretch(1); buttonLayout.addWidget(self.synthesizeButton)
        buttonLayout.addWidget(self.resetButton); buttonLayout.addStretch(1)
        # --- End UI Setup ---

    def selectPredictorDirectory(self):
        """Opens a directory dialog to select the predictor directory."""
        directory = QFileDialog.getExistingDirectory(self, "Select Predictor Directory", self.predictor_dir or os.path.expanduser("~"))
        if directory:
            self.predictor_dir = directory
            self.dirText.setText(directory)
            if self.par_file_path:
                 self.viewPredictors()

    def _parse_date(self, date_str):
        """Tries to parse date string in dd/mm/yyyy or mm/dd/yyyy format."""
        # Handle cases where it might already be a date object
        if isinstance(date_str, datetime.date):
            return date_str
        if isinstance(date_str, datetime.datetime):
            return date_str.date()

        # Proceed with string parsing
        date_str = str(date_str).strip()
        for fmt in ('%d/%m/%Y', '%m/%d/%Y'):
            try:
                return datetime.datetime.strptime(date_str, fmt).date()
            except ValueError:
                pass
        # Handle VB format from Print # statement which might not have slashes
        try:
            # Example: 01-JAN-1961 or similar - try common formats
            return datetime.datetime.strptime(date_str, '%d-%b-%Y').date()
        except ValueError:
             pass
        try: # VB Print # uses system locale - could be MM-DD-YYYY etc.
            return datetime.datetime.strptime(date_str, '%m-%d-%Y').date()
        except ValueError:
             pass
        # Add more formats if needed based on actual VB output
        raise ValueError(f"Date format not recognized: {date_str}")

    def loadPARFile(self, file_path):
        """Loads and parses PAR file data into instance variables."""
        self.reset_parsed_data()
        self.par_file_path = file_path
        self.par_file_text.setText(f"{os.path.basename(file_path)}")

        try:
            with open(file_path, 'r') as par_file:
                lines = [line.strip() for line in par_file] # Read all lines, strip whitespace

            line_idx = 0
            def get_line(allow_empty=False):
                nonlocal line_idx
                while line_idx < len(lines):
                    line = lines[line_idx]
                    line_idx += 1
                    # VB Input often reads until newline, but ignores leading/trailing spaces unless quoted.
                    # Our strip() handles this for most cases. Line Input # reads the whole line.
                    # Let's return the stripped line unless allow_empty is specifically for Line Input #.
                    # Re-reading VB: Line Input # reads *everything*, including spaces.
                    # Need to be careful here. Let's keep strip() for now as it likely handles most PAR formats.
                    if line or allow_empty: # Return non-empty lines or if allowed
                        return line # Return the stripped line
                raise EOFError("Unexpected end of PAR file.")

            # --- Read Header ---
            # 1. No of predictors (Negative indicates detrend applied)
            n_pred_raw_str = get_line()
            n_pred_raw = int(n_pred_raw_str)
            self.de_trend = n_pred_raw < 0
            self.n_predictors = abs(n_pred_raw)
            self.no_of_pred_text.setText(str(self.n_predictors))

            self.season_code = int(get_line())      # 2. Season code (1=Ann, 4=Seas, 12=Mon)
            self.year_length_par = int(get_line())  # 3. Year length - 360, 365, 366 (VB DummyYearLength)
            record_start_str = get_line()           # 4. Record Start date
            self.start_date_par = self._parse_date(record_start_str)
            self.r_start_text.setText(self.start_date_par.strftime('%d/%m/%Y'))
            self.n_days_r_par = int(get_line())     # 5. No of days in record
            self.r_length_text.setText(str(self.n_days_r_par))
            cal_fs_date_str = get_line()            # 6. Calibration start date
            self.cal_fs_date_par = self._parse_date(cal_fs_date_str)
            # Set UI default synthesis start/length based on Calibration info read from PAR
            self.fStartText.setText(self.cal_fs_date_par.strftime('%d/%m/%Y'))
            self.n_days_cal_par = int(get_line())   # 7. No of days in calibration
            self.fLengthText.setText(str(self.n_days_cal_par)) # Use Cal length as default Synth length

            # 8. Rain yes (Conditional Process?) - VB uses Input #, which expects non-quoted True/False
            #    However, some PAR files might use quoted strings or #TRUE#/#FALSE# (from Write #)
            rain_yes_str = get_line()
            cleaned_rain_yes = rain_yes_str.strip('#" ').upper() # Remove quotes, hashes, spaces, uppercase
            self.rain_yes = cleaned_rain_yes == "TRUE"
            self.process_label.setText("Conditional" if self.rain_yes else "Unconditional")

            self.local_model_trans = int(get_line()) # 9. Model transformation (1-5)
            _ = int(get_line()) # 10. Ensemble size from PAR - discard, use UI value

            # --- Handle SDSM 3.1 vs 4.2+ difference (AR flag/Predictand) ---
            # Line 11 could be AR flag ("True"/"False") OR Predictand filename
            potential_ar_or_ptand = get_line()
            # VB Input # reads unquoted True/False case-insensitively
            if potential_ar_or_ptand.upper() in ["TRUE", "FALSE"]: # SDSM 4.2+ format
                self.auto_regression = potential_ar_or_ptand.upper() == "TRUE"
                self.ptand_filename = get_line() # 12. Predictand file name
            else: # SDSM 3.1 or similar format where line 11 IS the predictand name
                self.auto_regression = False # AR didn't exist in 3.1
                self.ptand_filename = potential_ar_or_ptand # Line 11 was predictand name

            self.auto_regress_label.setText(str(self.auto_regression))

            # --- Read Predictor Filenames ---
            self.predictor_filenames = [] # Reset just in case
            self.predictor_filenames.append(self.ptand_filename) # Predictand listed first
            for _ in range(self.n_predictors):
                # VB uses 'Line Input #' which reads the *entire* line including spaces.
                # Python get_line() currently strips. Need to reconsider if exact spacing matters.
                # For filenames, stripping is generally desired. Let's assume PAR files don't rely on leading/trailing spaces in filenames.
                pred_fname = get_line(allow_empty=True).strip() # Read line, strip external whitespace
                self.predictor_filenames.append(pred_fname)

            # --- Determine Parameter Indices *AFTER* knowing AR/BoxCox status ---
            # Unconditional Parameters: Intercept(B0), NPredictors(B1..Bn), StdError(SE)
            # Indices are 0-based
            self.idx_b0_uncon = 0
            self.idx_b1_uncon = 1 # Start index for predictor coeffs B1 to Bn
            # SE index is after B0 and all Bn coeffs
            self.idx_se_uncon = 1 + self.n_predictors
            current_uncon_idx = self.idx_se_uncon # Last assigned index

            # Add AR parameter if used
            if self.auto_regression:
                current_uncon_idx += 1
                self.idx_ar_uncon = current_uncon_idx
            else:
                self.idx_ar_uncon = -1 # No AR parameter index

            # Add BoxCox parameters if used (Lambda and RightShift)
            if self.local_model_trans == 5:
                current_uncon_idx += 1
                self.idx_lambda = current_uncon_idx
                current_uncon_idx += 1
                self.idx_rshift = current_uncon_idx
            else:
                self.idx_lambda = -1
                self.idx_rshift = -1

            # Total number of unconditional parameters per month
            param_count_uncon = current_uncon_idx + 1

            # --- Read Unconditional Model Parameters ---
            # VB format: 12 lines, each potentially with fixed-width (14) parameters + BoxCox params appended
            self.uncon_parms = np.full((12, param_count_uncon), np.nan)
            if self.local_model_trans == 5:
                self.lamda_array = np.full((12, 2), np.nan) # Separate storage matches VB global array

            # Number of parameters expected in the fixed-width part (excluding BoxCox if present)
            params_in_fixed_width_uncon = param_count_uncon
            if self.local_model_trans == 5:
                params_in_fixed_width_uncon -= 2 # Lambda/Shift are appended after fixed width

            for i in range(12): # 12 months
                param_line = get_line()
                # Parse the line using fixed width for the core parameters
                params_parsed = parse_fixed_width(param_line, 14)

                # Assign the fixed-width parameters (B0, B1..Bn, SE, AR?)
                num_to_assign_fixed = min(len(params_parsed), params_in_fixed_width_uncon)
                self.uncon_parms[i, :num_to_assign_fixed] = params_parsed[:num_to_assign_fixed]

                # Extract Lambda/Shift if BoxCox - they appear *after* the fixed-width block in the line
                if self.local_model_trans == 5:
                    # Check if enough values were parsed beyond the fixed-width block
                    if len(params_parsed) > params_in_fixed_width_uncon:
                         lambda_val = params_parsed[params_in_fixed_width_uncon]
                         self.lamda_array[i, 0] = lambda_val
                         self.uncon_parms[i, self.idx_lambda] = lambda_val # Store in main array too
                    if len(params_parsed) > params_in_fixed_width_uncon + 1:
                         rshift_val = params_parsed[params_in_fixed_width_uncon + 1]
                         self.lamda_array[i, 1] = rshift_val
                         self.uncon_parms[i, self.idx_rshift] = rshift_val # Store in main array too


            # --- Read Conditional Model Parameters (if applicable) ---
            if self.rain_yes:
                # Parameters: Intercept(C0), VarInflation(C1), NPredictors(C2..Cn+1), StdError(SE)
                # Indices are 0-based
                # VB indexing in code/comments is 1-based and slightly confusing (C0=Parm(1), VarInf=Parm(2), C2=Parm(3)...)
                self.idx_b0_con = 0     # Intercept C0
                self.idx_varinf_con = 1 # Variance Inflation C1
                self.idx_b1_con = 2     # Start index for predictor coeffs C2 to Cn+1
                # SE index is after C0, C1, and all Cn coeffs
                self.idx_se_con = 2 + self.n_predictors
                param_count_con = self.idx_se_con + 1 # Total number of conditional parameters

                self.con_parms = np.full((12, param_count_con), np.nan)
                for i in range(12): # 12 months
                    param_line = get_line()
                    params_parsed = parse_fixed_width(param_line, 14)
                    num_to_assign = min(len(params_parsed), param_count_con)
                    self.con_parms[i, :num_to_assign] = params_parsed[:num_to_assign]


            # --- Read Predictand File Root (for Inv Normal ref / general info) ---
            # VB uses Line Input #, reads the whole line. Stripping seems safe here.
            self.ptand_file_root = get_line().strip()

            # --- Read Detrend Parameters (if applicable) ---
            if self.de_trend:
                self.de_trend_type = int(get_line()) # 1=linear, 2=power
                # Linear: B0 (intercept - not used?), B1 (gradient) -> 2 params read in VB loop
                # Power: a, b, min -> 3 params read in VB loop
                n_trend_params = 2 if self.de_trend_type == 1 else 3

                # Determine number of rows for BetaTrend based on SeasonCode
                # VB loops `For i = 1 To SeasonCode` when reading BetaTrend params.
                # SeasonCode=1 (Ann): Reads 1 set of params. BetaTrend(1, 1..n)
                # SeasonCode=4 (Seas): Reads 4 sets of params. BetaTrend(1..4, 1..n)
                # SeasonCode=12(Mon): Reads 12 sets of params. BetaTrend(1..12, 1..n)
                # The number of rows needed is simply the SeasonCode value.
                trend_rows = self.season_code
                if trend_rows not in [1, 4, 12]:
                    raise ValueError(f"Unsupported SeasonCode for Detrend: {self.season_code}")

                self.beta_trend = np.full((trend_rows, n_trend_params), np.nan)
                for i in range(trend_rows): # Read 'trend_rows' sets of parameters
                     # VB reads params one per line using Input #
                     p1 = float(get_line())
                     p2 = float(get_line())
                     self.beta_trend[i, 0] = p1 # Index 0 = VB BetaTrend(i, 1)
                     self.beta_trend[i, 1] = p2 # Index 1 = VB BetaTrend(i, 2)
                     if self.de_trend_type == 2: # Power function needs a third parameter
                        p3 = float(get_line())
                        self.beta_trend[i, 2] = p3 # Index 2 = VB BetaTrend(i, 3) (Minimum)


            # --- Post Load Actions ---
            par_dir = os.path.dirname(file_path)
            # If predictor_dir is not set or invalid, default to PAR file's directory
            if not self.predictor_dir or not os.path.isdir(self.predictor_dir):
                 self.predictor_dir = par_dir
                 self.dirText.setText(par_dir)
            self.viewPredictors() # Update list widget and check files existence

            QMessageBox.information(self, "PAR File Loaded",
                            f"Successfully loaded parameter file '{os.path.basename(file_path)}'.\nPlease verify Predictor Directory and Synthesis Settings.")

        except FileNotFoundError:
            QMessageBox.critical(self, "Error Loading PAR File", f"File not found: {file_path}")
            self.reset_all()
        except EOFError:
             QMessageBox.critical(self, "Error Loading PAR File", f"Unexpected end of file or missing data in:\n{file_path}\n{traceback.format_exc()}")
             self.reset_all()
        except ValueError as e:
             QMessageBox.critical(self, "Error Loading PAR File", f"Invalid data format or value in PAR file:\n{e}\nFile: {file_path}\n{traceback.format_exc()}")
             self.reset_all()
        except Exception as e:
            QMessageBox.critical(self, "Error Loading PAR File", f"Failed to parse PAR file:\n{str(e)}\n{traceback.format_exc()}")
            self.reset_all()


    def selectPARFile(self):
        """Opens a file dialog to select a PAR file."""
        start_dir = self.predictor_dir if os.path.isdir(self.predictor_dir) else self.default_dir
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Parameter File", start_dir, "PAR Files (*.par *.PAR);;All Files (*.*)")
        if file_name:
            self.loadPARFile(file_name)


    def selectOutputFile(self):
        """Opens a file dialog to select an output file."""
        default_name = ""
        if self.par_file_path and os.path.isdir(self.predictor_dir):
            base = os.path.splitext(os.path.basename(self.par_file_path))[0]
            default_name = os.path.join(self.predictor_dir, f"{base}.OUT")
        elif os.path.isdir(self.predictor_dir):
             default_name = os.path.join(self.predictor_dir, "output.OUT")
        else:
             default_name = os.path.join(self.default_dir, "output.OUT")

        file_name, _ = QFileDialog.getSaveFileName(self, "Save To .OUT File", default_name, "OUT Files (*.OUT);;All Files (*.*)")
        if file_name:
            # Ensure .OUT extension
            if not file_name.upper().endswith(".OUT"):
                 file_name += ".OUT"
            self.out_file_path = file_name
            self.outFileText.setText(os.path.basename(file_name))


    def viewPredictors(self):
        """Checks existence of predictor files listed in the PAR file and updates list widget."""
        self.predictorList.clear()

        if not self.par_file_path: return
        if not self.predictor_dir or not os.path.isdir(self.predictor_dir):
             QMessageBox.warning(self, "No Predictor Directory", "Please select a valid predictor directory.")
             return
        if not self.predictor_filenames:
             # PAR might be loaded but have 0 predictors
             if self.ptand_filename: # If only predictand exists
                 self.predictorList.addItem(f"Predictand: {self.ptand_filename} (No predictors)")
             # Else: PAR file seems empty or invalid, do nothing here.
             return

        missing_files = []
        found_files = []
        display_warning = False # Flag to show warning only once

        for i, filename in enumerate(self.predictor_filenames):
            prefix = "Predictand: " if i == 0 else f"Predictor {i}: "
            # Handle empty filename entries potentially read from PAR
            if not filename:
                self.predictorList.addItem(f"⚠️ {prefix}(Empty Filename in PAR!)")
                # Only warn if it's not the predictand (index 0) and n_predictors > 0
                if i > 0 and self.n_predictors > 0 : display_warning = True
                continue

            full_path = os.path.join(self.predictor_dir, filename)
            if not os.path.exists(full_path):
                missing_files.append(filename)
                self.predictorList.addItem(f"⚠️ {prefix}{filename} (Missing!)")
                display_warning = True # Need to show warning if any file is missing
            else:
                found_files.append(filename)
                self.predictorList.addItem(f"✅ {prefix}{filename}")

        if display_warning: # Show warning if any file was missing or filename empty
            missing_list = "\n- ".join(missing_files) if missing_files else "None"
            QMessageBox.warning(self, "File Verification Issues",
                            f"Issues found with files listed in PAR relative to directory:\n'{self.predictor_dir}'\n\nMissing Files:\n- {missing_list}\n\nPlease select the correct directory or check the PAR file contents.")


    def _prepare_inverse_normal(self):
        """Reads predictand data, sorts it, and calculates parameters for Inv Normal transform. Matches VB6 logic."""
        self.rank_data = []
        self.inv_norm_first_value_idx = -1
        self.inv_norm_n_split = 0
        self.inv_norm_limit = 0.0
        self.inv_norm_total_area = 0.0

        if not self.ptand_file_root:
             raise ValueError("Predictand file root path missing in PAR (required for Inv Normal).")

        # Determine the correct path to the predictand file used for ranking
        # VB stores the full path in PtandFileRoot. Let's prioritize that.
        # If it's not absolute, assume it's relative to the PAR file's directory.
        if os.path.isabs(self.ptand_file_root):
            ptand_path = self.ptand_file_root
        else:
            par_dir = os.path.dirname(self.par_file_path) if self.par_file_path else self.predictor_dir
            ptand_path = os.path.join(par_dir, self.ptand_file_root)

        if not os.path.exists(ptand_path):
             # Fallback: try relative to predictor dir (less likely based on VB logic)
             ptand_path_alt = os.path.join(self.predictor_dir, os.path.basename(self.ptand_file_root))
             if os.path.exists(ptand_path_alt):
                 ptand_path = ptand_path_alt
             else:
                 raise FileNotFoundError(f"Predictand file for Inv Normal not found.\nChecked PAR path: {ptand_path}\nChecked Predictor path: {ptand_path_alt}")

        try:
            # --- Read predictand data for the *calibration* period ---
            # VB Reads data between StartDate and CalFSDate + NDaysCal
            read_values = []
            line_count = 0
            cal_start_line = -1
            cal_end_line = -1

            # Determine line numbers for calibration period within the *full* record
            if self.start_date_par and self.cal_fs_date_par:
                 # Days from record start to calibration start
                 days_to_skip_cal = (self.cal_fs_date_par - self.start_date_par).days
                 if days_to_skip_cal < 0:
                      print(f"Warning: Calibration start date ({self.cal_fs_date_par}) is before record start date ({self.start_date_par}). Assuming skip count is 0.")
                      days_to_skip_cal = 0

                 cal_start_line = days_to_skip_cal # 0-based line index to start reading
                 cal_end_line = cal_start_line + self.n_days_cal_par # 0-based line index to stop reading (exclusive)
            else:
                 raise ValueError("Record Start Date or Calibration Fit Start Date not available from PAR for Inv Normal.")

            print(f"DEBUG InvNorm: Reading predictand '{os.path.basename(ptand_path)}' from line {cal_start_line+1} to {cal_end_line}.")

            with open(ptand_path, 'r') as f_ptand:
                for i, line in enumerate(f_ptand):
                    line_count = i
                    if cal_start_line <= i < cal_end_line:
                        try:
                            val = float(line.strip())
                            # VB code seems to include all valid numeric values in RankData,
                            # excluding the missing code.
                            if abs(val - self.global_missing_code) > 1e-9: # Exclude missing codes
                                 read_values.append(val)
                            # Else: simply skip missing values for ranking/translation
                        except ValueError:
                            # Treat lines that cannot be converted to float as missing/invalid
                            print(f"Warning: Skipping non-numeric value in predictand file {os.path.basename(ptand_path)} at line {i+1}: '{line.strip()}'")
                            pass # Skip non-numeric lines
                    elif i >= cal_end_line:
                        break # Stop reading after calibration period

            if line_count < cal_end_line -1 :
                 QMessageBox.warning(self, "Data Warning", f"Predictand file {os.path.basename(ptand_path)} for Inv Normal may have ended prematurely.\nExpected data until line {cal_end_line}, read {line_count+1} lines.")

            if not read_values:
                 raise ValueError(f"No valid numeric data (excluding missing code {self.global_missing_code}) found in predictand file {os.path.basename(ptand_path)} for the calibration period (lines {cal_start_line+1} to {cal_end_line}). Cannot perform Inverse Normal transform.")

            # --- Sort the valid observed data using Shell sort (matches VB6) ---
            self.rank_data = shell_sort(read_values) # Use VB6-like sort on valid data

            # --- Determine index of first value > threshold in sorted data ---
            # VB Code: `If RankData(i) > Thresh Then FirstValue = i; GoTo 50`. FirstValue is 1-based index.
            self.inv_norm_first_value_idx = -1
            for i, val in enumerate(self.rank_data):
                if val > self.thresh:
                    self.inv_norm_first_value_idx = i # Found first value > Thresh (0-based index)
                    break

            # Handle case where no value is strictly greater than threshold
            if self.inv_norm_first_value_idx == -1:
                 # VB logic implicitly proceeds if the loop finishes, potentially using FirstValue=N+1 (error).
                 # Let's check if any values are AT the threshold and use the first of those.
                 found_at_thresh = False
                 for i, val in enumerate(self.rank_data):
                      if abs(val - self.thresh) < 1e-9: # Check for equality within tolerance
                           self.inv_norm_first_value_idx = i
                           found_at_thresh = True
                           print(f"Warning: No data strictly > threshold ({self.thresh}) for Inv Normal. Using first value >= threshold at index {i}.")
                           break
                 if not found_at_thresh:
                      # No values are >= threshold. Inverse Normal cannot proceed.
                      raise ValueError(f"No data >= threshold ({self.thresh}) found in predictand file for calibration period. Cannot perform Inverse Normal transform.")

            # --- Calculate nSplit ---
            # VB Code: `nSplit = ReSampleNDays - FirstValue + 1`. ReSampleNDays is NDaysCal. FirstValue is 1-based index.
            # This VB calculation seems flawed. `nSplit` should be the *count* of values in RankData that are >= threshold.
            # Python: count = len(rank_data) - index_of_first_value_>=_thresh
            self.inv_norm_n_split = len(self.rank_data) - self.inv_norm_first_value_idx
            if self.inv_norm_n_split <= 0:
                 # This indicates an issue, possibly with threshold or data
                 raise ValueError(f"Inverse Normal nSplit calculation resulted in {self.inv_norm_n_split} (<= 0).\n"
                                  f"Total valid data points = {len(self.rank_data)}\n"
                                  f"Index of first value >= threshold ({self.thresh}) = {self.inv_norm_first_value_idx}\n"
                                  "Check threshold value and predictand data for calibration period.")

            print(f"DEBUG InvNorm: NRankData={len(self.rank_data)}, Thresh={self.thresh}, FirstValueIdx={self.inv_norm_first_value_idx}, FirstValue={self.rank_data[self.inv_norm_first_value_idx]:.4f}, nSplit={self.inv_norm_n_split}")


            # --- Locate lower bound Z-score (limit) ---
            # Calculation follows VB6 TRAPEZ/INTRAPEZ logic (search downwards from Z=0)
            # zStart is the probability in the lower tail excluded from the mapping.
            z_start = 1.0 / (self.inv_norm_n_split + 1.0)
            delta = 0.0001 # Step size used in VB search
            area = 0.5     # Start from center (area to the left of Z=0)
            fx = 0.0       # Starting Z-score (mean of standard normal)
            fx_old_pdf = normal_pdf(fx) # PDF at starting Z
            self.inv_norm_limit = np.nan # Initialize as NaN

            # Max iterations to prevent infinite loop, similar to VB loop structure
            search_success = False
            for _ in range(50000): # VB limit
                fx -= delta # Move Z-score down (leftwards)
                fx_new_pdf = normal_pdf(fx)
                # Area subtracted = integral from fx_new to fx (approximated by trapezoid)
                # This calculates area removed from the left tail as fx decreases
                area -= (delta * 0.5 * (fx_old_pdf + fx_new_pdf))
                # Stop when the area to the left of fx is <= z_start
                if area <= z_start:
                    # We found the Z-score (fx) corresponding to the lower tail probability z_start
                    self.inv_norm_limit = fx
                    search_success = True
                    break # Exit loop like VB GoTo 20
                fx_old_pdf = fx_new_pdf # Update PDF for next step

            if not search_success:
                # This mimics VB reaching the end of its loop without `GoTo 20`
                QMessageBox.warning(self, "Inv Normal Warning", f"Could not accurately find lower limit Z-score for P={z_start:.4f} within 50k iterations. Search stopped at Z={fx:.4f} with Area={area:.4f}. Using this Z as limit.")
                # Use the last calculated fx as the limit, although it might not be accurate.
                # Setting to -5.0 might be too arbitrary if the search just failed near the target.
                self.inv_norm_limit = fx # Use the value where the loop stopped
                if area > z_start: # Log if the area is still significantly off
                     print(f"WARN: Inv Norm limit search failed. Area {area:.6f} > zStart {z_start:.6f}. Limit set to {self.inv_norm_limit:.6f}")


            # Total area used for scaling = 1 - 2*z_start (area excluding both tails)
            # VB: `totalArea = (1 - (2 * zStart))`
            self.inv_norm_total_area = max(0.0, 1.0 - (2.0 * z_start)) # Ensure non-negative
            if self.inv_norm_total_area <= 1e-9: # Check for near-zero area
                 QMessageBox.warning(self,"Inv Normal Warning", f"Total Area for Inv Norm scaling is near zero ({self.inv_norm_total_area:.2e}). nSplit={self.inv_norm_n_split}. Check threshold/data.")
                 # Avoid division by zero later, set to small positive number
                 if self.inv_norm_total_area <= 0: self.inv_norm_total_area = 1e-9

            print(f"DEBUG InvNorm: zStart={z_start:.6f}, limit={self.inv_norm_limit:.6f}, totalArea={self.inv_norm_total_area:.6f}")


        except Exception as e:
            raise IOError(f"Error processing predictand file '{ptand_path}' for Inverse Normal Transform:\n{e}\n{traceback.format_exc()}")

    def _translator_inv_norm(self, passed_value):
        """Inverse Normal Transform: Converts Z-score back to data value using ranked data. Matches VB6 Translator logic."""
        # Ensure rank_data is valid and prepared
        if not self.rank_data or self.inv_norm_first_value_idx < 0 or self.inv_norm_first_value_idx >= len(self.rank_data) or self.inv_norm_n_split <= 0:
            print(f"ERROR: Translator called with invalid state: nRank={len(self.rank_data)}, firstVIdx={self.inv_norm_first_value_idx}, nSplit={self.inv_norm_n_split}")
            return self.global_missing_code # Or raise error

        # Handle Z-scores below the calculated lower limit
        # VB: `If (passedValue <= limit) Then Translator = RankData(FirstValue)`
        # Remember RankData in VB is 1-based, FirstValue is 1-based index.
        # RankData(FirstValue) corresponds to rank_data[inv_norm_first_value_idx] in Python.
        if passed_value <= self.inv_norm_limit:
            # Return the smallest value that was >= threshold
            return self.rank_data[self.inv_norm_first_value_idx]

        # Calculate area under normal curve from limit up to passed_value (Z-score)
        # Uses trapezoidal rule matching VB6 INTRAPEZ integration within Translator
        interval = (passed_value - self.inv_norm_limit) / 100.0 # 100 steps like VB
        # Ensure interval is not excessively small or zero if passed_value is very close to limit
        if abs(interval) < 1e-15: return self.rank_data[self.inv_norm_first_value_idx]

        area_from_limit = 0.0
        fx = self.inv_norm_limit
        try:
            fx_old_pdf = normal_pdf(fx)
        except Exception: fx_old_pdf = 0.0 # Handle potential errors in PDF calculation

        for _ in range(100): # VB loop 1 to 100
            fx += interval
            try:
                fx_new_pdf = normal_pdf(fx)
            except Exception: fx_new_pdf = 0.0
            # Trapezoid area for this small interval
            area_from_limit += (interval * 0.5 * (fx_old_pdf + fx_new_pdf))
            fx_old_pdf = fx_new_pdf

        # Scale the calculated area relative to the total usable area
        # Prevent area from exceeding totalArea (can happen due to numerical precision)
        # VB: `If area > totalArea Then area = totalArea`
        area_from_limit = min(area_from_limit, self.inv_norm_total_area)
        # Ensure area is non-negative
        area_from_limit = max(0.0, area_from_limit)

        # Determine the index offset within the valid portion of rank_data (values >= threshold)
        if self.inv_norm_total_area <= 1e-9: # Avoid division by zero
            index_offset_float = 0.0
        else:
            # VB: `locateValue = (FirstValue) + Int(area * nSplit / totalArea)`
            # `FirstValue` is 1-based index. `Int` truncates towards zero for positive numbers.
            # `area` here corresponds to `area_from_limit`.
            # Python equivalent: index = first_value_0_based + floor(area * nSplit / totalArea)
            index_offset_float = (area_from_limit / self.inv_norm_total_area) * self.inv_norm_n_split

        # Use math.floor to match VB's Int() truncation for non-negative values
        locate_index_offset = math.floor(index_offset_float)

        # Calculate final 0-based index by adding offset to the start index of the valid range
        locate_index = self.inv_norm_first_value_idx + locate_index_offset

        # Clamp the index to be within the valid range of rank_data (indices corresponding to values >= threshold)
        # VB: `If (locateValue >= (FirstValue + nSplit - 1)) Then locateValue = (FirstValue + nSplit - 1)`
        # Max VB 1-based index is `FirstValue + nSplit - 1`.
        # Max Python 0-based index is `self.inv_norm_first_value_idx + self.inv_norm_n_split - 1`
        max_allowable_index = self.inv_norm_first_value_idx + self.inv_norm_n_split - 1

        # Also ensure max_allowable_index doesn't exceed actual array bounds
        # (Can happen if nSplit was calculated slightly off or due to float precision)
        max_allowable_index = min(max_allowable_index, len(self.rank_data) - 1)

        # Apply clamping
        if locate_index >= max_allowable_index:
            locate_index = max_allowable_index

        # Lower bound check: ensure index is at least the first valid index
        # Should naturally be >= first_value if offset is non-negative, but added for safety.
        locate_index = max(locate_index, self.inv_norm_first_value_idx)

        # Final safety check on index before accessing array
        if self.inv_norm_first_value_idx <= locate_index < len(self.rank_data):
            return self.rank_data[locate_index]
        else:
            # This should ideally not happen if logic above is correct
            print(f"WARN: Translator index {locate_index} out of bounds [{self.inv_norm_first_value_idx}-{max_allowable_index}]. Z={passed_value}, Area={area_from_limit:.4f}, OffsetF={index_offset_float:.4f}, OffsetI={locate_index_offset}")
            # Fallback: return first or last valid value in the split range
            if passed_value <= self.inv_norm_limit:
                return self.rank_data[self.inv_norm_first_value_idx]
            else:
                 # If index calculation failed high, return the highest valid value
                 # Check if max_allowable_index itself is valid before returning
                 safe_max_idx = min(max_allowable_index, len(self.rank_data) - 1)
                 if safe_max_idx >= 0:
                      return self.rank_data[safe_max_idx]
                 else: # Should be impossible if rank_data exists
                      return self.global_missing_code


    def synthesizeData(self):
        """Performs the main data synthesis, replicating VB6 SynthesizeData logic."""
        self._cancel_synthesis = False # Reset cancel flag

        # --- Initial Validation ---
        if not self.par_file_path or not os.path.exists(self.par_file_path):
            QMessageBox.warning(self, "Missing Input", "Select a valid PAR file first.")
            return
        if self.uncon_parms is None:
             QMessageBox.warning(self, "PAR Not Loaded", "Load PAR file successfully before synthesizing.")
             return
        if not self.out_file_path:
            QMessageBox.warning(self, "Missing Input", "Select an output file path.")
            return
        if not self.predictor_dir or not os.path.isdir(self.predictor_dir):
            QMessageBox.warning(self, "Missing Input", "Select a valid predictor directory.")
            return
        # Verify predictor files one last time
        self.viewPredictors()
        if self.predictorList.count() > 0:
             if any("Missing" in self.predictorList.item(i).text() or "Empty Filename" in self.predictorList.item(i).text() for i in range(self.predictorList.count())):
                  QMessageBox.critical(self, "Missing/Invalid Files", "Cannot synthesize. Required predictor files are missing or filenames invalid. Check paths and PAR file.")
                  return

        try:
            # Validate and get UI settings
            ensemble_size = int(self.eSize.text())
            if not 1 <= ensemble_size <= 100: # VB limit seems to be 100 in arrays
                QMessageBox.warning(self, "Invalid Input", "Ensemble size must be between 1 and 100.")
                return

            synthesis_start_date = self._parse_date(self.fStartText.text())

            synthesis_length = int(self.fLengthText.text())
            if synthesis_length < 1:
                QMessageBox.warning(self, "Invalid Input", "Synthesis length must be at least 1 day.")
                return

            # Date sanity checks (optional but good practice)
            if self.start_date_par and synthesis_start_date < self.start_date_par:
                 # VB doesn't explicitly warn here, but proceeds. We can add a warning.
                 print(f"Warning: Synthesis start date ({synthesis_start_date}) is before the Record start date ({self.start_date_par}) defined in the PAR file.")
            # Further checks: synthesis end date vs record end date?

        except ValueError as e:
            QMessageBox.critical(self, "Invalid Input", f"Error in synthesis settings:\n{e}\n\nPlease check dates (dd/mm/yyyy or mm/dd/yyyy) and numbers.")
            return
        except Exception as e:
             QMessageBox.critical(self, "Input Error", f"Error processing inputs: {e}")
             return

        # --- Setup ---
        sim_file_path = os.path.splitext(self.out_file_path)[0] + ".SIM"

        # --- Random Seed ---
        # *** CRITICAL FOR REPLICATION ATTEMPTS ***
        # NOTE: Python's random number generator is DIFFERENT from VB6's.
        # Using seed(1) makes Python's sequence repeatable, but it WILL NOT
        # match the sequence generated by VB6 Rnd -1; Randomize 1.
        # Exact numerical replication requires implementing the VB6 PRNG.
        if not self.use_random_seed: # If False, use fixed seed (like VB6 Rnd -1; Randomize 1)
             random.seed(1)
             # np.random.seed(1) # Only needed if using numpy's random functions
             print("DEBUG: Using fixed Python random seed (1) for repeatability. NOTE: Sequence differs from VB6.")
        else:
             # If True, let Python seed from system sources (non-repeatable)
             random.seed()
             # np.random.seed()
             print("DEBUG: Using system random seed (non-repeatable).")


        # --- Progress Dialog ---
        # Estimate total steps: Prep + Skip + Main Loop + SIM write
        init_steps = 3 # File open, InvNorm prep, Detrend init
        skip_days = max(0, (synthesis_start_date - self.start_date_par).days if self.start_date_par else 0)
        total_prog_steps = init_steps + skip_days + synthesis_length + 1
        progress = QProgressDialog("Initializing Synthesis...", "Cancel", 0, total_prog_steps, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setWindowTitle("Processing")
        progress.setValue(0)
        #progress.show() # Show later inside the try block
        QCoreApplication.processEvents() # Process events before potentially long operations


        # --- Main Logic ---
        predictor_file_handles = []
        out_file_handle = None
        current_progress = 0

        try:
            progress.show() # Show progress bar now
            QCoreApplication.processEvents()

            # --- Prepare Inverse Normal (if needed) ---
            if self.local_model_trans == 4:
                 progress.setLabelText("Preparing Inverse Normal data...")
                 progress.setValue(current_progress); current_progress += 1
                 QCoreApplication.processEvents()
                 if progress.wasCanceled(): raise InterruptedError("Cancelled")
                 self._prepare_inverse_normal()

            # --- Open Predictor Files ---
            progress.setLabelText("Opening predictor files...")
            progress.setValue(current_progress); current_progress += 1
            QCoreApplication.processEvents()
            if progress.wasCanceled(): raise InterruptedError("Cancelled")

            # Open predictor files (skip predictand at index 0)
            predictor_files_to_open = self.predictor_filenames[1:]
            if len(predictor_files_to_open) != self.n_predictors:
                 # Allow if the list has placeholders for empty filenames read from PAR
                 actual_files_in_list = len([f for f in predictor_files_to_open if f])
                 if actual_files_in_list == self.n_predictors:
                     print(f"Warning: Number of non-empty predictor filenames ({actual_files_in_list}) matches NPredictors ({self.n_predictors}).")
                 elif len(self.predictor_filenames) == self.n_predictors + 1:
                     print(f"Warning: Total filenames in list ({len(self.predictor_filenames)-1}) matches NPredictors ({self.n_predictors}), but some might be empty/invalid.")
                 else:
                     # This is a more critical mismatch
                     raise ValueError(f"Mismatch: Expected {self.n_predictors} predictors, found {len(predictor_files_to_open)} filename entries in list after predictand.")

            # Use a loop corresponding to n_predictors to open files based on list index
            for i in range(self.n_predictors):
                predictor_idx_in_list = i + 1 # Index in self.predictor_filenames
                filename = self.predictor_filenames[predictor_idx_in_list] if predictor_idx_in_list < len(self.predictor_filenames) else None

                if not filename: # Skip opening if filename was empty in PAR
                     predictor_file_handles.append(None) # Keep placeholder for indexing
                     print(f"Warning: Skipping empty predictor filename entry for predictor {i+1}.")
                     continue
                filepath = os.path.join(self.predictor_dir, filename)
                if not os.path.exists(filepath):
                     # Raise error immediately if a required file is missing
                     raise FileNotFoundError(f"Predictor file not found: {filepath}")
                try:
                    predictor_file_handles.append(open(filepath, 'r'))
                except Exception as e:
                    raise IOError(f"Error opening predictor file {filepath}: {e}")

            # --- Open Output File ---
            try:
                out_file_handle = open(self.out_file_path, 'w')
            except Exception as e:
                raise IOError(f"Error opening output file {self.out_file_path} for writing: {e}")

            # --- Initialize Detrending Variables ---
            days_used_linear = {} # Tracks offset from CalFSDate for linear trend (per period)
            days_used_power = {}  # Tracks offset from StartDate for power trend baseline (per period)
            cal_fs_date_baseline_days = {} # Days counted per period up to CalFSDate (relative to StartDate)
            fs_date_baseline_days = {}     # Days counted per period up to FSDate (relative to StartDate) - used for power mainly
            trend_rows_beta = 0 # Number of rows in beta_trend array (1, 4, or 12)

            if self.de_trend:
                progress.setLabelText("Initializing detrend variables...")
                progress.setValue(current_progress); current_progress += 1
                QCoreApplication.processEvents()
                if progress.wasCanceled(): raise InterruptedError("Cancelled")

                if self.beta_trend is None: raise ValueError("Detrending enabled but BetaTrend parameters not loaded.")
                trend_rows_beta = self.beta_trend.shape[0] # Get actual number of rows loaded (should match season_code)
                if trend_rows_beta != self.season_code:
                    print(f"Warning: Mismatch between SeasonCode ({self.season_code}) and loaded BetaTrend rows ({trend_rows_beta}). Using {trend_rows_beta} rows.")
                    # Proceed with the number of rows loaded, but be aware of potential issues.

                # Calculate baseline day counts up to Calibration Fit Start Date (CalFSDate) relative to StartDate
                current_d_cal = self.start_date_par
                days_diff_cal = 0
                if self.start_date_par and self.cal_fs_date_par:
                     days_diff_cal = max(0, (self.cal_fs_date_par - self.start_date_par).days)

                # Determine period index based on SeasonCode and track counts
                # Initialize baseline counts to 0 for all possible periods
                for period_idx in range(trend_rows_beta):
                    cal_fs_date_baseline_days[period_idx] = 0

                for _ in range(days_diff_cal):
                    month = current_d_cal.month
                    period_idx = -1
                    if self.season_code == 1: period_idx = 0 # Annual index is always 0
                    elif self.season_code == 4: period_idx = get_season(month) # 0-3 index
                    elif self.season_code == 12: period_idx = month - 1 # 0-11 index

                    # Increment count only if the period index is valid for the loaded BetaTrend array
                    if 0 <= period_idx < trend_rows_beta:
                         cal_fs_date_baseline_days[period_idx] = cal_fs_date_baseline_days.get(period_idx, 0) + 1
                    else:
                         # This might happen if season_code != trend_rows_beta
                         print(f"Warning: Skipping detrend baseline count for date {current_d_cal}, invalid period index {period_idx} for trend rows {trend_rows_beta}")

                    # Increment date using standard calendar logic
                    try:
                        current_d_cal += datetime.timedelta(days=1)
                    except OverflowError:
                        raise ValueError("Date overflow during detrend baseline calculation. Check dates.")

            # --- Skip Initial Data in Predictor Files ---
            progress.setLabelText("Skipping initial predictor data...")
            progress.setValue(current_progress); # Keep progress value here until loop starts
            QCoreApplication.processEvents()

            days_to_skip = 0
            if self.start_date_par and synthesis_start_date > self.start_date_par:
                days_to_skip = max(0, (synthesis_start_date - self.start_date_par).days)

            current_d_skip = self.start_date_par if self.start_date_par else None

            # Skip lines in predictor files AND update detrend baselines up to synthesis_start_date
            if days_to_skip > 0 and current_d_skip is None:
                 raise ValueError("Cannot skip initial data: Record Start Date (start_date_par) is missing.")

            # Initialize Power function baseline and FSDate baseline counts
            for period_idx in range(trend_rows_beta if self.de_trend else 0):
                days_used_power[period_idx] = 0
                fs_date_baseline_days[period_idx] = 0


            for day_skip_idx in range(days_to_skip):
                 if progress.wasCanceled(): raise InterruptedError("Cancelled")
                 progress.setValue(current_progress + day_skip_idx + 1) # Update progress during skip
                 if day_skip_idx % 100 == 0: QCoreApplication.processEvents() # Process events periodically

                 # Read and discard one line from each *opened* predictor file
                 for i, f_handle in enumerate(predictor_file_handles):
                      if f_handle is not None: # Skip None placeholders for empty filenames
                           line = f_handle.readline()
                           if not line:
                                # Find the actual filename for the error message
                                filename_for_error = f"(Predictor {i+1})" # Default if list access fails
                                if (i+1) < len(self.predictor_filenames):
                                    filename_for_error = self.predictor_filenames[i+1] or f"(Predictor {i+1} - empty name)"
                                raise EOFError(f"Predictor file '{filename_for_error}' ended prematurely during initial skip at day {day_skip_idx+1} (Date: {current_d_skip.strftime('%d/%m/%Y') if current_d_skip else 'N/A'}).")

                 # Update detrending day counts for the skipped day (relative to StartDate)
                 if self.de_trend and current_d_skip:
                      month = current_d_skip.month
                      period_idx = -1
                      if self.season_code == 1: period_idx = 0
                      elif self.season_code == 4: period_idx = get_season(month)
                      elif self.season_code == 12: period_idx = month - 1

                      if 0 <= period_idx < trend_rows_beta:
                          # Track days from StartDate up to current skipped day (FSDate baseline)
                          fs_date_baseline_days[period_idx] = fs_date_baseline_days.get(period_idx, 0) + 1
                          # Initialize/Update DaysUsedPower (offset from StartDate)
                          days_used_power[period_idx] = fs_date_baseline_days[period_idx]
                      # else: warning already printed potentially during cal baseline calc

                 # Increment skip date
                 if current_d_skip:
                      try:
                          current_d_skip += datetime.timedelta(days=1)
                      except OverflowError:
                          raise ValueError("Date overflow during initial data skipping. Check dates.")

            # Update progress value after skipping is done
            current_progress += days_to_skip

            # --- Initialize Simulation State ---
            current_date = synthesis_start_date
            start_month_idx = synthesis_start_date.month - 1 # 0-11

            # Initialize AR seed using intercept of the first month *of synthesis*
            # VB: AutoRegressionSeed(EnsembleWorkingOn) = UnconParms(mm, 1) before the main loop
            initial_intercept = 0.0
            if self.uncon_parms is not None and 0 <= start_month_idx < 12 and self.idx_b0_uncon != -1:
                 # Check if the intercept value is valid (not NaN)
                 intercept_val = self.uncon_parms[start_month_idx, self.idx_b0_uncon]
                 if not np.isnan(intercept_val):
                      initial_intercept = intercept_val
                 else:
                      print(f"Warning: Missing Uncon Intercept (NaN) for starting month {start_month_idx+1}. Initial AR seed set to 0.")
            else:
                 print(f"Warning: Cannot get Uncon Intercept for starting month {start_month_idx+1}. Initial AR seed set to 0.")

            # AR seed array for the ensemble (initialized for day 0)
            auto_regression_seed = np.full(ensemble_size, initial_intercept)

            # Initialize linear detrend counter (offset relative to CalFSDate)
            # days_used_linear starts at the difference between synthesis start count and cal start count
            if self.de_trend:
                for i in range(trend_rows_beta):
                     # Get baseline counts for the period index i (default to 0 if missing)
                     fs_base = fs_date_baseline_days.get(i, 0)
                     cal_base = cal_fs_date_baseline_days.get(i, 0)
                     # Linear trend starts from the difference at the beginning of synthesis
                     days_used_linear[i] = fs_base - cal_base
                     # days_used_power is already initialized to fs_base during skip phase

            # --- Main Simulation Loop ---
            progress.setLabelText("Running synthesis...")
            progress.setMaximum(total_prog_steps) # Ensure max is correct
            progress.setValue(current_progress)
            QCoreApplication.processEvents()

            # Array to hold the prediction for each ensemble member for the current day
            daily_prediction = np.full(ensemble_size, self.global_missing_code)
            # Array to hold wet/dry status (True/False) for conditional models
            is_wet_status = np.zeros(ensemble_size, dtype=bool) if self.rain_yes else None

            # Cache parameters for the current month/period to avoid repeated lookups/checks
            cached_month_idx = -1
            cached_period_idx = -1 # For detrending
            cached_uncon_params = None
            cached_con_params = None
            cached_lambda_params = None
            cached_trend_params = None


            for day_counter in range(synthesis_length):
                if progress.wasCanceled(): raise InterruptedError("Cancelled")
                # Update progress less frequently for performance
                if day_counter % 50 == 0 or day_counter == synthesis_length - 1:
                    progress.setValue(current_progress + day_counter + 1)
                    QCoreApplication.processEvents()

                current_month_idx = current_date.month - 1 # 0-11 index
                current_period_idx = -1 # For detrending period

                # --- Update Parameters and Detrend Period Index if Month Changed or First Day ---
                if current_month_idx != cached_month_idx or day_counter == 0:
                    cached_month_idx = current_month_idx
                    cached_uncon_params = None
                    cached_con_params = None
                    cached_lambda_params = None

                    # Get Unconditional parameters for the current month
                    if self.uncon_parms is not None and 0 <= current_month_idx < 12:
                        params = self.uncon_parms[current_month_idx, :]
                        # Basic check for essential params (Intercept, SE)
                        if self.idx_b0_uncon != -1 and not np.isnan(params[self.idx_b0_uncon]) and \
                           self.idx_se_uncon != -1 and not np.isnan(params[self.idx_se_uncon]):
                             cached_uncon_params = params
                        else:
                            if day_counter == 0 : print(f"WARN: Missing essential Uncon params (B0 or SE) for month {current_month_idx+1}.")

                    # Get Conditional parameters for the current month
                    if self.rain_yes:
                        if self.con_parms is not None and 0 <= current_month_idx < 12:
                             params = self.con_parms[current_month_idx, :]
                             # Basic check for essential params (Intercept, VarInf, SE)
                             if self.idx_b0_con != -1 and not np.isnan(params[self.idx_b0_con]) and \
                                self.idx_varinf_con != -1 and not np.isnan(params[self.idx_varinf_con]) and \
                                self.idx_se_con != -1 and not np.isnan(params[self.idx_se_con]):
                                  cached_con_params = params
                             else:
                                  if day_counter == 0 : print(f"WARN: Missing essential Con params (C0, VarInf, or SE) for month {current_month_idx+1}.")

                    # Get BoxCox parameters (Lambda, RightShift) stored in lamda_array
                    if self.local_model_trans == 5:
                        if self.lamda_array is not None and 0 <= current_month_idx < 12:
                             params = self.lamda_array[current_month_idx, :]
                             if not np.isnan(params).any():
                                  cached_lambda_params = params
                             else:
                                  if day_counter == 0 : print(f"WARN: Missing BoxCox params (Lambda or Shift) for month {current_month_idx+1}.")


                # --- Determine Detrending Period and Update Parameters/Counts ---
                if self.de_trend:
                    month = current_date.month
                    new_period_idx = -1
                    if self.season_code == 1: new_period_idx = 0
                    elif self.season_code == 4: new_period_idx = get_season(month) # 0-3
                    elif self.season_code == 12: new_period_idx = month - 1 # 0-11

                    # Check if period is valid based on loaded BetaTrend array size
                    if not (0 <= new_period_idx < trend_rows_beta):
                         if day_counter == 0 or new_period_idx != cached_period_idx: # Warn only once per invalid period change
                              print(f"WARN: Invalid detrend period index {new_period_idx} for date {current_date.strftime('%d/%m/%Y')}. Detrending skipped for this period.")
                         current_period_idx = -1 # Mark as invalid period
                         cached_trend_params = None # Clear cached trend params
                    else:
                         current_period_idx = new_period_idx
                         # Update trend params cache if period changed or first day
                         if current_period_idx != cached_period_idx or day_counter == 0:
                              cached_period_idx = current_period_idx
                              cached_trend_params = None
                              if self.beta_trend is not None and not np.isnan(self.beta_trend[cached_period_idx, :]).any():
                                  cached_trend_params = self.beta_trend[cached_period_idx, :]
                              else:
                                  if day_counter == 0: print(f"WARN: Missing detrend parameters for period {cached_period_idx+1}")

                         # Increment day counters for the *current valid* period
                         days_used_linear[current_period_idx] = days_used_linear.get(current_period_idx, 0) + 1
                         days_used_power[current_period_idx] = days_used_power.get(current_period_idx, 0) + 1


                # --- Read Predictor Data for the current day ---
                predictor_data = np.full(self.n_predictors, self.global_missing_code)
                missing_flag = False
                # Ensure predictor_file_handles has the expected number of entries (NPredictors)
                if len(predictor_file_handles) != self.n_predictors:
                     # This indicates an issue during file opening phase
                     raise RuntimeError(f"Internal Error: Expected {self.n_predictors} predictor file handles, found {len(predictor_file_handles)}.")

                for i, f_handle in enumerate(predictor_file_handles):
                    if f_handle is None: # Skip None placeholders (empty filename in PAR)
                         # If predictor i+1 data is needed (i.e., its coefficient is not NaN), mark as missing
                         # Simple check: mark missing if any handle is None
                         missing_flag = True
                         # predictor_data[i] remains global_missing_code
                         continue

                    line = f_handle.readline()
                    if not line:
                         filename_for_error = f"(Predictor {i+1})"
                         if (i+1) < len(self.predictor_filenames): filename_for_error = self.predictor_filenames[i+1] or f"(Predictor {i+1} - empty name)"
                         raise EOFError(f"Predictor '{filename_for_error}' ended unexpectedly at day {day_counter+1} (Date: {current_date.strftime('%d/%m/%Y')}). Expected {synthesis_length} days.")
                    try:
                        val = float(line.strip())
                        predictor_data[i] = val
                        # Check against global missing code
                        if abs(val - self.global_missing_code) < 1e-9:
                            missing_flag = True
                    except ValueError:
                        # Treat lines that cannot be converted to float as missing
                        print(f"Warning: Non-numeric value read from predictor {i+1} on day {day_counter+1}. Treating as missing. Line: '{line.strip()}'")
                        predictor_data[i] = self.global_missing_code
                        missing_flag = True


                # --- Downscaling Algorithm ---
                daily_prediction.fill(self.global_missing_code) # Reset predictions for the day

                # Proceed only if no predictor data was missing for this day
                if not missing_flag:
                    # Use cached parameters for the month/period
                    uncon_params_month = cached_uncon_params
                    con_params_month = cached_con_params
                    lambda_params_month = cached_lambda_params
                    trend_params = cached_trend_params if current_period_idx != -1 else None # Use trend params only if period is valid

                    # === Ensemble Loop 1: Unconditional Pred / Wet-Dry Probability ===
                    if uncon_params_month is None:
                        # Cannot proceed if unconditional parameters are missing for the month
                        missing_flag = True # Mark day as missing
                        if day_counter == 0 or current_month_idx != (current_date - datetime.timedelta(days=1)).month - 1:
                             print(f"ERROR: Missing essential unconditional parameters for month {current_month_idx+1}. Skipping day {day_counter+1}.")
                    else:
                        # Check if required predictor coefficients are valid
                        coeffs_ok = True
                        if self.n_predictors > 0 and self.idx_b1_uncon != -1:
                             uncon_coeffs = uncon_params_month[self.idx_b1_uncon : self.idx_se_uncon]
                             if len(uncon_coeffs) != self.n_predictors or np.isnan(uncon_coeffs).any():
                                  # Handle case where some coeffs might be NaN - numpy handles this in dot product? Check nansum.
                                  # If length mismatch, it's a definite error.
                                  if len(uncon_coeffs) != self.n_predictors:
                                       print(f"ERROR: Uncon coeff count ({len(uncon_coeffs)}) != NPredictors ({self.n_predictors}) for month {current_month_idx+1}. Skipping.")
                                       coeffs_ok = False; missing_flag = True
                                  # Allow NaN coeffs if nansum is used below
                        # Check AR coeff if needed
                        if self.auto_regression and (self.idx_ar_uncon == -1 or np.isnan(uncon_params_month[self.idx_ar_uncon])):
                             print(f"WARN: Missing AR coefficient for month {current_month_idx+1} when AutoRegression is True. AR term will be zero.")
                             # Can proceed, AR term will just be zero.

                        if coeffs_ok:
                            for ens_idx in range(ensemble_size):
                                # --- Calculate Unconditional Base Prediction (B0 + B1*X1 + ...) ---
                                pred_uncon_base = uncon_params_month[self.idx_b0_uncon]
                                if self.n_predictors > 0 and self.idx_b1_uncon != -1:
                                    uncon_coeffs = uncon_params_month[self.idx_b1_uncon : self.idx_se_uncon]
                                    # Use nansum to handle potential NaN coefficients gracefully (treats NaN coeff * value as 0)
                                    pred_uncon_base += np.nansum(uncon_coeffs * predictor_data)

                                # --- Autoregression Term ---
                                ar_term = 0.0
                                if self.auto_regression and self.idx_ar_uncon != -1:
                                    ar_coeff = uncon_params_month[self.idx_ar_uncon]
                                    # Check if seed is valid (not missing code) and coeff is valid (not NaN)
                                    if abs(auto_regression_seed[ens_idx] - self.global_missing_code) > 1e-9 and not np.isnan(ar_coeff):
                                        ar_term = auto_regression_seed[ens_idx] * ar_coeff
                                pred_uncon_base += ar_term

                                # --- Residual Term (Stochasticity) - Matches VB6 Rnd loop ---
                                std_err_uncon = uncon_params_month[self.idx_se_uncon]
                                residual = 0.0
                                # Check if StdErr is valid (not NaN and > 0) and variance inflation N > 0
                                if not np.isnan(std_err_uncon) and std_err_uncon > 1e-9 and self.prec_n > 0:
                                    # Sum N uniform random numbers [0, 1) using Python's seeded generator
                                    sum_rnd = sum(random.random() for _ in range(self.prec_n))
                                    # Center (subtract mean N/2) and scale by StdErr
                                    # VB: residual = (residual - (PrecN / 2)) * UnconParms(mm, NParameters - 1)
                                    residual = (sum_rnd - (self.prec_n / 2.0)) * std_err_uncon
                                # --- End VB6 Residual ---

                                # --- Determine Final Value OR Wet/Dry Status ---
                                if not self.rain_yes: # Unconditional Process
                                    # Add residual to base prediction
                                    final_pred_value = pred_uncon_base + residual

                                    # Apply Detrending to the combined value (Base + AR + Residual)
                                    # VB applies trend *before* the residual is added in the final value calculation?
                                    # VB Unconditional: Prediction = Base + AR -> Prediction = Prediction + residual -> If DeTrend -> Prediction = Prediction + Trend
                                    # Let's re-evaluate VB Unconditional logic:
                                    # 1. Prediction = B0 + Sum(Bk*Xk)
                                    # 2. If AR: Prediction = Prediction + Seed*ARCoeff
                                    # 3. residual = CalcResidual(SE_Uncon)
                                    # 4. Prediction = Prediction + residual
                                    # 5. If DeTrend: Prediction = Prediction + CalcTrend(...)
                                    # 6. If AllowNeg=False: Prediction = Max(0, Prediction)
                                    # 7. Seed = Prediction
                                    # OK, Python needs to match this order. Residual first, then Detrend.

                                    # Recalculate final_pred_value with correct order:
                                    final_pred_value = pred_uncon_base + residual # Base + AR + Residual

                                    if self.de_trend and trend_params is not None: # Check valid period and params
                                        trend_adjustment = 0.0
                                        try:
                                            current_days_linear = days_used_linear.get(current_period_idx, 0)
                                            current_days_power = days_used_power.get(current_period_idx, 0)

                                            if self.de_trend_type == 1: # Linear: Trend = B1 * DaysOffsetFromCalibStart
                                                # VB uses BetaTrend(PeriodValue, 2) which is gradient -> trend_params[1]
                                                trend_adjustment = trend_params[1] * current_days_linear
                                            else: # Power: Trend = a * (DaysFromRecordStart ^ b) - Abs(Min) - 0.001
                                                # VB uses BetaTrend(PeriodValue, 1)=a, BetaTrend(PeriodValue, 2)=b, BetaTrend(PeriodValue, 3)=Min
                                                power_base = float(current_days_power) # Ensure float for power calc
                                                if power_base < 0: power_base = 0 # Avoid issues with negative base if possible? VB doesn't check.
                                                # Check for NaN params before calculation
                                                if not np.isnan(trend_params[0]) and not np.isnan(trend_params[1]) and not np.isnan(trend_params[2]):
                                                    trend_adjustment = (trend_params[0] * (power_base ** trend_params[1]))
                                                    trend_adjustment -= abs(trend_params[2]) # Use abs() like VB
                                                    trend_adjustment -= 0.001 # VB specific adjustment
                                                else:
                                                    print(f"WARN: NaN in Power trend params for period {current_period_idx+1}. Trend set to 0.")

                                            final_pred_value += trend_adjustment
                                        except (OverflowError, ValueError) as trend_err:
                                             print(f"WARN: Uncon Detrend calculation error day {day_counter+1}, ens {ens_idx+1}, period {current_period_idx+1}: {trend_err}. Trend skipped.")
                                             # Keep final_pred_value without trend adjustment

                                    # Apply constraints (non-negative) if specified
                                    # VB: `If ((Not (AllowNeg)) And (Prediction(EnsembleWorkingOn) < 0)) Then Prediction(EnsembleWorkingOn) = 0`
                                    if not self.allow_neg and final_pred_value < 0:
                                         final_pred_value = 0.0

                                    # Store final unconditional prediction
                                    daily_prediction[ens_idx] = final_pred_value

                                    # Update AR seed with the *final* value for next day
                                    # VB: AutoRegressionSeed(EnsembleWorkingOn) = Prediction(EnsembleWorkingOn)
                                    auto_regression_seed[ens_idx] = final_pred_value

                                else: # Conditional process: Use unconditional part to determine Wet/Dry
                                    # 'pred_uncon_base' holds the value (B0 + Bk*Xk + AR) which represents wet probability P(W)
                                    # The unconditional residual is NOT added here.
                                    prob_wet = pred_uncon_base
                                    is_wet = False
                                    # VB uses Rnd for stochastic check, Python uses random.random()
                                    if self.conditional_selection == 1: # Stochastic (VB: Rnd <= Pred)
                                        # *** Uses Python's seeded random.random() ***
                                        is_wet = (random.random() <= prob_wet)
                                    else: # Fixed Threshold (VB: Pred >= Thresh)
                                        is_wet = (prob_wet >= self.conditional_thresh)

                                    is_wet_status[ens_idx] = is_wet

                                    # Update AR seed based on wet/dry status (0 or 1) for next day
                                    # VB: `AutoRegressionSeed(EnsembleWorkingOn) = Prediction(EnsembleWorkingOn)` where Prediction is 0 or 1 after the check
                                    auto_regression_seed[ens_idx] = 1.0 if is_wet else 0.0

                                    # Store 0 for dry days now, amount calculated in next loop
                                    if not is_wet:
                                         daily_prediction[ens_idx] = 0.0

                        # End of ensemble loop 1


                    # === Ensemble Loop 2: Calculate Amount for Wet Days (if Conditional) ===
                    # Only proceed if conditional process, not missing, and conditional params are valid
                    if self.rain_yes and not missing_flag:
                         if con_params_month is None:
                             missing_flag = True # Mark day as missing
                             if day_counter == 0 or current_month_idx != (current_date - datetime.timedelta(days=1)).month - 1:
                                  print(f"ERROR: Missing essential conditional parameters for month {current_month_idx+1}. Cannot calculate amount. Skipping day {day_counter+1}.")
                         else:
                             # Check conditional coefficients
                             coeffs_con_ok = True
                             if self.n_predictors > 0 and self.idx_b1_con != -1:
                                  con_coeffs = con_params_month[self.idx_b1_con : self.idx_se_con]
                                  if len(con_coeffs) != self.n_predictors:
                                       print(f"ERROR: Con coeff count ({len(con_coeffs)}) != NPredictors ({self.n_predictors}) for month {current_month_idx+1}. Skipping amount calc.")
                                       coeffs_con_ok = False; missing_flag = True
                                  # Allow NaN coeffs if using nansum

                             if coeffs_con_ok:
                                 for ens_idx in range(ensemble_size):
                                     # Only calculate amount if day was marked wet in Loop 1
                                     if is_wet_status[ens_idx]:
                                         # --- Calculate Conditional Amount Base (C0 + C2*X2 + ...) ---
                                         # VB: Prediction(EnsembleWorkingOn) = ConParms(mm, 1) + Sum(ConParms(mm, k + 2) * PredictorData(k))
                                         pred_amount_base = con_params_month[self.idx_b0_con] # C0
                                         if self.n_predictors > 0 and self.idx_b1_con != -1:
                                             con_coeffs = con_params_month[self.idx_b1_con : self.idx_se_con] # C2..Cn+1
                                             # Use nansum to handle potential NaN coefficients
                                             pred_amount_base += np.nansum(con_coeffs * predictor_data)

                                         # --- Apply Detrending to the Base Amount ---
                                         # VB applies trend BEFORE residual & transform steps in conditional mode
                                         # VB: If DeTrend Then Prediction = Prediction + Trend -> modifies base before residual/transform
                                         if self.de_trend and trend_params is not None: # Check valid period and params
                                             trend_adjustment_cond = 0.0
                                             try:
                                                 current_days_linear = days_used_linear.get(current_period_idx, 0)
                                                 current_days_power = days_used_power.get(current_period_idx, 0)
                                                 if self.de_trend_type == 1: # Linear Trend = B1 * DaysOffsetFromCalibStart
                                                     trend_adjustment_cond = trend_params[1] * current_days_linear
                                                 else: # Power Trend = a * (DaysFromRecordStart ^ b) - Abs(Min) - 0.001
                                                     power_base = float(current_days_power)
                                                     if power_base < 0: power_base = 0
                                                     if not np.isnan(trend_params[0]) and not np.isnan(trend_params[1]) and not np.isnan(trend_params[2]):
                                                          trend_adjustment_cond = (trend_params[0] * (power_base ** trend_params[1]))
                                                          trend_adjustment_cond -= abs(trend_params[2]) # Use abs() like VB
                                                          trend_adjustment_cond -= 0.001
                                                     else: print(f"WARN: NaN in Power trend params for period {current_period_idx+1}. Trend set to 0.")

                                                 # Add trend adjustment to the base prediction
                                                 pred_amount_base += trend_adjustment_cond
                                             except (OverflowError, ValueError) as trend_err:
                                                  print(f"WARN: Cond Detrend calculation error day {day_counter+1}, ens {ens_idx+1}, period {current_period_idx+1}: {trend_err}. Trend skipped.")
                                                  # pred_amount_base remains unchanged

                                         # --- Calculate Conditional Residual ---
                                         std_err_con = con_params_month[self.idx_se_con]
                                         residual_amount = 0.0
                                         if not np.isnan(std_err_con) and std_err_con > 1e-9 and self.prec_n > 0:
                                             # *** Uses Python's seeded random.random() ***
                                             sum_rnd_con = sum(random.random() for _ in range(self.prec_n))
                                             # VB: residual = (residual - (PrecN / 2)) * ConParms(mm, NParameters) -> NParameters here is SE index
                                             residual_amount = (sum_rnd_con - (self.prec_n / 2.0)) * std_err_con

                                         # --- Apply Variance Inflation, Transformation, Bias Correction ---
                                         # This part depends heavily on LocalModelTrans - follow VB logic precisely for each case
                                         var_inf = con_params_month[self.idx_varinf_con] # VB: ConParms(mm, 2)
                                         final_pred_amount = self.global_missing_code # Default to missing

                                         try:
                                             # Base value for transformations (potentially includes trend)
                                             base_plus_trend = pred_amount_base

                                             if self.local_model_trans == 1: # None
                                                 # VB: Prediction = BiasCorrection * (ConParms(mm, 2) * (Prediction) + residual)
                                                 # Here Prediction holds base+trend
                                                 val_to_bias = (var_inf * base_plus_trend) + residual_amount
                                                 final_pred_amount = self.bias_correction * val_to_bias

                                             elif self.local_model_trans == 2: # Fourth Root -> Power 4
                                                 # VB: Prediction = BiasCorrection * ((ConParms(mm, 2) * (Prediction + residual)) ^ 4)
                                                 # Here Prediction holds base+trend
                                                 val_to_inflate = base_plus_trend + residual_amount
                                                 val_to_power = var_inf * val_to_inflate
                                                 # Ensure base for power is non-negative
                                                 base_for_pow = max(0.0, val_to_power)
                                                 transformed_val = math.pow(base_for_pow, 4.0)
                                                 final_pred_amount = self.bias_correction * transformed_val

                                             elif self.local_model_trans == 3: # Log (Natural) -> Exp
                                                 # VB: Prediction = BiasCorrection * (Exp(ConParms(mm, 2) * (Prediction + residual)))
                                                 # Here Prediction holds base+trend
                                                 val_to_inflate = base_plus_trend + residual_amount
                                                 val_to_exp = var_inf * val_to_inflate
                                                 try:
                                                      transformed_val = math.exp(val_to_exp)
                                                 except OverflowError:
                                                      transformed_val = float('inf') # Handle overflow
                                                 final_pred_amount = self.bias_correction * transformed_val

                                             elif self.local_model_trans == 4: # Inverse Normal -> Translator
                                                 # VB: Prediction = BiasCorrection * (ConParms(mm, 2) * (Prediction) + residual)
                                                 # Here Prediction holds base+trend. Result is value fed into Translator.
                                                 val_for_translator = (var_inf * base_plus_trend) + residual_amount
                                                 interim_val = self.bias_correction * val_for_translator
                                                 # Then apply translator
                                                 final_pred_amount = self._translator_inv_norm(interim_val)
                                                 # Bias is already incorporated before Translator call, matching VB T4 logic.

                                             elif self.local_model_trans == 5: # Box-Cox
                                                 if lambda_params_month is not None:
                                                     lamda = lambda_params_month[0]
                                                     right_shift = lambda_params_month[1]
                                                     # VB: interimVal = (ConParms(mm, 2) * (Prediction) + residual) + LamdaArray(mm, 2)
                                                     # Here Prediction holds base+trend.
                                                     val_to_transform = (var_inf * base_plus_trend) + residual_amount + right_shift

                                                     # Apply inverse Box-Cox transformation
                                                     untransformed_val = self.global_missing_code
                                                     if abs(lamda) < 1e-9: # Log transform case (lambda approx 0)
                                                          # Y' = ln(Y + shift) => Y = exp(Y') - shift
                                                          try:
                                                               untransformed_val = math.exp(val_to_transform) - right_shift
                                                          except OverflowError: untransformed_val = float('inf')
                                                     else: # Power transform case
                                                          # Y' = ((Y + shift)^lambda - 1) / lambda
                                                          # => Y = (Y' * lambda + 1)^(1/lambda) - shift
                                                          term = val_to_transform * lamda + 1.0
                                                          if term < 1e-9: # Base must be positive for general power (allow small tolerance)
                                                               print(f"WARN: BoxCox invalid base term {term:.3f} <=0 day {day_counter+1}, ens {ens_idx+1}. Setting to missing.")
                                                               untransformed_val = self.global_missing_code
                                                          else:
                                                               try:
                                                                    # Use safe power function: sign(base) * (|base| ** exponent) ? No, standard power needed.
                                                                    untransformed_val = math.pow(term, 1.0 / lamda) - right_shift
                                                               except ValueError: # e.g., complex result from neg base ^ non-integer exp
                                                                    print(f"WARN: BoxCox ValueError (likely neg base {term:.3f} ^ {1.0/lamda:.3f}) day {day_counter+1}, ens {ens_idx+1}. Setting to missing.")
                                                                    untransformed_val = self.global_missing_code
                                                               except OverflowError:
                                                                    untransformed_val = float('inf')

                                                     # Apply bias AFTER inverse transform for BoxCox
                                                     # VB: Prediction = BiasCorrection * (interimVal - LamdaArray(mm, 2)) where interimVal is untransformed
                                                     if untransformed_val != self.global_missing_code and not math.isinf(untransformed_val):
                                                          final_pred_amount = self.bias_correction * untransformed_val
                                                     else:
                                                          final_pred_amount = untransformed_val # Keep missing or inf
                                                 else: # Missing lambda params
                                                     final_pred_amount = self.global_missing_code
                                                     if day_counter == 0: print(f"WARN: Missing BoxCox parameters for month {current_month_idx+1}, cannot transform.")

                                             # --- Final Checks and Threshold ---
                                             if math.isinf(final_pred_amount):
                                                 print(f"WARN: Infinite value after transform day {day_counter+1}, ens {ens_idx+1}, trans={self.local_model_trans}. Set to missing.")
                                                 final_pred_amount = self.global_missing_code
                                             elif math.isnan(final_pred_amount):
                                                  print(f"WARN: NaN value after transform day {day_counter+1}, ens {ens_idx+1}, trans={self.local_model_trans}. Set to missing.")
                                                  final_pred_amount = self.global_missing_code

                                             # Apply Threshold: If value is <= Thresh, set to Thresh + 0.001 (matches VB)
                                             # VB: `If ((Prediction <> GlobalMissingCode) And (Prediction <= Thresh)) Then Prediction = Thresh + 0.001`
                                             if final_pred_amount != self.global_missing_code:
                                                 if final_pred_amount <= self.thresh:
                                                      final_pred_amount = self.thresh + 0.001

                                         except (ValueError, OverflowError, TypeError) as transform_err:
                                             print(f"WARN: Transform/Calc Error day {day_counter+1}, ens {ens_idx+1}, trans={self.local_model_trans}: {transform_err}")
                                             final_pred_amount = self.global_missing_code # Set to missing on error

                                         # Store final conditional prediction amount
                                         daily_prediction[ens_idx] = final_pred_amount
                                     # End if wet day
                                 # End ensemble loop 2 for conditional amounts
                    # End conditional amount calculation block


                # --- Write Results for the Day ---
                # If missing_flag was set at any point (predictors or essential params), write missing codes
                if missing_flag:
                    daily_prediction.fill(self.global_missing_code)

                # Format to 3 decimal places with fixed point notation like VB Format(..., "#####0.000")
                output_parts = []
                for val in daily_prediction:
                    # Check for NaN or global missing code
                    if np.isnan(val) or abs(val - self.global_missing_code) < 1e-9:
                         # Format missing code as integer if possible, else float
                         output_parts.append(f"{int(self.global_missing_code):d}" if self.global_missing_code == int(self.global_missing_code) else f"{self.global_missing_code:.1f}")
                    else:
                         # Format valid numbers to 3 decimal places, fixed point
                         # Handle potential large numbers gracefully if needed, standard formatting usually okay.
                         formatted_val = f"{val:.3f}"
                         # Basic check to prevent excessively long output if numbers are huge
                         if len(formatted_val) > 20: formatted_val = f"{val:.3e}" # Switch to scientific if too long
                         output_parts.append(formatted_val)

                try:
                    out_file_handle.write("\t".join(output_parts) + "\n")
                except Exception as e:
                    raise IOError(f"Error writing to output file {self.out_file_path} on day {day_counter+1}: {e}")

                # --- Increment Date ---
                try:
                    current_date += datetime.timedelta(days=1)
                except OverflowError:
                     raise ValueError("Date overflow during simulation loop. Check synthesis length and start date.")

            # --- End of Main Simulation Loop ---
            progress.setValue(total_prog_steps -1) # Mark loop completion

            # --- Create *.SIM File ---
            progress.setLabelText("Creating SIM file...")
            QCoreApplication.processEvents()

            try:
                with open(sim_file_path, 'w') as sim_f:
                     # Match VB Print # (numbers) and Write # (quoted strings, #TRUE#/#FALSE#) format
                     # 1. NPredictors (abs value if detrend) - VB Print # uses space padding based on number size
                     np_val = abs(self.n_predictors) if self.de_trend else self.n_predictors
                     sim_f.write(f" {np_val}\n") # Add leading space like VB Print #
                     # 2. SeasonCode - VB Print #
                     sim_f.write(f" {self.season_code}\n")
                     # 3. YearIndicator (from settings) - VB Print #
                     sim_f.write(f" {self.year_indicator}\n")
                     # 4. FSDate (Synthesis Start Date from UI) - VB Print # uses default locale format, use dd/mm/yyyy consistent with PAR read
                     sim_start_date_ui = self._parse_date(self.fStartText.text())
                     # VB Print # for dates might depend on system settings. Use a consistent format.
                     sim_f.write(f"{sim_start_date_ui.strftime('%d/%m/%Y')}\n") # No leading space needed for date? Check VB output. Let's assume not for now.
                     # 5. NDays (Synthesis Length from UI) - VB Print #
                     sim_f.write(f" {synthesis_length}\n")
                     # 6. RainYes (Boolean) - VB Write # uses #TRUE#/#FALSE#
                     sim_f.write(f"#{str(self.rain_yes).upper()}#\n")
                     # 7. EnsembleSize (Used) - VB Print #
                     sim_f.write(f" {ensemble_size}\n")
                     # 8. PrecN (Variance Inflation N) - VB Print #
                     sim_f.write(f" {self.prec_n}\n")
                     # 9. LocalModelTrans - VB Print #
                     sim_f.write(f" {self.local_model_trans}\n")
                     # 10. BiasCorrection - VB Print # (float)
                     # Format float similar to how VB might print it (e.g., avoid trailing .0)
                     sim_f.write(f" {self.bias_correction:g}\n")
                     # 11. PtandFilename (String) - VB Write # quotes strings
                     sim_f.write(f'"{self.ptand_filename}"\n')
                     # 12+ Predictor Filenames (Strings) - VB Write # quotes strings
                     # Use original list index 1 to NPredictors+1
                     for i in range(self.n_predictors):
                         fname = self.predictor_filenames[i+1] if (i+1) < len(self.predictor_filenames) else ""
                         sim_f.write(f'"{fname}"\n')
            except Exception as e:
                raise IOError(f"Error writing SIM file {sim_file_path}: {e}")

            progress.setValue(total_prog_steps) # Mark completion

            QMessageBox.information(self, "Synthesis Complete",
                                f"Synthesis finished successfully.\n\nOutput: {self.out_file_path}\nSummary: {sim_file_path}")

        except FileNotFoundError as e:
            QMessageBox.critical(self, "File Error", f"Required file not found during synthesis:\n{e}\n{traceback.format_exc()}")
        except EOFError as e:
            QMessageBox.critical(self, "File Error", f"Unexpected end of input file encountered during synthesis:\n{e}\n{traceback.format_exc()}")
        except InterruptedError:
            QMessageBox.warning(self, "Cancelled", "Synthesis cancelled by user.")
        except IOError as e:
            QMessageBox.critical(self, "File I/O Error", f"Error reading/writing file during synthesis:\n{e}\n{traceback.format_exc()}")
        except MemoryError:
            QMessageBox.critical(self, "Memory Error", "Not enough memory to complete the operation. Try reducing ensemble size or synthesis length.")
        except ValueError as e:
            QMessageBox.critical(self, "Data Error", f"Invalid data or parameter encountered during synthesis:\n{e}\n{traceback.format_exc()}")
        except RuntimeError as e: # Catch internal logic errors
             QMessageBox.critical(self, "Runtime Error", f"An internal error occurred:\n{e}\n{traceback.format_exc()}")
        except Exception as e:
            QMessageBox.critical(self, "Synthesis Error", f"An unexpected error occurred during synthesis:\n{e}\n\n{traceback.format_exc()}")
        finally:
            # --- Cleanup ---
            if progress: progress.close()
            if out_file_handle and not out_file_handle.closed:
                try: out_file_handle.close()
                except Exception as e: print(f"Error closing output file: {e}")
            for f_handle in predictor_file_handles:
                if f_handle and not f_handle.closed:
                    try: f_handle.close()
                    except Exception as e: print(f"Error closing predictor file: {e}")
            # Reset mouse pointer and key preview if needed (handled by progress dialog closing)


    def reset_parsed_data(self):
        """Clears only the data parsed from the PAR file."""
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
        self.inv_norm_first_value_idx = -1
        self.inv_norm_n_split = 0
        self.inv_norm_limit = 0.0
        self.inv_norm_total_area = 0.0
        # Reset parameter indices
        self.idx_b0_uncon, self.idx_b1_uncon, self.idx_se_uncon, self.idx_ar_uncon = -1, -1, -1, -1
        self.idx_lambda, self.idx_rshift = -1, -1
        self.idx_b0_con, self.idx_varinf_con, self.idx_b1_con, self.idx_se_con = -1, -1, -1, -1


    def reset_all(self):
        """Resets the UI fields and internal state to defaults."""
        try:
            # Reset file paths and related UI
            self.par_file_path = ""
            self.predictor_dir = self.default_dir # Reset to default predictor dir
            self.out_file_path = ""
            self.par_file_text.setText("Not selected")
            self.dirText.setText(self.predictor_dir)
            self.outFileText.setText("Not selected")

            # Reset UI input fields
            self.eSize.setText("20")
            default_start = self.settings.get('globalSDate', "01/01/1961")
            self.fStartText.setText(default_start)
            self.fLengthText.setText("365")

            # Reset UI info labels derived from PAR
            self.predictorList.clear()
            self.no_of_pred_text.setText("0")
            self.auto_regress_label.setText("Unknown")
            self.process_label.setText("Unknown")
            self.r_start_text.setText("unknown")
            self.r_length_text.setText("unknown")

            # Clear all parsed PAR data and internal state
            self.reset_parsed_data()

        except Exception as e:
            QMessageBox.critical(self, "Reset Error", f"Error during reset: {str(e)}")


# --- Main Application Runner (Example) ---
if __name__ == '__main__':
    import sys

    # Ensure QCoreApplication exists for processEvents before QApplication loop
    _app = QCoreApplication.instance()
    if _app is None:
        _app = QApplication(sys.argv) # Create if doesn't exist
    else:
        print("QCoreApplication instance already exists.")

    # --- EXAMPLE: Define your settings dictionary here ---
    app_settings = {
        'yearIndicator': 365,       # Corresponds to YearIndicator in SIM output
        'globalSDate': "01/01/1961",# Default start date in UI
        'allowNeg': True,           # Corresponds to AllowNeg setting
        'randomSeed': False,        # *** ENSURE THIS IS FALSE FOR TESTING REPLICATION ATTEMPTS ***
        'thresh': 0.0,              # Corresponds to Thresh setting
        'defaultDir': os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data')), # Example default relative to script
        'globalMissingCode': -999.0,# Corresponds to GlobalMissingCode
        'varianceInflation': 12,    # This is PrecN in VB6 residual calculation
        'biasCorrection': 1.0,      # Corresponds to BiasCorrection setting
        'fixedThreshold': 0.5,      # Corresponds to ConditionalThresh setting (if ConditionalSelection=Fixed)
        'conditionalSelection': 'Stochastic', # 'Stochastic' or 'Fixed' (corresponds to ConditionalSelection=1 or 2)
    }
    # Ensure defaultDir exists, create if not (optional)
    default_dir_path = app_settings['defaultDir']
    if not os.path.exists(default_dir_path):
         try:
             os.makedirs(default_dir_path)
             print(f"Created default directory: {default_dir_path}")
         except Exception as e:
             print(f"Warning: Could not create default directory: {e}")
             default_dir_path = os.path.expanduser("~") # Fallback to home
             app_settings['defaultDir'] = default_dir_path
    elif not os.path.isdir(default_dir_path):
         print(f"Warning: defaultDir '{default_dir_path}' is not a directory. Falling back to home.")
         default_dir_path = os.path.expanduser("~") # Fallback to home
         app_settings['defaultDir'] = default_dir_path
    # ---

    app = QApplication.instance() # Get the instance created above or by previous import
    if app is None: # If it wasn't created for some reason
        app = QApplication(sys.argv)

    mainWindow = QMainWindow()
    mainWindow.setWindowTitle("SDSM Synthesize Data (Python Conversion)")
    contentWidget = ContentWidget(settings=app_settings)
    mainWindow.setCentralWidget(contentWidget)
    mainWindow.setGeometry(100, 100, 650, 750) # Adjusted size slightly
    mainWindow.show()
    sys.exit(app.exec_())