from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame, QComboBox, 
    QLineEdit, QListWidget, QFileDialog, QCheckBox, QRadioButton, QButtonGroup, 
    QGridLayout, QGroupBox, QSizePolicy, QMessageBox, QProgressBar, QSpacerItem
)
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import os
import csv
from datetime import datetime

class ContentWidget(QWidget):
    """
    A well-optimized UI layout based on the user's feedback.
    """
    def __init__(self):
        super().__init__()

        # --- Reset variables ---
        self.open_files = []
        self.global_kopout = False
        self.left_files_count = 0
        self.right_files_count = 0
        self.total_time_series_files = 0
        self.save_file = ""
        self.save_root = ""

        # ---default dates---
        self.global_start_date = "01/01/1948"
        self.global_end_date = "31/12/2017"
        self.global_n_days = "25567"

        # Define missing value code (used throughout the code)
        self.global_missing_code = -999.0

        # ---Default threshold values---
        self.percentile = 90
        self.spi_value = 3
        self.thresh = 0.1
        self.local_thresh = self.thresh
        self.pot_value = self.thresh
        self.nth_largest = 1
        self.largest_n_day = 1
        self.annual_percentile = 90
        self.pfl90_percentile = 90
        self.pnl90_percentile = 90
        self.total_stats_available = 23

        # --- Date-related variables ---
        self.CurrentDay = 1
        self.CurrentMonth = 1
        self.CurrentYear = 1948
        self.CurrentSeason = 1  #1=winter, 2=Spring, 3=Summer, 4=Autumn
        self.CurrentWaterYear = 1948
        
        # For checking period changes
        self.ThisMonth = 1
        self.ThisYear = 1948
        self.ThisSeason = 1
        self.ThisWaterYear = 1948
        
        # Settings for leap years
        self.YearLength = 1  # 1 = include leap days
        self.Leapvalue = 1  # 1 = add day, 0 = don't add day
        
        # --- Arrays for statistics calculations ---
        # Initialize arrays - Python uses 0-based indexing, but we'll mimic 1-based for compatibility
        max_files = 6
        max_years = 200
        max_months = 20
        max_stats = 25
        
        # Summary array to store statistics
        # VB: summaryArray(1 To 5, 1 To 200, 1 To 20, 1 To 25)
        self.summaryArray = [[[[self.global_missing_code for _ in range(max_stats)] 
                            for _ in range(max_months)]
                            for _ in range(max_years)]
                            for _ in range(max_files)]
        
        # Period array to store temporary data
        # VB: periodArray(1 To 5, 1 To 55000)
        max_days = 55000
        self.periodArray = [[self.global_missing_code for _ in range(max_days)] 
                            for _ in range(max_files)]
        
        # Arrays for SPI calculation
        # VB: RunningMonths(1 To 5, 1 To 2000, 1 To 5)
        max_running_months = 2000
        self.RunningMonths = [[[self.global_missing_code for _ in range(5)]
                            for _ in range(max_running_months)]
                            for _ in range(max_files)]
        
        # Arrays for spell statistics
        # VB: DrySpellArray(1 To 5, 1 To 366)
        max_spells = 366
        self.DrySpellArray = [[0 for _ in range(max_spells)] 
                            for _ in range(max_files)]
        self.WetSpellArray = [[0 for _ in range(max_spells)] 
                            for _ in range(max_files)]
        
        # Count of spells
        # VB: TotalDrySpells(1 To 5)
        self.TotalDrySpells = [0 for _ in range(max_files)]
        self.TotalWetSpells = [0 for _ in range(max_files)]
        
        # Arrays for results
        # VB: FractionResult(1 To 5, 1 To 200)
        self.FractionResult = [[self.global_missing_code for _ in range(max_years)]
                            for _ in range(max_files)]
        self.LongTermResults = [[self.global_missing_code for _ in range(max_years)]
                            for _ in range(max_files)]
        
        # Ensemble file flags
        # VB: EnsembleFile(1 To 5)
        self.EnsembleFile = [False for _ in range(max_files)]
        
        # Start and end years for analysis
        self.StartYear = 1
        self.EndYear = 1
        
        # Total months for SPI calculation
        self.TotalMonths = 0
        
        # List of selected files
        self.AllFilesList = []
        
        # --- Main Layout ---
        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(15, 15, 15, 15)
        mainLayout.setSpacing(12)
        self.setLayout(mainLayout)

        # --- Create a horizontal layout for the main content ---
        mainContentLayout = QHBoxLayout()
        mainLayout.addLayout(mainContentLayout)

        # --- Left Side: File Selection Section ---
        leftSideLayout = QVBoxLayout()
        leftSideLayout.setSpacing(10)

        # North File Selection
        self.fileSelectionLeft = self.CreateFileSelectionGroup("North File Selection")
        leftSideLayout.addWidget(self.fileSelectionLeft)

        # South File Selection
        self.fileSelectionRight = self.CreateFileSelectionGroup("South File Selection")
        leftSideLayout.addWidget(self.fileSelectionRight)

        # Add left side to main content layout
        mainContentLayout.addLayout(leftSideLayout)

        # --- Right Side: Time Period, Data Range, Save Results ---
        rightSideLayout = QVBoxLayout()
        rightSideLayout.setSpacing(30)

        # Time Period Selection
        timePeriodGroup = QGroupBox("Time Period")
        timePeriodLayout = QHBoxLayout()

        timePeriodLayout.setContentsMargins(10,15, 10, 15)

        self.DatesCombo = QComboBox()
        self.DatesCombo.addItems([
            "Raw Data", 
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December",
            "Winter", "Spring", "Summer", "Autumn", "Annual", "Water Year"
        ])

        self.DatesCombo.setFixedHeight(30)

        timePeriodLayout.addWidget(self.DatesCombo, alignment=Qt.AlignCenter)
        timePeriodGroup.setLayout(timePeriodLayout)
        rightSideLayout.addWidget(timePeriodGroup)

        rightSideLayout.addSpacing(15)

        # Date Range Box
        dataGroup = QGroupBox("Date")
        dataLayout = QGridLayout()

        dataLayout.setSpacing(12)
        dataLayout.setContentsMargins(10, 15, 10, 15)

        startLabel = QLabel("Start:")
        startLabel.setFont(QFont("Arial", 12))
        startLabel.setFixedWidth(50)
        startLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        endLabel = QLabel("End:")
        endLabel.setFont(QFont("Arial", 12)) 
        startLabel.setFixedWidth(50)
        startLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.startDateInput = QLineEdit()
        self.startDateInput.setPlaceholderText("01/01/1948")
        self.startDateInput.setFixedHeight(30)

        self.endDateInput = QLineEdit()
        self.endDateInput.setPlaceholderText("31/12/2017")
        self.endDateInput.setFixedHeight(30)

        dataLayout.addWidget(startLabel, 0, 0, Qt.AlignRight)
        dataLayout.addWidget(self.startDateInput, 0, 1)

        vSpacer = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed)
        dataLayout.addItem(vSpacer, 1, 0, 1, 2)

        dataLayout.addWidget(endLabel, 2, 0, Qt.AlignRight)
        dataLayout.addWidget(self.endDateInput, 2, 1)

        dataGroup.setLayout(dataLayout)
        dataGroup.setFixedHeight(140)
        rightSideLayout.addWidget(dataGroup)

        # Save Results Box
        saveGroup = QGroupBox("Save Results To")
        saveLayout = QVBoxLayout()
        saveLayout.setContentsMargins(5, 5, 5, 5)
        saveLayout.setSpacing(5)

        saveButtonsLayout = QHBoxLayout()

        self.selectSaveButton = QPushButton("📂 Select")
        self.selectSaveButton.font = QFont("Arial", 12)
        self.selectSaveButton.clicked.connect(self.SelectSaveFile)
        self.selectSaveButton.setFixedHeight(32)

        self.clearSaveButton = QPushButton("❌ Clear")
        self.clearSaveButton.font = QFont("Arial", 12)
        self.clearSaveButton.clicked.connect(self.ClearSaveFile)
        self.clearSaveButton.setFixedHeight(32)

        saveButtonsLayout.addWidget(self.selectSaveButton)
        saveButtonsLayout.addWidget(self.clearSaveButton)

        self.saveFileLabel = QLabel("File: *.CSV")
        self.saveFileLabel.setStyleSheet("border: 1px solid gray; padding: 5px;")

        saveLayout.addLayout(saveButtonsLayout)
        saveLayout.addWidget(self.saveFileLabel)
        saveGroup.setLayout(saveLayout)
        rightSideLayout.addWidget(saveGroup)

        # Add a stretch to push everything up
        rightSideLayout.addStretch(1)

        # Add right side to main content layout
        mainContentLayout.addLayout(rightSideLayout)

        # Set stretch factors to make left side take 3/4 of the width
        mainContentLayout.setStretchFactor(leftSideLayout, 3)
        mainContentLayout.setStretchFactor(rightSideLayout, 1)

        # --- Statistics Selection ---
        statsGroup = QGroupBox("Select Statistics")
        statsLayout = QGridLayout()

        statsLayout.setSpacing(1)
        statsLayout.setContentsMargins(2, 2, 2, 2)

        self.statsOptions = [
            "Sum", "Mean", "Maximum", "Winter/Summer ratio",
            "Maximum dry spell", "Maximum wet spell",
            "Dry day persistence", "Wet day persistence",
            "Partial Duration Series", "Percentile",
            "Standard Precipitation Index", "Peaks Over Threshold"
        ]

        # Create stat checkboxes and initialize statOptions array for compatibility
        self.statCheckboxes = []
        self.StatOptions = [False] * len(self.statsOptions)  # For compatibility with original code
        
        for i, stat in enumerate(self.statsOptions):
            checkbox = QCheckBox(stat)

            font = QFont()
            font.setPointSize(14)  # Set font size to 10 for better readability
            checkbox.setFont(font)

            checkbox.setStyleSheet("""
            QCheckBox {
                spacing: 1px;
                margin-top: 1px;
                margin-bottom: 1px;
                }
            """)

            if i == 0:  # Set Sum as default checked
                checkbox.setChecked(True)
                self.StatOptions[i] = True

            checkbox.stateChanged.connect(lambda state, idx=i: self.onStatOptionChanged(state, idx))
            self.statCheckboxes.append(checkbox)
            statsLayout.addWidget(checkbox, i // 3, i % 3)  # Three columns

        # --- Spell Duration Selection ---
        spellGroup = QGroupBox("Spell Duration Selection")
        spellLayout = QVBoxLayout()

        self.spellOptions = [
            "Mean dry spell", "Mean wet spell",
            "Median dry spell", "Median wet spell",
            "SD dry spell", "SD wet spell", "Spell length correlation"
        ]
        self.spellGroup = QButtonGroup()

        for option in self.spellOptions:
            radio = QRadioButton(option)

            font = QFont()
            font.setPointSize(14)  
            radio.setFont(font)

            self.spellGroup.addButton(radio)
            spellLayout.addWidget(radio)

        spellGroup.setLayout(spellLayout)
        spellGroup.setFixedHeight(300) 

        stat_rows = (len(self.statsOptions) + 2)/3
        statsLayout.addWidget(spellGroup, 0, 3, stat_rows, 1)

        # --- Threshold Inputs ---
        thresholdLayout = QGridLayout()

        self.percentileInput = QLineEdit()
        self.percentileInput.setPlaceholderText("90")
        self.percentileInput.setText("90")
        self.percentileInput.setFixedHeight(25)

        self.precipLongTermInput = QLineEdit()
        self.precipLongTermInput.setPlaceholderText("90")
        self.precipLongTermInput.setText("90")
        self.precipLongTermInput.setFixedHeight(25)

        self.numEventsInput = QLineEdit()
        self.numEventsInput.setPlaceholderText("90")
        self.numEventsInput.setText("90")
        self.numEventsInput.setFixedHeight(25)

        self.setupInputValidation()

        thresholdLayout.addWidget(QLabel("%Prec > annual %ile:"), 0, 0)
        thresholdLayout.addWidget(self.percentileInput, 0, 1)

        thresholdLayout.addWidget(QLabel("% All precip from events > long-term %ile:"), 1, 0)
        thresholdLayout.addWidget(self.precipLongTermInput, 1, 1)

        thresholdLayout.addWidget(QLabel("No. of events > long-term %ile:"), 2, 0)
        thresholdLayout.addWidget(self.numEventsInput, 2, 1)

        statsLayout.addLayout(thresholdLayout, stat_rows, 0, 3, 3)

        statsGroup.setLayout(statsLayout)
        mainLayout.addWidget(statsGroup)

        # --- Action Buttons ---
        #buttonLayout = QHBoxLayout()
        BottomButtonLayout = QHBoxLayout()

        self.generateButton = QPushButton("🚀 Generate")
        self.generateButton.setStyleSheet("background-color: #4CAF50; color: white; font-size: 14px; padding: 8px;")
        self.generateButton.clicked.connect(self.PlotData)  # Connect to PlotData method
        self.generateButton.setFixedHeight(30)
        BottomButtonLayout.addWidget(self.generateButton)

        self.resetButton = QPushButton("🔄 Reset")
        self.resetButton.setStyleSheet("background-color: #F44336; color: white; font-size: 14px; padding: 8px;")
        self.resetButton.clicked.connect(self.Reset_All)  # Connect to Reset_All method
        self.resetButton.setFixedHeight(30)
        BottomButtonLayout.addWidget(self.resetButton)

        self.helpButton = QPushButton("Help")
        self.helpButton.setStyleSheet("background-color: #0000FF; color: white; font-size: 14px; padding: 8px;")
        self.helpButton.clicked.connect(lambda: self.Help_Needed(1))
        self.helpButton.setFixedHeight(30)
        BottomButtonLayout.addWidget(self.helpButton)

        mainLayout.addLayout(BottomButtonLayout)


        # Add progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        mainLayout.addWidget(self.progress_bar)

    def CreateFileSelectionGroup(self, title):
        group = QGroupBox(title)
        layout = QVBoxLayout()
        fileList = QListWidget()
        fileList.setFixedHeight(80)
        directoryBrowser = QListWidget()
        directoryBrowser.setFixedHeight(80)
        layout.addWidget(fileList)
        layout.addWidget(directoryBrowser)
        group.setLayout(layout)
        return group

    def SelectSaveFile(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Save To File", filter="CSV Files (*.csv)")
        if file_name:
            self.saveFileLabel.setText(f"File: {file_name}")

    def ClearSaveFile(self):
        self.saveFileLabel.setText("File: *.CSV")

    # Main functions

    def onStatOptionChanged(self, state, idx):
        """Handler for when a statistic checkbox is changed"""
        self.StatOptions[idx] = (state == Qt.Checked)
        
        # Special handling for Winter/Summer ratio
        if idx == 6 and state == Qt.Checked:  # Winter/summer ratio selected
            self.DatesCombo.setCurrentIndex(17)

    def setupInputValidation(self):
        """Connect validation handlers to input fields"""
        # Percentile input
        self.percentileInput.textChanged.connect(self.onPercentileChanged)
        self.percentileInput.editingFinished.connect(self.onPercentileEditFinished)
        
        # Long-term precipitation percentile input
        self.precipLongTermInput.textChanged.connect(self.onPrecipLongTermChanged)
        self.precipLongTermInput.editingFinished.connect(self.onPrecipLongTermEditFinished)
        
        # Number of events percentile input
        self.numEventsInput.textChanged.connect(self.onNumEventsChanged)
        self.numEventsInput.editingFinished.connect(self.onNumEventsEditFinished)
        
        # Date inputs
        self.startDateInput.textChanged.connect(self.onStartDateChanged)
        self.startDateInput.editingFinished.connect(self.onStartDateEditFinished)
        
        self.endDateInput.textChanged.connect(self.onEndDateChanged)
        self.endDateInput.editingFinished.connect(self.onEndDateEditFinished)


    def onPercentileChanged(self):
        """Handler for when percentile input text changes"""
        text = self.percentileInput.text()
        
        if not text or not self.isNumeric(text):
            return  # Wait for editingFinished to show error
        
        value = float(text)
        if value < 1 or value > 100:
            return  # Wait for editingFinished to show error
        
        self.percentile = int(value)

    def onPercentileEditFinished(self):
        """Validation when percentile input loses focus"""
        text = self.percentileInput.text()
        
        if not text or not self.isNumeric(text):
            QMessageBox.critical(self, "Error Message", "Percentile must be a value.")
            self.percentileInput.setText(str(self.percentile))
            return
        
        value = float(text)
        if value < 1 or value > 100:
            QMessageBox.critical(self, "Error Message", "Percentile must be between 1 and 100.")
            self.percentileInput.setText(str(self.percentile))
            return
        
        self.percentile = int(value)
        self.percentileInput.setText(str(self.percentile))

    def onPrecipLongTermChanged(self):
        """Handler for when pfl90 percentile input text changes"""
        text = self.precipLongTermInput.text()
        
        if not text or not self.isNumeric(text):
            return  # Wait for editingFinished to show error
        
        value = float(text)
        if value < 10 or value > 99:
            return  # Wait for editingFinished to show error
        
        self.pfl90_percentile = value

    def onPrecipLongTermEditFinished(self):
        """Validation when pfl90 percentile input loses focus"""
        text = self.precipLongTermInput.text()
        
        if not text or not self.isNumeric(text):
            QMessageBox.critical(self, "Error Message", "Entry must be a number.")
            self.precipLongTermInput.setText(str(self.pfl90_percentile))
            return
        
        value = float(text)
        if value < 10 or value > 99:
            QMessageBox.critical(self, "Error Message", "Value must be a number between 10 and 99.")
            self.precipLongTermInput.setText(str(self.pfl90_percentile))
            return
        
        self.pfl90_percentile = value

    def onNumEventsChanged(self):
        """Handler for when pnl90 percentile input text changes"""
        text = self.numEventsInput.text()
        
        if not text or not self.isNumeric(text):
            return  # Wait for editingFinished to show error
        
        value = float(text)
        if value < 10 or value > 99:
            return  # Wait for editingFinished to show error
        
        self.pnl90_percentile = value

    def onNumEventsEditFinished(self):
        """Validation when pnl90 percentile input loses focus"""
        text = self.numEventsInput.text()
        
        if not text or not self.isNumeric(text):
            QMessageBox.critical(self, "Error Message", "Entry must be a number.")
            self.numEventsInput.setText(str(self.pnl90_percentile))
            return
        
        value = float(text)
        if value < 10 or value > 99:
            QMessageBox.critical(self, "Error Message", "Value must be a number between 10 and 99.")
            self.numEventsInput.setText(str(self.pnl90_percentile))
            return
        
        self.pnl90_percentile = value

    def onStartDateChanged(self):
        """Handler for when start date input text changes"""
        # Just store the value, validation happens on focus loss
        self.FSDate = self.startDateInput.text()

    def onStartDateEditFinished(self):
        """Validation when start date input loses focus"""
        try:
            if not self.is_valid_date(self.FSDate):
                QMessageBox.critical(self, "Error Message", 
                                "Start date is invalid - it must be in the format dd/mm/yyyy.")
                self.startDateInput.setText(self.global_start_date)
                self.FSDate = self.global_start_date
                return
            
            start_date = datetime.strptime(self.FSDate, "%d/%m/%Y")
            end_date = datetime.strptime(self.FEdate, "%d/%m/%Y")
            global_start = datetime.strptime(self.global_start_date, "%d/%m/%Y")
            
            if start_date >= end_date:
                QMessageBox.critical(self, "Error Message", 
                                "End date must be later than start date.")
                self.startDateInput.setText(self.global_start_date)
                self.FSDate = self.global_start_date
                return
                
            if global_start > start_date:
                QMessageBox.critical(self, "Error Message", 
                                "Fit start date must be later than record start date.")
                self.startDateInput.setText(self.global_start_date)
                self.FSDate = self.global_start_date
                return
            
            # Update number of days
            days = (end_date - start_date).days + 1
            # If you have a days display field, update it here
            
        except Exception as e:
            print(f"Error validating start date: {str(e)}")
            self.Mini_Reset()
            self.startDateInput.setText(self.global_start_date)
            self.FSDate = self.global_start_date

    def onEndDateChanged(self):
        """Handler for when end date input text changes"""
        # Just store the value, validation happens on focus loss
        self.FEdate = self.endDateInput.text()

    def onEndDateEditFinished(self):
        """Validation when end date input loses focus"""
        try:
            if not self.is_valid_date(self.FEdate):
                QMessageBox.critical(self, "Error Message", 
                                "End date is invalid - it must be in the format dd/mm/yyyy.")
                self.endDateInput.setText(self.global_end_date)
                self.FEdate = self.global_end_date
                return
            
            start_date = datetime.strptime(self.FSDate, "%d/%m/%Y")
            end_date = datetime.strptime(self.FEdate, "%d/%m/%Y")
            global_end = datetime.strptime(self.global_end_date, "%d/%m/%Y")
            
            if start_date >= end_date:
                QMessageBox.critical(self, "Error Message", 
                                "End date must be later than start date.")
                self.endDateInput.setText(self.global_end_date)
                self.FEdate = self.global_end_date
                return
                
            if global_end < end_date:
                QMessageBox.critical(self, "Error Message", 
                                "Fit end date must be earlier than record end date.")
                self.endDateInput.setText(self.global_end_date)
                self.FEdate = self.global_end_date
                return
            
            # Update number of days
            days = (end_date - start_date).days + 1
            # If you have a days display field, update it here
            
        except Exception as e:
            print(f"Error validating end date: {str(e)}")
            self.Mini_Reset()
            self.endDateInput.setText(self.global_end_date)
            self.FEdate = self.global_end_date

    def isNumeric(self, text):
        """Check if a string can be converted to a number"""
        try:
            float(text)
            return True
        except ValueError:
            return False

    def PlotData(self):
        try:
            # Initialize variables
            ok_to_plot = False
            ensemble_present = False
            
            # Set focus to save button to ensure all values are updated
            self.selectSaveButton.setFocus()
            
            # Check if user has made correct selections
            if self.total_time_series_files < 1:
                QMessageBox.critical(self, "Error Message", "You must select at least one file.")
                return
            elif self.total_time_series_files > 5:
                QMessageBox.critical(self, "Error Message", "You can only select up to a maximum of five files.")
                return
            elif not self.validate_start_date():
                # Start date not valid, error message already displayed
                return
            elif not self.validate_end_date():
                # End date not valid, error message already displayed
                return
            elif (datetime.strptime(self.global_end_date, "%d/%m/%Y") < 
                datetime.strptime(self.FEdate, "%d/%m/%Y")):
                QMessageBox.critical(self, "Error Message", 
                                "Fit end date must be earlier than record end date. Check program settings.")
                self.endDateInput.setText(self.global_end_date)
                return
            elif (self.statCheckboxes[6].isChecked() and self.DatesCombo.currentIndex() != 17):
                QMessageBox.critical(self, "Error Message", 
                                "You can only calculate Winter/Summer ratios with annual data. Please try again.")
                return
            elif ((datetime.strptime(self.FEdate, "%d/%m/%Y").year - 
                datetime.strptime(self.FSDate, "%d/%m/%Y").year > 10) and 
                (self.DatesCombo.currentIndex() == 0) and 
                (not self.statCheckboxes[4].isChecked())):
                QMessageBox.critical(self, "Error Message", 
                                "Maximum number of years you can plot as raw data is 10. Please try again.")
                return
            elif (datetime.strptime(self.FEdate, "%d/%m/%Y").year - 
                datetime.strptime(self.FSDate, "%d/%m/%Y").year > 150):
                QMessageBox.critical(self, "Error Message", 
                                "Maximum number of years you can work with is 150. Please try again.")
                return
            elif ((self.statCheckboxes[14].isChecked()) and (self.DatesCombo.currentIndex() > 16)):
                QMessageBox.critical(self, "Error Message", 
                                "You can only calculate Percentage Precipitation>Annual Percentile for monthly or seasonal data. Please try again.")
                return
            else:
                # All checks passed, proceed with plotting
                self.setCursor(Qt.WaitCursor)  # Set hourglass cursor
                
                # Close any open files
                # (In a real implementation, close file handles here)
                
                # Reset ensemble file flags
                for i in range(5):
                    self.EnsembleFile[i] = False
                
                # Show progress bar
                self.progress_bar.setVisible(True)
                self.progress_bar.setValue(0)
                self.progress_bar.setMaximum(100)
                self.progress_bar.setFormat("Creating Plot")
                
                # Allow processing of escape key
                # (In PyQt implementation, connect to keyPressEvent)
                
                # Clear the list of selected files
                self.AllFilesList = []
                
                # Open files and check if they're ensemble files
                file_no = 2  # File number 1 reserved for save file
                
                # Check left file list
                for i in range(self.fileSelectionLeft.findChild(QListWidget).count()):
                    item = self.fileSelectionLeft.findChild(QListWidget).item(i)
                    if item.isSelected():
                        self.AllFilesList.append(item.text())
                        
                        file_path = os.path.join(self.fileSelectionLeft.findChild(QListWidget).path, item.text())
                        try:
                            # Check if this is an ensemble file by reading first line
                            with open(file_path, 'r') as f:
                                dummy_string = f.readline()
                                if len(dummy_string) > 15:
                                    self.EnsembleFile[file_no - 2] = True
                                    ensemble_present = True
                            
                            # Reopen file for processing
                            # (In actual implementation, store file handles for later use)
                            file_no += 1
                        except Exception as e:
                            print(f"Error opening file {file_path}: {str(e)}")
                            self.Mini_Reset()
                            return
                
                # Check right file list
                for i in range(self.fileSelectionRight.findChild(QListWidget).count()):
                    item = self.fileSelectionRight.findChild(QListWidget).item(i)
                    if item.isSelected():
                        self.AllFilesList.append(item.text())
                        
                        file_path = os.path.join(self.fileSelectionRight.findChild(QListWidget).path, item.text())
                        try:
                            # Check if this is an ensemble file by reading first line
                            with open(file_path, 'r') as f:
                                dummy_string = f.readline()
                                if len(dummy_string) > 15:
                                    self.EnsembleFile[file_no - 2] = True
                                    ensemble_present = True
                            
                            # Reopen file for processing
                            # (In actual implementation, store file handles for later use)
                            file_no += 1
                        except Exception as e:
                            print(f"Error opening file {file_path}: {str(e)}")
                            self.Mini_Reset()
                            return
                
                # Warn user if ensemble files detected
                if ensemble_present:
                    QMessageBox.warning(self, "Warning Message", 
                                    "Warning - the data appear to contain multiple columns (ensembles). " +
                                    "Only the first column will be plotted.\n\n" +
                                    "Note - you can extract individual members using the Transform Screen.")
                
                # Process data based on selected statistics
                if self.statCheckboxes[4].isChecked():
                    # SPI option chosen - ignores DatesCombo
                    ok_to_plot = self.GenerateSPI()
                elif self.DatesCombo.currentIndex() == 0:
                    # Raw data selected
                    ok_to_plot = self.RawData()
                elif self.statCheckboxes[14].isChecked():
                    # % precipitation > annual maximum
                    ok_to_plot = self.GeneratePrecipAnnualMax()
                elif self.statCheckboxes[22].isChecked() or self.statCheckboxes[23].isChecked():
                    # pfl90 or pnl90 statistics
                    ok_to_plot = self.LongTermStats()
                else:
                    # Other statistics
                    ok_to_plot = self.GenerateData()
                
                if ok_to_plot:
                    # Save first value in time series array
                    series_data_first_value = self.TimeSeriesData[0][0]
                    
                    # Create and show the chart
                    # (In actual implementation, create a chart window)
                    print("Creating chart...")
                    
                    # Set legends to filenames
                    for i in range(self.total_time_series_files):
                        print(f"Legend {i+1}: {self.AllFilesList[i]}")
                    
                    # Set chart title based on selected statistic
                    chart_title = "Time Series Plot"
                    y_label = ""
                    
                    if self.statCheckboxes[4].isChecked():
                        chart_source = "SPI"
                    elif self.DatesCombo.currentIndex() == 0:
                        chart_source = "raw"
                    elif self.statCheckboxes[14].isChecked() or self.statCheckboxes[22].isChecked():
                        chart_source = "percentage"
                    else:
                        chart_source = "analysed"
                    
                    # Set Y-axis label based on selected statistic
                    if self.statCheckboxes[0].isChecked():
                        y_label = "Sum"
                    elif self.statCheckboxes[1].isChecked():
                        y_label = "Mean"
                    elif self.statCheckboxes[2].isChecked():
                        y_label = "Maximum"
                    elif self.statCheckboxes[3].isChecked():
                        y_label = "Percentile"
                    elif self.statCheckboxes[4].isChecked():
                        y_label = "SPI"
                    elif self.statCheckboxes[5].isChecked():
                        y_label = "PDS"
                    elif self.statCheckboxes[6].isChecked():
                        y_label = "Winter/Summer Ratio"
                    elif self.statCheckboxes[7].isChecked():
                        y_label = "Peaks Over Threshold"
                    elif self.statCheckboxes[8].isChecked():
                        y_label = f"{self.nth_largest} largest"
                    elif self.statCheckboxes[9].isChecked():
                        y_label = f"Largest {self.largest_n_day} Total"
                    elif self.statCheckboxes[10].isChecked():
                        y_label = "Maximum Dry Spell"
                    elif self.statCheckboxes[11].isChecked():
                        y_label = "Maximum Wet Spell"
                    elif self.statCheckboxes[12].isChecked():
                        y_label = "Mean Dry Spell"
                    elif self.statCheckboxes[13].isChecked():
                        y_label = "Mean Wet Spell"
                    elif self.statCheckboxes[14].isChecked():
                        y_label = "Percentage"
                    elif self.statCheckboxes[15].isChecked():
                        y_label = "Median Dry Spell"
                    elif self.statCheckboxes[16].isChecked():
                        y_label = "Median Wet Spell"
                    elif self.statCheckboxes[17].isChecked():
                        y_label = "SD Dry Spell"
                    elif self.statCheckboxes[18].isChecked():
                        y_label = "SD Wet Spell"
                    elif self.statCheckboxes[19].isChecked():
                        y_label = "Dry Day Persistence"
                    elif self.statCheckboxes[20].isChecked():
                        y_label = "Wet Day Persistence"
                    elif self.statCheckboxes[21].isChecked():
                        y_label = "Spell Length Correlation"
                    elif self.statCheckboxes[22].isChecked():
                        y_label = "Percentage"
                    elif self.statCheckboxes[23].isChecked():
                        y_label = "Percentage Precip>Long Term Percentile"
                    
                    print(f"Chart title: {chart_title}")
                    print(f"Y-axis label: {y_label}")
                    print(f"Chart source: {chart_source}")
                    
                    # Display the chart
                    # (In actual implementation, show chart window)
                    
                    # Save results if requested
                    if (self.save_root and 
                        (self.statCheckboxes[4].isChecked() or self.DatesCombo.currentIndex() != 0)):
                        self.SaveResults()
                else:
                    # Error occurred during data processing
                    if not self.global_kopout:
                        QMessageBox.critical(self, "Error Message", 
                                        "Sorry - have been unable to read in data correctly - please check settings.")
                    else:
                        # Reset flag so error can be shown next time
                        self.global_kopout = False
                
                # Close all open files
                # (In actual implementation, close file handles)
                
                # Reset cursor and hide progress bar
                self.setCursor(Qt.ArrowCursor)
                self.progress_bar.setVisible(False)
        
        except Exception as e:
            print(f"Error in PlotData: {str(e)}")
            self.Mini_Reset()
    
    def validate_start_date(self):
        """Helper function to validate start date"""
        try:
            if not self.is_valid_date(self.FSDate):
                QMessageBox.critical(self, "Error Message", 
                                   "Start date is invalid - it must be in the format dd/mm/yyyy.")
                self.startDateInput.setText(self.global_start_date)
                return False
            elif (datetime.strptime(self.FSDate, "%d/%m/%Y") >= 
                 datetime.strptime(self.FEdate, "%d/%m/%Y")):
                QMessageBox.critical(self, "Error Message", 
                                   "End date must be later than start date.")
                self.startDateInput.setText(self.global_start_date)
                return False
            elif (datetime.strptime(self.global_start_date, "%d/%m/%Y") > 
                 datetime.strptime(self.FSDate, "%d/%m/%Y")):
                QMessageBox.critical(self, "Error Message", 
                                   "Fit start date must be later than record start date.")
                self.startDateInput.setText(self.global_start_date)
                return False
            
            # Update days between dates
            days = (datetime.strptime(self.FEdate, "%d/%m/%Y") - 
                   datetime.strptime(self.FSDate, "%d/%m/%Y")).days + 1
            # (In actual implementation, update days display)
            
            return True
        except Exception as e:
            print(f"Error validating start date: {str(e)}")
            self.Mini_Reset()
            return False
    
    def validate_end_date(self):
        """Helper function to validate end date"""
        try:
            if not self.is_valid_date(self.FEdate):
                QMessageBox.critical(self, "Error Message", 
                                   "End date is invalid - it must be in the format dd/mm/yyyy.")
                self.endDateInput.setText(self.global_end_date)
                return False
            elif (datetime.strptime(self.FSDate, "%d/%m/%Y") >= 
                 datetime.strptime(self.FEdate, "%d/%m/%Y")):
                QMessageBox.critical(self, "Error Message", 
                                   "End date must be later than start date.")
                self.endDateInput.setText(self.global_end_date)
                return False
            elif (datetime.strptime(self.global_end_date, "%d/%m/%Y") < 
                 datetime.strptime(self.FEdate, "%d/%m/%Y")):
                QMessageBox.critical(self, "Error Message", 
                                   "Fit end date must be earlier than record end date.")
                self.endDateInput.setText(self.global_end_date)
                return False
            
            # Update days between dates
            days = (datetime.strptime(self.FEdate, "%d/%m/%Y") - 
                   datetime.strptime(self.FSDate, "%d/%m/%Y")).days + 1
            # (In actual implementation, update days display)
            
            return True
        except Exception as e:
            print(f"Error validating end date: {str(e)}")
            self.Mini_Reset()
            return False
    
    def is_valid_date(self, date_str):
        """Helper function to check if a string is a valid date"""
        try:
            datetime.strptime(date_str, "%d/%m/%Y")
            return True
        except ValueError:
            return False

    def RawData(self):
        try:
            # Calculate days to skip at the beginning
            total_to_read_in = (datetime.strptime(self.FSDate, "%d/%m/%Y") - 
                            datetime.strptime(self.global_start_date, "%d/%m/%Y")).days
            
            if total_to_read_in > 0:
                # Show progress bar
                self.progress_bar.setVisible(True)
                self.progress_bar.setValue(0)
                self.progress_bar.setMaximum(100)
            
            # Initialize variables 
            any_missing = False  # Track if any data points are missing
            
            # Set current date to global start date
            current_day = int(datetime.strptime(self.global_start_date, "%d/%m/%Y").day)
            current_month = int(datetime.strptime(self.global_start_date, "%d/%m/%Y").month)
            current_year = int(datetime.strptime(self.global_start_date, "%d/%m/%Y").year)
            total_numbers = 0
            
            # Skip unwanted data at the start of the file
            date_start = datetime(current_year, current_month, current_day)
            date_target = datetime.strptime(self.FSDate, "%d/%m/%Y")
            
            # Loop until we reach the start date for analysis
            while date_start <= date_target:
                # Check if user wants to exit
                if self.ExitAnalysis():
                    self.Mini_Reset()
                    return False
                
                # Skip data from all files
                for i in range(2, self.total_time_series_files + 2):
                    # In actual implementation, read and discard a line from each file
                    pass
                
                total_numbers += 1
                self.IncreaseDate()
                date_start = datetime(current_year, current_month, current_day)
                
                # Update progress bar
                progress_value = int((total_numbers / total_to_read_in) * 100)
                self.progress_bar.setValue(progress_value)
                
            # Now read in the data we want to analyze
            total_numbers = 0
            total_to_read_in = (datetime.strptime(self.FEdate, "%d/%m/%Y") - 
                            datetime.strptime(self.FSDate, "%d/%m/%Y")).days + 1
            
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.progress_bar.setMaximum(100)
            
            # Set current date to start date for analysis
            current_day = int(datetime.strptime(self.FSDate, "%d/%m/%Y").day)
            current_month = int(datetime.strptime(self.FSDate, "%d/%m/%Y").month)
            current_year = int(datetime.strptime(self.FSDate, "%d/%m/%Y").year)
            
            # Create a temporary array for the time series data
            time_series_data2 = [[None for _ in range(self.total_time_series_files + 1)] 
                            for _ in range(total_to_read_in + 1)]
            
            # Read in the data
            date_current = datetime(current_year, current_month, current_day)
            date_end = datetime.strptime(self.FEdate, "%d/%m/%Y")
            
            while date_current <= date_end:
                # Check if user wants to exit
                if self.ExitAnalysis():
                    self.Mini_Reset()
                    return False
                
                total_numbers += 1
                
                # Read data for the current day from each file
                for i in range(2, self.total_time_series_files + 2):
                    # In actual implementation, read data from file
                    # Here using placeholder value
                    if self.EnsembleFile[i-2]:
                        # Handle multi-column file
                        temp_double = 0  # Placeholder - would read first value from line
                    else:
                        # Handle single-column file
                        temp_double = 0  # Placeholder - would read value from file
                    
                    if temp_double == self.global_missing_code:
                        any_missing = True
                        time_series_data2[total_numbers-1][i-1] = None  # Empty value for missing data
                    else:
                        time_series_data2[total_numbers-1][i-1] = temp_double
                
                # Set category label
                time_series_data2[total_numbers-1][0] = str(total_numbers)
                
                # Increase date for next iteration
                self.IncreaseDate()
                date_current = datetime(current_year, current_month, current_day)
                
                # Update progress bar
                progress_value = int((total_numbers / total_to_read_in) * 100)
                self.progress_bar.setValue(progress_value)
            
            # Set time series length
            self.TimeSeriesLength = total_numbers
            
            # Transfer data to TimeSeriesData array
            self.TimeSeriesData = [[None for _ in range(self.total_time_series_files + 1)] 
                                for _ in range(total_numbers)]
            
            for i in range(total_numbers):
                for j in range(self.total_time_series_files + 1):
                    self.TimeSeriesData[i][j] = time_series_data2[i][j]
            
            # Make sure no "1" appears on x-axis to begin with
            self.TimeSeriesData[0][0] = " "
            
            if any_missing:
                print("Warning - some of the data were missing and will not be plotted.")
            
            return True
            
        except Exception as e:
            print(f"Error in RawData: {str(e)}")
            self.Mini_Reset()
            return False

    def GenerateData(self):
        try:
            # Calculate days to skip at the beginning
            total_to_read_in = (datetime.strptime(self.FSDate, "%d/%m/%Y") - 
                            datetime.strptime(self.global_start_date, "%d/%m/%Y")).days
            
            if total_to_read_in > 0:
                # Show progress bar
                self.progress_bar.setVisible(True)
                self.progress_bar.setValue(0)
                self.progress_bar.setMaximum(100)
                self.progress_bar.setFormat("Skipping Unnecessary Data")
            
            # Set current date to global start date
            current_day = int(datetime.strptime(self.global_start_date, "%d/%m/%Y").day)
            current_month = int(datetime.strptime(self.global_start_date, "%d/%m/%Y").month)
            current_year = int(datetime.strptime(self.global_start_date, "%d/%m/%Y").year)
            total_numbers = 0
            
            # Skip unwanted data at the start of the file
            date_start = datetime(current_year, current_month, current_day)
            date_target = datetime.strptime(self.FSDate, "%d/%m/%Y")
            
            # Loop until we reach the start date for analysis
            while date_start <= date_target:
                # Check if user wants to exit
                if self.ExitAnalysis():
                    self.Mini_Reset()
                    return False
                
                # Skip data from all files
                for i in range(2, self.total_time_series_files + 2):
                    # In actual implementation, read and discard a line from each file
                    pass
                
                total_numbers += 1
                self.IncreaseDate()
                date_start = datetime(current_year, current_month, current_day)
                
                # Update progress bar
                progress_value = int((total_numbers / total_to_read_in) * 100)
                self.progress_bar.setValue(progress_value)
            
            # Now read in the data we want to analyze
            total_numbers = 0
            total_to_read_in = (datetime.strptime(self.FEdate, "%d/%m/%Y") - 
                            datetime.strptime(self.FSDate, "%d/%m/%Y")).days + 1
            
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.progress_bar.setMaximum(100)
            self.progress_bar.setFormat("Reading in data for plot")
            
            # Set current date to start date for analysis
            current_day = int(datetime.strptime(self.FSDate, "%d/%m/%Y").day)
            current_month = int(datetime.strptime(self.FSDate, "%d/%m/%Y").month)
            current_year = int(datetime.strptime(self.FSDate, "%d/%m/%Y").year)
            current_season = self.GetSeason(current_month)
            current_water_year = self.GetWaterYear(current_month, current_year)
            
            # Initialize arrays for statistics
            sum_vals = [0] * (self.total_time_series_files + 1)
            max_value = [-10000] * (self.total_time_series_files + 1)
            total_missing = [0] * (self.total_time_series_files + 1)
            pds = [0] * (self.total_time_series_files + 1)
            pot_count = [0] * (self.total_time_series_files + 1)
            count = 0
            
            # Set up period tracking variables
            this_month = current_month
            this_year = current_year
            this_season = current_season
            this_water_year = current_water_year
            
            year_index = 1
            
            # Read in data and process by period
            date_current = datetime(current_year, current_month, current_day)
            date_end = datetime.strptime(self.FEdate, "%d/%m/%Y")
            
            while date_current <= date_end:
                # Check if user wants to exit
                if self.ExitAnalysis():
                    self.Mini_Reset()
                    return False
                
                # Check if we've reached the end of the current period
                if self.FinishedCurrentPeriod():
                    year_index = this_year - int(datetime.strptime(self.FSDate, "%d/%m/%Y").year) + 1
                    
                    # For each file, update summary array with period's statistics
                    for i in range(1, self.total_time_series_files + 1):
                        # Determine array position based on period type
                        if self.DatesCombo.currentIndex() >= 1 and self.DatesCombo.currentIndex() <= 12:
                            array_position = this_month
                        elif self.DatesCombo.currentIndex() >= 13 and self.DatesCombo.currentIndex() <= 16:
                            array_position = this_season + 12
                        elif self.DatesCombo.currentIndex() == 17:
                            array_position = 17  # Annual
                        elif self.statCheckboxes[6].isChecked():
                            array_position = this_season + 12  # Winter/summer ratio
                        else:
                            array_position = 18  # Water year
                        
                        # Check if all data are missing for this period
                        if total_missing[i] == count:
                            # Set all statistics to missing code
                            for j in range(1, self.total_stats_available + 1):
                                self.summaryArray[i][year_index][array_position][j] = self.global_missing_code
                        else:
                            # Calculate and store statistics
                            self.summaryArray[i][year_index][array_position][1] = sum_vals[i]
                            self.summaryArray[i][year_index][array_position][2] = max_value[i]
                            self.summaryArray[i][year_index][array_position][3] = count - total_missing[i]
                            self.summaryArray[i][year_index][array_position][4] = self.PercentilePeriodArray(i, count, self.percentile)
                            self.summaryArray[i][year_index][array_position][5] = sum_vals[i] / (count - total_missing[i])
                            self.summaryArray[i][year_index][array_position][6] = pds[i]
                            self.summaryArray[i][year_index][array_position][7] = pot_count[i]
                            self.summaryArray[i][year_index][array_position][8] = self.FindNthLargest(i, count)
                            self.summaryArray[i][year_index][array_position][9] = self.FindLargestNDayTotal(i, count)
                            self.summaryArray[i][year_index][array_position][10] = self.FindMaxDrySpell(i, count)
                            self.summaryArray[i][year_index][array_position][11] = self.FindMaxWetSpell(i, count)
                            self.summaryArray[i][year_index][array_position][12] = self.FindMeanDrySpell(i, count)
                            self.summaryArray[i][year_index][array_position][13] = self.FindMeanWetSpell(i, count)
                            self.summaryArray[i][year_index][array_position][15] = self.FindMedianDrySpell(i, count)
                            self.summaryArray[i][year_index][array_position][16] = self.FindMedianWetSpell(i, count)
                            self.summaryArray[i][year_index][array_position][17] = self.FindSDDrySpell(i, count)
                            self.summaryArray[i][year_index][array_position][18] = self.FindSDWetSpell(i, count)
                            self.summaryArray[i][year_index][array_position][19] = self.FindDDPersistence(i, count)
                            self.summaryArray[i][year_index][array_position][20] = self.FindWDPersistence(i, count)
                            self.summaryArray[i][year_index][array_position][21] = self.FindSpellLengthCorrelation(i, count)
                    
                    # Reset statistics for next period
                    for i in range(1, self.total_time_series_files + 1):
                        sum_vals[i] = 0
                        max_value[i] = -10000
                        total_missing[i] = 0
                        pds[i] = 0
                        pot_count[i] = 0
                    count = 0
                
                # Read data for the current day
                count += 1
                total_numbers += 1
                
                for i in range(2, self.total_time_series_files + 2):
                    # In actual implementation, read data from file
                    # Here using placeholder
                    value = 0  # Placeholder - would be actual data
                    
                    if self.EnsembleFile[i-2]:
                        # Handle multi-column file
                        value = 0  # Placeholder - would read first value from line
                    else:
                        # Handle single-column file
                        value = 0  # Placeholder - would read value from file
                    
                    # Store value in period array
                    self.periodArray[i-1][count] = value
                    
                    # Update statistics
                    if value == self.global_missing_code:
                        total_missing[i-1] += 1
                    else:
                        sum_vals[i-1] += value
                        if max_value[i-1] < value:
                            max_value[i-1] = value
                        # For Partial Duration Series
                        pds[i-1] += (value - self.local_thresh)
                        # For Peaks Over Threshold
                        if value > self.pot_value:
                            pot_count[i-1] += 1
                
                # Save current period values
                this_month = current_month
                this_year = current_year
                this_season = current_season
                this_water_year = current_water_year
                
                # Increase date for next iteration
                self.IncreaseDate()
                date_current = datetime(current_year, current_month, current_day)
                
                # Update progress bar
                progress_value = int((total_numbers / total_to_read_in) * 100)
                self.progress_bar.setValue(progress_value)
                self.progress_bar.setFormat("Generating Time Series Plot")
            
            # Process the last period's data
            year_index = this_year - int(datetime.strptime(self.FSDate, "%d/%m/%Y").year) + 1
            
            # Determine array position for last period
            if self.statCheckboxes[6].isChecked():  # Winter/summer ratio
                array_position = this_season + 12
                if this_season == 1 and int(datetime.strptime(self.FEdate, "%d/%m/%Y").month) == 12:
                    year_index += 1  # Adjust for winter spanning year boundary
            elif self.DatesCombo.currentIndex() >= 1 and self.DatesCombo.currentIndex() <= 12:
                array_position = this_month
            elif self.DatesCombo.currentIndex() >= 13 and self.DatesCombo.currentIndex() <= 16:
                array_position = this_season + 12
                if this_season == 1 and int(datetime.strptime(self.FEdate, "%d/%m/%Y").month) == 12:
                    year_index += 1  # Adjust for winter spanning year boundary
            elif self.DatesCombo.currentIndex() == 17:
                array_position = 17  # Annual
            else:
                array_position = 18  # Water year
                if this_month >= 10:
                    year_index += 1  # Adjust for water year boundary
            
            # Update summary array with the last period's statistics
            for i in range(1, self.total_time_series_files + 1):
                # Check if all data are missing for this period
                if total_missing[i] == count:
                    # Set all statistics to missing code
                    for j in range(1, self.total_stats_available + 1):
                        self.summaryArray[i][year_index][array_position][j] = self.global_missing_code
                else:
                    # Calculate and store statistics
                    self.summaryArray[i][year_index][array_position][1] = sum_vals[i]
                    self.summaryArray[i][year_index][array_position][2] = max_value[i]
                    self.summaryArray[i][year_index][array_position][3] = count - total_missing[i]
                    self.summaryArray[i][year_index][array_position][4] = self.PercentilePeriodArray(i, count, self.percentile)
                    self.summaryArray[i][year_index][array_position][5] = sum_vals[i] / (count - total_missing[i])
                    self.summaryArray[i][year_index][array_position][6] = pds[i]
                    self.summaryArray[i][year_index][array_position][7] = pot_count[i]
                    self.summaryArray[i][year_index][array_position][8] = self.FindNthLargest(i, count)
                    self.summaryArray[i][year_index][array_position][9] = self.FindLargestNDayTotal(i, count)
                    self.summaryArray[i][year_index][array_position][10] = self.FindMaxDrySpell(i, count)
                    self.summaryArray[i][year_index][array_position][11] = self.FindMaxWetSpell(i, count)
                    self.summaryArray[i][year_index][array_position][12] = self.FindMeanDrySpell(i, count)
                    self.summaryArray[i][year_index][array_position][13] = self.FindMeanWetSpell(i, count)
                    self.summaryArray[i][year_index][array_position][15] = self.FindMedianDrySpell(i, count)
                    self.summaryArray[i][year_index][array_position][16] = self.FindMedianWetSpell(i, count)
                    self.summaryArray[i][year_index][array_position][17] = self.FindSDDrySpell(i, count)
                    self.summaryArray[i][year_index][array_position][18] = self.FindSDWetSpell(i, count)
                    self.summaryArray[i][year_index][array_position][19] = self.FindDDPersistence(i, count)
                    self.summaryArray[i][year_index][array_position][20] = self.FindWDPersistence(i, count)
                    self.summaryArray[i][year_index][array_position][21] = self.FindSpellLengthCorrelation(i, count)
            
            # Determine start and end years for output
            start_year = 1
            end_year = year_index
            
            # Adjust start and end years based on selected period and available data
            if self.statCheckboxes[6].isChecked():  # Winter/summer ratio
                if int(datetime.strptime(self.FEdate, "%d/%m/%Y").month) == 12:
                    end_year -= 1  # Don't have following year's ratio
                if int(datetime.strptime(self.FEdate, "%d/%m/%Y").month) < 6:
                    end_year -= 1  # Don't have a summer to divide by
                if int(datetime.strptime(self.FSDate, "%d/%m/%Y").month) > 2:
                    start_year = 2  # Don't have a start winter in first year
            elif self.DatesCombo.currentIndex() >= 1 and self.DatesCombo.currentIndex() <= 12:  # Month
                if self.DatesCombo.currentIndex() < int(datetime.strptime(self.FSDate, "%d/%m/%Y").month):
                    start_year = 2  # This month is before fit start date
                if self.DatesCombo.currentIndex() > int(datetime.strptime(self.FEdate, "%d/%m/%Y").month):
                    end_year -= 1  # This month is after fit end date
            elif self.DatesCombo.currentIndex() >= 13 and self.DatesCombo.currentIndex() <= 16:  # Season
                selected_season = self.DatesCombo.currentIndex() - 12
                if selected_season < self.GetSeason(int(datetime.strptime(self.FSDate, "%d/%m/%Y").month)):
                    start_year = 2  # Season comes before fit start date
                if (int(datetime.strptime(self.FEdate, "%d/%m/%Y").month) != 12 and 
                    selected_season > self.GetSeason(int(datetime.strptime(self.FEdate, "%d/%m/%Y").month))):
                    end_year -= 1  # Season comes after fit end date
                if (int(datetime.strptime(self.FEdate, "%d/%m/%Y").month) == 12 and 
                    self.DatesCombo.currentIndex() != 13):  # Not winter
                    end_year -= 1
            elif self.DatesCombo.currentIndex() == 18:  # Water year
                if int(datetime.strptime(self.FSDate, "%d/%m/%Y").month) >= 10:
                    start_year = 2  # Start date is in water year
            
            # Prepare data for plotting
            self.TimeSeriesLength = end_year - start_year + 1
            # Create and initialize the TimeSeriesData array
            self.TimeSeriesData = [[None for _ in range(self.total_time_series_files + 1)] 
                            for _ in range(self.TimeSeriesLength)]
            
            any_missing = False
            
            # Fill TimeSeriesData array based on selected statistic
            for i in range(1, self.total_time_series_files + 1):
                for j in range(1, self.TimeSeriesLength + 1):
                    idx = j + start_year - 1  # Adjusted index into summary array
                    
                    # Determine value based on selected statistic
                    if self.statCheckboxes[0].isChecked():  # Sum
                        if self.summaryArray[i][idx][self.DatesCombo.currentIndex()][1] == self.global_missing_code:
                            self.TimeSeriesData[j-1][i] = None
                            any_missing = True
                        else:
                            self.TimeSeriesData[j-1][i] = self.summaryArray[i][idx][self.DatesCombo.currentIndex()][1]
                    
                    elif self.statCheckboxes[1].isChecked():  # Mean
                        if self.summaryArray[i][idx][self.DatesCombo.currentIndex()][5] == self.global_missing_code:
                            self.TimeSeriesData[j-1][i] = None
                            any_missing = True
                        else:
                            self.TimeSeriesData[j-1][i] = self.summaryArray[i][idx][self.DatesCombo.currentIndex()][5]
                    
                    elif self.statCheckboxes[2].isChecked():  # Maximum
                        if self.summaryArray[i][idx][self.DatesCombo.currentIndex()][2] == self.global_missing_code:
                            self.TimeSeriesData[j-1][i] = None
                            any_missing = True
                        else:
                            self.TimeSeriesData[j-1][i] = self.summaryArray[i][idx][self.DatesCombo.currentIndex()][2]
                    
                    elif self.statCheckboxes[3].isChecked():  # Percentile
                        if self.summaryArray[i][idx][self.DatesCombo.currentIndex()][4] == self.global_missing_code:
                            self.TimeSeriesData[j-1][i] = None
                            any_missing = True
                        else:
                            self.TimeSeriesData[j-1][i] = self.summaryArray[i][idx][self.DatesCombo.currentIndex()][4]
                    
                    elif self.statCheckboxes[5].isChecked():  # Partial Duration Series
                        if self.summaryArray[i][idx][self.DatesCombo.currentIndex()][6] == self.global_missing_code:
                            self.TimeSeriesData[j-1][i] = None
                            any_missing = True
                        else:
                            self.TimeSeriesData[j-1][i] = self.summaryArray[i][idx][self.DatesCombo.currentIndex()][6]
                    
                    elif self.statCheckboxes[6].isChecked():  # Winter/Summer ratio
                        if (self.summaryArray[i][idx][13][1] == self.global_missing_code or 
                            self.summaryArray[i][idx][15][1] == self.global_missing_code or 
                            self.summaryArray[i][idx][15][1] == 0):
                            self.TimeSeriesData[j-1][i] = None
                            any_missing = True
                        else:
                            self.TimeSeriesData[j-1][i] = self.summaryArray[i][idx][13][1] / self.summaryArray[i][idx][15][1]
                    
                    elif self.statCheckboxes[7].isChecked():  # Peaks Over Threshold
                        if self.summaryArray[i][idx][self.DatesCombo.currentIndex()][7] == self.global_missing_code:
                            self.TimeSeriesData[j-1][i] = None
                            any_missing = True
                        else:
                            self.TimeSeriesData[j-1][i] = self.summaryArray[i][idx][self.DatesCombo.currentIndex()][7]
                    
                    elif self.statCheckboxes[8].isChecked():  # Nth Largest
                        if self.summaryArray[i][idx][self.DatesCombo.currentIndex()][8] == self.global_missing_code:
                            self.TimeSeriesData[j-1][i] = None
                            any_missing = True
                        else:
                            self.TimeSeriesData[j-1][i] = self.summaryArray[i][idx][self.DatesCombo.currentIndex()][8]
                    
                    elif self.statCheckboxes[9].isChecked():  # Largest N day total
                        if self.summaryArray[i][idx][self.DatesCombo.currentIndex()][9] == self.global_missing_code:
                            self.TimeSeriesData[j-1][i] = None
                            any_missing = True
                        else:
                            self.TimeSeriesData[j-1][i] = self.summaryArray[i][idx][self.DatesCombo.currentIndex()][9]
                    
                    elif self.statCheckboxes[10].isChecked():  # Max dry spell
                        if self.summaryArray[i][idx][self.DatesCombo.currentIndex()][10] == self.global_missing_code:
                            self.TimeSeriesData[j-1][i] = None
                            any_missing = True
                        else:
                            self.TimeSeriesData[j-1][i] = self.summaryArray[i][idx][self.DatesCombo.currentIndex()][10]
                    
                    elif self.statCheckboxes[11].isChecked():  # Max wet spell
                        if self.summaryArray[i][idx][self.DatesCombo.currentIndex()][11] == self.global_missing_code:
                            self.TimeSeriesData[j-1][i] = None
                            any_missing = True
                        else:
                            self.TimeSeriesData[j-1][i] = self.summaryArray[i][idx][self.DatesCombo.currentIndex()][11]
                    
                    elif self.statCheckboxes[12].isChecked():  # Mean dry spell
                        if self.summaryArray[i][idx][self.DatesCombo.currentIndex()][12] == self.global_missing_code:
                            self.TimeSeriesData[j-1][i] = None
                            any_missing = True
                        else:
                            self.TimeSeriesData[j-1][i] = self.summaryArray[i][idx][self.DatesCombo.currentIndex()][12]
                    
                    elif self.statCheckboxes[13].isChecked():  # Mean wet spell
                        if self.summaryArray[i][idx][self.DatesCombo.currentIndex()][13] == self.global_missing_code:
                            self.TimeSeriesData[j-1][i] = None
                            any_missing = True
                        else:
                            self.TimeSeriesData[j-1][i] = self.summaryArray[i][idx][self.DatesCombo.currentIndex()][13]
                    
                    elif self.statCheckboxes[15].isChecked():  # Median dry spell
                        if self.summaryArray[i][idx][self.DatesCombo.currentIndex()][15] == self.global_missing_code:
                            self.TimeSeriesData[j-1][i] = None
                            any_missing = True
                        else:
                            self.TimeSeriesData[j-1][i] = self.summaryArray[i][idx][self.DatesCombo.currentIndex()][15]
                    
                    elif self.statCheckboxes[16].isChecked():  # Median wet spell
                        if self.summaryArray[i][idx][self.DatesCombo.currentIndex()][16] == self.global_missing_code:
                            self.TimeSeriesData[j-1][i] = None
                            any_missing = True
                        else:
                            self.TimeSeriesData[j-1][i] = self.summaryArray[i][idx][self.DatesCombo.currentIndex()][16]
                    
                    elif self.statCheckboxes[17].isChecked():  # SD dry spell
                        if self.summaryArray[i][idx][self.DatesCombo.currentIndex()][17] == self.global_missing_code:
                            self.TimeSeriesData[j-1][i] = None
                            any_missing = True
                        else:
                            self.TimeSeriesData[j-1][i] = self.summaryArray[i][idx][self.DatesCombo.currentIndex()][17]
                    
                    elif self.statCheckboxes[18].isChecked():  # SD wet spell
                        if self.summaryArray[i][idx][self.DatesCombo.currentIndex()][18] == self.global_missing_code:
                            self.TimeSeriesData[j-1][i] = None
                            any_missing = True
                        else:
                            self.TimeSeriesData[j-1][i] = self.summaryArray[i][idx][self.DatesCombo.currentIndex()][18]
                    
                    elif self.statCheckboxes[19].isChecked():  # Dry day persistence
                        if self.summaryArray[i][idx][self.DatesCombo.currentIndex()][19] == self.global_missing_code:
                            self.TimeSeriesData[j-1][i] = None
                            any_missing = True
                        else:
                            self.TimeSeriesData[j-1][i] = self.summaryArray[i][idx][self.DatesCombo.currentIndex()][19]
                    
                    elif self.statCheckboxes[20].isChecked():  # Wet day persistence
                        if self.summaryArray[i][idx][self.DatesCombo.currentIndex()][20] == self.global_missing_code:
                            self.TimeSeriesData[j-1][i] = None
                            any_missing = True
                        else:
                            self.TimeSeriesData[j-1][i] = self.summaryArray[i][idx][self.DatesCombo.currentIndex()][20]
                    
                    elif self.statCheckboxes[21].isChecked():  # Spell length correlation
                        if self.summaryArray[i][idx][self.DatesCombo.currentIndex()][21] == self.global_missing_code:
                            self.TimeSeriesData[j-1][i] = None
                            any_missing = True
                        else:
                            self.TimeSeriesData[j-1][i] = self.summaryArray[i][idx][self.DatesCombo.currentIndex()][21]
                    
                    # Set year label for x-axis
                    if self.DatesCombo.currentIndex() == 18:  # Water year
                        self.TimeSeriesData[j-1][0] = str(int(datetime.strptime(self.FSDate, "%d/%m/%Y").year) + j + start_year - 3)
                    else:
                        self.TimeSeriesData[j-1][0] = str(int(datetime.strptime(self.FSDate, "%d/%m/%Y").year) + start_year + j - 2)
            
            if any_missing:
                print("Warning - some of the data were missing and will not be plotted.")
            
            return True
            
        except Exception as e:
            print(f"Error in GenerateData: {str(e)}")
            self.Mini_Reset()
            return False   

    def GenerateSPI(self):
        try:
            # Initialize variables for reading in data
            total_to_read_in = (datetime.strptime(self.global_start_date, "%d/%m/%Y") - 
                            datetime.strptime(self.FSDate, "%d/%m/%Y")).days
            
            if total_to_read_in > 0:
                # Show progress bar
                self.progress_bar.setVisible(True)
                self.progress_bar.setValue(0)
                self.progress_bar.setMaximum(100)
                
            # Set current date to the global start date
            current_day = int(datetime.strptime(self.global_start_date, "%d/%m/%Y").day)
            current_month = int(datetime.strptime(self.global_start_date, "%d/%m/%Y").month)
            current_year = int(datetime.strptime(self.global_start_date, "%d/%m/%Y").year)
            total_numbers = 0
            self.TotalMonths = 0  # Reset total months counter
            
            # Skip unwanted data at the start of the file
            date_start = datetime(current_year, current_month, current_day)
            date_target = datetime.strptime(self.FSDate, "%d/%m/%Y")
            
            # Loop until we reach the start date for analysis
            while date_start <= date_target:
                # Check if user wants to exit
                if self.ExitAnalysis():
                    self.Mini_Reset()
                    return False
                
                # Skip data from all files
                for i in range(2, self.total_time_series_files + 2):
                    # Skip a line from each file
                    # (Actual file reading would be implemented here)
                    pass
                
                total_numbers += 1
                self.IncreaseDate()
                date_start = datetime(current_year, current_month, current_day)
                
                # Update progress bar
                progress_value = int((total_numbers / total_to_read_in) * 100)
                self.progress_bar.setValue(progress_value)
            
            # Now read in the data we want to analyze
            total_numbers = 0
            total_to_read_in = (datetime.strptime(self.FEdate, "%d/%m/%Y") - 
                            datetime.strptime(self.FSDate, "%d/%m/%Y")).days + 1
            
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.progress_bar.setMaximum(100)
            
            # Set current date to start date for analysis
            current_day = int(datetime.strptime(self.FSDate, "%d/%m/%Y").day)
            current_month = int(datetime.strptime(self.FSDate, "%d/%m/%Y").month)
            current_year = int(datetime.strptime(self.FSDate, "%d/%m/%Y").year)
            
            # Initialize arrays for calculations
            sum_vals = [0] * (self.total_time_series_files + 1)
            total_missing = [0] * (self.total_time_series_files + 1)
            count = 0
            
            this_month = current_month
            this_year = current_year
            year_index = this_year - int(datetime.strptime(self.FSDate, "%d/%m/%Y").year) + 1
            
            # Read in data and calculate monthly sums
            date_current = datetime(current_year, current_month, current_day)
            date_end = datetime.strptime(self.FEdate, "%d/%m/%Y")
            
            while date_current <= date_end:
                # Check if user wants to exit
                if self.ExitAnalysis():
                    self.Mini_Reset()
                    return False
                
                # Check if we've reached the end of a month
                if self.FinishedCurrentPeriod():
                    year_index = this_year - int(datetime.strptime(self.FSDate, "%d/%m/%Y").year) + 1
                    
                    # Save monthly sums to summaryArray
                    for i in range(1, self.total_time_series_files + 1):
                        if total_missing[i] == count:  # All values were missing
                            self.summaryArray[i][year_index][this_month][1] = self.global_missing_code
                        else:
                            self.summaryArray[i][year_index][this_month][1] = sum_vals[i]
                    
                    self.TotalMonths += 1  # Increment total months counter
                    
                    # Reset counters for next month
                    for i in range(1, self.total_time_series_files + 1):
                        sum_vals[i] = 0
                        total_missing[i] = 0
                    count = 0
                
                # Read data for the current day
                total_numbers += 1
                count += 1
                
                for i in range(2, self.total_time_series_files + 2):
                    # Read a value from each file
                    # In a real implementation, you'd read from actual files
                    value_in = 0  # Placeholder - would be actual file data
                    
                    if value_in != self.global_missing_code:
                        if value_in > self.thresh:
                            sum_vals[i-1] += value_in
                    else:
                        total_missing[i-1] += 1
                
                # Update this_month and this_year
                this_month = current_month
                this_year = current_year
                
                # Increase date for next iteration
                self.IncreaseDate()
                date_current = datetime(current_year, current_month, current_day)
                
                # Update progress bar
                progress_value = int((total_numbers / total_to_read_in) * 100)
                self.progress_bar.setValue(progress_value)
            
            # Process the last month's data
            year_index = this_year - int(datetime.strptime(self.FSDate, "%d/%m/%Y").year) + 1
            
            for i in range(1, self.total_time_series_files + 1):
                if total_missing[i] == count:  # All values were missing
                    self.summaryArray[i][year_index][this_month][1] = self.global_missing_code
                else:
                    self.summaryArray[i][year_index][this_month][1] = sum_vals[i]
            
            self.TotalMonths += 1
            
            # Check if SPI period is valid
            if self.spi_value >= self.TotalMonths:
                print("The SPI index is longer than the fit period.")
                return False
            
            # Populate the RunningMonths array
            for i in range(1, self.total_time_series_files + 1):
                array_index = 1
                for j in range(1, year_index + 1):  # For each year
                    if j == 1:
                        start = int(datetime.strptime(self.FSDate, "%d/%m/%Y").month)
                    else:
                        start = 1
                    
                    if j == year_index:
                        finish = int(datetime.strptime(self.FEdate, "%d/%m/%Y").month)
                    else:
                        finish = 12
                    
                    for k in range(start, finish + 1):
                        self.RunningMonths[i-1][array_index-1][0] = self.summaryArray[i][j][k][1]  # Sum
                        self.RunningMonths[i-1][array_index-1][1] = j  # Year code
                        self.RunningMonths[i-1][array_index-1][2] = k  # Month code
                        array_index += 1
            
            # Calculate moving averages
            for i in range(1, self.total_time_series_files + 1):
                for j in range(1, self.TotalMonths - self.spi_value + 2):
                    month_sum = 0
                    month_missing = 0
                    
                    for k in range(1, self.spi_value + 1):
                        if self.RunningMonths[i-1][j+k-2][0] != self.global_missing_code:
                            month_sum += self.RunningMonths[i-1][j+k-2][0]
                        else:
                            month_missing += 1
                    
                    if month_missing == self.spi_value:  # All months missing
                        self.RunningMonths[i-1][j+k-2][3] = self.global_missing_code
                    else:
                        self.RunningMonths[i-1][j+k-2][3] = month_sum / (self.spi_value - month_missing)
            
            # Normalize the data (convert to SPI values)
            standard_deviation = [0] * (self.total_time_series_files + 1)
            mean_values = [0] * (self.total_time_series_files + 1)
            
            for i in range(1, self.total_time_series_files + 1):
                total_of_all = 0
                missing = 0
                available_months = self.TotalMonths - self.spi_value + 1
                
                # Calculate mean
                for j in range(self.spi_value, self.TotalMonths + 1):
                    if self.RunningMonths[i-1][j-1][3] == self.global_missing_code:
                        missing += 1
                    else:
                        total_of_all += self.RunningMonths[i-1][j-1][3]
                
                if missing == available_months:
                    print("Sorry - too many missing values to compute a solution.")
                    return False
                else:
                    mean_values[i] = total_of_all / (available_months - missing)
                
                # Calculate standard deviation
                missing = 0
                total_sqr_error = 0
                
                for j in range(self.spi_value, self.TotalMonths + 1):
                    if self.RunningMonths[i-1][j-1][3] == self.global_missing_code:
                        missing += 1
                    else:
                        total_sqr_error += ((self.RunningMonths[i-1][j-1][3] - mean_values[i]) ** 2)
                
                standard_deviation[i] = math.sqrt(total_sqr_error / (available_months - missing))
                
                # Normalize the data (SPI values)
                for j in range(self.spi_value, self.TotalMonths + 1):
                    if self.RunningMonths[i-1][j-1][3] == self.global_missing_code:
                        self.RunningMonths[i-1][j-1][4] = self.global_missing_code
                    else:
                        self.RunningMonths[i-1][j-1][4] = ((self.RunningMonths[i-1][j-1][3] - mean_values[i]) / 
                                                        standard_deviation[i])
            
            # Update summaryArray with SPI values
            for i in range(1, self.total_time_series_files + 1):
                for j in range(1, self.TotalMonths + 1):
                    self.summaryArray[i][int(self.RunningMonths[i-1][j-1][1])][int(self.RunningMonths[i-1][j-1][2])][5] = self.RunningMonths[i-1][j-1][4]
            
            # Prepare data for plotting
            self.TimeSeriesLength = self.TotalMonths - self.spi_value + 1
            # Create and initialize the TimeSeriesData array
            self.TimeSeriesData = [[0 for _ in range(self.total_time_series_files + 1)] 
                                for _ in range(self.TimeSeriesLength)]
            
            any_missing = False
            
            for i in range(1, self.total_time_series_files + 1):
                array_index = 1
                for j in range(1, year_index + 1):  # For each year
                    if j == 1:
                        start = int(datetime.strptime(self.FSDate, "%d/%m/%Y").month) + self.spi_value - 1
                        if start > 12:
                            start = start - 12
                            j = 2  # First data point must be in year 2
                    else:
                        start = 1
                    
                    if j == year_index:
                        finish = int(datetime.strptime(self.FEdate, "%d/%m/%Y").month)
                    else:
                        finish = 12
                    
                    for k in range(start, finish + 1):
                        if self.summaryArray[i][j][k][5] == self.global_missing_code:
                            self.TimeSeriesData[array_index-1][i] = None  # Empty value
                            any_missing = True
                        else:
                            self.TimeSeriesData[array_index-1][i] = self.summaryArray[i][j][k][5]
                        
                        self.TimeSeriesData[array_index-1][0] = " "  # Blank x-axis label
                        array_index += 1
                    
                    # Add year to x-axis label
                    self.TimeSeriesData[array_index-k+start-1][0] = str(int(datetime.strptime(self.FSDate, "%d/%m/%Y").year) + j - 1)
            
            if any_missing:
                print("Warning - some of the data were missing and will not be plotted.")
            
            return True
    
        except Exception as e:
            print(f"Error in GenerateSPI: {str(e)}")
            self.Mini_Reset()
            return False

    def GeneratePrecipAnnualMax(self):
        try:
            # Initialize variables
            total_to_read_in = (datetime.strptime(self.FSDate, "%d/%m/%Y") - 
                            datetime.strptime(self.global_start_date, "%d/%m/%Y")).days
            
            if total_to_read_in > 0:
                # Show progress bar
                self.progress_bar.setVisible(True)
                self.progress_bar.setValue(0)
                self.progress_bar.setMaximum(100)
            
            # Initialize year percentile array to store annual percentiles for each file and year
            year_percentile = [[self.global_missing_code for _ in range(200)] for _ in range(6)]  # [1-5][1-200]
            
            # Set current date to the global start date
            current_day = int(datetime.strptime(self.global_start_date, "%d/%m/%Y").day)
            current_month = int(datetime.strptime(self.global_start_date, "%d/%m/%Y").month)
            current_year = int(datetime.strptime(self.global_start_date, "%d/%m/%Y").year)
            total_numbers = 0
            
            # Skip unwanted data at the start of the file
            date_start = datetime(current_year, current_month, current_day)
            date_target = datetime.strptime(self.FSDate, "%d/%m/%Y")
            
            # Loop until we reach the start date for analysis
            while date_start <= date_target:
                # Check if user wants to exit
                if self.ExitAnalysis():
                    self.Mini_Reset()
                    return False
                
                # Skip data from all files
                for i in range(2, self.total_time_series_files + 2):
                    # Skip a line from each file
                    # (Actual file reading would be implemented here)
                    pass
                
                total_numbers += 1
                self.IncreaseDate()
                date_start = datetime(current_year, current_month, current_day)
                
                # Update progress bar
                progress_value = int((total_numbers / total_to_read_in) * 100)
                self.progress_bar.setValue(progress_value)
            
            # Now read in the data for annual percentile calculations
            total_numbers = 0
            total_to_read_in = (datetime.strptime(self.FEdate, "%d/%m/%Y") - 
                            datetime.strptime(self.FSDate, "%d/%m/%Y")).days + 1
            
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.progress_bar.setMaximum(100)
            
            # Reset current date to start date for analysis
            current_day = int(datetime.strptime(self.FSDate, "%d/%m/%Y").day)
            current_month = int(datetime.strptime(self.FSDate, "%d/%m/%Y").month)
            current_year = int(datetime.strptime(self.FSDate, "%d/%m/%Y").year)
            
            # Initialize count array - tracks valid data for each file
            count = [0] * 6
            
            this_year = current_year
            year_index = 1
            
            # Read annual data to calculate annual percentiles
            date_current = datetime(current_year, current_month, current_day)
            date_end = datetime.strptime(self.FEdate, "%d/%m/%Y")
            
            while date_current <= date_end:
                # Check if user wants to exit
                if self.ExitAnalysis():
                    self.Mini_Reset()
                    return False
                
                # Check if we've reached the end of a year
                if this_year != current_year:
                    year_index = this_year - int(datetime.strptime(self.FSDate, "%d/%m/%Y").year) + 1
                    
                    # Calculate percentiles for each file for this year
                    for i in range(1, self.total_time_series_files + 1):
                        if count[i] == 0:  # No valid data
                            year_percentile[i][year_index] = self.global_missing_code
                        else:
                            year_percentile[i][year_index] = self.PercentilePeriodArray(i, count[i], self.annual_percentile)
                    
                    # Reset counters
                    count = [0] * 6
                
                # Read data for the current day
                total_numbers += 1
                
                for i in range(2, self.total_time_series_files + 2):
                    # Read value from file
                    value_in = 0  # Placeholder - would be actual file data
                    
                    if value_in != self.global_missing_code and value_in >= self.thresh:
                        count[i-1] += 1
                        self.periodArray[i-1][count[i-1]] = value_in
                
                this_year = current_year
                
                # Increase date for next iteration
                self.IncreaseDate()
                date_current = datetime(current_year, current_month, current_day)
                
                # Update progress bar
                progress_value = int((total_numbers / total_to_read_in) * 100)
                self.progress_bar.setValue(progress_value)
            
            # Process the last year's data
            year_index = this_year - int(datetime.strptime(self.FSDate, "%d/%m/%Y").year) + 1
            
            for i in range(1, self.total_time_series_files + 1):
                if count[i] == 0:  # No valid data
                    year_percentile[i][year_index] = self.global_missing_code
                else:
                    year_percentile[i][year_index] = self.PercentilePeriodArray(i, count[i], self.annual_percentile)
            
            # Close and reopen files to process monthly/seasonal data
            # In practice, this might be handled differently in Python
            
            # Skip unwanted data at the start of the file again for second pass
            current_day = int(datetime.strptime(self.global_start_date, "%d/%m/%Y").day)
            current_month = int(datetime.strptime(self.global_start_date, "%d/%m/%Y").month)
            current_year = int(datetime.strptime(self.global_start_date, "%d/%m/%Y").year)
            total_numbers = 0
            
            date_start = datetime(current_year, current_month, current_day)
            date_target = datetime.strptime(self.FSDate, "%d/%m/%Y")
            
            # Loop until we reach the start date for analysis (second pass)
            while date_start <= date_target:
                # Skip data
                total_numbers += 1
                self.IncreaseDate()
                date_start = datetime(current_year, current_month, current_day)
            
            # Now read in data for period calculations
            total_numbers = 0
            total_to_read_in = (datetime.strptime(self.FEdate, "%d/%m/%Y") - 
                            datetime.strptime(self.FSDate, "%d/%m/%Y")).days + 1
            
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.progress_bar.setMaximum(100)
            
            # Reset current date to start date for second pass
            current_day = int(datetime.strptime(self.FSDate, "%d/%m/%Y").day)
            current_month = int(datetime.strptime(self.FSDate, "%d/%m/%Y").month)
            current_year = int(datetime.strptime(self.FSDate, "%d/%m/%Y").year)
            current_season = self.GetSeason(current_month)
            current_water_year = self.GetWaterYear(current_month, current_year)
            
            # Initialize count array again
            count = [0] * 6
            
            this_month = current_month
            this_year = current_year
            this_season = current_season
            this_water_year = current_water_year
            
            year_index = 1
            
            # Read data for period calculations (month/season)
            date_current = datetime(current_year, current_month, current_day)
            date_end = datetime.strptime(self.FEdate, "%d/%m/%Y")
            
            while date_current <= date_end:
                # Check if user wants to exit
                if self.ExitAnalysis():
                    self.Mini_Reset()
                    return False
                
                # Check if we've reached the end of the selected period
                if self.FinishedCurrentPeriod():
                    year_index = this_year - int(datetime.strptime(self.FSDate, "%d/%m/%Y").year) + 1
                    
                    # Only calculate if this period is the one selected by user
                    if (this_month == self.DatesCombo.currentIndex() or 
                        (this_season + 12) == self.DatesCombo.currentIndex()):
                        
                        for i in range(1, self.total_time_series_files + 1):
                            if count[i] == 0:  # No valid data
                                self.FractionResult[i-1][year_index] = self.global_missing_code
                            else:
                                # Calculate percentage above annual percentile
                                self.FractionResult[i-1][year_index] = self.FindPrecipAboveAnnPercentile(
                                    i, count[i], year_percentile[i][year_index])
                    
                    # Reset counters for next period
                    count = [0] * 6
                
                # Read data for the current day
                total_numbers += 1
                
                for i in range(2, self.total_time_series_files + 2):
                    # Read value from file
                    value_in = 0  # Placeholder - would be actual file data
                    
                    if value_in != self.global_missing_code and value_in >= self.thresh:
                        count[i-1] += 1
                        self.periodArray[i-1][count[i-1]] = value_in
                
                # Save current period values
                this_month = current_month
                this_year = current_year
                this_season = current_season
                this_water_year = current_water_year
                
                # Increase date for next iteration
                self.IncreaseDate()
                date_current = datetime(current_year, current_month, current_day)
                
                # Update progress bar
                progress_value = int((total_numbers / total_to_read_in) * 100)
                self.progress_bar.setValue(progress_value)
            
            # Process the last period's data
            year_index = this_year - int(datetime.strptime(self.FSDate, "%d/%m/%Y").year) + 1
            
            if (this_month == self.DatesCombo.currentIndex() or 
                (this_season + 12) == self.DatesCombo.currentIndex()):
                
                for i in range(1, self.total_time_series_files + 1):
                    if count[i] == 0:  # No valid data
                        self.FractionResult[i-1][year_index] = self.global_missing_code
                    else:
                        # Calculate percentage above annual percentile
                        self.FractionResult[i-1][year_index] = self.FindPrecipAboveAnnPercentile(
                            i, count[i], year_percentile[i][year_index])
            
            # Determine start and end years for output
            start_year = 1
            end_year = year_index
            
            # Adjust start and end years based on selected period
            if self.DatesCombo.currentIndex() >= 1 and self.DatesCombo.currentIndex() <= 12:  # Month
                if self.DatesCombo.currentIndex() < int(datetime.strptime(self.FSDate, "%d/%m/%Y").month):
                    start_year = 2
                if self.DatesCombo.currentIndex() > int(datetime.strptime(self.FEdate, "%d/%m/%Y").month):
                    end_year -= 1
            elif self.DatesCombo.currentIndex() >= 13 and self.DatesCombo.currentIndex() <= 16:  # Season
                selected_season = self.DatesCombo.currentIndex() - 12
                if selected_season < self.GetSeason(int(datetime.strptime(self.FSDate, "%d/%m/%Y").month)):
                    start_year = 2
                if (int(datetime.strptime(self.FEdate, "%d/%m/%Y").month) != 12 and 
                    selected_season > self.GetSeason(int(datetime.strptime(self.FEdate, "%d/%m/%Y").month))):
                    end_year -= 1
            
            # Prepare data for plotting
            self.TimeSeriesLength = end_year - start_year + 1
            # Create and initialize the TimeSeriesData array
            self.TimeSeriesData = [[0 for _ in range(self.total_time_series_files + 1)] 
                                for _ in range(self.TimeSeriesLength)]
            
            any_missing = False
            
            for i in range(1, self.total_time_series_files + 1):
                for j in range(1, self.TimeSeriesLength + 1):
                    if self.FractionResult[i-1][j+start_year-1] == self.global_missing_code:
                        self.TimeSeriesData[j-1][i] = None  # Empty value
                        any_missing = True
                    else:
                        self.TimeSeriesData[j-1][i] = self.FractionResult[i-1][j+start_year-1]
                    
                    if self.DatesCombo.currentIndex() == 18:  # Water year
                        self.TimeSeriesData[j-1][0] = str(int(datetime.strptime(self.FSDate, "%d/%m/%Y").year) + j + start_year - 3)
                    else:
                        self.TimeSeriesData[j-1][0] = str(int(datetime.strptime(self.FSDate, "%d/%m/%Y").year) + start_year + j - 2)
            
            if any_missing:
                print("Warning - some of the data were missing and will not be plotted.")
            
            return True
    
        except Exception as e:
            print(f"Error in GeneratePrecipAnnualMax: {str(e)}")
            self.Mini_Reset()
            return False

    def LongTermStats(self):
        try:
            # Initialize variables
            total_to_read_in = (datetime.strptime(self.FSDate, "%d/%m/%Y") - 
                            datetime.strptime(self.global_start_date, "%d/%m/%Y")).days
            
            if total_to_read_in > 0:
                # Show progress bar
                self.progress_bar.setVisible(True)
                self.progress_bar.setValue(0)
                self.progress_bar.setMaximum(100)
            
            # Initialize long term percentile array to store percentiles for each file
            long_term_percentile = [self.global_missing_code] * 6  # [1-5]
            
            # Set current date to the global start date
            current_day = int(datetime.strptime(self.global_start_date, "%d/%m/%Y").day)
            current_month = int(datetime.strptime(self.global_start_date, "%d/%m/%Y").month)
            current_year = int(datetime.strptime(self.global_start_date, "%d/%m/%Y").year)
            total_numbers = 0
            
            # Set cursor to hourglass
            self.setCursor(Qt.WaitCursor)
            
            # Skip unwanted data at the start of the file
            date_start = datetime(current_year, current_month, current_day)
            date_target = datetime.strptime(self.FSDate, "%d/%m/%Y")
            
            # Loop until we reach the start date for analysis
            while date_start <= date_target:
                # Check if user wants to exit
                if self.ExitAnalysis():
                    self.Mini_Reset()
                    return False
                
                # Skip data from all files
                for i in range(2, self.total_time_series_files + 2):
                    # Skip a line from each file
                    # (Actual file reading would be implemented here)
                    pass
                
                total_numbers += 1
                self.IncreaseDate()
                date_start = datetime(current_year, current_month, current_day)
                
                # Update progress bar
                progress_value = int((total_numbers / total_to_read_in) * 100)
                self.progress_bar.setValue(progress_value)
            
            # Now read in all data to calculate long-term percentiles
            total_numbers = 0
            total_to_read_in = (datetime.strptime(self.FEdate, "%d/%m/%Y") - 
                            datetime.strptime(self.FSDate, "%d/%m/%Y")).days + 1
            
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.progress_bar.setMaximum(100)
            
            # Reset current date to start date for analysis
            current_day = int(datetime.strptime(self.FSDate, "%d/%m/%Y").day)
            current_month = int(datetime.strptime(self.FSDate, "%d/%m/%Y").month)
            current_year = int(datetime.strptime(self.FSDate, "%d/%m/%Y").year)
            
            # Initialize count array - tracks valid data for each file
            count = [0] * 6
            
            # Read all data to calculate long-term percentile
            date_current = datetime(current_year, current_month, current_day)
            date_end = datetime.strptime(self.FEdate, "%d/%m/%Y")
            
            while date_current <= date_end:
                # Check if user wants to exit
                if self.ExitAnalysis():
                    self.Mini_Reset()
                    return False
                
                # Read data for the current day
                total_numbers += 1
                
                for i in range(2, self.total_time_series_files + 2):
                    # Read value from file
                    value_in = 0  # Placeholder - would be actual file data
                    
                    if value_in != self.global_missing_code and value_in >= self.thresh:
                        count[i-1] += 1
                        self.periodArray[i-1][count[i-1]] = value_in
                
                # Increase date for next iteration
                self.IncreaseDate()
                date_current = datetime(current_year, current_month, current_day)
                
                # Update progress bar
                progress_value = int((total_numbers / total_to_read_in) * 100)
                self.progress_bar.setValue(progress_value)
            
            # Get the correct percentile value based on selected statistic
            if self.statCheckboxes[22].isChecked():  # pfl90 selected
                ptile = self.pfl90_percentile
            else:  # pnl90 selected
                ptile = self.pnl90_percentile
            
            # Calculate long-term percentiles for each file
            for i in range(1, self.total_time_series_files + 1):
                long_term_percentile[i] = self.PercentilePeriodArray(i, count[i], ptile)
            
            # Close and reopen files to process monthly/seasonal data
            # In practice, this might be handled differently in Python
            
            # Skip unwanted data at the start of the file again for second pass
            current_day = int(datetime.strptime(self.global_start_date, "%d/%m/%Y").day)
            current_month = int(datetime.strptime(self.global_start_date, "%d/%m/%Y").month)
            current_year = int(datetime.strptime(self.global_start_date, "%d/%m/%Y").year)
            total_numbers = 0
            
            date_start = datetime(current_year, current_month, current_day)
            date_target = datetime.strptime(self.FSDate, "%d/%m/%Y")
            
            # Loop until we reach the start date for analysis (second pass)
            while date_start <= date_target:
                # Skip data
                total_numbers += 1
                self.IncreaseDate()
                date_start = datetime(current_year, current_month, current_day)
            
            # Now read in data for period calculations
            total_numbers = 0
            total_to_read_in = (datetime.strptime(self.FEdate, "%d/%m/%Y") - 
                            datetime.strptime(self.FSDate, "%d/%m/%Y")).days + 1
            
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.progress_bar.setMaximum(100)
            
            # Reset current date to start date for second pass
            current_day = int(datetime.strptime(self.FSDate, "%d/%m/%Y").day)
            current_month = int(datetime.strptime(self.FSDate, "%d/%m/%Y").month)
            current_year = int(datetime.strptime(self.FSDate, "%d/%m/%Y").year)
            current_season = self.GetSeason(current_month)
            current_water_year = self.GetWaterYear(current_month, current_year)
            
            # Arrays for tracking statistics
            rainfall_above_percentile = [0] * 6
            total_rainfall_in_period = [0] * 6
            count_of_events_above_percentile = [0] * 6
            count = [0] * 6
            
            this_month = current_month
            this_year = current_year
            this_season = current_season
            this_water_year = current_water_year
            
            year_index = 1
            
            # Read data for period calculations (month/season)
            date_current = datetime(current_year, current_month, current_day)
            date_end = datetime.strptime(self.FEdate, "%d/%m/%Y")
            
            while date_current <= date_end:
                # Check if user wants to exit
                if self.ExitAnalysis():
                    self.Mini_Reset()
                    return False
                
                # Check if we've reached the end of the selected period
                if self.FinishedCurrentPeriod():
                    year_index = this_year - int(datetime.strptime(self.FSDate, "%d/%m/%Y").year) + 1
                    
                    # Only calculate if this period is the one selected by user
                    if (this_month == self.DatesCombo.currentIndex() or 
                        (this_season + 12) == self.DatesCombo.currentIndex()):
                        
                        for i in range(1, self.total_time_series_files + 1):
                            if count[i] == 0:  # No valid data
                                self.LongTermResults[i-1][year_index] = self.global_missing_code
                            else:
                                if self.statCheckboxes[22].isChecked():  # pfl90 selected
                                    # Calculate percentage of rainfall from events above long-term percentile
                                    self.LongTermResults[i-1][year_index] = (rainfall_above_percentile[i] / 
                                                                        total_rainfall_in_period[i]) * 100
                                else:  # pnl90 selected
                                    # Count of events above long-term percentile
                                    self.LongTermResults[i-1][year_index] = count_of_events_above_percentile[i]
                    
                    # Reset counters for next period
                    rainfall_above_percentile = [0] * 6
                    total_rainfall_in_period = [0] * 6
                    count_of_events_above_percentile = [0] * 6
                    count = [0] * 6
                
                # Read data for the current day
                total_numbers += 1
                
                for i in range(2, self.total_time_series_files + 2):
                    # Read value from file
                    value_in = 0  # Placeholder - would be actual file data
                    
                    if value_in != self.global_missing_code and value_in >= self.thresh:
                        count[i-1] += 1
                        total_rainfall_in_period[i-1] += value_in
                        
                        if value_in > long_term_percentile[i-1]:
                            count_of_events_above_percentile[i-1] += 1
                            rainfall_above_percentile[i-1] += value_in
                
                # Save current period values
                this_month = current_month
                this_year = current_year
                this_season = current_season
                this_water_year = current_water_year
                
                # Increase date for next iteration
                self.IncreaseDate()
                date_current = datetime(current_year, current_month, current_day)
                
                # Update progress bar
                progress_value = int((total_numbers / total_to_read_in) * 100)
                self.progress_bar.setValue(progress_value)
            
            # Process the last period's data
            year_index = this_year - int(datetime.strptime(self.FSDate, "%d/%m/%Y").year) + 1
            
            if (this_month == self.DatesCombo.currentIndex() or 
                (this_season + 12) == self.DatesCombo.currentIndex()):
                
                for i in range(1, self.total_time_series_files + 1):
                    if count[i] == 0:  # No valid data
                        self.LongTermResults[i-1][year_index] = self.global_missing_code
                    else:
                        if self.statCheckboxes[22].isChecked():  # pfl90 selected
                            # Calculate percentage of rainfall from events above long-term percentile
                            self.LongTermResults[i-1][year_index] = (rainfall_above_percentile[i] / 
                                                                    total_rainfall_in_period[i]) * 100
                        else:  # pnl90 selected
                            # Count of events above long-term percentile
                            self.LongTermResults[i-1][year_index] = count_of_events_above_percentile[i]
            
            # Determine start and end years for output
            start_year = 1
            end_year = year_index
            
            # Adjust start and end years based on selected period
            if self.DatesCombo.currentIndex() >= 1 and self.DatesCombo.currentIndex() <= 12:  # Month
                if self.DatesCombo.currentIndex() < int(datetime.strptime(self.FSDate, "%d/%m/%Y").month):
                    start_year = 2
                if self.DatesCombo.currentIndex() > int(datetime.strptime(self.FEdate, "%d/%m/%Y").month):
                    end_year -= 1
            elif self.DatesCombo.currentIndex() >= 13 and self.DatesCombo.currentIndex() <= 16:  # Season
                selected_season = self.DatesCombo.currentIndex() - 12
                if selected_season < self.GetSeason(int(datetime.strptime(self.FSDate, "%d/%m/%Y").month)):
                    start_year = 2
                if (int(datetime.strptime(self.FEdate, "%d/%m/%Y").month) != 12 and 
                    selected_season > self.GetSeason(int(datetime.strptime(self.FEdate, "%d/%m/%Y").month))):
                    end_year -= 1
            
            # Prepare data for plotting
            self.TimeSeriesLength = end_year - start_year + 1
            # Create and initialize the TimeSeriesData array
            self.TimeSeriesData = [[0 for _ in range(self.total_time_series_files + 1)] 
                                for _ in range(self.TimeSeriesLength)]
            
            any_missing = False
            
            for i in range(1, self.total_time_series_files + 1):
                for j in range(1, self.TimeSeriesLength + 1):
                    if self.LongTermResults[i-1][j+start_year-1] == self.global_missing_code:
                        self.TimeSeriesData[j-1][i] = None  # Empty value
                        any_missing = True
                    else:
                        self.TimeSeriesData[j-1][i] = self.LongTermResults[i-1][j+start_year-1]
                    
                    if self.DatesCombo.currentIndex() == 18:  # Water year
                        self.TimeSeriesData[j-1][0] = str(int(datetime.strptime(self.FSDate, "%d/%m/%Y").year) + j + start_year - 3)
                    else:
                        self.TimeSeriesData[j-1][0] = str(int(datetime.strptime(self.FSDate, "%d/%m/%Y").year) + start_year + j - 2)
            
            if any_missing:
                print("Warning - some of the data were missing and will not be plotted.")
            
            # Reset cursor
            self.setCursor(Qt.ArrowCursor)
            
            return True
    
        except Exception as e:
            print(f"Error in LongTermStats: {str(e)}")
            self.Mini_Reset()
            return False
    
    #Support Functions

    def FindPrecipAboveAnnPercentile(self, file_no, size_of, ann_percentile):
        try:
            # Check if annual percentile is a missing value
            if ann_percentile == self.global_missing_code:
                return self.global_missing_code
            
            total_precip = 0
            total_precip_greater = 0
            
            # Calculate total precipitation and precipitation above threshold
            for i in range(size_of):
                value = self.periodArray[file_no][i]
                total_precip += value
                
                if value > ann_percentile:
                    total_precip_greater += value
            
            # Calculate percentage
            if total_precip == 0:
                return self.global_missing_code
            else:
                return (total_precip_greater / total_precip) * 100
    
        except Exception as e:
            print(f"Error in FindPrecipAboveAnnPercentile: {str(e)}")
            self.Mini_Reset()
            return self.global_missing_code

    def FinishedCurrentPeriod(self):
        result = False
        if self.StatOptions[4]:  # SPI chosen so need months
            if self.ThisMonth != self.CurrentMonth:
                result = True
        elif self.StatOptions[6]:  # Winter/summer ratio selected
            if self.ThisSeason != self.CurrentSeason:
                result = True
        elif self.DatesCombo.currentIndex() >= 1 and self.DatesCombo.currentIndex() <= 12:  # Month selected
            if self.ThisMonth != self.CurrentMonth:
                result = True        
        elif self.DatesCombo.currentIndex() >= 13 and self.DatesCombo.currentIndex() <= 16:  # Season selected
            if self.ThisSeason != self.CurrentSeason:
                result = True
        elif self.DatesCombo.currentIndex() == 17:  # Annual period selected
            if self.ThisYear != self.CurrentYear:
                result = True
        else:  # Water year selected
            if self.ThisWaterYear != self.CurrentWaterYear:
                result = True
        
        return result


    def GetWaterYear(self,month, year):
        if month >= 10:  # October, November, December
            return year
        else:  # January through September
            return year - 1

    def PercentilePeriodArray(self, file_no, size_of, percentile):
        try:
            # Create a filtered copy without missing values
            temp_array = []
            missing_value_count = 0
            
            for i in range(size_of):
                if self.periodArray[file_no][i] != self.global_missing_code:
                    temp_array.append(self.periodArray[file_no][i])
                else:
                    missing_value_count += 1
            
            local_size = size_of - missing_value_count
            
            # Handle edge cases
            if local_size == 0:
                return self.global_missing_code
            elif local_size == 1:
                return temp_array[0]
            
            # Sort the array in ascending order
            temp_array.sort()
            
            # Calculate percentile position
            position = 1 + (percentile * (local_size - 1) / 100)
            lower_bound = int(position)
            upper_bound = lower_bound + 1
            proportion = position - lower_bound
            
            # Calculate final percentile value
            if upper_bound >= local_size:
                return temp_array[local_size - 1]
            
            value_range = temp_array[upper_bound] - temp_array[lower_bound]
            percentile_value = temp_array[lower_bound] + (value_range * proportion)
            
            return percentile_value
    
        except Exception as e:
            print(f"Error in PercentilePeriodArray: {str(e)}")
            self.Mini_Reset()
            return self.global_missing_code

    def FindNthLargest(self, file_no, size_of):
        try:
            # Create a clean array without missing values
            clean_values = []
            missing_value_count = 0
            
            for i in range(size_of):
                if self.periodArray[file_no][i] != self.global_missing_code:
                    clean_values.append(self.periodArray[file_no][i])
                else:
                    missing_value_count += 1
            
            local_size = size_of - missing_value_count
            
            if local_size < self.nth_largest:
                # Insufficient data to get Nth largest
                return self.global_missing_code
            else:
                # Sort values in descending order
                sorted_values = sorted(clean_values, reverse=True)
                # Return the Nth largest value
                return sorted_values[self.nth_largest - 1]
        
        except Exception as e:
            print(f"Error in FindNthLargest: {str(e)}")
            self.Mini_Reset()
            return self.global_missing_code

    def FindLargestNDayTotal(self, file_no, size_of):
        try:
            if size_of < self.largest_n_day:
                # Not enough data for the requested window size
                return self.global_missing_code
            
            largest_sum = -10000  # Initialize with a very low value
            
            # Loop through all possible N-day windows
            for i in range(size_of - self.largest_n_day + 1):
                current_sum = 0
                
                # Calculate sum for this window
                for j in range(self.largest_n_day):
                    current_sum += self.periodArray[file_no][i + j]
                
                # Update if this sum is larger than previous largest
                if current_sum > largest_sum:
                    largest_sum = current_sum
            
            return largest_sum
    
        except Exception as e:
            print(f"Error in FindLargestNDayTotal: {str(e)}")
            self.Mini_Reset()
            return self.global_missing_code

    def FindMaxDrySpell(self, file_no, size_of):
        try:
        # Create dry spell array first
            self.CreateDrySpellArray(file_no, size_of)
            
            max_dry_count = 0
            
            # Find the longest dry spell
            if self.TotalDrySpells[file_no] > 0:
                for i in range(self.TotalDrySpells[file_no]):
                    if self.DrySpellArray[file_no][i] > max_dry_count:
                        max_dry_count = self.DrySpellArray[file_no][i]
            
            return max_dry_count
    
        except Exception as e:
            print(f"Error in FindMaxDrySpell: {str(e)}")
            self.Mini_Reset()
            return 0


    def FindMaxWetSpell(self, file_no, size_of):
        try:
            # Create wet spell array first
            self.CreateWetSpellArray(file_no, size_of)
            
            max_wet_count = 0
            
            # Find the longest wet spell
            if self.TotalWetSpells[file_no] > 0:
                for i in range(self.TotalWetSpells[file_no]):
                    if self.WetSpellArray[file_no][i] > max_wet_count:
                        max_wet_count = self.WetSpellArray[file_no][i]
            
            return max_wet_count
    
        except Exception as e:
            print(f"Error in FindMaxWetSpell: {str(e)}")
            self.Mini_Reset()
            return 0
    
    def CreateWetSpellArray(self, file_no, size_of):
        try:
            # Initialize counters
            wet_count = 0                         # Counter for consecutive wet days
            self.TotalWetSpells[file_no] = 0      # Reset count of wet spells for this file
            
            # Determine initial state
            if (self.periodArray[file_no][0] == self.global_missing_code or 
                self.periodArray[file_no][0] <= self.thresh):
                is_wet = False                    # Start in dry state
            else:
                is_wet = True                     # Start in wet state
                wet_count = 1
            
            # Process each day
            for i in range(1, size_of):
                # Case 1: Continuing wet spell
                if (is_wet and self.periodArray[file_no][i] > self.thresh):
                    wet_count += 1
                    
                # Case 2: End of wet spell (wet to dry or missing)
                elif (is_wet and (self.periodArray[file_no][i] <= self.thresh or 
                                self.periodArray[file_no][i] == self.global_missing_code)):
                    is_wet = False
                    self.TotalWetSpells[file_no] += 1
                    self.WetSpellArray[file_no][self.TotalWetSpells[file_no] - 1] = wet_count
                    wet_count = 0
                    
                # Case 3: Start of wet spell (dry to wet)
                elif (not is_wet and self.periodArray[file_no][i] > self.thresh):
                    is_wet = True
                    wet_count = 1
                
                # Case 4: Continuing dry spell (do nothing)
            
            # Check if we're still in a wet spell at the end of the period
            if wet_count > 0:
                self.TotalWetSpells[file_no] += 1
                self.WetSpellArray[file_no][self.TotalWetSpells[file_no] - 1] = wet_count
        
        except Exception as e:
            print(f"Error in CreateWetSpellArray: {str(e)}")
            self.Mini_Reset()

    def CreateDrySpellArray(self, file_no, size_of):
        try:
            # Initialize counters
            dry_count = 0                         # Counter for consecutive dry days
            self.TotalDrySpells[file_no] = 0      # Reset count of dry spells for this file
            
            # Determine initial state
            if (self.periodArray[file_no][0] == self.global_missing_code or 
                self.periodArray[file_no][0] > self.thresh):
                is_dry = False                    # Start in wet state
            else:
                is_dry = True                     # Start in dry state
                dry_count = 1
            
            # Process each day
            for i in range(1, size_of):
                # Case 1: Continuing dry spell
                if (is_dry and self.periodArray[file_no][i] <= self.thresh):
                    dry_count += 1
                    
                # Case 2: End of dry spell (dry to wet or missing)
                elif (is_dry and (self.periodArray[file_no][i] > self.thresh or 
                                self.periodArray[file_no][i] == self.global_missing_code)):
                    is_dry = False
                    self.TotalDrySpells[file_no] += 1
                    self.DrySpellArray[file_no][self.TotalDrySpells[file_no] - 1] = dry_count
                    dry_count = 0
                    
                # Case 3: Start of dry spell (wet to dry)
                elif (not is_dry and self.periodArray[file_no][i] <= self.thresh):
                    is_dry = True
                    dry_count = 1
                
                # Case 4: Continuing wet spell (do nothing)
            
            # Check if we're still in a dry spell at the end of the period
            if dry_count > 0:
                self.TotalDrySpells[file_no] += 1
                self.DrySpellArray[file_no][self.TotalDrySpells[file_no] - 1] = dry_count
        
        except Exception as e:
            print(f"Error in CreateDrySpellArray: {str(e)}")
            self.Mini_Reset()

    def FindMeanDrySpell(self, file_no, size_of):
        try:
            # Create dry spell array first
            self.CreateDrySpellArray(file_no, size_of)
            
            mean_dry_spell = 0
            spell_sum = 0
            
            if self.TotalDrySpells[file_no] > 0:
                for i in range(self.TotalDrySpells[file_no]):
                    spell_sum += self.DrySpellArray[file_no][i]
                
                mean_dry_spell = spell_sum / self.TotalDrySpells[file_no]
            
            return mean_dry_spell
    
        except Exception as e:
            print(f"Error in FindMeanDrySpell: {str(e)}")
            self.Mini_Reset()
            return 0

    def FindMeanWetSpell(self, file_no, size_of):
        try:
            # Create wet spell array first
            self.CreateWetSpellArray(file_no, size_of)
            
            mean_wet_spell = 0
            spell_sum = 0
            
            if self.TotalWetSpells[file_no] > 0:
                for i in range(self.TotalWetSpells[file_no]):
                    spell_sum += self.WetSpellArray[file_no][i]
                
                mean_wet_spell = spell_sum / self.TotalWetSpells[file_no]
            
            return mean_wet_spell
    
        except Exception as e:
            print(f"Error in FindMeanWetSpell: {str(e)}")
            self.Mini_Reset()
            return 0

    def FindMedianDrySpell(self, file_no, size_of):
        try:
            # Create dry spell array first
            self.CreateDrySpellArray(file_no, size_of)
            
            median_dry_spell = 0
            
            if self.TotalDrySpells[file_no] > 0:
                if self.TotalDrySpells[file_no] == 1:
                    # If only one spell, it's the median
                    median_dry_spell = self.DrySpellArray[file_no][0]
                else:
                    # Create a sorted copy of the dry spells
                    sorted_spells = sorted([self.DrySpellArray[file_no][i] for i in range(self.TotalDrySpells[file_no])])
                    
                    # Find median position
                    position = self.TotalDrySpells[file_no] // 2
                    
                    # Calculate median based on odd or even number of spells
                    if self.TotalDrySpells[file_no] % 2 != 0:  # Odd number
                        median_dry_spell = sorted_spells[position]
                    else:  # Even number
                        median_dry_spell = (sorted_spells[position - 1] + sorted_spells[position]) / 2
            
            return median_dry_spell
    
        except Exception as e:
            print(f"Error in FindMedianDrySpell: {str(e)}")
            self.Mini_Reset()
            return 0

    def FindMedianWetSpell(self, file_no, size_of):
        try:
            # Create wet spell array first
            self.CreateWetSpellArray(file_no, size_of)
            
            median_wet_spell = 0
            
            if self.TotalWetSpells[file_no] > 0:
                if self.TotalWetSpells[file_no] == 1:
                    # If only one spell, it's the median
                    median_wet_spell = self.WetSpellArray[file_no][0]
                else:
                    # Create a sorted copy of the wet spells
                    sorted_spells = sorted([self.WetSpellArray[file_no][i] for i in range(self.TotalWetSpells[file_no])])
                    
                    # Find median position
                    position = self.TotalWetSpells[file_no] // 2
                    
                    # Calculate median based on odd or even number of spells
                    if self.TotalWetSpells[file_no] % 2 != 0:  # Odd number
                        median_wet_spell = sorted_spells[position]
                    else:  # Even number
                        median_wet_spell = (sorted_spells[position - 1] + sorted_spells[position]) / 2
            
            return median_wet_spell
        
        except Exception as e:
            print(f"Error in FindMedianWetSpell: {str(e)}")
            self.Mini_Reset()
            return 0

    def FindSDDrySpell(self, file_no, size_of):
        try:
            # First get the mean - this also creates the dry spell array
            mean = self.FindMeanDrySpell(file_no, size_of)
            
            sd_dry_spell = 0
            
            # If mean is 0, there were no spells or they were all length 0
            if mean > 0:
                sum_squared_diff = 0
                
                # Calculate sum of squared differences from mean
                for i in range(self.TotalDrySpells[file_no]):
                    sum_squared_diff += (self.DrySpellArray[file_no][i] - mean) ** 2
                
                # Calculate standard deviation
                if self.TotalDrySpells[file_no] > 0:
                    sd_dry_spell = (sum_squared_diff / self.TotalDrySpells[file_no]) ** 0.5
            
            return sd_dry_spell
    
        except Exception as e:
            print(f"Error in FindSDDrySpell: {str(e)}")
            self.Mini_Reset()
            return 0

    def FindSDWetSpell(self, file_no, size_of):
        try:
            # First get the mean - this also creates the wet spell array
            mean = self.FindMeanWetSpell(file_no, size_of)
            
            sd_wet_spell = 0
            
            # If mean is 0, there were no spells or they were all length 0
            if mean > 0:
                sum_squared_diff = 0
                
                # Calculate sum of squared differences from mean
                for i in range(self.TotalWetSpells[file_no]):
                    sum_squared_diff += (self.WetSpellArray[file_no][i] - mean) ** 2
                
                # Calculate standard deviation
                if self.TotalWetSpells[file_no] > 0:
                    sd_wet_spell = (sum_squared_diff / self.TotalWetSpells[file_no]) ** 0.5
            
            return sd_wet_spell
    
        except Exception as e:
            print(f"Error in FindSDWetSpell: {str(e)}")
            self.Mini_Reset()
            return 0


    def FindDDPersistence(self, file_no, size_of):
        try:
        # Create dry spell array first
            self.CreateDrySpellArray(file_no, size_of)
            
            dry_day_persistence = 0
            dry_day_count = 0        # counts all dry days
            consec_dry_count = 0     # counts only consecutive dry days
        
            if self.TotalDrySpells[file_no] > 0:
                for i in range(self.TotalDrySpells[file_no]):
                    dry_day_count += self.DrySpellArray[file_no][i]
                    # Only count consecutive days if spell length > 1
                    if self.DrySpellArray[file_no][i] > 1:
                        consec_dry_count += self.DrySpellArray[file_no][i]
                
                # Calculate persistence if there were any dry days
                if dry_day_count > 0:
                    dry_day_persistence = consec_dry_count / dry_day_count
            
            return dry_day_persistence
    
        except Exception as e:
            print(f"Error in FindDryDayPersistence: {str(e)}")
            self.Mini_Reset()
            return 0   

    def FindWDPersistence(self, file_no, size_of):
        try:
            # Create wet spell array first
            self.CreateWetSpellArray(file_no, size_of)
            
            wet_day_persistence = 0
            wet_day_count = 0        # counts all wet days
            consec_wet_count = 0     # counts only consecutive wet days
            
            if self.TotalWetSpells[file_no] > 0:
                for i in range(self.TotalWetSpells[file_no]):
                    wet_day_count += self.WetSpellArray[file_no][i]
                    # Only count consecutive days if spell length > 1
                    if self.WetSpellArray[file_no][i] > 1:
                        consec_wet_count += self.WetSpellArray[file_no][i]
                
                # Calculate persistence if there were any wet days
                if wet_day_count > 0:
                    wet_day_persistence = consec_wet_count / wet_day_count
            
            return wet_day_persistence
    
        except Exception as e:
            print(f"Error in FindWetDayPersistence: {str(e)}")
            self.Mini_Reset()
            return 0

    def FindSpellLengthCorrelation(self, file_no, size_of):
        try:
            wet_persistence = self.FindWetDayPersistence(file_no, size_of)
            dry_persistence = self.FindDryDayPersistence(file_no, size_of)
            return wet_persistence - (1 - dry_persistence)
        except Exception as e:
            print(f"Error in FindSpellLengthCorrelation: {str(e)}")
            self.Mini_Reset()
            return 0

    #Utility Functions

    def CreateDrySpellArray():
        pass

    def CreateWetSpellArray():
        pass

    def IncreaseDate(self):
        days_in_month = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    
        # Increment the day
        self.CurrentDay += 1
        
        # Check for leap year
        leap = 0
        if self.CurrentMonth == 2:  # February
            if self.IsLeap(self.CurrentYear):
                # Only add a leap day if the application settings allow it
                if self.YearLength == 1:
                    leap = self.Leapvalue  # Either 0 or 1 depending on settings
        
        # Check if we need to move to the next month
        if self.CurrentDay > (days_in_month[self.CurrentMonth] + leap):
            self.CurrentMonth += 1
            self.CurrentDay = 1
        
        # Check if we need to move to the next year
        if self.CurrentMonth > 12:
            self.CurrentMonth = 1
            self.CurrentYear += 1
        
        # Update season and water year
        self.CurrentSeason = self.GetSeason(self.CurrentMonth)
        self.CurrentWaterYear = self.GetWaterYear(self.CurrentMonth, self.CurrentYear)
    
    def IsLeap(self, year):
        #checks for leap year
        if year % 400 == 0:
            return True
        elif year % 100 == 0:
            return False
        elif year % 4 == 0:
            return True
        else:
            return False
    
    def GetSeason(self, month):
        if month in [12, 1, 2]:
            return 1  # Winter
        elif month in [3, 4, 5]:
            return 2  # Spring
        elif month in [6, 7, 8]:
            return 3  # Summer
        else:  # months 9, 10, 11
            return 4  # Autumn


    def ExitAnalysis(self):
        try:
        # Check if the global cancel flag has been set
            if self.global_kopout:
                # Reset the flag for next time
                self.global_kopout = False
                return True
        
        # If we reach here, no cancellation is requested
            return False
        
        except Exception as e:
            print(f"Error in ExitAnalysis: {str(e)}")
                # In case of error, return False to avoid unexpected termination
            return False

    def SaveResults(self, file_no):
        try:
            if not self.save_root:
                print("No save file selected")
                return
            
            with open(self.save_root, 'w', newline='') as csv_file:
                writer = csv.writer(csv_file)
                
                # Handle different saving modes based on selected options
                if self.statCheckboxes[4].isChecked():  # SPI chosen
                    # Write header row with file names
                    header = [self.AllFilesList[i] for i in range(self.total_time_series_files)]
                    writer.writerow(header)
                    
                    # Write data for each month
                    for j in range(self.TotalMonths):
                        row = [self.RunningMonths[i][j][4] for i in range(1, self.total_time_series_files + 1)]
                        writer.writerow(row)
                        
                elif self.statCheckboxes[14].isChecked():  # % precip > annual percentile
                    # Write header row
                    header = []
                    for i in range(self.total_time_series_files):
                        header.extend([self.AllFilesList[i], "%Precip>Annual Percentile"])
                    writer.writerow(header)
                    
                    # Write data for each year
                    for j in range(self.StartYear, self.EndYear + 1):
                        row = []
                        for i in range(1, self.total_time_series_files + 1):
                            row.extend([int(datetime.strptime(self.global_start_date, "%d/%m/%Y").year) + j - 1, 
                                    self.FractionResult[i-1][j-1]])
                        writer.writerow(row)
                
                elif self.statCheckboxes[22].isChecked():  # pfl90 statistic
                    # Write header row
                    header = []
                    for i in range(self.total_time_series_files):
                        header.extend([self.AllFilesList[i], "%Total Precip from events>long-term percentile"])
                    writer.writerow(header)
                    
                    # Write data for each year
                    for j in range(self.StartYear, self.EndYear + 1):
                        row = []
                        for i in range(1, self.total_time_series_files + 1):
                            row.extend([int(datetime.strptime(self.global_start_date, "%d/%m/%Y").year) + j - 1, 
                                    self.LongTermResults[i-1][j-1]])
                        writer.writerow(row)
                
                elif self.statCheckboxes[23].isChecked():  # pnl90 statistic
                    # Write header row
                    header = []
                    for i in range(self.total_time_series_files):
                        header.extend([self.AllFilesList[i], "No events>long-term percentile"])
                    writer.writerow(header)
                    
                    # Write data for each year
                    for j in range(self.StartYear, self.EndYear + 1):
                        row = []
                        for i in range(1, self.total_time_series_files + 1):
                            row.extend([int(datetime.strptime(self.global_start_date, "%d/%m/%Y").year) + j - 1, 
                                    self.LongTermResults[i-1][j-1]])
                        writer.writerow(row)
                
                elif self.statCheckboxes[6].isChecked():  # Winter/summer ratio
                    # Write header row
                    header = []
                    for i in range(self.total_time_series_files):
                        header.extend([self.AllFilesList[i], "Winter/Summer Ratio"])
                    writer.writerow(header)
                    
                    # Write data for each year
                    start_year = int(datetime.strptime(self.global_start_date, "%d/%m/%Y").year)
                    for j in range(self.StartYear, self.EndYear + 1):
                        row = []
                        for i in range(1, self.total_time_series_files + 1):
                            # Check for division by zero or missing values
                            if (self.summaryArray[i][j][15][1] == 0 or 
                                self.summaryArray[i][j][15][1] == self.global_missing_code or 
                                self.summaryArray[i][j][13][1] == self.global_missing_code):
                                row.extend([start_year + j - 1, self.global_missing_code])
                            else:
                                ratio = self.summaryArray[i][j][13][1] / self.summaryArray[i][j][15][1]
                                row.extend([start_year + j - 1, ratio])
                        writer.writerow(row)
                
                else:  # Handle other statistics
                    # Define season names
                    season_names = ["", "Winter", "Spring", "Summer", "Autumn"]
                    
                    # Write header row
                    header = []
                    for i in range(self.total_time_series_files):
                        if not self.statCheckboxes[6].isChecked():  # Not winter/summer ratio
                            header.extend([self.AllFilesList[i], "Month/Season/Year", "Sum", "Max", "Percentile", 
                                        "Mean", "PDS", "POT", "Nth Largest", "Largest N day total", 
                                        "Max dry spell", "Max wet spell", "Mean dry spell", "Mean wet spell", 
                                        "Median dry spell", "Median wet spell", "SD dry spell", "SD wet spell", 
                                        "Mean dry day persistence", "Mean wet day persistence", "Spell length correlation"])
                    writer.writerow(header)
                    
                    # Write data based on selected period
                    start_year = int(datetime.strptime(self.global_start_date, "%d/%m/%Y").year)
                    for j in range(self.StartYear, self.EndYear + 1):
                        if self.DatesCombo.currentIndex() >= 1 and self.DatesCombo.currentIndex() <= 12:  # Month selected
                            k = self.DatesCombo.currentIndex()
                            row = []
                            for i in range(1, self.total_time_series_files + 1):
                                stats = [start_year + j - 1, k]
                                # Add all statistics in order
                                for stat_idx in range(1, 22):  # 21 different statistics
                                    stats.append(self.summaryArray[i-1][j-1][k-1][stat_idx-1])
                                row.extend(stats)
                            writer.writerow(row)
                        
                        elif self.DatesCombo.currentIndex() >= 13 and self.DatesCombo.currentIndex() <= 16:  # Season selected
                            k = self.DatesCombo.currentIndex()
                            row = []
                            for i in range(1, self.total_time_series_files + 1):
                                stats = [start_year + j - 1, season_names[k-12]]
                                # Add all statistics in order
                                for stat_idx in range(1, 22):  # 21 different statistics
                                    stats.append(self.summaryArray[i-1][j-1][k-1][stat_idx-1])
                                row.extend(stats)
                            writer.writerow(row)
                        
                        elif self.DatesCombo.currentIndex() == 17:  # Annual selected
                            row = []
                            for i in range(1, self.total_time_series_files + 1):
                                stats = [start_year + j - 1, "Annual"]
                                # Add all statistics in order
                                for stat_idx in range(1, 22):  # 21 different statistics
                                    stats.append(self.summaryArray[i-1][j-1][16][stat_idx-1])  # 17th index is Annual
                                row.extend(stats)
                            writer.writerow(row)
                        
                        elif self.DatesCombo.currentIndex() == 18:  # Water year selected
                            skip = 2 if j == 1 and int(datetime.strptime(self.global_start_date, "%d/%m/%Y").month) < 10 else 1
                            row = []
                            for i in range(1, self.total_time_series_files + 1):
                                stats = [start_year + j - skip, "Water Year"]
                                # Add all statistics in order
                                for stat_idx in range(1, 22):  # 21 different statistics
                                    stats.append(self.summaryArray[i-1][j-1][17][stat_idx-1])  # 18th index is Water Year
                                row.extend(stats)
                            writer.writerow(row)
                    
                print(f"Results saved to {self.save_root}")
        
        except Exception as e:
            print(f"Error in SaveResults: {str(e)}")
            self.Mini_Reset()
        

    def Help_Needed(self, help_context):
        """
        Displays help information based on the context provided
        """
        try:
        # In PyQt we'd use QDesktopServices to open a help file or webpage
            
            
            help_file = "help/sdsm_help.html"  # Local file path

            
            if os.path.exists(help_file):
                # Create the full URL with the context parameter
                file_url = QUrl.fromLocalFile(os.path.abspath(help_file))
                
                # Add the context as a fragment
                file_url.setFragment(str(help_context))
                
                # Open the help file in the default browser
                QDesktopServices.openUrl(file_url)
            else:
                # If the file doesn't exist, show an error message
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self,
                    "Help File Not Found",
                    f"Could not find the help file: {help_file}\nPlease make sure the help documentation is installed correctly."
                )
            
        except Exception as e:
            # Handle any errors that occur
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "Help System Error",
                f"An error occurred in the help system: {str(e)}"
            )

    def Mini_Reset(self):
        try:
            # In Python, we'd close any open file handles
            # This is different from VB where files are referenced by numbers
            if hasattr(self, 'open_files') and self.open_files:
                for file in self.open_files:
                    if not file.closed:
                        file.close()
                self.open_files = []
            
            # Reset mouse cursor (equivalent to MousePointer = 0 in VB)
            self.setCursor(Qt.ArrowCursor)
            
            # Hide progress bar if it exists
            if hasattr(self, 'progress_bar') and self.progress_bar:
                self.progress_bar.setVisible(False)
            
            # Set escape key handling (equivalent to KeyPreview = False)
            # In PyQt, we'd typically use event handlers for this
            
            # Reset the global cancel flag
            self.global_kopout = False
        
        except Exception as e:
            print(f"Error in Mini_Reset: {str(e)}")

    def Reset_All(self):
        try:
            # Call Mini_Reset to close files and reset UI elements
            self.Mini_Reset()
            
            # Reset total statistics available
            self.total_stats_available = 23
            
            # Clear file selections in left and right list widgets
            file_lists = [
                self.fileSelectionLeft.findChild(QListWidget),
                self.fileSelectionRight.findChild(QListWidget)
            ]
            for file_list in file_lists:
                file_list.clearSelection()
            
            # Reset file counts
            self.left_files_count = 0
            self.right_files_count = 0
            self.total_time_series_files = 0
            
            # Clear save file information
            self.save_file = ""
            self.save_root = ""
            self.saveFileLabel.setText("File: *.CSV")
            
            # Reset date fields to global defaults
            self.startDateInput.setText(self.global_start_date)
            self.endDateInput.setText(self.global_end_date)
            
            # Set days between dates
            # Actual days calculation would require datetime conversion
            
            # Reset dropdowns
            self.timePeriodDropdown.setCurrentIndex(0)
            
            # Reset percentile and statistics values
            self.percentile = 90
            self.percentileInput.setText("90")
            
            self.spi_value = 3
            
            # Reset threshold values
            self.local_thresh = self.thresh  # For Partial Duration Series
            self.pot_value = self.thresh  # For Peaks Over Threshold
            
            # Reset N values
            self.nth_largest = 1
            
            self.largest_n_day = 1
            
            # Reset statistics options - select Sum as default
            for checkbox in self.statCheckboxes:
                checkbox.setChecked(checkbox.text() == "Sum")
            
            # Reset annual percentile
            self.annual_percentile = 90
            self.percentileInput.setText("90")
            
            # Reset STARDEX statistics percentiles
            self.pfl90_percentile = 90
            self.precipLongTermInput.setText("90")
            self.pnl90_percentile = 90
            self.numEventsInput.setText("90")
            
            # Reset directory paths would go here
            # These would interact with the file browsers
            
        except Exception as e:
            # Handle errors
            print(f"Error in Reset_All: {str(e)}")

    def DumpForm(self):
        try:
            # Hide the window first
            self.hide()
            
            # Disconnect any signals that might be connected to this widget
            # This is a general approach - you may need to disconnect specific signals
            self.disconnect()
            
            # Close any open resources
            self.Mini_Reset()
            
            # Schedule the widget for deletion when control returns to the event loop
            self.deleteLater()
            
            print("Form successfully unloaded")
        
        except Exception as e:
            print(f"Error in DumpForm: {str(e)}")