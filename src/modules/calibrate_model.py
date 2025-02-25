from PyQt5.QtWidgets import (QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QSizePolicy, 
                             QFrame, QLabel, QFileDialog, QScrollArea, QDateEdit, QCheckBox,
                             QButtonGroup, QRadioButton, QLineEdit, QGroupBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor, QIcon
from os import listdir

# Define the name of the module for display in the content area
moduleName = "Calibrate Model"



class borderedQGroupBox(QGroupBox):
    def __init__(self,args):
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

        self.predictorPath = 'predictor files'
        self.predictandSelected = ""
        self.predictorsSelected = []



        # Main layout for the entire widget
        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the layout
        mainLayout.setSpacing(0)  # No spacing between elements
        self.setLayout(mainLayout)  # Apply the main layout to the widget

        self.setStyleSheet("""
                           QFrame{
                                background-color: #F0F0F0;}
                           borderedQGroupBox{
                                background-color: #F0F0F0;
                                border : 1px solid #CECECE;
                                border-top-left-radius : 20px;
                                border-top-right-radius : 20px;
                                border-bottom-left-radius : 20px;
                                border-bottom-right-radius : 20px;}""")

        # --- Button Bar ---
        # Layout for the buttonBar at the top of the screen
        buttonBarLayout = QHBoxLayout()
        buttonBarLayout.setSpacing(0)  # No spacing between buttons
        buttonBarLayout.setContentsMargins(0, 0, 0, 0)  # No margins around the layout
        buttonBarLayout.setAlignment(Qt.AlignLeft)  # Align buttons to the left

        # Create placeholder buttons for the buttonBar
        buttonNames = ["Reset", "Calibrate", "Settings"]  # Names of the buttons for clarity
        for name in buttonNames:
            button = QPushButton(name)  # Create a button with the given name
            button.setIcon(QIcon("placeholder_icon.png"))  # Placeholder icon
            button.clicked.connect(self.handleMenuButtonClicks)
            button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)  # Expanding size policy
            button.sizeHint()  # Set a Expanding size for the button
            button.setStyleSheet(
                "border: 1px solid lightgray; background-color: #F0F0F0; text-align: left;"
            )  # Style to match the overall design
            buttonBarLayout.addWidget(button)  # Add the button to the buttonBar layout

        # Frame for the buttonBar
        buttonBarFrame = QFrame()
        buttonBarFrame.setLayout(buttonBarLayout)  # Apply the button layout to the frame
        buttonBarFrame.setFrameShape(QFrame.NoFrame)  # No border around the frame
        buttonBarFrame.setFixedHeight(50)  # Match height with other UI elements
        buttonBarFrame.setStyleSheet("background-color: #F0F0F0;")  # Dark gray background
        mainLayout.addWidget(buttonBarFrame)  # Add the buttonBar frame to the main layout

        # --- Content Area ---
        # Frame for the contentArea
        '''
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
        '''
        # --- Center Label (Placeholder) ---
        # Label to display the name of the module (Calibrate Model)
        '''moduleLabel = QLabel(moduleName, self)
        moduleLabel.setStyleSheet("font-size: 24px; color: black;")  # Style the label text
        titleLayout.addWidget(moduleLabel)  # Add the label to the contentArea layout'''


        contentAreaFrame = QFrame()
        contentAreaFrame.setFrameStyle(QFrame.NoFrame)  # No border around the frame
        contentAreaFrame.setBaseSize(600,100)
        contentAreaFrame.setSizePolicy(QSizePolicy.Preferred,QSizePolicy.Expanding)

        # Layout for the contentArea frame
        contentAreaLayout = QHBoxLayout()
        contentAreaLayout.setContentsMargins(10, 10, 10, 10)  # Remove padding from the layout
        contentAreaLayout.setSpacing(10)  # No spacing between elements
        contentAreaFrame.setLayout(contentAreaLayout)  # Apply the layout to the frame

        mainLayout.addWidget(contentAreaFrame)

        #Frame that holds the selectPredictand frame and the selectDate frame
        filesDateFrame = QFrame()
        filesDateFrame.setFrameStyle(QFrame.NoFrame)  # No border around the frame
        filesDateFrame.setBaseSize(200,500)
        filesDateFrame.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)

        filesDateLayout = QVBoxLayout()
        filesDateLayout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the layout
        filesDateLayout.setSpacing(10)  # No spacing between elements
        filesDateFrame.setLayout(filesDateLayout)  # Apply the layout to the frame

        contentAreaLayout.addWidget(filesDateFrame)

        #Create selectPredictandFile frame
        selectPredictandFileFrame = borderedQGroupBox("Select Predictand")
        selectPredictandFileFrame.setBaseSize(200,200)


        #Layout for selectPredictandFile frame
        selectPredictandFileLayout = QVBoxLayout()
        selectPredictandFileLayout.setContentsMargins(25,25,25,25) #Pad 10 pixels each way
        selectPredictandFileLayout.setSpacing(0)  # No spacing between elements


        selectPredictandFileFrame.setLayout(selectPredictandFileLayout)
        
        filesDateLayout.addWidget(selectPredictandFileFrame)

        #Create selectPredictandFile frame
        selectOutputFileFrame = borderedQGroupBox("Select Output File")
        selectOutputFileFrame.setBaseSize(200,200)


        #Layout for selectPredictandFile frame
        selectOutputFileLayout = QVBoxLayout()
        selectOutputFileLayout.setContentsMargins(25,25,25,25) #Pad 10 pixels each way
        selectOutputFileLayout.setSpacing(0)  # No spacing between elements


        selectOutputFileFrame.setLayout(selectOutputFileLayout)
        
        filesDateLayout.addWidget(selectPredictandFileFrame)

        #Create selectDate Frame
        selectDateFrame = borderedQGroupBox("Select Date")
        selectDateFrame.setBaseSize(200,200)


        selectDateLayout = QVBoxLayout()
        selectDateLayout.setContentsMargins(10, 10, 10, 10)  # Remove padding from the layout
        selectDateLayout.setSpacing(0)  # No spacing between elements
        selectDateFrame.setLayout(selectDateLayout)  # Apply the layout to the frame

        filesDateLayout.addWidget(selectDateFrame)

        #Horizontal frames needed in selectDateFrame for labels to be attached to date selectors

        fitStartDateFrame = QFrame()
        fitStartDateFrame.setFrameStyle(QFrame.NoFrame) 
        fitStartDateFrame.setBaseSize(190,50)

        fitStartDateLayout = QHBoxLayout()
        fitStartDateLayout.setContentsMargins(10, 10, 10, 10)  # 10 Pixel padding
        fitStartDateLayout.setSpacing(0)  # No spacing between elements
        fitStartDateFrame.setLayout(fitStartDateLayout)  # Apply the layout to the frame

        fitEndDateFrame = QFrame()
        fitEndDateFrame.setFrameStyle(QFrame.NoFrame) 
        fitEndDateFrame.setBaseSize(190,50)

        fitEndDateLayout = QHBoxLayout()
        fitEndDateLayout.setContentsMargins(10, 10, 10, 10)  # 10 Pixel padding
        fitEndDateLayout.setSpacing(0)  # No spacing between elements
        fitEndDateFrame.setLayout(fitEndDateLayout)  # Apply the layout to the frame

        selectDateLayout.addWidget(fitStartDateFrame)
        selectDateLayout.addWidget(fitEndDateFrame)





        #Create selectPredictor frame
        selectPredictorsFrame = borderedQGroupBox("Select Predictors")
        selectPredictorsFrame.setBaseSize(200,400)



        #Layout for selectPredictors frame
        selectPredictorsLayout = QVBoxLayout()
        selectPredictorsLayout.setContentsMargins(10,10,10,10) #Pad 10 pixels each way
        selectPredictorsLayout.setSpacing(0)  # No spacing between elements


        selectPredictorsFrame.setLayout(selectPredictorsLayout)
        
        contentAreaLayout.addWidget(selectPredictorsFrame)

        optionsFrame = QFrame()
        optionsFrame.setFrameStyle(QFrame.NoFrame)   
        optionsFrame.setBaseSize(200,400)



        #Layout for selectPredictors frame
        optionsLayout = QVBoxLayout()
        optionsLayout.setContentsMargins(10,10,10,10) #Pad 10 pixels each way
        optionsLayout.setSpacing(0)  # No spacing between elements
        optionsFrame.setLayout(optionsLayout)
        
        contentAreaLayout.addWidget(optionsFrame)

        modelProcessFrame = QFrame()
        modelProcessFrame.setFrameStyle(QFrame.NoFrame)   
        modelProcessFrame.setBaseSize(200,100)

        #Layout for selectPredictors frame
        modelProcessLayout = QHBoxLayout()
        modelProcessLayout.setContentsMargins(10,10,10,10) #Pad 10 pixels each way
        modelProcessLayout.setSpacing(0)  # No spacing between elements
        modelProcessFrame.setLayout(modelProcessLayout)
        
        optionsLayout.addWidget(modelProcessFrame)

        modelTypeFrame = borderedQGroupBox("Select Model Type")
        modelTypeFrame.setBaseSize(200,100)

        #Layout for selectPredictors frame
        modelTypeLayout = QVBoxLayout()
        modelTypeLayout.setContentsMargins(10,10,10,10) #Pad 10 pixels each way
        modelTypeLayout.setSpacing(0)  # No spacing between elements
        modelTypeFrame.setLayout(modelTypeLayout)
        
        modelProcessLayout.addWidget(modelTypeFrame)

        processFrame = borderedQGroupBox("Select Process")
        processFrame.setBaseSize(200,100)

        #Layout for selectPredictors frame
        processLayout = QVBoxLayout()
        processLayout.setContentsMargins(10,10,10,10) #Pad 10 pixels each way
        processLayout.setSpacing(0)  # No spacing between elements
        processFrame.setLayout(processLayout)
        
        modelProcessLayout.addWidget(processFrame)


        autoregressionResidualFrame = QFrame()
        autoregressionResidualFrame.setFrameStyle(QFrame.NoFrame)   
        autoregressionResidualFrame.setBaseSize(200,100)

        #Layout for selectPredictors frame
        autoregressionResidualLayout = QHBoxLayout()
        autoregressionResidualLayout.setContentsMargins(10,10,10,10) #Pad 10 pixels each way
        autoregressionResidualLayout.setSpacing(0)  # No spacing between elements
        autoregressionResidualFrame.setLayout(autoregressionResidualLayout)
        
        optionsLayout.addWidget(autoregressionResidualFrame)

        autoregressionFrame = borderedQGroupBox("Autoregression")
        autoregressionFrame.setBaseSize(200,100)

        #Layout for selectPredictors frame
        autoregressionLayout = QHBoxLayout()
        autoregressionLayout.setContentsMargins(10,10,10,10) #Pad 10 pixels each way
        autoregressionLayout.setSpacing(0)  # No spacing between elements
        autoregressionFrame.setLayout(autoregressionLayout)
        
        autoregressionResidualLayout.addWidget(autoregressionFrame)

        residualFrame = borderedQGroupBox("Residual")
        residualFrame.setBaseSize(200,100)

        #Layout for selectPredictors frame
        residualLayout = QHBoxLayout()
        residualLayout.setContentsMargins(10,10,10,10) #Pad 10 pixels each way
        residualLayout.setSpacing(0)  # No spacing between elements
        residualFrame.setLayout(residualLayout)
        
        autoregressionResidualLayout.addWidget(residualFrame)

        chowHistogramFrame = QFrame()
        chowHistogramFrame.setFrameStyle(QFrame.NoFrame)   
        chowHistogramFrame.setBaseSize(200,100)



        #Layout for selectPredictors frame
        chowHistogramLayout = QHBoxLayout()
        chowHistogramLayout.setContentsMargins(10,10,10,10) #Pad 10 pixels each way
        chowHistogramLayout.setSpacing(0)  # No spacing between elements
        chowHistogramFrame.setLayout(chowHistogramLayout)
        
        optionsLayout.addWidget(chowHistogramFrame)

        chowTestFrame = borderedQGroupBox("Chow Test")
        chowTestFrame.setBaseSize(200,100)

        #Layout for selectPredictors frame
        chowTestLayout = QHBoxLayout()
        chowTestLayout.setContentsMargins(10,10,10,10) #Pad 10 pixels each way
        chowTestLayout.setSpacing(0)  # No spacing between elements
        chowTestFrame.setLayout(chowTestLayout)

        chowHistogramLayout.addWidget(chowTestFrame)

        histogramFrame = borderedQGroupBox("Histogram")
        histogramFrame.setBaseSize(200,100)

        #Layout for selectPredictors frame
        histogramLayout = QHBoxLayout()
        histogramLayout.setContentsMargins(10,10,10,10) #Pad 10 pixels each way
        histogramLayout.setSpacing(0)  # No spacing between elements
        histogramFrame.setLayout(histogramLayout)

        chowHistogramLayout.addWidget(histogramFrame)

        deTrendFrame = borderedQGroupBox("De Trend")
        deTrendFrame.setBaseSize(200,100)
        #Wait, I could just make a frame wrapper that does this for me


        #Layout for selectPredictors frame
        deTrendLayout = QHBoxLayout()
        deTrendLayout.setContentsMargins(10,10,10,10) #Pad 10 pixels each way
        deTrendLayout.setSpacing(0)  # No spacing between elements
        deTrendFrame.setLayout(deTrendLayout)
        
        optionsLayout.addWidget(deTrendFrame)

        crossValFrame = borderedQGroupBox("Cross Validation")
        crossValFrame.setBaseSize(200,100)
        #Wait, I could just make a frame wrapper that does this for me


        #Layout for selectPredictors frame
        crossValLayout = QHBoxLayout()
        crossValLayout.setContentsMargins(10,10,10,10) #Pad 10 pixels each way
        crossValLayout.setSpacing(0)  # No spacing between elements
        crossValFrame.setLayout(crossValLayout)
        
        optionsLayout.addWidget(crossValFrame)





        #Actual Content


        #Create predictor label
        predictorLabel = QLabel("Predictor Variables")
        selectPredictorsLayout.addWidget(predictorLabel)

        #Create a scroll area for the predictors, and a frame for predictor labels to inhabit within the scroll area
        predictorsScrollArea = QScrollArea()
        predictorsScrollArea.setWidgetResizable(True)
        predictorsScrollFrame = QFrame()
        predictorsScrollFrame.setFrameStyle(QFrame.NoFrame)  # No border around the frame
        
        #predictorsScrollFrame.setBaseSize(200,300)
        #predictorsScrollFrame.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Fixed)


        predictorsScrollLayout = QVBoxLayout()
        selectPredictorsLayout.setContentsMargins(25, 25, 25, 25) #Pad 10 pixels each way
        predictorsScrollLayout.setSpacing(0)  # No spacing between elements
        predictorsScrollLayout.setAlignment(Qt.AlignHCenter)
        predictorsScrollFrame.setLayout(predictorsScrollLayout)  # Apply the layout to the frame


        selectPredictorsLayout.addWidget(predictorsScrollArea)

        #Get all predictors and populate scroll frame

        for predictor in listdir(self.predictorPath):
            #These are functionally labels, but QLabels do not have an onclick function that emits a sender signal,
            #so QPushButtons are used instead
            predictorScrollLabelButton = QPushButton(predictor)
            predictorScrollLabelButton.setFlat = True
            predictorScrollLabelButton.setStyleSheet("color: black; background-color: #F0F0F0")
            predictorScrollLabelButton.clicked.connect(self.predictorLabelClicked)
            predictorScrollLabelButton.setBaseSize(200, 20)
            predictorScrollLabelButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            predictorsScrollLayout.addWidget(predictorScrollLabelButton) 
        
        predictorsScrollArea.setWidget(predictorsScrollFrame)

        #Radio buttons for model type

        #Process radio buttons
        modelRadioButtonGroup = QButtonGroup()
        modelRadioButtonGroup.setExclusive(True)
        monthlyRadioButton = QRadioButton("Monthly")
        monthlyRadioButton.setChecked(True)
        seasonalRadioButton = QRadioButton("Seasonal")
        annualRadioButton = QRadioButton("Annual")
        modelRadioButtonGroup.addButton(monthlyRadioButton)
        modelRadioButtonGroup.addButton(seasonalRadioButton)
        modelRadioButtonGroup.addButton(annualRadioButton)

        modelTypeLayout.addWidget(monthlyRadioButton)
        modelTypeLayout.addWidget(seasonalRadioButton)
        modelTypeLayout.addWidget(annualRadioButton)

        #Process radio buttons
        processRadioButtonGroup = QButtonGroup()
        processRadioButtonGroup.setExclusive(True)
        unconditionalRadioButton = QRadioButton("Unconditional")
        unconditionalRadioButton.setChecked(True)
        conditionalRadioButton = QRadioButton("Conditional")
        processRadioButtonGroup.addButton(unconditionalRadioButton)
        processRadioButtonGroup.addButton(conditionalRadioButton)

        processLayout.addWidget(unconditionalRadioButton)
        processLayout.addWidget(conditionalRadioButton)


        # Add a spacer to ensure content is properly spaced
        #titleLayout.addStretch()
    def predictorLabelClicked(self,*args):
        button = self.sender() #Get the buttonLabel that was clicked
        predictor = button.text() #Get the name of the buttonLabel, so the predictor file
        if predictor not in self.predictorsSelected:
            self.predictorsSelected.append(predictor)
            button.setStyleSheet("color: white; background-color: blue")
        else:
            self.predictorsSelected.remove(predictor)
            button.setStyleSheet("color: black; background-color: #F0F0F0")

        
    
    def handleMenuButtonClicks(self):
        button = self.sender().text()
        if button == "Correlation":
            print("nope, that aint right")
        else:
            print("work in progress, pardon our dust")
