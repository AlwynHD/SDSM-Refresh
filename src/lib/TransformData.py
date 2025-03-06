import numpy as np

#Alex's attempts to understand the original Transform Data Screen
#Extract ensemble member seems to just take one column from the input file?
#Apply threshold does not apply the transformation to the value if it is below threshold
#Can't figure out what sim or out file do
#Pad data adds missing values based on dates given
#Outliers remove outliers from file

globalMissingCode = -999
data = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 15]])

def ln(data):
    return np.log(data)

def log(data):
    return np.log10(data)

def power(data, pow):
    return np.float_power(data, pow)

def exponent(base, data):
    return np.float_power(base, data)

def backwardsChange(data):
    """Returns the difference between each value and the previous value"""
    returnData = np.empty_like(data)
    for c in range(len(data.T)):
        for r in range(len(data[:, c])):
            if r == 0 or (data[r][c] == globalMissingCode or data[r - 1][c] == globalMissingCode):
                returnData[r][c] = globalMissingCode
            else:
                returnData[r][c] = data[r][c] - data[r - 1][c]
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
        returnData[:, c] = [1 if entry > binomial else 0 for entry in data.T[c]]
    return returnData

def applyThreshold(inputData, thresh):
    #Removes all values below threshold
    return [entry for entry in inputData if entry > thresh]

def applyThresholdTransformation(inputData, thresh):
    #Keeps values below threshold, but doesn't transform them
    outputData = []
    for entry in inputData:
        if entry > thresh:
            entry = entry #Apply whatever transformation you want
        outputData.append(entry)
    return outputData

#region Settings

#Pad Data
#Create SIM File
#Apply Threshold
#Remove Outliers
#Create OUT File
#Wrap

#endregion

#region Transformations

#Functions
ln(data)
log(data)
power(data, 2)
power(data, 3)
power(data, 4)
power(data, -1)

#Inverse Functions
exponent(np.e, data)
exponent(10, data)
power(data, 1/2)
power(data, 1/3)
power(data, 1/4)
power(data, 1)

#Other Transformations
backwardsChange(data)
lag(data, 1)
binomial(data, 1)
#Box Cox
#Unbox Cox

#endregion