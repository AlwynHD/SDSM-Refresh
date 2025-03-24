from PyQt5.QtWidgets import (QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QSizePolicy, 
                             QFrame, QLabel, QLineEdit, QFileDialog, QGroupBox, 
                             QGridLayout, QListWidget, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import os

class ContentWidget(QWidget):
    """
    A polished and modernized UI for the Weather Generator with an improved structure and user experience.
    """
    def __init__(self):
        super().__init__()

        # Main layout
        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(30, 30, 30, 30)
        mainLayout.setSpacing(20)
        self.setLayout(mainLayout)

        # --- File Selection Section ---
        fileSelectionGroup = QGroupBox("File Selection")
        fileSelectionLayout = QGridLayout()

        self.parFileButton = QPushButton("📂 Select Parameter File")
        self.parFileButton.clicked.connect(self.selectPARFile)
        self.parFileText = QLabel("Not selected")

        self.outFileButton = QPushButton("💾 Save To File")
        self.outFileButton.clicked.connect(self.selectOutputFile)
        self.outFileText = QLabel("Not selected")

        fileSelectionLayout.addWidget(self.parFileButton, 0, 0)
        fileSelectionLayout.addWidget(self.parFileText, 0, 1)
        fileSelectionLayout.addWidget(self.outFileButton, 1, 0)
        fileSelectionLayout.addWidget(self.outFileText, 1, 1)

        fileSelectionGroup.setLayout(fileSelectionLayout)
        mainLayout.addWidget(fileSelectionGroup)

        # --- Predictor Information Section ---
        predInfoGroup = QGroupBox("Predictor Information")
        predInfoLayout = QGridLayout()

        self.noOfPredText = QLabel("📊 No. of predictors: 0")
        self.autoRegressLabel = QLabel("🔄 Autoregression: Unknown")
        self.processLabel = QLabel("⚙️ Process: Unknown")
        self.rStartText = QLabel("📅 Record Start: Unknown")
        self.rLengthText = QLabel("📏 Record Length: Unknown")

        self.viewPredictorsButton = QPushButton("👁️ View Predictors")
        self.viewPredictorsButton.clicked.connect(self.viewPredictors)
        
        predInfoLayout.addWidget(self.noOfPredText, 0, 0)
        predInfoLayout.addWidget(self.autoRegressLabel, 0, 1)
        predInfoLayout.addWidget(self.processLabel, 1, 0)
        predInfoLayout.addWidget(self.rStartText, 1, 1)
        predInfoLayout.addWidget(self.rLengthText, 2, 0)
        predInfoLayout.addWidget(self.viewPredictorsButton, 2, 1)

        predInfoGroup.setLayout(predInfoLayout)
        mainLayout.addWidget(predInfoGroup)

        # --- Predictors List Section ---
        predictorsGroup = QGroupBox("Predictors List")
        predictorsLayout = QVBoxLayout()
        
        self.predictorList = QListWidget()
        predictorsLayout.addWidget(self.predictorList)
        
        predictorsGroup.setLayout(predictorsLayout)
        mainLayout.addWidget(predictorsGroup)

        # --- Synthesis Parameters ---
        synthesisGroup = QGroupBox("Synthesis Parameters")
        synthesisLayout = QGridLayout()

        self.fStartText = QLineEdit()
        self.fStartText.setPlaceholderText("DD/MM/YYYY")
        self.fLengthText = QLineEdit()
        self.fLengthText.setPlaceholderText("Enter number of days")
        
        self.eSize = QLineEdit("20")
        self.eSize.setPlaceholderText("1-100")
        
        synthesisLayout.addWidget(QLabel("📅 Synthesis Start Date:"), 0, 0)
        synthesisLayout.addWidget(self.fStartText, 0, 1)
        synthesisLayout.addWidget(QLabel("📏 Synthesis Length:"), 0, 2)
        synthesisLayout.addWidget(self.fLengthText, 0, 3)
        synthesisLayout.addWidget(QLabel("📊 Ensemble Size:"), 1, 0)
        synthesisLayout.addWidget(self.eSize, 1, 1)

        synthesisGroup.setLayout(synthesisLayout)
        mainLayout.addWidget(synthesisGroup)

        # --- Progress Bar (hidden by default) ---
        self.progressPicture = QFrame()
        self.progressPicture.setFrameShape(QFrame.Box)
        self.progressPicture.setFixedHeight(30)
        self.progressPicture.setVisible(False)
        mainLayout.addWidget(self.progressPicture)

        # --- Buttons ---
        buttonLayout = QHBoxLayout()
        
        self.synthesizeButton = QPushButton("🚀 Synthesize Data")
        self.synthesizeButton.clicked.connect(self.synthesizeData)
        self.synthesizeButton.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        
        self.resetButton = QPushButton("🔄 Reset")
        self.resetButton.clicked.connect(self.reset_all)
        self.resetButton.setStyleSheet("background-color: #F44336; color: white; font-weight: bold;")
        
        buttonLayout.addWidget(self.synthesizeButton)
        buttonLayout.addWidget(self.resetButton)
        mainLayout.addLayout(buttonLayout)

    def selectPARFile(self):
        """Opens a file dialog to select a PAR file."""
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Parameter File", "", "PAR Files (*.PAR);;All Files (*.*)")
        if file_name:
            self.parFileText.setText(f"📂 {file_name}")

        self.par_file_path = file_name
        self.par_file_text.setText(f"📂 {os.path.basename(file_name)}")

        try:
            self.predictor_list.clear()
            
            # Parse PAR file
            with open(file_name, 'r') as par_file:
                # Read number of predictors
                line = par_file.readline().strip()
                n_predictors = int(line)
                
                detrend_applied = False
                if n_predictors < 0:
                    detrend_applied = True
                    n_predictors = abs(n_predictors)
                
                self.no_of_pred_text.setText(f"📊 No. of predictors: {n_predictors}")
                
                season_code = int(par_file.readline().strip())
                
                year_length = int(par_file.readline().strip())
                
                record_start_date = par_file.readline().strip()
                self.r_start_text.setText(f"📅 Record Start: {record_start_date}")
                
                record_length = int(par_file.readline().strip())
                self.r_length_text.setText(f"📏 Record Length: {record_length}")
                
                calibration_start_date = par_file.readline().strip()
                self.f_start_text.setText(calibration_start_date)
                
                calibration_days = int(par_file.readline().strip())
                self.f_length_text.setText(str(calibration_days))
                
                rain_flag = par_file.readline().strip().lower() == "true"
                if rain_flag:
                    self.process_label.setText("⚙️ Process: Conditional")
                else:
                    self.process_label.setText("⚙️ Process: Unconditional")
                
                model_trans = int(par_file.readline().strip())
                
                _ = par_file.readline().strip()
                
                line = par_file.readline().strip()
                
                if line.lower() == "true" or line.lower() == "false":
                    auto_regression = line.lower() == "true"
                    self.auto_regress_label.setText(f"🔄 Autoregression: {auto_regression}")
                    predictand_filename = par_file.readline().strip()
                else:
                    auto_regression = False
                    self.auto_regress_label.setText("🔄 Autoregression: False")
                    predictand_filename = line
                
                self.predictor_list.addItem(predictand_filename)

                for i in range(n_predictors):
                    predictor_filename = par_file.readline().strip()
                    self.predictor_list.addItem(predictor_filename)
            
            # Show success message
            QMessageBox.information(self, "PAR File Loaded", 
                                f"Successfully loaded parameter file with {n_predictors} predictors.")
            
        except Exception as e:
            QMessageBox.critical(self, "Error Loading PAR File", f"Failed to parse the parameter file: {str(e)}")
            # Reset file path on error
            self.par_file_path = ""
            self.par_file_text.setText("Not selected")
    

    def selectOutputFile(self):
        """Opens a file dialog to select an output file."""
        file_name, _ = QFileDialog.getSaveFileName(self, "Save To File", "", "OUT Files (*.OUT);;All Files (*.*)")
        if file_name:
            self.outFileText.setText(f"💾 {file_name}")
            
    def viewPredictors(self):
        """Loads and displays predictors from the PAR file."""
        if not self.par_file_path:
            QMessageBox.critical(self, "No PAR file selected", 
                            "You must select a parameter file first.")
            return
            
        try:
        
            par_dir = os.path.dirname(self.par_file_path)
            
            # Check predictor file existence
            missing_files = []
            found_files = []
            
            for index in range(self.predictor_list.count()):
                predictor_file = self.predictor_list.item(index).text()
                
                # Remove previous warning marks
                if predictor_file.startswith('⚠️ '):
                    predictor_file = predictor_file.split(' (Missing)')[0][2:]
                    self.predictor_list.item(index).setText(predictor_file)
                
                predictor_path = os.path.join(par_dir, predictor_file)
                
                # Mark the missing files with prefix 
                if not os.path.exists(predictor_path):
                    missing_files.append(predictor_file)
                    self.predictor_list.item(index).setText(f"⚠️ {predictor_file} (Missing)")
                else:
                    found_files.append(predictor_file)
            
            # file missing warning
            if missing_files:
                missing_list = "\n- ".join(missing_files)
                QMessageBox.warning(self, "Missing Predictor Files", 
                                f"The following predictor files were not found in the PAR file directory:\n- {missing_list}\n\nPlease ensure all predictor files are in the same directory as the PAR file.")
            else:
                QMessageBox.information(self, "Predictors Verified", 
                                    f"All {len(found_files)} predictor files were found in the directory.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error Checking Predictors", 
                            f"An error occurred while checking predictor files: {str(e)}")
    
    def synthesizeData(self):
        """Handles the synthesis of weather data."""
        # Check input fields validity
        if self.parFileText.text() == "Not selected":
            # Show error message
            print("You must select a parameter file first.")
            return
        
        if self.outFileText.text() == "Not selected":
            # Show error message
            print("You must select a suitable output file to save to.")
            return
        
        # Show progress
        self.progressPicture.setVisible(True)
        
        # In a real application, this would process the data
        # For now, just simulate progress
        import time
        time.sleep(1)
        
        # Hide progress
        self.progressPicture.setVisible(False)
        print("Synthesis completed.")
    
    def reset_all(self):
        try:
            self.parFileText.setText("Not selected")
            self.outFileText.setText("Not selected")
            self.eSize.setText("20")
            self.predictorList.clear()
            self.noOfPredText.setText("📊 No. of predictors: 0")
            self.autoRegressLabel.setText("🔄 Autoregression: Unknown")
            self.processLabel.setText("⚙️ Process: Unknown")
            self.rStartText.setText("📅 Record Start: Unknown")
            self.rLengthText.setText("📏 Record Length: Unknown")
            self.fStartText.setText("")
            self.fLengthText.setText("")
        except OSError as e:
            if e.errno == 2:
                print("Error: default directory no good")
                raise
            else:
                print("Error Number: ", e.errno)
                raise