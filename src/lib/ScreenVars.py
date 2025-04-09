import math
import datetime
import numpy as np
import scipy.stats as stats                
from src.lib.utils import *
#from utils import *
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QTabWidget
from PyQt5.QtGui import QFont

#Local version
predictorSelected = ['predictor files/ncep_dswr.dat']
predictandSelected = ['predictand files/NoviSadPrecOBS.dat']

settings = {
    'fSDate': datetime.date(1948, 1, 1),
    'fEDate': datetime.date(2015, 12, 31),
    'analysisPeriodChosen': 0,
    'conditional': False,
    'autoRegressionTick': True,
    'sigLevelInput': 0.05 #todo check whether this would be a correct input
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

def correlation(predictandSelected, predictorSelected, inputs):
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
    settings = getSettings()
    analysisPeriod = ["Annual", "Winter", "Spring", "Summer", "Autumn", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

    
    #from settings
    leapYear = settings["leapYear"]
    thirtyDay = settings["thirtyDay"]
    threshold = settings["fixedthreshold"]
    missingCode = settings["globalmissingcode"]
    globalSDate = settings["globalsdate"]
    globalEDate = settings["globaledate"]

    #from user choices
    fSDate = inputs.get('fSDate')
    fEDate = inputs.get('fEDate')
    if thirtyDay:
        fSDate = thirtyDate(fSDate.year, fSDate.month, fSDate.day)
        fEDate = thirtyDate(fEDate.year, fEDate.month, fEDate.day)
        
    analysisPeriodChosen = inputs.get('analysisPeriodChosen', 0)
    conditional = inputs.get('conditional', False)
    autoRegressionTick = inputs.get('autoRegressionTick', False)

    #epsilon = inputs.get('epsilon', 1e-10)
    
    # Input validation with returned error messages
    if predictandSelected == "":
        return {"error": "Predictand Error"}
    elif len(predictorSelected) < 1 and not autoRegressionTick:
        return {"error": "Predictor Error"}
    elif len(predictorSelected) > 1:
        return {"error": "Predictor Error"}
    elif autoRegressionTick and len(predictorSelected) == 1:
        return {"error": "Predictor Error"}
    # Set up variables
    nVariables = len(predictorSelected) + 1
    
    # Load data files
    loadedFiles = loadFilesIntoMemory(predictandSelected + predictorSelected)
    loadedFiles = [file[(fSDate - globalSDate).days:] for file in loadedFiles]

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
        workingDate = increaseDate(workingDate, 1, leapYear)
    
    inputData = np.array(inputData)
    
    # Handle autoregression if requested
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
        "error": "NA",
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

def analyseData(predictandSelected, predictorSelected, inputs):
    """
    Analyzes the relationship between predictand and predictors data
    
    Args:
        predictandSelected: The selected predictand variable
        predictorSelected: List of selected predictor variables
        fSDate: File start date
        fEDate: File end date
        globalSDate: Global start date
        globalEDate: Global end date
        autoRegressionTick: Boolean indicating whether to use autoregression
        leapYear: Boolean indicating whether to account for leap years
        sigLevelInput: Significance level for statistical tests
        
    Returns:
        A numpy array with correlation statistics for each month
    """
    settings = getSettings()
    
    #from settings
    leapYear = settings["leapYear"]
    thirtyDay = settings["thirtyDay"]
    threshold = settings["fixedthreshold"]
    missingCode = settings["globalmissingcode"]
    globalSDate = settings["globalsdate"]
    globalEDate = settings["globaledate"]

    #from user choices
    fSDate = inputs.get('fSDate')
    fEDate = inputs.get('fEDate')
    if thirtyDay:
        fSDate = thirtyDate(fSDate.year, fSDate.month, fSDate.day)
        fEDate = thirtyDate(fEDate.year, fEDate.month, fEDate.day)
    
    conditional = inputs.get('conditional', False)
    autoRegressionTick = inputs.get('autoRegressionTick', False)
    sigLevelInput = inputs.get('sigLevelInput', 0.05)

    # Input validation
    if predictandSelected == "":
        return {"error": "You must select a predictand."}
    elif len(predictorSelected) < 1 and not autoRegressionTick:
        return {"error": "You must select at least one predictor."}
    elif not fSDateOK(fSDate, fEDate, globalSDate):
        return {"error": "File start date is not okay"}
    elif not fEDateOK(fSDate, fEDate, globalEDate):
        return {"error": "File end date is not okay"}
    elif not sigLevelOK(sigLevelInput):
        return {"error": "Sig level is not okay"}

    # Number of variables including predictand and predictors
    nVariables = len(predictorSelected) + 1
    
    # Add one more variable slot if autoregression is enabled
    if autoRegressionTick:
        nVariables += 1

    # Load files into memory
    try:
        loadedFiles = loadFilesIntoMemory(predictandSelected + predictorSelected)
    except FileNotFoundError:
        return {"error": "Predictand file must be selected"}
    
    # Slice the loaded files starting from the file start date
    loadedFiles = [file[(fSDate - globalSDate).days:] for file in loadedFiles]

    # Initialize working date to file start date
    workingDate = fSDate
    lastMonth = workingDate.month - 1
    totalNumbers = 0
    totalFalseMissingCode = 0

    # Initialize arrays for each month
    months = [[] for _ in range(12)]
    monthCount = np.zeros(12, dtype=int)
    missing = np.zeros(12, dtype=int)

    # Loop through each day in the date range
    for i in range((fEDate - fSDate).days):
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
    if conditional:
        for month in months:
            if len(month) > 0:  # Make sure month array is not empty
                month[:, 0] = np.where(month[:, 0] > threshold, 1, np.where(month[:, 0] != missingCode, 0, missingCode))

    # Initialize return data array
    returnData = np.zeros((12, 4, nVariables), dtype=float)  # Changed dimensions to store stats for each variable
    
    # Process each month
    for index, monthData in enumerate(months):
        if len(monthData) == 0:
            print("ERROR NO DATA")
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
    results = {
        "FSDate": inputs.get('fSDate'),  # Start date of analysis
        "FEDate": inputs.get('fEDate'),  # End date of analysis
        "SigLevel": inputs.get('sigLevelInput', 0.05),  # Significance level
        "PTandFile": predictandSelected,  # Predictand file name
        "FileList": predictorSelected,  # List of predictor files
        "TotalMissing": int(np.sum(missing)),  # Total missing values
        "NVariables": len(predictorSelected) + 1,  # Number of variables
        "error": None,
        # Prepare R-squared and p-value matrices
        "RSQD": [],  # 2D list of R-squared values
        "pr": []     # 2D list of p-values
    }
    
    # Convert returnData to lists for dictionary
    for month_data in returnData:
        month_rsqd = month_data[1].tolist()  # R-squared values
        month_pvalues = month_data[3].tolist()  # p-values
        
        results["RSQD"].append(month_rsqd)
        results["pr"].append(month_pvalues)
    
    return results

def scatterPlot(predictandSelected, predictorSelected, inputs):
    settings = getSettings()
    #analysisPeriod = ["Annual", "Winter", "Spring", "Summer", "Autumn", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

    #from settings
    leapYear = settings["leapYear"]
    thirtyDay = settings["thirtyDay"]
    threshold = settings["fixedthreshold"]
    missingCode = settings["globalmissingcode"]
    globalSDate = settings["globalsdate"]
    #globalEDate = settings["globaledate"]

    #from user choices
    fSDate = inputs.get('fSDate')
    fEDate = inputs.get('fEDate')
    if thirtyDay:
        fSDate = thirtyDate(fSDate.year, fSDate.month, fSDate.day)
        fEDate = thirtyDate(fEDate.year, fEDate.month, fEDate.day)
        
    analysisPeriodChosen = inputs.get('analysisPeriodChosen', 0)
    conditional = inputs.get('conditional', False)
    autoRegressionTick = inputs.get('autoRegressionTick', False)

    if predictandSelected == "":
        return {"error": "Predictand Error"}
    elif len(predictorSelected) < 1 and not autoRegressionTick:
        return {"error": "Predictor Error"}
    elif len(predictorSelected) > 1:
        return {"error": "Predictor Error"}
    elif autoRegressionTick and len(predictorSelected) == 1:
        return {"error": "Predictor Error"}

    nVariables = len(predictorSelected) + 1

    loadedFiles = []
    loadedFiles = loadFilesIntoMemory(predictandSelected + predictorSelected)

    # Slice the loaded files starting from the file start date
    loadedFiles = [file[(fSDate - globalSDate).days:] for file in loadedFiles]

    nameOfFiles = displayFiles(predictandSelected + predictorSelected)


    totalNumbers = 0
    totalMissing = 0 
    totalMissingRows = 0
    #totalBelowThreshold = 0

    #todo import from settings
    workingDate = fSDate
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
        workingDate = increaseDate(workingDate, 1, leapYear)

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

    return {"error": "NA", "Data": inputData.T}



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
    #effective_sample_size = results['stats']['effectiveSampleSize']
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

def formatCorrelationResults(results):
    """
    Format correlation analysis results for display in a PyQt5 application.
    
    Parameters:
    results (dict): Dictionary containing correlation analysis results
    
    Returns:
    str: Formatted string representation of the correlation results
    """
    # Extract necessary data from results dictionary
    startDate = results['analysisPeriod']['startDate']
    endDate = results['analysisPeriod']['endDate']
    periodName = results['analysisPeriod']['periodName']
    
    # Statistics
    totalMissing = results['stats']['missingValues']
    totalMissingRows = results['stats']['missingRows']
    totalBelowThreshold = results['stats']['belowThreshold']
    conditional = results['settings_used']['conditionalAnalysis']
    
    # Data
    fileNames = results['names']
    crossCorr = results['crossCorrelation']
    partialCorrelations = results['partialCorrelations'] if 'partialCorrelations' in results else None
    
    # Format output as a string
    output = []
    
    # Header section
    output.append("CORRELATION MATRIX")
    output.append("")
    output.append(f"Analysis Period: {startDate} - {endDate} ({periodName})")
    output.append("")
    output.append(f"Missing values: {totalMissing}")
    output.append(f"Missing rows: {totalMissingRows}")
    if conditional:
        output.append(f"Values less than or equal to threshold: {totalBelowThreshold}")
    output.append("")
    
    # Calculate the maximum length of file names for formatting
    maxLength = max(len(file) for file in fileNames) + 1
    nVariables = len(fileNames)
    
    # Cross-correlation matrix header
    headerRow = " "
    for j in range(1, nVariables + 1):
        headerRow += f" {j:{maxLength + 1}}"
    output.append(headerRow)
    
    # Cross-correlation matrix rows
    for j in range(nVariables):
        row = f"{j+1} {fileNames[j]:{maxLength}}"
        
        for k in range(nVariables):
            corrValue = crossCorr[j][k]
            if k == j:
                tempY = "1"
            else:
                tempY = f"{corrValue:.3f}"
            row += f"{tempY:{maxLength + 2}}"
        
        output.append(row)
    
    output.append("")
    
    # Partial correlations section
    if nVariables < 3:
        output.append("NO PARTIAL CORRELATIONS TO CALCULATE")
    else:
        output.append(f"PARTIAL CORRELATIONS WITH {fileNames[0]}")
        output.append("")
        output.append(" " * 24 + f"{'Partial r':12}{'P value':12}")
        output.append("")
        
        # Add partial correlation results if available
        if partialCorrelations:
            for i in range(1, nVariables):
                if i-1 < len(partialCorrelations):
                    partialR = partialCorrelations[i-1]['correlation']
                    pValue = partialCorrelations[i-1]['p_value']
                    output.append(f"{fileNames[i]:24}{partialR:<12.3f}{pValue:<12.3f}")
    
    # Join all lines with newlines
    return "\n".join(output)

def displayCorrelationResultsQt(results, textWidget):
    """
    Display correlation results in a PyQt5 text widget.
    
    Parameters:
    results (dict): Dictionary containing correlation analysis results
    textWidget (QTextEdit/QPlainTextEdit): PyQt5 text widget to display the results
    """
    # Format the results
    formattedText = formatCorrelationResults(results)
    
    # Set the font to a monospaced font for proper alignment
    font = QFont("Courier New", 10)
    textWidget.setFont(font)
    
    # Display the formatted text
    textWidget.setPlainText(formattedText)

def createCorrelationTableWidget(results):
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
    
    fileNames = results['names']
    crossCorr = results['crossCorrelation']
    nVariables = len(fileNames)
    
    # Create table widget
    table = QTableWidget()
    table.setRowCount(nVariables)
    table.setColumnCount(nVariables + 1)  # +1 for row headers
    
    # Set headers
    table.setHorizontalHeaderLabels(['Variable'] + fileNames)
    
    # Populate table
    for i in range(nVariables):
        # Add row label
        nameItem = QTableWidgetItem(fileNames[i])
        nameItem.setFlags(Qt.ItemIsEnabled)  # Make it non-editable
        table.setItem(i, 0, nameItem)
        
        # Add correlation values
        for j in range(nVariables):
            corrValue = crossCorr[i][j]
            valueItem = QTableWidgetItem(f"{corrValue:.3f}" if i != j else "1.000")
            valueItem.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            valueItem.setFlags(Qt.ItemIsEnabled)  # Make it non-editable
            
            # Color coding based on correlation strength
            if i != j:  # Skip the diagonal
                # Use blue shades for positive correlations, red for negative
                if corrValue > 0:
                    intensity = min(255, int(corrValue * 255))
                    color = QColor(255 - intensity, 255 - intensity, 255)
                else:
                    intensity = min(255, int(abs(corrValue) * 255))
                    color = QColor(255, 255 - intensity, 255 - intensity)
                    
                valueItem.setBackground(QBrush(color))
            
            table.setItem(i, j + 1, valueItem)
    
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
        self.tabWidget = QTabWidget()
        
        # Text view tab
        self.textWidget = QTextEdit()
        self.textWidget.setReadOnly(True)
        self.tabWidget.addTab(self.textWidget, "Text View")
        
        # Set the central widget
        self.setCentralWidget(self.tabWidget)
    
    def loadResults(self, results):
        # Display text format
        displayCorrelationResultsQt(results, self.textWidget)
        
        # Create and add table view
        tableWidget = createCorrelationTableWidget(results)
        self.tabWidget.addTab(tableWidget, "Table View")

def formatAnalysisResults(data):
    """
    Format results of variance analysis with precise column alignment.
    """
    # Initialize output string
    results = []
    
    # Print header with consistent formatting
    results.append("RESULTS: EXPLAINED VARIANCE")
    results.append("")
    
    # Analysis details with consistent indentation
    results.append(f"Analysis Period: {data['FSDate']} - {data['FEDate']}")
    results.append(f"Significance level: {data['SigLevel']}")
    results.append("")

    # Calculate max length for predictors and predictand
    predictorNames = displayFiles(data['FileList'])
    predictandName = displayFiles(data['PTandFile'])
    
    # Combine all names to find max length
    allNames = predictorNames + [predictandName, "Predictors:"]
    maxNameLength = max(len(name) for name in allNames)
    
    # Missing values and predictand information
    results.append(f"Total missing values: {data['TotalMissing']}")
    results.append(f"Predictand: {predictandName}")
    
    # Months for header
    months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", 
              "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
    
    # Prepare month headers with consistent first column padding and 7-character month width
    headerParts = [f"{'Predictors:':<{maxNameLength + 2}}"] + [f"{month:>7}" for month in months]
    header = "".join(headerParts)
    results.append(header)
    
    # Print results for each predictor with precise alignment
    for i in range(1, data['NVariables']):
        # Get the filename for this predictor, left-aligned with consistent padding
        predictorName = predictorNames[i-1]
        line = f"{predictorName:<{maxNameLength + 2}}"
        
        for mm in range(12):
            # Check if p-value is significant
            if data['pr'][mm][i] <= data['SigLevel']:
                # Format R-squared value with consistent precision
                rsqdVal = f"{data['RSQD'][mm][i]:.3f}"
                
                # Use right-aligned 7-character width for each column
                line += f"{rsqdVal:>7}"
            else:
                # Add empty space for non-significant months
                line += f"{'':>7}"
        
        results.append(line)
    
    # Convert to single string with newline separators
    return "\n".join(results)

def displayAnalyseDataResultsQt(results, textWidget):
    """
    Display analysis results in a PyQt5 text widget using the same formatting as formatAnalysisResults.
    """
    # Format the results
    formattedText = formatAnalysisResults(results)
    
    # Set the font to a monospaced font for proper alignment
    font = QFont("Courier New", 10)
    textWidget.setFont(font)
    
    # Display the formatted text
    textWidget.setPlainText(formattedText)

def createAnalysisResultsTableWidget(results):
    """
    Create a QTableWidget to display the analysis results in a tabular format.
    """
    from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem
    from PyQt5.QtGui import QColor, QBrush
    from PyQt5.QtCore import Qt
    
    # Months list for column headers
    months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", 
              "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
    
    # Predictor names
    predictorNames = displayFiles(results['FileList'])
    
    # Create table widget
    table = QTableWidget()
    
    # Set table dimensions
    # Rows: Predictors
    # Columns: Predictor name + 12 months
    table.setRowCount(len(predictorNames))
    table.setColumnCount(len(months) + 1)
    
    # Set headers
    headers = ['Predictor'] + months
    table.setHorizontalHeaderLabels(headers)
    
    # Add a description in the table's header or tooltip if needed
    table.setToolTip(
        f"Analysis Period: {results['FSDate']} - {results['FEDate']}\n"
        f"Significance Level: {results['SigLevel']}\n"
        f"Total Missing Values: {results['TotalMissing']}\n"
        f"Predictand: {displayFiles(results['PTandFile'])}"
    )
    
    # Populate table with R-squared values
    for i, predictorName in enumerate(predictorNames):
        # Predictor name
        nameItem = QTableWidgetItem(predictorName)
        nameItem.setFlags(Qt.ItemIsEnabled)
        table.setItem(i, 0, nameItem)
        
        # R-squared values for each month
        for j in range(12):
            # Check significance
            if results['pr'][j][i+1] <= results['SigLevel']:
                rsqdValue = results['RSQD'][j][i+1]
                
                # Create table item
                valueItem = QTableWidgetItem(f"{rsqdValue:.3f}")
                valueItem.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                valueItem.setFlags(Qt.ItemIsEnabled)
                
                # Color coding based on R-squared value
                # Use blue shades, darker blue for higher values
                intensity = min(255, int(rsqdValue * 255))
                color = QColor(255 - intensity, 255 - intensity, 255)
                valueItem.setBackground(QBrush(color))
            else:
                # Non-significant values
                valueItem = QTableWidgetItem("N/S")
                valueItem.setTextAlignment(Qt.AlignCenter)
                valueItem.setFlags(Qt.ItemIsEnabled)
                valueItem.setBackground(QBrush(QColor(240, 240, 240)))
            
            table.setItem(i, j + 1, valueItem)
    
    # Adjust table appearance
    table.resizeColumnsToContents()
    table.resizeRowsToContents()
    
    return table

class AnalysisResultsApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Analysis Results")
        self.resize(1000, 600)
        
        # Create a tab widget
        self.tabWidget = QTabWidget()
        
        # Text view tab
        self.textWidget = QTextEdit()
        self.textWidget.setReadOnly(True)
        self.tabWidget.addTab(self.textWidget, "Text View")
        
        # Set the central widget
        self.setCentralWidget(self.tabWidget)
    
    def loadResults(self, results):
        # Display text format
        displayAnalyseDataResultsQt(results, self.textWidget)
        
        # Create and add table view
        tableWidget = createAnalysisResultsTableWidget(results)
        self.tabWidget.addTab(tableWidget, "Table View")

# Run the application
"""if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CorrelationAnalysisApp()
    window.show()
    sys.exit(app.exec_())"""

if __name__ == '__main__':
    thing = "here"
