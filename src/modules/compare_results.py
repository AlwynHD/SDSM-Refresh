from PyQt5.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
    QPushButton,
    QSizePolicy,
    QFrame,
    QLabel,
    QFileDialog,
    QScrollArea,
    QDateEdit,
    QCheckBox,
    QButtonGroup,
    QRadioButton,
    QLineEdit,
    QGroupBox,
    QMessageBox,
    QApplication,
    QComboBox,
)
from PyQt5.QtCore import Qt, QSize, QDate

# Define the name of the module for display in the content area
moduleName = "Compare Results"


def displayBox(messageType, messageInfo, messageTitle, isError=False):
    messageBox = QMessageBox()
    if isError:
        messageBox.setIcon(QMessageBox.Critical)
    else:
        messageBox.setIcon(QMessageBox.Information)
    messageBox.setText(messageType)
    messageBox.setInformativeText(messageInfo)
    messageBox.setWindowTitle(messageTitle)
    messageBox.exec_()


class borderedQGroupBox(QGroupBox):
    def __init__(self, args):
        super().__init__(args)


class comparedFileBox(borderedQGroupBox):
    def __init__(self, args):
        super().__init__(args)

        self.pathSelected = ""
        self.statSelected = ""

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 25, 0, 25)
        layout.setSpacing(25)
        self.setLayout(layout)

        fileFrame = QFrame()
        fileFrame.setFrameStyle(QFrame.NoFrame)
        fileLayout = QVBoxLayout()
        fileFrame.setLayout(fileLayout)

        fileButton = QPushButton("Select File")
        fileButton.setContentsMargins(25, 25, 25, 25)
        fileButton.setMaximumWidth(200)
        fileButton.clicked.connect(self.selectFile)
        fileLayout.addWidget(fileButton)

        self.fileLabel = QLabel("File: Not Selected")
        self.fileLabel.setContentsMargins(25, 25, 25, 25)
        fileLayout.addWidget(self.fileLabel)

        fileLayout.setAlignment(Qt.AlignHCenter)
        layout.addWidget(fileFrame)

        spacerFrame = QFrame()
        spacerFrame.setFrameShape(QFrame.HLine | QFrame.Sunken)
        layout.addWidget(spacerFrame)

        statsLabel = QLabel("Select Statistic")
        statsLabel.setContentsMargins(25, 0, 25, 0)
        layout.addWidget(statsLabel)

        selectStatsFrame = QFrame()
        selectStatsFrame.setFrameStyle(QFrame.NoFrame)
        selectStatsLayout = QVBoxLayout()
        selectStatsLayout.setContentsMargins(25, 0, 25, 0)  # Pad 10 pixels each way
        selectStatsLayout.setSpacing(10)  # No spacing between elements
        selectStatsFrame.setLayout(selectStatsLayout)

        statsScrollArea = QScrollArea()
        statsScrollArea.setWidgetResizable(True)
        statsScrollFrame = QFrame()

        statsScrollFrame.setFrameStyle(QFrame.NoFrame)  # No border around the frame

        # predictorsScrollFrame.setBaseSize(200,300)
        # predictorsScrollFrame.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Fixed)

        self.statsScrollLayout = QVBoxLayout()
        self.statsScrollLayout.setSpacing(0)  # No spacing between elements
        self.statsScrollLayout.setAlignment(Qt.AlignHCenter)
        statsScrollFrame.setLayout(
            self.statsScrollLayout
        )  # Apply the layout to the frame

        selectStatsLayout.addWidget(statsScrollArea)

        # Get all predictors and populate scroll frame

        statsScrollArea.setWidget(statsScrollFrame)

        layout.addWidget(selectStatsFrame)

    def selectFile(self):
        fileName = QFileDialog.getOpenFileName(
            self, "Select statistic file", "", "All Files (*.*)"
        )
        if fileName[0] != "":
            self.pathSelected = fileName[0]
            self.fileLabel.setText(
                "File: " + self.pathSelected.split("/")[-1]
            )  # Only show the name of the file, not the whole path
            self.writeStats()
        else:
            self.pathSelected = ""
            self.fileLabel.setText("File: Not Selected")
            self.writeStats()

    def writeStats(self):
        from src.lib.CompareResults import readSumStatsFile

        # Remove all stats
        while self.statsScrollLayout.count():
            item = self.statsScrollLayout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)

        # Add in new stats
        if self.pathSelected == "":
            return None
        stats, data = readSumStatsFile(self.pathSelected)
        self.statButtons = []
        for stat in stats:
            statScrollLabelButton = QPushButton(stat)
            statScrollLabelButton.setFlat = True
            statScrollLabelButton.clicked.connect(self.statLabelClicked)
            statScrollLabelButton.setBaseSize(200, 20)
            statScrollLabelButton.setStyleSheet(
                "color: black; background-color: #F0F0F0"
            )
            statScrollLabelButton.setSizePolicy(
                QSizePolicy.Expanding, QSizePolicy.Expanding
            )
            self.statsScrollLayout.addWidget(statScrollLabelButton)
            self.statButtons.append(statScrollLabelButton)

    def statLabelClicked(self):
        button = self.sender()
        for statButton in self.statButtons:
            statButton.setStyleSheet("color: black; background-color: #F0F0F0")
        button.setStyleSheet("color: white; background-color: blue")
        if self.statSelected == button.text():
            button.setStyleSheet("color: black; background-color: #F0F0F0")
            self.statSelected = ""
            return None
        self.statSelected = button.text()


class ContentWidget(QWidget):
    """
    A widget to display the Screen Variables screen (UI/UX).
    Includes a buttonBar at the top and a contentArea for displaying details.
    """

    def __init__(self):
        """
        Initialize the Screen Variables screen UI/UX, setting up the layout, buttonBar, and contentArea.
        """
        super().__init__()

        self.predictorPath = "predictor files"

        self.predictandSelected = ""
        self.predictorsSelected = []

        # Main layout for the entire widget
        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the layout
        mainLayout.setSpacing(0)  # No spacing between elements
        self.setLayout(mainLayout)  # Apply the main layout to the widget

        self.setStyleSheet(
            """
                            
                            QFrame{
                                background-color: #F0F0F0;
                                font-size: 18px;}
                           
                            QRadioButton
                           {
                                font-size: 18px;
                           }
                           QDateEdit
                           {
                                font-size: 18px;
                           }
                           QLineEdit
                           {
                                font-size: 18px;
                           }
                           QCheckBox
                           {
                                font-size: 18px;
                           }
                            borderedQGroupBox{
                                background-color: #F0F0F0;
                                border : 1px solid #CECECE;
                                border-top-left-radius : 20px;
                                border-top-right-radius : 20px;
                                border-bottom-left-radius : 20px;
                                border-bottom-right-radius : 20px;}"""
        )

        # --- Content Area ---

        """


        """
        contentAreaFrame = QFrame()
        contentAreaFrame.setFrameStyle(QFrame.NoFrame)  # No border around the frame
        contentAreaFrame.setBaseSize(600, 100)
        contentAreaFrame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Layout for the contentArea frame
        contentAreaLayout = QHBoxLayout()
        contentAreaLayout.setContentsMargins(
            25, 25, 25, 25
        )  # Remove padding from the layout
        contentAreaLayout.setSpacing(10)  # No spacing between elements
        contentAreaFrame.setLayout(contentAreaLayout)  # Apply the layout to the frame

        mainLayout.addWidget(contentAreaFrame)

        # Frame that holds the selectPredictand frame and the selectDate frame

        self.fileOneFrame = comparedFileBox("Input File One")

        contentAreaLayout.addWidget(self.fileOneFrame)

        self.fileTwoFrame = comparedFileBox("Input File Two")
        contentAreaLayout.addWidget(self.fileTwoFrame)

        buttonFrame = QFrame()
        buttonFrame.setBaseSize(600, 60)
        buttonFrame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        buttonLayout = QHBoxLayout()
        buttonLayout.setContentsMargins(25, 25, 25, 25)
        buttonLayout.setSpacing(10)

        buttonFrame.setLayout(buttonLayout)

        mainLayout.addWidget(buttonFrame)

        # ------------ ACTUAL CONTENT ------------
        # Label to display the name of the module (Screen Variables)
        """moduleLabel = QLabel(moduleName, self)
        moduleLabel.setStyleSheet("font-size: 24px; color: black;")  # Style the label text
        titleLayout.addWidget(moduleLabel)  # Add the label to the contentArea layout """

        # Predictand file selector button

        barGraphButton = QPushButton("Bar Chart")
        barGraphButton.clicked.connect(self.doBarChart)
        barGraphButton.setStyleSheet(
            "background-color: #4CAF50; color: white; font-weight: bold;"
        )

        buttonLayout.addWidget(barGraphButton)

        lineGraphButton = QPushButton("Line Chart")
        lineGraphButton.clicked.connect(self.doLineChart)
        lineGraphButton.setStyleSheet(
            "background-color: #1FC7F5; color: white; font-weight: bold;"
        )

        buttonLayout.addWidget(lineGraphButton)

        resetButton = QPushButton("🔄 Reset")
        resetButton.setStyleSheet(
            "background-color: #F44336; color: white; font-weight: bold;"
        )
        resetButton.clicked.connect(self.resetAll)
        buttonLayout.addWidget(resetButton)

        # Add a spacer to ensure content is properly spaced

        # titleLayout.addStretch()
        # contentAreaLayout.addStretch()

    def resetAll(self):
        self.fileOneFrame.pathSelected = ""
        self.fileOneFrame.statSelected = ""
        self.fileOneFrame.fileLabel.setText("File: Not Selected")
        self.fileOneFrame.writeStats()

        self.fileTwoFrame.pathSelected = ""
        self.fileTwoFrame.statSelected = ""
        self.fileTwoFrame.fileLabel.setText("File: Not Selected")
        self.fileTwoFrame.writeStats()

    def doBarChart(self):
        from src.lib.CompareResults import readSumStatsFile, plotMultiple

        if self.fileOneFrame.pathSelected == "" and self.fileTwoFrame.pathSelected == "":
            return displayBox(
                "File Error",
                "You must select at least one statistic file.",
                "Files Not Selected",
                isError=True,
            )
        
        if self.fileOneFrame.pathSelected != "" and self.fileOneFrame.statSelected == "":
            return displayBox(
                "Stats Error",
                "Please select a statistic for file one.",
                "Statistics Not Selected",
                isError=True,
            )
        
        if self.fileTwoFrame.pathSelected != "" and self.fileTwoFrame.statSelected == "":
            return displayBox(
                "Stats Error",
                "Please select a statistic for file two.",
                "Statistics Not Selected",
                isError=True,
            )
        
        fields = []
        stats = []
        statIndices = []

        if self.fileOneFrame.pathSelected != "":
            fieldsOne, statsOne = readSumStatsFile(self.fileOneFrame.pathSelected)
            statIndexOne = fieldsOne.index(self.fileOneFrame.statSelected)

            fields.append(fieldsOne)
            stats.append(statsOne)
            statIndices.append(statIndexOne)

        if self.fileTwoFrame.pathSelected != "":
            fieldsTwo, statsTwo = readSumStatsFile(self.fileTwoFrame.pathSelected)
            statIndexTwo = fieldsTwo.index(self.fileTwoFrame.statSelected)

            fields.append(fieldsTwo)
            stats.append(statsTwo)
            statIndices.append(statIndexTwo)
        
        plotMultiple(
            fields,
            stats,
            statIndices,
            False,
        )

    def doLineChart(self):
        from src.lib.CompareResults import readSumStatsFile, plotMultiple

        if self.fileOneFrame.pathSelected == "" and self.fileTwoFrame.pathSelected == "":
            return displayBox(
                "File Error",
                "You must select at least one statistic file.",
                "Files Not Selected",
                isError=True,
            )
        
        if self.fileOneFrame.pathSelected != "" and self.fileOneFrame.statSelected == "":
            return displayBox(
                "Stats Error",
                "Please select a statistic for file one.",
                "Statistics Not Selected",
                isError=True,
            )
        
        if self.fileTwoFrame.pathSelected != "" and self.fileTwoFrame.statSelected == "":
            return displayBox(
                "Stats Error",
                "Please select a statistic for file two.",
                "Statistics Not Selected",
                isError=True,
            )
        
        fields = []
        stats = []
        statIndices = []

        if self.fileOneFrame.pathSelected != "":
            fieldsOne, statsOne = readSumStatsFile(self.fileOneFrame.pathSelected)
            statIndexOne = fieldsOne.index(self.fileOneFrame.statSelected)

            fields.append(fieldsOne)
            stats.append(statsOne)
            statIndices.append(statIndexOne)

        if self.fileTwoFrame.pathSelected != "":
            fieldsTwo, statsTwo = readSumStatsFile(self.fileTwoFrame.pathSelected)
            statIndexTwo = fieldsTwo.index(self.fileTwoFrame.statSelected)

            fields.append(fieldsTwo)
            stats.append(statsTwo)
            statIndices.append(statIndexTwo)
        
        plotMultiple(
            fields,
            stats,
            statIndices,
            True,
        )

    def QDateEditToDateTime(self, dateEdit):
        rawStartDate = dateEdit.date()
        dateTime = rawStartDate.toPyDate()
        return dateTime
