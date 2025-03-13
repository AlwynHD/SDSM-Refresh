from PyQt5.QtWidgets import (QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QSizePolicy, 
                             QFrame, QLabel, QFileDialog, QScrollArea, QDateEdit, QCheckBox,
                             QButtonGroup, QRadioButton, QLineEdit, QGroupBox, QMessageBox,
                             )
import pyqtgraph as pg
from PyQt5.QtCore import Qt, QSize, QDate
from PyQt5.QtGui import QPalette, QColor, QIcon
from src.lib.ScreenVars import correlation, analyseData, filesNames, scatterPlot
from os import listdir
from datetime import datetime, date

# Define the name of the module for display in the content area
moduleName = "Screen Variables"

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

        # Frame for the contentArea
        titleFrame = QFrame()
        titleFrame.setFrameStyle(QFrame.NoFrame)  # No border around the frame
        titleFrame.setBaseSize(100,50)
        titleFrame.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Maximum)

        # Layout for the contentArea frame
        titleLayout = QVBoxLayout()
        titleLayout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the layout
        titleLayout.setSpacing(0)  # No spacing between elements
        titleFrame.setLayout(titleLayout)  # Apply the layout to the frame

        

        # Set the background color to light gray
        titleFrame.setStyleSheet("background-color: #F0F0F0;")

        # Add the title frame to the main layout
        mainLayout.addWidget(titleFrame)
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
        fileDateFrame = QFrame()
        fileDateFrame.setFrameStyle(QFrame.NoFrame)  # No border around the frame
        fileDateFrame.setBaseSize(200,500)
        fileDateFrame.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)

        fileDateLayout = QVBoxLayout()
        fileDateLayout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the layout
        fileDateLayout.setSpacing(10)  # No spacing between elements
        fileDateFrame.setLayout(fileDateLayout)  # Apply the layout to the frame

        contentAreaLayout.addWidget(fileDateFrame)

        #Create selectPredictandFile frame
        selectPredictandFileFrame = borderedQGroupBox("Select Predictand")
        selectPredictandFileFrame.setBaseSize(200,200)
        selectPredictandFileFrame.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)


        #Layout for selectPredictandFile frame
        selectPredictandFileLayout = QVBoxLayout()
        selectPredictandFileLayout.setContentsMargins(25,25,25,25) #Pad 10 pixels each way
        selectPredictandFileLayout.setSpacing(0)  # No spacing between elements


        selectPredictandFileFrame.setLayout(selectPredictandFileLayout)
        
        fileDateLayout.addWidget(selectPredictandFileFrame)

        #Create selectDate Frame
        selectDateFrame = borderedQGroupBox("Select Start/End Date")
        selectDateFrame.setBaseSize(200,200)
        selectDateFrame.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)


        selectDateLayout = QVBoxLayout()
        selectDateLayout.setContentsMargins(25, 25, 25, 25)  # Remove padding from the layout
        selectDateLayout.setSpacing(0)  # No spacing between elements
        selectDateFrame.setLayout(selectDateLayout)  # Apply the layout to the frame

        fileDateLayout.addWidget(selectDateFrame)

        #Horizontal frames needed in selectDateFrame for labels to be attached to date selectors

        fitStartDateFrame = QFrame()
        fitStartDateFrame.setFrameStyle(QFrame.NoFrame) 
        fitStartDateFrame.setBaseSize(190,50)
        fitStartDateFrame.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)

        fitStartDateLayout = QHBoxLayout()
        fitStartDateLayout.setContentsMargins(25, 25, 25, 25)  # 10 Pixel padding
        fitStartDateLayout.setSpacing(0)  # No spacing between elements
        fitStartDateFrame.setLayout(fitStartDateLayout)  # Apply the layout to the frame

        fitEndDateFrame = QFrame()
        fitEndDateFrame.setFrameStyle(QFrame.NoFrame) 
        fitEndDateFrame.setBaseSize(190,50)
        fitEndDateFrame.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)

        fitEndDateLayout = QHBoxLayout()
        fitEndDateLayout.setContentsMargins(25, 25, 25, 25)  # 10 Pixel padding
        fitEndDateLayout.setSpacing(0)  # No spacing between elements
        fitEndDateFrame.setLayout(fitEndDateLayout)  # Apply the layout to the frame

        selectDateLayout.addWidget(fitStartDateFrame)
        selectDateLayout.addWidget(fitEndDateFrame)





        #Create selectPredictor frame
        selectPredictorsFrame = borderedQGroupBox("Select Predictors")
        selectPredictorsFrame.setBaseSize(200,400)
        selectPredictorsFrame.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)



        #Layout for selectPredictors frame
        selectPredictorsLayout = QVBoxLayout()
        selectPredictorsLayout.setContentsMargins(25, 25, 25, 25) #Pad 10 pixels each way
        selectPredictorsLayout.setSpacing(0)  # No spacing between elements


        selectPredictorsFrame.setLayout(selectPredictorsLayout)
        
        contentAreaLayout.addWidget(selectPredictorsFrame)

        #Create description, autoregression, process, significance (DARPS) frame
        selectDARPSFrame = QFrame()
        selectDARPSFrame.setFrameStyle(QFrame.NoFrame)  # No border around the frame
        selectDARPSFrame.setBaseSize(200,500)
        selectDARPSFrame.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)

        #Create DARPS Layout

        selectDARPSLayout = QVBoxLayout()
        selectDARPSLayout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the layout
        selectDARPSLayout.setSpacing(10)  # No spacing between elements
        selectDARPSFrame.setLayout(selectDARPSLayout)  # Apply the layout to the frame

        contentAreaLayout.addWidget(selectDARPSFrame)

        #Create predictorDescription frame
        predictorDescriptionFrame = borderedQGroupBox("Predictor Description")
        predictorDescriptionFrame.setBaseSize(200,100)
        predictorDescriptionFrame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)


        #Layout for predictorDescription frame
        predictorDescriptionLayout = QVBoxLayout()
        predictorDescriptionLayout.setContentsMargins(25, 25, 25, 25) #Pad 10 pixels each way
        predictorDescriptionLayout.setSpacing(0)  # No spacing between elements
        predictorDescriptionFrame.setLayout(predictorDescriptionLayout)

        selectDARPSLayout.addWidget(predictorDescriptionFrame)

        #Create autoregression frame
        autoregressionFrame = borderedQGroupBox("Autoregression")
        autoregressionFrame.setBaseSize(200,100)
        autoregressionFrame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)


        #Layout for autoregression frame
        autoregressionLayout = QVBoxLayout()
        autoregressionLayout.setContentsMargins(25, 25, 25, 25) #Pad 10 pixels each way
        autoregressionLayout.setSpacing(0)  # No spacing between elements
        autoregressionFrame.setLayout(autoregressionLayout)

    

        selectDARPSLayout.addWidget(autoregressionFrame)

        #Create process frame
        processFrame = borderedQGroupBox("Process")
        processFrame.setBaseSize(200,100)
        processFrame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)


        #Layout for process frame
        processLayout = QVBoxLayout()
        processLayout.setContentsMargins(25, 25, 25, 25) #Pad 10 pixels each way
        processLayout.setSpacing(0)  # No spacing between elements
        processFrame.setLayout(processLayout)


        selectDARPSLayout.addWidget(processFrame)

        #Create significance frame
        significanceFrame = borderedQGroupBox("Significance")
        significanceFrame.setBaseSize(200,100)
        significanceFrame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)


        #Layout for significance frame
        significanceLayout = QVBoxLayout()
        significanceLayout.setContentsMargins(25, 25, 25, 25) #Pad 10 pixels each way
        significanceLayout.setSpacing(0)  # No spacing between elements
        significanceFrame.setLayout(significanceLayout)


        selectDARPSLayout.addWidget(significanceFrame)


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
        selectPredictandButton = QPushButton("📂 Select Predictand File")
        selectPredictandButton.clicked.connect(self.selectPredictandButtonClicked)
        selectPredictandFileLayout.addWidget(selectPredictandButton)

        self.selectPredictandLabel = QLabel("No predictand selected")
        selectPredictandFileLayout.addWidget(self.selectPredictandLabel)

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
        predictorsScrollLayout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the layout
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
        
            predictorScrollLabelButton.clicked.connect(self.predictorLabelClicked)
            predictorScrollLabelButton.setBaseSize(200, 20)
            predictorScrollLabelButton.setStyleSheet("color: black; background-color: #F0F0F0")
            predictorScrollLabelButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            predictorsScrollLayout.addWidget(predictorScrollLabelButton) 
        
        predictorsScrollArea.setWidget(predictorsScrollFrame)


        #Create a date edit box in the fitStart frame to choose start fit date

        fitStartDateLabel = QLabel("Fit Start:")
        fitStartDateLayout.addWidget(fitStartDateLabel)
        self.fitStartDateChooser = QDateEdit(calendarPopup=True)
        self.fitStartDateChooser.setDate(QDate(1948,1,1))
        self.fitStartDateChooser.setMinimumWidth(100)

        fitStartDateLayout.addWidget(self.fitStartDateChooser)

        #Create a date edit box in the fitEnd frame to choose start fit date

        fitEndDateLabel = QLabel("Fit End:")
        fitEndDateLayout.addWidget(fitEndDateLabel)
        self.fitEndDateChooser = QDateEdit(calendarPopup=True)
        self.fitEndDateChooser.setMinimumWidth(100)
        self.fitEndDateChooser.setDate(QDate(2015,12,31))
        fitEndDateLayout.addWidget(self.fitEndDateChooser)

        #Create a label that gets updated on predictandButtonClick
        self.predictorDescriptionLabel = QLabel("No predictor selected")
        predictorDescriptionLayout.addWidget(self.predictorDescriptionLabel)

        #Autoregression Button
        autoregressionLabel = QLabel("Autoregression")
        autoregressionLayout.addWidget(autoregressionLabel)

        self.autoregressionCheckBox = QCheckBox("Autoregressive Term")
        autoregressionLayout.addWidget(self.autoregressionCheckBox)

        #Process radio buttons
        processRadioButtonGroup = QButtonGroup()
        processRadioButtonGroup.setExclusive(True)
        unconditionalRadioButton = QRadioButton("Unconditional")
        unconditionalRadioButton.setChecked(True)
        conditionalRadioButton = QRadioButton("Conditional")
        conditionalRadioButton.setStyleSheet("QRadioButton::indicator{;width:14px;height:14px;border-radius:8px;}QRadioButton::indicator::checked{background-color: #FF00A0;border:1px solid grey;}QRadioButton::indicator::unchecked{background-color: white;border:1px solid grey}")
        processRadioButtonGroup.addButton(unconditionalRadioButton)
        processRadioButtonGroup.addButton(conditionalRadioButton)

        processLayout.addWidget(unconditionalRadioButton)
        processLayout.addWidget(conditionalRadioButton)

        #Significance input

        significanceLabel = QLabel("Significance")
        significanceLayout.addWidget(significanceLabel)
        significanceInput = QLineEdit("0.05")
        significanceLayout.addWidget(significanceInput)

        correlationButton = QPushButton("Correlation")
        correlationButton.clicked.connect(self.doCorrelation)
        correlationButton.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")

        buttonLayout.addWidget(correlationButton)

        analyseButton = QPushButton("Analyse")
        #analyseButton.clicked.connect(self.doCorrelation)
        analyseButton.setStyleSheet("background-color: #1FC7F5; color: white; font-weight: bold")

        buttonLayout.addWidget(analyseButton)

        scatterButton = QPushButton("Scatter")
        scatterButton.clicked.connect(self.showScatterGraph)
        scatterButton.setStyleSheet("background-color: #F57F0C; color: white; font-weight: bold")
        buttonLayout.addWidget(scatterButton)



        # Add a spacer to ensure content is properly spaced
        
        #titleLayout.addStretch()
        #contentAreaLayout.addStretch()
    def doCorrelation(self):
        #Get dates
        fitStartDate = self.QDateEditToDateTime(self.fitStartDateChooser)


        fitEndDate = self.QDateEditToDateTime(self.fitEndDateChooser)

        if fitEndDate <= fitStartDate:
            return displayBox("Date Error","End date cannot be before start date.","Error",isError=True)
            

        #Get autoregression state
        autoregression = self.autoregressionCheckBox.isChecked()

        #Perform correlation
        print(["predictor files/"+predictor for predictor in self.predictorsSelected])
        data = correlation([self.predictandSelected], [predictor for predictor in self.predictorsSelected], fitStartDate, fitEndDate, autoregression)

        if data == "Predictand Error":
            return displayBox("Predictand Error","No predictand file selected.","Error",isError=True)
        elif data == "Predictor Error":
            return displayBox("Predictor Error",
                              "There can only be between one and twelve predictor files selected.",
                              "Error",isError=True)

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
        button = self.sender() #Get the buttonLabel that was clicked
        predictor = button.text() #Get the name of the buttonLabel, so the predictor file
        if (self.predictorPath+"/"+predictor) not in self.predictorsSelected:
            self.predictorsSelected.append(self.predictorPath+"/"+predictor)
            button.setStyleSheet("color: white; background-color: blue")
        else:
            self.predictorsSelected.remove(self.predictorPath+"/"+predictor)
            button.setStyleSheet("color: black; background-color: #F0F0F0")
        try:
            predictorDescription = filesNames(predictor)
            self.predictorDescriptionLabel.setText(predictorDescription[0])

        except IndexError:
            self.predictorDescriptionLabel.setText("Description not found")
        
    


    def QDateEditToDateTime(self, dateEdit):
        rawStartDate = dateEdit.date()
        dateTime = rawStartDate.toPyDate()
        return dateTime
    
    def showScatterGraph(self):
        print()
        fitStartDate = self.QDateEditToDateTime(self.fitStartDateChooser)
        fitEndDate = self.QDateEditToDateTime(self.fitEndDateChooser)

        if fitEndDate <= fitStartDate:
            return displayBox("Date Error","End date cannot be before start date.","Error",isError=True)

        autoregression = self.autoregressionCheckBox.isChecked()
        print(self.predictandSelected)
        print(self.predictorsSelected)
        data = scatterPlot([self.predictandSelected], self.predictorsSelected, fitStartDate,fitEndDate,fitStartDate,fitEndDate, autoregression)
        print(data)
        if data == "Predictand Error":
            return displayBox("Predictand Error","No predictand file selected.","Error",isError=True)
        elif data == "Predictor Error":
            return displayBox("Predictor Error",
                              "You must have only one predictor selected when autoregressive term is not checked. If autoregressive term is checked, no predictors should be selected.",
                              "Error",isError=True)
        plot = pg.plot()
        scatter = pg.ScatterPlotItem(size=10, brush=pg.mkBrush(255, 255, 255, 120))
        print(data.size)
        spots = [{'pos': [data[1,i],data[0,i]]}
                 for i in range(int(data.size/2))]
        scatter.addPoints(spots)
        plot.addItem(scatter)

