import numpy as np
import datetime as dt
import scipy as sci
from src.lib.utils import loadFilesIntoMemory, selectFile

def loadData(file):
    data = loadFilesIntoMemory(file)[0]
    if np.ndim(data) == 1:
        newData = np.empty((len(data), 1))
        newData[:, 0] = data
        data = newData
    data.astype(np.longdouble)
    return data

def valueIsValid(value):
    return value != globalMissingCode and (not applyThresh or value > thresh)

def genericTransform(data, func):
    returnData = np.empty_like(data)
    for c in range(len(data.T)):
        for r in range(len(data[:, c])):
            if valueIsValid(data[r][c]):
                returnData[r][c] = func(data[r][c])
            else:
                returnData[r][c] = data[r][c]
    return returnData

def square(n): return np.float_power(n, 2)
def cube(n): return np.float_power(n, 3)
def powFour(n): return np.float_power(n, 4)
def powMinusOne(n): return np.float_power(n, -1)
def eToTheN(n): return np.float_power(np.e, n)
def tenToTheN(n): return np.float_power(10, n)
def powHalf(n): return np.float_power(n, 1/2)
def powThird(n): return np.float_power(n, 1/3)
def powQuarter(n): return np.float_power(n, 1/4)
def returnSelf(n): return n

def backwardsChange(data):
    """Returns the difference between each value and the previous value"""
    returnData = np.empty_like(data)
    for c in range(len(data.T)):
        for r in range(len(data[:, c])):
            if valueIsValid(data[r][c]):
                if r == 0 or not valueIsValid(data[r - 1][c]):
                    returnData[r][c] = globalMissingCode
                else:
                    returnData[r][c] = data[r][c] - data[r - 1][c]
            else:
                returnData[r][c] = data[r][c]
    return returnData

def lag(data, n):
    """Rewrite data so it begins at position n. Values before n wrap to bottom."""
    returnData = np.empty_like(data)
    for c in range(len(data.T)):
        returnData[:, c] = np.concatenate((data[:, c][n:], data[:, c][:n])) #The double brackets here are required
    return returnData

def binomial(data, binomial):
    """Returns 1 if value in column is above binomial value, otherwise returns 0"""
    returnData = np.empty_like(data)
    for c in range(len(data.T)):
        for r in range(len(data[:, c])):
            if valueIsValid(data[r][c]):
                returnData[r][c] = 1 if data[r][c] > binomial else 0
            else:
                returnData[r][c] = data[r][c]
    return returnData

def extractEnsemble(data, column):
    return data[:, column - 1]

def padData(data):
    startDiff = dataSDate - globalSDate
    endDiff = globalEDate - dataEDate
    return np.pad(data, [(startDiff.days, endDiff.days), (0, 0)], mode='constant', constant_values=globalMissingCode)

def removeOutliers(data, sdFilterValue):
    returnData = np.empty_like(data)
    for c in range(len(data.T)):
        column = data[:, c]
        threshCol = [entry for entry in column if valueIsValid(entry)]
        if len(threshCol) > 0:
            mean = sum(threshCol) / len(threshCol)
            sd = 0
            for entry in threshCol:
                if valueIsValid(entry):
                    sd += np.power((entry - mean), 2)
            sd = np.sqrt(sd / len(threshCol))
            sdFilter = sd * sdFilterValue
        
        filteredCol = np.empty_like(column)
        for r in range(len(column)):
            if valueIsValid(column[r]) and (column[r] > (mean + sdFilter) or column[r] < (mean - sdFilter)):
                filteredCol[r] = globalMissingCode
            else:
                filteredCol[r] = column[r]
        returnData[:, c] = filteredCol
    return returnData

if __name__ == "__main__":
    """Variables that are gotten from the settings or the screen."""
    file = selectFile()
    globalSDate = dt.date(1948, 1, 1)
    globalEDate = dt.date(2015, 12, 31)
    dataSDate = dt.date(1948, 1, 1)
    dataEDate = dt.date(2015, 12, 31)
    globalMissingCode = -999
    thresh = 0
    applyThresh = True

    data = loadData(file)

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
    lag(data, 1)
    binomial(data, 1)

    extractEnsemble(data, 1)

    padData(data)

    removeOutliers(data)

    sci.stats.boxcox(data)
    sci.special.inv_boxcox(data, 1)