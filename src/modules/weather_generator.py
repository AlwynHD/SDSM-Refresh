import os
import math
import random
import datetime
import calendar
import numpy as np
from scipy.stats import norm as scipy_norm
import traceback

from PyQt5.QtWidgets import (QVBoxLayout, QWidget, QHBoxLayout, QPushButton,
                             QFrame, QLabel, QLineEdit, QFileDialog, QGroupBox,
                             QGridLayout, QListWidget, QMessageBox, QProgressDialog, QApplication, QMainWindow)
from PyQt5.QtCore import Qt, QCoreApplication

# --- Helper Functions ---
def normal_pdf(x):
    """Calculate the probability density at point x for a standard normal distribution."""
    try:
        return scipy_norm.pdf(x)
    except Exception:
         # Handle extreme values that might cause calculation issues
         return 0.0

def get_season(month):
    """Convert month number to season index (0=Winter, 1=Spring, 2=Summer, 3=Autumn)."""
    if month in [12, 1, 2]: return 0  # Winter
    elif month in [3, 4, 5]: return 1  # Spring
    elif month in [6, 7, 8]: return 2  # Summer
    elif month in [9, 10, 11]: return 3  # Autumn
    else: raise ValueError(f"Invalid month: {month}")

def parse_fixed_width(line, width=14):
    """Parse a line of text containing fixed-width floating point numbers.
    
    Args:
        line: Text line containing the numbers
        width: Width of each number field (default: 14)
        
    Returns:
        List of parsed floating point values
    """
    values = []
    line_stripped = line.rstrip()
    line_len = len(line_stripped)
    
    for i in range(0, line_len, width):
        segment = line_stripped[i:min(i + width, line_len)].strip()
        if segment:  # Only process non-empty segments
            try:
                values.append(float(segment))
            except ValueError:
                # Handle non-numeric entries (e.g., "---")
                values.append(np.nan)
    return values

def shell_sort(arr):
    """Sort a list using Shell's method.
    
    This implementation matches the original algorithm used in the VB6 version
    to ensure consistent results when comparing outputs.
    """
    arr_copy = list(arr)  # Work on a copy to preserve the original
    n = len(arr_copy)
    gap = n // 2
    
    while gap > 0:
        for i in range(gap, n):
            temp = arr_copy[i]
            j = i
            while j >= gap and arr_copy[j - gap] > temp:
                arr_copy[j] = arr_copy[j - gap]
                j -= gap
            arr_copy[j] = temp
        gap //= 2
        
    return arr_copy

# --- Main Application Widget ---
class ContentWidget(QWidget):
    def __init__(self, settings=None):
        super().__init__()

        # --- Default Configuration Settings ---
        default_settings = {
            'allowNeg': True,             # Allow negative values in predictions
            'randomSeed': False,          # Use fixed random seed for reproducibility
            'thresh': 0.0,                # Threshold for precipitation events
            'globalMissingCode': -999.0,  # Value used to represent missing data
            'varianceInflation': 12,      # Controls randomness in predictions
            'biasCorrection': 1.0,        # Correction factor for predictions
            'fixedThreshold': 0.5,        # Threshold for fixed precipitation events
            'conditionalSelection': 'Stochastic',  # Method for wet/dry day selection
            'yearIndicator': 365,         # Days in year
            'globalSDate': "01/01/1961",  # Default start date
            'defaultDir': os.path.expanduser("~")  # Default directory
        }
        self.settings = settings if settings else default_settings

        # Load settings with proper type conversion
        self.allow_neg = bool(self.settings.get('allowNeg', True))
        self.use_random_seed = bool(self.settings.get('randomSeed', False))
        self.thresh = float(self.settings.get('thresh', 0.0))
        self.global_missing_code = float(self.settings.get('globalMissingCode', -999.0))
        self.prec_n = int(self.settings.get('varianceInflation', 12))
        self.bias_correction = float(self.settings.get('biasCorrection', 1.0))
        self.conditional_thresh = float(self.settings.get('fixedThreshold', 0.5))
        
        # Selection method: 1=Stochastic, 2=Fixed
        cond_sel_str = str(self.settings.get('conditionalSelection', 'Stochastic')).lower()
        self.conditional_selection = 1 if cond_sel_str == 'stochastic' else 2
        
        self.year_indicator = int(self.settings.get('yearIndicator', 365))
        self.default_dir = self.settings.get('defaultDir', os.path.expanduser("~"))

        # --- File paths ---
        self.par_file_path = ""
        self.predictor_dir = self.default_dir
        self.out_file_path = ""

        # --- Parameters from PAR file ---
        self.n_predictors = 0             # Number of predictor variables
        self.season_code = 0              # Time resolution (1=Annual, 4=Seasonal, 12=Monthly)
        self.year_length_par = 0          # Calendar type (360, 365, 366 days)
        self.start_date_par = None        # Record start date
        self.n_days_r_par = 0             # Record length in days
        self.cal_fs_date_par = None       # Calibration start date
        self.n_days_cal_par = 0           # Calibration length in days
        self.rain_yes = False             # True if this is a precipitation model
        self.local_model_trans = 0        # Transformation type (1=None, 2=4th Root, etc.)
        self.auto_regression = False      # Whether to use autoregression
        self.ptand_filename = ""          # Predictand filename
        self.predictor_filenames = []     # List of predictor filenames
        
        # Model parameters (to be loaded from PAR file)
        self.uncon_parms = None           # Unconditional model parameters by month
        self.con_parms = None             # Conditional model parameters by month
        self.lamda_array = None           # Box-Cox transformation parameters
        self.beta_trend = None            # Detrending parameters
        self.de_trend = False             # Whether detrending was applied
        self.de_trend_type = 0            # Detrending method (1=linear, 2=power)
        self.ptand_file_root = ""         # Path to predictand file
        
        # Inverse Normal Transform variables
        self.rank_data = []               # Sorted predictand data for transformation
        self.inv_norm_first_value_idx = -1  # Index of first value >= threshold
        self.inv_norm_n_split = 0         # Count of values >= threshold
        self.inv_norm_limit = 0.0         # Lower z-score bound
        self.inv_norm_total_area = 0.0    # Area between bounds
        
        # Parameter indices for model calculations
        self.idx_b0_uncon = -1            # Intercept index
        self.idx_b1_uncon = -1            # First predictor coefficient index
        self.idx_se_uncon = -1            # Standard error index
        self.idx_ar_uncon = -1            # Autoregression coefficient index
        self.idx_lambda = -1              # Box-Cox lambda parameter index
        self.idx_rshift = -1              # Box-Cox right shift index
        self.idx_b0_con = -1              # Conditional intercept index
        self.idx_varinf_con = -1          # Variance inflation index
        self.idx_b1_con = -1              # First conditional coefficient index
        self.idx_se_con = -1              # Conditional standard error index
        
        # Operation state
        self._cancel_synthesis = False

        # --- Set up the user interface ---
        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(10, 10, 10, 10)
        mainLayout.setSpacing(10)
        self.setLayout(mainLayout)

        # File Selection Section
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
        fileSelectionLayout.addWidget(self.par_file_text, 0, 1, 1, 2)
        fileSelectionLayout.addWidget(self.outFileButton, 1, 0)
        fileSelectionLayout.addWidget(self.outFileText, 1, 1, 1, 2)
        fileSelectionLayout.addWidget(self.simLabel, 2, 1, 1, 2)

        # Predictor Directory Section
        predictorDirGroup = QGroupBox("Predictor Data Directory")
        predictorDirLayout = QGridLayout()
        predictorDirGroup.setLayout(predictorDirLayout)
        mainLayout.addWidget(predictorDirGroup)

        self.dirButton = QPushButton("📁 Select Directory Containing Predictor Files")
        self.dirButton.clicked.connect(self.selectPredictorDirectory)
        self.dirText = QLabel(self.predictor_dir)
        self.dirText.setWordWrap(True)

        predictorDirLayout.addWidget(self.dirButton, 0, 0)
        predictorDirLayout.addWidget(self.dirText, 0, 1)

        # Data Section
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
        self.predictorList.setMaximumHeight(150)
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

        # Ensemble Size Section
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

        # Buttons
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

    def selectPredictorDirectory(self):
        """Open a directory dialog to select where the predictor files are located."""
        directory = QFileDialog.getExistingDirectory(self, "Select Predictor Directory", self.predictor_dir or os.path.expanduser("~"))
        if directory:
            self.predictor_dir = directory
            self.dirText.setText(directory)
            if self.par_file_path:
                 self.viewPredictors()

    def _parse_date(self, date_str):
        """Parse a date string in various formats into a datetime.date object.
        
        Attempts multiple formats including dd/mm/yyyy, mm/dd/yyyy, and others
        that may appear in input files.
        """
        # Handle cases where it might already be a date object
        if isinstance(date_str, datetime.date):
            return date_str
        if isinstance(date_str, datetime.datetime):
            return date_str.date()

        # Try different date formats
        date_str = str(date_str).strip()
        for fmt in ('%d/%m/%Y', '%m/%d/%Y'):
            try:
                return datetime.datetime.strptime(date_str, fmt).date()
            except ValueError:
                pass
                
        # Try other possible formats
        try:
            return datetime.datetime.strptime(date_str, '%d-%b-%Y').date()
        except ValueError:
             pass
        try:
            return datetime.datetime.strptime(date_str, '%m-%d-%Y').date()
        except ValueError:
             pass
             
        raise ValueError(f"Date format not recognized: {date_str}")

    def loadPARFile(self, file_path):
        """Load and parse a parameter (PAR) file.
        
        The PAR file contains model parameters and configuration details
        needed for the weather generation process.
        """
        self.reset_parsed_data()
        self.par_file_path = file_path
        self.par_file_text.setText(f"{os.path.basename(file_path)}")

        try:
            with open(file_path, 'r') as par_file:
                lines = [line.strip() for line in par_file]

            line_idx = 0
            def get_line(allow_empty=False):
                """Get the next non-empty line from the file."""
                nonlocal line_idx
                while line_idx < len(lines):
                    line = lines[line_idx]
                    line_idx += 1
                    if line or allow_empty:
                        return line
                raise EOFError("Unexpected end of PAR file.")

            # --- Read Header Information ---
            # Number of predictors (negative indicates detrending was applied)
            n_pred_raw_str = get_line()
            n_pred_raw = int(n_pred_raw_str)
            self.de_trend = n_pred_raw < 0
            self.n_predictors = abs(n_pred_raw)
            self.no_of_pred_text.setText(str(self.n_predictors))

            # Time resolution and calendar settings
            self.season_code = int(get_line())      # 1=Annual, 4=Seasonal, 12=Monthly
            self.year_length_par = int(get_line())  # Days in year (360, 365, or 366)
            
            # Date information
            record_start_str = get_line()
            self.start_date_par = self._parse_date(record_start_str)
            self.r_start_text.setText(self.start_date_par.strftime('%d/%m/%Y'))
            
            self.n_days_r_par = int(get_line())     # Record length in days
            self.r_length_text.setText(str(self.n_days_r_par))
            
            cal_fs_date_str = get_line()            # Calibration start date
            self.cal_fs_date_par = self._parse_date(cal_fs_date_str)
            
            # Set default synthesis settings based on calibration
            self.fStartText.setText(self.cal_fs_date_par.strftime('%d/%m/%Y'))
            
            self.n_days_cal_par = int(get_line())   # Calibration length in days
            self.fLengthText.setText(str(self.n_days_cal_par))

            # Process type (conditional or unconditional)
            rain_yes_str = get_line()
            cleaned_rain_yes = rain_yes_str.strip('#" ').upper()
            self.rain_yes = cleaned_rain_yes == "TRUE"
            self.process_label.setText("Conditional" if self.rain_yes else "Unconditional")

            # Model configuration
            self.local_model_trans = int(get_line())  # Transformation type
            _ = int(get_line())  # Ensemble size from PAR (we'll use UI value instead)

            # Handle different PAR file format versions
            potential_ar_or_ptand = get_line()
            if potential_ar_or_ptand.upper() in ["TRUE", "FALSE"]:  # Newer format
                self.auto_regression = potential_ar_or_ptand.upper() == "TRUE"
                self.ptand_filename = get_line()  # Read predictand filename next
            else:  # Older format where line is already the predictand filename
                self.auto_regression = False
                self.ptand_filename = potential_ar_or_ptand

            self.auto_regress_label.setText(str(self.auto_regression))

            # --- Read Predictor Filenames ---
            self.predictor_filenames = []
            self.predictor_filenames.append(self.ptand_filename)  # Predictand is first
            
            for _ in range(self.n_predictors):
                pred_fname = get_line(allow_empty=True).strip()
                self.predictor_filenames.append(pred_fname)

            # --- Determine Parameter Indices Based on Model Configuration ---
            # Set up indices for accessing model parameters in arrays
            self.idx_b0_uncon = 0  # Intercept
            self.idx_b1_uncon = 1  # First predictor coefficient
            self.idx_se_uncon = 1 + self.n_predictors  # Standard error after all coefficients
            current_uncon_idx = self.idx_se_uncon  # Last assigned index

            # Add autoregression parameter if needed
            if self.auto_regression:
                current_uncon_idx += 1
                self.idx_ar_uncon = current_uncon_idx
            else:
                self.idx_ar_uncon = -1

            # Add Box-Cox parameters if that transformation is used
            if self.local_model_trans == 5:  # Box-Cox
                current_uncon_idx += 1
                self.idx_lambda = current_uncon_idx
                current_uncon_idx += 1
                self.idx_rshift = current_uncon_idx
            else:
                self.idx_lambda = -1
                self.idx_rshift = -1

            # Total parameters per month
            param_count_uncon = current_uncon_idx + 1

            # --- Read Unconditional Model Parameters ---
            # Each month has a set of parameters
            self.uncon_parms = np.full((12, param_count_uncon), np.nan)
            if self.local_model_trans == 5:
                self.lamda_array = np.full((12, 2), np.nan)

            # Number of parameters in fixed-width part
            params_in_fixed_width_uncon = param_count_uncon
            if self.local_model_trans == 5:
                params_in_fixed_width_uncon -= 2  # Lambda/Shift are appended separately

            for i in range(12):  # For each month
                param_line = get_line()
                # Parse parameters using fixed width format
                params_parsed = parse_fixed_width(param_line, 14)

                # Assign the fixed-width parameters
                num_to_assign_fixed = min(len(params_parsed), params_in_fixed_width_uncon)
                self.uncon_parms[i, :num_to_assign_fixed] = params_parsed[:num_to_assign_fixed]

                # Extract Box-Cox parameters if needed
                if self.local_model_trans == 5:
                    if len(params_parsed) > params_in_fixed_width_uncon:
                         lambda_val = params_parsed[params_in_fixed_width_uncon]
                         self.lamda_array[i, 0] = lambda_val
                         self.uncon_parms[i, self.idx_lambda] = lambda_val
                    if len(params_parsed) > params_in_fixed_width_uncon + 1:
                         rshift_val = params_parsed[params_in_fixed_width_uncon + 1]
                         self.lamda_array[i, 1] = rshift_val
                         self.uncon_parms[i, self.idx_rshift] = rshift_val

            # --- Read Conditional Model Parameters (for precipitation models) ---
            if self.rain_yes:
                # Set up indices for conditional parameters
                self.idx_b0_con = 0       # Intercept
                self.idx_varinf_con = 1   # Variance inflation factor
                self.idx_b1_con = 2       # First predictor coefficient
                self.idx_se_con = 2 + self.n_predictors  # Standard error
                param_count_con = self.idx_se_con + 1

                self.con_parms = np.full((12, param_count_con), np.nan)
                for i in range(12):  # For each month
                    param_line = get_line()
                    params_parsed = parse_fixed_width(param_line, 14)
                    num_to_assign = min(len(params_parsed), param_count_con)
                    self.con_parms[i, :num_to_assign] = params_parsed[:num_to_assign]

            # --- Read Predictand File Path ---
            self.ptand_file_root = get_line().strip()

            # --- Read Detrending Parameters (if applicable) ---
            if self.de_trend:
                self.de_trend_type = int(get_line())  # 1=linear, 2=power
                
                # Number of parameters depends on detrending method
                n_trend_params = 2 if self.de_trend_type == 1 else 3

                # Number of parameter sets depends on season_code
                trend_rows = self.season_code
                if trend_rows not in [1, 4, 12]:
                    raise ValueError(f"Unsupported SeasonCode for Detrend: {self.season_code}")

                self.beta_trend = np.full((trend_rows, n_trend_params), np.nan)
                for i in range(trend_rows):
                     p1 = float(get_line())
                     p2 = float(get_line())
                     self.beta_trend[i, 0] = p1
                     self.beta_trend[i, 1] = p2
                     if self.de_trend_type == 2:  # Power function needs a third parameter
                        p3 = float(get_line())
                        self.beta_trend[i, 2] = p3

            # --- Post-Load Actions ---
            par_dir = os.path.dirname(file_path)
            # If predictor directory not set, use PAR file's directory
            if not self.predictor_dir or not os.path.isdir(self.predictor_dir):
                 self.predictor_dir = par_dir
                 self.dirText.setText(par_dir)
            self.viewPredictors()  # Check if predictor files exist

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
        """Open a file dialog to browse for and select a parameter (PAR) file."""
        start_dir = self.predictor_dir if os.path.isdir(self.predictor_dir) else self.default_dir
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Parameter File", start_dir, "PAR Files (*.par *.PAR);;All Files (*.*)")
        if file_name:
            self.loadPARFile(file_name)

    def selectOutputFile(self):
        """Open a file dialog to choose where to save the output data."""
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
            # Ensure proper extension
            if not file_name.upper().endswith(".OUT"):
                 file_name += ".OUT"
            self.out_file_path = file_name
            self.outFileText.setText(os.path.basename(file_name))

    def viewPredictors(self):
        """Check if all predictor files exist and display their status in the UI."""
        self.predictorList.clear()

        if not self.par_file_path: return
        if not self.predictor_dir or not os.path.isdir(self.predictor_dir):
             QMessageBox.warning(self, "No Predictor Directory", "Please select a valid predictor directory.")
             return
        if not self.predictor_filenames:
             if self.ptand_filename:
                 self.predictorList.addItem(f"Predictand: {self.ptand_filename} (No predictors)")
             return

        missing_files = []
        found_files = []
        display_warning = False

        for i, filename in enumerate(self.predictor_filenames):
            prefix = "Predictand: " if i == 0 else f"Predictor {i}: "
            if not filename:
                self.predictorList.addItem(f"⚠️ {prefix}(Empty Filename in PAR!)")
                if i > 0 and self.n_predictors > 0: display_warning = True
                continue

            full_path = os.path.join(self.predictor_dir, filename)
            if not os.path.exists(full_path):
                missing_files.append(filename)
                self.predictorList.addItem(f"⚠️ {prefix}{filename} (Missing!)")
                display_warning = True
            else:
                found_files.append(filename)
                self.predictorList.addItem(f"✅ {prefix}{filename}")

        if display_warning:
            missing_list = "\n- ".join(missing_files) if missing_files else "None"
            QMessageBox.warning(self, "File Verification Issues",
                            f"Issues found with files listed in PAR relative to directory:\n'{self.predictor_dir}'\n\nMissing Files:\n- {missing_list}\n\nPlease select the correct directory or check the PAR file contents.")

    def _prepare_inverse_normal(self):
        """Prepare data for Inverse Normal transformation.
        
        This reads the original predictand data, sorts it, and calculates
        parameters needed for applying the transformation during synthesis.
        """
        self.rank_data = []
        self.inv_norm_first_value_idx = -1
        self.inv_norm_n_split = 0
        self.inv_norm_limit = 0.0
        self.inv_norm_total_area = 0.0

        if not self.ptand_file_root:
             raise ValueError("Predictand file root path missing in PAR (required for Inv Normal).")

        # Find the predictand file path
        if os.path.isabs(self.ptand_file_root):
            ptand_path = self.ptand_file_root
        else:
            par_dir = os.path.dirname(self.par_file_path) if self.par_file_path else self.predictor_dir
            ptand_path = os.path.join(par_dir, self.ptand_file_root)

        if not os.path.exists(ptand_path):
             # Try alternate location
             ptand_path_alt = os.path.join(self.predictor_dir, os.path.basename(self.ptand_file_root))
             if os.path.exists(ptand_path_alt):
                 ptand_path = ptand_path_alt
             else:
                 raise FileNotFoundError(f"Predictand file for Inv Normal not found.\nChecked PAR path: {ptand_path}\nChecked Predictor path: {ptand_path_alt}")

        try:
            # --- Read predictand data from the calibration period ---
            read_values = []
            line_count = 0
            cal_start_line = -1
            cal_end_line = -1

            # Calculate which lines correspond to the calibration period
            if self.start_date_par and self.cal_fs_date_par:
                 days_to_skip_cal = (self.cal_fs_date_par - self.start_date_par).days
                 if days_to_skip_cal < 0:
                      print(f"Warning: Calibration start date ({self.cal_fs_date_par}) is before record start date ({self.start_date_par}). Assuming skip count is 0.")
                      days_to_skip_cal = 0

                 cal_start_line = days_to_skip_cal
                 cal_end_line = cal_start_line + self.n_days_cal_par
            else:
                 raise ValueError("Record Start Date or Calibration Fit Start Date not available from PAR for Inv Normal.")

            print(f"DEBUG InvNorm: Reading predictand '{os.path.basename(ptand_path)}' from line {cal_start_line+1} to {cal_end_line}.")

            with open(ptand_path, 'r') as f_ptand:
                for i, line in enumerate(f_ptand):
                    line_count = i
                    if cal_start_line <= i < cal_end_line:
                        try:
                            val = float(line.strip())
                            # Include all valid values except missing codes
                            if abs(val - self.global_missing_code) > 1e-9:
                                 read_values.append(val)
                        except ValueError:
                            print(f"Warning: Skipping non-numeric value in predictand file {os.path.basename(ptand_path)} at line {i+1}: '{line.strip()}'")
                            pass
                    elif i >= cal_end_line:
                        break  # Stop once we've read enough lines

            if line_count < cal_end_line - 1:
                 QMessageBox.warning(self, "Data Warning", f"Predictand file {os.path.basename(ptand_path)} for Inv Normal may have ended prematurely.\nExpected data until line {cal_end_line}, read {line_count+1} lines.")

            if not read_values:
                 raise ValueError(f"No valid numeric data (excluding missing code {self.global_missing_code}) found in predictand file {os.path.basename(ptand_path)} for the calibration period (lines {cal_start_line+1} to {cal_end_line}). Cannot perform Inverse Normal transform.")

            # --- Sort the data for lookup during transformation ---
            self.rank_data = shell_sort(read_values)

            # --- Find the first value above threshold ---
            self.inv_norm_first_value_idx = -1
            for i, val in enumerate(self.rank_data):
                if val > self.thresh:
                    self.inv_norm_first_value_idx = i
                    break

            # Handle case where no value is strictly greater than threshold
            if self.inv_norm_first_value_idx == -1:
                 found_at_thresh = False
                 for i, val in enumerate(self.rank_data):
                      if abs(val - self.thresh) < 1e-9:  # Check for equality
                           self.inv_norm_first_value_idx = i
                           found_at_thresh = True
                           print(f"Warning: No data strictly > threshold ({self.thresh}) for Inv Normal. Using first value >= threshold at index {i}.")
                           break
                 if not found_at_thresh:
                      raise ValueError(f"No data >= threshold ({self.thresh}) found in predictand file for calibration period. Cannot perform Inverse Normal transform.")

            # --- Calculate split point and other parameters ---
            self.inv_norm_n_split = len(self.rank_data) - self.inv_norm_first_value_idx
            if self.inv_norm_n_split <= 0:
                 raise ValueError(f"Inverse Normal nSplit calculation resulted in {self.inv_norm_n_split} (<= 0).\n"
                                  f"Total valid data points = {len(self.rank_data)}\n"
                                  f"Index of first value >= threshold ({self.thresh}) = {self.inv_norm_first_value_idx}\n"
                                  "Check threshold value and predictand data for calibration period.")

            print(f"DEBUG InvNorm: NRankData={len(self.rank_data)}, Thresh={self.thresh}, FirstValueIdx={self.inv_norm_first_value_idx}, FirstValue={self.rank_data[self.inv_norm_first_value_idx]:.4f}, nSplit={self.inv_norm_n_split}")

            # --- Find the z-score limit (used to scale normal distribution) ---
            z_start = 1.0 / (self.inv_norm_n_split + 1.0)  # Probability in lower tail
            delta = 0.0001  # Step size for search
            area = 0.5      # Start from middle of distribution
            fx = 0.0        # Starting z-score
            fx_old_pdf = normal_pdf(fx)
            self.inv_norm_limit = np.nan

            # Search for z-score that gives desired tail area
            search_success = False
            for _ in range(50000):  # Limit iterations to prevent infinite loop
                fx -= delta  # Move left in the distribution
                fx_new_pdf = normal_pdf(fx)
                # Calculate area removed from this step
                area -= (delta * 0.5 * (fx_old_pdf + fx_new_pdf))
                # Stop when we reach the target area
                if area <= z_start:
                    self.inv_norm_limit = fx
                    search_success = True
                    break
                fx_old_pdf = fx_new_pdf

            if not search_success:
                QMessageBox.warning(self, "Inv Normal Warning", f"Could not accurately find lower limit Z-score for P={z_start:.4f} within 50k iterations. Search stopped at Z={fx:.4f} with Area={area:.4f}. Using this Z as limit.")
                self.inv_norm_limit = fx
                if area > z_start:
                     print(f"WARN: Inv Norm limit search failed. Area {area:.6f} > zStart {z_start:.6f}. Limit set to {self.inv_norm_limit:.6f}")

            # Calculate total area for scaling
            self.inv_norm_total_area = max(0.0, 1.0 - (2.0 * z_start))
            if self.inv_norm_total_area <= 1e-9:
                 QMessageBox.warning(self,"Inv Normal Warning", f"Total Area for Inv Norm scaling is near zero ({self.inv_norm_total_area:.2e}). nSplit={self.inv_norm_n_split}. Check threshold/data.")
                 if self.inv_norm_total_area <= 0: self.inv_norm_total_area = 1e-9

            print(f"DEBUG InvNorm: zStart={z_start:.6f}, limit={self.inv_norm_limit:.6f}, totalArea={self.inv_norm_total_area:.6f}")

        except Exception as e:
            raise IOError(f"Error processing predictand file '{ptand_path}' for Inverse Normal Transform:\n{e}\n{traceback.format_exc()}")

    def _translator_inv_norm(self, passed_value):
        """Apply the Inverse Normal transformation to convert a z-score to a data value.
        
        Args:
            passed_value: Z-score to transform
            
        Returns:
            Transformed value based on the original data distribution
        """
        # Check if transformation parameters are ready
        if not self.rank_data or self.inv_norm_first_value_idx < 0 or self.inv_norm_first_value_idx >= len(self.rank_data) or self.inv_norm_n_split <= 0:
            print(f"ERROR: Translator called with invalid state: nRank={len(self.rank_data)}, firstVIdx={self.inv_norm_first_value_idx}, nSplit={self.inv_norm_n_split}")
            return self.global_missing_code

        # Handle z-scores below the lower limit
        if passed_value <= self.inv_norm_limit:
            return self.rank_data[self.inv_norm_first_value_idx]

        # Calculate area under normal curve from limit to passed_value
        interval = (passed_value - self.inv_norm_limit) / 100.0
        if abs(interval) < 1e-15: return self.rank_data[self.inv_norm_first_value_idx]

        area_from_limit = 0.0
        fx = self.inv_norm_limit
        try:
            fx_old_pdf = normal_pdf(fx)
        except Exception: fx_old_pdf = 0.0

        # Integrate the normal PDF using trapezoidal rule
        for _ in range(100):
            fx += interval
            try:
                fx_new_pdf = normal_pdf(fx)
            except Exception: fx_new_pdf = 0.0
            area_from_limit += (interval * 0.5 * (fx_old_pdf + fx_new_pdf))
            fx_old_pdf = fx_new_pdf

        # Ensure area is within bounds
        area_from_limit = min(area_from_limit, self.inv_norm_total_area)
        area_from_limit = max(0.0, area_from_limit)

        # Convert area to an index in the sorted data
        if self.inv_norm_total_area <= 1e-9:
            index_offset_float = 0.0
        else:
            index_offset_float = (area_from_limit / self.inv_norm_total_area) * self.inv_norm_n_split

        # Calculate final lookup index
        locate_index_offset = math.floor(index_offset_float)
        locate_index = self.inv_norm_first_value_idx + locate_index_offset

        # Ensure index is within valid range
        max_allowable_index = self.inv_norm_first_value_idx + self.inv_norm_n_split - 1
        max_allowable_index = min(max_allowable_index, len(self.rank_data) - 1)

        if locate_index >= max_allowable_index:
            locate_index = max_allowable_index

        locate_index = max(locate_index, self.inv_norm_first_value_idx)

        # Return the value at the calculated index
        if self.inv_norm_first_value_idx <= locate_index < len(self.rank_data):
            return self.rank_data[locate_index]
        else:
            print(f"WARN: Translator index {locate_index} out of bounds [{self.inv_norm_first_value_idx}-{max_allowable_index}]. Z={passed_value}, Area={area_from_limit:.4f}, OffsetF={index_offset_float:.4f}, OffsetI={locate_index_offset}")
            if passed_value <= self.inv_norm_limit:
                return self.rank_data[self.inv_norm_first_value_idx]
            else:
                 safe_max_idx = min(max_allowable_index, len(self.rank_data) - 1)
                 if safe_max_idx >= 0:
                      return self.rank_data[safe_max_idx]
                 else:
                      return self.global_missing_code

    def synthesizeData(self):
        """Generate synthetic weather data based on the loaded model parameters.
        
        This is the main function that performs the weather generation process,
        reading predictor data and applying statistical relationships to 
        generate the synthetic time series.
        """
        self._cancel_synthesis = False

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
            # Get and validate synthesis settings from UI
            ensemble_size = int(self.eSize.text())
            if not 1 <= ensemble_size <= 100:
                QMessageBox.warning(self, "Invalid Input", "Ensemble size must be between 1 and 100.")
                return

            synthesis_start_date = self._parse_date(self.fStartText.text())

            synthesis_length = int(self.fLengthText.text())
            if synthesis_length < 1:
                QMessageBox.warning(self, "Invalid Input", "Synthesis length must be at least 1 day.")
                return

            # Optional date checks
            if self.start_date_par and synthesis_start_date < self.start_date_par:
                 print(f"Warning: Synthesis start date ({synthesis_start_date}) is before the Record start date ({self.start_date_par}) defined in the PAR file.")

        except ValueError as e:
            QMessageBox.critical(self, "Invalid Input", f"Error in synthesis settings:\n{e}\n\nPlease check dates (dd/mm/yyyy or mm/dd/yyyy) and numbers.")
            return
        except Exception as e:
             QMessageBox.critical(self, "Input Error", f"Error processing inputs: {e}")
             return

        # --- Setup output files ---
        sim_file_path = os.path.splitext(self.out_file_path)[0] + ".SIM"

        # --- Set random seed for reproducibility ---
        if not self.use_random_seed:
             random.seed(1)
             print("DEBUG: Using fixed Python random seed (1) for repeatability. NOTE: Sequence differs from VB6.")
        else:
             random.seed()
             print("DEBUG: Using system random seed (non-repeatable).")

        # --- Configure progress dialog ---
        init_steps = 3
        skip_days = max(0, (synthesis_start_date - self.start_date_par).days if self.start_date_par else 0)
        total_prog_steps = init_steps + skip_days + synthesis_length + 1
        progress = QProgressDialog("Initializing Synthesis...", "Cancel", 0, total_prog_steps, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setWindowTitle("Processing")
        progress.setValue(0)
        QCoreApplication.processEvents()

        # --- Main Processing Variables ---
        predictor_file_handles = []
        out_file_handle = None
        current_progress = 0

        try:
            progress.show()
            QCoreApplication.processEvents()

            # --- Prepare Inverse Normal transformation if needed ---
            if self.local_model_trans == 4:  # Inverse Normal
                 progress.setLabelText("Preparing Inverse Normal data...")
                 progress.setValue(current_progress); current_progress += 1
                 QCoreApplication.processEvents()
                 if progress.wasCanceled(): raise InterruptedError("Cancelled")
                 self._prepare_inverse_normal()

            # --- Open predictor data files ---
            progress.setLabelText("Opening predictor files...")
            progress.setValue(current_progress); current_progress += 1
            QCoreApplication.processEvents()
            if progress.wasCanceled(): raise InterruptedError("Cancelled")

            # Open each predictor file (skip predictand at index 0)
            predictor_files_to_open = self.predictor_filenames[1:]
            if len(predictor_files_to_open) != self.n_predictors:
                 actual_files_in_list = len([f for f in predictor_files_to_open if f])
                 if actual_files_in_list == self.n_predictors:
                     print(f"Warning: Number of non-empty predictor filenames ({actual_files_in_list}) matches NPredictors ({self.n_predictors}).")
                 elif len(self.predictor_filenames) == self.n_predictors + 1:
                     print(f"Warning: Total filenames in list ({len(self.predictor_filenames)-1}) matches NPredictors ({self.n_predictors}), but some might be empty/invalid.")
                 else:
                     raise ValueError(f"Mismatch: Expected {self.n_predictors} predictors, found {len(predictor_files_to_open)} filename entries in list after predictand.")

            for i in range(self.n_predictors):
                predictor_idx_in_list = i + 1
                filename = self.predictor_filenames[predictor_idx_in_list] if predictor_idx_in_list < len(self.predictor_filenames) else None

                if not filename:
                     predictor_file_handles.append(None)
                     print(f"Warning: Skipping empty predictor filename entry for predictor {i+1}.")
                     continue
                filepath = os.path.join(self.predictor_dir, filename)
                if not os.path.exists(filepath):
                     raise FileNotFoundError(f"Predictor file not found: {filepath}")
                try:
                    predictor_file_handles.append(open(filepath, 'r'))
                except Exception as e:
                    raise IOError(f"Error opening predictor file {filepath}: {e}")

            # --- Open output file ---
            try:
                out_file_handle = open(self.out_file_path, 'w')
            except Exception as e:
                raise IOError(f"Error opening output file {self.out_file_path} for writing: {e}")

            # --- Initialize detrending variables ---
            days_used_linear = {}  # Days from calibration start date
            days_used_power = {}   # Days from record start date
            cal_fs_date_baseline_days = {}  # Day counts up to calibration date
            fs_date_baseline_days = {}      # Day counts up to synthesis date
            trend_rows_beta = 0  # Number of period rows for detrending

            if self.de_trend:
                progress.setLabelText("Initializing detrend variables...")
                progress.setValue(current_progress); current_progress += 1
                QCoreApplication.processEvents()
                if progress.wasCanceled(): raise InterruptedError("Cancelled")

                if self.beta_trend is None: raise ValueError("Detrending enabled but BetaTrend parameters not loaded.")
                trend_rows_beta = self.beta_trend.shape[0]
                if trend_rows_beta != self.season_code:
                    print(f"Warning: Mismatch between SeasonCode ({self.season_code}) and loaded BetaTrend rows ({trend_rows_beta}). Using {trend_rows_beta} rows.")

                # Calculate baseline day counts up to calibration start date
                current_d_cal = self.start_date_par
                days_diff_cal = 0
                if self.start_date_par and self.cal_fs_date_par:
                     days_diff_cal = max(0, (self.cal_fs_date_par - self.start_date_par).days)

                # Initialize counts for each period
                for period_idx in range(trend_rows_beta):
                    cal_fs_date_baseline_days[period_idx] = 0

                # Count days by period up to calibration start
                for _ in range(days_diff_cal):
                    month = current_d_cal.month
                    period_idx = -1
                    if self.season_code == 1: period_idx = 0  # Annual
                    elif self.season_code == 4: period_idx = get_season(month)  # Seasonal
                    elif self.season_code == 12: period_idx = month - 1  # Monthly

                    if 0 <= period_idx < trend_rows_beta:
                         cal_fs_date_baseline_days[period_idx] = cal_fs_date_baseline_days.get(period_idx, 0) + 1
                    else:
                         print(f"Warning: Skipping detrend baseline count for date {current_d_cal}, invalid period index {period_idx} for trend rows {trend_rows_beta}")

                    # Move to next day
                    try:
                        current_d_cal += datetime.timedelta(days=1)
                    except OverflowError:
                        raise ValueError("Date overflow during detrend baseline calculation. Check dates.")

            # --- Skip initial data to reach synthesis start date ---
            progress.setLabelText("Skipping initial predictor data...")
            progress.setValue(current_progress)
            QCoreApplication.processEvents()

            days_to_skip = 0
            if self.start_date_par and synthesis_start_date > self.start_date_par:
                days_to_skip = max(0, (synthesis_start_date - self.start_date_par).days)

            current_d_skip = self.start_date_par if self.start_date_par else None

            # Initialize detrending counters for power function
            for period_idx in range(trend_rows_beta if self.de_trend else 0):
                days_used_power[period_idx] = 0
                fs_date_baseline_days[period_idx] = 0

            # Skip lines in input files
            for day_skip_idx in range(days_to_skip):
                 if progress.wasCanceled(): raise InterruptedError("Cancelled")
                 progress.setValue(current_progress + day_skip_idx + 1)
                 if day_skip_idx % 100 == 0: QCoreApplication.processEvents()

                 # Skip one line in each predictor file
                 for i, f_handle in enumerate(predictor_file_handles):
                      if f_handle is not None:
                           line = f_handle.readline()
                           if not line:
                                filename_for_error = f"(Predictor {i+1})"
                                if (i+1) < len(self.predictor_filenames):
                                    filename_for_error = self.predictor_filenames[i+1] or f"(Predictor {i+1} - empty name)"
                                raise EOFError(f"Predictor file '{filename_for_error}' ended prematurely during initial skip at day {day_skip_idx+1} (Date: {current_d_skip.strftime('%d/%m/%Y') if current_d_skip else 'N/A'}).")

                 # Update detrending counters for skipped days
                 if self.de_trend and current_d_skip:
                      month = current_d_skip.month
                      period_idx = -1
                      if self.season_code == 1: period_idx = 0
                      elif self.season_code == 4: period_idx = get_season(month)
                      elif self.season_code == 12: period_idx = month - 1

                      if 0 <= period_idx < trend_rows_beta:
                          fs_date_baseline_days[period_idx] = fs_date_baseline_days.get(period_idx, 0) + 1
                          days_used_power[period_idx] = fs_date_baseline_days[period_idx]

                 # Move to next day
                 if current_d_skip:
                      try:
                          current_d_skip += datetime.timedelta(days=1)
                      except OverflowError:
                          raise ValueError("Date overflow during initial data skipping. Check dates.")

            # Update progress after skipping
            current_progress += days_to_skip

            # --- Initialize simulation state ---
            current_date = synthesis_start_date
            start_month_idx = synthesis_start_date.month - 1

            # Initialize autoregression seed value
            initial_intercept = 0.0
            if self.uncon_parms is not None and 0 <= start_month_idx < 12 and self.idx_b0_uncon != -1:
                 intercept_val = self.uncon_parms[start_month_idx, self.idx_b0_uncon]
                 if not np.isnan(intercept_val):
                      initial_intercept = intercept_val
                 else:
                      print(f"Warning: Missing Uncon Intercept (NaN) for starting month {start_month_idx+1}. Initial AR seed set to 0.")
            else:
                 print(f"Warning: Cannot get Uncon Intercept for starting month {start_month_idx+1}. Initial AR seed set to 0.")

            # Array of autoregression seed values for each ensemble member
            auto_regression_seed = np.full(ensemble_size, initial_intercept)

            # Initialize detrending counters
            if self.de_trend:
                for i in range(trend_rows_beta):
                     fs_base = fs_date_baseline_days.get(i, 0)
                     cal_base = cal_fs_date_baseline_days.get(i, 0)
                     days_used_linear[i] = fs_base - cal_base

            # --- Main Simulation Loop ---
            progress.setLabelText("Running synthesis...")
            progress.setMaximum(total_prog_steps)
            progress.setValue(current_progress)
            QCoreApplication.processEvents()

            # Arrays to hold daily predictions for each ensemble member
            daily_prediction = np.full(ensemble_size, self.global_missing_code)
            is_wet_status = np.zeros(ensemble_size, dtype=bool) if self.rain_yes else None

            # Caching for performance
            cached_month_idx = -1
            cached_period_idx = -1
            cached_uncon_params = None
            cached_con_params = None
            cached_lambda_params = None
            cached_trend_params = None

            for day_counter in range(synthesis_length):
                if progress.wasCanceled(): raise InterruptedError("Cancelled")
                if day_counter % 50 == 0 or day_counter == synthesis_length - 1:
                    progress.setValue(current_progress + day_counter + 1)
                    QCoreApplication.processEvents()

                current_month_idx = current_date.month - 1
                current_period_idx = -1

                # --- Update cached parameters if month changed ---
                if current_month_idx != cached_month_idx or day_counter == 0:
                    cached_month_idx = current_month_idx
                    cached_uncon_params = None
                    cached_con_params = None
                    cached_lambda_params = None

                    # Get unconditional parameters for current month
                    if self.uncon_parms is not None and 0 <= current_month_idx < 12:
                        params = self.uncon_parms[current_month_idx, :]
                        if self.idx_b0_uncon != -1 and not np.isnan(params[self.idx_b0_uncon]) and \
                           self.idx_se_uncon != -1 and not np.isnan(params[self.idx_se_uncon]):
                             cached_uncon_params = params
                        else:
                            if day_counter == 0: print(f"WARN: Missing essential Uncon params (B0 or SE) for month {current_month_idx+1}.")

                    # Get conditional parameters for current month
                    if self.rain_yes:
                        if self.con_parms is not None and 0 <= current_month_idx < 12:
                             params = self.con_parms[current_month_idx, :]
                             if self.idx_b0_con != -1 and not np.isnan(params[self.idx_b0_con]) and \
                                self.idx_varinf_con != -1 and not np.isnan(params[self.idx_varinf_con]) and \
                                self.idx_se_con != -1 and not np.isnan(params[self.idx_se_con]):
                                  cached_con_params = params
                             else:
                                  if day_counter == 0: print(f"WARN: Missing essential Con params (C0, VarInf, or SE) for month {current_month_idx+1}.")

                    # Get Box-Cox parameters if needed
                    if self.local_model_trans == 5:
                        if self.lamda_array is not None and 0 <= current_month_idx < 12:
                             params = self.lamda_array[current_month_idx, :]
                             if not np.isnan(params).any():
                                  cached_lambda_params = params
                             else:
                                  if day_counter == 0: print(f"WARN: Missing BoxCox params (Lambda or Shift) for month {current_month_idx+1}.")

                # --- Determine current period for detrending ---
                if self.de_trend:
                    month = current_date.month
                    new_period_idx = -1
                    if self.season_code == 1: new_period_idx = 0
                    elif self.season_code == 4: new_period_idx = get_season(month)
                    elif self.season_code == 12: new_period_idx = month - 1

                    if not (0 <= new_period_idx < trend_rows_beta):
                         if day_counter == 0 or new_period_idx != cached_period_idx:
                              print(f"WARN: Invalid detrend period index {new_period_idx} for date {current_date.strftime('%d/%m/%Y')}. Detrending skipped for this period.")
                         current_period_idx = -1
                         cached_trend_params = None
                    else:
                         current_period_idx = new_period_idx
                         if current_period_idx != cached_period_idx or day_counter == 0:
                              cached_period_idx = current_period_idx
                              cached_trend_params = None
                              if self.beta_trend is not None and not np.isnan(self.beta_trend[cached_period_idx, :]).any():
                                  cached_trend_params = self.beta_trend[cached_period_idx, :]
                              else:
                                  if day_counter == 0: print(f"WARN: Missing detrend parameters for period {cached_period_idx+1}")

                         # Update day counters for current period
                         days_used_linear[current_period_idx] = days_used_linear.get(current_period_idx, 0) + 1
                         days_used_power[current_period_idx] = days_used_power.get(current_period_idx, 0) + 1

                # --- Read predictor data for current day ---
                predictor_data = np.full(self.n_predictors, self.global_missing_code)
                missing_flag = False
                
                if len(predictor_file_handles) != self.n_predictors:
                     raise RuntimeError(f"Internal Error: Expected {self.n_predictors} predictor file handles, found {len(predictor_file_handles)}.")

                for i, f_handle in enumerate(predictor_file_handles):
                    if f_handle is None:
                         missing_flag = True
                         continue

                    line = f_handle.readline()
                    if not line:
                         filename_for_error = f"(Predictor {i+1})"
                         if (i+1) < len(self.predictor_filenames): filename_for_error = self.predictor_filenames[i+1] or f"(Predictor {i+1} - empty name)"
                         raise EOFError(f"Predictor '{filename_for_error}' ended unexpectedly at day {day_counter+1} (Date: {current_date.strftime('%d/%m/%Y')}). Expected {synthesis_length} days.")
                    try:
                        val = float(line.strip())
                        predictor_data[i] = val
                        if abs(val - self.global_missing_code) < 1e-9:
                            missing_flag = True
                    except ValueError:
                        print(f"Warning: Non-numeric value read from predictor {i+1} on day {day_counter+1}. Treating as missing. Line: '{line.strip()}'")
                        predictor_data[i] = self.global_missing_code
                        missing_flag = True

                # --- Weather Generation Algorithm ---
                daily_prediction.fill(self.global_missing_code)

                # Proceed only if all inputs are valid
                if not missing_flag:
                    # Use cached parameters
                    uncon_params_month = cached_uncon_params
                    con_params_month = cached_con_params
                    lambda_params_month = cached_lambda_params
                    trend_params = cached_trend_params if current_period_idx != -1 else None

                    # --- Generate unconditional values and/or wet/dry probabilities ---
                    if uncon_params_month is None:
                        missing_flag = True
                        if day_counter == 0 or current_month_idx != (current_date - datetime.timedelta(days=1)).month - 1:
                             print(f"ERROR: Missing essential unconditional parameters for month {current_month_idx+1}. Skipping day {day_counter+1}.")
                    else:
                        # Check if predictor coefficients are valid
                        coeffs_ok = True
                        if self.n_predictors > 0 and self.idx_b1_uncon != -1:
                             uncon_coeffs = uncon_params_month[self.idx_b1_uncon : self.idx_se_uncon]
                             if len(uncon_coeffs) != self.n_predictors:
                                  print(f"ERROR: Uncon coeff count ({len(uncon_coeffs)}) != NPredictors ({self.n_predictors}) for month {current_month_idx+1}. Skipping.")
                                  coeffs_ok = False; missing_flag = True
                             
                        # Check autoregression coefficient if needed
                        if self.auto_regression and (self.idx_ar_uncon == -1 or np.isnan(uncon_params_month[self.idx_ar_uncon])):
                             print(f"WARN: Missing AR coefficient for month {current_month_idx+1} when AutoRegression is True. AR term will be zero.")

                        if coeffs_ok:
                            for ens_idx in range(ensemble_size):
                                # --- Calculate base prediction from linear model ---
                                pred_uncon_base = uncon_params_month[self.idx_b0_uncon]  # Intercept
                                if self.n_predictors > 0 and self.idx_b1_uncon != -1:
                                    uncon_coeffs = uncon_params_month[self.idx_b1_uncon : self.idx_se_uncon]
                                    pred_uncon_base += np.nansum(uncon_coeffs * predictor_data)

                                # --- Add autoregression term if enabled ---
                                ar_term = 0.0
                                if self.auto_regression and self.idx_ar_uncon != -1:
                                    ar_coeff = uncon_params_month[self.idx_ar_uncon]
                                    if abs(auto_regression_seed[ens_idx] - self.global_missing_code) > 1e-9 and not np.isnan(ar_coeff):
                                        ar_term = auto_regression_seed[ens_idx] * ar_coeff
                                pred_uncon_base += ar_term

                                # --- Add random residual term for variability ---
                                std_err_uncon = uncon_params_month[self.idx_se_uncon]
                                residual = 0.0
                                if not np.isnan(std_err_uncon) and std_err_uncon > 1e-9 and self.prec_n > 0:
                                    # Sum N random values and scale to match desired variance
                                    sum_rnd = sum(random.random() for _ in range(self.prec_n))
                                    residual = (sum_rnd - (self.prec_n / 2.0)) * std_err_uncon

                                # --- Determine final value or wet/dry status ---
                                if not self.rain_yes:  # Unconditional process (e.g., temperature)
                                    # Calculate final value with residual
                                    final_pred_value = pred_uncon_base + residual

                                    # Apply detrending adjustment if enabled
                                    if self.de_trend and trend_params is not None:
                                        trend_adjustment = 0.0
                                        try:
                                            current_days_linear = days_used_linear.get(current_period_idx, 0)
                                            current_days_power = days_used_power.get(current_period_idx, 0)

                                            if self.de_trend_type == 1:  # Linear trend
                                                trend_adjustment = trend_params[1] * current_days_linear
                                            else:  # Power trend
                                                power_base = float(current_days_power)
                                                if power_base < 0: power_base = 0
                                                if not np.isnan(trend_params[0]) and not np.isnan(trend_params[1]) and not np.isnan(trend_params[2]):
                                                    trend_adjustment = (trend_params[0] * (power_base ** trend_params[1]))
                                                    trend_adjustment -= abs(trend_params[2])
                                                    trend_adjustment -= 0.001
                                                else:
                                                    print(f"WARN: NaN in Power trend params for period {current_period_idx+1}. Trend set to 0.")

                                            final_pred_value += trend_adjustment
                                        except (OverflowError, ValueError) as trend_err:
                                             print(f"WARN: Uncon Detrend calculation error day {day_counter+1}, ens {ens_idx+1}, period {current_period_idx+1}: {trend_err}. Trend skipped.")

                                    # Ensure non-negative if required
                                    if not self.allow_neg and final_pred_value < 0:
                                         final_pred_value = 0.0

                                    # Store the final value
                                    daily_prediction[ens_idx] = final_pred_value

                                    # Update autoregression seed for next day
                                    auto_regression_seed[ens_idx] = final_pred_value

                                else:  # Conditional process (e.g., precipitation)
                                    # Use unconditional prediction as probability of wet day
                                    prob_wet = pred_uncon_base
                                    is_wet = False
                                    
                                    if self.conditional_selection == 1:  # Stochastic method
                                        is_wet = (random.random() <= prob_wet)
                                    else:  # Fixed threshold method
                                        is_wet = (prob_wet >= self.conditional_thresh)

                                    is_wet_status[ens_idx] = is_wet

                                    # Update AR seed based on wet/dry status
                                    auto_regression_seed[ens_idx] = 1.0 if is_wet else 0.0

                                    # Initialize dry days to zero
                                    if not is_wet:
                                         daily_prediction[ens_idx] = 0.0

                        # End of first ensemble loop

                    # --- Calculate precipitation amounts for wet days ---
                    if self.rain_yes and not missing_flag:
                         if con_params_month is None:
                             missing_flag = True
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

                             if coeffs_con_ok:
                                 for ens_idx in range(ensemble_size):
                                     # Only calculate amount for wet days
                                     if is_wet_status[ens_idx]:
                                         # --- Calculate base amount from linear model ---
                                         pred_amount_base = con_params_month[self.idx_b0_con]  # Intercept
                                         if self.n_predictors > 0 and self.idx_b1_con != -1:
                                             con_coeffs = con_params_month[self.idx_b1_con : self.idx_se_con]
                                             pred_amount_base += np.nansum(con_coeffs * predictor_data)

                                         # --- Apply detrending to base amount ---
                                         if self.de_trend and trend_params is not None:
                                             trend_adjustment_cond = 0.0
                                             try:
                                                 current_days_linear = days_used_linear.get(current_period_idx, 0)
                                                 current_days_power = days_used_power.get(current_period_idx, 0)
                                                 if self.de_trend_type == 1:  # Linear trend
                                                     trend_adjustment_cond = trend_params[1] * current_days_linear
                                                 else:  # Power trend
                                                     power_base = float(current_days_power)
                                                     if power_base < 0: power_base = 0
                                                     if not np.isnan(trend_params[0]) and not np.isnan(trend_params[1]) and not np.isnan(trend_params[2]):
                                                          trend_adjustment_cond = (trend_params[0] * (power_base ** trend_params[1]))
                                                          trend_adjustment_cond -= abs(trend_params[2])
                                                          trend_adjustment_cond -= 0.001
                                                     else: print(f"WARN: NaN in Power trend params for period {current_period_idx+1}. Trend set to 0.")

                                                 pred_amount_base += trend_adjustment_cond
                                             except (OverflowError, ValueError) as trend_err:
                                                  print(f"WARN: Cond Detrend calculation error day {day_counter+1}, ens {ens_idx+1}, period {current_period_idx+1}: {trend_err}. Trend skipped.")

                                         # --- Calculate random residual term ---
                                         std_err_con = con_params_month[self.idx_se_con]
                                         residual_amount = 0.0
                                         if not np.isnan(std_err_con) and std_err_con > 1e-9 and self.prec_n > 0:
                                             sum_rnd_con = sum(random.random() for _ in range(self.prec_n))
                                             residual_amount = (sum_rnd_con - (self.prec_n / 2.0)) * std_err_con

                                         # --- Apply transformation based on model type ---
                                         var_inf = con_params_month[self.idx_varinf_con]
                                         final_pred_amount = self.global_missing_code

                                         try:
                                             # Get base value for transformations
                                             base_plus_trend = pred_amount_base

                                             if self.local_model_trans == 1:  # No transformation
                                                 val_to_bias = (var_inf * base_plus_trend) + residual_amount
                                                 final_pred_amount = self.bias_correction * val_to_bias

                                             elif self.local_model_trans == 2:  # Fourth Root transformation
                                                 val_to_inflate = base_plus_trend + residual_amount
                                                 val_to_power = var_inf * val_to_inflate
                                                 base_for_pow = max(0.0, val_to_power)
                                                 transformed_val = math.pow(base_for_pow, 4.0)
                                                 final_pred_amount = self.bias_correction * transformed_val

                                             elif self.local_model_trans == 3:  # Log transform
                                                 val_to_inflate = base_plus_trend + residual_amount
                                                 val_to_exp = var_inf * val_to_inflate
                                                 try:
                                                      transformed_val = math.exp(val_to_exp)
                                                 except OverflowError:
                                                      transformed_val = float('inf')
                                                 final_pred_amount = self.bias_correction * transformed_val

                                             elif self.local_model_trans == 4:  # Inverse Normal
                                                 val_for_translator = (var_inf * base_plus_trend) + residual_amount
                                                 interim_val = self.bias_correction * val_for_translator
                                                 # Apply translator to convert to data space
                                                 final_pred_amount = self._translator_inv_norm(interim_val)

                                             elif self.local_model_trans == 5:  # Box-Cox
                                                 if lambda_params_month is not None:
                                                     lamda = lambda_params_month[0]
                                                     right_shift = lambda_params_month[1]
                                                     val_to_transform = (var_inf * base_plus_trend) + residual_amount + right_shift

                                                     # Apply inverse Box-Cox
                                                     untransformed_val = self.global_missing_code
                                                     if abs(lamda) < 1e-9:  # Log case (lambda ≈ 0)
                                                          try:
                                                               untransformed_val = math.exp(val_to_transform) - right_shift
                                                          except OverflowError: untransformed_val = float('inf')
                                                     else:  # Power case
                                                          term = val_to_transform * lamda + 1.0
                                                          if term < 1e-9:  # Base must be positive
                                                               print(f"WARN: BoxCox invalid base term {term:.3f} <=0 day {day_counter+1}, ens {ens_idx+1}. Setting to missing.")
                                                               untransformed_val = self.global_missing_code
                                                          else:
                                                               try:
                                                                    untransformed_val = math.pow(term, 1.0 / lamda) - right_shift
                                                               except ValueError:
                                                                    print(f"WARN: BoxCox ValueError (likely neg base {term:.3f} ^ {1.0/lamda:.3f}) day {day_counter+1}, ens {ens_idx+1}. Setting to missing.")
                                                                    untransformed_val = self.global_missing_code
                                                               except OverflowError:
                                                                    untransformed_val = float('inf')

                                                     # Apply bias correction
                                                     if untransformed_val != self.global_missing_code and not math.isinf(untransformed_val):
                                                          final_pred_amount = self.bias_correction * untransformed_val
                                                     else:
                                                          final_pred_amount = untransformed_val
                                                 else:  # Missing Box-Cox parameters
                                                     final_pred_amount = self.global_missing_code
                                                     if day_counter == 0: print(f"WARN: Missing BoxCox parameters for month {current_month_idx+1}, cannot transform.")

                                             # --- Handle special values ---
                                             if math.isinf(final_pred_amount):
                                                 print(f"WARN: Infinite value after transform day {day_counter+1}, ens {ens_idx+1}, trans={self.local_model_trans}. Set to missing.")
                                                 final_pred_amount = self.global_missing_code
                                             elif math.isnan(final_pred_amount):
                                                  print(f"WARN: NaN value after transform day {day_counter+1}, ens {ens_idx+1}, trans={self.local_model_trans}. Set to missing.")
                                                  final_pred_amount = self.global_missing_code

                                             # Apply threshold for precipitation
                                             if final_pred_amount != self.global_missing_code:
                                                 if final_pred_amount <= self.thresh:
                                                      final_pred_amount = self.thresh + 0.001

                                         except (ValueError, OverflowError, TypeError) as transform_err:
                                             print(f"WARN: Transform/Calc Error day {day_counter+1}, ens {ens_idx+1}, trans={self.local_model_trans}: {transform_err}")
                                             final_pred_amount = self.global_missing_code

                                         # Store final amount
                                         daily_prediction[ens_idx] = final_pred_amount
                                     # End if wet day
                                 # End ensemble loop for conditional amounts
                    # End conditional amount calculation

                # --- Write results for the day ---
                # Set all values to missing if any issues occurred
                if missing_flag:
                    daily_prediction.fill(self.global_missing_code)

                # Format values for output
                output_parts = []
                for val in daily_prediction:
                    if np.isnan(val) or abs(val - self.global_missing_code) < 1e-9:
                         output_parts.append(f"{int(self.global_missing_code):d}" if self.global_missing_code == int(self.global_missing_code) else f"{self.global_missing_code:.1f}")
                    else:
                         formatted_val = f"{val:.3f}"
                         if len(formatted_val) > 20: formatted_val = f"{val:.3e}"  # Use scientific for very large values
                         output_parts.append(formatted_val)

                try:
                    out_file_handle.write("\t".join(output_parts) + "\n")
                except Exception as e:
                    raise IOError(f"Error writing to output file {self.out_file_path} on day {day_counter+1}: {e}")

                # Move to next day
                try:
                    current_date += datetime.timedelta(days=1)
                except OverflowError:
                     raise ValueError("Date overflow during simulation loop. Check synthesis length and start date.")

            # --- End of main synthesis loop ---
            progress.setValue(total_prog_steps - 1)

            # --- Create summary file (SIM) ---
            progress.setLabelText("Creating SIM file...")
            QCoreApplication.processEvents()

            try:
                with open(sim_file_path, 'w') as sim_f:
                     # Write model configuration and synthesis information
                     np_val = abs(self.n_predictors) if self.de_trend else self.n_predictors
                     sim_f.write(f" {np_val}\n")
                     sim_f.write(f" {self.season_code}\n")
                     sim_f.write(f" {self.year_indicator}\n")
                     
                     sim_start_date_ui = self._parse_date(self.fStartText.text())
                     sim_f.write(f"{sim_start_date_ui.strftime('%d/%m/%Y')}\n")
                     sim_f.write(f" {synthesis_length}\n")
                     sim_f.write(f"#{str(self.rain_yes).upper()}#\n")
                     sim_f.write(f" {ensemble_size}\n")
                     sim_f.write(f" {self.prec_n}\n")
                     sim_f.write(f" {self.local_model_trans}\n")
                     sim_f.write(f" {self.bias_correction:g}\n")
                     sim_f.write(f'"{self.ptand_filename}"\n')
                     
                     # Write predictor filenames
                     for i in range(self.n_predictors):
                         fname = self.predictor_filenames[i+1] if (i+1) < len(self.predictor_filenames) else ""
                         sim_f.write(f'"{fname}"\n')
            except Exception as e:
                raise IOError(f"Error writing SIM file {sim_file_path}: {e}")

            progress.setValue(total_prog_steps)

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
        except RuntimeError as e:
             QMessageBox.critical(self, "Runtime Error", f"An internal error occurred:\n{e}\n{traceback.format_exc()}")
        except Exception as e:
            QMessageBox.critical(self, "Synthesis Error", f"An unexpected error occurred during synthesis:\n{e}\n\n{traceback.format_exc()}")
        finally:
            # Clean up resources
            if progress: progress.close()
            if out_file_handle and not out_file_handle.closed:
                try: out_file_handle.close()
                except Exception as e: print(f"Error closing output file: {e}")
            for f_handle in predictor_file_handles:
                if f_handle and not f_handle.closed:
                    try: f_handle.close()
                    except Exception as e: print(f"Error closing predictor file: {e}")

    def reset_parsed_data(self):
        """Clear all parsed data from the PAR file."""
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
        """Reset the application to its initial state."""
        try:
            # Reset file paths and UI
            self.par_file_path = ""
            self.predictor_dir = self.default_dir
            self.out_file_path = ""
            self.par_file_text.setText("Not selected")
            self.dirText.setText(self.predictor_dir)
            self.outFileText.setText("Not selected")

            # Reset UI input fields
            self.eSize.setText("20")
            default_start = self.settings.get('globalSDate', "01/01/1961")
            self.fStartText.setText(default_start)
            self.fLengthText.setText("365")

            # Reset UI info labels
            self.predictorList.clear()
            self.no_of_pred_text.setText("0")
            self.auto_regress_label.setText("Unknown")
            self.process_label.setText("Unknown")
            self.r_start_text.setText("unknown")
            self.r_length_text.setText("unknown")

            # Clear all internal data
            self.reset_parsed_data()

        except Exception as e:
            QMessageBox.critical(self, "Reset Error", f"Error during reset: {str(e)}")

# --- Main Application Runner ---
if __name__ == '__main__':
    import sys

    # Ensure QCoreApplication exists for processEvents before QApplication loop
    _app = QCoreApplication.instance()
    if _app is None:
        _app = QApplication(sys.argv)
    else:
        print("QCoreApplication instance already exists.")

    # --- Define application settings ---
    app_settings = {
        'yearIndicator': 365,           # Days in year for synthesis
        'globalSDate': "01/01/1961",    # Default synthesis start date
        'allowNeg': True,               # Allow negative values in outputs
        'randomSeed': False,            # Use fixed seed for reproducibility 
        'thresh': 0.0,                  # Threshold for precipitation events
        'defaultDir': os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data')),
        'globalMissingCode': -999.0,    # Code for missing values
        'varianceInflation': 12,        # Controls random variation
        'biasCorrection': 1.0,          # Correction factor for outputs
        'fixedThreshold': 0.5,          # Threshold for fixed precipitation method
        'conditionalSelection': 'Stochastic',  # Method for wet/dry day selection
    }
    
    # Ensure default directory exists
    default_dir_path = app_settings['defaultDir']
    if not os.path.exists(default_dir_path):
         try:
             os.makedirs(default_dir_path)
             print(f"Created default directory: {default_dir_path}")
         except Exception as e:
             print(f"Warning: Could not create default directory: {e}")
             default_dir_path = os.path.expanduser("~")  # Fallback to home directory
             app_settings['defaultDir'] = default_dir_path
    elif not os.path.isdir(default_dir_path):
         print(f"Warning: defaultDir '{default_dir_path}' is not a directory. Falling back to home.")
         default_dir_path = os.path.expanduser("~")
         app_settings['defaultDir'] = default_dir_path

    # Create and launch the application
    app = QApplication.instance()  # Get the instance created above
    if app is None:  # If it wasn't created for some reason
        app = QApplication(sys.argv)

    mainWindow = QMainWindow()
    mainWindow.setWindowTitle("Weather Generator (SDSM Python)")
    contentWidget = ContentWidget(settings=app_settings)
    mainWindow.setCentralWidget(contentWidget)
    mainWindow.setGeometry(100, 100, 650, 750)
    mainWindow.show()
    sys.exit(app.exec_())