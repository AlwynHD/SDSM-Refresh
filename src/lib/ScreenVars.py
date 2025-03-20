import math
import datetime
import numpy as np
import scipy.stats as stats                
from src.lib.utils import *
#from utils import *
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QTabWidget
from PyQt5.QtGui import QFont
import src.core.data_settings as global_settings

#Local version
predictorSelected = ['predictor files/ncep_dswr.dat']
predictandSelected = ['predictand files/NoviSadPrecOBS.dat']

settings = {
    'fSDate': datetime.date(1948, 1, 1),
    'fEDate': datetime.date(2015, 12, 31),
    'leapYear': True,
    'threshold': 0.5,
    'missingCode': -999,
    'analysisPeriodChosen': 0,
    'analysisPeriod': ["Annual", "Winter", "Spring", "Summer", "Autumn", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
    'conditional': False,
    'autoRegressionTick': True
}

def partialCorrelation(A, B, n, crossCorr, corrArrayList):
    """
     Recursive function that calculates the partial correlation between variables A and B,
    given other controlling variables in corrArrayList.
    
    Parameters:
    - A, B: indices of the two variables to calculate correlation between
    - n: step counter for recursion
    - crossCorr: matrix of correlation coefficients
    - corrArrayList: list of indices for controlling variables
    
    Returns:
    - Partial correlation coefficient, or -1 if calculation fails
    """
    r13 = 0
    r23 = 0
    denom = 0
    result = ""
    if n == 1:
        result = crossCorr[A][B] - ( crossCorr[A][int(corrArrayList[0])] * crossCorr[B][int(corrArrayList[0])] )
        denom = (1 - crossCorr[A][int(corrArrayList[0])] ** 2) * (1 - crossCorr[B][int(corrArrayList[0])] ** 2)
    else:                #r12.34567etc... case - calculate r12.3456, r17.3456, r27.3456 for example
        result = partialCorrelation(A, B, n - 1, crossCorr, corrArrayList)     #r12.3456 for r12.34567 for example
        r13 = partialCorrelation(A, int(corrArrayList[n]), n - 1, crossCorr, corrArrayList) #r17.3456 for r12.34567 for example
        r23 = partialCorrelation(B, int(corrArrayList[n]), n - 1, crossCorr, corrArrayList) #r27.3456 for r12.34567 for example
        result = result - (r13 * r23)
        denom = (1 - r13 ** 2) * (1 - r23 ** 2)

    if denom <= 0:                          #Trap errors - return -1 if a problem occurs
        return -1
    else:
        return result / math.sqrt(denom)

def correlation(predictandSelected, predictorSelected, settings):
    global_settings.loadSettings()
    """
    Calculates correlation and partial correlation between predictand and predictors.
    
    Parameters:
    - predictandSelected: name of the predictand file
    - predictorSelected: list of predictor file names
    - settings: Dictionary containing all configuration parameters:
        - 'fSDate': Start date for analysis
        - 'fEDate': End date for analysis
        - 'leapYear': Whether to consider leap years in date calculation
        - 'threshold': Threshold value for conditional analysis
        - 'missingCode': Value used to represent missing data
        - 'analysisPeriodChosen': Index of selected analysis period
        - 'analysisPeriod': List of analysis period names
        - 'conditional': Whether to use conditional analysis
        - 'epsilon': Small value for numerical stability (optional)
    
    Returns:
    - Dictionary containing all calculated data and metadata
    """
    # Extract settings with defaults for optional parameters
    #print(loadsettings())
    fSDate = settings.get('fSDate')
    fEDate = settings.get('fEDate')
    leapYear = settings.get('leapYear', True)
    threshold = settings.get('threshold', 0)
    missingCode = settings.get('missingCode', -999)
    analysisPeriodChosen = settings.get('analysisPeriodChosen', 0)
    analysisPeriod = settings.get('analysisPeriod', ["All Year", "Winter", "Spring", "Summer", "Fall"])
    conditional = settings.get('conditional', False)
    epsilon = settings.get('epsilon', 1e-10)
    
    # Input validation with returned error messages
    if predictandSelected == "":
        return {"error": "You must select a predictand."}
    elif len(predictorSelected) < 1:
        return {"error": "You must select at least one predictor."}
    elif len(predictorSelected) > 12:
        return {"error": "Sorry - you are allowed a maximum of 12 predictors only."}
    elif fSDate is None or fEDate is None:
        return {"error": "Start date and end date must be provided in settings."}
    
    # Set up variables
    nVariables = len(predictorSelected) + 1
    
    # Load data files
    loadedFiles = loadFilesIntoMemory(predictandSelected + predictorSelected)
    nameOfFiles = displayFiles(predictandSelected + predictorSelected)
    
    # Initialize counters
    totalNumbers = 0
    totalMissing = 0
    totalMissingRows = 0
    totalBelowThreshold = 0
    
    # Process data
    workingDate = fSDate
    inputData = []
    sumData = np.zeros(nVariables)
    
    # Collect data points
    for i in range((fEDate - fSDate).days):
        if dateWanted(workingDate, analysisPeriodChosen):
            totalNumbers += 1
            row = [file[i] for file in loadedFiles]
            
            missingNumber = row.count(missingCode)
            
            # Check for missing values
            if missingNumber > 0:
                totalMissingRows += 1
                totalMissing += missingNumber
            # Include row if it meets criteria
            elif (conditional and row[0] > threshold) or not conditional:
                sumData += row
            
            # Count threshold failures
            if row[0] <= threshold and conditional and row[0] != missingCode:
                totalBelowThreshold += 1
                
            inputData.append(row)
        increaseDate(workingDate, 1, leapYear)
    
    inputData = np.array(inputData)
    
    # Handle autoregression if requested
    autoRegressionTick = settings.get('autoRegressionTick', False)
    if autoRegressionTick:
        nVariables += 1
        firstColumn = inputData[:, 0]
        
        # Create lagged column (shift values down by 1)
        newColumn = np.roll(firstColumn, 1)
        newColumn[0] = missingCode  # Use missing code for first value since we have no prior data
        
        # Add new column to data array
        inputData = np.hstack((inputData, newColumn.reshape(-1, 1)))
        
        #todo make sure that this is correct
        # Update sum for the new column
        valid_lagged = newColumn[(newColumn != missingCode) &  (~(conditional & (newColumn <= threshold)))]
        if len(valid_lagged) > 0:
            sumData = np.append(sumData, np.sum(valid_lagged))
        else:
            sumData = np.append(sumData, 0)
            
        nameOfFiles.append("Autoregression")
    
    # Calculate means
    effectiveSampleSize = totalNumbers - totalMissingRows - totalBelowThreshold
    if effectiveSampleSize == 0:
        return {"error": "No valid dates in time period choosen"}
    
    xBar = sumData / effectiveSampleSize
    
    # Initialize arrays for residuals
    sumresid = np.zeros(nVariables)
    sqresid = np.zeros(nVariables)
    prodresid = np.zeros((nVariables, nVariables))
    
    # Calculate residuals and products
    for i in range(totalNumbers):
        row = inputData[i]
        
        if not (missingCode in row) and ((conditional and row[0] > threshold) or not conditional):
            resid = row - xBar
            sumresid += resid
            sqresid += resid**2
            prodresid += np.outer(resid, resid)
    
    # Calculate standard deviations
    sd = np.sqrt(sqresid / (effectiveSampleSize - 1))
    
    # Calculate cross-correlation matrix
    crossCorr = np.zeros((nVariables, nVariables))
    for j in range(nVariables):
        for k in range(nVariables):
            crossCorr[j, k] = prodresid[j, k] / ((effectiveSampleSize - 1) * sd[j] * sd[k])
    
    # Calculate partial correlations
    partial_correlations = []
    if nVariables >= 3:
       for i in range(1, nVariables):
                corrArrayList = np.zeros(nVariables + 1)
                arrayCount = 0
                for j in range(1, nVariables):
                    if i != j:
                        corrArrayList[arrayCount] = j
                        arrayCount += 1
                
                tempResult = partialCorrelation(0, i, nVariables-2, crossCorr, corrArrayList)
                
                if abs(tempResult) < 0.999:
                    TTestValue = (tempResult * np.sqrt(totalNumbers - 2 - totalMissingRows - totalBelowThreshold)) / np.sqrt(1 - (tempResult ** 2))
                    PrValue = (((1 + ((TTestValue ** 2) / (totalNumbers - totalMissingRows - totalBelowThreshold))) ** -((totalNumbers + 1 - totalMissingRows - totalBelowThreshold) / 2))) / (np.sqrt((totalNumbers - totalMissingRows - totalBelowThreshold) * np.pi))
                    PrValue = PrValue * np.sqrt(totalNumbers - totalMissingRows - totalBelowThreshold)  # Correction for large N
                else:
                    TTestValue = 0
                    PrValue = 1
                    tempResult = 0

                partial_correlations.append({
                'variable': nameOfFiles[i],
                'correlation': tempResult,
                'p_value': PrValue,
                'TTestValue': TTestValue
            })

    
    # Create dictionary with all results
    results = {
        'analysisPeriod': {
            'startDate': fSDate,
            'endDate': fEDate,
            'periodName': analysisPeriod[analysisPeriodChosen],
            'periodIndex': analysisPeriodChosen
        },
        'settings_used': {
            'threshold': threshold,
            'missingCode': missingCode,
            'conditionalAnalysis': conditional,
            'leapYearHandling': leapYear,
            'autoregression': autoRegressionTick
        },
        'stats': {
            'totalCases': totalNumbers,
            'missingValues': totalMissing,
            'missingRows': totalMissingRows,
            'belowThreshold': totalBelowThreshold,
            'effectiveSampleSize': effectiveSampleSize
        },
        'names': nameOfFiles,
        'crossCorrelation': crossCorr.tolist(),
        'partialCorrelations': partial_correlations,
        'means': xBar.tolist(),
        'stddevs': sd.tolist(),
        'rawData': {
            'inputData': inputData.tolist(),
            'sumResiduals': sumresid.tolist(),
            'squaredResiduals': sqresid.tolist(),
            'productResiduals': prodresid.tolist()
        }
    }
    
    return results

def analyseData(predictandSelected, predictorSelected, fSDate, feDate, globalSDate, globalEDate, autoRegressionTick, leapYear, sigLevelInput):
    """
    Analyzes the relationship between predictand and predictors data
    
    Args:
        predictandSelected: The selected predictand variable
        predictorSelected: List of selected predictor variables
        fSDate: File start date
        feDate: File end date
        globalSDate: Global start date
        globalEDate: Global end date
        autoRegressionTick: Boolean indicating whether to use autoregression
        leapYear: Boolean indicating whether to account for leap years
        sigLevelInput: Significance level for statistical tests
        
    Returns:
        A numpy array with correlation statistics for each month
    """
    # Input validation
    if predictandSelected == "":
        print("You must select a predictand.") 
        return None
    elif len(predictorSelected) < 1 and not autoRegressionTick:
        print("You must select at least one predictor.") 
        return None
    elif not fSDateOK(fSDate, feDate, globalSDate):
        print("file start date is not okay") 
        return None
    elif not fEDateOK(fSDate, feDate, globalEDate):
        print("file end date is not okay") 
        return None
    elif not sigLevelOK(sigLevelInput):
        print("Sig level is not okay")
        return None
    else:
        # Number of variables including predictand and predictors
        nVariables = len(predictorSelected) + 1
        
        # Add one more variable slot if autoregression is enabled
        if autoRegressionTick:
            nVariables += 1

        # Load files into memory
        loadedFiles = loadFilesIntoMemory(predictandSelected + predictorSelected)
        
        # Slice the loaded files starting from the file start date
        loadedFiles = [file[(fSDate - globalSDate).days:] for file in loadedFiles]

        # Initialize working date to file start date
        workingDate = fSDate
        lastMonth = workingDate.month - 1
        missingCode = -999
        totalNumbers = 0
        totalFalseMissingCode = 0

        # Initialize arrays for each month
        months = [[] for _ in range(12)]
        monthCount = np.zeros(12, dtype=int)
        missing = np.zeros(12, dtype=int)

        # Loop through each day in the date range
        for i in range((feDate - fSDate).days):
            if lastMonth != workingDate.month - 1:
                # If month changed, add missing code row for previous month
                currentDay = np.full((1, nVariables), missingCode, dtype=float)
                if len(months[lastMonth]) > 0:  # Only append if the month array exists
                    months[lastMonth] = np.concatenate((months[lastMonth], currentDay))
                    totalFalseMissingCode += 1
                lastMonth = workingDate.month - 1
            
            totalNumbers += 1
            monthCount[workingDate.month-1] += 1

            # Extract data row for current day
            currentDay = np.array([[file[i] for file in loadedFiles]], dtype=float)
            
            # If using autoregression and not the first day, add previous day's value
            if autoRegressionTick and i > 0:
                # Add previous day's predictand value as an additional predictor
                previousValue = np.array([[loadedFiles[0][i-1]]])
                currentDay = np.concatenate((currentDay, previousValue), axis=1)
            
            # Count missing values
            missingCount = np.count_nonzero(currentDay == missingCode)
            missing[workingDate.month-1] += missingCount

            # Add row to appropriate month
            if len(months[workingDate.month - 1]) == 0:
                months[workingDate.month - 1] = currentDay
            else:
                months[workingDate.month - 1] = np.concatenate((months[workingDate.month-1], currentDay))
            
            # Increment the date
            workingDate = increaseDate(workingDate, 1, leapYear)

        # Apply conditional thresholding to predictand if needed
        conditional = True
        threshold = 0
        if conditional:
            for month in months:
                if len(month) > 0:  # Make sure month array is not empty
                    month[:, 0] = np.where(month[:, 0] > threshold, 1, np.where(month[:, 0] != missingCode, 0, missingCode))

        # Initialize return data array
        returnData = np.zeros((12, 4, nVariables), dtype=float)  # Changed dimensions to store stats for each variable
        
        # Process each month
        for index, monthData in enumerate(months):
            if len(monthData) == 0:
                continue  # Skip empty months
                
            # Initialize statistics arrays
            sumData = np.zeros(nVariables)
            sumDataSquared = np.zeros(nVariables)
            sumDataPredictandPredictor = np.zeros(nVariables)
            
            validRows = 0
            
            # Calculate sums
            for i in range(len(monthData)):
                row = monthData[i].copy()  # Make a copy to avoid modifying original data
                
                # Skip rows where predictand is missing
                if row[0] == missingCode:
                    continue
                    
                # Replace missing values with zeros for calculations
                row = np.array([0 if data == missingCode else data for data in row])
                validRows += 1
                
                # Calculate sums
                sumData += row
                sumDataSquared += row**2
                sumDataPredictandPredictor += row * row[0]
            
            # Skip month if no valid data
            if validRows == 0:
                continue
                
            # Skip calculations for the predictand itself (i=0) since it correlates perfectly with itself
            returnData[index, 0, 0] = 1.0  # Correlation with self is 1
            returnData[index, 1, 0] = 1.0  # R² with self is 1
            returnData[index, 2, 0] = float('inf')  # T-statistic is infinite
            returnData[index, 3, 0] = 0.0  # p-value is 0

            denominatorY = (validRows * sumDataSquared[0]) - (sumData[0] ** 2)
            # Calculate statistics for each variable
            for i in range(1, nVariables):  
                
                # Calculate correlation coefficient
                numerator = (validRows * sumDataPredictandPredictor[i]) - (sumData[i] * sumData[0])
                denominatorX = (validRows * sumDataSquared[i]) - (sumData[i] ** 2)
                
                # Check if denominator is valid
                if denominatorX <= 0 or denominatorY <= 0:
                    correlation = 0
                else:
                    correlation = numerator / (np.sqrt(denominatorX) * np.sqrt(denominatorY))
                
                # Ensure correlation is within bounds
                correlation = max(-1.0, min(1.0, correlation))
                
                # Calculate R-squared
                Rsquared = correlation ** 2
                
                # Calculate T-statistic
                if Rsquared > 0.999:
                    Tstat = 9999
                else:
                    Tstat = (correlation * np.sqrt(validRows - 2)) / np.sqrt(1 - Rsquared)
                
                # Use scipy for accurate p-value calculation
                pValue = 2 * (1 - stats.t.cdf(abs(Tstat), validRows - 2))
                
                # Store results
                returnData[index, 0, i] = correlation
                returnData[index, 1, i] = Rsquared
                returnData[index, 2, i] = Tstat
                returnData[index, 3, i] = pValue
        
        #returnData is for every month of the year there is 4 values.
        # 0 is correlation
        # 1 is R Squared, which is what the orgianal vb outputs
        # 2 is T stat
        # 3 is p Value or pr in the orgianl vb
        
        return returnData

def scatterPlot(predictandSelected, predictorSelected, fSDate, fEDate, globalSDate, globalEDate, autoRegressionTick, leapYear):
    if predictandSelected == "":
        print("You must select a predictand.") # todo proper error message
    elif len(predictorSelected) < 1 and not autoRegressionTick:
        return "Predictor Error" # todo proper error message
    elif len(predictorSelected) > 1:
        return "Predictor Error" # todo proper error message
    elif autoRegressionTick and len(predictorSelected) == 1:
        return "Predictor Error" # todo proper error message
    else:
        nVariables = len(predictorSelected) + 1

        loadedFiles = []
        loadedFiles = loadFilesIntoMemory(predictandSelected + predictorSelected)
        nameOfFiles = displayFiles(predictandSelected + predictorSelected)


        totalNumbers = 0
        totalMissing = 0 
        totalMissingRows = 0
        totalBelowThreshold = 0

        #todo import from settings
        threshold = 0 
        missingCode = -999
        workingDate = fSDate
        conditional = False
        analysisPeriodChosen = 0
        inputData = []
        sumData = np.zeros(nVariables)
        #####################
        # gets data into an array of shape (length of data, number of files)
        # only puts data in if date is in the analysis period chosen
        #####################
        for i in range((fEDate - fSDate).days):
            if dateWanted(workingDate, analysisPeriodChosen):
                totalNumbers += 1    
                row = [file[i] for file in loadedFiles]

                missingNumber = row.count(missingCode)

                # there are missingCodes
                if missingNumber > 0:
                    totalMissingRows += 1
                    totalMissing += missingNumber

                # there is no missingCodes
                elif (conditional and row[0] > threshold) or not conditional:
                    inputData.append(row)
            increaseDate(workingDate, 1, leapYear)

        inputData = np.array(inputData)

        if autoRegressionTick:
            nVariables +=1
            firstColumn = inputData[:, 0]

            # create a new column for position end with the first element shifted down
            newColumn = np.roll(firstColumn, 1)
            newColumn[0] = 0  # Replace the first element with 0 or any placeholder value
            
            # Append the new column to the original array
            inputData = np.hstack((inputData, newColumn.reshape(-1, 1)))
            
            if inputData[totalNumbers - 1, 0] != missingCode and (not (inputData[totalNumbers - 1, 0] <= threshold) and conditional):
                sumData = np.append(sumData, inputData[totalNumbers - 1, 0])
                
            else:
                sumData = np.append(sumData, sumData[0])
                nameOfFiles.append("Autoregression")

        return inputData.T

def format_correlation_results(results):
    """
    Format correlation analysis results for display in a PyQt5 application.
    
    Parameters:
    results (dict): Dictionary containing correlation analysis results
    
    Returns:
    str: Formatted string representation of the correlation results
    """
    # Extract necessary data from results dictionary
    start_date = results['analysisPeriod']['startDate']
    end_date = results['analysisPeriod']['endDate']
    period_name = results['analysisPeriod']['periodName']
    
    # Statistics
    total_missing = results['stats']['missingValues']
    total_missing_rows = results['stats']['missingRows']
    total_below_threshold = results['stats']['belowThreshold']
    effective_sample_size = results['stats']['effectiveSampleSize']
    conditional = results['settings_used']['conditionalAnalysis']
    
    # Data
    file_names = results['names']
    cross_corr = results['crossCorrelation']
    partial_correlations = results['partialCorrelations'] if 'partialCorrelations' in results else None
    
    # Format output as a string
    output = []
    
    # Header section
    output.append("CORRELATION MATRIX")
    output.append("")
    output.append(f"Analysis Period: {start_date} - {end_date} ({period_name})")
    output.append("")
    output.append(f"Missing values: {total_missing}")
    output.append(f"Missing rows: {total_missing_rows}")
    if conditional:
        output.append(f"Values less than or equal to threshold: {total_below_threshold}")
    output.append("")
    
    # Calculate the maximum length of file names for formatting
    max_length = max(len(file) for file in file_names) + 1
    n_variables = len(file_names)
    
    # Cross-correlation matrix header
    header_row = " "
    for j in range(1, n_variables + 1):
        header_row += f" {j:{max_length + 1}}"
    output.append(header_row)
    
    # Cross-correlation matrix rows
    for j in range(n_variables):
        row = f"{j+1} {file_names[j]:{max_length}}"
        
        for k in range(n_variables):
            corr_value = cross_corr[j][k]
            if k == j:
                temp_y = "1"
            else:
                temp_y = f"{corr_value:.3f}"
            row += f"{temp_y:{max_length + 2}}"
        
        output.append(row)
    
    output.append("")
    
    # Partial correlations section
    if n_variables < 3:
        output.append("NO PARTIAL CORRELATIONS TO CALCULATE")
    else:
        output.append(f"PARTIAL CORRELATIONS WITH {file_names[0]}")
        output.append("")
        output.append(" " * 24 + f"{'Partial r':12}{'P value':12}")
        output.append("")
        
        # Add partial correlation results if available
        if partial_correlations:
            for i in range(1, n_variables):
                if i-1 < len(partial_correlations):
                    partial_r = partial_correlations[i-1]['correlation']
                    p_value = partial_correlations[i-1]['p_value']
                    output.append(f"{file_names[i]:24}{partial_r:<12.3f}{p_value:<12.3f}")
    
    # Join all lines with newlines
    return "\n".join(output)

def display_correlation_results_qt(results, text_widget):
    """
    Display correlation results in a PyQt5 text widget.
    
    Parameters:
    results (dict): Dictionary containing correlation analysis results
    text_widget (QTextEdit/QPlainTextEdit): PyQt5 text widget to display the results
    """
    # Format the results
    formatted_text = format_correlation_results(results)
    
    # Set the font to a monospaced font for proper alignment
    font = QFont("Courier New", 10)
    text_widget.setFont(font)
    
    # Display the formatted text
    text_widget.setPlainText(formatted_text)
    
    # Alternatively, if you want to preserve formatting with rich text:
    # formatted_html = "<pre>" + formatted_text.replace("\n", "<br>") + "</pre>"
    # text_widget.setHtml(formatted_html)
    
def create_correlation_table_widget(results):
    """
    Create a QTableWidget to display the correlation matrix.
    This provides a more interactive way to view correlations.
    
    Parameters:
    results (dict): Dictionary containing correlation analysis results
    
    Returns:
    QTableWidget: Table widget displaying the correlation matrix
    """
    from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem
    from PyQt5.QtGui import QColor, QBrush
    from PyQt5.QtCore import Qt
    
    file_names = results['names']
    cross_corr = results['crossCorrelation']
    n_variables = len(file_names)
    
    # Create table widget
    table = QTableWidget()
    table.setRowCount(n_variables)
    table.setColumnCount(n_variables + 1)  # +1 for row headers
    
    # Set headers
    table.setHorizontalHeaderLabels(['Variable'] + file_names)
    
    # Populate table
    for i in range(n_variables):
        # Add row label
        name_item = QTableWidgetItem(file_names[i])
        name_item.setFlags(Qt.ItemIsEnabled)  # Make it non-editable
        table.setItem(i, 0, name_item)
        
        # Add correlation values
        for j in range(n_variables):
            corr_value = cross_corr[i][j]
            value_item = QTableWidgetItem(f"{corr_value:.3f}" if i != j else "1.000")
            value_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            value_item.setFlags(Qt.ItemIsEnabled)  # Make it non-editable
            
            # Color coding based on correlation strength
            if i != j:  # Skip the diagonal
                # Use blue shades for positive correlations, red for negative
                if corr_value > 0:
                    intensity = min(255, int(corr_value * 255))
                    color = QColor(255 - intensity, 255 - intensity, 255)
                else:
                    intensity = min(255, int(abs(corr_value) * 255))
                    color = QColor(255, 255 - intensity, 255 - intensity)
                    
                value_item.setBackground(QBrush(color))
            
            table.setItem(i, j + 1, value_item)
    
    # Adjust table appearance
    table.resizeColumnsToContents()
    table.resizeRowsToContents()
    
    return table

class CorrelationAnalysisApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Correlation Analysis")
        self.resize(800, 600)
        
        # Create a tab widget for different views
        self.tab_widget = QTabWidget()
        
        # Text view tab
        self.text_widget = QTextEdit()
        self.text_widget.setReadOnly(True)
        self.tab_widget.addTab(self.text_widget, "Text View")
        
        # Table view tab
        # The table will be created when data is available
        
        # Set the central widget
        self.setCentralWidget(self.tab_widget)
        
        results = correlation(predictandSelected, predictorSelected, settings)
        # Test with some data
        self.load_results(results)  # Your results dictionary
    
    def load_results(self, results):
        # Display text format
        display_correlation_results_qt(results, self.text_widget)
        
        # Create and add table view
        table_widget = create_correlation_table_widget(results)
        self.tab_widget.addTab(table_widget, "Table View")

# Run the application
"""if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CorrelationAnalysisApp()
    window.show()
    sys.exit(app.exec_())"""

if __name__ == '__main__':
    print("NOO")
    #leapYear = True
    #data = analyseData(predictandSelected, predictorSelected, fSDate, fEDate, globalSDate, globalEDate, autoRegressionTick, leapYear, sigLevelInput)

    #for line in data:
    #    print(line[1][1])
    #predictorSelected = selectFile()
    #predictandSelected = selectFile()

    #correlation(predictandSelected, predictorSelected, settings)
    #scatterPlot(predictandSelected, predictorSelected, fSDate, fEDate, globalSDate, globalEDate, autoRegressionTick, leapYear)
    #print(np.random.normal(size=(2, 200), scale=1e-5))