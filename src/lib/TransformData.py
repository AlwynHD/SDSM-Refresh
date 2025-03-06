import numpy as np
import datetime as dt

#Alex's attempts to understand the original Transform Data Screen
#Extract ensemble member seems to just take one column from the input file?
#Apply threshold does not apply the transformation to the value if it is below threshold
#Can't figure out what sim or out file do
#Pad data adds missing values based on dates given
#Outliers remove outliers from file

globalSDate = dt.datetime(1948, 1, 1)
globalEDate = dt.datetime(2015, 12, 31)
dataSDate = dt.datetime(1948, 1, 1)
dataEDate = dt.datetime(2015, 12, 31)
globalMissingCode = -999
thresh = 4
applyThresh = True
#data = np.array([[2], [3], [4], [5], [6], [7], [8], [9], [10], [100], [120], [145], [145], [555], [444], [333], [333], [333], [333], [333]])
#data = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]])
data = np.array([[1], [2], [3], [4], [5], [6], [7], [8], [9]])

def valueIsValid(value):
    #todo move to utils
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


#region Settings

padData(data)
#Create SIM File
#Apply Threshold
#Remove Outliers
#Create OUT File
#Wrap

#endregion

#region Transformations

genericTransform(data, np.log)
genericTransform(data, np.log10)
genericTransform(data, square)
genericTransform(data, cube)
#genericTransform(data, powFour)
genericTransform(data, powMinusOne)
#genericTransform(data, eToTheN)
#genericTransform(data, tenToTheN)
genericTransform(data, powHalf)
genericTransform(data, powThird)
genericTransform(data, powQuarter)
data

backwardsChange(data)
lag(data, 1)
binomial(data, 5)
"""

#Other Transformations
backwardsChange(data)
lag(data, 1)
binomial(data, 1)
#Box Cox
#Unbox Cox
"""

removeOutliers(data, 1)
#endregion