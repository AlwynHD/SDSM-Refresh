import calendar
import datetime
import math
import numpy as np
try:
    from src.lib.utils import loadFilesIntoMemory, increaseDate, checkForFile, checkIfFileFormatted, selectFile
except ModuleNotFoundError:
    from utils import loadFilesIntoMemory, increaseDate, checkForFile, checkIfFileFormatted, selectFile

#Local version
predictorSelected = ['predictor files/ncep_dswr.dat']
predictandSelected = ['predictand files/NoviSadPrecOBS.dat']

#Currently accessing local file, change as needed for your own version.
selectedFile = "predictand files/NoviSadPrecOBS.dat"
outlierFile = "outlier.txt"

#Variables obtained from global settings
globalSDate = datetime.date(1948, 1, 1)
leapYear = True
globalMissingCode = -999
applyThresh = False
thresh = 0

def valueIsValid(value, applyThresh):
    return value != globalMissingCode and (not applyThresh or value > thresh)

def dailyMeansNew(filePath, applyThresh):
    data = loadFilesIntoMemory(filePath)[0]
    dailyStats = np.zeros((7, 4), float)
    #[i][0]: sum, [i][1]: count, [i][2]: mean, [i][3] standard deviation
    #i represents the day

    #Mean
    day = globalSDate.day
    for value in data:
        if valueIsValid(value, applyThresh):
            dailyStats[day][0] += value
            dailyStats[day][1] += 1
            day = (day + 1) % 7

    for stat in dailyStats:
        stat[2] = stat[0] / stat[1] if stat[1] > 0 else globalMissingCode

    #Standard Deviation
    day = globalSDate.day
    for value in data:
        if dailyStats[day][2] != globalMissingCode and valueIsValid(value, applyThresh):
            dailyStats[day][3] += (value - dailyStats[day][2]) ** 2
            day = (day + 1) % 7

    for stat in dailyStats:
        stat[3] = math.sqrt(stat[3] / stat[1]) if stat[1] > 0 else globalMissingCode

    #Output
    output = ""
    for i in range(7):
        output += str(calendar.day_name[i]) + ": Mean: " + str(round(dailyStats[i][2], 2)) + " SD: " + str(round(dailyStats[i][3], 2)) + "\n"

    return output

def getOutliersNew(filePath, outlierFile, sdFilterValue, applyThresh):
    data = loadFilesIntoMemory(filePath)[0]
    workingData = [value for value in data if valueIsValid(value, applyThresh)]
    if len(workingData) > 0:
            mean = sum(workingData) / len(workingData)
            sd = 0
            for value in workingData:
                if valueIsValid(value, applyThresh):
                    sd += np.power((value - mean), 2)
            sd = np.sqrt(sd / len(workingData))
            sdFilter = sd * sdFilterValue

    index = []
    outliers = []
    for i in range(len(data)):
        if valueIsValid(data[i], applyThresh) and (data[i] > (mean + sdFilter) or data[i] < (mean - sdFilter)):
            index.append(i + 1)
            outliers.append(data[i])

    file = open(outlierFile, "w")
    for i in range(len(outliers)):
        whitespaceCount = 30 - len(str(index[i]))
        file.write(str(index[i]) + (" " * whitespaceCount) + str(outliers[i]) + "\n")
    file.close()

    return str(len(outliers)) + " outliers identified and written to file."

def qualityCheckNew(filePath, applyThresh):
    data = loadFilesIntoMemory(filePath)[0]
    totalCount = len(data)
    missingCount = sum(1 if entry == globalMissingCode else 0 for entry in data)
    okCount = totalCount - missingCount
    threshCount = sum(1 if valueIsValid(entry, True) else 0 for entry in data)
    
    validData = [entry for entry in data if valueIsValid(entry, applyThresh)]
    dataSum = sum(validData)
    dataMax = max(validData)
    dataMin = min(validData)

    prevValue = globalMissingCode
    maxDifference = -9999
    for i in range(len(data)):
        if prevValue != globalMissingCode:
            if (valueIsValid(data[i], applyThresh)):
                difference = abs(prevValue - data[i])
                if difference > maxDifference:
                    maxDifference = round(difference, 4) #Floating point calc
                    maxDiffVal1 = prevValue
                    maxDiffVal2 = data[i]
        
        if (applyThresh and data[i] > thresh) or (not applyThresh):
            prevValue = data[i]

    if applyThresh and threshCount > 0:
        mean = round(dataSum / threshCount, 4)
    elif okCount > 0:
        mean = round(dataSum / okCount, 4)
    else:
        mean = globalMissingCode

    return dataMin, dataMax, mean, totalCount, missingCount, okCount, maxDifference, maxDiffVal1, maxDiffVal2, threshCount, 0, 0, globalMissingCode, thresh

def pettittTest(data, ptPercent):
    place = "holder"

def performPettittTest(data):
    petMatrix = np.zeros((len(data), 4), float)

    petMatrix[:, 0] = [i for i in range(1, len(data) + 1)]
    petMatrix[:, 1] = data

    data.sort()

    for i in range(len(data)):
        for j in range(len(data)):
            if petMatrix[j][1] == data[i] and petMatrix[j][2] == 0:
                petMatrix[j][2] = i + 1

    sum = 0
    for i in range(len(data)):
        sum += petMatrix[i][2]
        petMatrix[i][3] = (2 * sum) - ((i + 1) * (len(data) + 1))

    petMatrix[:, 3] = np.abs(petMatrix[:, 3])
    return round(2 * np.e ** ((-6 * max(petMatrix[:, 3]) ** 2) / ((20 ** 3) + (20 ** 2))), 5)

if __name__ == '__main__':
    filePath = selectFile()
    pettittPercent = 90
    applyThresh = False
    standardDeviations = 5

    print(getOutliersNew(filePath, r"C:\Users\ajs25\Downloads\outliers.dat", standardDeviations, applyThresh))

    data = [2, 3, 4, 5, 6, 7, 8, 9, 10, 100, 120, 145, 145, 555, 444, 333, 333, 333, 333, 333]
    #print(performPettittTest(data))