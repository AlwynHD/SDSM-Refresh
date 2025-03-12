import math
import datetime
import numpy as np
from src.lib.utils import *

#Local version
predictorSelected = ['predictor files/ncep_dswr.dat']
predictandSelected = ['predictand files/NoviSadPrecOBS.dat']

#predictorSelected = ['C:/Code/SDSM/SDSM-Refresh/predictor files/ncep_dswr.dat'] #todo remove default
#predictandSelected = ['C:/Code/SDSM/SDSM-Refresh/predictand files/NoviSadPrecOBS.dat'] #todo remove default
#nameOfFiles = ["NoviSadPrecOBS", "ncep_dswr"]
globalSDate = datetime.date(1948, 1, 1)
globalEDate = datetime.date(2015, 12, 31)
fSDate = datetime.date(1948, 1, 1)
fEDate = datetime.date(2015, 12, 31)
analysisPeriod = ["Annual", "Winter", "Spring", "Summer", "Autumn", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
analysisPeriodChosen = 0
autoRegressionTick = False

def partialCorrelation(A, B, n, crossCorr, corrArrayList):
    """
    recursive function that gets the partial correlation
    error is -1
    A and B are positionals
    n is step counter
    crossCorr is the array to get values from
    corrArrayList is used as index don't understand partial correlation enough to change it
    """

    #print(f"A: {A} B: {B}, n: {n}, \n crossCorr: {crossCorr} \n CorrArrayList: {corrArrayList}")
    # Calculates partial correlation of the form r12.34567 etc.
    # In the form; rab.corrArrayList(n); where n signifies how many terms we want from global array
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

def correlation(predictandSelected, predictorSelected, fSDate, fEDate, autoRegressionTick):
    """checks the correlation between the predicant and predictors"""
    if predictandSelected == "":
        print("You must select a predictand.") # todo proper error message
    elif len(predictorSelected) < 1:
        print("You must select at least one predictor.") # todo proper error message
    elif len(predictorSelected) > 12:
        print("Sorry - you are allowed a maximum of 12 predictors only.") #todo proper error message
    else:
        nVariables = len(predictorSelected) + 1

        loadedFiles = []
        loadedFiles = loadFilesIntoMemory(predictandSelected + predictorSelected)
        nameOfFiles = displayFiles(predictandSelected + predictorSelected)

        #todo progress bar

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
        #todo check that it skips to file start date if file start is not global start date
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
                    sumData += row

                # the threshold only applies to the predictand file not the predictor files
                if row[0] <= threshold and conditional and row[0] != missingCode:
                    totalBelowThreshold +=1

                inputData.append(row)
            increaseDate(workingDate, 1)

        inputData = np.array(inputData)

        # auto regression
        # change shape of array too (length of data, files +1)
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


        xBar = np.array([total/(totalNumbers - totalMissingRows - totalBelowThreshold) for total in sumData])
        
        sumresid = sqresid = np.zeros(nVariables)
        prodresid = np.zeros((nVariables, nVariables))

        for i in range(totalNumbers):
            row = inputData[i]

            if not (missingCode in row) and ((conditional and row[0] > threshold) or not conditional):
                sumData += row
                resid = np.array([row[i]-xBar[i] for i in range(row.size)])
                sumresid += resid
                sqresid += [res**2 for res in resid]
                prodresid += np.outer(resid, resid)
        
        sd = np.array([(number/(totalNumbers - 1 - totalMissingRows - totalBelowThreshold)) ** 0.5 for number in sqresid])


        #############################
        # Print Header Information
        #############################

        print("CORRELATION MATRIX")
        print()
        print(f"Analysis Period: {fSDate} - {fEDate} ({analysisPeriod[analysisPeriodChosen]})")
        print()
        print(f"Missing values: {totalMissing}")
        print(f"Missing rows: {totalMissingRows}")
        if conditional:
            print(f"Values less than or equal to threshold: {totalBelowThreshold}")
        print()

        maxLength = max(len(file) for file in nameOfFiles) + 1

        print("SOMETHING")
        print(nameOfFiles)

        # Print column headers
        #literally just the 1 2 3 
        print(" ", end="")
        for j in range(1, nVariables + 1):
            print(f" {j:{maxLength + 1}}", end="")
        print()

        # Print Cross Correlation Matrix
        crossCorr = np.zeros((nVariables, nVariables))
        for j in range(nVariables):
            print(f"{j+1} ", end="")
            print(f"{nameOfFiles[j]:{maxLength}}", end="")
            
            for k in range(nVariables):
                crossCorr[j, k] = prodresid[j, k] / ((totalNumbers - 1 - totalMissingRows - totalBelowThreshold) * sd[j] * sd[k])
                tempY = f"{crossCorr[j, k]:.3f}"
                if k == j:
                    tempY = "1"
                print(f"{tempY:{maxLength + 2}}", end="")
            print()
        print()

        # Check Partial Correlations
        if nVariables < 3:
            print("NO PARTIAL CORRELATIONS TO CALCULATE")
        else:
            print("PARTIAL CORRELATIONS WITH", nameOfFiles[0])
            print()

            print(" " *24, end="")
            print(f"{'Partial r':12}{'P value':12}")
            print()
            
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

                print(f"{nameOfFiles[i]:24}{tempResult:<12.3f}{PrValue:<12.3f}")

def analyseData(predictandSelected, predictorSelected, fsDate, feDate, globalSDate, globalEDate, autoRegressionTick):
    """analyses the data"""
    sigLevelInput = 0
    if predictandSelected == "":
        print("You must select a predictand.") # todo proper error message
    elif len(predictorSelected) < 1 and not autoRegressionTick:
        print("You must select at least one predictor.") # todo proper error message
    elif not fsDateOK(fsDate, feDate, globalSDate):
        print("file start date is not okay") #todo proper error message
    elif not feDateOK(fsDate, feDate, globalEDate):
        print("file end date is not okay") #todo proper error message
    elif not sigLevelOK(sigLevelInput):
        print("Sig level is not okay")
    else:
        nVariables = len(predictorSelected) + 1

        loadedFiles = []
        loadedFiles = loadFilesIntoMemory(predictandSelected + predictorSelected)
        
        loadedFiles = [file[(fsDate - globalSDate).days:] for file in loadedFiles]
        nameOfFiles = displayFiles(predictandSelected + predictorSelected)


        workingDate = fSDate
        lastMonth = workingDate.month - 1
        missingCode = -999
        totalNumbers = 0
        totalFalseMissingCode = 0

        months = [[],[],[],[],[],[],[],[],[],[],[],[]]
        monthCount = np.zeros(12, dtype=int)
        missing = np.zeros(12, dtype=int)

        for i in range((fEDate - fSDate).days):
        #for i in range(4749, 4905):
            if lastMonth != workingDate.month -1:
                other = np.full((1,nVariables), missingCode, dtype=int)
                months[lastMonth] = np.concatenate((months[lastMonth], other))
                totalFalseMissingCode += 1
                lastMonth = workingDate.month-1
            
            totalNumbers += 1
            monthCount[workingDate.month-1] += 1

            other = np.array([[file[i] for file in loadedFiles]])
            missing[workingDate.month-1] = np.count_nonzero(other == missingCode)

            if len(months[workingDate.month-1]) == 0:
                months[workingDate.month-1] = other
            else:
                months[workingDate.month-1] = np.concatenate((months[workingDate.month-1], other))
            
            workingDate = increaseDate(workingDate, 1)
        

        # data is in months (month, length of files, files)

        """------------------------
        Calculate Stats
        -----------------------"""
        conditional = True
        threshold = 0
        if conditional:
            for month in months:
                month[:, 0] = np.where(month[:, 0] > threshold, 1, np.where(month[:, 0] != missingCode, 0, missingCode))

        #TODO extract data and reset every month
        #todo check if right line 806
        for index, month in enumerate(months):
            sumData = sumDataSquared = SumDataPredictandPredictor = np.zeros(nVariables)
            for i in range(len(month)):
                row = month[i]
                if row[0] == missingCode:
                    row = [0 for file in row] # np.zero(len(row))
                row = [0 if data == missingCode else data for data in row]
                #if autoregression then last one needs to be sumdata += month[i-1][nvariables]
                #SUMX
                sumData += row
                #SUMXX
                sumDataSquared += [data**2 for data in row]
                #SUMXY
                SumDataPredictandPredictor += [data*row[0] for data in row]
                #SUMY not needed as it is in SUMX same with SUMYY

                if autoRegressionTick:
                    sumData[nVariables] += month[i-1][nVariables]
                    sumData[nVariables] += month[i-1][nVariables] ** 2
                    sumData[nVariables] += month[i-1][nVariables] * row[0]
            """
            collapsedArray = np.vstack(months)
            print("Collapsed array")
            print(collapsedArray.shape) 

            print(sumData, "SUMDATA")
            columnSums = np.sum(collapsedArray, axis=0)
            print(columnSums)
            squared_columnSums = np.sum(collapsedArray ** 2, axis=0)
            print(squared_columnSums)
            multiplication_sums = np.sum(collapsedArray * collapsedArray[0], axis=0)
            print(multiplication_sums)        
            """
            denomintor = [(len(month) - missing[i] * SumDataPredictandPredictor[i]) - (sumData[i] ** 2) for i in range(nVariables)]
            
            CORR = [0 if denomintor[i] <= 0 else ((len(month)- missing[i] * SumDataPredictandPredictor[0])- sumData[i]*sumData[0])/(np.sqrt(denomintor[i]) * np.sqrt(denomintor[0]) ) for i in range(nVariables)]
            RSQD = [COORvalue ** 2 for COORvalue in CORR]

            T = [9999 if RSQD[i] > 0.999 else (CORR[i] * np.sqrt(len(month) - missing[i]) - 2 ) / np.sqrt(1 - RSQD[i]) for i in range(nVariables)]

            pr = [(((1 + ((T[i] ** 2) / (len(month) - missing[index]))) ** -(((len(month) - missing[index]) + 1) / 2))) / (np.sqrt(((len(month) - missing[index]) * math.pi))) * np.sqrt((len(month) - missing[index])) for i in range(nVariables)] # line 875
        # return each months CORR, RSQD, T, pr

def scatterPlot(predictandSelected, predictorSelected, fsDate, feDate, globalSDate, globalEDate, autoRegressionTick):
    print(predictandSelected)
    if predictandSelected[0] == "":
        return "Predictand Error" # todo proper error message
    elif len(predictorSelected) < 1 and not autoRegressionTick:
        return "Predictor Error" # todo proper error message
    elif len(predictorSelected) < 1:
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
            increaseDate(workingDate, 1)

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

if __name__ == '__main__':
    #analyseData(predictandSelected, predictorSelected, fSDate, fEDate, globalSDate, globalEDate, autoRegressionTick)
    #predictorSelected = selectFile()
    #predictandSelected = selectFile()

    #correlation(predictandSelected, predictorSelected, fSDate, fEDate, autoRegressionTick)
    scatterPlot(predictandSelected, predictorSelected, fSDate, fEDate, globalSDate, globalEDate, autoRegressionTick)
    #print(np.random.normal(size=(2, 200), scale=1e-5))