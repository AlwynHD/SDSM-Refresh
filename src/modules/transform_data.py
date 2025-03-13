from PyQt5.QtWidgets import (QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QSizePolicy, 
                             QFrame, QLabel, QFileDialog, QScrollArea, QDateEdit, QCheckBox,
                             QButtonGroup, QRadioButton, QLineEdit, QGroupBox, QMessageBox)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QPalette, QColor, QIcon
from src.lib.TransformData import *
from src.lib.utils import loadFilesIntoMemory

# Define the name of the module for display in the content area
moduleName = "Transform Data"

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

class labeledQLineEditFrame(QFrame):
    def __init__(self,labelVal,lineEditVal):
        super().__init__()
        layout = QHBoxLayout()
        label = QLabel(labelVal)
        self.lineEdit = QLineEdit(lineEditVal)
        layout.addWidget(label)
        layout.addWidget(self.lineEdit)
        self.setLayout(layout)
    def getLineEditVal(self):
        return self.lineEdit.text()
    




class ContentWidget(QWidget):
    """
    A widget to display the Transform Data screen (UI/UX).
    Includes a buttonBar at the top and a contentArea for displaying details.
    """
    def __init__(self):
        """
        Initialize the Transform Data screen UI/UX, setting up the layout, buttonBar, and contentArea.
        """
        super().__init__()

        self.predictorPath = 'predictor files'

        self.inputSelected = ""
        self.outputSelected = ""

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


        # --- Frame Area ---

        contentAreaFrame = QFrame()
        contentAreaFrame.setFrameStyle(QFrame.NoFrame)  # No border around the frame
        contentAreaFrame.setBaseSize(600,100)
        contentAreaFrame.setSizePolicy(QSizePolicy.Preferred,QSizePolicy.Expanding)

        # Layout for the contentArea frame
        contentAreaLayout = QHBoxLayout()
        contentAreaLayout.setContentsMargins(25, 25, 25, 25)  # Remove padding from the layout
        contentAreaLayout.setSpacing(10)  # No spacing between elements
        contentAreaFrame.setLayout(contentAreaLayout)  # Apply the layout to the frame

        mainLayout.addWidget(contentAreaFrame)

        #Frame to hold Input file, Columns in input file, SIM file, Ensemble member, Threshold, OUT File (ICSETO)
        selectICSETOFrame = QFrame()
        selectICSETOFrame.setFrameStyle(QFrame.NoFrame)
        selectICSETOFrame.setBaseSize(200,500)
        selectICSETOFrame.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)

        selectICSETOLayout = QVBoxLayout()
        selectICSETOLayout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the layout
        selectICSETOLayout.setSpacing(10)  # No spacing between elements
        selectICSETOFrame.setLayout(selectICSETOLayout) 
        
        contentAreaLayout.addWidget(selectICSETOFrame)

        #Create selectInputFile frame
        selectInputFileFrame = borderedQGroupBox("Select Input File")
        selectInputFileFrame.setBaseSize(200,200)

        #Layout for selectInputFile frame
        selectInputFileLayout = QVBoxLayout()
        selectInputFileLayout.setContentsMargins(25,25,25,25) #Pad 10 pixels each way
        selectInputFileLayout.setSpacing(0)  # No spacing between elements


        selectInputFileFrame.setLayout(selectInputFileLayout)
        
        selectICSETOLayout.addWidget(selectInputFileFrame)

        columnFrame = borderedQGroupBox("Columns in Input File")
        columnFrame.setBaseSize(200,200)

        columnLayout = QHBoxLayout()
        columnLayout.setContentsMargins(25,25,25,25)
        columnLayout.setSpacing(0)

        columnFrame.setLayout(columnLayout)

        selectICSETOLayout.addWidget(columnFrame)

        simFrame = borderedQGroupBox("Create SIM File")
        simFrame.setBaseSize(200,200)

        simLayout = QHBoxLayout()
        simLayout.setContentsMargins(25,25,25,25)
        simLayout.setSpacing(0)

        simFrame.setLayout(simLayout)

        selectICSETOLayout.addWidget(simFrame)

        ensembleFrame = borderedQGroupBox("Extract Ensemble Member")
        ensembleFrame.setBaseSize(200,200)

        ensembleLayout = QHBoxLayout()
        ensembleLayout.setContentsMargins(25,25,25,25)
        ensembleLayout.setSpacing(0)

        ensembleFrame.setLayout(ensembleLayout)

        selectICSETOLayout.addWidget(ensembleFrame)

        thresholdFrame = borderedQGroupBox("Threshold")
        thresholdFrame.setBaseSize(200,200)

        thresholdLayout = QHBoxLayout()
        thresholdLayout.setContentsMargins(25,25,25,25)
        thresholdLayout.setSpacing(0)

        thresholdFrame.setLayout(thresholdLayout)

        selectICSETOLayout.addWidget(thresholdFrame)

        outputFrame = borderedQGroupBox("Create .OUT File ")
        outputFrame.setBaseSize(200,200)

        outputLayout = QHBoxLayout()
        outputLayout.setContentsMargins(25,25,25,25)
        outputLayout.setSpacing(0)

        outputFrame.setLayout(outputLayout)

        selectICSETOLayout.addWidget(outputFrame)

        transformationFrame = borderedQGroupBox("Transformation")
        transformationFrame.setBaseSize(200,500)
        transformationFrame.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)

        transformationLayout = QVBoxLayout()
        transformationLayout.setContentsMargins(0, 25, 0, 25)  # Remove padding from the layout
        transformationLayout.setSpacing(10)  # No spacing between elements
        transformationFrame.setLayout(transformationLayout)  # Apply the layout to the frame

        contentAreaLayout.addWidget(transformationFrame)

        #selectOPBOFrame, Output file, Pad data, Box, Outliers (OPBO)
        selectOPBOFrame = QFrame()
        selectOPBOFrame.setFrameStyle(QFrame.NoFrame)  # No border around the frame
        selectOPBOFrame.setBaseSize(200,500)
        selectOPBOFrame.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)

        selectOPBOLayout = QVBoxLayout()
        selectOPBOLayout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the layout
        selectOPBOLayout.setSpacing(10)  # No spacing between elements
        selectOPBOFrame.setLayout(selectOPBOLayout)  # Apply the layout to the frame

        contentAreaLayout.addWidget(selectOPBOFrame)

        #Select Output File
        selectOutputFileFrame = borderedQGroupBox("Select Output File")
        selectOutputFileFrame.setBaseSize(200,200)


        #Layout for selectPredictandFile frame
        selectOutputFileLayout = QVBoxLayout()
        selectOutputFileLayout.setContentsMargins(25,25,25,25) #Pad 10 pixels each way
        selectOutputFileLayout.setSpacing(0)  # No spacing between elements


        selectOutputFileFrame.setLayout(selectOutputFileLayout)
        
        selectOPBOLayout.addWidget(selectOutputFileFrame) 

        padDataFrame = borderedQGroupBox("Pad Data") 
        padDataFrame.setBaseSize(200,200)

        padDataLayout = QVBoxLayout()
        padDataLayout.setContentsMargins(25,25,25,25)   
        padDataLayout.setSpacing(0)

        padDataFrame.setLayout(padDataLayout)
        selectOPBOLayout.addWidget(padDataFrame)

        boxFrame = borderedQGroupBox("Box Cox")
        boxFrame.setBaseSize(200,200)

        boxLayout = QVBoxLayout()
        boxLayout.setContentsMargins(25,25,25,25)
        boxLayout.setSpacing(0)

        boxFrame.setLayout(boxLayout)
        selectOPBOLayout.addWidget(boxFrame)

        outlierFrame = borderedQGroupBox("Outlier Filter")
        outlierFrame.setBaseSize(200,200)

        outlierLayout = QVBoxLayout()
        outlierLayout.setContentsMargins(25,25,25,25)
        outlierLayout.setSpacing(0)

        outlierFrame.setLayout(outlierLayout)
        selectOPBOLayout.addWidget(outlierFrame)

        buttonFrame = QFrame()
        buttonFrame.setBaseSize(600,60)
        buttonFrame.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Fixed)

        buttonLayout = QHBoxLayout()
        buttonLayout.setContentsMargins(25,25,25,25)
        buttonLayout.setSpacing(10)

        buttonFrame.setLayout(buttonLayout)

        mainLayout.addWidget(buttonFrame)

        #Content

        #Predictand file selector button
        selectInputButton = QPushButton("📂 Select Input File")
        selectInputButton.clicked.connect(self.selectInputButtonClicked)
        selectInputFileLayout.addWidget(selectInputButton)

        self.selectInputLabel = QLabel("File: Not Selected")
        selectInputFileLayout.addWidget(self.selectInputLabel)

        columnInput = QLineEdit("1")
        columnLayout.addWidget(columnInput)
        
        simCheckBox = QCheckBox("Create")
        simLayout.addWidget(simCheckBox)

        ensembleCheckBox = QCheckBox("Extract")
        ensembleInput = QLineEdit("1")
        ensembleLayout.addWidget(ensembleCheckBox)
        ensembleLayout.addWidget(ensembleInput)

        thresholdCheckBox = QCheckBox("Apply Threshold")
        thresholdLayout.addWidget(thresholdCheckBox)

        outputCheckBox = QCheckBox("Create .OUT File")
        outputLayout.addWidget(outputCheckBox)



        self.transformRadioGroup = QButtonGroup()
        self.transformRadioGroup.setExclusive(True)
        self.transformRadioGroup.buttonPressed.connect(self.unPressOtherRadios)

        transformationsFrame = QFrame()
        transformationsFrame.setBaseSize(200,300)
        transformationFrame.setContentsMargins(25,0,25,0)
        transformationsFrame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        transformationsLayout = QHBoxLayout()
        transformationsFrame.setLayout(transformationsLayout)
        functionTransformationsFrame = QFrame()
        functionTransformationsLayout = QVBoxLayout()
        functionTransformationsFrame.setLayout(functionTransformationsLayout)

        functionsLabel = QLabel("Functions")
        functionsLabel.setAlignment(Qt.AlignTop)
        functionTransformationsLayout.addWidget(functionsLabel)

        natLogRadio = QRadioButton("Ln")
        self.transformRadioGroup.addButton(natLogRadio)
        functionTransformationsLayout.addWidget(natLogRadio)

        logRadio = QRadioButton("Log")
        self.transformRadioGroup.addButton(logRadio)
        functionTransformationsLayout.addWidget(logRadio)

        squareRadio = QRadioButton("x²")
        self.transformRadioGroup.addButton(squareRadio)
        functionTransformationsLayout.addWidget(squareRadio)

        cubeRadio = QRadioButton("x³")
        self.transformRadioGroup.addButton(cubeRadio)
        functionTransformationsLayout.addWidget(cubeRadio)

        fourRadio = QRadioButton("x⁴")
        self.transformRadioGroup.addButton(fourRadio)
        functionTransformationsLayout.addWidget(fourRadio)

        recipRadio = QRadioButton("x⁻¹")
        self.transformRadioGroup.addButton(recipRadio)
        functionTransformationsLayout.addWidget(recipRadio)

        inverseTransformationsFrame = QFrame()
        inverseTransformationsLayout = QVBoxLayout()
        inverseTransformationsFrame.setLayout(inverseTransformationsLayout)

        inverseLabel = QLabel("Inverse")
        inverseLabel.setAlignment(Qt.AlignTop)
        inverseTransformationsLayout.addWidget(inverseLabel)

        eXRadio = QRadioButton("eˣ")
        self.transformRadioGroup.addButton(eXRadio)
        inverseTransformationsLayout.addWidget(eXRadio)

        tenXRadio = QRadioButton("10ˣ")
        self.transformRadioGroup.addButton(tenXRadio)
        inverseTransformationsLayout.addWidget(tenXRadio)

        sqrtRadio = QRadioButton("√x")
        self.transformRadioGroup.addButton(sqrtRadio)
        inverseTransformationsLayout.addWidget(sqrtRadio)

        cbrtRadio = QRadioButton("∛x")
        self.transformRadioGroup.addButton(cbrtRadio)
        inverseTransformationsLayout.addWidget(cbrtRadio)

        fourRtRadio = QRadioButton("∜x")
        self.transformRadioGroup.addButton(fourRtRadio)
        inverseTransformationsLayout.addWidget(fourRtRadio)
        
        xRadio = QRadioButton("x")
        self.transformRadioGroup.addButton(xRadio)
        inverseTransformationsLayout.addWidget(xRadio)

        transformationsLayout.addWidget(functionTransformationsFrame)
        transformationsLayout.addWidget(inverseTransformationsFrame)

        transformationLayout.addWidget(transformationsFrame)

        spacerFrame = QFrame()
        spacerFrame.setFrameShape(QFrame.HLine|QFrame.Sunken)
        transformationLayout.addWidget(spacerFrame)


        otherTransformationsFrame = QFrame()
        otherTransformationsLayout = QVBoxLayout()
        otherTransformationsFrame.setContentsMargins(25,0,25,0)
        backwardChangeRadio = QRadioButton("Backward Change")
        self.transformRadioGroup.addButton(backwardChangeRadio)
        otherTransformationsFrame.setLayout(otherTransformationsLayout)
        otherTransformationsLayout.addWidget(backwardChangeRadio)
        transformationLayout.addWidget(otherTransformationsFrame)


        
        lagNFrame = QFrame()
        lagNLayout = QHBoxLayout()
        lagNRadio = QRadioButton("Lag n")
        self.transformRadioGroup.addButton(lagNRadio)
        lagNLineEdit = QLineEdit("0")
        lagNLayout.addWidget(lagNRadio)
        lagNLayout.addWidget(lagNLineEdit)
        lagNFrame.setLayout(lagNLayout)
        otherTransformationsLayout.addWidget(lagNFrame)

        binomialFrame = QFrame()
        binomialLayout = QHBoxLayout()
        binomialRadio = QRadioButton("Binomial")
        self.transformRadioGroup.addButton(binomialRadio)

        binomialLineEdit = QLineEdit("0")
        binomialWrapCheckBox = QCheckBox("Wrap")
        binomialLayout.addWidget(binomialRadio)
        binomialLayout.addWidget(binomialLineEdit)
        binomialLayout.addWidget(binomialWrapCheckBox)
        binomialFrame.setLayout(binomialLayout)
        otherTransformationsLayout.addWidget(binomialFrame)
        





        selectOutputButton = QPushButton("📂 Select Output File")
        selectOutputButton.clicked.connect(self.selectOutputButtonClicked)
        selectOutputFileLayout.addWidget(selectOutputButton)

        self.selectOutputLabel = QLabel("File: Not Selected")
        selectOutputFileLayout.addWidget(self.selectOutputLabel)

        self.padDataCheckBox = QCheckBox("Pad Data")

        startDateFrame = QFrame()
        startDateLayout = QHBoxLayout()
        startDateLabel = QLabel("Start Date: ")
        self.startDateEdit = QDateEdit(calendarPopup=True)
        self.startDateEdit.setDate(QDate(1948,1,1))

        startDateLayout.addWidget(startDateLabel)
        startDateLayout.addWidget(self.startDateEdit)
        startDateFrame.setLayout(startDateLayout)
        
        endDateFrame = QFrame()
        endDateLayout = QHBoxLayout()
        endDateLabel = QLabel("End Date: ")
        self.endDateEdit = QDateEdit(calendarPopup=True)
        self.endDateEdit.setDate(QDate(2015,12,31))
        endDateLayout.addWidget(endDateLabel)
        endDateLayout.addWidget(self.endDateEdit)
        endDateFrame.setLayout(endDateLayout)

        padDataLayout.addWidget(self.padDataCheckBox)
        padDataLayout.addWidget(startDateFrame)
        padDataLayout.addWidget(endDateFrame)

        boxCoxRadioGroup = QButtonGroup()
        boxCoxRadioGroup.setExclusive(True)
        boxCoxRadio = QRadioButton("Box Cox")
        unBoxCoxRadio = QRadioButton("Un-Box Cox")
        boxCoxRadioGroup.addButton(boxCoxRadio)
        boxCoxRadioGroup.addButton(unBoxCoxRadio)
        lambdaFrame = labeledQLineEditFrame("Lambda: ", "1")
        shiftFrame = labeledQLineEditFrame("Shift: ", "0")

        boxLayout.addWidget(boxCoxRadio)
        boxLayout.addWidget(unBoxCoxRadio)
        boxLayout.addWidget(lambdaFrame)
        boxLayout.addWidget(shiftFrame)

        outlierCheckBox = QCheckBox("Remove Outliers")
        standardDevFrame = labeledQLineEditFrame("Standard Dev: ", "0")
        outlierLayout.addWidget(outlierCheckBox)
        outlierLayout.addWidget(standardDevFrame)

        transformButton = QPushButton("Transform Data")
        transformButton.clicked.connect(self.doTransform)
        transformButton.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")

        buttonLayout.addWidget(transformButton)


    def QDateEditToDateTime(self, dateEdit):
        rawStartDate = dateEdit.date()
        dateTime = rawStartDate.toPyDate()
        return dateTime

    def selectInputButtonClicked(self):
        #Will have to be changed soon, as it relies on known file "predictand files"
        fileName = QFileDialog.getOpenFileName(self, "Select input file", 'predictand files', "DAT Files (*.DAT)") 
        print(fileName)
        if fileName[0] != '':
            self.inputSelected = fileName[0]
            self.selectInputLabel.setText("File: "+self.inputSelected.split("/")[-1]) #Only show the name of the file, not the whole path
        else:
            self.inputSelected = None
            self.selectInputLabel.setText("File: Not Selected")

    def selectOutputButtonClicked(self):
        #Will have to be changed soon, as it relies on known file "predictand files"
        fileName = QFileDialog.getOpenFileName(self, "Select output file", 'SDSM Refresh', "") 
        print(fileName)
        if fileName[0] != '':
            self.outputSelected = fileName[0]
            self.selectOutputLabel.setText("File: "+self.outputSelected.split("/")[-1]) #Only show the name of the file, not the whole path
        else:
            self.outputSelected = None
            self.selectOutputLabel.setText("File: Not Selected")

    def unPressOtherRadios(self,*args):
         #Needed to make sure function radio and inverse radio buttons cant be clicked at same time
        radio = self.sender()
        buttons = self.transformRadioGroup.buttons()
        for button in buttons:
            if button != radio:
                if button.isChecked():
                    button.setChecked(False)

    def doTransform(self):
        from numpy import log, log10, ndim, empty,longdouble
        #print("https://www.youtube.com/watch?v=7F2QE8O-Y1g")
        try:
            trans = self.transformRadioGroup.checkedButton().text()
        except AttributeError:
            return displayBox("Transformation Error","A transformation must be selected.","Error",isError=True)
        try:
            file = open(self.inputSelected,"r")
            file.close()
        except FileNotFoundError:
            return displayBox("Input Error","No input file selected.","Error",isError=True)
        try:
            outputFile = open(self.outputSelected, "w")
        except FileNotFoundError:
            return displayBox("Output Error","No output file selected, and you have not selected one to be generated.","Error",isError=True)
        data = loadData([self.inputSelected])
        transformations = [["Ln",log],["Log",log10],["x²",square], ["x³",cube],["x⁴",powFour],["x⁻¹",powMinusOne],["eˣ",eToTheN],["10ˣ",tenToTheN],["√x",powHalf],["∛x",powThird],["∜x",powQuarter],["x",returnSelf]]
        if self.padDataCheckBox.isChecked():
            padData(data, self.QDateEditToDateTime(self.startDateEdit), self.QDateEditToDateTime(self.endDateEdit))
        for i in transformations:
            if i[0] == trans:
                print(i[0] +" found")
                returnedData = genericTransform(data, i[1])
                for i in returnedData:
                    outputFile.write(str(i[0])+"\n")
        outputFile.close()