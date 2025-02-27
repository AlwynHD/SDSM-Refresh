import numpy as np

globalMissingCode = -999
data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 700, 27, 16]

#Functions
np.log(data)
np.log10(data)
np.power(data, 2)
np.power(data, 3)
np.power(data, 4)
np.ones(len(data)) / data

#Inverse
np.power(np.e, data)
np.power(10, data)
np.power(data, 0.5)
np.power(data, 1/3)
np.power(data, 0.25)
data

def backwardsChange(inputData):
    outputData = [-999]
    for i in range(1, len(inputData)):
        currVal = inputData[i]
        prevVal = inputData[i - 1]
        if (currVal != globalMissingCode) and (prevVal != globalMissingCode):
            outputData.append(currVal - prevVal)
        else:
            outputData.append(globalMissingCode)
    return outputData

def lag(inputData, n):
    return inputData[n:] + inputData[:n]

def binomial(inputData, binomialValue):
    return [0 if entry <= binomialValue else 1 for entry in inputData]

def applyThreshold(inputData, thresh):
    return [entry for entry in inputData if entry > thresh]

print(applyThreshold(data, 3))