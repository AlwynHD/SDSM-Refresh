from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame, QComboBox, 
    QLineEdit, QListWidget, QFileDialog, QCheckBox, QRadioButton, QButtonGroup, 
    QGridLayout, QGroupBox, QSizePolicy
)
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import os
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

        # --- Main Layout ---
        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(15, 15, 15, 15)  # Reduced margins to save space
        mainLayout.setSpacing(12)  # Adjusted spacing for better layout flow
        self.setLayout(mainLayout)

        # --- Time Period Selection (Smaller) ---
        timePeriodGroup = QGroupBox("Time Period")
        timePeriodLayout = QHBoxLayout()
        self.timePeriodDropdown = QComboBox()
        self.timePeriodDropdown.addItems(["Raw Data", "Processed Data"])
        self.timePeriodDropdown.setFixedHeight(25)  # Reduced height for better fit
        timePeriodLayout.addWidget(self.timePeriodDropdown, alignment=Qt.AlignCenter)
        timePeriodGroup.setLayout(timePeriodLayout)
        mainLayout.addWidget(timePeriodGroup, alignment=Qt.AlignCenter)

        # --- File Selection Section (Side-by-Side) ---
        fileSelectionLayout = QHBoxLayout()

        # Left File Selection (Reduced height)
        self.fileSelectionLeft = self.createFileSelectionGroup("File Selection")
        fileSelectionLayout.addWidget(self.fileSelectionLeft)

        # Right File Selection
        self.fileSelectionRight = self.createFileSelectionGroup("File Selection")
        fileSelectionLayout.addWidget(self.fileSelectionRight)

        mainLayout.addLayout(fileSelectionLayout)

        # --- Bottom Section (Data Range + Save Results) ---
        bottomLayout = QHBoxLayout()

        # Data Range Box (Smaller Height)
        dataGroup = QGroupBox("Data")
        dataLayout = QGridLayout()

        self.startDateInput = QLineEdit()
        self.startDateInput.setPlaceholderText("01/01/1948")
        self.startDateInput.setFixedHeight(25)

        self.endDateInput = QLineEdit()
        self.endDateInput.setPlaceholderText("31/12/2017")
        self.endDateInput.setFixedHeight(25)

        dataLayout.addWidget(QLabel("Start:"), 0, 0)
        dataLayout.addWidget(self.startDateInput, 0, 1)
        dataLayout.addWidget(QLabel("End:"), 1, 0)
        dataLayout.addWidget(self.endDateInput, 1, 1)

        dataGroup.setLayout(dataLayout)
        dataGroup.setFixedHeight(80)  # Reduced height to fit better
        bottomLayout.addWidget(dataGroup)

        # Save Results Box (Aligned with Data Section)
        saveGroup = QGroupBox("Save Results To")
        saveLayout = QVBoxLayout()

        saveButtonsLayout = QHBoxLayout()
        self.selectSaveButton = QPushButton("📂 Select")
        self.selectSaveButton.clicked.connect(self.selectSaveFile)
        self.selectSaveButton.setFixedHeight(30)

        self.clearSaveButton = QPushButton("❌ Clear")
        self.clearSaveButton.clicked.connect(self.clearSaveFile)
        self.clearSaveButton.setFixedHeight(30)

        saveButtonsLayout.addWidget(self.selectSaveButton)
        saveButtonsLayout.addWidget(self.clearSaveButton)

        self.saveFileLabel = QLabel("File: *.CSV")
        self.saveFileLabel.setStyleSheet("border: 1px solid gray; padding: 5px;")

        saveLayout.addLayout(saveButtonsLayout)
        saveLayout.addWidget(self.saveFileLabel)

        saveGroup.setLayout(saveLayout)
        bottomLayout.addWidget(saveGroup)

        mainLayout.addLayout(bottomLayout)

        # --- Statistics Selection (Better Organized) ---
        statsGroup = QGroupBox("Select Statistics")
        statsLayout = QGridLayout()

        self.statsOptions = [
            "Sum", "Mean", "Maximum", "Winter/Summer ratio",
            "Maximum dry spell", "Maximum wet spell",
            "Dry day persistence", "Wet day persistence",
            "Partial Duration Series", "Percentile",
            "Standard Precipitation Index", "Peaks Over Threshold"
        ]

        self.statCheckboxes = []
        for i, stat in enumerate(self.statsOptions):
            checkbox = QCheckBox(stat)
            self.statCheckboxes.append(checkbox)
            statsLayout.addWidget(checkbox, i // 2, i % 2)  # Two columns

        # --- Spell Duration Selection (Smaller to Fit) ---
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
            self.spellGroup.addButton(radio)
            spellLayout.addWidget(radio)

        spellGroup.setLayout(spellLayout)
        spellGroup.setFixedHeight(150)  # Reduced height to fit better
        statsLayout.addWidget(spellGroup, 0, 2, len(self.spellOptions) // 2, 1)

        # --- Threshold Inputs (Now Fits Properly) ---
        thresholdLayout = QGridLayout()

        self.percentileInput = QLineEdit()
        self.percentileInput.setPlaceholderText("90")
        self.percentileInput.setFixedHeight(25)

        self.precipLongTermInput = QLineEdit()
        self.precipLongTermInput.setPlaceholderText("90")
        self.precipLongTermInput.setFixedHeight(25)

        self.numEventsInput = QLineEdit()
        self.numEventsInput.setPlaceholderText("90")
        self.numEventsInput.setFixedHeight(25)

        thresholdLayout.addWidget(QLabel("%Prec > annual %ile:"), 0, 0)
        thresholdLayout.addWidget(self.percentileInput, 0, 1)

        thresholdLayout.addWidget(QLabel("% All precip from events > long-term %ile:"), 1, 0)
        thresholdLayout.addWidget(self.precipLongTermInput, 1, 1)

        thresholdLayout.addWidget(QLabel("No. of events > long-term %ile:"), 2, 0)
        thresholdLayout.addWidget(self.numEventsInput, 2, 1)

        statsLayout.addLayout(thresholdLayout, 6, 0, 1, 2)
        statsGroup.setLayout(statsLayout)
        mainLayout.addWidget(statsGroup)

        # --- Action Buttons (Smaller & Aligned) ---
        buttonLayout = QHBoxLayout()
        generateButton = QPushButton("🚀 Generate")
        generateButton.setStyleSheet("background-color: #4CAF50; color: white; font-size: 14px; padding: 8px;")

        resetButton = QPushButton("🔄 Reset")
        resetButton.setStyleSheet("background-color: #F44336; color: white; font-size: 14px; padding: 8px;")

        buttonLayout.addWidget(generateButton)
        buttonLayout.addWidget(resetButton)
        mainLayout.addLayout(buttonLayout)

        helpButton = QPushButton("Help")
        helpButton.clicked.connect(lambda: self.Help_Needed(1))
        mainLayout.addWidget(helpButton)

    def createFileSelectionGroup(self, title):
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

    def selectSaveFile(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Save To File", filter="CSV Files (*.csv)")
        if file_name:
            self.saveFileLabel.setText(f"File: {file_name}")

    def clearSaveFile(self):
        self.saveFileLabel.setText("File: *.CSV")



    # Main functions

    def PlotData():
        pass

    def RawData():
        pass

    def GenerateData():
        pass   

    def GenerateSPI():
        pass

    def GeneratePrecipAnnualMax():
        pass

    def LongTermStats():
        pass
    
    #Support Functions

    def FindPrecipAbouveAnnPercentile():
        pass

    def FinsihedCurrentPeriod():
        pass

    def GetWaterYear():
        pass

    def PercentilePeriodArray():
        pass

    def FindNthLargest():
        pass

    def FindLargestNDayTotal():
        pass

    def FindMaxDrySpell():
        pass

    def FindMaxWetSpell():
        pass

    def FindMeanDrySpell():
        pass

    def FindMeanWetSpell():
        pass

    def FindMedianDrySpell():
        pass

    def FindMedianWetSpell():
        pass

    def FindSDDrySpell():
        pass

    def FindSDWetSpell():
        pass

    def FindDDPersistence():
        pass   

    def findWDPersistence():
        pass

    def FindSpellLengthCorrelation():
        pass

    #Utility Functions

    def CreateDrySpellArray():
        pass

    def CreateWetSpellArray():
        pass

    def IncreaseDate():
        pass

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

    def SaveResults(self):
        

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
        """
        Performs a minimal reset of UI elements and closes any open files.
        """
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
         """
        Resets all UI elements and variables to their default values.
        Called when form loads and when reset is triggered.
        """
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

    def DumpForm():
        pass