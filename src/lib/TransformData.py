import numpy as np
import datetime as dt
import scipy as sci
try:
    from src.lib.utils import loadFilesIntoMemory, selectFile
except ModuleNotFoundError:
    from utils import loadFilesIntoMemory, selectFile

globalSDate = dt.date(1948, 1, 1)
globalEDate = dt.date(2015, 12, 31)
globalMissingCode = -999
thresh = 0

def loadData(file):
    data = loadFilesIntoMemory(file)[0]

    if np.ndim(data) == 0:
        data = [data]
    
    if np.ndim(data) == 1:
        newData = np.empty((len(data), 1))
        newData[:, 0] = data
        data = newData
    data.astype(np.longdouble)
    return data

def valueIsValid(value, applyThresh):
    return value != globalMissingCode and (not applyThresh or value > thresh)

def genericTransform(data, func):
    returnData = np.empty_like(data)
    success = 0
    overflow = 0
    failure = 0

    for c in range(len(data.T)):
        for r in range(len(data[:, c])):
            if valueIsValid(data[r][c], applyThresh):
                newVal = func(data[r][c])
                returnData[r][c] = newVal
                if newVal == globalMissingCode:
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

def square(n): return np.float_power(n, 2) if n <= 1e154 else globalMissingCode
def cube(n): return np.float_power(n, 3) if n <= 1e102 else globalMissingCode
def powFour(n): return np.float_power(n, 4) if n <= 1e77 else globalMissingCode
def powMinusOne(n): return np.float_power(n, -1) if n >= 1e-308 else globalMissingCode
def eToTheN(n): return np.float_power(np.e, n) if n <= 709 else globalMissingCode
def tenToTheN(n): return np.float_power(10, n) if n <= 308 else globalMissingCode
def powHalf(n): return np.float_power(n, 1/2) if n <= 1e308 else globalMissingCode
def powThird(n): return np.float_power(n, 1/3) if n <= 1e308 else globalMissingCode
def powQuarter(n): return np.float_power(n, 1/4) if n<= 1e308 else globalMissingCode
def returnSelf(n): return n

def backwardsChange(data):
    """Returns the difference between each value and the previous value"""
    returnData = np.empty_like(data)
    success = 0
    failure = 0

    for c in range(len(data.T)):
        for r in range(len(data[:, c])):
            if valueIsValid(data[r][c], applyThresh):
                success += 1
                if r == 0 or not valueIsValid(data[r - 1][c], applyThresh):
                    returnData[r][c] = globalMissingCode
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
    """Rewrite data so it begins at position n. Values before n wrap to bottom."""
    returnData = np.empty_like(data)
    processed = 0

    for c in range(len(data.T)):
        if n > len(data.T):
            return returnData, "Cannot perform lag transformation, input past end of file."
        
        processed += 1
        if wrap:
            returnData[:, c] = np.concatenate((data[:, c][n:], data[:, c][:n])) #The double brackets here are required
        else:
            returnData[:, c] = np.concatenate((data[:, c][n:], np.full(n, globalMissingCode)))

    infoString = "Processed " + str(processed) + " values.\n"

    return returnData, infoString

def binomial(data, binomial):
    """Returns 1 if value in column is above binomial value, otherwise returns 0"""
    returnData = np.empty_like(data)
    success = 0
    failure = 0

    for c in range(len(data.T)):
        for r in range(len(data[:, c])):
            if valueIsValid(data[r][c], applyThresh):
                returnData[r][c] = 1 if data[r][c] > binomial else 0
                success = 0
            else:
                returnData[r][c] = data[r][c]
                failure = 0

    infoString = "Processed " + str(success + failure) + " values.\n"
    if failure > 0:
        infoString += str(failure) + " value(s) were not transformed (missing or below threshold)."

    return returnData, infoString

def extractEnsemble(data, column):
    return data[:, column - 1]

def padData(data, dataSDate, dataEDate):
    startDiff = dataSDate - globalSDate
    endDiff = globalEDate - dataEDate
    return np.pad(data, [(startDiff.days, endDiff.days), (0, 0)], mode='constant', constant_values=globalMissingCode)

def removeOutliers(data, sdFilterValue):
    returnData = np.empty_like(data)
    remained = 0
    removed = 0

    for c in range(len(data.T)):
        column = data[:, c]
        threshCol = [entry for entry in column if valueIsValid(entry, applyThresh)]
        if len(threshCol) > 0:
            mean = sum(threshCol) / len(threshCol)
            sd = 0
            for entry in threshCol:
                if valueIsValid(entry, applyThresh):
                    sd += np.power((entry - mean), 2)
            sd = np.sqrt(sd / len(threshCol))
            sdFilter = sd * sdFilterValue
        
        filteredCol = np.empty_like(column)
        for r in range(len(column)):
            if valueIsValid(column[r], applyThresh) and (column[r] > (mean + sdFilter) or column[r] < (mean - sdFilter)):
                filteredCol[r] = globalMissingCode
                removed += 1
            else:
                filteredCol[r] = column[r]
                remained += 1
        returnData[:, c] = filteredCol

    infoString = "Processed " + str(remained + removed) + " values.\n"
    if removed > 0:
        infoString += str(removed) + " value(s) were identified as outliers and removed."

    return returnData, infoString

def boxCox(data):
    #todo check with Chris if we can use auto generated lambda or if he wants his method
    #todo also check if he will let us boxcox data with fewer than 50 entries
    #todo and if we can run this for multiple columns
    returnData = np.empty_like(data)
    success = 0

    for c in range(len(data.T)):
        boxCoxData = [entry for entry in data[:, c] if valueIsValid(entry, applyThresh)]
        minVal = np.min(boxCoxData)
        boxCoxData = sci.stats.boxcox(boxCoxData)

        invalidCount = 0
        for r in range(len(data[:, c])):
            if valueIsValid(data[r][c], applyThresh):
                returnData[r][c] = boxCoxData[0][r - invalidCount]
                success += 1
            else:
                returnData[r][c] = data[r][c]
                invalidCount += 1

    infoString = "Processed " + str(success + invalidCount) + " values.\n"
    if invalidCount > 0:
        infoString += str(invalidCount) + " value(s) excluded from transformation (missing or below threshold).\n"
    infoString += "Optimal lamda value: " + str(boxCoxData[1])
    infoString += "\nData right shifted: " + str(minVal)
    
    return returnData, infoString

def unBoxCox(data, lamda, leftShift):
    returnData = np.empty_like(data)
    success = 0

    for c in range(len(data.T)):
        unBoxCoxData = [entry for entry in data[:, c] if valueIsValid(entry, applyThresh)]
        for i in range(len(unBoxCoxData)):
            unBoxCoxData[i] += leftShift

        unBoxCoxData = sci.special.inv_boxcox(unBoxCoxData, lamda)
        for i in range(len(unBoxCoxData)):
            unBoxCoxData[i] -= leftShift

        invalidCount = 0
        for r in range(len(data[:, c])):
            if valueIsValid(data[r][c], applyThresh):
                returnData[r][c] = unBoxCoxData[r - invalidCount]
                success += 1
            else:
                returnData[r][c] = data[r][c]
                invalidCount += 1

    infoString = "Processed " + str(success + invalidCount) + " values.\n"
    if invalidCount > 0:
        infoString += str(invalidCount) + " value(s) excluded from transformation (missing or below threshold).\n"

    return returnData, infoString

if __name__ == "__main__":
    """Variables that are gotten from the screen."""
    applyThresh = True
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
    print(data)

    genericTransform(data, np.log)
    genericTransform(data, np.log10)
    genericTransform(data, square)
    genericTransform(data, cube)
    genericTransform(data, powFour)
    genericTransform(data, powMinusOne)

    genericTransform(data, eToTheN)
    genericTransform(data, tenToTheN)
    genericTransform(data, powHalf)
    genericTransform(data, powThird)
    genericTransform(data, powQuarter)
    genericTransform(data, returnSelf)

    backwardsChange(data)
    lag(data, lagValue, wrap)
    binomial(data, binomialValue)

    extractEnsemble(data, ensembleCol)

    padData(data, dataSDate, dataEDate)

    removeOutliers(data, sdFilter)

    boxCox(data)
    unBoxCox(data, lamda, leftShift)