from PyQt5.QtWidgets import QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QSizePolicy, QFrame, QLabel, QFileDialog, QScrollArea
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QPalette, QColor, QIcon
from ScreenVars import correlation, analyseData
from os import listdir

# Define the name of the module for display in the content area
moduleName = "Screen Variables"

    
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

        self.predictorPath = 'predictor files'

        self.predictandSelected = ""
        self.predictorsSelected = []
        
        # Main layout for the entire widget
        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the layout
        mainLayout.setSpacing(0)  # No spacing between elements
        self.setLayout(mainLayout)  # Apply the main layout to the widget

        # --- Button Bar ---
        # Layout for the buttonBar at the top of the screen
        buttonBarLayout = QHBoxLayout()
        buttonBarLayout.setSpacing(0)  # No spacing between buttons
        buttonBarLayout.setContentsMargins(0, 0, 0, 0)  # No margins around the layout
        buttonBarLayout.setAlignment(Qt.AlignLeft)  # Align buttons to the left

        # Create placeholder buttons for the buttonBar
        buttonNames = ["Reset", "Analyse", "Correlation", "Scatter", "Settings"]  # Names of the buttons for clarity
        for name in buttonNames:
            button = QPushButton(name)  # Create a button with the given name
            button.setIcon(QIcon("placeholder_icon.png"))  # Placeholder icon
            button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)  # Fixed size policy
            button.sizeHint()  # Set a fixed size for the button
            button.setStyleSheet(
                "border: 1px solid lightgray; background-color: #F0F0F0; text-align: left;"
            )  # Style to match the overall design
            buttonBarLayout.addWidget(button)  # Add the button to the buttonBar layout

        # Frame for the buttonBar
        buttonBarFrame = QFrame()
        buttonBarFrame.setLayout(buttonBarLayout)  # Apply the button layout to the frame
        buttonBarFrame.setFrameShape(QFrame.NoFrame)  # No border around the frame
        buttonBarFrame.setFixedHeight(50)  # Match height with other UI elements
        buttonBarFrame.setStyleSheet("background-color: #A9A9A9;")  # Dark gray background
        mainLayout.addWidget(buttonBarFrame)  # Add the buttonBar frame to the main layout

        # --- Content Area ---
        # Frame for the contentArea
        titleFrame = QFrame()
        titleFrame.setFrameShape(QFrame.NoFrame)  # No border around the frame
        titleFrame.setFixedHeight(100)

        # Layout for the contentArea frame
        titleLayout = QVBoxLayout()
        titleLayout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the layout
        titleLayout.setSpacing(0)  # No spacing between elements
        titleFrame.setLayout(titleLayout)  # Apply the layout to the frame

        

        # Set the background color to light gray
        titleFrame.setStyleSheet("background-color: #D3D3D3;")

        # Add the title frame to the main layout
        mainLayout.addWidget(titleFrame)

        contentAreaFrame = QFrame()
        contentAreaFrame.setFrameShape(QFrame.NoFrame)  # No border around the frame
        contentAreaFrame.setBaseSize(100,100)
        contentAreaFrame.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)

        # Layout for the contentArea frame
        contentAreaLayout = QHBoxLayout()
        contentAreaLayout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the layout
        contentAreaLayout.setSpacing(0)  # No spacing between elements
        contentAreaFrame.setLayout(contentAreaLayout)  # Apply the layout to the frame

        mainLayout.addWidget(contentAreaFrame)

        #Frame that holds the selectPredictand frame and the selectDate frame
        fileDateFrame = QFrame()
        fileDateFrame.setFrameShape(QFrame.NoFrame)  # No border around the frame
        fileDateFrame.setBaseSize(200,500)
        fileDateFrame.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Expanding)

        fileDateLayout = QVBoxLayout()
        fileDateLayout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the layout
        fileDateLayout.setSpacing(0)  # No spacing between elements
        fileDateFrame.setLayout(fileDateLayout)  # Apply the layout to the frame

        contentAreaLayout.addWidget(fileDateFrame)

        #Create selectPredictandFile frame
        selectPredictandFileFrame = QFrame()
        selectPredictandFileFrame.setFrameShape(QFrame.StyledPanel)   
        selectPredictandFileFrame.setFixedSize(200,200)


        #Layout for selectPredictandFile frame
        selectPredictandFileLayout = QVBoxLayout()
        selectPredictandFileLayout.setContentsMargins(25,25,25,25) #Pad 10 pixels each way
        selectPredictandFileLayout.setSpacing(0)  # No spacing between elements
        selectPredictandFileFrame.setStyleSheet("background-color: #D3D3D3;")


        selectPredictandFileFrame.setLayout(selectPredictandFileLayout)
        
        fileDateLayout.addWidget(selectPredictandFileFrame)

        #Create selectDate Frame
        selectDateFrame = QFrame()
        selectDateFrame.setFrameShape(QFrame.StyledPanel) 
        selectDateFrame.setFixedSize(200,200)
        selectDateFrame.setStyleSheet("background-color: #D3D3D3;")


        selectDateLayout = QVBoxLayout()
        selectDateLayout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the layout
        selectDateLayout.setSpacing(0)  # No spacing between elements
        selectDateFrame.setLayout(selectDateLayout)  # Apply the layout to the frame

        fileDateLayout.addWidget(selectDateFrame)




        #Create selectPredictor frame
        selectPredictorsFrame = QFrame()
        selectPredictorsFrame.setFrameShape(QFrame.StyledPanel)   
        selectPredictorsFrame.setFixedSize(200,400)


        #Layout for selectPredictors frame
        selectPredictorsLayout = QVBoxLayout()
        selectPredictorsLayout.setContentsMargins(25,25,25,25) #Pad 10 pixels each way
        selectPredictorsLayout.setSpacing(0)  # No spacing between elements
        selectPredictorsFrame.setStyleSheet("background-color: #D3D3D3;")


        selectPredictorsFrame.setLayout(selectPredictorsLayout)
        
        contentAreaLayout.addWidget(selectPredictorsFrame)

        #Create description, autoregression, process, significance (DARPS) frame
        selectDARPSFrame = QFrame()
        selectDARPSFrame.setFrameShape(QFrame.NoFrame)  # No border around the frame
        selectDARPSFrame.setBaseSize(200,500)
        selectDARPSFrame.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Expanding)

        #Create DARPS Layout

        selectDARPSLayout = QVBoxLayout()
        selectDARPSLayout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the layout
        selectDARPSLayout.setSpacing(0)  # No spacing between elements
        selectDARPSFrame.setLayout(selectDARPSLayout)  # Apply the layout to the frame

        contentAreaLayout.addWidget(selectDARPSFrame)

        #Create predictorDescription frame
        predictorDescriptionFrame = QFrame()
        predictorDescriptionFrame.setFrameShape(QFrame.StyledPanel)   
        predictorDescriptionFrame.setFixedSize(200,100)


        #Layout for predictorDescription frame
        predictorDescriptionLayout = QVBoxLayout()
        predictorDescriptionLayout.setContentsMargins(25,25,25,25) #Pad 10 pixels each way
        predictorDescriptionLayout.setSpacing(0)  # No spacing between elements
        predictorDescriptionFrame.setStyleSheet("background-color: #D3D3D3;")
        predictorDescriptionFrame.setLayout(predictorDescriptionLayout)

        selectDARPSLayout.addWidget(predictorDescriptionFrame)

        #Create autoregression frame
        autoregressionFrame = QFrame()
        autoregressionFrame.setFrameShape(QFrame.StyledPanel)   
        autoregressionFrame.setFixedSize(200,100)


        #Layout for autoregression frame
        autoregressionLayout = QVBoxLayout()
        autoregressionLayout.setContentsMargins(25,25,25,25) #Pad 10 pixels each way
        autoregressionLayout.setSpacing(0)  # No spacing between elements
        autoregressionFrame.setStyleSheet("background-color: #D3D3D3;")
        autoregressionFrame.setLayout(autoregressionLayout)

    

        selectDARPSLayout.addWidget(autoregressionFrame)

        #Create process frame
        processFrame = QFrame()
        processFrame.setFrameShape(QFrame.StyledPanel)   
        processFrame.setFixedSize(200,100)


        #Layout for process frame
        processLayout = QVBoxLayout()
        processLayout.setContentsMargins(25,25,25,25) #Pad 10 pixels each way
        processLayout.setSpacing(0)  # No spacing between elements
        processFrame.setStyleSheet("background-color: #D3D3D3;")
        processFrame.setLayout(processLayout)


        selectDARPSLayout.addWidget(processFrame)

        #Create significance frame
        significanceFrame = QFrame()
        significanceFrame.setFrameShape(QFrame.StyledPanel)   
        significanceFrame.setFixedSize(200,100)


        #Layout for significance frame
        significanceLayout = QVBoxLayout()
        significanceLayout.setContentsMargins(25,25,25,25) #Pad 10 pixels each way
        significanceLayout.setSpacing(0)  # No spacing between elements
        significanceFrame.setStyleSheet("background-color: #D3D3D3;")
        significanceFrame.setLayout(significanceLayout)


        selectDARPSLayout.addWidget(significanceFrame)

        


        # ------------ ACTUAL CONTENT ------------
        # Label to display the name of the module (Screen Variables)
        moduleLabel = QLabel(moduleName, self)
        moduleLabel.setStyleSheet("font-size: 24px; color: black;")  # Style the label text
        titleLayout.addWidget(moduleLabel)  # Add the label to the contentArea layout

        #Predictand file selector button
        selectPredictandButton = QPushButton("Select predictand")
        selectPredictandButton.clicked.connect(self.selectPredictandButtonClicked)
        selectPredictandFileLayout.addWidget(selectPredictandButton)

        self.selectPredictandLabel = QLabel("No predictand selected")
        selectPredictandFileLayout.addWidget(self.selectPredictandLabel)

        #Predictor files selector button
        '''selectPredictorsButton = QPushButton("Select predictors")
        selectPredictorsButton.clicked.connect(self.selectPredictorsButtonClicked)
        selectPredictorsLayout.addWidget(selectPredictorsButton)

        self.selectPredictorsLabel = QLabel("No predictors selected")
        selectPredictorsLayout.addWidget(self.selectPredictorsLabel)'''

        #Create a scroll area for the predictors, and a frame for predictor labels to inhabit within the scroll area
        predictorsScrollArea = QScrollArea()

        predictorsScrollFrame = QFrame()
        predictorsScrollFrame.setFrameShape(QFrame.NoFrame)  # No border around the frame
        predictorsScrollFrame.setBaseSize(200,300)
        predictorsScrollFrame.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)


        predictorsScrollLayout = QVBoxLayout()
        predictorsScrollLayout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the layout
        predictorsScrollLayout.setSpacing(0)  # No spacing between elements
        predictorsScrollFrame.setLayout(predictorsScrollLayout)  # Apply the layout to the frame


        selectPredictorsLayout.addWidget(predictorsScrollArea)

        #Get all predictors and populate scroll frame


        for predictor in listdir(self.predictorPath):
            predictorScrollLabel = QPushButton(predictor)
            predictorScrollLabel.setFlat = True
            predictorScrollLabel.clicked.connect(self.predictorLabelClicked)
            predictorsScrollLayout.addWidget(predictorScrollLabel) 
        
        predictorsScrollArea.setWidget(predictorsScrollFrame)





        #Blank frame to allow placement wherever I want
        blankFrame = QFrame()
        blankFrame.setFrameShape(QFrame.NoFrame)  # No border around the frame
        blankFrame.setBaseSize(QSize(200,200))
        blankFrame.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding) #Allow our blank frame to fill the bottom of the screen

        # Layout for the contentArea frame
        blankLayout = QVBoxLayout()
        blankLayout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the layout
        blankLayout.setSpacing(0)  # No spacing between elements
        blankFrame.setLayout(blankLayout)  # Apply the layout to the frame

        mainLayout.addWidget(blankFrame) #Is a bodge, hopefully figure it out later

        # Add a spacer to ensure content is properly spaced
        
        titleLayout.addStretch()
        contentAreaLayout.addStretch()

    def selectPredictandButtonClicked(self):
        #Will have to be changed soon, as it relies on known file "predictand files"
        fileName = QFileDialog.getOpenFileName(self, "Select predictand file", 'predictand files', "DAT Files (*.DAT)") 
        print(fileName)
        if fileName[0] != '':
            self.predictandSelected = fileName[0]
            self.selectPredictandLabel.setText("File: "+self.predictandSelected.split("/")[-1]) #Only show the name of the file, not the whole path
        else:
            self.predictandSelected = None
            self.selectPredictandLabel.setText("No predictand selected")

    def predictorLabelClicked(self,*args):
        print("You clicked a label")
        button = self.sender()
        predictor = button.text()
        if predictor not in self.predictorsSelected:
            self.predictorsSelected.append(predictor)
            button.setStyleSheet("color: white; background-color: blue")
        else:
            self.predictorsSelected.remove(predictor)
            button.setStyleSheet("color: black; background-color: #D3D3D3")
        print(self.predictorsSelected)
        #def selectPredictorsButtonClicked(self):
        #Will have to be changed soon, as it relies on known file "predictor files"
        #fileNames = QFileDialog.getOpenFileNames(self, "Select predictor files", 'predictor files', "DAT Files (*.DAT)")
        #self.predictorsSelected = []
        #for file in fileNames[0]:
        #    self.predictorsSelected.append(file)
        #print(self.predictorsSelected)

