import numpy as np
import datetime as dt
import scipy as sci
import csv
try:
    from src.lib.utils import loadFilesIntoMemory, selectFile, getSettings
except ModuleNotFoundError:
    from utils import loadFilesIntoMemory, selectFile, getSettings

def loadData(file):
    #Load data in a 2d numpy array, even if data only has one column
    data = loadFilesIntoMemory(file)[0]

    #If data a single value, put this single value into an array
    if np.ndim(data) == 0:
        data = [data]
    
    #If data is a single colum, put this single column in a 2D array
    if np.ndim(data) == 1:
        newData = np.empty((len(data), 1))
        newData[:, 0] = data
        data = newData

    #longdouble chosen to support larger numbers
    data.astype(np.longdouble)
    return data

def valueIsValid(value, applyThresh, missingCode, thresh):
    return value != missingCode and (not applyThresh or value > thresh)

def genericTransform(data, func, applyThresh):
    """ Takes all transformations which require a single function and applies them to all values in all columns.
        Specific transformations used are listed below."""
    
    settings = getSettings()
    missingCode = settings["globalmissingcode"]
    thresh = settings["fixedthreshold"]
    
    returnData = np.empty_like(data)
    success = 0
    overflow = 0
    failure = 0

    for c in range(len(data.T)):
        for r in range(len(data[:, c])):
            if valueIsValid(data[r][c], applyThresh, missingCode, thresh):
                newVal = func(data[r][c], missingCode)
                returnData[r][c] = newVal
                if newVal == missingCode:
                    overflow += 1
                else:
                    success += 1
            else:
                returnData[r][c] = data[r][c]
                failure += 1
                
    infoString = "Processed " + str(success + overflow + failure) + " values.\n"
    if failure > 0:
        infoString += str(failure) + " value(s) not transformed (missing or below threshold).\n"
    if overflow > 0:
        infoString += str(overflow) + " value(s) would have caused overflow, replaced by global missing code."

    return returnData, infoString

def ln(n, missingCode): return np.log(n) if 0 < n <= 1e308 else missingCode
def log(n, missingCode): return np.log10(n) if 0 < n <= 1e308 else missingCode
def square(n, missingCode): return np.float_power(n, 2) if n <= 1e154 else missingCode
def cube(n, missingCode): return np.float_power(n, 3) if n <= 1e102 else missingCode
def powFour(n, missingCode): return np.float_power(n, 4) if n <= 1e77 else missingCode
def powMinusOne(n, missingCode): return np.float_power(n, -1) if n >= 1e-308 else missingCode
def eToTheN(n, missingCode): return np.float_power(np.e, n) if n <= 709 else missingCode
def tenToTheN(n, missingCode): return np.float_power(10, n) if n <= 308 else missingCode
def powHalf(n, missingCode): return np.float_power(n, 1/2) if n <= 1e308 else missingCode
def powThird(n, missingCode): return np.float_power(n, 1/3) if n <= 1e308 else missingCode
def powQuarter(n, missingCode): return np.float_power(n, 1/4) if n <= 1e308 else missingCode
def returnSelf(n, missingCode): return n

def backwardsChange(data, applyThresh):
    """Returns the difference between each value in a column and the previous value in that column"""

    settings = getSettings()
    missingCode = settings["globalmissingcode"]
    thresh = settings["fixedthreshold"]

    returnData = np.empty_like(data)
    success = 0
    failure = 0

    for c in range(len(data.T)):
        for r in range(len(data[:, c])):
            if valueIsValid(data[r][c], applyThresh):
                success += 1
                if r == 0 or not valueIsValid(data[r - 1][c], applyThresh, missingCode, thresh):
                    returnData[r][c] = missingCode
                else:
                    returnData[r][c] = data[r][c] - data[r - 1][c]
            else:
                failure += 1
                returnData[r][c] = data[r][c]

    infoString = "Processed " + str(success + failure) + " values.\n"
    if failure > 0:
        infoString += str(failure) + " value(s) were not transformed (missing or below threshold)."

    return returnData, infoString

def lag(data, n, wrap):
    """ Rewrite data so it begins at position n.
        If wrap selected, values before n are written at the bottom of the file.
        Else, values before n are replaced with the global missing code."""

    settings = getSettings()
    missingCode = settings["globalmissingcode"]

    returnData = np.empty_like(data)
    processed = 0

    for c in range(len(data.T)):
        if n > len(data.T):
            return returnData, "Cannot perform lag transformation, input past end of file."
        
        processed += len(data.T)
        if wrap:
            returnData[:, c] = np.concatenate((data[:, c][n:], data[:, c][:n])) #The double brackets here are required
        else:
            returnData[:, c] = np.concatenate((data[:, c][n:], np.full(n, missingCode)))

    infoString = "Processed " + str(processed) + " values.\n"

    return returnData, infoString

def binomial(data, binomial, applyThresh):
    """ For every value in every column, return 1 if above binomial value else return 0"""

    settings = getSettings()
    missingCode = settings["globalmissingcode"]
    thresh = settings["fixedthreshold"]

    returnData = np.empty_like(data)
    success = 0
    failure = 0

    for c in range(len(data.T)):
        for r in range(len(data[:, c])):
            if valueIsValid(data[r][c], applyThresh, missingCode, thresh):
                returnData[r][c] = 1 if data[r][c] > binomial else 0
                success += 1
            else:
                returnData[r][c] = data[r][c]
                failure += 1

    infoString = "Processed " + str(success + failure) + " values.\n"
    if failure > 0:
        infoString += str(failure) + " value(s) were not transformed (missing or below threshold)."

    return returnData, infoString

def extractEnsemble(data, column):
    """Select a column"""
    numOfCols = data.shape[1]
    if column < 1 or column > numOfCols:
        return [[]], "Please select a column that is within the range of the data." 
    else:
        return [data[:, column - 1]], "Extracted ensemble member at column " + str(column) + "."

def padData(data, dataSDate, dataEDate):
    """ Adds the global missing code based on the difference between dates.
        For every day the dataSDate is ahead of the globalSDate, one line of global missing code is written at the start of the file.
        For every day the dataEDate is behind the globalEDate, one line of global missing code is written at the end of the file."""
    
    settings = getSettings()
    missingCode = settings["globalmissingcode"]
    globalSDate = settings["globalsdate"]
    globalEDate = settings["globaledate"]
    
    startDiff = dataSDate - globalSDate
    endDiff = globalEDate - dataEDate
    return np.pad(data, [(startDiff.days, endDiff.days), (0, 0)], mode='constant', constant_values=missingCode)

def removeOutliers(data, sdFilterValue, applyThresh):
    """Identifies outliers and removes them from the file"""

    settings = getSettings()
    missingCode = settings["globalmissingcode"]
    thresh = settings["fixedthreshold"]
    
    returnData = np.empty_like(data)
    remained = 0
    removed = 0

    for c in range(len(data.T)):
        column = data[:, c]
        threshCol = [entry for entry in column if valueIsValid(entry, applyThresh, missingCode, thresh)]

        #Calculation standard deviation of the column
        if len(threshCol) > 0:
            mean = sum(threshCol) / len(threshCol)
            sd = 0
            for entry in threshCol:
                if valueIsValid(entry, applyThresh, missingCode, thresh):
                    sd += np.power((entry - mean), 2)
            sd = np.sqrt(sd / len(threshCol))
            sdFilter = sd * sdFilterValue
        
        #Create an empty column. Write all non-outliers to this column.
        filteredCol = np.empty_like(column)
        for r in range(len(column)):
            if valueIsValid(column[r], applyThresh, missingCode, thresh) and (column[r] > (mean + sdFilter) or column[r] < (mean - sdFilter)):
                filteredCol[r] = missingCode
                removed += 1
            else:
                filteredCol[r] = column[r]
                remained += 1
        returnData[:, c] = filteredCol

    infoString = "Processed " + str(remained + removed) + " values.\n"
    if removed > 0:
        infoString += str(removed) + " value(s) were identified as outliers and removed."

    return returnData, infoString

def boxCox(data, applyThresh):
    """Performs the boxcox transformation on a set of data."""

    settings = getSettings()
    missingCode = settings["globalmissingcode"]
    thresh = settings["fixedthreshold"]

    returnData = np.empty_like(data)
    success = 0

    for c in range(len(data.T)):
        boxCoxData = [entry for entry in data[:, c] if valueIsValid(entry, applyThresh, missingCode, thresh)]

        #Right shift data
        minVal = np.min(boxCoxData)
        boxCoxData = [entry + abs(minVal) for entry in boxCoxData]

        #Remove all zero values
        boxCoxData = [entry for entry in boxCoxData if entry > 0]

        #Box Cox Transform
        boxCoxData = sci.stats.boxcox(boxCoxData)

        invalidCount = 0
        for r in range(len(data[:, c])):
            if valueIsValid(data[r][c], applyThresh, missingCode, thresh) or data[r][c] == minVal:
                returnData[r][c] = boxCoxData[0][r - invalidCount]
                success += 1
            else:
                returnData[r][c] = data[r][c]
                invalidCount += 1

    infoString = "Processed " + str(success + invalidCount) + " values.\n"
    if invalidCount > 0:
        infoString += str(invalidCount) + " value(s) excluded from transformation (missing or below threshold).\n"
    infoString += "Optimal lamda value: " + str(boxCoxData[1])
    infoString += "\nData right shifted: " + str(abs(min(0, minVal)))
    
    return returnData, infoString

def unBoxCox(data, lamda, leftShift, applyThresh):
    """Reverse a box cox transformation. Requires a value for lamda and left shift."""

    settings = getSettings()
    missingCode = settings["globalmissingcode"]
    thresh = settings["fixedthreshold"]

    returnData = np.empty_like(data)
    success = 0

    for c in range(len(data.T)):
        unBoxCoxData = [entry for entry in data[:, c] if valueIsValid(entry, applyThresh, missingCode, thresh)]

        #Left shift data
        for i in range(len(unBoxCoxData)):
            unBoxCoxData[i] += leftShift

        #Reverse boxcox
        unBoxCoxData = sci.special.inv_boxcox(unBoxCoxData, lamda)
        for i in range(len(unBoxCoxData)):
            unBoxCoxData[i] -= leftShift

        #Write back to column
        invalidCount = 0
        for r in range(len(data[:, c])):
            if valueIsValid(data[r][c], applyThresh, missingCode, thresh):
                returnData[r][c] = unBoxCoxData[r - invalidCount]
                success += 1
            else:
                returnData[r][c] = data[r][c]
                invalidCount += 1

    infoString = "Processed " + str(success + invalidCount) + " values.\n"
    if invalidCount > 0:
        infoString += str(invalidCount) + " value(s) excluded from transformation (missing or below threshold).\n"

    return returnData, infoString

def createOut(filepath):
    #Read from .csv
    file = csv.reader(open(filepath))
    data = [row for row in file]
    data = np.asarray(data)
        
    #Get .out filepath
    outPath = filepath[:-4]
    outPath += ".out"

    #Get longest lengths to format columns
    longestLengths = []
    for column in data.T:
        longestLengths.append(len(max(column, key=len)))

    #Write to .out
    file = open(outPath, "w")
    for r in range(len(data)):
        for c in range(len(data[r])):
            extraWhitespace = longestLengths[c] - len(data[r][c])
            file.write(data[r][c] + " " * (5 + extraWhitespace))
        file.write("\n")
    file.close()

    return outPath

def writeToFile(data, path):
    longestLengths = []
    for column in data:
        strColumn = [str(entry) for entry in column]
        longestLengths.append(len(max(strColumn, key=len)))

    file = open(path, "w")
    for r in range(len(data)):
        for c in range(len(data[r])):
            extraWhitespace = longestLengths[c] - len(str(data[r][c]))
            file.write(str(data[r][c]) + " " * (20 + extraWhitespace) + " ")
        file.write("\n")
    file.close()

if __name__ == "__main__":
    """Variables that are gotten from the screen."""
    applyThresh = False
    dataSDate = dt.date(1948, 1, 1)
    dataEDate = dt.date(2015, 12, 31)
    lagValue = 3
    binomialValue = 1
    ensembleCol = 1
    sdFilter = 1
    lamda = 2
    leftShift = 5
    wrap = False

    file = selectFile()
    data = loadData(file)

    settings = getSettings()

    outData = genericTransform(data, ln, applyThresh)[0]
    #genericTransform(data, log, applyThresh)
    #genericTransform(data, square, applyThresh)[0])
    #genericTransform(data, cube, applyThresh)
    #genericTransform(data, powFour, applyThresh)
    #genericTransform(data, powMinusOne, applyThresh)

    #genericTransform(data, eToTheN, applyThresh)
    #genericTransform(data, tenToTheN, applyThresh)
    #genericTransform(data, powHalf, applyThresh)
    #genericTransform(data, powThird, applyThresh)
    #genericTransform(data, powQuarter, applyThresh)
    #genericTransform(data, returnSelf, applyThresh)

    #backwardsChange(data, applyThresh)
    #lag(data, lagValue, wrap)
    #binomial(data, binomialValue, applyThresh)

    #extractEnsemble(data, ensembleCol)

    #padData(data, dataSDate, dataEDate)

    #removeOutliers(data, sdFilter, applyThresh)

    #boxCox(data, applyThresh)
    #unBoxCox(data, lamda, leftShift, applyThresh)
    #createOut(r"C:\Users\ajs25\Downloads\csvTest.csv")