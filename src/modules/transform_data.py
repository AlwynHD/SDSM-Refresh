from PyQt5.QtWidgets import (QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QSizePolicy, 
                             QFrame, QLabel, QFileDialog, QScrollArea, QDateEdit, QCheckBox,
                             QButtonGroup, QRadioButton, QLineEdit, QGroupBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor, QIcon

# Define the name of the module for display in the content area
moduleName = "Transform Data"

class borderedQGroupBox(QGroupBox):
    def __init__(self,args):
         super().__init__(args)

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

        outputFrame = borderedQGroupBox("Threshold")
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
        transformationLayout.setContentsMargins(25, 25, 25, 25)  # Remove padding from the layout
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
        

        



