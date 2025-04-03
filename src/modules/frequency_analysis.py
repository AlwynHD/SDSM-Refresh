from PyQt5.QtWidgets import QApplication, QCheckBox,QPushButton, QComboBox,QFrame,QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QLabel, QTableWidget, QTableWidgetItem, QRadioButton, QGroupBox, QSpinBox, QLineEdit, QDateEdit, QFileDialog
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor, QIcon
import sys

# Define the name of the module for display in the content area
moduleName = "Frequency Analysis"

class ContentWidget(QWidget):
    """
    A widget to display the Frequency Analysis screen (UI/UX).
    Includes a buttonBar at the top and a contentArea for displaying details.
    """
    def __init__(self):
        """
        Initialize the Frequency Analysis screen UI/UX, setting up the layout, buttonBar, and contentArea.
        """
        super().__init__()

        self.setWindowTitle("Frequency Analysis")
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout()  # Main vertical layout
        
        # ---- Row 1: Observed Data & Modelled Data ---- #
        dataLayout = QHBoxLayout()
        
        # Observed Data Group Box (Reduced Width)
        obsDataGroupBox = QGroupBox("Observed Data")
        obsDataGroupBox.setStyleSheet("color: black;")
        obsDataLayout = QVBoxLayout()
        self.obs_data_button = QPushButton("Select Observed Data 📂 ")
        self.obs_data_label = QLabel("File: Not selected")
        self.obs_data_button.clicked.connect(self.select_observed_data)
        obsDataLayout.addWidget(self.obs_data_button)
        obsDataLayout.addWidget(self.obs_data_label)
        obsDataGroupBox.setLayout(obsDataLayout)
        obsDataGroupBox.setFixedHeight(100)  # Reduce width
        
        # Modelled Data Group Box (Reduced Width)
        modDataGroupBox = QGroupBox("Modelled Data")
        modDataGroupBox.setStyleSheet("color: black;")
        modDataLayout = QVBoxLayout()
        self.mod_data_button = QPushButton("Select Modelled Data 📂 ")
        self.mod_data_label = QLabel("File: Not selected")
        self.mod_data_button.clicked.connect(self.select_modeled_data)
        modDataLayout.addWidget(self.mod_data_button)
        modDataLayout.addWidget(self.mod_data_label)
        modDataGroupBox.setLayout(modDataLayout)
        modDataGroupBox.setFixedHeight(100)  # Reduce width
        
        dataLayout.addWidget(obsDataGroupBox)
        dataLayout.addWidget(modDataGroupBox)
        layout.addLayout(dataLayout)
        
        
        # ---- Row 2: Analysis Series & Frequency Analysis ---- #
        analysisFreqLayout = QHBoxLayout()
        
        # Left Side: Analysis Series + Ensemble
        leftSideLayout = QVBoxLayout()
        
        # Analysis Series Group Box (Reduced Height)
        analysisGroupBox = QGroupBox("Analysis Series")
        analysisGroupBox.setStyleSheet("color: black;")
        analysisLayoutBox = QVBoxLayout()
        self.start_date_label = QLabel("Analysis start date:")
        self.start_date = QDateEdit()
        self.end_date_label = QLabel("Analysis end date:")
        self.end_date = QDateEdit()
        analysisLayoutBox.addWidget(self.start_date_label)
        analysisLayoutBox.addWidget(self.start_date)
        analysisLayoutBox.addWidget(self.end_date_label)
        analysisLayoutBox.addWidget(self.end_date)
        analysisGroupBox.setLayout(analysisLayoutBox)
        analysisGroupBox.setFixedHeight(200)  # Reduce height
        
        # Ensemble Group Box (Referencing the Image)
        ensembleGroupBox = QGroupBox("Ensemble")
        ensembleGroupBox.setStyleSheet("color: black;")
        ensembleLayout = QVBoxLayout()
        
        self.all_members_radio = QRadioButton("All Members")
        self.ensemble_mean_radio = QRadioButton("Ensemble Mean")
        self.ensemble_member_radio = QRadioButton("Ensemble Member:")
        self.ensemble_member_spinbox = QSpinBox()
        self.ensemble_member_spinbox.setValue(0)
        self.all_mean_ensemble_radio = QRadioButton("All + Mean Ensemble")
        
        self.all_members_radio.setChecked(True)
        
        ensembleRow = QHBoxLayout()
        ensembleRow.addWidget(self.ensemble_member_radio)
        ensembleRow.addWidget(self.ensemble_member_spinbox)
        
        ensembleLayout.addWidget(self.all_members_radio)
        ensembleLayout.addWidget(self.ensemble_mean_radio)
        ensembleLayout.addLayout(ensembleRow)
        ensembleLayout.addWidget(self.all_mean_ensemble_radio)
        
        ensembleGroupBox.setLayout(ensembleLayout)
        ensembleGroupBox.setFixedHeight(150)  # Same height as Analysis Series
        
        # Add both group boxes to left side
        leftSideLayout.addWidget(analysisGroupBox)
        leftSideLayout.addWidget(ensembleGroupBox)
        
        
               # ---- Frequency Analysis Group Box ---- #
        faGroupBox = QGroupBox("Frequency Analysis")
        faGroupBox.setStyleSheet("color: black;")
        faLayout = QVBoxLayout()
        
        # Confidence Input
        self.confidence_label = QLabel("Confidence (%):")
        self.confidence_input = QSpinBox()
        self.confidence_input.setValue(5)
        faLayout.addWidget(self.confidence_label)
        faLayout.addWidget(self.confidence_input)
        
        # Probability Distribution Options
        self.empirical_radio = QRadioButton("Empirical")
        self.gev_radio = QRadioButton("GEV")
        self.gumbel_radio = QRadioButton("Gumbel")
        self.stretched_exp_radio = QRadioButton("Stretched Exponential")
        self.empirical_radio.setChecked(True)
        
        faLayout.addWidget(self.empirical_radio)
        faLayout.addWidget(self.gev_radio)
        faLayout.addWidget(self.gumbel_radio)
        faLayout.addWidget(self.stretched_exp_radio)
        
        # Threshold Input
        self.threshold_label = QLabel("Threshold:")
        self.threshold_input = QSpinBox()
        self.threshold_input.setValue(10)
        faLayout.addWidget(self.threshold_label)
        faLayout.addWidget(self.threshold_input)
        
        # ---- Separator Line ---- #
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)  # Horizontal line
        separator.setFrameShadow(QFrame.Sunken)
        faLayout.addWidget(separator)
        
        # Save Results Button
        self.save_button = QPushButton("Save Results To 💾")
        self.save_label = QLabel("File: Not selected")
        self.save_button.clicked.connect(self.save_results)
        faLayout.addWidget(self.save_button)
        faLayout.addWidget(self.save_label)
        faGroupBox.setFixedHeight(350)
        faGroupBox.setLayout(faLayout)
        
        # Add both sections to the row
        analysisFreqLayout.addLayout(leftSideLayout)
        analysisFreqLayout.addWidget(faGroupBox)
        layout.addLayout(analysisFreqLayout)

        # ---- Data Period, Threshold & PDF Categories (Stacked) ---- #
        extraSettingsLayout = QHBoxLayout()

        dataPeriodGroupBox = QGroupBox("Data Period")
        dataPeriodLayout = QVBoxLayout()
        self.data_period_combo = QComboBox()
        self.data_period_combo.addItems(["All Data", "January","February","March", "April", "May", "June", "July", "August", "Septemeber","October", "November", "December", "Winter", "Autumn","Summer","Spring"])
        dataPeriodLayout.addWidget(self.data_period_combo)
        dataPeriodGroupBox.setFixedHeight(100)
        dataPeriodGroupBox.setLayout(dataPeriodLayout)

        thresholdGroupBox = QGroupBox("Threshold")
        thresholdLayout = QVBoxLayout()
        self.apply_threshold_checkbox = QCheckBox("Apply threshold?")
        thresholdLayout.addWidget(self.apply_threshold_checkbox)
        thresholdGroupBox.setFixedHeight(100)
        thresholdGroupBox.setLayout(thresholdLayout)

        pdfGroupBox = QGroupBox("PDF Categories")
        pdfLayout = QVBoxLayout()
        self.pdf_label = QLabel("No of PDF categories")
        self.pdf_spinbox = QSpinBox()
        self.pdf_spinbox.setValue(20)
        pdfLayout.addWidget(self.pdf_label)
        pdfLayout.addWidget(self.pdf_spinbox)
        pdfGroupBox.setFixedHeight(100)
        pdfGroupBox.setLayout(pdfLayout)

        extraSettingsLayout.addWidget(dataPeriodGroupBox)
        extraSettingsLayout.addWidget(thresholdGroupBox)
        extraSettingsLayout.addWidget(pdfGroupBox)

        layout.addLayout(extraSettingsLayout)


        idfSettingsLayout = QHBoxLayout()
        # IDF Settings Group Box
        idfGroupBox = QGroupBox("IDF Settings")
        idfLayout = QHBoxLayout()
         
        self.method_moments_radio = QRadioButton("Method of Moments")
        self.parameter_power_radio = QRadioButton("Parameter Power Scaling")
        self.parameter_linear_radio = QRadioButton("Parameter Linear Scaling")
        self.method_moments_radio.setChecked(True)  # Default selection
        
        self.running_sum_label = QLabel("Running Sum Length (Days):")
        self.running_sum_input = QSpinBox()
        self.running_sum_input.setValue(2)
        
        # Adding elements to IDF Layout
        idfLayout.addWidget(self.method_moments_radio)
        idfLayout.addWidget(self.parameter_power_radio)
        idfLayout.addWidget(self.parameter_linear_radio)
        idfLayout.addWidget(self.running_sum_label)
        idfLayout.addWidget(self.running_sum_input)
        idfGroupBox.setLayout(idfLayout)

        idfSettingsLayout.addWidget(idfGroupBox)

        layout.addLayout(idfSettingsLayout)
        
            
        graphButtonsLayout= QHBoxLayout()

        qqPlotButton = QPushButton("Q-Q Plot")
        #qqPlotButton.clicked.connect(self.checkFile)
        qqPlotButton.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
       
        pdfPlotButton = QPushButton("PDF Plot")
        #pdfPlotButton.clicked.connect(self.getDailyStats)
        pdfPlotButton.setStyleSheet("background-color: #1FC7F5; color: white; font-weight: bold")

        linePlotButton = QPushButton("Line Plot")
        #linePlotButton.clicked.connect(self.doOutliers)
        linePlotButton.setStyleSheet("background-color: #F57F0C; color: white; font-weight: bold")
       
        faGraphicalButton = QPushButton("FA Graphical")
        #qqPlotButton.clicked.connect(self.checkFile)
        faGraphicalButton.setStyleSheet("background-color: #5adbb5; color: white; font-weight: bold;")

        
        graphButtonsLayout.addWidget(qqPlotButton)
        graphButtonsLayout.addWidget(pdfPlotButton)
        graphButtonsLayout.addWidget(linePlotButton)
        graphButtonsLayout.addWidget(faGraphicalButton)
        layout.addLayout(graphButtonsLayout)

        tabButtonsLayout= QHBoxLayout()

        faTabButton = QPushButton("FA Tabular")
        #qqPlotButton.clicked.connect(self.checkFile)
        faTabButton.setStyleSheet("background-color: #ffbd03; color: white; font-weight: bold;")

        
        idfPlotButton = QPushButton("IDF Plot")
        #pdfPlotButton.clicked.connect(self.getDailyStats)
        idfPlotButton.setStyleSheet("background-color: #dd7973; color: white; font-weight: bold")

        idfTabButton = QPushButton("IDF Tabular")
        #linePlotButton.clicked.connect(self.doOutliers)
        idfTabButton.setStyleSheet("background-color: #4681f4; color: white; font-weight: bold")
        
        resetButton = QPushButton(" 🔄 Reset Values")
        #qqPlotButton.clicked.connect(self.checkFile)
        resetButton.setStyleSheet("background-color: #ED0800; color: white; font-weight: bold;")

        tabButtonsLayout.addWidget(faTabButton)
        tabButtonsLayout.addWidget(idfPlotButton)
        tabButtonsLayout.addWidget(idfTabButton)
        tabButtonsLayout.addWidget(resetButton)
        layout.addLayout(tabButtonsLayout)

        self.setLayout(layout)
    
    def select_observed_data(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Observed Data File")
        if file_name:
            self.obs_data_label.setText(f"File: {file_name}")
    
    def select_modeled_data(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Modeled Data File")
        if file_name:
            self.mod_data_label.setText(f"File: {file_name}")
    
    def save_results(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Results File")
        if file_name:
            self.save_label.setText(f"File: {file_name}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ContentWidget()
    window.show()
    sys.exit(app.exec_())