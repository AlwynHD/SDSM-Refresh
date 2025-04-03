import os
import datetime
import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QGroupBox,
    QPushButton, QRadioButton, QCheckBox, QFileDialog, QMessageBox,
    QProgressBar, QTextBrowser, QDialog, QSpinBox, QComboBox, QGridLayout
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont

class ContentWidget(QWidget):
    def __init__(self):
        """
        Initialize the Summary Statistics module widget.
        """
        super().__init__()
        
        # Initial variable setup
        self.input_filename = ""
        self.output_filename = ""
        self.input_file_root = ""
        self.out_fname = ""
        self.sim_fname = ""
        self.save_filename = ""
        self.save_file_root = ""
        self.global_missing_code = -999
        self.ndays_r = 0
        self.no_of_days = 0
        self.fs_date = datetime.datetime.now()
        self.fe_date = datetime.datetime.now()
        self.data_s_date = None
        self.data_e_date = None
        self.ensemble_wanted = 1
        self.ensemble_size = 1
        self.ensemble_mean_checked = True
        self.rain_yes = False
        self.threshold = 0.1  # Default rain threshold
        self.local_year_indicator = 366
        self.local_year_length = 1
        self.local_leap_value = 1
        self.deltaresults = np.zeros((18, 35))
        self.escape_processed = False
        self.error_occurred = False
        self.pot = 95  # Default percentile over threshold 
        self.pbt = 5   # Default percentile below threshold
        self.percentile = 90  # Default percentile
        self.prec_pot = 90  # Default precipitation POT
        self.nday_total = 5  # Default N-day total
        self.delta_wanted = 1  # 1 = percentage, 2 = absolute
        self.source_is_modelled = True  # True = modelled, False = observed
        
        # Statistics parameters
        # Format: (name, enabled, description)
        self.stats_params = [
            ("Mean", "Y", "Mean value"),
            ("Maximum", "Y", "Maximum value"),
            ("Minimum", "Y", "Minimum value"),
            ("Median", "Y", "Median value"),
            ("Variance", "Y", "Variance"),
            ("IQR", "Y", "Inter-quartile range"),
            ("POT", "N", "Count of values above threshold"),
            ("PBT", "N", "Count of values below threshold"),
            ("Percentile", "Y", "User-defined percentile"),
            ("Sum", "N", "Sum divided by years"),
            ("ACF", "N", "Auto-correlation function"),
            ("Skewness", "N", "Skewness"),
            ("MaxNDayTotal", "N", "Maximum N-day total"),
            ("Count", "N", "Number of values"),
            ("WetDayPercent", "N", "Percentage wet days"),
            ("MeanDrySpell", "N", "Mean dry spell length"),
            ("MeanWetSpell", "N", "Mean wet spell length"),
            ("MaxDrySpell", "N", "Maximum dry spell length"),
            ("MaxWetSpell", "N", "Maximum wet spell length"),
            ("SDWetSpell", "N", "Standard deviation of wet spell length"),
            ("SDDrySpell", "N", "Standard deviation of dry spell length"),
            ("PrecPOT", "N", "Precipitation POT"),
            ("PrecPOTPercent", "N", "Precipitation POT as percentage of total"),
            ("ExtremeRange", "N", "Extreme range"),
            ("MinRange", "N", "Minimum range"),
            ("MeanWetDayPers", "N", "Mean wet day persistence"),
            ("MeanDryDayPers", "N", "Mean dry day persistence"),
            ("CorrSpellLength", "N", "Correlation of spell lengths"),
            ("MedianWetSpell", "N", "Median wet spell length"),
            ("MedianDrySpell", "N", "Median dry spell length"),
            ("PFL90", "N", "90th percentile of precipitation"),
            ("PNL90", "N", "90th percentile of number of events")
        ]
        
        # Period labels
        self.labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
                     "Winter", "Spring", "Summer", "Autumn", "Annual"]
        
        # Results arrays
        self.results_array = np.full((101, 18, 35), self.global_missing_code, dtype=float)
        self.t_test_results_a = np.full((18, 3), self.global_missing_code, dtype=float)
        self.t_test_results_b = np.full((18, 3), self.global_missing_code, dtype=float)
        self.t_test_results_c = np.full((18, 3), self.global_missing_code, dtype=float)
        
        # Delta analysis dates
        self.base_start = None
        self.base_end = None
        self.period_a_start = None
        self.period_a_end = None
        self.period_b_start = None
        self.period_b_end = None
        self.period_c_start = None
        self.period_c_end = None
        
        # Initialize UI
        self.init_ui()
        
    def init_ui(self):
        """
        Set up the user interface layout
        """
        main_layout = QVBoxLayout()
        
        # File selection area
        file_group = QGroupBox("Data Source and Output Files")
        file_layout = QVBoxLayout()
        
        input_file_layout = QHBoxLayout()
        input_file_layout.addWidget(QLabel("Input File:"))
        self.input_file_text = QLineEdit()
        self.input_file_text.setReadOnly(True)
        self.input_file_text.setText("Not selected")
        input_file_layout.addWidget(self.input_file_text)
        self.select_input_btn = QPushButton("Select Input File")
        self.select_input_btn.clicked.connect(self.select_input_file)
        input_file_layout.addWidget(self.select_input_btn)
        file_layout.addLayout(input_file_layout)
        
        save_file_layout = QHBoxLayout()
        save_file_layout.addWidget(QLabel("Save Results To:"))
        self.save_file_text = QLineEdit()
        self.save_file_text.setReadOnly(True)
        self.save_file_text.setText("Not selected")
        save_file_layout.addWidget(self.save_file_text)
        self.save_btn = QPushButton("Select Save File")
        self.save_btn.clicked.connect(self.save_button_click)
        save_file_layout.addWidget(self.save_btn)
        file_layout.addLayout(save_file_layout)
        
        # Data source radio buttons
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("Data Source:"))
        self.source_modelled = QRadioButton("Modelled")
        self.source_modelled.setChecked(True)
        self.source_observed = QRadioButton("Observed")
        source_layout.addWidget(self.source_modelled)
        source_layout.addWidget(self.source_observed)
        source_layout.addStretch()
        file_layout.addLayout(source_layout)
        
        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)
        
        # File details area
        details_group = QGroupBox("File Details")
        details_layout = QVBoxLayout()
        
        details_grid = QHBoxLayout()
        
        self.show_file_details_btn = QPushButton("Show File Details")
        self.show_file_details_btn.clicked.connect(self.show_file_details_click)
        details_grid.addWidget(self.show_file_details_btn)
        
        details_grid.addWidget(QLabel("N Predictors:"))
        self.file_n_predictors = QLineEdit()
        self.file_n_predictors.setText("unknown")
        self.file_n_predictors.setReadOnly(True)
        details_grid.addWidget(self.file_n_predictors)
        
        details_grid.addWidget(QLabel("Season Code:"))
        self.file_season_code = QLineEdit()
        self.file_season_code.setText("unknown")
        self.file_season_code.setReadOnly(True)
        details_grid.addWidget(self.file_season_code)
        
        details_grid.addWidget(QLabel("Year Length:"))
        self.file_year_length = QLineEdit()
        self.file_year_length.setText("unknown")
        self.file_year_length.setReadOnly(True)
        details_grid.addWidget(self.file_year_length)
        
        details_layout.addLayout(details_grid)
        
        details_grid2 = QHBoxLayout()
        
        details_grid2.addWidget(QLabel("Start Date:"))
        self.file_start_date = QLineEdit()
        self.file_start_date.setText("unknown")
        self.file_start_date.setReadOnly(True)
        details_grid2.addWidget(self.file_start_date)
        
        details_grid2.addWidget(QLabel("Number of Days:"))
        self.file_n_days = QLineEdit()
        self.file_n_days.setText("unknown")
        self.file_n_days.setReadOnly(True)
        details_grid2.addWidget(self.file_n_days)
        
        details_grid2.addWidget(QLabel("Ensemble Size:"))
        self.file_ensemble_size = QLineEdit()
        self.file_ensemble_size.setText("unknown")
        self.file_ensemble_size.setReadOnly(True)
        details_grid2.addWidget(self.file_ensemble_size)
        
        details_layout.addLayout(details_grid2)
        details_group.setLayout(details_layout)
        main_layout.addWidget(details_group)
        
        # Analysis period area
        period_group = QGroupBox("Analysis Period")
        period_layout = QHBoxLayout()
        
        period_layout.addWidget(QLabel("Start Date:"))
        self.fs_date_text = QLineEdit()
        current_date = datetime.datetime.now()
        self.fs_date_text.setText(current_date.strftime("%Y-%m-%d"))
        self.fs_date_text.editingFinished.connect(self.fs_date_changed)
        period_layout.addWidget(self.fs_date_text)
        
        period_layout.addWidget(QLabel("End Date:"))
        self.fe_date_text = QLineEdit()
        self.fe_date_text.setText(current_date.strftime("%Y-%m-%d"))
        self.fe_date_text.editingFinished.connect(self.fe_date_changed)
        period_layout.addWidget(self.fe_date_text)
        
        period_layout.addWidget(QLabel("No. of Days:"))
        self.no_of_days_text = QLineEdit()
        self.no_of_days_text.setText("1")
        self.no_of_days_text.setReadOnly(True)
        period_layout.addWidget(self.no_of_days_text)
        
        period_group.setLayout(period_layout)
        main_layout.addWidget(period_group)
        
        # Ensemble selection area
        ensemble_group = QGroupBox("Ensemble Selection")
        ensemble_layout = QHBoxLayout()
        
        self.ensemble_mean_check = QCheckBox("Calculate Ensemble Mean")
        self.ensemble_mean_check.setChecked(True)
        self.ensemble_mean_check.stateChanged.connect(self.ensemble_mean_check_click)
        ensemble_layout.addWidget(self.ensemble_mean_check)
        
        ensemble_layout.addWidget(QLabel("Ensemble Number:"))
        self.ensemble_number = QSpinBox()
        self.ensemble_number.setMinimum(0)
        self.ensemble_number.setMaximum(100)
        self.ensemble_number.setValue(0)
        self.ensemble_number.setEnabled(False)
        ensemble_layout.addWidget(self.ensemble_number)
        
        ensemble_group.setLayout(ensemble_layout)
        main_layout.addWidget(ensemble_group)
        
        # Action buttons
        buttons_group = QGroupBox()
        buttons_layout = QHBoxLayout()
        
        # Add statistics button
        self.stats_select_btn = QPushButton("Select Statistics")
        self.stats_select_btn.clicked.connect(self.open_stats_select)
        buttons_layout.addWidget(self.stats_select_btn)
        
        # Add analyze button
        self.analyze_btn = QPushButton("Analyze Data")
        self.analyze_btn.clicked.connect(self.analyze_data)
        buttons_layout.addWidget(self.analyze_btn)
        
        # Add delta stats button
        self.delta_stats_btn = QPushButton("Delta Statistics")
        self.delta_stats_btn.clicked.connect(self.delta_stats)
        buttons_layout.addWidget(self.delta_stats_btn)
        
        # Add reset button
        self.reset_btn = QPushButton("Reset All")
        self.reset_btn.clicked.connect(self.reset_all)
        buttons_layout.addWidget(self.reset_btn)
        
        buttons_group.setLayout(buttons_layout)
        main_layout.addWidget(buttons_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        self.setLayout(main_layout)
        
    def select_input_file(self):
        """
        Opens file dialog to select input file
        """
        options = QFileDialog.Options()
        file_filter = "OUT Files (*.OUT);;DAT Files (*.DAT);;TXT Files (*.TXT);;All Files (*.*)"
        filename, _ = QFileDialog.getOpenFileName(self, "Select Input File", "", 
                                                file_filter, options=options)
        if filename:
            self.input_filename = os.path.basename(filename)
            self.input_file_text.setText(self.input_filename)
            self.input_file_root = filename
            self.out_fname = filename
            self.sim_fname = os.path.splitext(filename)[0] + ".SIM"
    
    def save_button_click(self):
        """
        Opens file dialog to select save file
        """
        options = QFileDialog.Options()
        file_filter = "TXT Files (*.TXT);;All Files (*.*)"
        filename, _ = QFileDialog.getSaveFileName(self, "Save Results", "", 
                                                file_filter, options=options)
        if filename:
            self.save_filename = os.path.basename(filename)
            self.save_file_text.setText(self.save_filename)
            self.save_file_root = filename
    
    def show_file_details_click(self):
        """
        Shows details from the SIM file
        """
        if not self.input_filename:
            QMessageBox.critical(self, "Error Message", "You must select a scenario file first.")
            return
        elif len(self.input_filename) < 5:
            QMessageBox.critical(self, "Error Message", "You must select an appropriate scenario (*.OUT) file.")
            return
        elif not (self.input_filename.lower().endswith('.out')):
            QMessageBox.critical(self, "Error Message", "You must select an appropriate scenario (*.OUT) file.")
            return
        elif self.source_observed.isChecked():
            QMessageBox.critical(self, "Error Message", "You have selected observed data. There is no scenario file available for observed data.")
            return
        
        if self.open_sim_file():
            self.file_n_predictors.setText(str(self.n_predictors))
            self.file_season_code.setText(str(self.season_code))
            self.file_year_length.setText(str(self.local_year_indicator))
            self.file_start_date.setText(self.data_s_date.strftime("%Y-%m-%d"))
            self.file_n_days.setText(str(self.ndays_r))
            self.file_ensemble_size.setText(str(self.ensemble_size))
        else:
            QMessageBox.critical(self, "Error Message", "Sorry - an error has occurred opening the SIM file. Please check settings and try again.")
    
    def open_sim_file(self):
        """
        Opens the SIM file and reads configuration 
        """
        try:
            with open(self.sim_fname, 'r') as f:
                # 1. Number of predictors
                self.n_predictors = int(f.readline().strip())
                
                # 2. Season code
                self.season_code = int(f.readline().strip())
                
                # 3. Year length from sim file - 366, 365, 360
                self.local_year_indicator = int(f.readline().strip())
                
                if self.local_year_indicator == 360:
                    self.local_year_length = 2  # LocalYearLength overrides global YearLength
                else:
                    self.local_year_length = 1
                
                if self.local_year_indicator == 366:
                    self.local_leap_value = 1
                else:
                    self.local_leap_value = 0
                
                # 4. Scenario Start date
                date_str = f.readline().strip()
                try:
                    self.data_s_date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                except ValueError:
                    try:
                        self.data_s_date = datetime.datetime.strptime(date_str, "%m/%d/%Y")
                    except ValueError:
                        self.data_s_date = datetime.datetime.strptime(date_str, "%d/%m/%Y")
                
                # 5. Record length
                self.ndays_r = int(f.readline().strip())
                
                # 6. Rain yes is boolean
                rain_value = f.readline().strip()
                self.rain_yes = False if rain_value == "#FALSE#" else True
                
                # 7. Ensemble size
                self.ensemble_size = int(f.readline().strip())
                
                # 8. PrecN for future enhancement
                _ = f.readline().strip()
                
                # 9. Model transformation
                _ = f.readline().strip()
                
                # 10. Bias correction for future enhancement
                _ = f.readline().strip()
                
            return True
        except Exception as e:
            print(f"Error opening SIM file: {e}")
            return False
    
    def fs_date_changed(self):
        """
        Handle change of start date
        """
        try:
            if not self.fs_date_text.text():
                return
                
            # Try to parse the date
            try:
                new_date = datetime.datetime.strptime(self.fs_date_text.text(), "%Y-%m-%d")
            except ValueError:
                try:
                    new_date = datetime.datetime.strptime(self.fs_date_text.text(), "%m/%d/%Y")
                except ValueError:
                    new_date = datetime.datetime.strptime(self.fs_date_text.text(), "%d/%m/%Y")
            
            # Check if end date is later than start date
            if self.fe_date_text.text():
                try:
                    end_date = datetime.datetime.strptime(self.fe_date_text.text(), "%Y-%m-%d")
                except ValueError:
                    try:
                        end_date = datetime.datetime.strptime(self.fe_date_text.text(), "%m/%d/%Y")
                    except ValueError:
                        end_date = datetime.datetime.strptime(self.fe_date_text.text(), "%d/%m/%Y")
                
                if new_date > end_date:
                    QMessageBox.critical(self, "Error Message", "Analysis start date must be earlier than analysis end date.")
                    self.fs_date_text.setText(self.fs_date.strftime("%Y-%m-%d"))
                    return
                
                days_diff = (end_date - new_date).days + 1
                if days_diff > 150 * 365:
                    QMessageBox.critical(self, "Error Message", "Analysis period must be less than 150 years.")
                    self.fs_date_text.setText(self.fs_date.strftime("%Y-%m-%d"))
                    return
                
                self.no_of_days = days_diff
                self.no_of_days_text.setText(str(self.no_of_days))
            
            self.fs_date = new_date
            
        except Exception as e:
            QMessageBox.critical(self, "Error Message", f"Analysis start date is invalid: {e}")
            self.fs_date_text.setText(self.fs_date.strftime("%Y-%m-%d"))
    
    def fe_date_changed(self):
        """
        Handle change of end date
        """
        try:
            if not self.fe_date_text.text():
                return
                
            # Try to parse the date
            try:
                new_date = datetime.datetime.strptime(self.fe_date_text.text(), "%Y-%m-%d")
            except ValueError:
                try:
                    new_date = datetime.datetime.strptime(self.fe_date_text.text(), "%m/%d/%Y")
                except ValueError:
                    new_date = datetime.datetime.strptime(self.fe_date_text.text(), "%d/%m/%Y")
            
            # Check if start date is earlier than end date
            if self.fs_date_text.text():
                try:
                    start_date = datetime.datetime.strptime(self.fs_date_text.text(), "%Y-%m-%d")
                except ValueError:
                    try:
                        start_date = datetime.datetime.strptime(self.fs_date_text.text(), "%m/%d/%Y")
                    except ValueError:
                        start_date = datetime.datetime.strptime(self.fs_date_text.text(), "%d/%m/%Y")
                
                if new_date < start_date:
                    QMessageBox.critical(self, "Error Message", "Analysis end date must be later than analysis start date.")
                    self.fe_date_text.setText(self.fe_date.strftime("%Y-%m-%d"))
                    return
                
                days_diff = (new_date - start_date).days + 1
                if days_diff > 150 * 365:
                    QMessageBox.critical(self, "Error Message", "Analysis period must be less than 150 years.")
                    self.fe_date_text.setText(self.fe_date.strftime("%Y-%m-%d"))
                    return
                
                self.no_of_days = days_diff
                self.no_of_days_text.setText(str(self.no_of_days))
            
            self.fe_date = new_date
            
        except Exception as e:
            QMessageBox.critical(self, "Error Message", f"Analysis end date is invalid: {e}")
            self.fe_date_text.setText(self.fe_date.strftime("%Y-%m-%d"))
    
    def ensemble_mean_check_click(self, state):
        """
        Handle ensemble mean checkbox
        """
        if state == Qt.Checked:
            self.ensemble_number.setValue(0)
            self.ensemble_number.setEnabled(False)
            self.ensemble_mean_checked = True
        else:
            self.ensemble_number.setEnabled(True)
            self.ensemble_number.setValue(1)
            self.ensemble_mean_checked = False
            self.ensemble_wanted = 1
    
    def reset_all(self):
        """
        Reset all form fields
        """
        # Reset file selections
        self.input_filename = ""
        self.input_file_text.setText("Not selected")
        self.input_file_root = ""
        self.out_fname = ""
        self.sim_fname = ""
        
        self.save_filename = ""
        self.save_file_text.setText("Not selected")
        self.save_file_root = ""
        
        # Reset file details
        self.file_n_predictors.setText("unknown")
        self.file_season_code.setText("unknown")
        self.file_year_length.setText("unknown")
        self.file_start_date.setText("unknown")
        self.file_n_days.setText("unknown")
        self.file_ensemble_size.setText("unknown")
        
        # Reset date fields
        current_date = datetime.datetime.now()
        self.fs_date = current_date
        self.fe_date = current_date
        self.fs_date_text.setText(current_date.strftime("%Y-%m-%d"))
        self.fe_date_text.setText(current_date.strftime("%Y-%m-%d"))
        
        # Reset data source
        self.source_modelled.setChecked(True)
        self.source_is_modelled = True
        
        # Reset ensemble options
        self.ensemble_mean_check.setChecked(True)
        self.ensemble_number.setValue(0)
        self.ensemble_number.setEnabled(False)
        
        # Reset variables
        self.local_year_indicator = 366
        self.local_year_length = 1
        self.local_leap_value = 1
        self.ensemble_wanted = 1
        
    def open_stats_select(self):
        """
        Open dialog to select statistics
        """
        dialog = StatsSelectDialog(self.stats_params, parent=self)
        if dialog.exec_():
            self.stats_params = dialog.get_updated_stats()
            # Update rain_yes based on selected stats
            self.rain_yes = False
            for i in range(15, 24):
                if i < len(self.stats_params) and self.stats_params[i][1] == "Y":
                    self.rain_yes = True
            for i in range(26, 33):
                if i < len(self.stats_params) and self.stats_params[i][1] == "Y":
                    self.rain_yes = True
    
    def analyze_data(self):
        """
        Run the full analysis
        """
        if not self.check_settings():
            return
        
        self.error_occurred = False
        self.calc_stats(self.fs_date, self.fe_date, False)
        
        if not self.error_occurred and not self.escape_processed:
            self.print_results(False)
    
    def days_in_month(self, month, year_length, leap_year=False):
        """
        Return days in month based on SDSM year length
        """
        if year_length == 2:  # 360-day calendar
            return 30
        
        days = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        if month == 2 and leap_year:
            return 29
        
        return days[month]
    
    def is_leap(self, year):
        """
        Check if year is a leap year
        """
        if year % 400 == 0:
            return True
        if year % 100 == 0:
            return False
        return year % 4 == 0
    
    def get_season(self, month):
        """
        Convert month to season
        1 = Winter (Dec, Jan, Feb)
        2 = Spring (Mar, Apr, May)
        3 = Summer (Jun, Jul, Aug)
        4 = Autumn (Sep, Oct, Nov)
        """
        if month in [12, 1, 2]:
            return 1  # Winter
        elif month in [3, 4, 5]:
            return 2  # Spring
        elif month in [6, 7, 8]:
            return 3  # Summer
        else:  # 9, 10, 11
            return 4  # Autumn
    
    def increase_date(self, current_day, current_month, current_year):
        """
        Increase the current date by one day
        Returns tuple (day, month, year, season)
        """
        day = current_day + 1
        month = current_month
        year = current_year
        
        leap = 0
        if month == 2:
            if self.is_leap(year) and self.local_year_length == 1:
                leap = self.local_leap_value
        
        days_in_month = self.days_in_month(month, self.local_year_length, 
                                          leap_year=self.is_leap(year))
        
        if day > days_in_month:
            month += 1
            day = 1
        
        if month > 12:
            month = 1
            year += 1
        
        season = self.get_season(month)
        
        return (day, month, year, season)
    
    def check_settings(self):
        """
        Check for valid settings before analysis
        """
        if not self.input_filename or len(self.input_filename) < 5:
            QMessageBox.critical(self, "Error Message", "You must select a data file first.")
            return False
        
        if not self.save_filename:
            QMessageBox.critical(self, "Error Message", "You must enter a filename to save summary results to.")
            return False
        
        if self.source_modelled.isChecked():
            if not (self.input_filename.lower().endswith('.out')):
                QMessageBox.critical(self, "Error Message", "You must select an appropriate scenario file for modelled analyses.")
                return False
            
            if not self.ensemble_mean_check.isChecked() and self.ensemble_number.value() == 0:
                QMessageBox.critical(self, "Error Message", "You must enter an ensemble member if you do not wish to analyse the mean.")
                return False
            
            if not self.open_sim_file():
                QMessageBox.critical(self, "Error Message", "An error occurred opening the *.SIM file. Please try again.")
                return False
            
            if not self.ensemble_mean_check.isChecked() and self.ensemble_wanted > self.ensemble_size:
                QMessageBox.critical(self, "Error Message", "Ensemble member does not exist in data file.")
                return False
        
        return True
    
    def calc_stats(self, calc_start_date, calc_end_date, doing_deltas):
        """
        Calculate all statistics for the given period
        doing_deltas - if True, calculate variance for delta t-test
        """
        if not self.check_settings():
            self.error_occurred = True
            return
        
        # Convert string dates to datetime if needed
        if isinstance(calc_start_date, str):
            try:
                calc_start_date = datetime.datetime.strptime(calc_start_date, "%Y-%m-%d")
            except ValueError:
                try:
                    calc_start_date = datetime.datetime.strptime(calc_start_date, "%m/%d/%Y")
                except ValueError:
                    calc_start_date = datetime.datetime.strptime(calc_start_date, "%d/%m/%Y")
                
        if isinstance(calc_end_date, str):
            try:
                calc_end_date = datetime.datetime.strptime(calc_end_date, "%Y-%m-%d")
            except ValueError:
                try:
                    calc_end_date = datetime.datetime.strptime(calc_end_date, "%m/%d/%Y")
                except ValueError:
                    calc_end_date = datetime.datetime.strptime(calc_end_date, "%d/%m/%Y")
        
        self.escape_processed = False
        
        # Set up preliminary variables
        end_of_section = 32766  # Any code to mark end will do
        end_of_data = 32767  # End of data marker
        
        # Initialize array positions
        array_position = np.ones((101, 18), dtype=int)
        
        # Set RainYes based on selected stats
        self.rain_yes = False
        for i in range(15, 24):
            if i < len(self.stats_params) and self.stats_params[i][1] == "Y":
                self.rain_yes = True
        for i in range(26, 33):
            if i < len(self.stats_params) and self.stats_params[i][1] == "Y":
                self.rain_yes = True
        
        # If observed data selected, ensemble size is 1
        if self.source_observed.isChecked():
            self.ensemble_size = 1
        
        # Set up data array - w=ensemble number, x=Jan,Feb..Dec, Winter, Summer, Annual; y=data
        total_to_read = 200 + (calc_end_date - calc_start_date).days
        data_array = np.full((self.ensemble_size + 1, 18, total_to_read + 1), 
                             self.global_missing_code, dtype=float)
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Analyzing Scenario")
        
        try:
            with open(self.input_file_root, 'r') as input_file:
                # Skip data before start date
                total_to_skip = (calc_start_date - self.data_s_date).days
                if total_to_skip > 0:
                    self.progress_bar.setFormat("Skipping Unnecessary Data")
                    
                    current_day = self.data_s_date.day
                    current_month = self.data_s_date.month
                    current_year = self.data_s_date.year
                    total_numbers = 0
                    
                    current_date = datetime.datetime(current_year, current_month, current_day)
                    while (current_date < calc_start_date):
                        # Skip a line in the file
                        _ = input_file.readline()
                        total_numbers += 1
                        
                        current_day, current_month, current_year, _ = self.increase_date(
                            current_day, current_month, current_year
                        )
                        current_date = datetime.datetime(current_year, current_month, current_day)
                        
                        prog_value = int((total_numbers / total_to_skip) * 100)
                        self.progress_bar.setValue(prog_value)
                        
                # Now read the actual data needed
                total_to_read = (calc_end_date - calc_start_date).days
                self.progress_bar.setValue(0)
                self.progress_bar.setFormat("Reading in Data")
                
                current_day = calc_start_date.day
                current_month = calc_start_date.month
                current_year = calc_start_date.year
                current_season = self.get_season(current_month)
                
                total_numbers = 0
                this_month = current_month
                this_year = current_year
                this_season = self.get_season(this_month)
                
                # Main loop for reading data
                while True:
                    # Check if month changed
                    if this_month != current_month:
                        for i in range(1, self.ensemble_size + 1):
                            data_array[i, this_month, array_position[i, this_month]] = end_of_section
                            array_position[i, this_month] += 1
                        this_month = current_month
                        
                    # Check if season changed
                    if this_season != current_season:
                        for i in range(1, self.ensemble_size + 1):
                            data_array[i, this_season + 12, array_position[i, this_season + 12]] = end_of_section
                            array_position[i, this_season + 12] += 1
                        this_season = current_season
                        
                    # Check if year changed
                    if this_year != current_year:
                        for i in range(1, self.ensemble_size + 1):
                            data_array[i, 17, array_position[i, 17]] = end_of_section
                            array_position[i, 17] += 1
                        this_year = current_year
                        
                    # Read in a line of data
                    data_string = input_file.readline()
                    if not data_string:
                        break
                        
                    if self.ensemble_size > 1:
                        # Parse multiple columns of data
                        values = data_string.strip().split()
                        for i in range(1, self.ensemble_size + 1):
                            if i <= len(values):
                                try:
                                    data_value = float(values[i-1])
                                    data_array[i, this_month, array_position[i, this_month]] = data_value
                                    data_array[i, this_season + 12, array_position[i, this_season + 12]] = data_value
                                    data_array[i, 17, array_position[i, 17]] = data_value
                                    
                                    array_position[i, this_month] += 1
                                    array_position[i, this_season + 12] += 1
                                    array_position[i, 17] += 1
                                except ValueError:
                                    pass
                    else:
                        # Single value
                        try:
                            data_value = float(data_string.strip())
                            data_array[1, this_month, array_position[1, this_month]] = data_value
                            data_array[1, this_season + 12, array_position[1, this_season + 12]] = data_value
                            data_array[1, 17, array_position[1, 17]] = data_value
                            
                            array_position[1, this_month] += 1
                            array_position[1, this_season + 12] += 1
                            array_position[1, 17] += 1
                        except ValueError:
                            pass
                    
                    # Update current date
                    this_month = current_month
                    this_year = current_year
                    this_season = self.get_season(this_month)
                    
                    current_day, current_month, current_year, current_season = self.increase_date(
                        current_day, current_month, current_year
                    )
                    
                    total_numbers += 1
                    prog_value = int((total_numbers / total_to_read) * 100)
                    self.progress_bar.setValue(prog_value)
                    
                    # Check if we've reached the end date
                    if datetime.datetime(current_year, current_month, current_day) > calc_end_date:
                        break
                
                # Mark end of sections for the last month/season/year
                for i in range(1, self.ensemble_size + 1):
                    data_array[i, this_month, array_position[i, this_month]] = end_of_section
                    data_array[i, this_season + 12, array_position[i, this_season + 12]] = end_of_section
                    data_array[i, 17, array_position[i, 17]] = end_of_section
                    
                    array_position[i, this_month] += 1
                    array_position[i, this_season + 12] += 1
                    array_position[i, 17] += 1
                
                # Mark end of data for all periods
                for i in range(1, self.ensemble_size + 1):
                    for j in range(1, 18):
                        data_array[i, j, array_position[i, j]] = end_of_data
            
            # Calculate stats from the loaded data
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("Calculating Statistics - Please Wait")
            
            # Initialize arrays to track valid data
            was_any_data_valid = np.zeros((101, 18), dtype=bool)
            year_count_2d = np.zeros((101, 18), dtype=int)
            year_count_1d = np.zeros(18, dtype=int)
            
            # Calculate simple statistics first - Mean, Max, Min, Sum, Count, POT, PBT
            prog_value = 0
            for i in range(1, self.ensemble_size + 1):
                for j in range(1, 18):
                    prog_value += 1
                    self.progress_bar.setValue(int((prog_value / (self.ensemble_size * 17)) * 100))
                    
                    total_sum = 0.0
                    total_count = 0
                    minimum_so_far = 999999.0
                    maximum_so_far = -999999.0
                    pot_count = 0
                    pbt_count = 0
                    dry_day_count = 0
                    
                    was_any_data_valid[i, j] = False  # Assume no valid data initially
                    
                    # Process data values for this period
                    for k in range(1, array_position[i, j]):
                        data_value = data_array[i, j, k]
                        
                        # Skip missing values and end markers
                        if (data_value != self.global_missing_code and 
                            data_value != end_of_section and 
                            data_value != end_of_data):
                            
                            was_any_data_valid[i, j] = True
                            
                            # Count values based on whether we're handling precipitation
                            if (not self.rain_yes) or (self.rain_yes and data_value > self.threshold):
                                total_count += 1
                                total_sum += data_value
                                
                                if data_value > maximum_so_far:
                                    maximum_so_far = data_value
                                if data_value < minimum_so_far:
                                    minimum_so_far = data_value
                                
                                if data_value >= self.pot:
                                    pot_count += 1
                                if data_value <= self.pbt:
                                    pbt_count += 1
                            
                            # Count dry days for precipitation data
                            if self.rain_yes and data_value <= self.threshold:
                                dry_day_count += 1
                    
                    # Handle invalid data cases
                    if maximum_so_far == -999999.0:
                        maximum_so_far = self.global_missing_code
                    if minimum_so_far == 999999.0:
                        minimum_so_far = self.global_missing_code
                    
                    # Calculate extremes range if needed
                    if was_any_data_valid[i, j] and (self.stats_params[23][1] == "Y" or self.stats_params[24][1] == "Y"):
                        extreme_range = -1.0
                        min_range = 99999.0
                        section_max = -99999.0
                        section_min = 99999.0
                        
                        for k in range(1, array_position[i, j]):
                            data_value = data_array[i, j, k]
                            
                            if (data_value != self.global_missing_code and 
                                data_value != end_of_section and 
                                data_value != end_of_data):
                                
                                if (not self.rain_yes) or (self.rain_yes and data_value > self.threshold):
                                    if data_value > section_max:
                                        section_max = data_value
                                    if data_value < section_min:
                                        section_min = data_value
                            
                            if data_value == end_of_section:
                                this_range = section_max - section_min
                                if this_range > extreme_range:
                                    extreme_range = this_range
                                if this_range < min_range and this_range != -199998:
                                    min_range = this_range
                                
                                section_max = -99999.0
                                section_min = 99999.0
                        
                        if extreme_range == -1:
                            extreme_range = self.global_missing_code
                        if min_range == 99999.0:
                            min_range = self.global_missing_code
                    else:
                        extreme_range = self.global_missing_code
                        min_range = self.global_missing_code
                    
                    # Store calculated statistics
                    if was_any_data_valid[i, j]:
                        self.results_array[i, j, 2] = maximum_so_far  # Maximum
                        self.results_array[i, j, 3] = minimum_so_far  # Minimum
                        self.results_array[i, j, 7] = pot_count  # POT
                        self.results_array[i, j, 8] = pbt_count  # PBT
                        self.results_array[i, j, 10] = total_sum  # Sum
                        self.results_array[i, j, 14] = total_count  # Count
                        self.results_array[i, j, 24] = extreme_range  # Extreme range
                        self.results_array[i, j, 25] = min_range  # Minimum range
                        
                        # Calculate percentage wet
                        if (total_count + dry_day_count) == 0:
                            self.results_array[i, j, 15] = 0
                        else:
                            self.results_array[i, j, 15] = total_count / (total_count + dry_day_count)
                        
                        # Calculate mean
                        if total_count > 0:
                            self.results_array[i, j, 1] = total_sum / total_count
                        else:
                            self.results_array[i, j, 1] = self.global_missing_code
                    else:
                        # No valid data
                        self.results_array[i, j, 2] = self.global_missing_code  # Maximum
                        self.results_array[i, j, 3] = self.global_missing_code  # Minimum
                        self.results_array[i, j, 7] = self.global_missing_code  # POT
                        self.results_array[i, j, 8] = self.global_missing_code  # PBT
                        self.results_array[i, j, 10] = self.global_missing_code  # Sum
                        self.results_array[i, j, 14] = self.global_missing_code  # Count
                        self.results_array[i, j, 24] = self.global_missing_code  # Extreme range
                        self.results_array[i, j, 25] = self.global_missing_code  # Minimum range
                        self.results_array[i, j, 15] = self.global_missing_code  # Wet day %
                        self.results_array[i, j, 1] = self.global_missing_code  # Mean
            
            # Pass through data again for variance and skewness if needed
            if self.stats_params[4][1] == "Y" or self.stats_params[11][1] == "Y" or doing_deltas:
                prog_value = 0
                self.progress_bar.setValue(0)
                self.progress_bar.setFormat("Calculating Moments - Please Wait")
                
                for i in range(1, self.ensemble_size + 1):
                    for j in range(1, 18):
                        prog_value += 1
                        self.progress_bar.setValue(int((prog_value / (self.ensemble_size * 17)) * 100))
                        
                        if was_any_data_valid[i, j]:
                            total_variance = 0.0
                            total_skewness = 0.0
                            total_count = 0
                            
                            for k in range(1, array_position[i, j]):
                                data_value = data_array[i, j, k]
                                
                                if (data_value != self.global_missing_code and 
                                    data_value != end_of_section and 
                                    data_value != end_of_data):
                                    
                                    if (not self.rain_yes) or (self.rain_yes and data_value > self.threshold):
                                        total_count += 1
                                        total_variance += (data_value - self.results_array[i, j, 1]) ** 2
                                        total_skewness += (data_value - self.results_array[i, j, 1]) ** 3
                            
                            if total_count > 0:
                                self.results_array[i, j, 5] = total_variance / total_count  # Variance
                                
                                if self.results_array[i, j, 5] > 0:
                                    standard_dev = np.sqrt(self.results_array[i, j, 5])
                                    self.results_array[i, j, 12] = (total_skewness / total_count) / (standard_dev ** 3)  # Skewness
                                else:
                                    self.results_array[i, j, 12] = 0  # Skewness
                            else:
                                self.results_array[i, j, 5] = 0
                                self.results_array[i, j, 12] = 0
                        else:
                            self.results_array[i, j, 5] = self.global_missing_code
                            self.results_array[i, j, 12] = self.global_missing_code
            
            # Calculate years for each section
            for i in range(1, self.ensemble_size + 1):
                for j in range(1, 18):
                    year_count_2d[i, j] = 0
                    
                    if was_any_data_valid[i, j]:
                        section_ok = False
                        
                        for k in range(1, array_position[i, j]):
                            if (data_array[i, j, k] != self.global_missing_code and 
                                data_array[i, j, k] != end_of_section and 
                                not section_ok):
                                
                                section_ok = True
                                year_count_2d[i, j] += 1
                            
                            if data_array[i, j, k] == end_of_section:
                                section_ok = False
            
            # Find greatest year count across all ensembles
            for j in range(1, 18):
                year_count_1d[j] = 0
                for i in range(1, self.ensemble_size + 1):
                    if year_count_2d[i, j] > year_count_1d[j]:
                        year_count_1d[j] = year_count_2d[i, j]
            
            # Calculate Maximum N-day total if needed
            if self.stats_params[12][1] == "Y":
                prog_value = 0
                self.progress_bar.setValue(0)
                self.progress_bar.setFormat("Calculating N Day Total - Please Wait")
                
                for i in range(1, self.ensemble_size + 1):
                    for j in range(1, 18):
                        prog_value += 1
                        self.progress_bar.setValue(int((prog_value / (self.ensemble_size * 17)) * 100))
                        
                        if was_any_data_valid[i, j]:
                            if array_position[i, j] < self.nday_total:
                                self.results_array[i, j, 13] = 0
                            else:
                                max_n_day_total = 0.0
                                
                                for k in range(1, array_position[i, j] - self.nday_total + 1):
                                    running_sum = 0.0
                                    section_valid = True
                                    
                                    for l in range(self.nday_total):
                                        if (data_array[i, j, k + l] == end_of_section or 
                                            data_array[i, j, k + l] == end_of_data):
                                            section_valid = False
                                        elif data_array[i, j, k + l] != self.global_missing_code:
                                            running_sum += data_array[i, j, k + l]
                                    
                                    if section_valid and running_sum > max_n_day_total:
                                        max_n_day_total = running_sum
                                
                                self.results_array[i, j, 13] = max_n_day_total
                        else:
                            self.results_array[i, j, 13] = self.global_missing_code
            
            # Calculate Auto-correlation function if needed
            if self.stats_params[10][1] == "Y":
                prog_value = 0
                self.progress_bar.setValue(0)
                self.progress_bar.setFormat("Calculating Autocorrelation Function - Please Wait")
                
                for i in range(1, self.ensemble_size + 1):
                    for j in range(1, 18):
                        prog_value += 1
                        self.progress_bar.setValue(int((prog_value / (self.ensemble_size * 17)) * 100))
                        
                        if was_any_data_valid[i, j]:
                            # Create correlation arrays
                            correlation_array = np.zeros((3, total_to_read + 2))
                            counter = 0
                            
                            # Populate correlation array with valid data pairs
                            for k in range(1, array_position[i, j] - 1):
                                if (data_array[i, j, k] != self.global_missing_code and 
                                    data_array[i, j, k] != end_of_data and 
                                    data_array[i, j, k] != end_of_section):
                                    
                                    if (data_array[i, j, k+1] != self.global_missing_code and 
                                        data_array[i, j, k+1] != end_of_data and 
                                        data_array[i, j, k+1] != end_of_section):
                                        
                                        counter += 1
                                        correlation_array[1, counter] = data_array[i, j, k]
                                        correlation_array[2, counter] = data_array[i, j, k+1]
                            
                            if counter <= 2:
                                self.results_array[i, j, 11] = self.global_missing_code
                            else:
                                # Calculate means
                                sum1 = np.sum(correlation_array[1, 1:counter+1])
                                sum2 = np.sum(correlation_array[2, 1:counter+1])
                                
                                mean1 = sum1 / counter
                                mean2 = sum2 / counter
                                
                                # Calculate correlation coefficients
                                brhs = np.sum((correlation_array[2, 1:counter+1] - mean2) ** 2)
                                blhs = np.sum((correlation_array[1, 1:counter+1] - mean1) ** 2)
                                
                                numerator = np.sum((correlation_array[1, 1:counter+1] - mean1) * 
                                                  (correlation_array[2, 1:counter+1] - mean2))
                                
                                denominator = np.sqrt(blhs * brhs)
                                
                                if denominator == 0:
                                    self.results_array[i, j, 11] = 1  # Model has zero variance
                                else:
                                    self.results_array[i, j, 11] = numerator / denominator
                        else:
                            self.results_array[i, j, 11] = self.global_missing_code
            
            # Calculate precipitation statistics if needed
            if (self.rain_yes and (self.stats_params[15][1] == "Y" or
                                  self.stats_params[16][1] == "Y" or
                                  self.stats_params[17][1] == "Y" or
                                  self.stats_params[18][1] == "Y" or
                                  self.stats_params[19][1] == "Y" or
                                  self.stats_params[20][1] == "Y" or
                                  self.stats_params[25][1] == "Y" or
                                  self.stats_params[26][1] == "Y" or
                                  self.stats_params[27][1] == "Y" or
                                  self.stats_params[28][1] == "Y" or
                                  self.stats_params[29][1] == "Y")):
                
                prog_value = 0
                self.progress_bar.setValue(0)
                self.progress_bar.setFormat("Calculating Precipitation Statistics - Please Wait")
                
                max_spells = 27450  # Maximum number of spells to track
                
                for i in range(1, self.ensemble_size + 1):
                    for j in range(1, 18):
                        prog_value += 1
                        self.progress_bar.setValue(int((prog_value / (self.ensemble_size * 17)) * 100))
                        
                        if array_position[i, j] <= 2 or not was_any_data_valid[i, j]:
                            # Not enough data for analysis
                            self.results_array[i, j, 16] = self.global_missing_code  # Mean dry spell
                            self.results_array[i, j, 17] = self.global_missing_code  # Mean wet spell
                            self.results_array[i, j, 18] = self.global_missing_code  # Max dry spell
                            self.results_array[i, j, 19] = self.global_missing_code  # Max wet spell
                            self.results_array[i, j, 20] = self.global_missing_code  # SD wet spell
                            self.results_array[i, j, 21] = self.global_missing_code  # SD dry spell
                            self.results_array[i, j, 26] = self.global_missing_code  # Mean wet day persistence
                            self.results_array[i, j, 27] = self.global_missing_code  # Mean dry day persistence
                            self.results_array[i, j, 28] = self.global_missing_code  # Correlation spell lengths
                            self.results_array[i, j, 29] = self.global_missing_code  # Median wet spell
                            self.results_array[i, j, 30] = self.global_missing_code  # Median dry spell
                        else:
                            # Analyze dry and wet spells
                            dry_spell_array = np.zeros(max_spells, dtype=int)
                            wet_spell_array = np.zeros(max_spells, dtype=int)
                            
                            no_of_dry_spells = 0
                            no_of_wet_spells = 0
                            
                            # Determine initial state
                            if (data_array[i, j, 1] == self.global_missing_code or 
                                data_array[i, j, 1] == end_of_section):
                                its_wet = "?"
                            elif data_array[i, j, 1] > self.threshold:
                                its_wet = "Y"
                                wet_count = 1
                            else:
                                its_wet = "N"
                                dry_count = 1
                            
                            # Process data to identify spell lengths
                            for k in range(2, array_position[i, j]):
                                data_value = data_array[i, j, k]
                                
                                # Handle end markers or missing data
                                if (data_value == self.global_missing_code or 
                                    data_value == end_of_section or 
                                    data_value == end_of_data):
                                    
                                    if its_wet == "Y":
                                        no_of_wet_spells += 1
                                        wet_spell_array[no_of_wet_spells] = wet_count
                                    elif its_wet == "N":
                                        no_of_dry_spells += 1
                                        dry_spell_array[no_of_dry_spells] = dry_count
                                    
                                    its_wet = "?"
                                
                                # Handle wet values
                                elif data_value > self.threshold:
                                    if its_wet == "Y":
                                        wet_count += 1
                                    elif its_wet == "N":
                                        no_of_dry_spells += 1
                                        dry_spell_array[no_of_dry_spells] = dry_count
                                        wet_count = 1
                                    else:
                                        wet_count = 1
                                    
                                    its_wet = "Y"
                                
                                # Handle dry values
                                else:
                                    if its_wet == "N":
                                        dry_count += 1
                                    elif its_wet == "Y":
                                        no_of_wet_spells += 1
                                        wet_spell_array[no_of_wet_spells] = wet_count
                                        dry_count = 1
                                    else:
                                        dry_count = 1
                                    
                                    its_wet = "N"
                            
                            # Process wet spell statistics
                            if no_of_wet_spells == 0:
                                self.results_array[i, j, 17] = 0  # Mean wet spell
                                self.results_array[i, j, 19] = 0  # Max wet spell
                                self.results_array[i, j, 20] = 0  # SD wet spell
                                self.results_array[i, j, 26] = 0  # Mean wet day persistence
                            else:
                                # Calculate mean and max
                                mean_wet_spell_length = np.sum(wet_spell_array[1:no_of_wet_spells+1]) / no_of_wet_spells
                                max_wet_spell_length = np.max(wet_spell_array[1:no_of_wet_spells+1])
                                
                                # Calculate persistence
                                total_wet_days = np.sum(wet_spell_array[1:no_of_wet_spells+1])
                                total_consec_wet = np.sum(wet_spell_array[1:no_of_wet_spells+1][wet_spell_array[1:no_of_wet_spells+1] > 1])
                                
                                mean_wet_day_pers = 0
                                if total_wet_days != 0:
                                    mean_wet_day_pers = total_consec_wet / total_wet_days
                                
                                # Calculate standard deviation
                                sd_wet_spell = np.sqrt(np.sum((wet_spell_array[1:no_of_wet_spells+1] - mean_wet_spell_length) ** 2) / no_of_wet_spells)
                                
                                self.results_array[i, j, 17] = mean_wet_spell_length
                                self.results_array[i, j, 19] = max_wet_spell_length
                                self.results_array[i, j, 20] = sd_wet_spell
                                self.results_array[i, j, 26] = mean_wet_day_pers
                            
                            # Process dry spell statistics
                            if no_of_dry_spells == 0:
                                self.results_array[i, j, 16] = 0  # Mean dry spell
                                self.results_array[i, j, 18] = 0  # Max dry spell
                                self.results_array[i, j, 21] = 0  # SD dry spell
                                self.results_array[i, j, 27] = 0  # Mean dry day persistence
                            else:
                                # Calculate mean and max
                                mean_dry_spell_length = np.sum(dry_spell_array[1:no_of_dry_spells+1]) / no_of_dry_spells
                                max_dry_spell_length = np.max(dry_spell_array[1:no_of_dry_spells+1])
                                
                                # Calculate persistence
                                total_dry_days = np.sum(dry_spell_array[1:no_of_dry_spells+1])
                                total_consec_dry = np.sum(dry_spell_array[1:no_of_dry_spells+1][dry_spell_array[1:no_of_dry_spells+1] > 1])
                                
                                mean_dry_day_pers = 0
                                if total_dry_days != 0:
                                    mean_dry_day_pers = total_consec_dry / total_dry_days
                                
                                # Calculate standard deviation
                                sd_dry_spell = np.sqrt(np.sum((dry_spell_array[1:no_of_dry_spells+1] - mean_dry_spell_length) ** 2) / no_of_dry_spells)
                                
                                self.results_array[i, j, 16] = mean_dry_spell_length
                                self.results_array[i, j, 18] = max_dry_spell_length
                                self.results_array[i, j, 21] = sd_dry_spell
                                self.results_array[i, j, 27] = mean_dry_day_pers
                            
                            # Calculate correlation
                            if mean_wet_day_pers != 0 and mean_dry_day_pers != 0:
                                self.results_array[i, j, 28] = mean_wet_day_pers - (1 - mean_dry_day_pers)
                            else:
                                self.results_array[i, j, 28] = self.global_missing_code
                            
                            # Calculate median wet spell length if needed
                            if self.stats_params[28][1] == "Y":
                                if no_of_wet_spells == 0:
                                    self.results_array[i, j, 29] = self.global_missing_code
                                elif no_of_wet_spells == 1:
                                    self.results_array[i, j, 29] = wet_spell_array[1]
                                else:
                                    # Sort the wet spell array
                                    sorted_wet = np.sort(wet_spell_array[1:no_of_wet_spells+1])
                                    
                                    position = no_of_wet_spells // 2
                                    if no_of_wet_spells % 2 != 0:  # Odd number
                                        self.results_array[i, j, 29] = sorted_wet[position]
                                    else:  # Even number
                                        self.results_array[i, j, 29] = (sorted_wet[position-1] + sorted_wet[position]) / 2
                            
                            # Calculate median dry spell length if needed
                            if self.stats_params[29][1] == "Y":
                                if no_of_dry_spells == 0:
                                    self.results_array[i, j, 30] = self.global_missing_code
                                elif no_of_dry_spells == 1:
                                    self.results_array[i, j, 30] = dry_spell_array[1]
                                else:
                                    # Sort the dry spell array
                                    sorted_dry = np.sort(dry_spell_array[1:no_of_dry_spells+1])
                                    
                                    position = no_of_dry_spells // 2
                                    if no_of_dry_spells % 2 != 0:  # Odd number
                                        self.results_array[i, j, 30] = sorted_dry[position]
                                    else:  # Even number
                                        self.results_array[i, j, 30] = (sorted_dry[position-1] + sorted_dry[position]) / 2
            
            # Calculate median, percentile, IQR, and POT/POT% for precipitation
            if (self.stats_params[3][1] == "Y" or
                self.stats_params[8][1] == "Y" or
                self.stats_params[5][1] == "Y" or
                self.stats_params[21][1] == "Y" or
                self.stats_params[22][1] == "Y" or
                self.stats_params[30][1] == "Y"):
                
                prog_value = 0
                self.progress_bar.setValue(0)
                self.progress_bar.setFormat("Calculating Median and Percentiles - Please Wait")
                
                for i in range(1, self.ensemble_size + 1):
                    # Process in reverse order to ensure annual stats computed first
                    for j in range(17, 0, -1):
                        prog_value += 1
                        self.progress_bar.setValue(int((prog_value / (self.ensemble_size * 17)) * 100))
                        
                        if was_any_data_valid[i, j]:
                            # Filter data to remove missing values, end markers, and low precipitation
                            valid_data = []
                            
                            for k in range(1, array_position[i, j]):
                                if (data_array[i, j, k] != self.global_missing_code and
                                    data_array[i, j, k] != end_of_section and
                                    data_array[i, j, k] != end_of_data):
                                    
                                    if (not self.rain_yes) or (self.rain_yes and data_array[i, j, k] > self.threshold):
                                        valid_data.append(data_array[i, j, k])
                            
                            if len(valid_data) > 1:
                                # Sort the data
                                valid_data.sort()
                                
                                # Calculate percentile
                                self.results_array[i, j, 9] = self.calculate_percentile(valid_data, self.percentile)
                                
                                # Calculate median
                                self.results_array[i, j, 4] = self.calculate_percentile(valid_data, 50)
                                
                                # Calculate IQR
                                twenty_fifth = self.calculate_percentile(valid_data, 25)
                                seventy_fifth = self.calculate_percentile(valid_data, 75)
                                self.results_array[i, j, 6] = seventy_fifth - twenty_fifth
                                
                                # Calculate Precipitation POT and POT% if needed
                                if self.rain_yes:
                                    # Use annual percentile as the threshold
                                    if j == 17:  # For annual data, calculate the percentile threshold
                                        precip_thresh = self.calculate_percentile(valid_data, self.prec_pot)
                                    
                                    pot_counter = 0
                                    pot_sum = 0
                                    complete_sum = sum(valid_data)
                                    
                                    for val in valid_data:
                                        if val > precip_thresh:
                                            pot_counter += 1
                                            pot_sum += val
                                    
                                    self.results_array[i, j, 22] = pot_counter
                                    
                                    if complete_sum > 0:
                                        self.results_array[i, j, 23] = pot_sum / complete_sum
                                    else:
                                        self.results_array[i, j, 23] = self.global_missing_code
                                
                            elif len(valid_data) == 1:
                                self.results_array[i, j, 9] = valid_data[0]  # Percentile
                                self.results_array[i, j, 4] = valid_data[0]  # Median
                                self.results_array[i, j, 6] = 0  # IQR
                            else:
                                self.results_array[i, j, 9] = self.global_missing_code  # Percentile
                                self.results_array[i, j, 4] = self.global_missing_code  # Median
                                self.results_array[i, j, 6] = self.global_missing_code  # IQR
                        else:
                            self.results_array[i, j, 9] = self.global_missing_code  # Percentile
                            self.results_array[i, j, 4] = self.global_missing_code  # Median
                            self.results_array[i, j, 6] = self.global_missing_code  # IQR
                            self.results_array[i, j, 22] = self.global_missing_code  # POT
                            self.results_array[i, j, 23] = self.global_missing_code  # POT as % of total
            
            # Convert sum to sum divided by years available
            for i in range(1, self.ensemble_size + 1):
                for j in range(1, 18):
                    if year_count_1d[j] == 0:
                        self.results_array[i, j, 10] = self.global_missing_code
                    elif self.results_array[i, j, 10] != self.global_missing_code:
                        self.results_array[i, j, 10] = self.results_array[i, j, 10] / year_count_1d[j]
            
            # Calculate ensemble mean if needed
            if self.ensemble_size > 1 and self.ensemble_mean_checked:
                for stat_wanted in range(1, 34):  # For all stats
                    for j in range(1, 18):  # For each period
                        # Calculate mean
                        mean_stats = 0
                        missing = 0
                        
                        for i in range(1, self.ensemble_size + 1):
                            if self.results_array[i, j, stat_wanted] == self.global_missing_code:
                                missing += 1
                            else:
                                mean_stats += self.results_array[i, j, stat_wanted]
                        
                        if missing == self.ensemble_size:
                            mean_stats = self.global_missing_code
                        else:
                            mean_stats = mean_stats / (self.ensemble_size - missing)
                        
                        # Calculate standard deviation
                        if mean_stats == self.global_missing_code:
                            sd_stats = self.global_missing_code
                        else:
                            sd_stats = 0
                            for i in range(1, self.ensemble_size + 1):
                                if self.results_array[i, j, stat_wanted] != self.global_missing_code:
                                    sd_stats += (self.results_array[i, j, stat_wanted] - mean_stats) ** 2
                            
                            sd_stats = sd_stats / (self.ensemble_size - missing)
                            sd_stats = np.sqrt(sd_stats)
                        
                        # Store results
                        self.results_array[1, j, stat_wanted] = mean_stats
                        self.results_array[2, j, stat_wanted] = sd_stats
            # Copy specific ensemble results to first position if not using mean
            elif self.ensemble_size > 1 and not self.ensemble_mean_checked:
                for j in range(1, 18):
                    for stat in range(1, 34):
                        self.results_array[1, j, stat] = self.results_array[self.ensemble_wanted, j, stat]
            
            self.progress_bar.setVisible(False)
            
            return True
            
        except Exception as e:
            self.progress_bar.setVisible(False)
            QMessageBox.critical(self, "Error", f"An error occurred during analysis: {e}")
            self.error_occurred = True
            return False
    
    def calculate_percentile(self, data, ptile):
        """
        Calculate percentile from data array
        """
        if not data:
            return self.global_missing_code
            
        n = len(data)
        position = 1 + (ptile * (n - 1) / 100)
        
        lower_bound = int(position)
        upper_bound = min(lower_bound + 1, n)
        
        proportion = position - lower_bound
        
        if lower_bound < 1:
            return data[0]
            
        if lower_bound >= n:
            return data[-1]
            
        range_val = data[upper_bound-1] - data[lower_bound-1]
        
        return data[lower_bound-1] + (range_val * proportion)
    
    def print_results(self, deltas_used):
        """
        Print all results to file and display in a dialog
        """
        results_dialog = ResultsDialog(parent=self)
        results_dialog.setWindowTitle("Analysis Results")
        
        if not deltas_used:
            print_start_date = self.fs_date
            print_end_date = self.fe_date
        else:
            print_start_date = self.base_start
            print_end_date = self.base_end
        
        # Write to file
        with open(self.save_file_root, 'w') as f:
            f.write(f"SUMMARY STATISTICS FOR: {self.input_filename}\n\n")
            f.write(f"Analysis Start Date: {print_start_date.strftime('%Y-%m-%d')}\n")
            f.write(f"Analysis End Date: {print_end_date.strftime('%Y-%m-%d')}\n")
            
            if self.ensemble_size > 1 and self.ensemble_mean_checked:
                f.write("Ensemble Member(s): ALL\n")
            elif self.ensemble_size > 1 and not self.ensemble_mean_checked:
                f.write(f"Ensemble Member(s): {self.ensemble_wanted}\n")
            
            f.write("-\n")
            
            # Write column headers
            f.write("Month")
            for i in range(len(self.stats_params)):
                if self.stats_params[i][1] == "Y":
                    f.write(f",{self.stats_params[i][0]}")
            f.write("\n-\n")
            
            # Write data for each period
            for i in range(1, 18):
                f.write(f"{self.labels[i-1]}")
                for j in range(1, len(self.stats_params) + 1):
                    if j < len(self.stats_params) and self.stats_params[j-1][1] == "Y":
                        f.write(f",{self.results_array[1, i, j]}")
                f.write("\n")
            
            # Write standard deviations if mean selected
            if self.ensemble_size > 1 and self.ensemble_mean_checked:
                f.write("\nStandard Deviations of Results\n")
                
                for i in range(1, 18):
                    f.write(f"{self.labels[i-1]}")
                    for j in range(1, len(self.stats_params) + 1):
                        if j < len(self.stats_params) and self.stats_params[j-1][1] == "Y":
                            f.write(f",{self.results_array[2, i, j]}")
                    f.write("\n")
        
        # Format text for dialog display
        result_text = f"SUMMARY STATISTICS FOR: {self.input_filename}\n\n"
        result_text += f"Analysis Start Date: {print_start_date.strftime('%Y-%m-%d')}\n"
        result_text += f"Analysis End Date: {print_end_date.strftime('%Y-%m-%d')}\n"
        
        if self.ensemble_size > 1 and self.ensemble_mean_checked:
            result_text += "Ensemble Member(s): ALL\n\n"
        elif self.ensemble_size > 1 and not self.ensemble_mean_checked:
            result_text += f"Ensemble Member(s): {self.ensemble_wanted}\n\n"
        else:
            result_text += "\n"
        
        # Format column headers
        header_row = "Month\t"
        for i in range(len(self.stats_params)):
            if self.stats_params[i][1] == "Y":
                header_row += f"{self.stats_params[i][0]}\t"
        result_text += header_row + "\n\n"
        
        # Format data rows
        for i in range(1, 18):
            row = f"{self.labels[i-1]}\t"
            for j in range(1, len(self.stats_params) + 1):
                if j < len(self.stats_params) and self.stats_params[j-1][1] == "Y":
                    if self.results_array[1, i, j] == self.global_missing_code:
                        row += "---\t"
                    else:
                        row += f"{self.results_array[1, i, j]:.3f}\t"
            result_text += row + "\n"
        
        # Add standard deviations if ensemble mean used
        if self.ensemble_size > 1 and self.ensemble_mean_checked:
            result_text += "\nStandard Deviations of Results\n\n"
            
            for i in range(1, 18):
                row = f"{self.labels[i-1]}\t"
                for j in range(1, len(self.stats_params) + 1):
                    if j < len(self.stats_params) and self.stats_params[j-1][1] == "Y":
                        if self.results_array[2, i, j] == self.global_missing_code:
                            row += "---\t"
                        else:
                            row += f"{self.results_array[2, i, j]:.3f}\t"
                result_text += row + "\n"
        
        results_dialog.set_results(result_text)
        results_dialog.exec_()
    
    def delta_stats(self):
        """
        Calculate delta statistics between base period and three future periods
        """
        # Open dialog to get period dates
        delta_dialog = DeltaPeriodsDialog(parent=self)
        if delta_dialog.exec_():
            # Get period dates
            self.base_start, self.base_end = delta_dialog.get_base_period()
            self.period_a_start, self.period_a_end = delta_dialog.get_period_a()
            self.period_b_start, self.period_b_end = delta_dialog.get_period_b()
            self.period_c_start, self.period_c_end = delta_dialog.get_period_c()
            self.delta_wanted = delta_dialog.get_delta_type()
            
            # Calculate base period stats
            self.error_occurred = False
            self.calc_stats(self.base_start, self.base_end, True)
            
            if not self.error_occurred and not self.escape_processed:
                self.print_results(True)
                
                # Store base results
                base_results = np.copy(self.results_array[1, :, :])
                
                # Calculate period A stats
                self.calc_stats(self.period_a_start, self.period_a_end, True)
                
                if not self.error_occurred and not self.escape_processed:
                    # Calculate deltas
                    for i in range(1, 18):
                        for j in range(1, len(self.stats_params) + 1):
                            if j < len(self.stats_params) and self.stats_params[j-1][1] == "Y":
                                if self.delta_wanted == 1:  # Percentage
                                    if (abs(base_results[i, j]) < 0.005 or 
                                        base_results[i, j] == self.global_missing_code or 
                                        self.results_array[1, i, j] == self.global_missing_code):
                                        self.deltaresults[i, j] = self.global_missing_code
                                    else:
                                        self.deltaresults[i, j] = 100 * ((self.results_array[1, i, j] - base_results[i, j]) / base_results[i, j])
                                else:  # Absolute
                                    if (base_results[i, j] == self.global_missing_code or 
                                        self.results_array[1, i, j] == self.global_missing_code):
                                        self.deltaresults[i, j] = self.global_missing_code
                                    else:
                                        self.deltaresults[i, j] = self.results_array[1, i, j] - base_results[i, j]
                    
                    # Calculate T-test
                    self.calculate_t_test(base_results)
                    
                    # Store T-test results for period A
                    for i in range(1, 18):
                        self.t_test_results_a[i, 1] = self.t_test_results[i, 1]
                        self.t_test_results_a[i, 2] = self.t_test_results[i, 2]
                    
                    # Print delta results
                    self.print_delta_results("2020s")
                    
                    # Calculate period B stats
                    self.calc_stats(self.period_b_start, self.period_b_end, True)
                    
                    if not self.error_occurred and not self.escape_processed:
                        # Calculate deltas
                        for i in range(1, 18):
                            for j in range(1, len(self.stats_params) + 1):
                                if j < len(self.stats_params) and self.stats_params[j-1][1] == "Y":
                                    if self.delta_wanted == 1:  # Percentage
                                        if (abs(base_results[i, j]) < 0.005 or 
                                            base_results[i, j] == self.global_missing_code or 
                                            self.results_array[1, i, j] == self.global_missing_code):
                                            self.deltaresults[i, j] = self.global_missing_code
                                        else:
                                            self.deltaresults[i, j] = 100 * ((self.results_array[1, i, j] - base_results[i, j]) / base_results[i, j])
                                    else:  # Absolute
                                        if (base_results[i, j] == self.global_missing_code or 
                                            self.results_array[1, i, j] == self.global_missing_code):
                                            self.deltaresults[i, j] = self.global_missing_code
                                        else:
                                            self.deltaresults[i, j] = self.results_array[1, i, j] - base_results[i, j]
                        
                        # Calculate T-test
                        self.calculate_t_test(base_results)
                        
                        # Store T-test results for period B
                        for i in range(1, 18):
                            self.t_test_results_b[i, 1] = self.t_test_results[i, 1]
                            self.t_test_results_b[i, 2] = self.t_test_results[i, 2]
                        
                        # Print delta results
                        self.print_delta_results("2050s")
                        
                        # Calculate period C stats
                        self.calc_stats(self.period_c_start, self.period_c_end, True)
                        
                        if not self.error_occurred and not self.escape_processed:
                            # Calculate deltas
                            for i in range(1, 18):
                                for j in range(1, len(self.stats_params) + 1):
                                    if j < len(self.stats_params) and self.stats_params[j-1][1] == "Y":
                                        if self.delta_wanted == 1:  # Percentage
                                            if (abs(base_results[i, j]) < 0.005 or 
                                                base_results[i, j] == self.global_missing_code or 
                                                self.results_array[1, i, j] == self.global_missing_code):
                                                self.deltaresults[i, j] = self.global_missing_code
                                            else:
                                                self.deltaresults[i, j] = 100 * ((self.results_array[1, i, j] - base_results[i, j]) / base_results[i, j])
                                        else:  # Absolute
                                            if (base_results[i, j] == self.global_missing_code or 
                                                self.results_array[1, i, j] == self.global_missing_code):
                                                self.deltaresults[i, j] = self.global_missing_code
                                            else:
                                                self.deltaresults[i, j] = self.results_array[1, i, j] - base_results[i, j]
                            
                            # Calculate T-test
                            self.calculate_t_test(base_results)
                            
                            # Store T-test results for period C
                            for i in range(1, 18):
                                self.t_test_results_c[i, 1] = self.t_test_results[i, 1]
                                self.t_test_results_c[i, 2] = self.t_test_results[i, 2]
                            
                            # Print delta results
                            self.print_delta_results("2080s")
                            
                            # Print T-test results
                            self.print_t_test_results()
    
    def calculate_t_test(self, base_results):
        """
        Calculate T-test between base period and current period
        """
        self.t_test_results = np.full((18, 3), self.global_missing_code, dtype=float)
        
        for i in range(1, 18):
            # Check if data are valid
            if (self.results_array[1, i, 14] == 0 or 
                base_results[i, 14] == 0 or 
                self.results_array[1, i, 14] == self.global_missing_code or 
                base_results[i, 14] == self.global_missing_code):
                self.t_test_results[i, 1] = self.global_missing_code
                self.t_test_results[i, 2] = self.global_missing_code
            elif (self.results_array[1, i, 1] == self.global_missing_code or 
                  base_results[i, 1] == self.global_missing_code):
                self.t_test_results[i, 1] = self.global_missing_code
                self.t_test_results[i, 2] = self.global_missing_code
            elif (self.results_array[1, i, 5] == self.global_missing_code or 
                  base_results[i, 5] == self.global_missing_code):
                self.t_test_results[i, 1] = self.global_missing_code
                self.t_test_results[i, 2] = self.global_missing_code
            else:
                # Calculate T-test
                t_test_denom = self.results_array[1, i, 5] / self.results_array[1, i, 14]
                t_test_denom += base_results[i, 5] / base_results[i, 14]
                t_test_denom = np.sqrt(t_test_denom)
                
                if t_test_denom < 0.005:  # Avoid small division
                    self.t_test_results[i, 1] = self.global_missing_code
                    self.t_test_results[i, 2] = self.global_missing_code
                else:
                    # Calculate T-test value
                    self.t_test_results[i, 1] = abs((base_results[i, 1] - self.results_array[1, i, 1]) / t_test_denom)
                    
                    # Calculate degrees of freedom
                    dov_denom = (base_results[i, 5] ** 2) / ((base_results[i, 14] ** 2) * (base_results[i, 14] + 1))
                    dov_denom += ((self.results_array[1, i, 5] ** 2) / ((self.results_array[1, i, 14] ** 2) * (self.results_array[1, i, 14] + 1)))
                    
                    dov_numerator = (base_results[i, 5] / base_results[i, 14])
                    dov_numerator += (self.results_array[1, i, 5] / self.results_array[1, i, 14])
                    dov_numerator = dov_numerator ** 2
                    
                    if dov_denom == 0:
                        self.t_test_results[i, 2] = self.global_missing_code
                    else:
                        self.t_test_results[i, 2] = (dov_numerator / dov_denom) - 2
    
    def print_delta_results(self, period):
        """
        Print delta results to file and display in a dialog
        """
        # Open file in append mode
        with open(self.save_file_root, 'a') as f:
            f.write("\n")
            f.write(f"DELTA STATISTICS for {period}")
            
            if self.delta_wanted == 1:
                f.write(" (percentage difference)\n")
            else:
                f.write(" (absolute difference)\n")
            
            f.write("\n")
            
            # Write column headers
            f.write("Month")
            for i in range(len(self.stats_params)):
                if self.stats_params[i][1] == "Y":
                    f.write(f",{self.stats_params[i][0]}")
            f.write("\n")
            
            # Write data for each period
            for i in range(1, 18):
                f.write(f"{self.labels[i-1]}")
                for j in range(1, len(self.stats_params) + 1):
                    if j < len(self.stats_params) and self.stats_params[j-1][1] == "Y":
                        f.write(f",{self.deltaresults[i, j]}")
                f.write("\n")
        
        # Display results in dialog
        results_dialog = ResultsDialog(parent=self)
        results_dialog.setWindowTitle(f"Delta Statistics for {period}")
        
        # Format text for dialog display
        result_text = f"DELTA STATISTICS for {period}"
        if self.delta_wanted == 1:
            result_text += " (percentage difference)\n\n"
        else:
            result_text += " (absolute difference)\n\n"
        
        # Format column headers
        header_row = "Month\t"
        for i in range(len(self.stats_params)):
            if self.stats_params[i][1] == "Y":
                header_row += f"{self.stats_params[i][0]}\t"
        result_text += header_row + "\n\n"
        
        # Format data rows
        for i in range(1, 18):
            row = f"{self.labels[i-1]}\t"
            for j in range(1, len(self.stats_params) + 1):
                if j < len(self.stats_params) and self.stats_params[j-1][1] == "Y":
                    if self.deltaresults[i, j] == self.global_missing_code:
                        row += "---\t"
                    else:
                        row += f"{self.deltaresults[i, j]:.3f}\t"
            result_text += row + "\n"
        
        results_dialog.set_results(result_text)
        results_dialog.exec_()
    
    def print_t_test_results(self):
        """
        Print T-test results to file and display in a dialog
        """
        # Open file in append mode
        with open(self.save_file_root, 'a') as f:
            f.write("\n")
            f.write("T Test Results\n")
            f.write("\n")
            f.write("Period,Period A,Period B,Period C\n")
            
            # Write T-test values
            for i in range(1, 18):
                f.write(f"{self.labels[i-1]}")
                f.write(f",{self.t_test_results_a[i, 1]}")
                f.write(f",{self.t_test_results_b[i, 1]}")
                f.write(f",{self.t_test_results_c[i, 1]}\n")
            
            f.write("\n")
            f.write("Degrees of Freedom for T Test\n")
            f.write("\n")
            f.write("Period,Period A,Period B,Period C\n")
            
            # Write degrees of freedom
            for i in range(1, 18):
                f.write(f"{self.labels[i-1]}")
                f.write(f",{int(round(self.t_test_results_a[i, 2]))}")
                f.write(f",{int(round(self.t_test_results_b[i, 2]))}")
                f.write(f",{int(round(self.t_test_results_c[i, 2]))}\n")
        
        # Display results in dialog
        results_dialog = ResultsDialog(parent=self)
        results_dialog.setWindowTitle("T-Test Results")
        
        # Format text for dialog display
        result_text = "T Test Results\n\n"
        result_text += "Period\tPeriod A\tPeriod B\tPeriod C\n\n"
        
        # Format T-test values, highlighting significant values
        for i in range(1, 18):
            row = f"{self.labels[i-1]}\t"
            
            # Period A
            if self.t_test_results_a[i, 1] == self.global_missing_code:
                row += "---\t"
            else:
                t_value = self.t_test_results_a[i, 1]
                if t_value > 1.96:  # Critical value at 0.025 point of t distribution
                    row += f"*{t_value:.3f}*\t"
                else:
                    row += f"{t_value:.3f}\t"
            
            # Period B
            if self.t_test_results_b[i, 1] == self.global_missing_code:
                row += "---\t"
            else:
                t_value = self.t_test_results_b[i, 1]
                if t_value > 1.96:
                    row += f"*{t_value:.3f}*\t"
                else:
                    row += f"{t_value:.3f}\t"
            
            # Period C
            if self.t_test_results_c[i, 1] == self.global_missing_code:
                row += "---"
            else:
                t_value = self.t_test_results_c[i, 1]
                if t_value > 1.96:
                    row += f"*{t_value:.3f}*"
                else:
                    row += f"{t_value:.3f}"
            
            result_text += row + "\n"
        
        result_text += "\nDegrees of Freedom for T Test\n\n"
        result_text += "Period\tPeriod A\tPeriod B\tPeriod C\n\n"
        
        # Format degrees of freedom
        for i in range(1, 18):
            row = f"{self.labels[i-1]}\t"
            
            if self.t_test_results_a[i, 2] == self.global_missing_code:
                row += "---\t"
            else:
                row += f"{int(round(self.t_test_results_a[i, 2]))}\t"
            
            if self.t_test_results_b[i, 2] == self.global_missing_code:
                row += "---\t"
            else:
                row += f"{int(round(self.t_test_results_b[i, 2]))}\t"
            
            if self.t_test_results_c[i, 2] == self.global_missing_code:
                row += "---"
            else:
                row += f"{int(round(self.t_test_results_c[i, 2]))}"
            
            result_text += row + "\n"
        
        result_text += "\n* Values > 1.96 are significant at the 95% confidence level"
        
        results_dialog.set_results(result_text)
        results_dialog.exec_()


class ResultsDialog(QDialog):
    """
    Dialog to display analysis results
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Analysis Results")
        self.resize(800, 600)
        
        layout = QVBoxLayout()
        
        self.results_text = QTextBrowser()
        self.results_text.setFont(QFont("Courier New", 10))
        layout.addWidget(self.results_text)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
        
        self.setLayout(layout)
    
    def set_results(self, text):
        """
        Set the results text
        """
        self.results_text.setPlainText(text)


class StatsSelectDialog(QDialog):
    """
    Dialog to select which statistics to calculate
    """
    def __init__(self, stats_params, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Statistics")
        self.resize(800, 400)  # Wider but less tall
        
        self.stats_params = stats_params.copy()
        
        main_layout = QVBoxLayout()
        
        # Create a horizontal layout for the statistics groups
        stats_horizontal_layout = QHBoxLayout()
        
        # Group statistics by type
        basic_group = QGroupBox("Basic Statistics")
        basic_layout = QVBoxLayout()
        
        distribution_group = QGroupBox("Distribution Statistics")
        distribution_layout = QVBoxLayout()
        
        precip_group = QGroupBox("Precipitation Statistics")
        precip_layout = QVBoxLayout()
        
        # Create checkboxes for each statistic
        self.stat_checkboxes = []
        
        for i, (name, enabled, desc) in enumerate(self.stats_params):
            checkbox = QCheckBox(f"{name} - {desc}")
            checkbox.setChecked(enabled == "Y")
            
            # Group statistics
            if i < 10:  # Basic statistics
                basic_layout.addWidget(checkbox)
            elif i < 15:  # Distribution statistics
                distribution_layout.addWidget(checkbox)
            else:  # Precipitation statistics
                precip_layout.addWidget(checkbox)
            
            self.stat_checkboxes.append(checkbox)
        
        basic_group.setLayout(basic_layout)
        distribution_group.setLayout(distribution_layout)
        precip_group.setLayout(precip_layout)
        
        # Add groups horizontally instead of vertically
        stats_horizontal_layout.addWidget(basic_group)
        stats_horizontal_layout.addWidget(distribution_group)
        stats_horizontal_layout.addWidget(precip_group)
        
        main_layout.addLayout(stats_horizontal_layout)
        
        # Horizontal layout for threshold settings
        threshold_row = QHBoxLayout()
        
        # Threshold settings in left column
        threshold_group = QGroupBox("Threshold Settings")
        threshold_layout = QGridLayout()  # Using grid layout for better organization
        
        # Precipitation threshold
        threshold_layout.addWidget(QLabel("Precipitation Threshold:"), 0, 0)
        self.thresh_value = QLineEdit("0.1")
        threshold_layout.addWidget(self.thresh_value, 0, 1)
        threshold_layout.addWidget(QLabel("mm"), 0, 2)
        
        # POT setting
        threshold_layout.addWidget(QLabel("Percentile Over Threshold:"), 1, 0)
        self.pot_value = QLineEdit("95")
        threshold_layout.addWidget(self.pot_value, 1, 1)
        threshold_layout.addWidget(QLabel("%"), 1, 2)
        
        # PBT setting
        threshold_layout.addWidget(QLabel("Percentile Below Threshold:"), 2, 0)
        self.pbt_value = QLineEdit("5")
        threshold_layout.addWidget(self.pbt_value, 2, 1)
        threshold_layout.addWidget(QLabel("%"), 2, 2)
        
        # Right column of threshold settings
        threshold_layout.addWidget(QLabel("Percentile:"), 0, 3)
        self.percentile_value = QLineEdit("90")
        threshold_layout.addWidget(self.percentile_value, 0, 4)
        threshold_layout.addWidget(QLabel("%"), 0, 5)
        
        # N-day total setting
        threshold_layout.addWidget(QLabel("N-Day Total:"), 1, 3)
        self.nday_value = QLineEdit("5")
        threshold_layout.addWidget(self.nday_value, 1, 4)
        threshold_layout.addWidget(QLabel("days"), 1, 5)
        
        threshold_group.setLayout(threshold_layout)
        main_layout.addWidget(threshold_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self.select_all)
        button_layout.addWidget(select_all_btn)
        
        clear_all_btn = QPushButton("Clear All")
        clear_all_btn.clicked.connect(self.clear_all)
        button_layout.addWidget(clear_all_btn)
        
        button_layout.addStretch()
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
    
    def select_all(self):
        """
        Select all statistics
        """
        for checkbox in self.stat_checkboxes:
            checkbox.setChecked(True)
    
    def clear_all(self):
        """
        Clear all statistics
        """
        for checkbox in self.stat_checkboxes:
            checkbox.setChecked(False)
    
    def get_updated_stats(self):
        """
        Get the updated statistics parameters
        """
        updated_stats = []
        
        for i, (name, _, desc) in enumerate(self.stats_params):
            enabled = "Y" if self.stat_checkboxes[i].isChecked() else "N"
            updated_stats.append((name, enabled, desc))
        
        return updated_stats


class DeltaPeriodsDialog(QDialog):
    """
    Dialog to set periods for delta statistics
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Delta Statistics Periods")
        
        layout = QVBoxLayout()
        
        # Base period
        base_group = QGroupBox("Base Period")
        base_layout = QHBoxLayout()
        
        base_layout.addWidget(QLabel("Start Date:"))
        self.base_start = QLineEdit("1961-01-01")
        base_layout.addWidget(self.base_start)
        
        base_layout.addWidget(QLabel("End Date:"))
        self.base_end = QLineEdit("1990-12-31")
        base_layout.addWidget(self.base_end)
        
        base_group.setLayout(base_layout)
        layout.addWidget(base_group)
        
        # Period A (2020s)
        period_a_group = QGroupBox("Period A (2020s)")
        period_a_layout = QHBoxLayout()
        
        period_a_layout.addWidget(QLabel("Start Date:"))
        self.period_a_start = QLineEdit("2010-01-01")
        period_a_layout.addWidget(self.period_a_start)
        
        period_a_layout.addWidget(QLabel("End Date:"))
        self.period_a_end = QLineEdit("2039-12-31")
        period_a_layout.addWidget(self.period_a_end)
        
        period_a_group.setLayout(period_a_layout)
        layout.addWidget(period_a_group)
        
        # Period B (2050s)
        period_b_group = QGroupBox("Period B (2050s)")
        period_b_layout = QHBoxLayout()
        
        period_b_layout.addWidget(QLabel("Start Date:"))
        self.period_b_start = QLineEdit("2040-01-01")
        period_b_layout.addWidget(self.period_b_start)
        
        period_b_layout.addWidget(QLabel("End Date:"))
        self.period_b_end = QLineEdit("2069-12-31")
        period_b_layout.addWidget(self.period_b_end)
        
        period_b_group.setLayout(period_b_layout)
        layout.addWidget(period_b_group)
        
        # Period C (2080s)
        period_c_group = QGroupBox("Period C (2080s)")
        period_c_layout = QHBoxLayout()
        
        period_c_layout.addWidget(QLabel("Start Date:"))
        self.period_c_start = QLineEdit("2070-01-01")
        period_c_layout.addWidget(self.period_c_start)
        
        period_c_layout.addWidget(QLabel("End Date:"))
        self.period_c_end = QLineEdit("2099-12-31")
        period_c_layout.addWidget(self.period_c_end)
        
        period_c_group.setLayout(period_c_layout)
        layout.addWidget(period_c_group)
        
        # Delta type
        delta_group = QGroupBox("Delta Type")
        delta_layout = QHBoxLayout()
        
        self.delta_percentage = QRadioButton("Percentage Change")
        self.delta_percentage.setChecked(True)
        delta_layout.addWidget(self.delta_percentage)
        
        self.delta_absolute = QRadioButton("Absolute Change")
        delta_layout.addWidget(self.delta_absolute)
        
        delta_group.setLayout(delta_layout)
        layout.addWidget(delta_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def get_base_period(self):
        """
        Get the base period start and end dates
        """
        try:
            start = datetime.datetime.strptime(self.base_start.text(), "%Y-%m-%d")
            end = datetime.datetime.strptime(self.base_end.text(), "%Y-%m-%d")
            return start, end
        except ValueError:
            QMessageBox.critical(self, "Error", "Invalid base period dates")
            return None, None
    
    def get_period_a(self):
        """
        Get period A start and end dates
        """
        try:
            start = datetime.datetime.strptime(self.period_a_start.text(), "%Y-%m-%d")
            end = datetime.datetime.strptime(self.period_a_end.text(), "%Y-%m-%d")
            return start, end
        except ValueError:
            QMessageBox.critical(self, "Error", "Invalid period A dates")
            return None, None
    
    def get_period_b(self):
        """
        Get period B start and end dates
        """
        try:
            start = datetime.datetime.strptime(self.period_b_start.text(), "%Y-%m-%d")
            end = datetime.datetime.strptime(self.period_b_end.text(), "%Y-%m-%d")
            return start, end
        except ValueError:
            QMessageBox.critical(self, "Error", "Invalid period B dates")
            return None, None
    
    def get_period_c(self):
        """
        Get period C start and end dates
        """
        try:
            start = datetime.datetime.strptime(self.period_c_start.text(), "%Y-%m-%d")
            end = datetime.datetime.strptime(self.period_c_end.text(), "%Y-%m-%d")
            return start, end
        except ValueError:
            QMessageBox.critical(self, "Error", "Invalid period C dates")
            return None, None
    
    def get_delta_type(self):
        """
        Get the delta type (1=percentage, 2=absolute)
        """
        return 1 if self.delta_percentage.isChecked() else 2