from PyQt5.QtWidgets import (QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QSizePolicy, QFrame, QLabel, QFileDialog,
                             QLineEdit, QCheckBox, QMessageBox, QGroupBox)
from PyQt5.QtCore import Qt
import threading
import time
# Define the name of the module for display in the content area
moduleName = "Quality Control"

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

class ThreadWithReturnValue(threading.Thread):
    
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs={}, Verbose=None):
        threading.Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None

    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args,
                                                **self._kwargs)
            return self._return
 
        

class borderedQGroupBox(QGroupBox):
    def __init__(self,args):
        super().__init__(args)


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
                                border-bottom-right-radius : 20px;}""")

        self.selectedFile = ""
        self.selectedOutlier = ""

        # Main layout for the entire widget
        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the layout
        mainLayout.setSpacing(0)  # No spacing between elements
        self.setLayout(mainLayout)  # Apply the main layout to the widget



        # --- Content Frames ---
        # Frame for the title
        '''titleFrame = QFrame()
        titleFrame.setFrameShape(QFrame.NoFrame)  # No border around the frame
        titleFrame.setBaseSize(10,50)
        titleFrame.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Maximum)

        # Layout for the title frame
        titleLayout = QVBoxLayout()
        titleLayout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the layout
        titleLayout.setSpacing(0)  # No spacing between elements
        titleFrame.setLayout(titleLayout)  # Apply the layout to the frame

        # Set the background color to light gray
        titleFrame.setStyleSheet("background-color: #F0F0F0;")

        # Add the contentArea frame to the main layout
        mainLayout.addWidget(titleFrame)'''

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

        resultsFrame = borderedQGroupBox("Results")
        resultsFrame.setBaseSize(400,400)
        resultsFrame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)


        # Layout for the results frame
        resultsLayout = QVBoxLayout()
        resultsLayout.setContentsMargins(25, 25, 25, 25) 
        resultsLayout.setSpacing(10)  # No spacing between elements

        resultsFrame.setLayout(resultsLayout)  # Apply the layout to the frame

        contentAreaLayout.addWidget(resultsFrame)

        #Create selectFile frame
        selectFileFrame = borderedQGroupBox("Select File")
        selectFileFrame.setBaseSize(200,100)
        selectFileFrame.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)



        #Layout for selectFile frame
        selectFileLayout = QVBoxLayout()
        selectFileLayout.setContentsMargins(25,25,25,25) #Pad 10 pixels each way
        selectFileLayout.setSpacing(10)  # No spacing between elements


        selectFileFrame.setLayout(selectFileLayout)
        
        SPTOLayout.addWidget(selectFileFrame)

        #Create pettitt frame
        pettittFrame = borderedQGroupBox("Pettitt Test")
        pettittFrame.setBaseSize(200,100)
        pettittFrame.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)


        #Layout for pettitt frame
        pettittLayout = QHBoxLayout()
        pettittLayout.setContentsMargins(25,25,25,25) #Pad 10 pixels each way
        pettittLayout.setSpacing(10)  # 10 pixel spacing between elements


        pettittFrame.setLayout(pettittLayout)
        
        SPTOLayout.addWidget(pettittFrame)

        #Create threshold frame
        thresholdFrame = borderedQGroupBox("Threshold")
        thresholdFrame.setBaseSize(200,100)
        thresholdFrame.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)


        #Layout for threshold frame
        thresholdLayout = QVBoxLayout()
        thresholdLayout.setContentsMargins(25,25,25,25) #Pad 10 pixels each way
        thresholdLayout.setSpacing(10)  # No spacing between elements


        thresholdFrame.setLayout(thresholdLayout)
        
        SPTOLayout.addWidget(thresholdFrame)

        #Create outliers frame
        outliersFrame = borderedQGroupBox("Outliers")
        outliersFrame.setBaseSize(200,100)
        outliersFrame.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)


        #Layout for selectFile frame
        outliersLayout = QVBoxLayout()
        outliersLayout.setContentsMargins(25,25,25,25) #Pad 10 pixels each way
        outliersLayout.setSpacing(10)  # No spacing between elements


        outliersFrame.setLayout(outliersLayout)
        
        SPTOLayout.addWidget(outliersFrame)

        buttonFrame = QFrame()
        buttonFrame.setBaseSize(600,60)
        buttonFrame.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Fixed)

        buttonLayout = QHBoxLayout()
        buttonLayout.setContentsMargins(25,25,25,25)
        buttonLayout.setSpacing(10)

        buttonFrame.setLayout(buttonLayout)

        mainLayout.addWidget(buttonFrame)
        


        # ------------ ACTUAL CONTENT ------------
        # --- Center Label (Placeholder) ---
        # Label to display the name of the module (Quality Control)
        '''moduleLabel = QLabel(moduleName, self)
        moduleLabel.setStyleSheet("font-size: 24px; color: black;")  # Style the label text
        titleLayout.addWidget(moduleLabel)  # Add the label to the contentArea layout'''


        selectFileButton = QPushButton("📂 Select File")
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

        selectOutlierFileButton = QPushButton("📂 Select File")
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

        checkFileButton = QPushButton("Check File")
        checkFileButton.clicked.connect(self.checkFile)
        checkFileButton.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")

        buttonLayout.addWidget(checkFileButton)

        dailyStatsButton = QPushButton("Daily Stats")
        dailyStatsButton.clicked.connect(self.getDailyStats)
        dailyStatsButton.setStyleSheet("background-color: #1FC7F5; color: white; font-weight: bold")

        buttonLayout.addWidget(dailyStatsButton)

        self.outliersButton = QPushButton("Outliers")
        
        self.outliersButton.clicked.connect(self.doOutliers)
        self.outliersButton.setStyleSheet("background-color: #F57F0C; color: white; font-weight: bold")
        buttonLayout.addWidget(self.outliersButton)

        



       
        # Add a spacer to ensure content is properly spaced
        #titleLayout.addStretch()
        #contentAreaLayout.addStretch()

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
    
    def checkFile(self):
        #https://www.youtube.com/watch?v=QY4KKG4TBFo im keeping this in the comments
        from src.lib.QualityControl import qualityCheck
        print("https://www.youtube.com/watch?v=QY4KKG4TBFo") #Are easter eggs allowed?
        try:
            min, max, count, missing, mean, maxDiff,maxDiff1, maxDiff2,threshCount, pettitt, pettitMaxPos, globalMissingCount, thresh = qualityCheck(self.selectedFile)
            self.minimumFrame.contentLabel.setText(min)
            self.maximumFrame.contentLabel.setText(max)
            self.meanFrame.contentLabel.setText(mean)
            self.numOfValuesFrame.contentLabel.setText(count+missing)
            self.missingFrame.contentLabel.setText(missing)
            self.numOfOKValuesFrame.contentLabel.setText(count)
            self.maximumDifferenceFrame.contentLabel.setText(maxDiff)
            self.maximumDifferenceValOneFrame.contentLabel.setText(maxDiff1)
            self.maximumDifferenceValTwoFrame.contentLabel.setText(maxDiff2)
            self.valueOverThreshFrame.contentLabel.setText(threshCount)
            self.pettittSigFrame.contentLabel.setText(pettitt)
            self.pettittMaxFrame.contentLabel.setText(pettitMaxPos)
            self.missingValCodeFrame.contentLabel.setText(globalMissingCount)
            self.eventThreshFrame.contentLabel.setText(thresh)
            
        except FileNotFoundError:
            displayBox("File Error", "Please ensure a predictand file is selected and exists.","Error", isError=True)

    def getDailyStats(self):
        from src.lib.QualityControl import dailyMeans
        try:
            stats = dailyMeans(self.selectedFile)
            displayBox("Daily Stats:", stats, "Daily Results")
        except FileNotFoundError:
            displayBox("File Error", "Please ensure a predictand file is selected and exists.", "Error", isError=True)
    def doOutliers(self):
        proc = ThreadWithReturnValue(target=self.checkOutliers)
        proc.daemon = True
        proc.start()
        

    def checkOutliers(self):
        self.outliersButton.setText("Calculating")
        from src.lib.QualityControl import outliersID
        try:
            message= outliersID(self.selectedFile, self.selectedOutlier)
            self.outliersButton.setText("Outliers")
            print("message in checkOutliers=",message)
            #proc = threading.Thread(target=displayBox, args=("Outliers Identified", message, "Outlier Results"))
            #proc.start()
            #displayBox("Outliers Identified", message, "Outlier Results")

            self.outliersButton.setText(message)
            time.sleep(5)
            self.outliersButton.setText("Outliers")

        except FileNotFoundError:
            self.outliersButton.setText("Outliers")
    


