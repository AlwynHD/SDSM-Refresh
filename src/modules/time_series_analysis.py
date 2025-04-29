from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame, QComboBox, 
    QLineEdit, QListWidget, QFileDialog, QCheckBox, QRadioButton, QButtonGroup, 
    QGridLayout, QGroupBox, QSizePolicy, QMessageBox, QProgressBar, QSpacerItem, QListWidgetItem,
    QDialog
)
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import os
import csv
from datetime import datetime
import math
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import numpy as np

# Chapter 1 for me
"""
project management
refactor what oes where
gannt chart - team structure
make up a kanban board 
bottom of every chapter is the markscheme
follow that
"""

class ContentWidget(QWidget):
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

        # Define missing value code
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
        self.CurrentSeason = 1
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
        self.summaryArray = [[[[self.global_missing_code for _ in range(max_stats)] 
                            for _ in range(max_months)]
                            for _ in range(max_years)]
                            for _ in range(max_files)]
        
        # Period array to store temporary data
        max_days = 55000
        self.periodArray = [[self.global_missing_code for _ in range(max_days)] 
                            for _ in range(max_files)]
        
        # Arrays for SPI calculation
        max_running_months = 2000
        self.RunningMonths = [[[self.global_missing_code for _ in range(5)]
                            for _ in range(max_running_months)]
                            for _ in range(max_files)]
        
        # Arrays for spell statistics
        max_spells = 366
        self.DrySpellArray = [[0 for _ in range(max_spells)] 
                            for _ in range(max_files)]
        self.WetSpellArray = [[0 for _ in range(max_spells)] 
                            for _ in range(max_files)]
        
        # Count of spells
        self.TotalDrySpells = [0 for _ in range(max_files)]
        self.TotalWetSpells = [0 for _ in range(max_files)]
        
        # Arrays for results
        self.FractionResult = [[self.global_missing_code for _ in range(max_years)]
                            for _ in range(max_files)]
        self.LongTermResults = [[self.global_missing_code for _ in range(max_years)]
                            for _ in range(max_files)]
        
        # Ensemble file flags
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

        # Create North File Selection Group
        northGroupBox = QGroupBox("North File Selection")
        northLayout = QVBoxLayout()

        # Create file list widget for North files
        self.northFileList = QListWidget()
        self.northFileList.setFixedHeight(150)
        self.northFileList.setSelectionMode(QListWidget.MultiSelection)
        self.northFileList.path = ""
        self.northFileList.itemSelectionChanged.connect(
            lambda: self.updateFileCount(self.northFileList, "North")
        )

        # Create button layout for North files
        northButtonLayout = QHBoxLayout()

        # Create select files button for North files
        northSelectButton = QPushButton("Browse Files")
        northSelectButton.setFixedHeight(30)
        northSelectButton.clicked.connect(
            lambda: self.openFileExplorer(self.northFileList, "North")
        )
        northButtonLayout.addWidget(northSelectButton)

        # Create clear button for North files
        northClearButton = QPushButton("Clear")
        northClearButton.setFixedHeight(30)
        northClearButton.clicked.connect(
            lambda: (self.northFileList.clear(), self.updateFileCount(self.northFileList, "North"))
        )
        northButtonLayout.addWidget(northClearButton)

        # Count label for North files
        self.northCountLabel = QLabel("Selected: 0")

        # Add widgets to North layout
        northLayout.addWidget(self.northFileList)
        northLayout.addLayout(northButtonLayout)
        northLayout.addWidget(self.northCountLabel)
        northGroupBox.setLayout(northLayout)
        leftSideLayout.addWidget(northGroupBox)

        # Create South File Selection Group (similar to North)
        southGroupBox = QGroupBox("South File Selection")
        southLayout = QVBoxLayout()

        # Create file list widget for South files
        self.southFileList = QListWidget()
        self.southFileList.setFixedHeight(150)
        self.southFileList.setSelectionMode(QListWidget.MultiSelection)
        self.southFileList.path = ""
        self.southFileList.itemSelectionChanged.connect(
            lambda: self.updateFileCount(self.southFileList, "South")
        )

        # Create button layout for South files
        southButtonLayout = QHBoxLayout()

        # Create select files button for South files
        southSelectButton = QPushButton("Browse Files")
        southSelectButton.setFixedHeight(30)
        southSelectButton.clicked.connect(
            lambda: self.openFileExplorer(self.southFileList, "South")
        )
        southButtonLayout.addWidget(southSelectButton)

        # Create clear button for South files
        southClearButton = QPushButton("Clear")
        southClearButton.setFixedHeight(30)
        southClearButton.clicked.connect(
            lambda: (self.southFileList.clear(), self.updateFileCount(self.southFileList, "South"))
        )
        southButtonLayout.addWidget(southClearButton)

        # Count label for South files
        self.southCountLabel = QLabel("Selected: 0")

        # Add widgets to South layout
        southLayout.addWidget(self.southFileList)
        southLayout.addLayout(southButtonLayout)
        southLayout.addWidget(self.southCountLabel)
        southGroupBox.setLayout(southLayout)
        leftSideLayout.addWidget(southGroupBox)

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

        statsLayout.setSpacing(5)  # Increased spacing for better appearance
        statsLayout.setContentsMargins(10, 15, 10, 15)

        # Create a button group for statistics (single selection)
        self.statsButtonGroup = QButtonGroup()

        # Statistics options
        self.statsOptions = [
            "Sum", "Mean", "Maximum", "Winter/Summer ratio",
            "Maximum dry spell", "Maximum wet spell",
            "Dry day persistence", "Wet day persistence",
            "Partial Duration Series", "Percentile",
            "Standard Precipitation Index", "Peaks Over Threshold",
            "Nth largest", "Largest N-day total"
        ]

        # Create radio buttons instead of checkboxes
        self.statRadioButtons = []
        for i, stat in enumerate(self.statsOptions):
            radio = QRadioButton(stat)
            font = QFont()
            font.setPointSize(14)
            radio.setFont(font)
            
            # Add to button group
            self.statsButtonGroup.addButton(radio, i)
            
            # Add to layout - 3 columns
            statsLayout.addWidget(radio, i // 3, i % 3)
            self.statRadioButtons.append(radio)

        # Set first option (Sum) as default
        self.statRadioButtons[0].setChecked(True)

        # Connect selection changed signal
        self.statsButtonGroup.buttonClicked.connect(self.onStatOptionChanged)

        # --- Spell Duration Selection ---
        spellGroup = QGroupBox("Spell Duration Selection")
        spellLayout = QVBoxLayout()
        spellLayout.setContentsMargins(10, 15, 10, 15)
        spellLayout.setSpacing(8)

        self.spellOptions = [
            "Mean dry spell", "Mean wet spell",
            "Median dry spell", "Median wet spell",
            "SD dry spell", "SD wet spell", "Spell length correlation"
        ]

        # Create button group for spell selection
        self.spellButtonGroup = QButtonGroup()

        for i, option in enumerate(self.spellOptions):
            radio = QRadioButton(option)
            font = QFont()
            font.setPointSize(14)
            radio.setFont(font)
            
            self.spellButtonGroup.addButton(radio, i)
            spellLayout.addWidget(radio)

        # Set first spell option as default
        self.spellButtonGroup.buttons()[0].setChecked(True)

        spellGroup.setLayout(spellLayout)
        spellGroup.setFixedHeight(300)

        # Calculate how many rows the stats grid will have
        stat_rows = (len(self.statsOptions) + 2) // 3
        statsLayout.addWidget(spellGroup, 0, 3, stat_rows, 1)

        # --- Threshold Inputs ---
        # Create parameter groups for each statistic that needs it
        # Each will be shown/hidden based on the selected statistic

        # Main parameters container
        paramsGroup = QGroupBox("Parameters")
        paramsLayout = QGridLayout()
        paramsLayout.setContentsMargins(10, 15, 10, 15)
        paramsLayout.setSpacing(10)

        # 1. Percentile parameters
        self.percentileParams = QWidget()
        percentileLayout = QGridLayout(self.percentileParams)
        percentileLayout.setContentsMargins(0, 0, 0, 0)

        self.percentileInput = QLineEdit()
        self.percentileInput.setPlaceholderText("90")
        self.percentileInput.setText("90")
        self.percentileInput.setFixedHeight(25)
        percentileLayout.addWidget(QLabel("Percentile value:"), 0, 0)
        percentileLayout.addWidget(self.percentileInput, 0, 1)

        # 2. SPI parameters
        self.spiParams = QWidget()
        spiLayout = QGridLayout(self.spiParams)
        spiLayout.setContentsMargins(0, 0, 0, 0)

        self.spiValueInput = QLineEdit()
        self.spiValueInput.setPlaceholderText("3")
        self.spiValueInput.setText("3")
        self.spiValueInput.setFixedHeight(25)
        spiLayout.addWidget(QLabel("SPI period (months):"), 0, 0)
        spiLayout.addWidget(self.spiValueInput, 0, 1)

        # 3. Peaks Over Threshold parameters
        self.potParams = QWidget()
        potLayout = QGridLayout(self.potParams)
        potLayout.setContentsMargins(0, 0, 0, 0)

        self.potValueInput = QLineEdit()
        self.potValueInput.setPlaceholderText("0.1")
        self.potValueInput.setText("0.1")
        self.potValueInput.setFixedHeight(25)
        potLayout.addWidget(QLabel("Threshold value:"), 0, 0)
        potLayout.addWidget(self.potValueInput, 0, 1)

        # 4. Nth Largest parameters
        self.nthLargestParams = QWidget()
        nthLargestLayout = QGridLayout(self.nthLargestParams)
        nthLargestLayout.setContentsMargins(0, 0, 0, 0)

        self.nthLargestInput = QLineEdit()
        self.nthLargestInput.setPlaceholderText("1")
        self.nthLargestInput.setText("1")
        self.nthLargestInput.setFixedHeight(25)
        nthLargestLayout.addWidget(QLabel("N (nth largest):"), 0, 0)
        nthLargestLayout.addWidget(self.nthLargestInput, 0, 1)

        # 5. Largest N-day total parameters
        self.largestNDayParams = QWidget()
        largestNDayLayout = QGridLayout(self.largestNDayParams)
        largestNDayLayout.setContentsMargins(0, 0, 0, 0)

        self.largestNDayInput = QLineEdit()
        self.largestNDayInput.setPlaceholderText("1")
        self.largestNDayInput.setText("1")
        self.largestNDayInput.setFixedHeight(25)
        largestNDayLayout.addWidget(QLabel("N (days):"), 0, 0)
        largestNDayLayout.addWidget(self.largestNDayInput, 0, 1)

        # 6. PDS Parameters
        self.pdsParams = QWidget()
        pdsLayout = QGridLayout(self.pdsParams)
        pdsLayout.setContentsMargins(0, 0, 0, 0)

        self.pdsThreshInput = QLineEdit()
        self.pdsThreshInput.setPlaceholderText("0.1")
        self.pdsThreshInput.setText("0.1")
        self.pdsThreshInput.setFixedHeight(25)
        pdsLayout.addWidget(QLabel("Threshold value:"), 0, 0)
        pdsLayout.addWidget(self.pdsThreshInput, 0, 1)

        # 7. Annual Percentile parameters (existing UI)
        self.annualPercentileParams = QWidget()
        annualPercentileLayout = QGridLayout(self.annualPercentileParams)
        annualPercentileLayout.setContentsMargins(0, 0, 0, 0)

        self.annualPercentileInput = QLineEdit()
        self.annualPercentileInput.setPlaceholderText("90")
        self.annualPercentileInput.setText("90")
        self.annualPercentileInput.setFixedHeight(25)
        annualPercentileLayout.addWidget(QLabel("%Prec > annual %ile:"), 0, 0)
        annualPercentileLayout.addWidget(self.annualPercentileInput, 0, 1)

        self.precipLongTermInput = QLineEdit()
        self.precipLongTermInput.setPlaceholderText("90")
        self.precipLongTermInput.setText("90")
        self.precipLongTermInput.setFixedHeight(25)
        annualPercentileLayout.addWidget(QLabel("% All precip from events > long-term %ile:"), 1, 0)
        annualPercentileLayout.addWidget(self.precipLongTermInput, 1, 1)

        self.numEventsInput = QLineEdit()
        self.numEventsInput.setPlaceholderText("90")
        self.numEventsInput.setText("90")
        self.numEventsInput.setFixedHeight(25)
        annualPercentileLayout.addWidget(QLabel("No. of events > long-term %ile:"), 2, 0)
        annualPercentileLayout.addWidget(self.numEventsInput, 2, 1)

        # Add all parameter widgets to the params layout
        # Initially only show the default one (Sum has no parameters)
        paramsLayout.addWidget(self.percentileParams, 0, 0)
        paramsLayout.addWidget(self.spiParams, 1, 0)
        paramsLayout.addWidget(self.potParams, 2, 0)
        paramsLayout.addWidget(self.nthLargestParams, 3, 0)
        paramsLayout.addWidget(self.largestNDayParams, 4, 0)
        paramsLayout.addWidget(self.pdsParams, 5, 0)
        paramsLayout.addWidget(self.annualPercentileParams, 6, 0)

        # Hide all parameter sets initially
        self.percentileParams.hide()
        self.spiParams.hide()
        self.potParams.hide()
        self.nthLargestParams.hide()
        self.largestNDayParams.hide()
        self.pdsParams.hide()
        self.annualPercentileParams.hide()

        paramsGroup.setLayout(paramsLayout)
        statsLayout.addWidget(paramsGroup, stat_rows, 0, 3, 3)

        statsGroup.setLayout(statsLayout)
        mainLayout.addWidget(statsGroup)

        # Call setup validation function (need to modify this function)
        self.setupInputValidation()

        # --- Action Buttons ---
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


    def onStatOptionChanged(self, button):
        """Handler for when a statistic option is changed"""
        # Hide all parameter sets first
        self.percentileParams.hide()
        self.spiParams.hide()
        self.potParams.hide()
        self.nthLargestParams.hide()
        self.largestNDayParams.hide()
        self.pdsParams.hide()
        self.annualPercentileParams.hide()
        
        # Show parameters based on which statistic is selected
        selected_id = self.statsButtonGroup.id(button)
        
        if selected_id == 3:  # Winter/Summer ratio
            # Set period to Annual
            self.DatesCombo.setCurrentIndex(17)
        elif selected_id == 8:  # Partial Duration Series
            self.pdsParams.show()
        elif selected_id == 9:  # Percentile
            self.percentileParams.show()
        elif selected_id == 10:  # Standard Precipitation Index
            self.spiParams.show()
        elif selected_id == 11:  # Peaks Over Threshold
            self.potParams.show()
        elif selected_id == 12:  # Nth largest
            self.nthLargestParams.show()
        elif selected_id == 13:  # Largest N-day total
            self.largestNDayParams.show()
        elif selected_id == 14:  # %Prec > annual %ile
            self.annualPercentileParams.show()

    def CreateFileSelectionGroup(self, title):
        """
        Creates a file selection group with directory navigation and file selection capabilities
        
        Args:
            title (str): The title for the group box
            
        Returns:
            QGroupBox: The configured file selection group
        """
        group = QGroupBox(title)
        layout = QVBoxLayout()
        
        # Create file list widget
        file_list = QListWidget()
        file_list.setFixedHeight(150)
        file_list.setSelectionMode(QListWidget.MultiSelection)
        file_list.itemSelectionChanged.connect(lambda: self.updateFileCount(file_list, title))
        
        # Create directory navigator
        dir_layout = QHBoxLayout()
        
        # Drive selection dropdown
        drive_combo = QComboBox()
        drives = [chr(x) + ':' for x in range(65, 91) if os.path.exists(chr(x) + ':')]
        drive_combo.addItems(drives)
        if drives:  # Set default drive if available
            default_drive = os.path.abspath(os.path.dirname(__file__))[0:2]
            index = drive_combo.findText(default_drive)
            if index >= 0:
                drive_combo.setCurrentIndex(index)
        drive_combo.currentTextChanged.connect(lambda text: self.onDriveChanged(text, file_list, dir_list))
        
        # Directory list widget
        dir_list = QListWidget()
        dir_list.setFixedHeight(100)
        dir_list.itemClicked.connect(lambda item: self.onDirChanged(item.text(), file_list, dir_list))
        
        # Populate directories for current drive
        if drives:
            current_drive = drive_combo.currentText()
            try:
                current_dir = os.path.join(current_drive, '\\')
                dirs = [d for d in os.listdir(current_dir) if os.path.isdir(os.path.join(current_dir, d))]
                dir_list.addItems(dirs)
            except Exception as e:
                print(f"Error accessing drive {current_drive}: {str(e)}")
        
        # Add drive and directory list to layout
        dir_layout.addWidget(QLabel("Drive:"))
        dir_layout.addWidget(drive_combo)
        
        # Store the file_list and dir_list as properties of the group box for later access
        group.file_list = file_list
        group.dir_list = dir_list
        group.drive_combo = drive_combo
        group.current_path = os.path.abspath(os.path.dirname(__file__))
        
        # Count label for selected files
        count_label = QLabel("Selected: 0")
        group.count_label = count_label
        
        # Add widgets to main layout
        layout.addWidget(file_list)
        layout.addLayout(dir_layout)
        layout.addWidget(dir_list)
        layout.addWidget(count_label)
        
        group.setLayout(layout)
        return group
    
    def openFileExplorer(self, file_list, section_name):
        """Opens file explorer dialog to select multiple CSV files"""
        files, _ = QFileDialog.getOpenFileNames(
            self, f"Select CSV Files for {section_name}", "", "CSV Files (*.csv)"
        )
        
        if files:
            file_list.path = os.path.dirname(files[0])
            for file_path in files:
                file_name = os.path.basename(file_path)
                # Check if file already in list
                if not file_list.findItems(file_name, Qt.MatchExactly):
                    item = QListWidgetItem(file_name)
                    file_list.addItem(item)
                    item.setSelected(True)
            self.updateFileCount(file_list, section_name)

    def updateFileCount(self, file_list, section_name):
        """Update the count of selected files"""
        selected_count = len(file_list.selectedItems())
        
        if section_name == "North":
            self.northCountLabel.setText(f"Selected: {selected_count}")
            self.left_files_count = selected_count
        else:  # South
            self.southCountLabel.setText(f"Selected: {selected_count}")
            self.right_files_count = selected_count
        
        self.total_time_series_files = self.left_files_count + self.right_files_count
        
        if self.total_time_series_files > 5:
            QMessageBox.warning(self, "Warning Message", 
                            "You can only plot up to five files. You will have to deselect at least one file.")

    def onDriveChanged(self, drive, file_list, dir_list):
        """Handle drive selection change"""
        try:
            # Update current path
            self.current_path = drive + "\\"
            
            # Clear and update directory list
            dir_list.clear()
            try:
                dirs = [d for d in os.listdir(self.current_path) 
                    if os.path.isdir(os.path.join(self.current_path, d))]
                dir_list.addItems(dirs)
            except Exception as e:
                print(f"Error accessing directories on drive {drive}: {str(e)}")
            
            # Clear file list
            file_list.clear()
            
            # Update corresponding file selection count
            self.updateFileCount(file_list, file_list.parent().title())
            
        except Exception as e:
            print(f"Error changing drive: {str(e)}")
            QMessageBox.critical(self, "Drive Error", 
                            f"Cannot access drive {drive}. It may not be ready or may require permission.")

    def onDirChanged(self, dir_name, file_list, dir_list):
        """Handle directory selection change"""
        try:
            # Get the parent group box to access its properties
            group_box = file_list.parent()
            
            # Build the new path
            new_path = os.path.join(group_box.current_path, dir_name)
            
            # Update current path
            group_box.current_path = new_path
            
            # Clear and update directory list
            dir_list.clear()
            try:
                dirs = [d for d in os.listdir(new_path) 
                    if os.path.isdir(os.path.join(new_path, d))]
                dir_list.addItems(dirs)
            except Exception as e:
                print(f"Error accessing directories in {new_path}: {str(e)}")
                return
            
            # Clear and update file list - only show CSV files
            file_list.clear()
            try:
                files = [f for f in os.listdir(new_path) 
                        if os.path.isfile(os.path.join(new_path, f)) and f.lower().endswith('.csv')]
                file_list.addItems(files)
            except Exception as e:
                print(f"Error accessing files in {new_path}: {str(e)}")
                return
            
            # Store the path in the file_list for later access
            file_list.path = new_path
            
            # Update corresponding file selection count
            self.updateFileCount(file_list, group_box.title())
            
        except Exception as e:
            print(f"Error changing directory: {str(e)}")

    def updateFileCount(self, file_list, title):
        """Update the count of selected files"""
        try:
            # Get parent group box
            group_box = file_list.parent()
            if not group_box:
                return
                
            # Count selected items
            selected_count = len(file_list.selectedItems())
            
            # Update the count label
            group_box.count_label.setText(f"Selected: {selected_count}")
            
            # Update appropriate counter based on which file list this is
            if "North" in title:
                self.left_files_count = selected_count
            else:
                self.right_files_count = selected_count
                
            # Update total file count
            self.total_time_series_files = self.left_files_count + self.right_files_count
            
            # Check if too many files selected
            if self.total_time_series_files > 5:
                QMessageBox.warning(self, "Warning Message", 
                                "You can only plot up to five files. You will have to deselect at least one file.")
                
        except Exception as e:
            print(f"Error updating file count: {str(e)}")

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
        
        # SPI value input
        self.spiValueInput.textChanged.connect(self.onSPIValueChanged)
        self.spiValueInput.editingFinished.connect(self.onSPIValueEditFinished)
        
        # POT value input
        self.potValueInput.textChanged.connect(self.onPOTValueChanged)
        self.potValueInput.editingFinished.connect(self.onPOTValueEditFinished)
        
        # Nth largest input
        self.nthLargestInput.textChanged.connect(self.onNthLargestChanged)
        self.nthLargestInput.editingFinished.connect(self.onNthLargestEditFinished)
        
        # Largest N-day input
        self.largestNDayInput.textChanged.connect(self.onLargestNDayChanged)
        self.largestNDayInput.editingFinished.connect(self.onLargestNDayEditFinished)
        
        # PDS threshold input
        self.pdsThreshInput.textChanged.connect(self.onPDSThreshChanged)
        self.pdsThreshInput.editingFinished.connect(self.onPDSThreshEditFinished)
        
        # Annual percentile input
        self.annualPercentileInput.textChanged.connect(self.onAnnualPercentileChanged)
        self.annualPercentileInput.editingFinished.connect(self.onAnnualPercentileEditFinished)
        
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
                self.close_open_files()
                
                # Reset ensemble file flags
                for i in range(5):
                    self.EnsembleFile[i] = False
                
                # Show progress bar
                self.progress_bar.setVisible(True)
                self.progress_bar.setValue(0)
                self.progress_bar.setMaximum(100)
                self.progress_bar.setFormat("Creating Plot")
                
                # Allow processing of escape key
                self.setKeyPressed(True)
                
                # Clear the list of selected files
                self.AllFilesList = []
                self.open_files = []
                
                # Open files and check if they're ensemble files
                file_no = 2  # File number 1 reserved for save file
                
                # Check left file list
                for i in range(self.northFileList.count()):
                    item = self.northFileList.item(i)
                    if item.isSelected():
                        self.AllFilesList.append(item.text())
                        
                        file_path = os.path.join(self.northFileList.path, item.text())
                        try:
                            # Check if this is an ensemble file by reading first line
                            with open(file_path, 'r') as f:
                                dummy_string = f.readline()
                                if len(dummy_string) > 15:
                                    self.EnsembleFile[file_no - 2] = True
                                    ensemble_present = True
                            
                            # Reopen file for processing
                            input_file = open(file_path, 'r')
                            self.open_files.append(input_file)
                            file_no += 1
                        except Exception as e:
                            print(f"Error opening file {file_path}: {str(e)}")
                            self.Mini_Reset()
                            return
                
                # Check right file list
                for i in range(self.southFileList.count()):
                    item = self.southFileList.item(i)
                    if item.isSelected():
                        self.AllFilesList.append(item.text())
                        
                        file_path = os.path.join(self.southFileList.path, item.text())
                        try:
                            # Check if this is an ensemble file by reading first line
                            with open(file_path, 'r') as f:
                                dummy_string = f.readline()
                                if len(dummy_string) > 15:
                                    self.EnsembleFile[file_no - 2] = True
                                    ensemble_present = True
                            
                            # Reopen file for processing
                            input_file = open(file_path, 'r')
                            self.open_files.append(input_file)
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
                    self.create_and_show_chart()
                    
                    # Save results if requested
                    if (self.save_root and 
                        (self.statCheckboxes[4].isChecked() or self.DatesCombo.currentIndex() != 0)):
                        self.SaveResults(series_data_first_value)
                else:
                    # Error occurred during data processing
                    if not self.global_kopout:
                        QMessageBox.critical(self, "Error Message", 
                                        "Sorry - have been unable to read in data correctly - please check settings.")
                    else:
                        # Reset flag so error can be shown next time
                        self.global_kopout = False
                
                # Close all open files
                self.close_open_files()
                
                # Reset cursor and hide progress bar
                self.setCursor(Qt.ArrowCursor)
                self.progress_bar.setVisible(False)
                
                # Disable key press event processing
                self.setKeyPressed(False)
        
        except Exception as e:
            print(f"Error in PlotData: {str(e)}")
            self.Mini_Reset()

    def close_open_files(self):
        """Close any open file handles"""
        if hasattr(self, 'open_files') and self.open_files:
            for file in self.open_files:
                if not file.closed:
                    file.close()
            self.open_files = []

    def setKeyPressed(self, enabled):
        """Enable or disable key press event processing"""
        if enabled:
            self.installEventFilter(self)
        else:
            self.removeEventFilter(self)

    def eventFilter(self, obj, event):
        """Process key press events"""
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Escape:
                response = QMessageBox.question(
                    self, 
                    "Cancel?", 
                    "Do you really want to cancel processing?",
                    QMessageBox.Yes | QMessageBox.No, 
                    QMessageBox.No
                )
                if response == QMessageBox.Yes:
                    self.global_kopout = True
                return True
        
        return super().eventFilter(obj, event)

    def create_and_show_chart(self):
        """Creates and displays the time series chart using matplotlib"""
        try:
            
            # Create chart window
            self.chart_window = QDialog(self)
            self.chart_window.setWindowTitle("Time Series Plot")
            self.chart_window.resize(900, 600)
            chart_layout = QVBoxLayout(self.chart_window)
            
            # Create matplotlib figure
            figure = Figure(figsize=(10, 6), dpi=100)
            canvas = FigureCanvas(figure)
            chart_layout.addWidget(canvas)
            
            # Add a toolbar with navigation buttons
            toolbar = NavigationToolbar(canvas, self.chart_window)
            chart_layout.addWidget(toolbar)
            
            # Create plot
            ax = figure.add_subplot(111)
            
            # Determine chart title based on selected data and statistic
            title = "Time Series Plot"
            y_label = ""
            
            # Set chart source type
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
            
            # Set chart title based on selected time period
            if self.statCheckboxes[4].isChecked():
                title = f"Standard Precipitation Index (SPI) - {self.spi_value} Month Period"
            elif self.DatesCombo.currentIndex() == 0:
                title = "Raw Data Time Series"
            elif self.DatesCombo.currentIndex() >= 1 and self.DatesCombo.currentIndex() <= 12:
                # Month names
                month_names = ["January", "February", "March", "April", "May", "June",
                            "July", "August", "September", "October", "November", "December"]
                title = f"{month_names[self.DatesCombo.currentIndex()-1]} {y_label}"
            elif self.DatesCombo.currentIndex() >= 13 and self.DatesCombo.currentIndex() <= 16:
                # Season names
                season_names = ["Winter", "Spring", "Summer", "Autumn"]
                title = f"{season_names[self.DatesCombo.currentIndex()-13]} {y_label}"
            elif self.DatesCombo.currentIndex() == 17:
                title = f"Annual {y_label}"
            elif self.DatesCombo.currentIndex() == 18:
                title = f"Water Year {y_label}"
            
            # Set title and labels
            ax.set_title(title, fontsize=12, fontweight='bold')
            ax.set_ylabel(y_label, fontsize=10)
            
            # Set X-axis label based on data type
            if self.statCheckboxes[4].isChecked():
                ax.set_xlabel("Date", fontsize=10)
            elif self.DatesCombo.currentIndex() == 0:
                ax.set_xlabel("Day", fontsize=10)
            else:
                ax.set_xlabel("Year", fontsize=10)
            
            # List of colors and markers for different time series
            colors = ['blue', 'red', 'green', 'purple', 'orange']
            markers = ['o', 's', '^', 'D', 'x']
            
            # Plot each time series
            for i in range(1, self.total_time_series_files + 1):
                # Extract x and y values, filter out None/Empty values
                x_values = []
                y_values = []
                
                for j in range(self.TimeSeriesLength):
                    if j < len(self.TimeSeriesData) and i < len(self.TimeSeriesData[j]):
                        if self.TimeSeriesData[j][i] is not None:
                            # Use actual x-axis values if available
                            if self.TimeSeriesData[j][0] and self.TimeSeriesData[j][0].strip():
                                try:
                                    # Try to convert to numeric x-value if possible
                                    x_val = float(self.TimeSeriesData[j][0])
                                except (ValueError, TypeError):
                                    # If not numeric, use the index
                                    x_val = j
                            else:
                                x_val = j
                                
                            x_values.append(x_val)
                            y_values.append(self.TimeSeriesData[j][i])
                
                if len(x_values) > 0:
                    # Plot the time series with a different color and marker for each file
                    color_idx = (i-1) % len(colors)
                    marker_idx = (i-1) % len(markers)
                    
                    if self.DatesCombo.currentIndex() == 0:  # Raw data - use line plot
                        line, = ax.plot(x_values, y_values, 
                                    color=colors[color_idx],
                                    marker=markers[marker_idx], 
                                    markersize=4,
                                    linestyle='-',
                                    linewidth=1,
                                    label=self.AllFilesList[i-1])
                    else:  # Other data - connect points with lines
                        line, = ax.plot(x_values, y_values, 
                                    color=colors[color_idx],
                                    marker=markers[marker_idx], 
                                    markersize=6,
                                    linestyle='-',
                                    linewidth=1.5,
                                    label=self.AllFilesList[i-1])
            
            # Customize x-axis based on data type
            if self.DatesCombo.currentIndex() != 0:  # Not raw data
                # Create custom tick marks for years
                ticks = []
                tick_labels = []
                
                for j in range(min(self.TimeSeriesLength, len(self.TimeSeriesData))):
                    if self.TimeSeriesData[j][0] and str(self.TimeSeriesData[j][0]).strip():
                        # Only add labels for even-numbered years to avoid crowding
                        if j % 2 == 0 or self.TimeSeriesLength < 10:
                            ticks.append(j)
                            tick_labels.append(str(self.TimeSeriesData[j][0]).strip())
                
                if ticks:
                    ax.set_xticks(ticks)
                    ax.set_xticklabels(tick_labels, rotation=45, ha='right')
            
            # Add grid
            ax.grid(True, linestyle='--', alpha=0.7)
            
            # Add legend if there's more than one time series
            if self.total_time_series_files > 1:
                ax.legend(loc='best', frameon=True, framealpha=0.8, fontsize='small')
            
            # Add data range information in the corner
            if self.DatesCombo.currentIndex() != 0:  # Not raw data
                date_text = f"Data period: {self.FSDate} to {self.FEdate}"
                plt.figtext(0.01, 0.01, date_text, fontsize=8, ha='left')
            
            # Adjust layout
            figure.tight_layout()
            
            # Add buttons below the plot
            button_layout = QHBoxLayout()
            
            # Save button - saves chart as image
            save_button = QPushButton("Save Chart")
            save_button.clicked.connect(lambda: self.save_chart_image(figure))
            button_layout.addWidget(save_button)
            
            # Print button
            print_button = QPushButton("Print Chart")
            print_button.clicked.connect(lambda: self.print_chart(figure))
            button_layout.addWidget(print_button)
            
            # Export Data button
            if not self.save_root:  # Only show if data hasn't been saved already
                export_button = QPushButton("Export Data")
                export_button.clicked.connect(self.export_chart_data)
                button_layout.addWidget(export_button)
            
            # Close button
            close_button = QPushButton("Close")
            close_button.clicked.connect(self.chart_window.accept)
            button_layout.addWidget(close_button)
            
            # Add buttons to the layout
            chart_layout.addLayout(button_layout)
            
            # Update progress
            self.progress_bar.setValue(100)
            self.progress_bar.setFormat("Chart Created")
            
            # Display the chart window modally
            self.chart_window.exec_()
            
        except Exception as e:
            print(f"Error creating chart: {str(e)}")
            QMessageBox.critical(self, "Chart Error", 
                            f"An error occurred while creating the chart: {str(e)}")

    def save_chart_image(self, figure):
        """Saves the chart as an image file"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self.chart_window,
                "Save Chart",
                "",
                "PNG Files (*.png);;JPEG Files (*.jpg);;PDF Files (*.pdf);;SVG Files (*.svg)")
            
            if file_path:
                figure.savefig(file_path, dpi=300, bbox_inches='tight')
                QMessageBox.information(self.chart_window, "Save Successful", 
                                    f"Chart successfully saved to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self.chart_window, "Save Error", 
                            f"Error saving chart: {str(e)}")

    def print_chart(self, figure):
        """Prints the chart"""
        try:
            from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
            from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
            from PyQt5.QtGui import QPainter, QPixmap, QImage
            
            printer = QPrinter(QPrinter.HighResolution)
            dialog = QPrintDialog(printer, self.chart_window)
            
            if dialog.exec_() == QPrintDialog.Accepted:
                # Create a QPainter to paint on the printer
                painter = QPainter()
                if painter.begin(printer):
                    # Get the size of the printer page
                    rect = painter.viewport()
                    
                    # Create a QPixmap from the figure
                    canvas = FigureCanvas(figure)
                    canvas.draw()
                    pixmap = QPixmap.fromImage(QImage(canvas.buffer_rgba(), 
                                                    canvas.width(), 
                                                    canvas.height(), 
                                                    QImage.Format_RGBA8888))
                    
                    # Scale the pixmap to fit the printer page
                    scaled_pixmap = pixmap.scaled(rect.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    
                    # Center the pixmap on the page
                    x = (rect.width() - scaled_pixmap.width()) / 2
                    y = (rect.height() - scaled_pixmap.height()) / 2
                    
                    # Draw the pixmap on the printer
                    painter.drawPixmap(x, y, scaled_pixmap)
                    painter.end()
                    
                    QMessageBox.information(self.chart_window, "Print Successful", 
                                        "Chart has been sent to the printer.")
        except Exception as e:
            QMessageBox.critical(self.chart_window, "Print Error", 
                            f"Error printing chart: {str(e)}")

    def export_chart_data(self):
        """Exports the chart data to a CSV file"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self.chart_window,
                "Export Data",
                "",
                "CSV Files (*.csv)")
            
            if file_path:
                with open(file_path, 'w', newline='') as csv_file:
                    writer = csv.writer(csv_file)
                    
                    # Write header row
                    header = ["TimeLabel"]
                    for i in range(self.total_time_series_files):
                        header.append(self.AllFilesList[i])
                    writer.writerow(header)
                    
                    # Write data rows
                    for j in range(self.TimeSeriesLength):
                        row = []
                        if j < len(self.TimeSeriesData):
                            # Add time label
                            row.append(self.TimeSeriesData[j][0])
                            
                            # Add data values
                            for i in range(1, self.total_time_series_files + 1):
                                if i < len(self.TimeSeriesData[j]):
                                    row.append(self.TimeSeriesData[j][i])
                                else:
                                    row.append("")
                            
                            writer.writerow(row)
                
                QMessageBox.information(self.chart_window, "Export Successful", 
                                    f"Data successfully exported to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self.chart_window, "Export Error", 
                            f"Error exporting data: {str(e)}")
    
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
            self.CurrentDay = current_day
            self.CurrentMonth = current_month
            self.CurrentYear = current_year
            total_numbers = 0
            
            # Skip unwanted data at the start of the file
            date_start = datetime(current_day=current_day, month=current_month, year=current_year)
            date_target = datetime.strptime(self.FSDate, "%d/%m/%Y")
            
            # Loop until we reach the start date for analysis
            while date_start < date_target:
                # Check if user wants to exit
                if self.ExitAnalysis():
                    self.Mini_Reset()
                    return False
                
                # Skip data from all files
                for i in range(len(self.open_files)):
                    file = self.open_files[i]
                    
                    if self.EnsembleFile[i]:
                        # Handle multi-column file (ensemble)
                        line = file.readline()
                        if not line:  # EOF
                            break
                    else:
                        # Handle single-column file
                        line = file.readline()
                        if not line:  # EOF
                            break
                
                total_numbers += 1
                self.IncreaseDate()
                date_start = datetime(day=self.CurrentDay, month=self.CurrentMonth, year=self.CurrentYear)
                
                # Update progress bar
                progress_value = int((total_numbers / total_to_read_in) * 100)
                self.progress_bar.setValue(progress_value)
                self.progress_bar.setFormat("Skipping Unnecessary Data")
            
            # Now read in the data we want to analyze
            total_numbers = 0
            total_to_read_in = (datetime.strptime(self.FEdate, "%d/%m/%Y") - 
                            datetime.strptime(self.FSDate, "%d/%m/%Y")).days + 1
            
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.progress_bar.setMaximum(100)
            self.progress_bar.setFormat("Reading Time Series Data")
            
            # Set current date to start date for analysis
            self.CurrentDay = int(datetime.strptime(self.FSDate, "%d/%m/%Y").day)
            self.CurrentMonth = int(datetime.strptime(self.FSDate, "%d/%m/%Y").month)
            self.CurrentYear = int(datetime.strptime(self.FSDate, "%d/%m/%Y").year)
            
            # Create a temporary array for the time series data
            time_series_data2 = [[None for _ in range(self.total_time_series_files + 1)] 
                            for _ in range(total_to_read_in + 1)]
            
            # Read in the data
            date_current = datetime(day=self.CurrentDay, month=self.CurrentMonth, year=self.CurrentYear)
            date_end = datetime.strptime(self.FEdate, "%d/%m/%Y")
            
            while date_current <= date_end:
                # Check if user wants to exit
                if self.ExitAnalysis():
                    self.Mini_Reset()
                    return False
                
                total_numbers += 1
                
                # Read data for the current day from each file
                for i, file in enumerate(self.open_files):
                    try:
                        if self.EnsembleFile[i]:
                            # Handle multi-column file (ensemble)
                            line = file.readline()
                            if not line:  # EOF
                                break
                            # Extract first value from the line (comma or space separated)
                            parts = line.strip().split()
                            if len(parts) > 0:
                                if ',' in parts[0]:
                                    values = parts[0].split(',')
                                    temp_double = float(values[0]) if values[0].strip() else self.global_missing_code
                                else:
                                    temp_double = float(parts[0]) if parts[0].strip() else self.global_missing_code
                            else:
                                temp_double = self.global_missing_code
                        else:
                            # Handle single-column file
                            line = file.readline()
                            if not line:  # EOF
                                break
                            line = line.strip()
                            if line:
                                temp_double = float(line)
                            else:
                                temp_double = self.global_missing_code
                        
                        # Store the value in the time series array
                        if temp_double == self.global_missing_code:
                            any_missing = True
                            time_series_data2[total_numbers-1][i+1] = None  # Empty value for missing data
                        else:
                            time_series_data2[total_numbers-1][i+1] = temp_double
                    except ValueError:
                        # Handle conversion errors (e.g., non-numeric data)
                        any_missing = True
                        time_series_data2[total_numbers-1][i+1] = None
                
                # Set category label (day number for x-axis)
                time_series_data2[total_numbers-1][0] = str(total_numbers)
                
                # Increase date for next iteration
                self.IncreaseDate()
                date_current = datetime(day=self.CurrentDay, month=self.CurrentMonth, year=self.CurrentYear)
                
                # Update progress bar
                progress_value = int((total_numbers / total_to_read_in) * 100)
                self.progress_bar.setValue(progress_value)
                self.progress_bar.setFormat("Reading Time Series Data")
            
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
            self.CurrentDay = int(datetime.strptime(self.global_start_date, "%d/%m/%Y").day)
            self.CurrentMonth = int(datetime.strptime(self.global_start_date, "%d/%m/%Y").month)
            self.CurrentYear = int(datetime.strptime(self.global_start_date, "%d/%m/%Y").year)
            self.CurrentSeason = self.GetSeason(self.CurrentMonth)
            self.CurrentWaterYear = self.GetWaterYear(self.CurrentMonth, self.CurrentYear)
            total_numbers = 0
            
            # Skip unwanted data at the start of the file
            date_start = datetime(day=self.CurrentDay, month=self.CurrentMonth, year=self.CurrentYear)
            date_target = datetime.strptime(self.FSDate, "%d/%m/%Y")
            
            # Loop until we reach the start date for analysis
            while date_start < date_target:
                # Check if user wants to exit
                if self.ExitAnalysis():
                    self.Mini_Reset()
                    return False
                
                # Skip data from all files
                for i, file in enumerate(self.open_files):
                    try:
                        if self.EnsembleFile[i]:
                            # Handle multi-column file (ensemble)
                            line = file.readline()
                            if not line:  # EOF
                                break
                        else:
                            # Handle single-column file
                            line = file.readline()
                            if not line:  # EOF
                                break
                    except Exception as e:
                        print(f"Error reading file {i}: {str(e)}")
                        self.Mini_Reset()
                        return False
                
                total_numbers += 1
                self.IncreaseDate()
                date_start = datetime(day=self.CurrentDay, month=self.CurrentMonth, year=self.CurrentYear)
                
                # Update progress bar
                progress_value = int((total_numbers / total_to_read_in) * 100) if total_to_read_in > 0 else 100
                self.progress_bar.setValue(progress_value)
            
            # Now read in the data we want to analyze
            total_numbers = 0
            total_to_read_in = (datetime.strptime(self.FEdate, "%d/%m/%Y") - 
                            datetime.strptime(self.FSDate, "%d/%m/%Y")).days + 1
            
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.progress_bar.setMaximum(100)
            self.progress_bar.setFormat("Reading in data for plot")
            
            # Reset current date to start date for analysis
            self.CurrentDay = int(datetime.strptime(self.FSDate, "%d/%m/%Y").day)
            self.CurrentMonth = int(datetime.strptime(self.FSDate, "%d/%m/%Y").month)
            self.CurrentYear = int(datetime.strptime(self.FSDate, "%d/%m/%Y").year)
            self.CurrentSeason = self.GetSeason(self.CurrentMonth)
            self.CurrentWaterYear = self.GetWaterYear(self.CurrentMonth, self.CurrentYear)
            
            # Initialize arrays for statistics
            sum_vals = [0] * (self.total_time_series_files + 1)
            max_value = [-10000] * (self.total_time_series_files + 1)
            total_missing = [0] * (self.total_time_series_files + 1)
            pds = [0] * (self.total_time_series_files + 1)
            pot_count = [0] * (self.total_time_series_files + 1)
            count = 0
            
            # Set up period tracking variables
            this_month = self.CurrentMonth
            this_year = self.CurrentYear
            this_season = self.CurrentSeason
            this_water_year = self.CurrentWaterYear
            
            year_index = 1
            
            # Read in data and process by period
            date_current = datetime(day=self.CurrentDay, month=self.CurrentMonth, year=self.CurrentYear)
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
                
                for i, file in enumerate(self.open_files):
                    try:
                        file_idx = i + 1  # Adjust for 1-based indexing in arrays
                        if self.EnsembleFile[i]:
                            # Handle multi-column file (ensemble)
                            line = file.readline()
                            if not line:  # EOF
                                value = self.global_missing_code
                            else:
                                # Extract first value from line
                                parts = line.strip().split()
                                if len(parts) > 0:
                                    if ',' in parts[0]:
                                        values = parts[0].split(',')
                                        value = float(values[0]) if values[0].strip() else self.global_missing_code
                                    else:
                                        value = float(parts[0]) if parts[0].strip() else self.global_missing_code
                                else:
                                    value = self.global_missing_code
                        else:
                            # Handle single-column file
                            line = file.readline()
                            if not line:  # EOF
                                value = self.global_missing_code
                            else:
                                line = line.strip()
                                value = float(line) if line else self.global_missing_code
                        
                        # Store value in period array
                        self.periodArray[file_idx][count] = value
                        
                        # Update statistics
                        if value == self.global_missing_code:
                            total_missing[file_idx] += 1
                        else:
                            sum_vals[file_idx] += value
                            if max_value[file_idx] < value:
                                max_value[file_idx] = value
                            # For Partial Duration Series
                            pds[file_idx] += max(0, value - self.local_thresh)
                            # For Peaks Over Threshold
                            if value > self.pot_value:
                                pot_count[file_idx] += 1
                    
                    except Exception as e:
                        print(f"Error processing file {i} on day {count}: {str(e)}")
                        self.periodArray[i+1][count] = self.global_missing_code
                        total_missing[i+1] += 1
                
                # Save current period values
                this_month = self.CurrentMonth
                this_year = self.CurrentYear
                this_season = self.CurrentSeason
                this_water_year = self.CurrentWaterYear
                
                # Increase date for next iteration
                self.IncreaseDate()
                date_current = datetime(day=self.CurrentDay, month=self.CurrentMonth, year=self.CurrentYear)
                
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
            total_to_read_in = (datetime.strptime(self.FSDate, "%d/%m/%Y") - 
                            datetime.strptime(self.global_start_date, "%d/%m/%Y")).days
            
            if total_to_read_in > 0:
                # Show progress bar
                self.progress_bar.setVisible(True)
                self.progress_bar.setValue(0)
                self.progress_bar.setMaximum(100)
                
            # Set current date to the global start date
            self.CurrentDay = int(datetime.strptime(self.global_start_date, "%d/%m/%Y").day)
            self.CurrentMonth = int(datetime.strptime(self.global_start_date, "%d/%m/%Y").month)
            self.CurrentYear = int(datetime.strptime(self.global_start_date, "%d/%m/%Y").year)
            total_numbers = 0
            self.TotalMonths = 0  # Reset total months counter
            
            # Skip unwanted data at the start of the file
            date_start = datetime(day=self.CurrentDay, month=self.CurrentMonth, year=self.CurrentYear)
            date_target = datetime.strptime(self.FSDate, "%d/%m/%Y")
            
            # Loop until we reach the start date for analysis
            while date_start < date_target:
                # Check if user wants to exit
                if self.ExitAnalysis():
                    self.Mini_Reset()
                    return False
                
                # Skip data from all files
                for i, file in enumerate(self.open_files):
                    try:
                        if self.EnsembleFile[i]:
                            # Handle multi-column file (ensemble)
                            line = file.readline()
                            if not line:  # EOF
                                break
                        else:
                            # Handle single-column file
                            line = file.readline()
                            if not line:  # EOF
                                break
                    except Exception as e:
                        print(f"Error reading file {i}: {str(e)}")
                        self.Mini_Reset()
                        return False
                
                total_numbers += 1
                self.IncreaseDate()
                date_start = datetime(day=self.CurrentDay, month=self.CurrentMonth, year=self.CurrentYear)
                
                # Update progress bar
                progress_value = int((total_numbers / total_to_read_in) * 100) if total_to_read_in > 0 else 100
                self.progress_bar.setValue(progress_value)
            
            # Now read in the data we want to analyze
            total_numbers = 0
            total_to_read_in = (datetime.strptime(self.FEdate, "%d/%m/%Y") - 
                            datetime.strptime(self.FSDate, "%d/%m/%Y")).days + 1
            
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.progress_bar.setMaximum(100)
            self.progress_bar.setFormat("Calculating SPI")
            
            # Set current date to start date for analysis
            self.CurrentDay = int(datetime.strptime(self.FSDate, "%d/%m/%Y").day)
            self.CurrentMonth = int(datetime.strptime(self.FSDate, "%d/%m/%Y").month)
            self.CurrentYear = int(datetime.strptime(self.FSDate, "%d/%m/%Y").year)
            
            # Initialize arrays for calculations
            sum_vals = [0] * (self.total_time_series_files + 1)
            total_missing = [0] * (self.total_time_series_files + 1)
            count = 0
            
            this_month = self.CurrentMonth
            this_year = self.CurrentYear
            year_index = this_year - int(datetime.strptime(self.FSDate, "%d/%m/%Y").year) + 1
            
            # Read in data and calculate monthly sums
            date_current = datetime(day=self.CurrentDay, month=self.CurrentMonth, year=self.CurrentYear)
            date_end = datetime.strptime(self.FEdate, "%d/%m/%Y")
            
            while date_current <= date_end:
                # Check if user wants to exit
                if self.ExitAnalysis():
                    self.Mini_Reset()
                    return False
                
                # Check if we've reached the end of a month
                if this_month != self.CurrentMonth:
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
                
                for i, file in enumerate(self.open_files):
                    try:
                        file_idx = i + 1  # Adjust for 1-based indexing in arrays
                        
                        if self.EnsembleFile[i]:
                            # Handle multi-column file (ensemble)
                            line = file.readline()
                            if not line:  # EOF
                                value_in = self.global_missing_code
                            else:
                                # Extract first value from line
                                parts = line.strip().split()
                                if len(parts) > 0:
                                    if ',' in parts[0]:
                                        values = parts[0].split(',')
                                        value_in = float(values[0]) if values[0].strip() else self.global_missing_code
                                    else:
                                        value_in = float(parts[0]) if parts[0].strip() else self.global_missing_code
                                else:
                                    value_in = self.global_missing_code
                        else:
                            # Handle single-column file
                            line = file.readline()
                            if not line:  # EOF
                                value_in = self.global_missing_code
                            else:
                                line = line.strip()
                                value_in = float(line) if line else self.global_missing_code
                        
                        if value_in != self.global_missing_code:
                            if value_in > self.thresh:
                                sum_vals[file_idx] += value_in
                        else:
                            total_missing[file_idx] += 1
                    
                    except Exception as e:
                        print(f"Error processing file {i} on day {count}: {str(e)}")
                        total_missing[i+1] += 1
                
                # Update this_month and this_year
                this_month = self.CurrentMonth
                this_year = self.CurrentYear
                
                # Increase date for next iteration
                self.IncreaseDate()
                date_current = datetime(day=self.CurrentDay, month=self.CurrentMonth, year=self.CurrentYear)
                
                # Update progress bar
                progress_value = int((total_numbers / total_to_read_in) * 100)
                self.progress_bar.setValue(progress_value)
                self.progress_bar.setFormat("Reading Data for SPI")
            
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
                QMessageBox.critical(self, "Error Message", 
                                "The SPI index is longer than the fit period. Please choose a shorter SPI period.")
                return False
            
            # Update progress bar
            self.progress_bar.setFormat("Calculating SPI Values")
            self.progress_bar.setValue(50)  # Halfway through processing
            
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
                    
                    for k in range(self.spi_value):
                        idx = j+k-1
                        if idx < len(self.RunningMonths[i-1]) and self.RunningMonths[i-1][idx][0] != self.global_missing_code:
                            month_sum += self.RunningMonths[i-1][idx][0]
                        else:
                            month_missing += 1
                    
                    if month_missing == self.spi_value:  # All months missing
                        self.RunningMonths[i-1][j+self.spi_value-2][3] = self.global_missing_code
                    else:
                        # Calculate the moving average - divide by number of non-missing months
                        self.RunningMonths[i-1][j+self.spi_value-2][3] = month_sum / (self.spi_value - month_missing)
            
            # Update progress bar
            self.progress_bar.setValue(75)  # 75% through processing
            self.progress_bar.setFormat("Normalizing SPI Values")
            
            # Normalize the data (convert to SPI values)
            standard_deviation = [0] * (self.total_time_series_files + 1)
            mean_values = [0] * (self.total_time_series_files + 1)
            
            for i in range(1, self.total_time_series_files + 1):
                # Calculate mean
                total_of_all = 0
                missing = 0
                available_months = self.TotalMonths - self.spi_value + 1
                
                for j in range(self.spi_value, self.TotalMonths + 1):
                    if j <= len(self.RunningMonths[i-1]) and self.RunningMonths[i-1][j-1][3] != self.global_missing_code:
                        total_of_all += self.RunningMonths[i-1][j-1][3]
                    else:
                        missing += 1
                
                if missing == available_months:
                    QMessageBox.critical(self, "Error Message", 
                                    "Sorry - too many missing values to compute a solution.")
                    return False
                else:
                    mean_values[i] = total_of_all / (available_months - missing)
                
                # Calculate standard deviation
                missing = 0
                total_sqr_error = 0
                
                for j in range(self.spi_value, self.TotalMonths + 1):
                    if j <= len(self.RunningMonths[i-1]) and self.RunningMonths[i-1][j-1][3] != self.global_missing_code:
                        diff = self.RunningMonths[i-1][j-1][3] - mean_values[i]
                        total_sqr_error += diff * diff
                    else:
                        missing += 1
                
                if available_months - missing > 0:
                    standard_deviation[i] = math.sqrt(total_sqr_error / (available_months - missing))
                else:
                    standard_deviation[i] = 0  # Avoid division by zero
                
                # Normalize the data (SPI values)
                for j in range(self.spi_value, self.TotalMonths + 1):
                    if j <= len(self.RunningMonths[i-1]):
                        if self.RunningMonths[i-1][j-1][3] == self.global_missing_code:
                            self.RunningMonths[i-1][j-1][4] = self.global_missing_code
                        elif standard_deviation[i] == 0:
                            self.RunningMonths[i-1][j-1][4] = 0  # Avoid division by zero
                        else:
                            # Calculate standardized (normalized) values (Z-scores)
                            self.RunningMonths[i-1][j-1][4] = ((self.RunningMonths[i-1][j-1][3] - mean_values[i]) / 
                                                        standard_deviation[i])
            
            # Update summaryArray with SPI values
            for i in range(1, self.total_time_series_files + 1):
                for j in range(1, self.TotalMonths + 1):
                    if j <= len(self.RunningMonths[i-1]):
                        year = int(self.RunningMonths[i-1][j-1][1])
                        month = int(self.RunningMonths[i-1][j-1][2])
                        if year < len(self.summaryArray[i]) and month < len(self.summaryArray[i][year]):
                            self.summaryArray[i][year][month][5] = self.RunningMonths[i-1][j-1][4]
            
            # Update progress bar
            self.progress_bar.setValue(90)  # 90% through processing
            self.progress_bar.setFormat("Preparing SPI Time Series")
            
            # Prepare data for plotting
            self.TimeSeriesLength = self.TotalMonths - self.spi_value + 1
            # Create and initialize the TimeSeriesData array
            self.TimeSeriesData = [[None for _ in range(self.total_time_series_files + 1)] 
                                for _ in range(self.TimeSeriesLength)]
            
            any_missing = False
            
            for i in range(1, self.total_time_series_files + 1):
                array_index = 0
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
                        if array_index < self.TimeSeriesLength:
                            if j < len(self.summaryArray[i]) and k < len(self.summaryArray[i][j]) and self.summaryArray[i][j][k][5] == self.global_missing_code:
                                self.TimeSeriesData[array_index][i] = None  # Empty value
                                any_missing = True
                            elif j < len(self.summaryArray[i]) and k < len(self.summaryArray[i][j]):
                                self.TimeSeriesData[array_index][i] = self.summaryArray[i][j][k][5]
                            
                            # Set month/year as X-axis label
                            month_name = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                                        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][k]
                            self.TimeSeriesData[array_index][0] = f"{month_name} {j+int(datetime.strptime(self.FSDate, '%d/%m/%Y').year)-1}"
                            
                            array_index += 1
            
            # Update progress bar
            self.progress_bar.setValue(100)  # Processing complete
            self.progress_bar.setFormat("SPI Calculation Complete")
            
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
            year_percentile = [[self.global_missing_code for _ in range(200)] for _ in range(6)]
            total_to_read_in = (datetime.strptime(self.FSDate, "%d/%m/%Y") - 
                            datetime.strptime(self.global_start_date, "%d/%m/%Y")).days
            
            # Show progress bar if we need to skip data
            if total_to_read_in > 0:
                self.progress_bar.setVisible(True)
                self.progress_bar.setValue(0)
                self.progress_bar.setMaximum(100)
                self.progress_bar.setFormat("Skipping Unnecessary Annual Data")
            
            # Set cursor to hourglass
            self.setCursor(Qt.WaitCursor)
            
            # Initialize date to start date
            self.CurrentDay = int(datetime.strptime(self.global_start_date, "%d/%m/%Y").day)
            self.CurrentMonth = int(datetime.strptime(self.global_start_date, "%d/%m/%Y").month)
            self.CurrentYear = int(datetime.strptime(self.global_start_date, "%d/%m/%Y").year)
            self.CurrentSeason = self.GetSeason(self.CurrentMonth)
            self.CurrentWaterYear = self.GetWaterYear(self.CurrentMonth, self.CurrentYear)
            total_numbers = 0
            
            # --- PASS 1: Calculate annual percentiles ---
            
            # Skip to analysis start date
            date_start = datetime(day=self.CurrentDay, month=self.CurrentMonth, year=self.CurrentYear)
            date_target = datetime.strptime(self.FSDate, "%d/%m/%Y")
            
            # Store original file positions so we can rewind later
            original_positions = []
            
            # Skip unwanted data at the start
            while date_start < date_target:
                if self.ExitAnalysis():
                    self.Mini_Reset()
                    return False
                
                # Skip a line in each file
                for file in self.open_files:
                    file.readline()
                
                total_numbers += 1
                self.IncreaseDate()
                date_start = datetime(day=self.CurrentDay, month=self.CurrentMonth, year=self.CurrentYear)
                
                # Update progress
                if total_to_read_in > 0:
                    progress_value = int((total_numbers / total_to_read_in) * 100)
                    self.progress_bar.setValue(progress_value)
            
            # Now read annual data for percentile calculation
            total_numbers = 0
            total_to_read_in = (datetime.strptime(self.FEdate, "%d/%m/%Y") - 
                        datetime.strptime(self.FSDate, "%d/%m/%Y")).days + 1
            
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.progress_bar.setMaximum(100)
            self.progress_bar.setFormat("Reading Annual Data")
            
            # Reset to analysis start date
            self.CurrentDay = int(datetime.strptime(self.FSDate, "%d/%m/%Y").day)
            self.CurrentMonth = int(datetime.strptime(self.FSDate, "%d/%m/%Y").month)
            self.CurrentYear = int(datetime.strptime(self.FSDate, "%d/%m/%Y").year)
            self.CurrentSeason = self.GetSeason(self.CurrentMonth)
            self.CurrentWaterYear = self.GetWaterYear(self.CurrentMonth, self.CurrentYear)
            
            # Initialize count array - tracks valid data points per file
            count = [0] * 6
            
            this_year = self.CurrentYear
            year_index = 1
            
            # Read data for annual percentile calculations
            date_current = datetime(day=self.CurrentDay, month=self.CurrentMonth, year=self.CurrentYear)
            date_end = datetime.strptime(self.FEdate, "%d/%m/%Y")
            
            while date_current <= date_end:
                # Check for user exit
                if self.ExitAnalysis():
                    self.Mini_Reset()
                    return False
                
                # Check if we've reached end of year
                if this_year != self.CurrentYear:
                    year_index = this_year - int(datetime.strptime(self.FSDate, "%d/%m/%Y").year) + 1
                    
                    # Calculate percentiles for each file for this year
                    for i in range(1, self.total_time_series_files + 1):
                        if count[i] == 0:  # No valid data
                            year_percentile[i][year_index] = self.global_missing_code
                        else:
                            year_percentile[i][year_index] = self.PercentilePeriodArray(i, count[i], self.annual_percentile)
                    
                    # Reset counters
                    for i in range(1, self.total_time_series_files + 1):
                        count[i] = 0
                
                # Read data for current day
                total_numbers += 1
                
                for i, file in enumerate(self.open_files):
                    try:
                        file_idx = i + 1  # Adjust for 1-based indexing in arrays
                        
                        line = file.readline()
                        if not line:  # EOF
                            value_in = self.global_missing_code
                        else:
                            # Extract value from line
                            if self.EnsembleFile[i]:
                                # Handle multi-column file
                                parts = line.strip().split()
                                if len(parts) > 0:
                                    if ',' in parts[0]:
                                        values = parts[0].split(',')
                                        value_in = float(values[0]) if values[0].strip() else self.global_missing_code
                                    else:
                                        value_in = float(parts[0]) if parts[0].strip() else self.global_missing_code
                                else:
                                    value_in = self.global_missing_code
                            else:
                                # Handle single-column file
                                line = line.strip()
                                value_in = float(line) if line else self.global_missing_code
                        
                        # Store valid precipitation values
                        if value_in != self.global_missing_code and value_in >= self.thresh:
                            count[file_idx] += 1
                            self.periodArray[file_idx][count[file_idx]] = value_in
                    
                    except Exception as e:
                        print(f"Error processing file {i} on day {total_numbers}: {str(e)}")
                
                this_year = self.CurrentYear
                
                # Increment date
                self.IncreaseDate()
                date_current = datetime(day=self.CurrentDay, month=self.CurrentMonth, year=self.CurrentYear)
                
                # Update progress
                progress_value = int((total_numbers / total_to_read_in) * 100)
                self.progress_bar.setValue(progress_value)
            
            # Process the last year's data
            year_index = this_year - int(datetime.strptime(self.FSDate, "%d/%m/%Y").year) + 1
            
            for i in range(1, self.total_time_series_files + 1):
                if count[i] == 0:  # No valid data
                    year_percentile[i][year_index] = self.global_missing_code
                else:
                    year_percentile[i][year_index] = self.PercentilePeriodArray(i, count[i], self.annual_percentile)
            
            # --- PASS 2: Calculate percentage above annual percentile ---
            
            # Reset file positions for second pass by reopening files
            self.close_open_files()
            
            # Reopen the files
            self.open_files = []
            for i, file_path in enumerate(self.AllFilesList):
                try:
                    # Find the full path
                    full_path = ""
                    if i < self.left_files_count:
                        full_path = os.path.join(self.fileSelectionLeft.file_list.path, file_path)
                    else:
                        full_path = os.path.join(self.fileSelectionRight.file_list.path, file_path)
                    
                    # Open the file
                    input_file = open(full_path, 'r')
                    self.open_files.append(input_file)
                except Exception as e:
                    print(f"Error reopening file {file_path}: {str(e)}")
                    self.Mini_Reset()
                    return False
            
            # Skip to analysis start date again
            self.CurrentDay = int(datetime.strptime(self.global_start_date, "%d/%m/%Y").day)
            self.CurrentMonth = int(datetime.strptime(self.global_start_date, "%d/%m/%Y").month)
            self.CurrentYear = int(datetime.strptime(self.global_start_date, "%d/%m/%Y").year)
            self.CurrentSeason = self.GetSeason(self.CurrentMonth)
            self.CurrentWaterYear = self.GetWaterYear(self.CurrentMonth, self.CurrentYear)
            total_numbers = 0
            
            date_start = datetime(day=self.CurrentDay, month=self.CurrentMonth, year=self.CurrentYear)
            date_target = datetime.strptime(self.FSDate, "%d/%m/%Y")
            
            # Skip unwanted data at start of second pass
            while date_start < date_target:
                for file in self.open_files:
                    file.readline()
                
                self.IncreaseDate()
                date_start = datetime(day=self.CurrentDay, month=self.CurrentMonth, year=self.CurrentYear)
            
            # Now read data for period calculations
            total_numbers = 0
            total_to_read_in = (datetime.strptime(self.FEdate, "%d/%m/%Y") - 
                        datetime.strptime(self.FSDate, "%d/%m/%Y")).days + 1
            
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.progress_bar.setMaximum(100)
            self.progress_bar.setFormat("Calculating Percentages")
            
            # Reset count array and dates
            count = [0] * 6
            
            self.CurrentDay = int(datetime.strptime(self.FSDate, "%d/%m/%Y").day)
            self.CurrentMonth = int(datetime.strptime(self.FSDate, "%d/%m/%Y").month)
            self.CurrentYear = int(datetime.strptime(self.FSDate, "%d/%m/%Y").year)
            self.CurrentSeason = self.GetSeason(self.CurrentMonth)
            self.CurrentWaterYear = self.GetWaterYear(self.CurrentMonth, self.CurrentYear)
            
            this_month = self.CurrentMonth
            this_year = self.CurrentYear
            this_season = self.CurrentSeason
            this_water_year = self.CurrentWaterYear
            
            year_index = 1
            
            # Read data for period calculations
            date_current = datetime(day=self.CurrentDay, month=self.CurrentMonth, year=self.CurrentYear)
            date_end = datetime.strptime(self.FEdate, "%d/%m/%Y")
            
            # Initialize fraction result array
            for i in range(self.total_time_series_files):
                for j in range(200):
                    self.FractionResult[i][j] = self.global_missing_code
            
            while date_current <= date_end:
                # Check for user exit
                if self.ExitAnalysis():
                    self.Mini_Reset()
                    return False
                
                # Check if we've reached end of period
                if self.FinishedCurrentPeriod():
                    year_index = this_year - int(datetime.strptime(self.FSDate, "%d/%m/%Y").year) + 1
                    
                    # Only calculate if this is the selected period
                    if (this_month == self.DatesCombo.currentIndex() or 
                        (this_season + 12) == self.DatesCombo.currentIndex()):
                        
                        for i in range(1, self.total_time_series_files + 1):
                            if count[i] == 0:  # No valid data
                                self.FractionResult[i-1][year_index] = self.global_missing_code
                            else:
                                # Calculate % precipitation above annual percentile
                                self.FractionResult[i-1][year_index] = self.FindPrecipAboveAnnPercentile(
                                    i, count[i], year_percentile[i][year_index])
                    
                    # Reset counters
                    for i in range(1, 6):
                        count[i] = 0
                
                # Read data for current day
                total_numbers += 1
                
                for i, file in enumerate(self.open_files):
                    try:
                        file_idx = i + 1  # Adjust for 1-based indexing in arrays
                        
                        line = file.readline()
                        if not line:  # EOF
                            value_in = self.global_missing_code
                        else:
                            # Extract value from line
                            if self.EnsembleFile[i]:
                                # Handle multi-column file
                                parts = line.strip().split()
                                if len(parts) > 0:
                                    if ',' in parts[0]:
                                        values = parts[0].split(',')
                                        value_in = float(values[0]) if values[0].strip() else self.global_missing_code
                                    else:
                                        value_in = float(parts[0]) if parts[0].strip() else self.global_missing_code
                                else:
                                    value_in = self.global_missing_code
                            else:
                                # Handle single-column file
                                line = line.strip()
                                value_in = float(line) if line else self.global_missing_code
                        
                        # Store valid precipitation values
                        if value_in != self.global_missing_code and value_in >= self.thresh:
                            if count[file_idx] < len(self.periodArray[file_idx]) - 1:  # Check array bounds
                                count[file_idx] += 1
                                self.periodArray[file_idx][count[file_idx]] = value_in
                    
                    except Exception as e:
                        print(f"Error processing file {i} on day {total_numbers}: {str(e)}")
                
                # Save current period values
                this_month = self.CurrentMonth
                this_year = self.CurrentYear
                this_season = self.CurrentSeason
                this_water_year = self.CurrentWaterYear
                
                # Increment date
                self.IncreaseDate()
                date_current = datetime(day=self.CurrentDay, month=self.CurrentMonth, year=self.CurrentYear)
                
                # Update progress
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
                        # Calculate % precipitation above annual percentile
                        self.FractionResult[i-1][year_index] = self.FindPrecipAboveAnnPercentile(
                            i, count[i], year_percentile[i][year_index])
            
            # Determine start and end years for output
            start_year = 1
            end_year = year_index
            
            # Adjust based on selected period
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
            
            # Prepare time series data for plotting
            self.TimeSeriesLength = end_year - start_year + 1
            self.TimeSeriesData = [[None for _ in range(self.total_time_series_files + 1)] 
                                for _ in range(self.TimeSeriesLength)]
            
            any_missing = False
            
            for i in range(1, self.total_time_series_files + 1):
                for j in range(1, self.TimeSeriesLength + 1):
                    idx = j + start_year - 1
                    
                    if idx < len(self.FractionResult[i-1]) and self.FractionResult[i-1][idx] == self.global_missing_code:
                        self.TimeSeriesData[j-1][i] = None
                        any_missing = True
                    elif idx < len(self.FractionResult[i-1]):
                        self.TimeSeriesData[j-1][i] = self.FractionResult[i-1][idx]
                    else:
                        self.TimeSeriesData[j-1][i] = None
                        any_missing = True
                    
                    # Set year label for x-axis
                    if self.DatesCombo.currentIndex() == 18:  # Water year
                        self.TimeSeriesData[j-1][0] = str(int(datetime.strptime(self.FSDate, "%d/%m/%Y").year) + j + start_year - 3)
                    else:
                        self.TimeSeriesData[j-1][0] = str(int(datetime.strptime(self.FSDate, "%d/%m/%Y").year) + start_year + j - 2)
            
            # Final progress update
            self.progress_bar.setValue(100)
            self.progress_bar.setFormat("Percentile Calculation Complete")
            
            if any_missing:
                print("Warning - some of the data were missing and will not be plotted.")
            
            # Reset cursor
            self.setCursor(Qt.ArrowCursor)
            
            return True
        
        except Exception as e:
            print(f"Error in GeneratePrecipAnnualMax: {str(e)}")
            traceback.print_exc()  # Print full traceback for debugging
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
                self.progress_bar.setFormat("Skipping Unnecessary Data")
            
            # Initialize long term percentile array to store percentiles for each file
            long_term_percentile = [self.global_missing_code] * 6  # [1-5]
            
            # Set current date to the global start date
            self.CurrentDay = int(datetime.strptime(self.global_start_date, "%d/%m/%Y").day)
            self.CurrentMonth = int(datetime.strptime(self.global_start_date, "%d/%m/%Y").month)
            self.CurrentYear = int(datetime.strptime(self.global_start_date, "%d/%m/%Y").year)
            self.CurrentSeason = self.GetSeason(self.CurrentMonth)
            self.CurrentWaterYear = self.GetWaterYear(self.CurrentMonth, self.CurrentYear)
            total_numbers = 0
            
            # Set cursor to hourglass
            self.setCursor(Qt.WaitCursor)
            
            # Skip unwanted data at the start of the file
            date_start = datetime(day=self.CurrentDay, month=self.CurrentMonth, year=self.CurrentYear)
            date_target = datetime.strptime(self.FSDate, "%d/%m/%Y")
            
            # Loop until we reach the start date for analysis
            while date_start < date_target:
                # Check if user wants to exit
                if self.ExitAnalysis():
                    self.Mini_Reset()
                    return False
                
                # Skip data from all files
                for i, file in enumerate(self.open_files):
                    try:
                        if self.EnsembleFile[i]:
                            # Handle multi-column file (ensemble)
                            line = file.readline()
                            if not line:  # EOF
                                break
                        else:
                            # Handle single-column file
                            line = file.readline()
                            if not line:  # EOF
                                break
                    except Exception as e:
                        print(f"Error reading file {i}: {str(e)}")
                        self.Mini_Reset()
                        return False
                
                total_numbers += 1
                self.IncreaseDate()
                date_start = datetime(day=self.CurrentDay, month=self.CurrentMonth, year=self.CurrentYear)
                
                # Update progress bar
                progress_value = int((total_numbers / total_to_read_in) * 100) if total_to_read_in > 0 else 100
                self.progress_bar.setValue(progress_value)
            
            # Now read in all data to calculate long-term percentiles
            total_numbers = 0
            total_to_read_in = (datetime.strptime(self.FEdate, "%d/%m/%Y") - 
                            datetime.strptime(self.FSDate, "%d/%m/%Y")).days + 1
            
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.progress_bar.setMaximum(100)
            self.progress_bar.setFormat("Reading All Data")
            
            # Reset current date to start date for analysis
            self.CurrentDay = int(datetime.strptime(self.FSDate, "%d/%m/%Y").day)
            self.CurrentMonth = int(datetime.strptime(self.FSDate, "%d/%m/%Y").month)
            self.CurrentYear = int(datetime.strptime(self.FSDate, "%d/%m/%Y").year)
            self.CurrentSeason = self.GetSeason(self.CurrentMonth)
            self.CurrentWaterYear = self.GetWaterYear(self.CurrentMonth, self.CurrentYear)
            
            # Initialize count array - tracks valid data for each file
            count = [0] * 6
            
            # Read all data to calculate long-term percentile
            date_current = datetime(day=self.CurrentDay, month=self.CurrentMonth, year=self.CurrentYear)
            date_end = datetime.strptime(self.FEdate, "%d/%m/%Y")
            
            while date_current <= date_end:
                # Check if user wants to exit
                if self.ExitAnalysis():
                    self.Mini_Reset()
                    return False
                
                # Read data for the current day
                total_numbers += 1
                
                for i, file in enumerate(self.open_files):
                    try:
                        file_idx = i + 1  # Adjust for 1-based indexing in arrays
                        
                        if self.EnsembleFile[i]:
                            # Handle multi-column file (ensemble)
                            line = file.readline()
                            if not line:  # EOF
                                value_in = self.global_missing_code
                            else:
                                # Extract first value from line
                                parts = line.strip().split()
                                if len(parts) > 0:
                                    if ',' in parts[0]:
                                        values = parts[0].split(',')
                                        value_in = float(values[0]) if values[0].strip() else self.global_missing_code
                                    else:
                                        value_in = float(parts[0]) if parts[0].strip() else self.global_missing_code
                                else:
                                    value_in = self.global_missing_code
                        else:
                            # Handle single-column file
                            line = file.readline()
                            if not line:  # EOF
                                value_in = self.global_missing_code
                            else:
                                line = line.strip()
                                value_in = float(line) if line else self.global_missing_code
                        
                        if value_in != self.global_missing_code and value_in >= self.thresh:
                            count[file_idx] += 1
                            self.periodArray[file_idx][count[file_idx]] = value_in
                    
                    except Exception as e:
                        print(f"Error processing file {i} on day {total_numbers}: {str(e)}")
                
                # Increase date for next iteration
                self.IncreaseDate()
                date_current = datetime(day=self.CurrentDay, month=self.CurrentMonth, year=self.CurrentYear)
                
                # Update progress bar
                progress_value = int((total_numbers / total_to_read_in) * 100)
                self.progress_bar.setValue(progress_value)
                self.progress_bar.setFormat("Reading All Data")
            
            # Get the correct percentile value based on selected statistic
            if self.statCheckboxes[22].isChecked():  # pfl90 selected
                ptile = self.pfl90_percentile
            else:  # pnl90 selected
                ptile = self.pnl90_percentile
            
            # Calculate long-term percentiles for each file
            for i in range(1, self.total_time_series_files + 1):
                if count[i] > 0:
                    long_term_percentile[i] = self.PercentilePeriodArray(i, count[i], ptile)
                else:
                    long_term_percentile[i] = self.global_missing_code
            
            # Close and reopen files to process monthly/seasonal data
            self.close_open_files()
            
            # Reopen the files
            file_no = 2
            for i, file_path in enumerate(self.AllFilesList):
                try:
                    # Find the full path based on whether the file is in left or right list
                    if i < self.left_files_count:
                        full_path = os.path.join(self.fileSelectionLeft.findChild(QListWidget).path, file_path)
                    else:
                        full_path = os.path.join(self.fileSelectionRight.findChild(QListWidget).path, file_path)
                    
                    # Check if this is an ensemble file
                    with open(full_path, 'r') as f:
                        line = f.readline()
                        if len(line) > 15:
                            self.EnsembleFile[i] = True
                    
                    # Open the file for reading
                    input_file = open(full_path, 'r')
                    self.open_files.append(input_file)
                except Exception as e:
                    print(f"Error reopening file {file_path}: {str(e)}")
                    self.Mini_Reset()
                    return False
            
            # Skip unwanted data at the start of the file again for second pass
            self.CurrentDay = int(datetime.strptime(self.global_start_date, "%d/%m/%Y").day)
            self.CurrentMonth = int(datetime.strptime(self.global_start_date, "%d/%m/%Y").month)
            self.CurrentYear = int(datetime.strptime(self.global_start_date, "%d/%m/%Y").year)
            self.CurrentSeason = self.GetSeason(self.CurrentMonth)
            self.CurrentWaterYear = self.GetWaterYear(self.CurrentMonth, self.CurrentYear)
            total_numbers = 0
            
            date_start = datetime(day=self.CurrentDay, month=self.CurrentMonth, year=self.CurrentYear)
            date_target = datetime.strptime(self.FSDate, "%d/%m/%Y")
            
            # Loop until we reach the start date for analysis (second pass)
            while date_start < date_target:
                for i, file in enumerate(self.open_files):
                    line = file.readline()  # Skip a line
                
                total_numbers += 1
                self.IncreaseDate()
                date_start = datetime(day=self.CurrentDay, month=self.CurrentMonth, year=self.CurrentYear)
            
            # Now read in data for period calculations
            total_numbers = 0
            total_to_read_in = (datetime.strptime(self.FEdate, "%d/%m/%Y") - 
                            datetime.strptime(self.FSDate, "%d/%m/%Y")).days + 1
            
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.progress_bar.setMaximum(100)
            self.progress_bar.setFormat("Calculating Long-Term Statistics")
            
            # Reset current date to start date for second pass
            self.CurrentDay = int(datetime.strptime(self.FSDate, "%d/%m/%Y").day)
            self.CurrentMonth = int(datetime.strptime(self.FSDate, "%d/%m/%Y").month)
            self.CurrentYear = int(datetime.strptime(self.FSDate, "%d/%m/%Y").year)
            self.CurrentSeason = self.GetSeason(self.CurrentMonth)
            self.CurrentWaterYear = self.GetWaterYear(self.CurrentMonth, self.CurrentYear)
            
            # Arrays for tracking statistics
            rainfall_above_percentile = [0] * 6
            total_rainfall_in_period = [0] * 6
            count_of_events_above_percentile = [0] * 6
            count = [0] * 6
            
            this_month = self.CurrentMonth
            this_year = self.CurrentYear
            this_season = self.CurrentSeason
            this_water_year = self.CurrentWaterYear
            
            year_index = 1
            
            # Read data for period calculations (month/season)
            date_current = datetime(day=self.CurrentDay, month=self.CurrentMonth, year=self.CurrentYear)
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
                                    if total_rainfall_in_period[i] > 0:
                                        self.LongTermResults[i-1][year_index] = (rainfall_above_percentile[i] / 
                                                                        total_rainfall_in_period[i]) * 100
                                    else:
                                        self.LongTermResults[i-1][year_index] = self.global_missing_code
                                else:  # pnl90 selected
                                    # Count of events above long-term percentile
                                    self.LongTermResults[i-1][year_index] = count_of_events_above_percentile[i]
                    
                    # Reset counters for next period
                    for i in range(1, 6):
                        rainfall_above_percentile[i] = 0
                        total_rainfall_in_period[i] = 0
                        count_of_events_above_percentile[i] = 0
                        count[i] = 0
                
                # Read data for the current day
                total_numbers += 1
                
                for i, file in enumerate(self.open_files):
                    try:
                        file_idx = i + 1  # Adjust for 1-based indexing in arrays
                        
                        if self.EnsembleFile[i]:
                            # Handle multi-column file (ensemble)
                            line = file.readline()
                            if not line:  # EOF
                                value_in = self.global_missing_code
                            else:
                                # Extract first value from line
                                parts = line.strip().split()
                                if len(parts) > 0:
                                    if ',' in parts[0]:
                                        values = parts[0].split(',')
                                        value_in = float(values[0]) if values[0].strip() else self.global_missing_code
                                    else:
                                        value_in = float(parts[0]) if parts[0].strip() else self.global_missing_code
                                else:
                                    value_in = self.global_missing_code
                        else:
                            # Handle single-column file
                            line = file.readline()
                            if not line:  # EOF
                                value_in = self.global_missing_code
                            else:
                                line = line.strip()
                                value_in = float(line) if line else self.global_missing_code
                        
                        if value_in != self.global_missing_code and value_in >= self.thresh:
                            count[file_idx] += 1
                            total_rainfall_in_period[file_idx] += value_in
                            
                            # Check if this value is above the long-term percentile
                            if long_term_percentile[file_idx] != self.global_missing_code and value_in > long_term_percentile[file_idx]:
                                count_of_events_above_percentile[file_idx] += 1
                                rainfall_above_percentile[file_idx] += value_in
                    
                    except Exception as e:
                        print(f"Error processing file {i} on day {total_numbers}: {str(e)}")
                
                # Save current period values
                this_month = self.CurrentMonth
                this_year = self.CurrentYear
                this_season = self.CurrentSeason
                this_water_year = self.CurrentWaterYear
                
                # Increase date for next iteration
                self.IncreaseDate()
                date_current = datetime(day=self.CurrentDay, month=self.CurrentMonth, year=self.CurrentYear)
                
                # Update progress bar
                progress_value = int((total_numbers / total_to_read_in) * 100)
                self.progress_bar.setValue(progress_value)
                self.progress_bar.setFormat("Calculating Long-Term Statistics")
            
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
                            if total_rainfall_in_period[i] > 0:
                                self.LongTermResults[i-1][year_index] = (rainfall_above_percentile[i] / 
                                                                total_rainfall_in_period[i]) * 100
                            else:
                                self.LongTermResults[i-1][year_index] = self.global_missing_code
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
            self.TimeSeriesLength = max(1, end_year - start_year + 1)  # Ensure at least one point
            
            # Create and initialize the TimeSeriesData array
            self.TimeSeriesData = [[None for _ in range(self.total_time_series_files + 1)] 
                                for _ in range(self.TimeSeriesLength)]
            
            any_missing = False
            
            for i in range(1, self.total_time_series_files + 1):
                for j in range(1, self.TimeSeriesLength + 1):
                    year_idx = j + start_year - 1
                    
                    if year_idx <= len(self.LongTermResults[i-1]) and self.LongTermResults[i-1][year_idx] == self.global_missing_code:
                        self.TimeSeriesData[j-1][i] = None  # Empty value
                        any_missing = True
                    elif year_idx <= len(self.LongTermResults[i-1]):
                        self.TimeSeriesData[j-1][i] = self.LongTermResults[i-1][year_idx]
                    else:
                        self.TimeSeriesData[j-1][i] = None
                        any_missing = True
                    
                    if self.DatesCombo.currentIndex() == 18:  # Water year
                        self.TimeSeriesData[j-1][0] = str(int(datetime.strptime(self.FSDate, "%d/%m/%Y").year) + j + start_year - 3)
                    else:
                        self.TimeSeriesData[j-1][0] = str(int(datetime.strptime(self.FSDate, "%d/%m/%Y").year) + start_year + j - 2)
            
            # Update progress bar
            self.progress_bar.setValue(100)
            self.progress_bar.setFormat("Long-Term Statistics Complete")
            
            if any_missing:
                print("Warning - some of the data were missing and will not be plotted.")
            
            # Reset cursor
            self.setCursor(Qt.ArrowCursor)
            
            return True
        
        except Exception as e:
            print(f"Error in LongTermStats: {str(e)}")
            traceback.print_exc()  # Print the full traceback for debugging
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

    def PercentilePeriodArray(self, file_number, size, ptile):
        try:
            # Create a filtered copy without missing values
            valid_values = []
            
            # Handle Python's 0-based indexing vs VB's 1-based indexing
            file_idx = file_number if isinstance(file_number, int) else int(file_number)
            
            # Extract non-missing values
            for i in range(size):
                if i < len(self.periodArray[file_idx]) and self.periodArray[file_idx][i] != self.global_missing_code:
                    valid_values.append(self.periodArray[file_idx][i])
            
            # Handle edge cases
            valid_size = len(valid_values)
            if valid_size == 0:
                return self.global_missing_code
            elif valid_size == 1:
                return valid_values[0]
            
            # Sort the values in ascending order
            valid_values.sort()
            
            # Calculate the position for the percentile
            # Formula for percentile position: 1 + (P/100) * (n-1) where P is percentile and n is sample size
            position = 1 + (ptile * (valid_size - 1) / 100)
            
            # Get the indices for interpolation
            lower_idx = int(position) - 1  # Adjust for 0-based indexing
            upper_idx = min(lower_idx + 1, valid_size - 1)  # Ensure we don't go out of bounds
            
            # Calculate the interpolation proportion
            fraction = position - int(position)
            
            # Handle edge cases where indices are the same
            if lower_idx == upper_idx:
                return valid_values[lower_idx]
            
            # Calculate the interpolated value
            range_value = valid_values[upper_idx] - valid_values[lower_idx]
            result = valid_values[lower_idx] + (range_value * fraction)
            
            return result
        
        except Exception as e:
            print(f"Error in PercentilePeriodArray: {str(e)}")
            traceback.print_exc()  # Print full traceback for debugging
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
            wet_count = 0                           # Counter for consecutive wet days
            self.TotalWetSpells[file_no] = 0        # Reset count of wet spells
            
            # Convert file_no to 0-based indexing if it's coming from 1-based code
            file_idx = file_no
            
            # Initialize spell array - clear any existing values
            self.WetSpellArray[file_idx] = [0] * len(self.WetSpellArray[file_idx])
            
            # Skip processing if no data
            if size_of <= 0:
                return
            
            # Determine initial state - are we starting in a wet spell?
            if (self.periodArray[file_idx][0] == self.global_missing_code or 
                self.periodArray[file_idx][0] <= self.thresh):
                is_wet = False                      # Start as not in a wet spell
            else:
                is_wet = True                       # Start in a wet spell
                wet_count = 1
            
            # Process each day
            for i in range(1, size_of):
                # Make sure we don't exceed array bounds
                if i >= len(self.periodArray[file_idx]):
                    break
                    
                # Case 1: Continuing wet spell (wet day follows wet day)
                if is_wet and self.periodArray[file_idx][i] > self.thresh:
                    wet_count += 1
                    
                # Case 2: End of wet spell (dry or missing day follows wet day)
                elif is_wet and (self.periodArray[file_idx][i] <= self.thresh or 
                                self.periodArray[file_idx][i] == self.global_missing_code):
                    # Record the completed wet spell
                    self.TotalWetSpells[file_idx] += 1
                    spell_idx = self.TotalWetSpells[file_idx] - 1
                    if spell_idx < len(self.WetSpellArray[file_idx]):
                        self.WetSpellArray[file_idx][spell_idx] = wet_count
                    
                    # Reset counter and state
                    is_wet = False
                    wet_count = 0
                    
                # Case 3: Start of wet spell (wet day follows dry or missing day)
                elif not is_wet and self.periodArray[file_idx][i] > self.thresh:
                    is_wet = True
                    wet_count = 1
            
            # If we're still in a wet spell at the end of the period, record it
            if wet_count > 0:
                self.TotalWetSpells[file_idx] += 1
                spell_idx = self.TotalWetSpells[file_idx] - 1
                if spell_idx < len(self.WetSpellArray[file_idx]):
                    self.WetSpellArray[file_idx][spell_idx] = wet_count
            
        except Exception as e:
            print(f"Error in CreateWetSpellArray: {str(e)}")
            traceback.print_exc()  # Print full traceback for debugging
            self.Mini_Reset()


    def CreateDrySpellArray(self, file_no, size_of):
        try:
            # Initialize counters
            dry_count = 0                           # Counter for consecutive dry days
            self.TotalDrySpells[file_no] = 0        # Reset count of dry spells
            
            # Convert file_no to 0-based indexing if it's coming from 1-based code
            file_idx = file_no
            
            # Initialize spell array - clear any existing values
            self.DrySpellArray[file_idx] = [0] * len(self.DrySpellArray[file_idx])
            
            # Skip processing if no data
            if size_of <= 0:
                return
            
            # Determine initial state - are we starting in a dry spell?
            if (self.periodArray[file_idx][0] == self.global_missing_code or 
                self.periodArray[file_idx][0] > self.thresh):
                is_dry = False                      # Start as not in a dry spell
            else:
                is_dry = True                       # Start in a dry spell
                dry_count = 1
            
            # Process each day
            for i in range(1, size_of):
                # Make sure we don't exceed array bounds
                if i >= len(self.periodArray[file_idx]):
                    break
                    
                # Case 1: Continuing dry spell (dry day follows dry day)
                if is_dry and self.periodArray[file_idx][i] <= self.thresh:
                    dry_count += 1
                    
                # Case 2: End of dry spell (wet or missing day follows dry day)
                elif is_dry and (self.periodArray[file_idx][i] > self.thresh or 
                                self.periodArray[file_idx][i] == self.global_missing_code):
                    # Record the completed dry spell
                    self.TotalDrySpells[file_idx] += 1
                    spell_idx = self.TotalDrySpells[file_idx] - 1
                    if spell_idx < len(self.DrySpellArray[file_idx]):
                        self.DrySpellArray[file_idx][spell_idx] = dry_count
                    
                    # Reset counter and state
                    is_dry = False
                    dry_count = 0
                    
                # Case 3: Start of dry spell (dry day follows wet or missing day)
                elif not is_dry and self.periodArray[file_idx][i] <= self.thresh:
                    is_dry = True
                    dry_count = 1
            
            # If we're still in a dry spell at the end of the period, record it
            if dry_count > 0:
                self.TotalDrySpells[file_idx] += 1
                spell_idx = self.TotalDrySpells[file_idx] - 1
                if spell_idx < len(self.DrySpellArray[file_idx]):
                    self.DrySpellArray[file_idx][spell_idx] = dry_count
            
        except Exception as e:
            print(f"Error in CreateDrySpellArray: {str(e)}")
            traceback.print_exc()  # Print full traceback for debugging
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


    def FindDryDayPersistence(self, file_no, size_of):
        try:
            # Create the dry spell array first
            self.CreateDrySpellArray(file_no, size_of)
            
            dry_day_persistence = 0
            dry_day_count = 0        # counts all dry days
            consec_dry_count = 0     # counts only consecutive dry days (in spells > 1 day)
            
            # Calculate dry day persistence if there are any dry spells
            if self.TotalDrySpells[file_no] > 0:
                for i in range(self.TotalDrySpells[file_no]):
                    spell_length = self.DrySpellArray[file_no][i]
                    dry_day_count += spell_length
                    
                    # Only count consecutive days if spell length > 1
                    if spell_length > 1:
                        consec_dry_count += spell_length
                
                # Calculate persistence if there were any dry days
                if dry_day_count > 0:
                    dry_day_persistence = consec_dry_count / dry_day_count
            
            return dry_day_persistence
    
        except Exception as e:
            print(f"Error in FindDDPersistence: {str(e)}")
            traceback.print_exc()  # Print full traceback for debugging
            self.Mini_Reset()
            return 0

    def FindWetDayPersistence(self, file_no, size_of):
        try:
            # Create the wet spell array first
            self.CreateWetSpellArray(file_no, size_of)
            
            wet_day_persistence = 0
            wet_day_count = 0        # counts all wet days
            consec_wet_count = 0     # counts only consecutive wet days (in spells > 1 day)
            
            # Calculate wet day persistence if there are any wet spells
            if self.TotalWetSpells[file_no] > 0:
                for i in range(self.TotalWetSpells[file_no]):
                    spell_length = self.WetSpellArray[file_no][i]
                    wet_day_count += spell_length
                    
                    # Only count consecutive days if spell length > 1
                    if spell_length > 1:
                        consec_wet_count += spell_length
                
                # Calculate persistence if there were any wet days
                if wet_day_count > 0:
                    wet_day_persistence = consec_wet_count / wet_day_count
            
            return wet_day_persistence
        
        except Exception as e:
            print(f"Error in FindWDPersistence: {str(e)}")
            traceback.print_exc()  # Print full traceback for debugging
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
                    header = ["Date"]
                    for i in range(self.total_time_series_files):
                        header.append(self.AllFilesList[i])
                    writer.writerow(header)
                    
                    # Write data for each month
                    for j in range(self.spi_value, self.TotalMonths + 1):
                        row = []
                        # Add date label (month and year)
                        year_code = int(self.RunningMonths[0][j-1][1])
                        month_code = int(self.RunningMonths[0][j-1][2])
                        month_name = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                                    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][month_code]
                        year_val = year_code + int(datetime.strptime(self.FSDate, '%d/%m/%Y').year) - 1
                        row.append(f"{month_name} {year_val}")
                        
                        # Add SPI values for each file
                        for i in range(self.total_time_series_files):
                            if i < len(self.RunningMonths) and j-1 < len(self.RunningMonths[i]) and self.RunningMonths[i][j-1][4] != self.global_missing_code:
                                row.append(f"{self.RunningMonths[i][j-1][4]:.3f}")
                            else:
                                row.append("")
                        writer.writerow(row)
                        
                elif self.statCheckboxes[14].isChecked():  # % precip > annual percentile
                    # Write header row
                    header = ["Year"]
                    for i in range(self.total_time_series_files):
                        header.append(self.AllFilesList[i])
                        header.append("%Precip>Annual Percentile")
                    writer.writerow(header)
                    
                    # Write data for each year
                    start_year = int(datetime.strptime(self.FSDate, "%d/%m/%Y").year)
                    for j in range(1, self.TimeSeriesLength + 1):
                        row = [str(start_year + j - 1)]  # Year
                        for i in range(1, self.total_time_series_files + 1):
                            file_idx = i - 1
                            year_idx = j
                            if file_idx < len(self.FractionResult) and year_idx < len(self.FractionResult[file_idx]) and self.FractionResult[file_idx][year_idx] != self.global_missing_code:
                                row.append(self.AllFilesList[file_idx])
                                row.append(f"{self.FractionResult[file_idx][year_idx]:.2f}")
                            else:
                                row.append(self.AllFilesList[file_idx])
                                row.append("")
                        writer.writerow(row)
                
                elif self.statCheckboxes[22].isChecked():  # pfl90 statistic
                    # Write header row
                    header = ["Year"]
                    for i in range(self.total_time_series_files):
                        header.append(self.AllFilesList[i])
                        header.append("%Total Precip from events>long-term percentile")
                    writer.writerow(header)
                    
                    # Write data for each year
                    start_year = int(datetime.strptime(self.FSDate, "%d/%m/%Y").year)
                    for j in range(1, self.TimeSeriesLength + 1):
                        row = [str(start_year + j - 1)]  # Year
                        for i in range(1, self.total_time_series_files + 1):
                            file_idx = i - 1
                            year_idx = j
                            if file_idx < len(self.LongTermResults) and year_idx < len(self.LongTermResults[file_idx]) and self.LongTermResults[file_idx][year_idx] != self.global_missing_code:
                                row.append(self.AllFilesList[file_idx])
                                row.append(f"{self.LongTermResults[file_idx][year_idx]:.2f}")
                            else:
                                row.append(self.AllFilesList[file_idx])
                                row.append("")
                        writer.writerow(row)
                
                elif self.statCheckboxes[23].isChecked():  # pnl90 statistic
                    # Write header row
                    header = ["Year"]
                    for i in range(self.total_time_series_files):
                        header.append(self.AllFilesList[i])
                        header.append("No events>long-term percentile")
                    writer.writerow(header)
                    
                    # Write data for each year
                    start_year = int(datetime.strptime(self.FSDate, "%d/%m/%Y").year)
                    for j in range(1, self.TimeSeriesLength + 1):
                        row = [str(start_year + j - 1)]  # Year
                        for i in range(1, self.total_time_series_files + 1):
                            file_idx = i - 1
                            year_idx = j
                            if file_idx < len(self.LongTermResults) and year_idx < len(self.LongTermResults[file_idx]) and self.LongTermResults[file_idx][year_idx] != self.global_missing_code:
                                row.append(self.AllFilesList[file_idx])
                                row.append(f"{int(self.LongTermResults[file_idx][year_idx])}")
                            else:
                                row.append(self.AllFilesList[file_idx])
                                row.append("")
                        writer.writerow(row)
                
                elif self.statCheckboxes[6].isChecked():  # Winter/summer ratio
                    # Write header row
                    header = ["Year"]
                    for i in range(self.total_time_series_files):
                        header.append(self.AllFilesList[i])
                        header.append("Winter/Summer Ratio")
                    writer.writerow(header)
                    
                    # Write data for each year
                    start_year = int(datetime.strptime(self.FSDate, "%d/%m/%Y").year)
                    for j in range(1, self.TimeSeriesLength + 1):
                        row = [str(start_year + j - 1)]  # Year
                        for i in range(1, self.total_time_series_files + 1):
                            # Check for division by zero or missing values
                            winter_val = self.summaryArray[i][j][13][1]  # Winter value (season 1 + 12 = 13)
                            summer_val = self.summaryArray[i][j][15][1]  # Summer value (season 3 + 12 = 15)
                            
                            if (summer_val == 0 or 
                                summer_val == self.global_missing_code or 
                                winter_val == self.global_missing_code):
                                row.append(self.AllFilesList[i-1])
                                row.append("")
                            else:
                                ratio = winter_val / summer_val
                                row.append(self.AllFilesList[i-1])
                                row.append(f"{ratio:.3f}")
                        writer.writerow(row)
                
                else:  # Handle other statistics
                    # Define season names
                    season_names = ["", "Winter", "Spring", "Summer", "Autumn"]
                    
                    # Write header row
                    header = ["Year", "Period"]
                    
                    # Create headers for all statistics
                    stat_headers = ["Sum", "Max", "Count", "Percentile", "Mean", "PDS", "POT", 
                                "Nth Largest", "Largest N day total", "Max dry spell", 
                                "Max wet spell", "Mean dry spell", "Mean wet spell", 
                                "Median dry spell", "Median wet spell", "SD dry spell", 
                                "SD wet spell", "Dry day persistence", "Wet day persistence", 
                                "Spell length correlation"]
                    
                    # Add file names and stat headers
                    for i in range(self.total_time_series_files):
                        for stat in stat_headers:
                            header.append(f"{self.AllFilesList[i]} {stat}")
                    
                    writer.writerow(header)
                    
                    # Write data based on selected period
                    start_year = int(datetime.strptime(self.FSDate, "%d/%m/%Y").year)
                    
                    for j in range(1, self.TimeSeriesLength + 1):
                        year_val = start_year + j - 1
                        
                        if self.DatesCombo.currentIndex() >= 1 and self.DatesCombo.currentIndex() <= 12:  # Month selected
                            month_idx = self.DatesCombo.currentIndex()
                            month_name = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                                        'July', 'August', 'September', 'October', 'November', 'December'][month_idx]
                            row = [str(year_val), month_name]
                            
                            # Add all statistics for each file
                            for i in range(1, self.total_time_series_files + 1):
                                for stat_idx in range(1, 21):  # 20 different statistics
                                    if stat_idx == 14:  # Skip index 14 (not used in summary array)
                                        continue
                                    
                                    value = self.summaryArray[i][j][month_idx][stat_idx]
                                    if value != self.global_missing_code:
                                        row.append(f"{value:.3f}")
                                    else:
                                        row.append("")
                            
                            writer.writerow(row)
                        
                        elif self.DatesCombo.currentIndex() >= 13 and self.DatesCombo.currentIndex() <= 16:  # Season selected
                            season_idx = self.DatesCombo.currentIndex() - 12
                            season_name = season_names[season_idx]
                            row = [str(year_val), season_name]
                            
                            # Add all statistics for each file
                            for i in range(1, self.total_time_series_files + 1):
                                for stat_idx in range(1, 21):  # 20 different statistics
                                    if stat_idx == 14:  # Skip index 14 (not used in summary array)
                                        continue
                                    
                                    value = self.summaryArray[i][j][season_idx+12][stat_idx]
                                    if value != self.global_missing_code:
                                        row.append(f"{value:.3f}")
                                    else:
                                        row.append("")
                            
                            writer.writerow(row)
                        
                        elif self.DatesCombo.currentIndex() == 17:  # Annual selected
                            row = [str(year_val), "Annual"]
                            
                            # Add all statistics for each file
                            for i in range(1, self.total_time_series_files + 1):
                                for stat_idx in range(1, 21):  # 20 different statistics
                                    if stat_idx == 14:  # Skip index 14 (not used in summary array)
                                        continue
                                    
                                    value = self.summaryArray[i][j][17][stat_idx]  # 17th index is Annual
                                    if value != self.global_missing_code:
                                        row.append(f"{value:.3f}")
                                    else:
                                        row.append("")
                            
                            writer.writerow(row)
                        
                        elif self.DatesCombo.currentIndex() == 18:  # Water year selected
                            row = [str(year_val), "Water Year"]
                            
                            # Add all statistics for each file
                            for i in range(1, self.total_time_series_files + 1):
                                for stat_idx in range(1, 21):  # 20 different statistics
                                    if stat_idx == 14:  # Skip index 14 (not used in summary array)
                                        continue
                                    
                                    value = self.summaryArray[i][j][18][stat_idx]  # 18th index is Water Year
                                    if value != self.global_missing_code:
                                        row.append(f"{value:.3f}")
                                    else:
                                        row.append("")
                            
                            writer.writerow(row)
                
                print(f"Results saved to {self.save_root}")
        
        except Exception as e:
            print(f"Error in SaveResults: {str(e)}")
            traceback.print_exc()  # Print full traceback for debugging
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
            
            # Clear file selections in North and South lists
            self.northFileList.clear()
            self.southFileList.clear()
            
            # Reset selection count labels
            self.northCountLabel.setText("Selected: 0")
            self.southCountLabel.setText("Selected: 0")
            
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
            
            # Reset dropdowns
            self.DatesCombo.setCurrentIndex(0)
            
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
            
            # Clear any data arrays/lists as needed
            self.AllFilesList = []
            
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