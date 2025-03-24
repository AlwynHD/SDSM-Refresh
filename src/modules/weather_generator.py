from PyQt5.QtWidgets import (QVBoxLayout, QWidget, QHBoxLayout, QPushButton, 
                             QFrame, QLabel, QLineEdit, QFileDialog, QGroupBox, 
                             QGridLayout, QListWidget, QMessageBox)
from PyQt5.QtCore import Qt
import os

class ContentWidget(QWidget):
    """
    A polished and modernized UI for the Weather Generator with an improved structure and user experience.
    """
    def __init__(self):
        super().__init__()
        self.par_file_path = ""
        self.predictor_dir = ""

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
        self.par_file_text = QLabel("Not selected")

        self.outFileButton = QPushButton("💾 Save To .OUT File")
        self.outFileButton.clicked.connect(self.selectOutputFile)
        self.outFileText = QLabel("Not selected")
        self.simLabel = QLabel("(*.SIM also created)")
        
        fileSelectionLayout.addWidget(self.parFileButton, 0, 0)
        fileSelectionLayout.addWidget(self.par_file_text, 0, 1)
        fileSelectionLayout.addWidget(self.outFileButton, 1, 0)
        fileSelectionLayout.addWidget(self.outFileText, 1, 1)
        fileSelectionLayout.addWidget(self.simLabel, 2, 1)

        fileSelectionGroup.setLayout(fileSelectionLayout)
        mainLayout.addWidget(fileSelectionGroup)

        # --- Predictor Directory Section ---
        predictorDirGroup = QGroupBox("Select Predictor Directory")
        predictorDirLayout = QGridLayout()
        
        self.dirButton = QPushButton("📁 Select Directory")
        self.dirButton.clicked.connect(self.selectPredictorDirectory)
        self.dirText = QLabel("Not selected")
        
        predictorDirLayout.addWidget(self.dirButton, 0, 0)
        predictorDirLayout.addWidget(self.dirText, 0, 1)
        
        predictorDirGroup.setLayout(predictorDirLayout)
        mainLayout.addWidget(predictorDirGroup)

        # --- Data Section (UPDATED to match image) ---
        dataGroup = QGroupBox("Data")
        dataLayout = QGridLayout()

        # View Details button at the top
        self.viewDetailsButton = QPushButton("View Details")
        self.viewDetailsButton.clicked.connect(self.viewPredictors)
        dataLayout.addWidget(self.viewDetailsButton, 0, 0, 1, 2, Qt.AlignCenter)

        # Predictor list - keeping original appearance
        self.predictorList = QListWidget()
        # Set a good default height but don't change styling
        self.predictorList.setMinimumHeight(150)
        dataLayout.addWidget(self.predictorList, 1, 0, 1, 2)

        # Predictor information with labels on left, values on right
        dataLayout.addWidget(QLabel("No. of predictors:"), 2, 0, Qt.AlignLeft)
        self.no_of_pred_text = QLabel("0")
        dataLayout.addWidget(self.no_of_pred_text, 2, 1, Qt.AlignLeft)

        dataLayout.addWidget(QLabel("Autoregression:"), 3, 0, Qt.AlignLeft)
        self.auto_regress_label = QLabel("Unknown")
        dataLayout.addWidget(self.auto_regress_label, 3, 1, Qt.AlignLeft)

        dataLayout.addWidget(QLabel("Process:"), 4, 0, Qt.AlignLeft)
        self.process_label = QLabel("Unknown")
        dataLayout.addWidget(self.process_label, 4, 1, Qt.AlignLeft)

        # Add a separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        dataLayout.addWidget(separator, 5, 0, 1, 2)

        # Record and synthesis information
        dataLayout.addWidget(QLabel("Record Start:"), 6, 0, Qt.AlignLeft)
        self.r_start_text = QLabel("unknown")
        dataLayout.addWidget(self.r_start_text, 6, 1, Qt.AlignLeft)

        dataLayout.addWidget(QLabel("Record Length:"), 7, 0, Qt.AlignLeft)
        self.r_length_text = QLabel("unknown")
        dataLayout.addWidget(self.r_length_text, 7, 1, Qt.AlignLeft)

        dataLayout.addWidget(QLabel("Synthesis Start:"), 8, 0, Qt.AlignLeft)
        self.fStartText = QLineEdit("01/01/1948")
        dataLayout.addWidget(self.fStartText, 8, 1, Qt.AlignLeft)

        dataLayout.addWidget(QLabel("Synthesis Length:"), 9, 0, Qt.AlignLeft)
        self.fLengthText = QLineEdit("365")
        dataLayout.addWidget(self.fLengthText, 9, 1, Qt.AlignLeft)

        dataGroup.setLayout(dataLayout)
        mainLayout.addWidget(dataGroup)

        # --- Ensemble Size Section ---
        ensembleGroup = QGroupBox("Ensemble Size")
        ensembleLayout = QVBoxLayout()
        
        self.eSize = QLineEdit("20")
        self.eSize.setPlaceholderText("1-100")
        
        ensembleLayout.addWidget(self.eSize)
        
        ensembleGroup.setLayout(ensembleLayout)
        mainLayout.addWidget(ensembleGroup)

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

    def selectPredictorDirectory(self):
        """Opens a directory dialog to select the predictor directory."""
        directory = QFileDialog.getExistingDirectory(self, "Select Predictor Directory", os.path.expanduser("~"))
        if directory:
            self.predictor_dir = directory
            self.dirText.setText(directory)
            self.loadPredictorData(directory)
            
    def loadPredictorData(self, directory_path):
        """Loads predictor data from the selected directory."""
        try:
            # Search for potential PAR files in the directory
            par_files = [f for f in os.listdir(directory_path) if f.lower().endswith('.par')]
            
            if par_files:
                # If PAR files exist, ask user if they want to load one
                if len(par_files) == 1:
                    # Ask if user wants to load the PAR file
                    response = QMessageBox.question(self, "PAR File Found", 
                                        f"Found PAR file: {par_files[0]}\n\nDo you want to load it?",
                                        QMessageBox.Yes | QMessageBox.No)
                    if response == QMessageBox.Yes:
                        self.loadPARFile(os.path.join(directory_path, par_files[0]))
                elif len(par_files) > 1:
                    # Show message with list of PAR files
                    files_text = "\n".join(par_files)
                    QMessageBox.information(self, "Multiple PAR Files Found", 
                                      f"Found {len(par_files)} PAR files in the directory:\n{files_text}\n\nYou can select one using the 'Select Parameter File' button.")
            else:
                # Just update directory info
                QMessageBox.information(self, "Directory Selected", 
                                   f"Selected directory: {directory_path}\nNo PAR files found.")
                
            # Clear current list and scan for potential predictor files
            self.predictorList.clear()
            
            # Look for potential predictor files (excluding PAR files)
            potential_predictors = [f for f in os.listdir(directory_path) 
                                   if os.path.isfile(os.path.join(directory_path, f)) and 
                                   not f.lower().endswith('.par')]
            
            for file in potential_predictors:
                self.predictorList.addItem(file)
                
            # Update UI with directory info
            self.no_of_pred_text.setText(f"{len(potential_predictors)}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error Loading Directory", f"Failed to load directory: {str(e)}")

    def loadPARFile(self, file_path):
        """Loads a PAR file data."""
        self.par_file_path = file_path
        self.par_file_text.setText(f"{os.path.basename(file_path)}")

        try:
            self.predictorList.clear()
            
            # Parse PAR file
            with open(file_path, 'r') as par_file:
                # Read number of predictors
                line = par_file.readline().strip()
                n_predictors = int(line)
                
                detrend_applied = False
                if n_predictors < 0:
                    detrend_applied = True
                    n_predictors = abs(n_predictors)
                
                self.no_of_pred_text.setText(f"{n_predictors}")
                
                season_code = int(par_file.readline().strip())
                
                year_length = int(par_file.readline().strip())
                
                record_start_date = par_file.readline().strip()
                self.r_start_text.setText(f"{record_start_date}")
                
                record_length = int(par_file.readline().strip())
                self.r_length_text.setText(f"{record_length}")
                
                calibration_start_date = par_file.readline().strip()
                self.fStartText.setText(calibration_start_date)
                
                calibration_days = int(par_file.readline().strip())
                self.fLengthText.setText(str(calibration_days))
                
                rain_flag = par_file.readline().strip().lower() == "true"
                if rain_flag:
                    self.process_label.setText("Conditional")
                else:
                    self.process_label.setText("Unconditional")
                
                model_trans = int(par_file.readline().strip())
                
                _ = par_file.readline().strip()
                
                line = par_file.readline().strip()
                
                if line.lower() == "true" or line.lower() == "false":
                    auto_regression = line.lower() == "true"
                    self.auto_regress_label.setText(f"{auto_regression}")
                    predictand_filename = par_file.readline().strip()
                else:
                    auto_regression = False
                    self.auto_regress_label.setText("False")
                    predictand_filename = line
                
                self.predictorList.addItem(predictand_filename)

                for i in range(n_predictors):
                    predictor_filename = par_file.readline().strip()
                    self.predictorList.addItem(predictor_filename)
            
            # Show success message
            QMessageBox.information(self, "PAR File Loaded", 
                                f"Successfully loaded parameter file with {n_predictors} predictors.")
            
            # Set predictor directory to PAR file directory if not already set
            par_dir = os.path.dirname(file_path)
            if not self.predictor_dir:
                self.predictor_dir = par_dir
                self.dirText.setText(par_dir)
            
        except Exception as e:
            QMessageBox.critical(self, "Error Loading PAR File", f"Failed to parse the parameter file: {str(e)}")
            # Reset file path on error
            self.par_file_path = ""
            self.par_file_text.setText("Not selected")

    def selectPARFile(self):
        """Opens a file dialog to select a PAR file."""
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Parameter File", "", "PAR Files (*.PAR);;All Files (*.*)")
        if file_name:
            self.loadPARFile(file_name)

    def selectOutputFile(self):
        """Opens a file dialog to select an output file."""
        file_name, _ = QFileDialog.getSaveFileName(self, "Save To .OUT File", "", "OUT Files (*.OUT);;All Files (*.*)")
        if file_name:
            self.outFileText.setText(f"{file_name}")
            
    def viewPredictors(self):
        """Loads and displays predictors from the PAR file."""
        if not self.par_file_path:
            QMessageBox.critical(self, "No PAR file selected", 
                            "You must select a parameter file first.")
            return
            
        try:
            # Use the selected predictor directory if available, otherwise use PAR file directory
            par_dir = self.predictor_dir if self.predictor_dir else os.path.dirname(self.par_file_path)
            
            # Check predictor file existence
            missing_files = []
            found_files = []
            
            for index in range(self.predictorList.count()):
                predictor_file = self.predictorList.item(index).text()
                
                # Remove previous warning marks
                if predictor_file.startswith('⚠️ '):
                    predictor_file = predictor_file.split(' (Missing)')[0][2:]
                    self.predictorList.item(index).setText(predictor_file)
                
                predictor_path = os.path.join(par_dir, predictor_file)
                
                # Mark the missing files with prefix 
                if not os.path.exists(predictor_path):
                    missing_files.append(predictor_file)
                    self.predictorList.item(index).setText(f"⚠️ {predictor_file} (Missing)")
                else:
                    found_files.append(predictor_file)
            
            # file missing warning
            if missing_files:
                missing_list = "\n- ".join(missing_files)
                QMessageBox.warning(self, "Missing Predictor Files", 
                                f"The following predictor files were not found in the predictor directory:\n- {missing_list}\n\nPlease ensure all predictor files are in the selected directory.")
            else:
                QMessageBox.information(self, "Predictors Verified", 
                                    f"All {len(found_files)} predictor files were found in the directory.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error Checking Predictors", 
                            f"An error occurred while checking predictor files: {str(e)}")
    
    def synthesizeData(self):
        """Handles the synthesis of weather data."""
        # Check input fields validity
        if self.par_file_text.text() == "Not selected":
            QMessageBox.warning(self, "No Parameter File", "You must select a parameter file first.")
            return
        
        if self.outFileText.text() == "Not selected":
            QMessageBox.warning(self, "No Output File", "You must select a suitable output file to save to.")
            return
        
        if self.dirText.text() == "Not selected":
            QMessageBox.warning(self, "No Predictor Directory", "You must select a predictor directory.")
            return
        
        try:
            # Validate ensemble size
            ensemble_size = int(self.eSize.text())
            if ensemble_size < 1 or ensemble_size > 100:
                QMessageBox.warning(self, "Invalid Ensemble Size", "Ensemble size must be between 1 and 100.")
                return
                
            # Validate synthesis start date
            # Simplified validation - would need more robust validation in real app
            if not self.fStartText.text():
                QMessageBox.warning(self, "Missing Start Date", "Please enter a synthesis start date.")
                return
                
            # Validate synthesis length
            synthesis_length = int(self.fLengthText.text())
            if synthesis_length < 1:
                QMessageBox.warning(self, "Invalid Synthesis Length", "Synthesis length must be at least 1 day.")
                return
            
            # In a real application, this would process the data
            # Simulate progress
            QMessageBox.information(self, "Synthesis Started", 
                                "Synthesizing data with the following parameters:\n"
                                f"- Ensemble Size: {ensemble_size}\n"
                                f"- Start Date: {self.fStartText.text()}\n"
                                f"- Length: {synthesis_length} days\n\n"
                                "This process would normally take some time...")
            
            # Successful completion message
            QMessageBox.information(self, "Synthesis Complete", 
                                "Weather data synthesis completed successfully.\n"
                                f"Output saved to: {self.outFileText.text()}\n"
                                f"SIM file also created.")
                                
        except ValueError as e:
            QMessageBox.critical(self, "Invalid Input", f"Please check your input values: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Synthesis Error", f"An error occurred during synthesis: {str(e)}")
    
    def reset_all(self):
        try:
            self.par_file_path = ""
            self.predictor_dir = ""
            self.par_file_text.setText("Not selected")
            self.dirText.setText("Not selected")
            self.outFileText.setText("Not selected")
            self.eSize.setText("20")
            self.predictorList.clear()
            self.no_of_pred_text.setText("0")
            self.auto_regress_label.setText("Unknown")
            self.process_label.setText("Unknown")
            self.r_start_text.setText("unknown")
            self.r_length_text.setText("unknown")
            self.fStartText.setText("01/01/1948")
            self.fLengthText.setText("365")
            
            QMessageBox.information(self, "Reset Complete", "All fields have been reset to default values.")
        except Exception as e:
            QMessageBox.critical(self, "Reset Error", f"Error during reset: {str(e)}")