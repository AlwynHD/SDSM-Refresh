from PyQt5.QtWidgets import (QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QSizePolicy, QFrame, QLabel, QFileDialog,
                             QLineEdit, QCheckBox)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPalette, QColor, QIcon
from QualityControl import qualityCheck
# Define the name of the module for display in the content area
moduleName = "Quality Control"


class borderedQFrame(QFrame):
    def __init__(self):
        super().__init__()

class resultsQFrame(QFrame):
    '''Wraps two labels, one being aligned to the right of the results frame'''
    def __init__(self, standardLabelText):
        super().__init__()
        self.standardLabel = QLabel(standardLabelText)
        self.contentLabel = QLabel()
        self.contentLabel.setAlignment(Qt.AlignRight)

        self.resultsLayout = QHBoxLayout()
        self.resultsLayout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the layout
        self.resultsLayout.setSpacing(0)  # No spacing between elements
        self.setLayout(self.resultsLayout)  # Apply the layout to the frame

        self.resultsLayout.addWidget(self.standardLabel)
        self.resultsLayout.addWidget(self.contentLabel)


class ContentWidget(QWidget):
    """
    A widget to display the Quality Control screen (UI/UX).
    Includes a buttonBar at the top and a contentArea for displaying details.
    """
    def __init__(self):
        """
        Initialize the Quality Control screen UI/UX, setting up the layout, buttonBar, and contentArea.
        """
        super().__init__()

        self.setStyleSheet("""
                           QFrame{
                                background-color: #D3D3D3;}
                           borderedQFrame{
                                background-color: #D3D3D3;
                                border : 1px solid black;
                                border-top-left-radius : 20px;
                                border-top-right-radius : 20px;
                                border-bottom-left-radius : 20px;
                                border-bottom-right-radius : 20px;}""")
        self.selectedFile = ""
        self.selectedOutlier = ""

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
        buttonNames = ["Reset","Check File", "Daily Stats", "Outliers", "Settings"]  # Names of the buttons for clarity
        for name in buttonNames:
            button = QPushButton(name)  # Create a button with the given name
            button.setIcon(QIcon("placeholder_icon.png"))  # Placeholder icon
            button.clicked.connect(self.handleMenuButtonClicks)
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

        # --- Content Frames ---
        # Frame for the title
        titleFrame = QFrame()
        titleFrame.setFrameShape(QFrame.NoFrame)  # No border around the frame
        titleFrame.setFixedHeight(100)

        # Layout for the title frame
        titleLayout = QVBoxLayout()
        titleLayout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the layout
        titleLayout.setSpacing(0)  # No spacing between elements
        titleFrame.setLayout(titleLayout)  # Apply the layout to the frame

        # Set the background color to light gray
        titleFrame.setStyleSheet("background-color: #D3D3D3;")

        # Add the contentArea frame to the main layout
        mainLayout.addWidget(titleFrame)

        #Frame that holds all content
        contentAreaFrame = QFrame()
        contentAreaFrame.setFrameShape(QFrame.NoFrame)  # No border around the frame
        contentAreaFrame.setBaseSize(600,100)
        contentAreaFrame.setSizePolicy(QSizePolicy.Preferred,QSizePolicy.Expanding)

        # Layout for the contentArea frame
        contentAreaLayout = QHBoxLayout()
        contentAreaLayout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the layout
        contentAreaLayout.setSpacing(10)  # No spacing between elements
        contentAreaFrame.setLayout(contentAreaLayout)  # Apply the layout to the frame

        mainLayout.addWidget(contentAreaFrame)

        #Frame which holds Select file, Pettitt test, Threshold, and Outlier (SPTO) frames
        SPTOFrame = QFrame()
        SPTOFrame.setFrameShape(QFrame.NoFrame)  # No border around the frame
        SPTOFrame.setBaseSize(200,400)
        SPTOFrame.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        

        # Layout for the contentArea frame
        SPTOLayout = QVBoxLayout()
        SPTOLayout.setContentsMargins(10, 10, 10, 10)  # Remove padding from the layout
        SPTOLayout.setSpacing(10)  # No spacing between elements
        SPTOFrame.setLayout(SPTOLayout)  # Apply the layout to the frame
        contentAreaLayout.addWidget(SPTOFrame)

        #Results frame

        resultsFrame = borderedQFrame()
        resultsFrame.setFrameShape(QFrame.StyledPanel)  # No border around the frame
        resultsFrame.setBaseSize(400,400)
        resultsFrame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)


        # Layout for the results frame
        resultsLayout = QVBoxLayout()
        resultsLayout.setContentsMargins(10, 10, 10, 10)  # Remove padding from the layout
        resultsLayout.setSpacing(10)  # No spacing between elements
        resultsFrame.setStyleSheet("background-color: #D3D3D3;")

        resultsFrame.setLayout(resultsLayout)  # Apply the layout to the frame

        contentAreaLayout.addWidget(resultsFrame)

        #Create selectFile frame
        selectFileFrame = borderedQFrame()
        selectFileFrame.setFrameShape(QFrame.StyledPanel)   
        selectFileFrame.setBaseSize(200,100)
        selectFileFrame.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)



        #Layout for selectFile frame
        selectFileLayout = QVBoxLayout()
        selectFileLayout.setContentsMargins(25,25,25,25) #Pad 10 pixels each way
        selectFileLayout.setSpacing(10)  # No spacing between elements
        selectFileFrame.setStyleSheet("background-color: #D3D3D3;")


        selectFileFrame.setLayout(selectFileLayout)
        
        SPTOLayout.addWidget(selectFileFrame)

        #Create pettitt frame
        pettittFrame = borderedQFrame()
        pettittFrame.setFrameShape(QFrame.StyledPanel)   
        pettittFrame.setBaseSize(200,100)
        pettittFrame.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)


        #Layout for pettitt frame
        pettittLayout = QHBoxLayout()
        pettittLayout.setContentsMargins(25,25,25,25) #Pad 10 pixels each way
        pettittLayout.setSpacing(10)  # 10 pixel spacing between elements
        pettittFrame.setStyleSheet("background-color: #D3D3D3;")


        pettittFrame.setLayout(pettittLayout)
        
        SPTOLayout.addWidget(pettittFrame)

        #Create threshold frame
        thresholdFrame = borderedQFrame()
        thresholdFrame.setFrameShape(QFrame.StyledPanel)   
        thresholdFrame.setBaseSize(200,100)
        thresholdFrame.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)


        #Layout for threshold frame
        thresholdLayout = QVBoxLayout()
        thresholdLayout.setContentsMargins(25,25,25,25) #Pad 10 pixels each way
        thresholdLayout.setSpacing(10)  # No spacing between elements
        thresholdFrame.setStyleSheet("background-color: #D3D3D3;")


        thresholdFrame.setLayout(thresholdLayout)
        
        SPTOLayout.addWidget(thresholdFrame)

        #Create outliers frame
        outliersFrame = borderedQFrame()
        outliersFrame.setFrameShape(QFrame.StyledPanel)   
        outliersFrame.setBaseSize(200,100)
        outliersFrame.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)


        #Layout for selectFile frame
        outliersLayout = QVBoxLayout()
        outliersLayout.setContentsMargins(25,25,25,25) #Pad 10 pixels each way
        outliersLayout.setSpacing(10)  # No spacing between elements
        outliersFrame.setStyleSheet("background-color: #D3D3D3;")


        outliersFrame.setLayout(outliersLayout)
        
        SPTOLayout.addWidget(outliersFrame)

        


        # ------------ ACTUAL CONTENT ------------
        # --- Center Label (Placeholder) ---
        # Label to display the name of the module (Quality Control)
        moduleLabel = QLabel(moduleName, self)
        moduleLabel.setStyleSheet("font-size: 24px; color: black;")  # Style the label text
        titleLayout.addWidget(moduleLabel)  # Add the label to the contentArea layout


        selectFileButton = QPushButton("Select File")
        selectFileButton.setObjectName("check file")

        selectFileButton.clicked.connect(self.selectFile)
        selectFileLayout.addWidget(selectFileButton)
        self.selectedFileLabel = QLabel("No file selected")
        selectFileLayout.addWidget(self.selectedFileLabel)

        #Pettitt Test input elements

        pettittLabel = QLabel("Minimum annual data threshold (%)")
        pettittLayout.addWidget(pettittLabel)
        pettittInput = QLineEdit("90")
        pettittLayout.addWidget(pettittInput)

        #Threshold elements

        thresholdCheckBox = QCheckBox("Apply Threshold")
        thresholdLayout.addWidget(thresholdCheckBox)

        #Outliers elements

        #Need a separate frame for the input
        standardDeviationFrame = QFrame()
        standardDeviationFrame.setFrameShape(QFrame.NoFrame)
        standardDeviationFrame.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)

        standardDeviationLayout = QHBoxLayout()
        standardDeviationLayout.setContentsMargins(0,0,0,0)
        standardDeviationLayout.setSpacing(10)

        standardDeviationFrame.setLayout(standardDeviationLayout)

        outliersLayout.addWidget(standardDeviationFrame)

        standardDeviationLabel = QLabel("Standard Deviations: ")
        standardDeviationLayout.addWidget(standardDeviationLabel)
        standardDeviationInput = QLineEdit("0")
        standardDeviationLayout.addWidget(standardDeviationInput)

        selectOutlierFileButton = QPushButton("Select File")
        selectOutlierFileButton.clicked.connect(self.selectFile)
        selectOutlierFileButton.setObjectName("outlier file")
        outliersLayout.addWidget(selectOutlierFileButton)
        self.selectedOutlierLabel = QLabel("No file selected")
        outliersLayout.addWidget(self.selectedOutlierLabel)

        #Results elements, just a lot of labels that need to be referenced from functions
        self.minimumFrame = resultsQFrame("Minimum: ")
        resultsLayout.addWidget(self.minimumFrame)

        self.maximumFrame = resultsQFrame("Maximum: ")
        resultsLayout.addWidget(self.maximumFrame)

        self.meanFrame = resultsQFrame("Mean: ")
        resultsLayout.addWidget(self.meanFrame)

        self.numOfValuesFrame = resultsQFrame("Number of values in file: ")
        resultsLayout.addWidget(self.numOfValuesFrame)

        self.missingFrame = resultsQFrame("Missing values: ")
        resultsLayout.addWidget(self.missingFrame)

        self.numOfOKValuesFrame = resultsQFrame("Number of values ok: ")
        resultsLayout.addWidget(self.numOfOKValuesFrame)

        self.maximumDifferenceFrame = resultsQFrame("Maximum difference: ")
        resultsLayout.addWidget(self.maximumDifferenceFrame)

        self.maximumDifferenceValOneFrame = resultsQFrame("Maximum difference value 1: ")
        resultsLayout.addWidget(self.maximumDifferenceValOneFrame)

        self.maximumDifferenceValTwoFrame = resultsQFrame("Maximum difference value 2: ")
        resultsLayout.addWidget(self.maximumDifferenceValTwoFrame)

        self.valueOverThreshFrame = resultsQFrame("Values over threshold: ")
        resultsLayout.addWidget(self.valueOverThreshFrame)

        self.pettittSigFrame = resultsQFrame("Pettitt test (significance): ")
        resultsLayout.addWidget(self.pettittSigFrame)

        self.pettittMaxFrame = resultsQFrame("Pettitt max position: ")
        resultsLayout.addWidget(self.pettittMaxFrame)

        self.missingValCodeFrame = resultsQFrame("Missing value code: ")
        resultsLayout.addWidget(self.missingValCodeFrame)

        self.eventThreshFrame = resultsQFrame("Event threshold: ")
        resultsLayout.addWidget(self.eventThreshFrame)




       
        # Add a spacer to ensure content is properly spaced
        titleLayout.addStretch()
        contentAreaLayout.addStretch()

    def selectFile(self):
        #Don't know which files it needs to get, will figure out later
        
        #Update correct label depending on button pressed
        if self.sender().objectName() == "check file":
            fileName = QFileDialog.getOpenFileName(self, "Select file", 'predictand files', "DAT Files (*.DAT)")
            self.selectedFile= self.updateLabels(self.selectedFileLabel, fileName[0])
        elif self.sender().objectName() == "outlier file":
            fileName = QFileDialog.getOpenFileName(self, "Select file", 'SDSM-REFRESH', "Text Files (*.txt)")
            self.selectedOutlier = self.updateLabels(self.selectedOutlierLabel, fileName[0])

    def updateLabels(self, label, fileName):
        #Updates label passed to it with file name
        if fileName != '':
            label.setText("Selected file: "+fileName.split("/")[-1])
            return fileName
        else:
            label.setText("No file selected")
            return ""
    
    def handleMenuButtonClicks(self):
        button = self.sender().text()
        if button == "Check File":
            #https://www.youtube.com/watch?v=QY4KKG4TBFo im keeping this in the comments
            print("https://www.youtube.com/watch?v=QY4KKG4TBFo") #Are easter eggs allowed?

            min, max, count, missing, mean = qualityCheck(self.selectedFile)
            self.minimumFrame.contentLabel.setText(min)
            self.maximumFrame.contentLabel.setText(max)
            self.meanFrame.contentLabel.setText(mean)
            self.numOfValuesFrame.contentLabel.setText(count)
            self.missingFrame.contentLabel.setText(missing)
            
        else:
            print("work in progress, pardon our dust")
