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
    QTabWidget,
    QTextEdit,
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QPalette, QColor, QIcon
from os import listdir

# Define the name of the module for display in the content area
moduleName = "Calibrate Model"


class borderedQGroupBox(QGroupBox):
    def __init__(self, args):
        super().__init__(args)


class ContentWidget(QWidget):
    """
    A widget to display the Calibrate Model screen (UI/UX).
    Includes a buttonBar at the top and a contentArea for displaying details.
    """

    def __init__(self):
        """
        Initialize the Calibrate Model screen UI/UX, setting up the layout, buttonBar, and contentArea.
        """
        super().__init__()

        self.predictorPath = "predictor files"
        self.predictandSelected = ""
        self.predictorsSelected = []
        self.outputSelected = ""

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
        # Frame for the contentArea
        """
        titleFrame = QFrame()
        titleFrame.setFrameShape(QFrame.NoFrame)  # No border around the frame

        # Layout for the contentArea frame
        titleLayout = QVBoxLayout()
        titleLayout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the layout
        titleLayout.setSpacing(0)  # No spacing between elements
        titleFrame.setLayout(titleLayout)  # Apply the layout to the frame

        # Set a light gray background color for the contentArea
        titleFrame.setStyleSheet("background-color: #F0F0F0;")

        # Add the contentArea frame to the main layout
        mainLayout.addWidget(titleFrame)
        """
        # --- Center Label (Placeholder) ---
        # Label to display the name of the module (Calibrate Model)
        """moduleLabel = QLabel(moduleName, self)
        moduleLabel.setStyleSheet("font-size: 24px; color: black;")  # Style the label text
        titleLayout.addWidget(moduleLabel)  # Add the label to the contentArea layout"""

        contentAreaFrame = QFrame()
        contentAreaFrame.setFrameStyle(QFrame.NoFrame)  # No border around the frame
        contentAreaFrame.setBaseSize(600, 100)
        contentAreaFrame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        # Layout for the contentArea frame
        contentAreaLayout = QHBoxLayout()
        contentAreaLayout.setContentsMargins(
            25, 25, 25, 25
        )  # Remove padding from the layout
        contentAreaLayout.setSpacing(10)  # No spacing between elements
        contentAreaFrame.setLayout(contentAreaLayout)  # Apply the layout to the frame

        mainLayout.addWidget(contentAreaFrame)

        # Frame that holds the selectPredictand frame and the selectDate frame
        filesDateFrame = QFrame()
        filesDateFrame.setFrameStyle(QFrame.NoFrame)  # No border around the frame
        filesDateFrame.setBaseSize(200, 500)
        filesDateFrame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        filesDateLayout = QVBoxLayout()
        filesDateLayout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the layout
        filesDateLayout.setSpacing(10)  # No spacing between elements
        filesDateFrame.setLayout(filesDateLayout)  # Apply the layout to the frame

        contentAreaLayout.addWidget(filesDateFrame)

        # Create selectPredictandFile frame
        selectPredictandFileFrame = borderedQGroupBox("Select Predictand")
        selectPredictandFileFrame.setBaseSize(200, 200)

        # Layout for selectPredictandFile frame
        selectPredictandFileLayout = QVBoxLayout()
        selectPredictandFileLayout.setContentsMargins(
            25, 25, 25, 25
        )  # Pad 10 pixels each way
        selectPredictandFileLayout.setSpacing(0)  # No spacing between elements

        selectPredictandFileFrame.setLayout(selectPredictandFileLayout)

        filesDateLayout.addWidget(selectPredictandFileFrame)

        # Create selectPredictandFile frame
        selectOutputFileFrame = borderedQGroupBox("Select Output File")
        selectOutputFileFrame.setBaseSize(200, 200)

        # Layout for selectPredictandFile frame
        selectOutputFileLayout = QVBoxLayout()
        selectOutputFileLayout.setContentsMargins(
            25, 25, 25, 25
        )  # Pad 10 pixels each way
        selectOutputFileLayout.setSpacing(0)  # No spacing between elements

        selectOutputFileFrame.setLayout(selectOutputFileLayout)

        filesDateLayout.addWidget(selectOutputFileFrame)

        # Create selectDate Frame
        selectDateFrame = borderedQGroupBox("Select Data Period")
        selectDateFrame.setBaseSize(200, 200)

        selectDateLayout = QVBoxLayout()
        selectDateLayout.setContentsMargins(
            25, 25, 25, 25
        )  # Remove padding from the layout
        selectDateLayout.setSpacing(0)  # No spacing between elements
        selectDateFrame.setLayout(selectDateLayout)  # Apply the layout to the frame

        filesDateLayout.addWidget(selectDateFrame)

        # Horizontal frames needed in selectDateFrame for labels to be attached to date selectors

        fitStartDateFrame = QFrame()
        fitStartDateFrame.setFrameStyle(QFrame.NoFrame)
        fitStartDateFrame.setBaseSize(190, 50)

        fitStartDateLayout = QHBoxLayout()
        fitStartDateLayout.setContentsMargins(25, 25, 25, 25)  # 10 Pixel padding
        fitStartDateLayout.setSpacing(0)  # No spacing between elements
        fitStartDateFrame.setLayout(fitStartDateLayout)  # Apply the layout to the frame

        fitEndDateFrame = QFrame()
        fitEndDateFrame.setFrameStyle(QFrame.NoFrame)
        fitEndDateFrame.setBaseSize(190, 50)

        fitEndDateLayout = QHBoxLayout()
        fitEndDateLayout.setContentsMargins(25, 25, 25, 25)  # 10 Pixel padding
        fitEndDateLayout.setSpacing(0)  # No spacing between elements
        fitEndDateFrame.setLayout(fitEndDateLayout)  # Apply the layout to the frame

        selectDateLayout.addWidget(fitStartDateFrame)
        selectDateLayout.addWidget(fitEndDateFrame)

        # Create selectPredictor frame
        selectPredictorsFrame = borderedQGroupBox("Select Predictors")
        selectPredictorsFrame.setBaseSize(200, 400)

        # Layout for selectPredictors frame
        selectPredictorsLayout = QVBoxLayout()
        selectPredictorsLayout.setContentsMargins(
            25, 25, 25, 25
        )  # Pad 10 pixels each way
        selectPredictorsLayout.setSpacing(0)  # No spacing between elements

        selectPredictorsFrame.setLayout(selectPredictorsLayout)

        contentAreaLayout.addWidget(selectPredictorsFrame)

        optionsFrame = QFrame()
        optionsFrame.setFrameStyle(QFrame.NoFrame)
        optionsFrame.setBaseSize(200, 400)

        # Layout for selectPredictors frame
        optionsLayout = QVBoxLayout()
        optionsLayout.setContentsMargins(0, 0, 0, 0)  # Pad 10 pixels each way
        optionsLayout.setSpacing(10)  # No spacing between elements
        optionsFrame.setLayout(optionsLayout)

        contentAreaLayout.addWidget(optionsFrame)

        modelProcessFrame = QFrame()
        modelProcessFrame.setFrameStyle(QFrame.NoFrame)
        modelProcessFrame.setBaseSize(200, 100)

        # Layout for selectPredictors frame
        modelProcessLayout = QHBoxLayout()
        modelProcessLayout.setContentsMargins(0, 0, 0, 0)  # Pad 10 pixels each way
        modelProcessLayout.setSpacing(10)  # No spacing between elements
        modelProcessFrame.setLayout(modelProcessLayout)

        optionsLayout.addWidget(modelProcessFrame)

        modelTypeFrame = borderedQGroupBox("Select Model Type")
        modelTypeFrame.setBaseSize(200, 100)

        # Layout for selectPredictors frame
        modelTypeLayout = QVBoxLayout()
        modelTypeLayout.setContentsMargins(25, 25, 25, 25)  # Pad 10 pixels each way
        modelTypeLayout.setSpacing(0)  # No spacing between elements
        modelTypeFrame.setLayout(modelTypeLayout)

        modelProcessLayout.addWidget(modelTypeFrame)

        processFrame = borderedQGroupBox("Select Process")
        processFrame.setBaseSize(200, 100)

        # Layout for selectPredictors frame
        processLayout = QVBoxLayout()
        processLayout.setContentsMargins(25, 25, 25, 25)  # Pad 10 pixels each way
        processLayout.setSpacing(0)  # No spacing between elements
        processFrame.setLayout(processLayout)

        modelProcessLayout.addWidget(processFrame)

        autoregressionResidualFrame = QFrame()
        autoregressionResidualFrame.setFrameStyle(QFrame.NoFrame)
        autoregressionResidualFrame.setBaseSize(200, 100)

        # Layout for selectPredictors frame
        autoregressionResidualLayout = QHBoxLayout()
        autoregressionResidualLayout.setContentsMargins(
            0, 0, 0, 0
        )  # Pad 10 pixels each way
        autoregressionResidualLayout.setSpacing(10)  # No spacing between elements
        autoregressionResidualFrame.setLayout(autoregressionResidualLayout)

        optionsLayout.addWidget(autoregressionResidualFrame)

        autoregressionFrame = borderedQGroupBox("Autoregression")
        autoregressionFrame.setBaseSize(200, 100)

        # Layout for selectPredictors frame
        autoregressionLayout = QHBoxLayout()
        autoregressionLayout.setContentsMargins(
            25, 25, 25, 25
        )  # Pad 25 pixels each way
        autoregressionLayout.setSpacing(0)  # No spacing between elements
        autoregressionFrame.setLayout(autoregressionLayout)

        autoregressionResidualLayout.addWidget(autoregressionFrame)

        residualFrame = borderedQGroupBox("Residual Analysis")
        residualFrame.setBaseSize(200, 100)

        # Layout for selectPredictors frame
        residualLayout = QVBoxLayout()
        residualLayout.setContentsMargins(25, 25, 25, 25)  # Pad 10 pixels each way
        residualLayout.setSpacing(0)  # No spacing between elements
        residualFrame.setLayout(residualLayout)

        autoregressionResidualLayout.addWidget(residualFrame)

        chowHistogramFrame = QFrame()
        chowHistogramFrame.setFrameStyle(QFrame.NoFrame)
        chowHistogramFrame.setBaseSize(200, 100)

        # Layout for selectPredictors frame
        chowHistogramLayout = QHBoxLayout()
        chowHistogramLayout.setContentsMargins(0, 0, 0, 0)  # Pad 10 pixels each way
        chowHistogramLayout.setSpacing(10)  # No spacing between elements
        chowHistogramFrame.setLayout(chowHistogramLayout)

        optionsLayout.addWidget(chowHistogramFrame)

        chowTestFrame = borderedQGroupBox("Chow Test")
        chowTestFrame.setBaseSize(200, 100)

        # Layout for selectPredictors frame
        chowTestLayout = QHBoxLayout()
        chowTestLayout.setContentsMargins(25, 25, 25, 25)  # Pad 10 pixels each way
        chowTestLayout.setSpacing(0)  # No spacing between elements
        chowTestFrame.setLayout(chowTestLayout)

        chowHistogramLayout.addWidget(chowTestFrame)

        histogramFrame = borderedQGroupBox("Histogram")
        histogramFrame.setBaseSize(200, 100)

        # Layout for selectPredictors frame
        histogramLayout = QHBoxLayout()
        histogramLayout.setContentsMargins(25, 25, 25, 25)  # Pad 10 pixels each way
        histogramLayout.setSpacing(10)  # No spacing between elements
        histogramFrame.setLayout(histogramLayout)

        chowHistogramLayout.addWidget(histogramFrame)

        deTrendFrame = borderedQGroupBox("De Trend")
        deTrendFrame.setBaseSize(200, 100)
        # Wait, I could just make a frame wrapper that does this for me

        # Layout for selectPredictors frame
        deTrendLayout = QHBoxLayout()
        deTrendLayout.setContentsMargins(25, 25, 25, 25)  # Pad 10 pixels each way
        deTrendLayout.setSpacing(0)  # No spacing between elements
        deTrendFrame.setLayout(deTrendLayout)

        optionsLayout.addWidget(deTrendFrame)

        crossValFrame = borderedQGroupBox("Cross Validation")
        crossValFrame.setBaseSize(200, 100)
        # Wait, I could just make a frame wrapper that does this for me

        # Layout for selectPredictors frame
        crossValLayout = QHBoxLayout()
        crossValLayout.setContentsMargins(25, 25, 25, 25)  # Pad 10 pixels each way
        crossValLayout.setSpacing(10)  # No spacing between elements
        crossValFrame.setLayout(crossValLayout)

        optionsLayout.addWidget(crossValFrame)

        buttonFrame = QFrame()
        buttonFrame.setBaseSize(600, 60)
        buttonFrame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        buttonLayout = QHBoxLayout()
        buttonLayout.setContentsMargins(25, 25, 25, 25)
        buttonLayout.setSpacing(10)

        buttonFrame.setLayout(buttonLayout)

        mainLayout.addWidget(buttonFrame)

        # Actual Content

        # Predictand file selector button
        selectPredictandButton = QPushButton("📂 Select Predictand File")
        selectPredictandButton.clicked.connect(self.selectPredictandButtonClicked)
        selectPredictandFileLayout.addWidget(selectPredictandButton)

        self.selectPredictandLabel = QLabel("No Predictand Selected")
        selectPredictandFileLayout.addWidget(self.selectPredictandLabel)

        # Predictand file selector button
        selectOutputButton = QPushButton("📂 Select Output File")
        selectOutputButton.clicked.connect(self.selectOutputButtonClicked)
        selectOutputFileLayout.addWidget(selectOutputButton)

        self.selectOutputLabel = QLabel("No Output Selected")
        selectOutputFileLayout.addWidget(self.selectOutputLabel)

        # Create a date edit box in the fitStart frame to choose start fit date

        fitStartDateLabel = QLabel("Fit Start:")
        fitStartDateLayout.addWidget(fitStartDateLabel)
        self.fitStartDateChooser = QDateEdit(calendarPopup=True)
        self.fitStartDateChooser.setDate(QDate(1948, 1, 1))
        self.fitStartDateChooser.setMinimumWidth(100)

        fitStartDateLayout.addWidget(self.fitStartDateChooser)

        # Create a date edit box in the fitEnd frame to choose start fit date

        fitEndDateLabel = QLabel("Fit End:")
        fitEndDateLayout.addWidget(fitEndDateLabel)
        self.fitEndDateChooser = QDateEdit(calendarPopup=True)
        self.fitEndDateChooser.setMinimumWidth(100)
        self.fitEndDateChooser.setDate(QDate(2015, 12, 31))
        fitEndDateLayout.addWidget(self.fitEndDateChooser)

        # Create predictor label
        predictorLabel = QLabel("Predictor Variables")
        selectPredictorsLayout.addWidget(predictorLabel)

        # Create a scroll area for the predictors, and a frame for predictor labels to inhabit within the scroll area
        predictorsScrollArea = QScrollArea()
        predictorsScrollArea.setWidgetResizable(True)
        predictorsScrollFrame = QFrame()
        predictorsScrollFrame.setFrameStyle(
            QFrame.NoFrame
        )  # No border around the frame

        # predictorsScrollFrame.setBaseSize(200,300)
        # predictorsScrollFrame.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Fixed)

        self.predictorsScrollLayout = QVBoxLayout()
        self.predictorsScrollLayout.setContentsMargins(
            0, 0, 0, 0
        )  # Remove padding from the layout
        self.predictorsScrollLayout.setSpacing(0)  # No spacing between elements
        self.predictorsScrollLayout.setAlignment(Qt.AlignHCenter)
        predictorsScrollFrame.setLayout(
            self.predictorsScrollLayout
        )  # Apply the layout to the frame

        selectPredictorsLayout.addWidget(predictorsScrollArea)

        # Get all predictors and populate scroll frame
        self.writePredictors()

        predictorsScrollArea.setWidget(predictorsScrollFrame)

        selectPredictorPathButton = QPushButton("📂 Select Predictor Path")
        selectPredictorPathButton.clicked.connect(self.updatePredictors)
        selectPredictorPathButton.setContentsMargins(0, 25, 0, 25)
        selectPredictorsLayout.addWidget(selectPredictorPathButton)

        # Radio buttons for model type

        # Process radio buttons
        self.modelRadioButtonGroup = QButtonGroup()
        self.modelRadioButtonGroup.setExclusive(True)
        self.monthlyRadioButton = QRadioButton("Monthly")
        self.monthlyRadioButton.setChecked(True)
        self.monthlyRadioButton.setObjectName("0")
        seasonalRadioButton = QRadioButton("Seasonal")
        seasonalRadioButton.setObjectName("1")
        annualRadioButton = QRadioButton("Annual")
        annualRadioButton.setObjectName("2")
        self.modelRadioButtonGroup.addButton(self.monthlyRadioButton)
        self.modelRadioButtonGroup.addButton(seasonalRadioButton)
        self.modelRadioButtonGroup.addButton(annualRadioButton)

        modelTypeLayout.addWidget(self.monthlyRadioButton)
        modelTypeLayout.addWidget(seasonalRadioButton)
        modelTypeLayout.addWidget(annualRadioButton)

        # Process radio buttons
        self.processRadioButtonGroup = QButtonGroup()
        self.processRadioButtonGroup.setExclusive(True)
        self.unconditionalRadioButton = QRadioButton("Unconditional")
        self.unconditionalRadioButton.setObjectName("0")
        self.unconditionalRadioButton.setChecked(True)
        conditionalRadioButton = QRadioButton("Conditional")
        conditionalRadioButton.setObjectName("1")
        self.processRadioButtonGroup.addButton(self.unconditionalRadioButton)
        self.processRadioButtonGroup.addButton(conditionalRadioButton)

        processLayout.addWidget(self.unconditionalRadioButton)
        processLayout.addWidget(conditionalRadioButton)

        # Autoregression check box
        self.autoregressionCheck = QCheckBox("Include Autoregression")
        autoregressionLayout.addWidget(self.autoregressionCheck)

        # Residual Analysis radio buttons
        self.residualRadioButtonGroup = QButtonGroup()
        self.residualRadioButtonGroup.setExclusive(True)
        self.noneRadioButton = QRadioButton("None")
        self.noneRadioButton.setChecked(True)
        scatterRadioButton = QRadioButton("Scatter Plot")
        histogramRadioButton = QRadioButton("Histogram")
        self.residualRadioButtonGroup.addButton(self.noneRadioButton)
        self.residualRadioButtonGroup.addButton(scatterRadioButton)
        self.residualRadioButtonGroup.addButton(histogramRadioButton)

        residualLayout.addWidget(self.noneRadioButton)
        residualLayout.addWidget(scatterRadioButton)
        residualLayout.addWidget(histogramRadioButton)

        # Chow Test CheckBox
        self.chowCheck = QCheckBox("Calculate Chow Test")
        chowTestLayout.addWidget(self.chowCheck)

        # Histogram Input

        histogramLabel = QLabel("No. of categories")
        histogramLayout.addWidget(histogramLabel)

        self.histogramInput = QLineEdit("14")
        self.histogramInput.setMaximumWidth(50)

        histogramLayout.addWidget(self.histogramInput)

        # De Trend Radio Buttons

        self.deTrendRadioButtonGroup = QButtonGroup()
        self.deTrendRadioButtonGroup.setExclusive(True)
        self.noneTrendRadioButton = QRadioButton("None")
        self.noneTrendRadioButton.setChecked(True)
        self.noneTrendRadioButton.setObjectName("0")
        linearRadioButton = QRadioButton("Linear")
        linearRadioButton.setObjectName("1")
        powerRadioButton = QRadioButton("Power Function")
        powerRadioButton.setObjectName("2")
        self.deTrendRadioButtonGroup.addButton(self.noneTrendRadioButton)
        self.deTrendRadioButtonGroup.addButton(linearRadioButton)
        self.deTrendRadioButtonGroup.addButton(powerRadioButton)

        deTrendLayout.addWidget(self.noneTrendRadioButton)
        deTrendLayout.addWidget(linearRadioButton)
        deTrendLayout.addWidget(powerRadioButton)

        # Cross Validation COntent

        self.crossValCalcCheck = QCheckBox("Calculate")
        crossValLayout.addWidget(self.crossValCalcCheck)

        crossValLabel = QLabel("No. of folds: ")
        crossValLayout.addWidget(crossValLabel)

        self.crossValInput = QLineEdit("2")
        self.crossValInput.setMaximumWidth(50)
        crossValLayout.addWidget(self.crossValInput)

        cailbrateButton = QPushButton("Calibrate")
        cailbrateButton.clicked.connect(self.doCalibration)
        cailbrateButton.setStyleSheet(
            "background-color: #4CAF50; color: white; font-weight: bold;"
        )

        buttonLayout.addWidget(cailbrateButton)

        resetButton = QPushButton("🔄 Reset")
        resetButton.clicked.connect(self.resetAll)
        resetButton.setStyleSheet(
            "background-color: #F44336; color: white; font-weight: bold;"
        )
        buttonLayout.addWidget(resetButton)

    def doCalibration(self):
        from src.lib.CalibrateModel import calibrateModel, CalibrateAnalysisApp, displayError

        print(self.predictandSelected)
        fitStartDate = self.QDateEditToDateTime(self.fitStartDateChooser)
        fitEndDate = self.QDateEditToDateTime(self.fitEndDateChooser)
        modelType = int(self.modelRadioButtonGroup.checkedButton().objectName())
        parmOpt = bool(int(self.processRadioButtonGroup.checkedButton().objectName()))
        deTrend = int(self.deTrendRadioButtonGroup.checkedButton().objectName())
        fileList = [
            self.predictandSelected
        ]  # Copy predictors to a new list so when calibrateModel messes with it it doesnt break absolutely everything
        for predictor in self.predictorsSelected:
            fileList.append(predictor)
        
        try:
            data = calibrateModel(
                fileList,
                self.outputSelected,
                fitStartDate,
                fitEndDate,
                modelType,
                parmOpt,
                self.autoregressionCheck.isChecked(),
                self.chowCheck.isChecked(),
                deTrend,
                self.crossValCalcCheck.isChecked(),
                int(self.crossValInput.text()),
            )   
        except Exception as e:
            displayError(e)
        else:
            #print(data)
            self.newWindow = CalibrateAnalysisApp()
            self.newWindow.loadResults(data)
            self.newWindow.show()

    def resetAll(self):
        # Reset file and path variables and labels
        self.predictorPath = "predictor files"
        self.predictandSelected = ""
        self.outputSelected = ""
        self.predictorsSelected = []
        self.selectPredictandLabel.setText("No Predictand Selected")
        self.selectOutputLabel.setText("No Output Selected")
        # Remove all clicked predictors and reset to default predictors
        self.resetPredictors()
        # Reset dates
        self.fitStartDateChooser.setDate(QDate(1948, 1, 1))
        self.fitEndDateChooser.setDate(QDate(2015, 12, 31))
        # Uncheck all checkboxes and return radios to default
        self.monthlyRadioButton.setChecked(True)
        self.unconditionalRadioButton.setChecked(True)
        self.autoregressionCheck.setChecked(False)
        self.noneRadioButton.setChecked(True)
        self.chowCheck.setChecked(False)
        self.noneTrendRadioButton.setChecked(True)
        self.crossValCalcCheck.setChecked(False)
        # Reset all line edit values to default
        self.histogramInput.setText("14")
        self.crossValInput.setText("2")

    def QDateEditToDateTime(self, dateEdit):
        rawStartDate = dateEdit.date()
        dateTime = rawStartDate.toPyDate()
        return dateTime

    def writePredictors(self):
        for predictor in sorted(listdir(self.predictorPath)):
            # These are functionally labels, but QLabels do not have an onclick function that emits a sender signal,
            # so QPushButtons are used instead
            predictor = predictor.lower()
            if predictor.split(".")[-1] == "dat":
                predictorScrollLabelButton = QPushButton(predictor)
                predictorScrollLabelButton.setFlat = True

                predictorScrollLabelButton.clicked.connect(self.predictorLabelClicked)
                predictorScrollLabelButton.setBaseSize(200, 20)
                predictorScrollLabelButton.setStyleSheet(
                    "color: black; background-color: #F0F0F0"
                )
                predictorScrollLabelButton.setSizePolicy(
                    QSizePolicy.Expanding, QSizePolicy.Expanding
                )
                self.predictorsScrollLayout.addWidget(predictorScrollLabelButton)

    def updatePredictors(self):
        self.predictorsSelected = []
        pathName = QFileDialog.getExistingDirectory(self)
        self.predictorPath = pathName
        while self.predictorsScrollLayout.count():
            item = self.predictorsScrollLayout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
        if self.predictorPath != "":
            self.writePredictors()
        else:
            self.predictorPath = "predictor files"
            self.writePredictors()

    def resetPredictors(self):
        self.predictorsSelected = []
        self.predictorPath = "predictor files"
        while self.predictorsScrollLayout.count():
            item = self.predictorsScrollLayout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
        self.writePredictors()

    def selectPredictandButtonClicked(self):
        # Will have to be changed soon, as it relies on known file "predictand files"
        fileName = QFileDialog.getOpenFileName(
            self, "Select predictand file", "predictand files", "DAT Files (*.DAT)"
        )
        print(fileName)
        if fileName[0] != "":
            self.predictandSelected = fileName[0]
            self.selectPredictandLabel.setText(
                "File: " + self.predictandSelected.split("/")[-1]
            )  # Only show the name of the file, not the whole path
        else:
            self.predictandSelected = None
            self.selectPredictandLabel.setText("No predictand selected.")

    def selectOutputButtonClicked(self):
        # Will have to be changed soon, as it relies on known file "predictand files"
        fileName = QFileDialog.getOpenFileName(
            self, "Select output file", "SDSM-REFRESH", "PAR Files (*.PAR)"
        )
        print(fileName)
        if fileName[0] != "":
            self.outputSelected = fileName[0]
            self.selectOutputLabel.setText(
                "File: " + self.outputSelected.split("/")[-1]
            )  # Only show the name of the file, not the whole path
        else:
            self.outputSelected = None
            self.selectOutputLabel.setText("No Output Selected.")

    def predictorLabelClicked(self, *args):
        button = self.sender()  # Get the buttonLabel that was clicked
        predictor = (
            button.text()
        )  # Get the name of the buttonLabel, so the predictor file
        if (self.predictorPath + "/" + predictor) not in self.predictorsSelected:
            self.predictorsSelected.append(self.predictorPath + "/" + predictor)
            button.setStyleSheet("color: white; background-color: blue")
        else:
            self.predictorsSelected.remove(self.predictorPath + "/" + predictor)
            button.setStyleSheet("color: black; background-color: #F0F0F0")

    def handleMenuButtonClicks(self):
        button = self.sender().text()
        if button == "Correlation":
            print("nope, that aint right")
        else:
            print("work in progress, pardon our dust")
