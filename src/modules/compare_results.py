from PyQt5.QtWidgets import (QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QSizePolicy, 
                             QFrame, QLabel, QFileDialog, QScrollArea, QDateEdit, QCheckBox,
                             QButtonGroup, QRadioButton, QLineEdit, QGroupBox, QMessageBox,
                             QApplication, QComboBox
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
    def __init__(self,args):
        super().__init__(args)

class comparedFileBox(borderedQGroupBox):
    def __init__(self,args):
        super().__init__(args)
        self.fileSelected = ""
        layout = QVBoxLayout()
        layout.setContentsMargins(0,25,0,25)
        layout.setSpacing(25)
        self.setLayout(layout)

        fileFrame = QFrame()
        fileFrame.setFrameStyle(QFrame.NoFrame)
        fileLayout = QVBoxLayout()
        fileFrame.setLayout(fileLayout)
        fileButton = QPushButton("Select First File")
        fileButton.setContentsMargins(25,25,25,25)
        fileButton.setMaximumWidth(200)
        fileLayout.addWidget(fileButton)
        self.fileLabel = QLabel("File: Not Selected")
        self.fileLabel.setContentsMargins(25,25,25,25)
        fileLayout.addWidget(self.fileLabel)

        fileLayout.setAlignment(Qt.AlignHCenter)
        layout.addWidget(fileFrame)

        spacerFrame = QFrame()
        spacerFrame.setFrameShape(QFrame.HLine|QFrame.Sunken)
        layout.addWidget(spacerFrame)


        statsLabel = QLabel("Select Statistic")
        statsLabel.setContentsMargins(25,0,25,0)
        layout.addWidget(statsLabel)

        selectStatsFrame = QFrame()
        selectStatsFrame.setFrameStyle(QFrame.NoFrame)
        selectStatsLayout = QVBoxLayout()
        selectStatsLayout.setContentsMargins(25, 0, 25, 0) #Pad 10 pixels each way
        selectStatsLayout.setSpacing(10)  # No spacing between elements
        selectStatsFrame.setLayout(selectStatsLayout)

        statsScrollArea = QScrollArea()
        statsScrollArea.setWidgetResizable(True)
        statsScrollFrame = QFrame()
        
        statsScrollFrame.setFrameStyle(QFrame.NoFrame)  # No border around the frame
        
        #predictorsScrollFrame.setBaseSize(200,300)
        #predictorsScrollFrame.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Fixed)


        self.statsScrollLayout = QVBoxLayout()
        self.statsScrollLayout.setSpacing(0)  # No spacing between elements
        self.statsScrollLayout.setAlignment(Qt.AlignHCenter)
        statsScrollFrame.setLayout(self.statsScrollLayout)  # Apply the layout to the frame


        selectStatsLayout.addWidget(statsScrollArea)

        #Get all predictors and populate scroll frame
        
        statsScrollArea.setWidget(statsScrollFrame)

        layout.addWidget(selectStatsFrame)






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




        # --- Content Area ---

        '''


        '''
        contentAreaFrame = QFrame()
        contentAreaFrame.setFrameStyle(QFrame.NoFrame)  # No border around the frame
        contentAreaFrame.setBaseSize(600,100)
        contentAreaFrame.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)

        # Layout for the contentArea frame
        contentAreaLayout = QHBoxLayout()
        contentAreaLayout.setContentsMargins(25, 25, 25, 25)  # Remove padding from the layout
        contentAreaLayout.setSpacing(10)  # No spacing between elements
        contentAreaFrame.setLayout(contentAreaLayout)  # Apply the layout to the frame

        mainLayout.addWidget(contentAreaFrame)

        #Frame that holds the selectPredictand frame and the selectDate frame
        
    
        fileOneFrame = comparedFileBox("Input File One")
        
        contentAreaLayout.addWidget(fileOneFrame)
        

        fileTwoFrame = comparedFileBox("Input File Two")
        contentAreaLayout.addWidget(fileTwoFrame)

        buttonFrame = QFrame()
        buttonFrame.setBaseSize(600,60)
        buttonFrame.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Fixed)

        buttonLayout = QHBoxLayout()
        buttonLayout.setContentsMargins(25,25,25,25)
        buttonLayout.setSpacing(10)

        buttonFrame.setLayout(buttonLayout)

        mainLayout.addWidget(buttonFrame)
        


        # ------------ ACTUAL CONTENT ------------
        # Label to display the name of the module (Screen Variables)
        '''moduleLabel = QLabel(moduleName, self)
        moduleLabel.setStyleSheet("font-size: 24px; color: black;")  # Style the label text
        titleLayout.addWidget(moduleLabel)  # Add the label to the contentArea layout '''


        

        #Predictand file selector button
       
        correlationButton = QPushButton("Compare")
        correlationButton.clicked.connect(self.goCompare)
        correlationButton.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")

        buttonLayout.addWidget(correlationButton)



        # Add a spacer to ensure content is properly spaced
        
        #titleLayout.addStretch()
        #contentAreaLayout.addStretch()

    def goCompare(self):
        print()

    def QDateEditToDateTime(self, dateEdit):
        rawStartDate = dateEdit.date()
        dateTime = rawStartDate.toPyDate()
        return dateTime
    
    