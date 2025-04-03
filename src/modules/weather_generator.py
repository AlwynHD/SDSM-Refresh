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
from PyQt5.QtCore import Qt

# --- Helper Functions ---
def normal_pdf(x):
    """Probability Density Function of the standard normal distribution."""
    return scipy_norm.pdf(x)

def get_season(month):
    """Returns season index (0-3 for Winter, Spring, Summer, Autumn)."""
    # Assuming Northern Hemisphere seasons
    if month in [12, 1, 2]: return 0 # Winter
    elif month in [3, 4, 5]: return 1 # Spring
    elif month in [6, 7, 8]: return 2 # Summer
    elif month in [9, 10, 11]: return 3 # Autumn
    else: raise ValueError(f"Invalid month: {month}")

def parse_fixed_width(line, width=14):
    """Parses a line with fixed-width floating point numbers."""
    values = []
    for i in range(0, len(line.rstrip()), width): # Use rstrip() to handle potential trailing whitespace
        segment = line[i:min(i + width, len(line))].strip() # Ensure segment doesn't exceed line length
        if segment:
            try: values.append(float(segment))
            except ValueError: values.append(np.nan) # Use NaN for parsing errors
        # Do not append if segment is empty (handles lines shorter than expected width)
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
            # Use while loop condition similar to VB GOTO
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
            'allowNeg': True, 'randomSeed': True, 'thresh': 0.0,
            'globalMissingCode': -999.0, 'varianceInflation': 12,
            'biasCorrection': 1.0, 'fixedThreshold': 0.5,
            'conditionalSelection': 'Stochastic', # 'Stochastic' or 'Fixed'
            'yearIndicator': 365, 'globalSDate': "01/01/1961",
            'defaultDir': os.path.expanduser("~")
        }
        self.settings = settings if settings else default_settings

        # Get values from settings, ensuring correct types
        self.allow_neg = bool(self.settings.get('allowNeg', True))
        self.use_random_seed = bool(self.settings.get('randomSeed', True))
        self.thresh = float(self.settings.get('thresh', 0.0))
        self.global_missing_code = float(self.settings.get('globalMissingCode', -999.0))
        self.prec_n = int(self.settings.get('varianceInflation', 12)) # Variance Inflation / N for residual sum
        self.bias_correction = float(self.settings.get('biasCorrection', 1.0))
        self.conditional_thresh = float(self.settings.get('fixedThreshold', 0.5))
        cond_sel_str = str(self.settings.get('conditionalSelection', 'Stochastic')).lower()
        self.conditional_selection = 1 if cond_sel_str == 'stochastic' else 2 # 1=VB Rnd<=Pred, 2=VB Pred>=Thresh
        self.year_indicator = int(self.settings.get('yearIndicator', 365))
        self.default_dir = self.settings.get('defaultDir', os.path.expanduser("~"))
        # --- End Settings ---

        self.par_file_path = ""
        self.predictor_dir = self.default_dir # Start with default predictor dir
        self.out_file_path = ""

        # --- Variables to store parsed PAR data ---
        self.n_predictors = 0
        self.season_code = 0 # 1=Ann, 4=Seas, 12=Mon
        self.year_length_par = 0 # 360, 365, 366 from PAR
        self.start_date_par = None # datetime.date
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
        self.beta_trend = None  # Numpy array [period_idx (0-11), param_idx]
        self.de_trend = False   # Was detrending applied during calibration?
        self.de_trend_type = 0  # 1=linear, 2=power
        self.ptand_file_root = "" # Path to predictand file for Inv Norm
        # --- Variables for Inverse Normal Transform ---
        self.rank_data = []
        self.inv_norm_first_value = -1 # Index in sorted rank_data >= thresh
        self.inv_norm_n_split = 0 # Count of values >= thresh
        self.inv_norm_limit = 0.0 # Lower z-score bound
        self.inv_norm_total_area = 0.0 # Area between lower/upper bounds
        # --- Parameter Indices (will be set after parsing PAR) ---
        self.idx_b0_uncon = -1
        self.idx_b1_uncon = -1
        self.idx_se_uncon = -1
        self.idx_ar_uncon = -1 # -1 if AR not used
        self.idx_lambda = -1   # -1 if BoxCox not used
        self.idx_rshift = -1   # -1 if BoxCox not used
        self.idx_b0_con = -1
        self.idx_varinf_con = -1
        self.idx_b1_con = -1
        self.idx_se_con = -1
        # --- Other state ---
        self._cancel_synthesis = False

        # --- UI Setup ---
        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(20, 20, 20, 20) # Reduced margins slightly
        mainLayout.setSpacing(15) # Reduced spacing slightly
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

        # View Details button replaced by loading PAR automatically
        self.viewDetailsButton = QPushButton("View/Verify Predictor Files")
        self.viewDetailsButton.setToolTip("Check if predictor files listed in the PAR exist in the selected directory")
        self.viewDetailsButton.clicked.connect(self.viewPredictors)
        dataLayout.addWidget(self.viewDetailsButton, 0, 0, 1, 2)#, Qt.AlignCenter)

        self.predictorList = QListWidget()
        self.predictorList.setToolTip("Predictand (first) and Predictor files read from PAR")
        self.predictorList.setMinimumHeight(100) # Reduced height
        self.predictorList.setMaximumHeight(200)
        dataLayout.addWidget(self.predictorList, 1, 0, 1, 2)

        # Use QHBoxLayout for label + value pairs for better alignment
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

        # Add a separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        dataLayout.addWidget(separator, 5, 0, 1, 2)

        # Record and synthesis information
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
        ensembleLayout = QHBoxLayout() # Use QHBoxLayout
        ensembleGroup.setLayout(ensembleLayout)
        mainLayout.addWidget(ensembleGroup)

        ensembleLayout.addWidget(QLabel("Number of ensemble members:"))
        self.eSize = QLineEdit("20")
        self.eSize.setToolTip("Enter number of simulations (1-100)")
        self.eSize.setMaximumWidth(80) # Limit width
        ensembleLayout.addWidget(self.eSize)
        ensembleLayout.addStretch(1) # Push to left


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

        buttonLayout.addStretch(1) # Add space before buttons
        buttonLayout.addWidget(self.synthesizeButton)
        buttonLayout.addWidget(self.resetButton)
        buttonLayout.addStretch(1) # Add space after buttons
        # --- End UI Setup ---


    def selectPredictorDirectory(self):
        """Opens a directory dialog to select the predictor directory."""
        directory = QFileDialog.getExistingDirectory(self, "Select Predictor Directory", self.predictor_dir or os.path.expanduser("~"))
        if directory:
            self.predictor_dir = directory
            self.dirText.setText(directory)
            # Re-verify files if PAR was already loaded
            if self.par_file_path:
                 self.viewPredictors()

    def _parse_date(self, date_str):
        """Tries to parse date string in dd/mm/yyyy or mm/dd/yyyy format."""
        for fmt in ('%d/%m/%Y', '%m/%d/%Y'):
            try:
                return datetime.datetime.strptime(date_str, fmt).date()
            except ValueError:
                pass
        raise ValueError(f"Date format not recognized: {date_str}")

    def loadPARFile(self, file_path):
        """Loads and parses PAR file data into instance variables."""
        self.reset_parsed_data() # Clear previous PAR data first
        self.par_file_path = file_path
        self.par_file_text.setText(f"{os.path.basename(file_path)}")

        try:
            with open(file_path, 'r') as par_file:
                lines = [line.strip() for line in par_file if line.strip()] # Read all non-empty lines

            line_idx = 0
            def get_line():
                nonlocal line_idx
                if line_idx >= len(lines): raise EOFError("Unexpected end of PAR file.")
                line = lines[line_idx]
                line_idx += 1
                return line

            # --- Read Header ---
            n_pred_raw = int(get_line())
            self.de_trend = n_pred_raw < 0
            self.n_predictors = abs(n_pred_raw)
            self.no_of_pred_text.setText(str(self.n_predictors))

            self.season_code = int(get_line())
            self.year_length_par = int(get_line())
            record_start_str = get_line()
            self.start_date_par = self._parse_date(record_start_str)
            self.r_start_text.setText(self.start_date_par.strftime('%d/%m/%Y'))
            self.n_days_r_par = int(get_line())
            self.r_length_text.setText(str(self.n_days_r_par))
            cal_fs_date_str = get_line()
            self.cal_fs_date_par = self._parse_date(cal_fs_date_str)
            # Set UI default synthesis start/length based on Calibration info
            self.fStartText.setText(self.cal_fs_date_par.strftime('%d/%m/%Y'))
            self.n_days_cal_par = int(get_line())
            self.fLengthText.setText(str(self.n_days_cal_par))
            self.rain_yes = get_line().lower() == "true"
            self.process_label.setText("Conditional" if self.rain_yes else "Unconditional")
            self.local_model_trans = int(get_line())
            _ = int(get_line()) # Ensemble size from PAR - unused

            # --- Handle SDSM 3.1 vs 4.2 difference ---
            potential_ar_flag = get_line()
            if potential_ar_flag.lower() in ["true", "false"]: # SDSM 4.2+
                self.auto_regression = potential_ar_flag.lower() == "true"
                self.ptand_filename = get_line()
            else: # SDSM 3.1
                self.auto_regression = False
                self.ptand_filename = potential_ar_flag
            self.auto_regress_label.setText(str(self.auto_regression))

            # --- Read Predictor Filenames ---
            self.predictor_filenames.append(self.ptand_filename) # Predictand listed first
            for _ in range(self.n_predictors):
                pred_fname = get_line()
                self.predictor_filenames.append(pred_fname)
            # Update UI list later in viewPredictors or after successful load

            # --- Determine Parameter Indices *AFTER* knowing AR/BoxCox status ---
            # Unconditional
            self.idx_b0_uncon = 0
            self.idx_b1_uncon = 1
            self.idx_se_uncon = self.idx_b1_uncon + self.n_predictors
            param_count_uncon = self.idx_se_uncon + 1 # Current count: B0 + Bpred + SE
            if self.auto_regression:
                self.idx_ar_uncon = param_count_uncon
                param_count_uncon += 1
            else: self.idx_ar_uncon = -1
            if self.local_model_trans == 5: # BoxCox
                self.idx_lambda = param_count_uncon
                self.idx_rshift = param_count_uncon + 1
                param_count_uncon += 2
            else: self.idx_lambda, self.idx_rshift = -1, -1

            # Conditional (Indices are simpler)
            if self.rain_yes:
                self.idx_b0_con = 0
                self.idx_varinf_con = 1 # Variance Inflation factor
                self.idx_b1_con = 2 # Start of predictor coefficients
                self.idx_se_con = self.idx_b1_con + self.n_predictors # SE after predictor coeffs
                param_count_con = self.idx_se_con + 1

            # --- Read Model Parameters (Unconditional) ---
            self.uncon_parms = np.full((12, param_count_uncon), np.nan) # 12 months
            if self.local_model_trans == 5:
                self.lamda_array = np.full((12, 2), np.nan)

            for i in range(12): # 12 months
                params = parse_fixed_width(get_line(), 14)
                # Ensure params list is long enough, pad with NaN if necessary
                if len(params) < param_count_uncon:
                    params.extend([np.nan] * (param_count_uncon - len(params)))

                self.uncon_parms[i, :] = params[:param_count_uncon] # Assign all expected params

                # Extract Lambda/Shift separately if BoxCox
                if self.local_model_trans == 5:
                     if self.idx_lambda < len(params): self.lamda_array[i, 0] = params[self.idx_lambda]
                     if self.idx_rshift < len(params): self.lamda_array[i, 1] = params[self.idx_rshift]


            # --- Read Model Parameters (Conditional, if applicable) ---
            if self.rain_yes:
                self.con_parms = np.full((12, param_count_con), np.nan)
                for i in range(12):
                    params = parse_fixed_width(get_line(), 14)
                    if len(params) < param_count_con:
                        params.extend([np.nan] * (param_count_con - len(params)))
                    self.con_parms[i, :] = params[:param_count_con]


            # --- Read Predictand File Root (for Inv Normal) ---
            self.ptand_file_root = get_line()

            # --- Read Detrend Parameters (if applicable) ---
            if self.de_trend:
                self.de_trend_type = int(get_line()) # 1=linear, 2=power
                n_trend_params = 3 if self.de_trend_type == 2 else 2
                # Determine number of rows for BetaTrend based on SeasonCode
                if self.season_code == 1: trend_rows = 1   # Annual
                elif self.season_code == 4: trend_rows = 4 # Seasonal
                elif self.season_code == 12: trend_rows = 12 # Monthly
                else: raise ValueError(f"Unsupported SeasonCode for Detrend: {self.season_code}")

                self.beta_trend = np.full((trend_rows, n_trend_params), np.nan)
                for i in range(trend_rows):
                     p1 = float(get_line())
                     p2 = float(get_line())
                     self.beta_trend[i, 0] = p1
                     self.beta_trend[i, 1] = p2
                     if self.de_trend_type == 2:
                        p3 = float(get_line())
                        self.beta_trend[i, 2] = p3 # Minimum value applied

            # --- Post Load Actions ---
            # Auto-select predictor directory if not set
            par_dir = os.path.dirname(file_path)
            if not os.path.exists(self.predictor_dir): # If current dir invalid or default
                self.predictor_dir = par_dir
                self.dirText.setText(par_dir)
            # Verify predictor files exist
            self.viewPredictors() # Update list widget and check files

            QMessageBox.information(self, "PAR File Loaded",
                            f"Successfully loaded parameter file '{os.path.basename(file_path)}'.\nPlease verify Predictor Directory and Synthesis Settings.")

        except FileNotFoundError:
            QMessageBox.critical(self, "Error Loading PAR File", f"File not found: {file_path}")
            self.reset_all()
        except (EOFError, IndexError):
             QMessageBox.critical(self, "Error Loading PAR File", f"Unexpected end of file or missing data in:\n{file_path}")
             self.reset_all()
        except ValueError as e:
             QMessageBox.critical(self, "Error Loading PAR File", f"Invalid data format in PAR file:\n{e}\nFile: {file_path}")
             self.reset_all()
        except Exception as e:
            QMessageBox.critical(self, "Error Loading PAR File", f"Failed to parse PAR file:\n{str(e)}\n{traceback.format_exc()}")
            self.reset_all()


    def selectPARFile(self):
        """Opens a file dialog to select a PAR file."""
        # Use predictor_dir as starting point if valid, else default_dir
        start_dir = self.predictor_dir if os.path.isdir(self.predictor_dir) else self.default_dir
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Parameter File", start_dir, "PAR Files (*.par *.PAR);;All Files (*.*)")
        if file_name:
            self.loadPARFile(file_name)


    def selectOutputFile(self):
        """Opens a file dialog to select an output file."""
        default_name = ""
        # Suggest a name based on PAR file in the predictor directory
        if self.par_file_path and os.path.isdir(self.predictor_dir):
            base = os.path.splitext(os.path.basename(self.par_file_path))[0]
            default_name = os.path.join(self.predictor_dir, f"{base}.OUT")
        elif os.path.isdir(self.predictor_dir):
             default_name = os.path.join(self.predictor_dir, "output.OUT")
        else:
             default_name = os.path.join(self.default_dir, "output.OUT")


        file_name, _ = QFileDialog.getSaveFileName(self, "Save To .OUT File", default_name, "OUT Files (*.OUT);;All Files (*.*)")
        if file_name:
            # Ensure extension is .OUT
            if not file_name.upper().endswith(".OUT"):
                 file_name += ".OUT"
            self.out_file_path = file_name
            self.outFileText.setText(os.path.basename(file_name))


    def viewPredictors(self):
        """Checks existence of predictor files listed in the PAR file and updates list widget."""
        self.predictorList.clear() # Clear previous items

        if not self.par_file_path:
            # QMessageBox.warning(self, "No PAR file selected", "Please load a parameter file first.")
            return # Silently return if no PAR loaded yet
        if not self.predictor_dir or not os.path.isdir(self.predictor_dir):
             QMessageBox.warning(self, "No Predictor Directory", "Please select a valid predictor directory.")
             return
        if not self.predictor_filenames:
             # QMessageBox.information(self, "No Predictors", "No predictor files listed in the loaded PAR file.")
             return # Silently return

        missing_files = []
        found_files = []

        for i, filename in enumerate(self.predictor_filenames):
            full_path = os.path.join(self.predictor_dir, filename)
            prefix = "Predictand: " if i == 0 else "Predictor:  "
            if not os.path.exists(full_path):
                missing_files.append(filename)
                self.predictorList.addItem(f"⚠️ {prefix}{filename} (Missing!)")
            else:
                found_files.append(filename)
                self.predictorList.addItem(f"✅ {prefix}{filename}")

        if missing_files:
            missing_list = "\n- ".join(missing_files)
            QMessageBox.warning(self, "Missing Files",
                            f"Predictor file(s) not found in '{self.predictor_dir}':\n- {missing_list}\n\nPlease select the correct directory.")
        # else:
            # Optionally show success message if needed
            # QMessageBox.information(self, "Files Verified",
            #                     f"All {len(found_files)} required files found in directory.")


    def _prepare_inverse_normal(self):
        """Reads predictand data, sorts it, and calculates parameters for Inv Normal transform."""
        self.rank_data = [] # Reset
        self.inv_norm_first_value = -1
        self.inv_norm_n_split = 0
        self.inv_norm_limit = 0.0
        self.inv_norm_total_area = 0.0

        if not self.ptand_file_root:
             raise ValueError("Predictand file root missing in PAR (required for Inv Normal).")

        # Try path relative to predictor dir first, then absolute path
        ptand_path_rel = os.path.join(self.predictor_dir, os.path.basename(self.ptand_file_root))
        ptand_path_abs = self.ptand_file_root

        if os.path.exists(ptand_path_rel):
            ptand_path = ptand_path_rel
        elif os.path.exists(ptand_path_abs):
            ptand_path = ptand_path_abs
        else:
            raise FileNotFoundError(f"Predictand file for Inv Normal not found at:\n1. {ptand_path_rel}\n2. {ptand_path_abs}")

        try:
            # --- Read predictand data for the *calibration* period ---
            read_values = []
            with open(ptand_path, 'r') as f_ptand:
                current_date = self.start_date_par
                # Skip data before calibration start date
                days_to_skip = (self.cal_fs_date_par - self.start_date_par).days
                if days_to_skip < 0: days_to_skip = 0 # Should not happen if PAR is valid
                for _ in range(days_to_skip):
                     line = f_ptand.readline()
                     if not line: raise EOFError("Predictand file ended before calibration start date.")
                     # No need to update current_date here, just skip lines

                # Read NDays of calibration data
                for _ in range(self.n_days_cal_par):
                    line = f_ptand.readline()
                    if not line:
                        QMessageBox.warning(self, "Data Warning", f"Predictand file {os.path.basename(ptand_path)} ended prematurely. Expected {self.n_days_cal_par} values after {self.cal_fs_date_par.strftime('%d/%m/%Y')}, got fewer.")
                        break
                    try:
                        val = float(line.strip())
                        # VB6 code using RankData seems to include all values for sorting,
                        # not just > Thresh initially. Let's store all valid floats.
                        if val != self.global_missing_code: # Exclude missing codes from rank data
                             read_values.append(val)
                        # Else: simply skip missing values for ranking/translation
                    except ValueError:
                        # Treat lines that cannot be converted to float as missing
                        pass # Skip non-numeric lines

            if not read_values:
                 raise ValueError(f"No valid numeric data found in predictand file {os.path.basename(ptand_path)} for the calibration period.")

            # --- Sort the valid observed data ---
            self.rank_data = shell_sort(read_values) # Use VB6-like sort on valid data

            # --- Determine index of first value > threshold in sorted data ---
            self.inv_norm_first_value = -1
            for i, val in enumerate(self.rank_data):
                # VB used > Thresh. Let's strictly follow that.
                if val > self.thresh:
                    self.inv_norm_first_value = i
                    break

            if self.inv_norm_first_value == -1:
                 # Check if any values are AT the threshold (VB might include these implicitly)
                 if any(abs(v - self.thresh) < 1e-9 for v in self.rank_data):
                      QMessageBox.warning(self, "Inv Normal Warning", f"No data strictly > threshold ({self.thresh}) found for Inv Normal.\nData exists at the threshold; using these.")
                      # Find first value >= threshold
                      for i, val in enumerate(self.rank_data):
                           if val >= self.thresh:
                                self.inv_norm_first_value = i
                                break
                 if self.inv_norm_first_value == -1: # Still not found
                      raise ValueError(f"No data >= threshold ({self.thresh}) found for Inv Normal.")


            self.inv_norm_n_split = len(self.rank_data) - self.inv_norm_first_value
            if self.inv_norm_n_split <= 0:
                 raise ValueError(f"Inverse Normal nSplit <= 0. FirstValue={self.inv_norm_first_value}, NRankData={len(self.rank_data)}")

            # --- Locate lower bound (limit) ---
            # Calculation follows VB6 TRAPEZ/INTRAPEZ logic
            z_start = 1.0 / (self.inv_norm_n_split + 1.0)
            delta = 0.0001
            area = 0.5
            fx = 0.0
            fx_old = normal_pdf(fx)
            self.inv_norm_limit = np.nan # Initialize as NaN

            # Search downwards from Z=0 for the Z-score where cumulative area = z_start
            for _ in range(50000): # Max iterations safeguard
                fx -= delta
                fx_new = normal_pdf(fx)
                # Area subtracted = integral from fx to fx_old (approximated by trapezoid)
                area -= (delta * 0.5 * (fx_old + fx_new))
                if area <= z_start:
                    # We found the Z-score (fx) corresponding to the lower tail probability z_start
                    self.inv_norm_limit = fx
                    break
                fx_old = fx_new
            else: # Loop finished without finding limit
                QMessageBox.warning(self, "Inv Normal Warning", f"Could not accurately find lower limit Z-score for P={z_start:.4f}. Using fallback Z=-5.0.")
                self.inv_norm_limit = -5.0 # Fallback Z-score

            # Total area used for scaling = 1 - 2*z_start (area excluding tails)
            self.inv_norm_total_area = max(0.0, 1.0 - (2.0 * z_start)) # Ensure non-negative
            if self.inv_norm_total_area <= 1e-9: # Check for near-zero area
                 QMessageBox.warning(self,"Inv Normal Warning", f"Total Area for scaling is near zero ({self.inv_norm_total_area:.2e}). nSplit={self.inv_norm_n_split}. Check threshold/data.")
                 # Avoid division by zero later, although this indicates a likely data issue
                 if self.inv_norm_total_area <= 0: self.inv_norm_total_area = 1e-9


        except Exception as e:
            raise IOError(f"Error processing predictand file {ptand_path} for Inv Normal: {e}\n{traceback.format_exc()}")

    def _translator_inv_norm(self, passed_value):
        """Inverse Normal Transform: Converts Z-score back to data value using ranked data."""
        # Ensure rank_data is valid and prepared
        if not self.rank_data or self.inv_norm_first_value < 0 or self.inv_norm_first_value >= len(self.rank_data) or self.inv_norm_n_split <= 0:
            QMessageBox.warning(self, "Translator Error", "Rank data invalid or not prepared for translation.")
            return self.global_missing_code # Or raise error

        # Handle Z-scores below the calculated lower limit
        if passed_value <= self.inv_norm_limit:
            # Return the first value in the ranked data that was >= threshold
            return self.rank_data[self.inv_norm_first_value]

        # Calculate area under normal curve from limit up to passed_value (Z-score)
        # Uses trapezoidal rule matching VB6 INTRAPEZ
        interval = (passed_value - self.inv_norm_limit) / 100.0 # 100 steps
        area_from_limit = 0.0
        fx = self.inv_norm_limit
        fx_old = normal_pdf(fx)
        for _ in range(100):
            fx += interval
            fx_new = normal_pdf(fx)
            area_from_limit += (interval * 0.5 * (fx_old + fx_new))
            fx_old = fx_new

        # Scale the calculated area relative to the total usable area (1 - 2*z_start)
        # Ensure area doesn't exceed total_area (can happen due to approximation)
        area_from_limit = min(area_from_limit, self.inv_norm_total_area)
        area_from_limit = max(0.0, area_from_limit) # Ensure non-negative

        # Determine the index offset within the valid portion of rank_data
        if self.inv_norm_total_area <= 1e-9: # Avoid division by zero
            index_offset_float = 0.0
        else:
            # Proportion of total usable area covered determines proportion through nSplit values
            index_offset_float = (area_from_limit / self.inv_norm_total_area) * self.inv_norm_n_split

        # Convert float offset to integer index, adding to the start index
        # VB uses Int(), which truncates towards negative infinity. Python int() truncates towards zero.
        # Let's use floor to match VB's Int() for positive/negative offsets if needed, though offset should be positive here.
        # However, VB's `Int(area * nSplit / totalArea)` likely assumes positive area. Simple int() is fine.
        locate_index_offset = int(index_offset_float)

        locate_index = self.inv_norm_first_value + locate_index_offset

        # Clamp the index to be within the valid range of rank_data >= threshold
        # Use VB6 clamping logic: `locateValue >= (FirstValue + nSplit - 1)`
        max_allowable_index = self.inv_norm_first_value + self.inv_norm_n_split - 1
        # Also ensure max_allowable_index doesn't exceed actual array bounds
        max_allowable_index = min(max_allowable_index, len(self.rank_data) - 1)

        if locate_index >= max_allowable_index:
            locate_index = max_allowable_index
        # Lower bound check (shouldn't be needed if passed_value > limit, but good practice)
        locate_index = max(locate_index, self.inv_norm_first_value)

        # Final safety check on index before accessing array
        if self.inv_norm_first_value <= locate_index < len(self.rank_data):
            return self.rank_data[locate_index]
        else:
            # This should ideally not happen if logic above is correct
            QMessageBox.warning(self, "Translator Warning", f"Calculated index {locate_index} out of bounds [{self.inv_norm_first_value}-{max_allowable_index}]. Returning boundary value.")
            # Fallback: return first or last valid value in the split range
            return self.rank_data[self.inv_norm_first_value] if passed_value <= self.inv_norm_limit else self.rank_data[max_allowable_index]


    def synthesizeData(self):
        """Performs the main data synthesis."""
        self._cancel_synthesis = False # Reset cancel flag

        # --- Initial Validation ---
        if not self.par_file_path or not os.path.exists(self.par_file_path):
            QMessageBox.warning(self, "Missing Input", "Select a valid PAR file first.")
            return
        # Check if PAR loading was successful (indicated by n_predictors > 0 or con_parms/uncon_parms existing)
        if self.uncon_parms is None:
             QMessageBox.warning(self, "PAR Not Loaded", "Load PAR file successfully before synthesizing.")
             return
        if not self.out_file_path:
            QMessageBox.warning(self, "Missing Input", "Select an output file path.")
            return
        if not self.predictor_dir or not os.path.isdir(self.predictor_dir):
            QMessageBox.warning(self, "Missing Input", "Select a valid predictor directory.")
            return
        # Verify predictor files one last time before starting
        self.viewPredictors()
        if self.predictorList.count() > 0 and "Missing" in self.predictorList.item(0).text():
             # Check if any item contains the missing marker
             if any("Missing" in self.predictorList.item(i).text() for i in range(self.predictorList.count())):
                  QMessageBox.critical(self, "Missing Files", "Cannot synthesize. Required predictor files are missing. Check paths.")
                  return


        try:
            # Validate and get UI settings
            ensemble_size = int(self.eSize.text())
            if not 1 <= ensemble_size <= 100:
                QMessageBox.warning(self, "Invalid Input", "Ensemble size must be between 1 and 100.")
                return

            synthesis_start_date = self._parse_date(self.fStartText.text())

            synthesis_length = int(self.fLengthText.text())
            if synthesis_length < 1:
                QMessageBox.warning(self, "Invalid Input", "Synthesis length must be at least 1 day.")
                return

            # Date sanity checks
            if self.start_date_par and synthesis_start_date < self.start_date_par:
                 # Allow but warn
                 QMessageBox.warning(self, "Date Warning", "Synthesis start date is before the Record start date defined in the PAR file.")
            if self.cal_fs_date_par and self.n_days_r_par > 0:
                 record_end_date = self.start_date_par + datetime.timedelta(days=self.n_days_r_par - 1)
                 synthesis_end_date = synthesis_start_date + datetime.timedelta(days=synthesis_length - 1)
                 # Warn if synthesis period goes way beyond original record? Optional.


        except ValueError as e:
            QMessageBox.critical(self, "Invalid Input", f"Error in synthesis settings:\n{e}\n\nPlease check dates (dd/mm/yyyy or mm/dd/yyyy) and numbers.")
            return
        except Exception as e:
             QMessageBox.critical(self, "Input Error", f"Error processing inputs: {e}")
             return

        # --- Setup ---
        sim_file_path = os.path.splitext(self.out_file_path)[0] + ".SIM"

        # --- Random Seed ---
        if not self.use_random_seed: # If False, use fixed seed (like VB6 Rnd -1; Randomize 1)
             random.seed(1)
             np.random.seed(1) # Seed numpy's generator too
        else:
             # If True, let Python/Numpy seed from system sources
             random.seed()
             np.random.seed()


        # --- Progress Dialog ---
        progress = QProgressDialog("Initializing Synthesis...", "Cancel", 0, synthesis_length + 3, self) # Add steps for init
        progress.setWindowModality(Qt.WindowModal)
        progress.setWindowTitle("Processing")
        progress.setValue(0)
        progress.show()
        QApplication.processEvents()


        # --- Main Logic ---
        predictor_file_handles = []
        out_file_handle = None
        current_progress = 0

        try:
            # --- Prepare Inverse Normal (if needed) ---
            if self.local_model_trans == 4:
                 progress.setLabelText("Preparing Inverse Normal data...")
                 progress.setValue(current_progress); current_progress += 1
                 QApplication.processEvents()
                 if progress.wasCanceled(): raise InterruptedError("Cancelled")
                 self._prepare_inverse_normal() # Reads predictand, sorts, calculates params

            # --- Open Predictor Files ---
            progress.setLabelText("Opening predictor files...")
            progress.setValue(current_progress); current_progress += 1
            QApplication.processEvents()
            if progress.wasCanceled(): raise InterruptedError("Cancelled")

            # Open predictor files (skip predictand at index 0)
            predictor_files_to_open = self.predictor_filenames[1:]
            if self.n_predictors > 0 and not predictor_files_to_open:
                 raise ValueError("Mismatch: NPredictors > 0 but no predictor files listed after predictand.")
            if len(predictor_files_to_open) != self.n_predictors:
                 raise ValueError(f"Mismatch: Expected {self.n_predictors} predictors, found {len(predictor_files_to_open)} filenames.")

            for filename in predictor_files_to_open:
                filepath = os.path.join(self.predictor_dir, filename)
                # Existence already checked, but double check just before opening
                if not os.path.exists(filepath): raise FileNotFoundError(f"Predictor file disappeared: {filepath}")
                predictor_file_handles.append(open(filepath, 'r'))

            # --- Open Output File ---
            out_file_handle = open(self.out_file_path, 'w')

            # --- Initialize Detrending Variables ---
            # Use dictionaries for sparse storage keyed by period index (0-11)
            days_used_linear = {} # Tracks offset from CalFSDate for linear trend
            days_used_power = {}  # Tracks offset from StartDate for power trend baseline
            fs_date_baseline_days = {} # Days skipped per period up to FSDate
            trend_rows = 0 # Number of rows in beta_trend array

            if self.de_trend:
                progress.setLabelText("Initializing detrend variables...")
                progress.setValue(current_progress); current_progress += 1
                QApplication.processEvents()
                if progress.wasCanceled(): raise InterruptedError("Cancelled")

                if self.beta_trend is None: raise ValueError("Detrending enabled but BetaTrend parameters not loaded.")
                trend_rows = self.beta_trend.shape[0] # Get actual number of rows loaded

                # Calculate baseline day counts up to Calibration Fit Start Date (CalFSDate)
                cal_fs_date_baseline_days = {} # Days skipped per period up to CalFSDate
                current_d_cal = self.start_date_par
                days_diff_cal = (self.cal_fs_date_par - self.start_date_par).days
                if days_diff_cal < 0: days_diff_cal = 0

                for _ in range(days_diff_cal):
                    # Determine period index based on SeasonCode
                    month = current_d_cal.month
                    if self.season_code == 1: period_idx = 0
                    elif self.season_code == 4: period_idx = get_season(month) # 0-3 index
                    elif self.season_code == 12: period_idx = month - 1 # 0-11 index
                    else: period_idx = -1 # Should not happen if PAR valid

                    if 0 <= period_idx < trend_rows:
                         cal_fs_date_baseline_days[period_idx] = cal_fs_date_baseline_days.get(period_idx, 0) + 1
                    current_d_cal += datetime.timedelta(days=1) # Assumes standard Gregorian calendar

            # --- Skip Initial Data in Predictor Files ---
            progress.setLabelText("Skipping initial predictor data...")
            progress.setMaximum(synthesis_length + current_progress) # Adjust max for actual synthesis days
            progress.setValue(current_progress)
            QApplication.processEvents()

            days_to_skip = (synthesis_start_date - self.start_date_par).days
            if days_to_skip < 0: days_to_skip = 0

            current_d_skip = self.start_date_par
            # Skip lines in predictor files and update detrend baselines up to synthesis_start_date
            for day_skip_idx in range(days_to_skip):
                 if progress.wasCanceled(): raise InterruptedError("Cancelled")
                 # Optional: Update progress less frequently during skip
                 # if day_skip_idx > 0 and day_skip_idx % 500 == 0:
                 #     progress.setValue(current_progress + int(...)) # Need careful scaling if used
                 #     QApplication.processEvents()

                 # Read and discard one line from each predictor file
                 for i, f_handle in enumerate(predictor_file_handles):
                      line = f_handle.readline()
                      if not line: raise EOFError(f"Predictor file {self.predictor_filenames[i+1]} ended prematurely during initial skip.")

                 # Update detrending day counts for the skipped day
                 if self.de_trend:
                      month = current_d_skip.month
                      if self.season_code == 1: period_idx = 0
                      elif self.season_code == 4: period_idx = get_season(month) # 0-3
                      elif self.season_code == 12: period_idx = month - 1 # 0-11
                      else: period_idx = -1

                      if 0 <= period_idx < trend_rows:
                          # Track days from StartDate up to FSDate
                          fs_date_baseline_days[period_idx] = fs_date_baseline_days.get(period_idx, 0) + 1
                          # Initialize DaysUsedPower (offset from StartDate)
                          days_used_power[period_idx] = fs_date_baseline_days[period_idx]

                 current_d_skip += datetime.timedelta(days=1)


            # --- Initialize Simulation State ---
            current_date = synthesis_start_date
            start_month_idx = synthesis_start_date.month - 1 # 0-11

            # Initialize AR seed using intercept of the first month *of synthesis*
            # Check if params exist for the start month
            initial_intercept = 0.0
            if self.uncon_parms is not None and self.uncon_parms.shape[0] > start_month_idx and not np.isnan(self.uncon_parms[start_month_idx, self.idx_b0_uncon]):
                 initial_intercept = self.uncon_parms[start_month_idx, self.idx_b0_uncon]
            else:
                 QMessageBox.warning(self, "Init Warning", f"Missing Uncon Intercept for starting month {start_month_idx+1}. Initial AR seed set to 0.")

            # AR seed array for the ensemble
            auto_regression_seed = np.full(ensemble_size, initial_intercept)

            # Initialize linear detrend counter (offset relative to CalFSDate)
            if self.de_trend:
                for i in range(trend_rows):
                     fs_base = fs_date_baseline_days.get(i, 0)
                     cal_base = cal_fs_date_baseline_days.get(i, 0)
                     days_used_linear[i] = fs_base - cal_base
                     # days_used_power already initialized during skip phase

            # --- Main Simulation Loop ---
            progress.setLabelText("Running synthesis...")
            progress.setValue(current_progress) # Set progress before loop
            QApplication.processEvents()

            # Pre-allocate daily result arrays
            daily_prediction = np.full(ensemble_size, self.global_missing_code)
            # For conditional models, store intermediate wet/dry status
            is_wet_status = np.zeros(ensemble_size, dtype=bool) if self.rain_yes else None


            for day_counter in range(synthesis_length):
                if progress.wasCanceled(): raise InterruptedError("Cancelled")
                progress.setValue(current_progress + day_counter + 1) # Update progress (0 to N-1)
                QApplication.processEvents()

                current_month_idx = current_date.month - 1 # 0-11 index

                # --- Update Detrend Day Counts for the current day ---
                period_value_idx = -1 # Reset period index for the day
                trend_params = None    # Reset trend params for the day
                if self.de_trend:
                    month = current_date.month
                    if self.season_code == 1: period_idx = 0
                    elif self.season_code == 4: period_idx = get_season(month) # 0-3
                    elif self.season_code == 12: period_idx = month - 1 # 0-11
                    else: period_idx = -1

                    if 0 <= period_idx < trend_rows:
                         period_value_idx = period_idx # Store valid index
                         # Increment day counters for this period
                         days_used_linear[period_value_idx] = days_used_linear.get(period_value_idx, 0) + 1
                         days_used_power[period_value_idx] = days_used_power.get(period_value_idx, 0) + 1
                         # Fetch trend params for this period, check validity
                         if self.beta_trend is not None and not np.isnan(self.beta_trend[period_value_idx, :]).any():
                             trend_params = self.beta_trend[period_value_idx, :]
                         # else: trend_params remains None if data missing

                    # else: period_value_idx remains -1 if month/season invalid


                # --- Read Predictor Data for the current day ---
                predictor_data = np.full(self.n_predictors, self.global_missing_code)
                missing_flag = False
                for i, f_handle in enumerate(predictor_file_handles):
                    line = f_handle.readline()
                    if not line: raise EOFError(f"Predictor {self.predictor_filenames[i+1]} ended at day {day_counter+1} ({current_date.strftime('%d/%m/%Y')}).")
                    try:
                        val = float(line.strip())
                        predictor_data[i] = val
                        # Check against global missing code
                        if abs(val - self.global_missing_code) < 1e-9: # Use tolerance for float comparison
                             missing_flag = True
                    except ValueError:
                        # Treat lines that cannot be converted to float as missing
                        predictor_data[i] = self.global_missing_code
                        missing_flag = True


                # --- Downscaling Algorithm ---
                # Reset daily predictions
                daily_prediction.fill(self.global_missing_code)

                if not missing_flag:
                    # Get parameters for the current month, checking validity
                    uncon_params_month = None
                    if self.uncon_parms is not None and self.uncon_parms.shape[0] > current_month_idx:
                        params = self.uncon_parms[current_month_idx, :]
                        # Check if essential params (intercept, SE) are valid
                        if not np.isnan(params[self.idx_b0_uncon]) and not np.isnan(params[self.idx_se_uncon]):
                             uncon_params_month = params
                             # Check AR param if needed
                             if self.auto_regression and np.isnan(params[self.idx_ar_uncon]):
                                  QMessageBox.warning(self, "Param Warning", f"Missing AR coeff for month {current_month_idx+1}. AR term skipped.")
                                  # Allow continuation, AR term will just be zero.
                        else: QMessageBox.warning(self,"Param Warning", f"Missing Uncon Intercept/SE for month {current_month_idx+1}. Skipping prediction for this month.")

                    con_params_month = None
                    if self.rain_yes:
                        if self.con_parms is not None and self.con_parms.shape[0] > current_month_idx:
                             params = self.con_parms[current_month_idx, :]
                             # Check essential conditional params
                             if not np.isnan(params[self.idx_b0_con]) and \
                                not np.isnan(params[self.idx_varinf_con]) and \
                                not np.isnan(params[self.idx_se_con]):
                                  con_params_month = params
                             else: QMessageBox.warning(self,"Param Warning", f"Missing Cond Intercept/VarInf/SE for month {current_month_idx+1}. Skipping conditional amount for this month.")
                        else: QMessageBox.warning(self,"Param Warning", f"Conditional params array invalid for month {current_month_idx+1}.")


                    lambda_params_month = None
                    if self.local_model_trans == 5:
                        if self.lamda_array is not None and self.lamda_array.shape[0] > current_month_idx:
                             params = self.lamda_array[current_month_idx, :]
                             if not np.isnan(params).any():
                                  lambda_params_month = params
                             else: QMessageBox.warning(self,"Param Warning", f"Missing BoxCox Lambda/Shift for month {current_month_idx+1}. BoxCox transform skipped.")
                        else: QMessageBox.warning(self,"Param Warning", f"Lambda array invalid for month {current_month_idx+1}.")

                    # === Ensemble Loop 1: Unconditional Pred + Wet/Dry Decision + AR Seed Update ===
                    # Only proceed if unconditional params are valid for the month
                    if uncon_params_month is not None:
                        for ens_idx in range(ensemble_size):
                            # --- Calculate Unconditional Base Prediction ---
                            # Y = b0 + b1*x1 + b2*x2 + ...
                            pred_uncon_base = uncon_params_month[self.idx_b0_uncon]
                            if self.n_predictors > 0:
                                pred_uncon_base += np.nansum(uncon_params_month[self.idx_b1_uncon:self.idx_se_uncon] * predictor_data)

                            # --- Autoregression Term ---
                            ar_term = 0.0
                            if self.auto_regression and self.idx_ar_uncon != -1 and not np.isnan(uncon_params_month[self.idx_ar_uncon]):
                                # Use seed if it's not the global missing code
                                if abs(auto_regression_seed[ens_idx] - self.global_missing_code) > 1e-9:
                                    ar_term = auto_regression_seed[ens_idx] * uncon_params_month[self.idx_ar_uncon]
                            pred_uncon_base += ar_term

                            # --- Residual Term (Stochasticity) ---
                            std_err_uncon = uncon_params_month[self.idx_se_uncon]
                            residual = 0.0
                            # Generate residual using direct normal (more accurate than VB approx)
                            # Ensure SE is positive before generating random number
                            if std_err_uncon > 1e-9: # Use tolerance
                                residual = np.random.normal(loc=0.0, scale=std_err_uncon)

                            # --- Final Unconditional Value OR Wet/Dry Probability ---
                            final_pred_value = pred_uncon_base # Start with AR-included base

                            if not self.rain_yes:
                                # Apply residual ONLY if unconditional process
                                final_pred_value += residual

                                # Apply Detrending ONLY if unconditional process & detrend active
                                if self.de_trend and period_value_idx != -1 and trend_params is not None:
                                    trend_adjustment = 0.0
                                    try:
                                        if self.de_trend_type == 1: # Linear
                                            trend_adjustment = trend_params[1] * days_used_linear[period_value_idx]
                                        else: # Power
                                            power_base = days_used_power[period_value_idx]
                                            # Avoid negative base for power if exponent is non-integer? VB didn't check. Assume positive days.
                                            if power_base >= 0:
                                                 trend_adjustment = (trend_params[0] * (power_base ** trend_params[1]))
                                                 trend_adjustment -= abs(trend_params[2]) # Subtract minimum (abs ensures subtraction)
                                                 trend_adjustment -= 0.001 # VB specific adjustment
                                            # else: skip trend if power base negative? Or take abs? VB likely assumed positive.
                                        final_pred_value += trend_adjustment
                                    except (OverflowError, ValueError) as trend_err:
                                         print(f"WARN: Detrend calculation error day {day_counter+1}: {trend_err}")
                                         # Continue without trend adjustment

                                # Apply constraints (e.g., non-negative) ONLY if unconditional final value
                                if not self.allow_neg and final_pred_value < 0:
                                     final_pred_value = 0.0

                                # Store final unconditional prediction
                                daily_prediction[ens_idx] = final_pred_value

                                # Update AR seed with the final value for next day
                                auto_regression_seed[ens_idx] = final_pred_value

                            else: # Conditional process: 'final_pred_value' is the probability
                                # --- Determine Wet/Dry Day Status ---
                                prob_wet = final_pred_value # Use the result from unconditional part (WITHOUT residual/detrend)
                                is_wet = False
                                if self.conditional_selection == 1: # Stochastic (VB: Rnd <= Pred)
                                    is_wet = (random.random() <= prob_wet)
                                else: # Fixed Threshold (VB: Pred >= Thresh)
                                    is_wet = (prob_wet >= self.conditional_thresh)

                                is_wet_status[ens_idx] = is_wet

                                # Update AR seed based on wet/dry status (0 or 1) for next day
                                auto_regression_seed[ens_idx] = 1.0 if is_wet else 0.0

                                # Store 0 for dry days now, amount calculated in next loop
                                if not is_wet:
                                     daily_prediction[ens_idx] = 0.0 # Use 0.0 for dry


                    # === Ensemble Loop 2: Calculate Amount for Wet Days (if Conditional) ===
                    if self.rain_yes and con_params_month is not None: # Check conditional params are valid
                         for ens_idx in range(ensemble_size):
                              # Only calculate amount if day was marked wet in Loop 1
                              if is_wet_status[ens_idx]:
                                   # --- Calculate Conditional Amount Base ---
                                   # Amount = c0 + c2*x2 + c3*x3 + ... (c1=VarInf used later)
                                   pred_amount_base = con_params_month[self.idx_b0_con]
                                   if self.n_predictors > 0:
                                       pred_amount_base += np.nansum(con_params_month[self.idx_b1_con:self.idx_se_con] * predictor_data)

                                   # --- Conditional Residual ---
                                   std_err_con = con_params_month[self.idx_se_con]
                                   residual_amount = 0.0
                                   if std_err_con > 1e-9:
                                       residual_amount = np.random.normal(loc=0.0, scale=std_err_con)

                                   # --- Combine Base and Residual ---
                                   pred_amount_combined = pred_amount_base + residual_amount

                                   # --- Apply Detrending to the COMBINED amount ---
                                   if self.de_trend and period_value_idx != -1 and trend_params is not None:
                                        trend_adjustment_cond = 0.0
                                        try:
                                            if self.de_trend_type == 1: # Linear
                                                trend_adjustment_cond = trend_params[1] * days_used_linear[period_value_idx]
                                            else: # Power
                                                power_base = days_used_power[period_value_idx]
                                                if power_base >= 0:
                                                    trend_adjustment_cond = (trend_params[0] * (power_base ** trend_params[1]))
                                                    trend_adjustment_cond -= abs(trend_params[2]) # Subtract minimum
                                                    trend_adjustment_cond -= 0.001
                                            pred_amount_combined += trend_adjustment_cond
                                        except (OverflowError, ValueError) as trend_err:
                                             print(f"WARN: Cond Detrend calculation error day {day_counter+1}: {trend_err}")


                                   # --- Apply Variance Inflation & Bias Correction (depends on ModelTrans) ---
                                   var_inf = con_params_month[self.idx_varinf_con]
                                   interim_val_for_transform = 0.0 # Value going into inverse transform

                                   # VB Logic: T1/T4 apply bias BEFORE transform step, T2/T3/T5 apply AFTER
                                   if self.local_model_trans == 1 or self.local_model_trans == 4:
                                       interim_val_for_transform = self.bias_correction * (var_inf * pred_amount_combined)
                                   else:
                                       interim_val_for_transform = var_inf * pred_amount_combined


                                   # --- Apply Inverse Transformation ---
                                   final_pred_amount = self.global_missing_code # Default to missing

                                   try:
                                       if self.local_model_trans == 1: # None
                                           final_pred_amount = interim_val_for_transform

                                       elif self.local_model_trans == 2: # Fourth Root -> Power 4
                                            # Need positive base for power > 1
                                            base_val = max(0, interim_val_for_transform)
                                            final_pred_amount = math.pow(base_val, 4.0)
                                            final_pred_amount *= self.bias_correction # Apply bias AFTER

                                       elif self.local_model_trans == 3: # Log (Natural) -> Exp
                                            # Clamp input to avoid huge numbers? VB doesn't seem to.
                                            try: final_pred_amount = math.exp(interim_val_for_transform)
                                            except OverflowError: final_pred_amount = float('inf') # Handle potential overflow
                                            final_pred_amount *= self.bias_correction # Apply bias AFTER

                                       elif self.local_model_trans == 4: # Inverse Normal -> Translator
                                            # Bias already applied in interim_val_for_transform
                                            final_pred_amount = self._translator_inv_norm(interim_val_for_transform)
                                            # No further bias needed here for T4

                                       elif self.local_model_trans == 5: # Box-Cox
                                           if lambda_params_month is not None:
                                               lamda = lambda_params_month[0]
                                               right_shift = lambda_params_month[1]
                                               # Add right shift *before* inverse transform logic (matching VB)
                                               val_to_transform = interim_val_for_transform + right_shift

                                               untransformed_val = self.global_missing_code
                                               if lamda == 0: # Log transform case Y' = ln(Y + shift)
                                                    try: untransformed_val = math.exp(val_to_transform) - right_shift
                                                    except OverflowError: untransformed_val = float('inf')
                                               else: # Power transform case Y' = ((Y + shift)^lambda - 1) / lambda
                                                    term = val_to_transform * lamda + 1.0
                                                    # Need term > 0 for power and log(term) later if derived that way
                                                    if term <= 1e-9: # Avoid non-positive base or issues near zero
                                                         untransformed_val = self.global_missing_code
                                                    else:
                                                         try: untransformed_val = math.pow(term, 1.0 / lamda) - right_shift
                                                         except ValueError: # e.g., negative base to fractional power
                                                              untransformed_val = self.global_missing_code
                                               final_pred_amount = untransformed_val
                                               # Apply bias AFTER inverse transform for BoxCox
                                               if final_pred_amount != self.global_missing_code and final_pred_amount != float('inf'):
                                                     final_pred_amount *= self.bias_correction
                                           else: # Missing lambda params
                                                final_pred_amount = self.global_missing_code

                                       # --- Final Threshold Check ---
                                       # Handle potential infinities from transforms
                                       if final_pred_amount == float('inf'):
                                           # What should happen? Missing code seems safest.
                                           final_pred_amount = self.global_missing_code
                                           print(f"WARN: Infinite value encountered day {day_counter+1}, ens {ens_idx+1}. Set to missing.")

                                       if final_pred_amount != self.global_missing_code:
                                           # Ensure result is at least threshold (VB: Thresh + 0.001)
                                           if final_pred_amount <= self.thresh:
                                                final_pred_amount = self.thresh + 0.001 # Match VB logic

                                   except (ValueError, OverflowError, TypeError) as transform_err:
                                       print(f"WARN: Transform Error day {day_counter+1}, ens {ens_idx+1}: {transform_err}, val={interim_val_for_transform}")
                                       final_pred_amount = self.global_missing_code # Set to missing on error

                                   # Store final conditional prediction amount
                                   daily_prediction[ens_idx] = final_pred_amount


                # --- Write Results for the Day ---
                # Format to 3 decimal places as in VB example
                output_line = "\t".join([f"{val:.3f}" if abs(val - self.global_missing_code) > 1e-9 else f"{self.global_missing_code:.0f}" for val in daily_prediction])
                out_file_handle.write(output_line + "\n")

                # --- Increment Date ---
                # Assumes standard Gregorian calendar as VB6 likely did
                current_date += datetime.timedelta(days=1)

            # --- End of Main Loop ---
            progress.setValue(current_progress + synthesis_length) # Mark completion

            # --- Create *.SIM File ---
            progress.setLabelText("Creating SIM file...")
            QApplication.processEvents()
            # Use known good values loaded from PAR or set by user where applicable
            with open(sim_file_path, 'w') as sim_f:
                 sim_f.write(f"{self.n_predictors}\n")
                 sim_f.write(f"{self.season_code}\n")
                 sim_f.write(f"{self.year_indicator}\n") # Use value from settings
                 # Re-read synthesis start date from UI field for SIM file
                 sim_start_date_str = self._parse_date(self.fStartText.text()).strftime('%d/%m/%Y')
                 sim_f.write(f"{sim_start_date_str}\n")
                 sim_f.write(f"{synthesis_length}\n")
                 sim_f.write(f"{self.rain_yes}\n") # Write True/False
                 sim_f.write(f"{ensemble_size}\n") # Use actual ensemble size used
                 sim_f.write(f"{self.prec_n}\n") # Variance Inflation N
                 sim_f.write(f"{self.local_model_trans}\n")
                 sim_f.write(f"{self.bias_correction}\n")
                 sim_f.write(f"{self.ptand_filename}\n")
                 # Write only predictor filenames (excluding predictand)
                 for fname in self.predictor_filenames[1:]:
                     sim_f.write(f"{fname}\n")

            QMessageBox.information(self, "Synthesis Complete",
                                f"Synthesis finished successfully.\n\nOutput: {self.out_file_path}\nSummary: {sim_file_path}")

        except FileNotFoundError as e: QMessageBox.critical(self, "File Error", f"Required file not found:\n{e}")
        except EOFError as e: QMessageBox.critical(self, "File Error", f"Unexpected end of input file encountered:\n{e}")
        except InterruptedError: QMessageBox.warning(self, "Cancelled", "Synthesis cancelled by user.")
        except IOError as e: QMessageBox.critical(self, "File I/O Error", f"Error reading/writing file:\n{e}")
        except MemoryError: QMessageBox.critical(self, "Memory Error", "Not enough memory to complete the operation.")
        except ValueError as e: QMessageBox.critical(self, "Data Error", f"Invalid data encountered during synthesis:\n{e}")
        except Exception as e:
            QMessageBox.critical(self, "Synthesis Error", f"An unexpected error occurred during synthesis:\n{e}\n\n{traceback.format_exc()}")
        finally:
            # --- Cleanup ---
            if out_file_handle and not out_file_handle.closed: out_file_handle.close()
            for f_handle in predictor_file_handles:
                if f_handle and not f_handle.closed: f_handle.close()
            if progress: progress.close() # Ensure progress dialog is closed

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
        self.inv_norm_first_value = -1
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
            # Use default start date from settings if available
            default_start = self.settings.get('globalSDate', "01/01/1961")
            self.fStartText.setText(default_start)
            self.fLengthText.setText("365") # Or consider using n_days_cal_par if PAR was loaded? No, reset fully.

            # Reset UI info labels
            self.predictorList.clear()
            self.no_of_pred_text.setText("0")
            self.auto_regress_label.setText("Unknown")
            self.process_label.setText("Unknown")
            self.r_start_text.setText("unknown")
            self.r_length_text.setText("unknown")


            # Clear all parsed PAR data and internal state
            self.reset_parsed_data()

            # QMessageBox.information(self, "Reset Complete", "All fields and internal states reset.")
        except Exception as e:
            QMessageBox.critical(self, "Reset Error", f"Error during reset: {str(e)}")


# --- Main Application Runner (Example) ---
if __name__ == '__main__':
    import sys

    # --- EXAMPLE: Define your settings dictionary here ---
    # This would typically be loaded from a config file or separate settings module
    app_settings = {
        # 'leapValue': 1, # Not directly used in SynthesizeData
        # 'yearLength': 1, # Not directly used in SynthesizeData (uses PAR value)
        'yearIndicator': 365, # Used for SIM file writing
        'globalSDate': "01/01/1961", # Default start date for UI
        # 'globalEDate': "31/12/1990", # Not used here
        # 'globalNDays': 0, # Not used here
        'allowNeg': True, # Allow negative values in unconditional non-precip?
        'randomSeed': False, # Use system time for seed? False uses fixed seed.
        'thresh': 0.0, # Threshold for precip amount / Inv Norm
        'defaultDir': os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data')), # Example default relative to script
        'globalMissingCode': -999.0, # Missing data code
        'varianceInflation': 12, # N value for VB6 residual approx (used in SIM writing, not calc) - Python uses direct normal
        'biasCorrection': 1.0, # Multiplicative bias correction factor
        'fixedThreshold': 0.5, # Threshold for conditional occurrence if 'Fixed'
        # 'modelTransformation': 'None', # Not used directly here (read from PAR)
        # 'optimizationAlgorithm': 'Ordinary Least Squares', # Not used here
        # 'criteriaType': 'AIC Criteria', # Not used here
        # 'stepwiseRegression': False, # Not used here
        'conditionalSelection': 'Stochastic', # 'Stochastic' or 'Fixed'
        # 'months': [0] * 12 # Not used here
    }
    # Ensure defaultDir exists, create if not (optional)
    if not os.path.exists(app_settings['defaultDir']):
         try:
             os.makedirs(app_settings['defaultDir'])
             print(f"Created default directory: {app_settings['defaultDir']}")
         except Exception as e:
             print(f"Warning: Could not create default directory: {e}")
             app_settings['defaultDir'] = os.path.expanduser("~") # Fallback to home
    elif not os.path.isdir(app_settings['defaultDir']):
         print(f"Warning: defaultDir '{app_settings['defaultDir']}' is not a directory. Falling back to home.")
         app_settings['defaultDir'] = os.path.expanduser("~") # Fallback to home
    # ---

    app = QApplication(sys.argv)
    mainWindow = QMainWindow()
    mainWindow.setWindowTitle("SDSM Synthesize Data (Python Conversion)")
    # Pass the settings to the widget
    contentWidget = ContentWidget(settings=app_settings)
    mainWindow.setCentralWidget(contentWidget)
    mainWindow.setGeometry(100, 100, 700, 800) # Adjusted size
    mainWindow.show()
    sys.exit(app.exec_())