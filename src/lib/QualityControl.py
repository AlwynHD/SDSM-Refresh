import calendar
import datetime
import math
import numpy as np
try:
    from src.lib.utils import loadFilesIntoMemory, selectFile, getSettings
except ModuleNotFoundError:
    from utils import loadFilesIntoMemory, selectFile, getSettings

def valueIsValid(value, applyThresh, missingCode, thresh):
    return value != missingCode and (not applyThresh or value > thresh)

def dailyMeans(filePath, applyThresh, globalSDate):
    settings = getSettings()
    data = loadFilesIntoMemory(filePath)[0]
    dailyStats = np.zeros((7, 4), float)
    missingCode = settings["globalmissingcode"]
    thresh = settings["fixedthreshold"]
    #[i][0]: sum, [i][1]: count, [i][2]: mean, [i][3] standard deviation
    #i represents the day

    #Mean
    day = globalSDate.day
    for value in data:
        if valueIsValid(value, applyThresh, missingCode, thresh):
            dailyStats[day][0] += value
            dailyStats[day][1] += 1
            day = (day + 1) % 7

    for stat in dailyStats:
        stat[2] = stat[0] / stat[1] if stat[1] > 0 else missingCode

    #Standard Deviation
    day = globalSDate.day
    for value in data:
        if dailyStats[day][2] != missingCode and valueIsValid(value, applyThresh, missingCode, thresh):
            dailyStats[day][3] += (value - dailyStats[day][2]) ** 2
            day = (day + 1) % 7

    for stat in dailyStats:
        stat[3] = math.sqrt(stat[3] / stat[1]) if stat[1] > 0 else missingCode

    #Output
    output = ""
    for i in range(7):
        output += str(calendar.day_name[i]) + ": Mean: " + str(round(dailyStats[i][2], 2)) + " SD: " + str(round(dailyStats[i][3], 2)) + "\n"

    return output

def getOutliers(filePath, outlierFile, sdFilterValue, applyThresh):
    settings = getSettings()
    missingCode = settings["globalmissingcode"]
    thresh = settings["fixedthreshold"]
    data = loadFilesIntoMemory(filePath)[0]
    workingData = [value for value in data if valueIsValid(value, applyThresh, missingCode, thresh)]
    if len(workingData) > 0:
            mean = sum(workingData) / len(workingData)
            sd = 0
            for value in workingData:
                if valueIsValid(value, applyThresh, missingCode, thresh):
                    sd += np.power((value - mean), 2)
            sd = np.sqrt(sd / len(workingData))
            sdFilter = sd * sdFilterValue

    index = []
    outliers = []
    for i in range(len(data)):
        if valueIsValid(data[i], applyThresh, missingCode, thresh) and (data[i] > (mean + sdFilter) or data[i] < (mean - sdFilter)):
            index.append(i + 1)
            outliers.append(data[i])

    file = open(outlierFile, "w")
    for i in range(len(outliers)):
        whitespaceCount = 30 - len(str(index[i]))
        file.write(str(index[i]) + (" " * whitespaceCount) + str(outliers[i]) + "\n")
    file.close()

    return str(len(outliers)) + " outliers identified and written to file."

def qualityCheck(filePath, applyThresh):
    settings = getSettings()
    missingCode = settings["globalmissingcode"]
    thresh = settings["fixedthreshold"]
    data = loadFilesIntoMemory(filePath)[0]
    totalCount = len(data)
    missingCount = sum(1 if entry == missingCode else 0 for entry in data)
    okCount = totalCount - missingCount
    threshCount = sum(1 if valueIsValid(entry, True, missingCode, thresh) else 0 for entry in data)
    
    validData = [entry for entry in data if valueIsValid(entry, applyThresh, missingCode, thresh)]
    dataSum = sum(validData)
    dataMax = max(validData)
    dataMin = min(validData)

    prevValue = missingCode
    maxDifference = -9999
    for i in range(len(data)):
        if prevValue != missingCode:
            if (valueIsValid(data[i], applyThresh, missingCode, thresh)):
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
        mean = missingCode

    return dataMin, dataMax, mean, totalCount, missingCount, okCount, maxDifference, maxDiffVal1, maxDiffVal2, threshCount, 0, 0, missingCode, thresh

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

    settings = getSettings()

    missingCode = settings["globalmissingcode"]
    thresh = settings["fixedthreshold"]
    globalSDate = settings["globalsdate"]

    #print(dailyMeans(filePath, applyThresh, missingCode, thresh, globalSDate))
    #print(getOutliers(filePath, r"C:\Users\ajs25\Downloads\outliers.dat", standardDeviations, applyThresh, missingCode, thresh))
    #print(qualityCheck(filePath, applyThresh, missingCode, thresh))

    data = [2, 3, 4, 5, 6, 7, 8, 9, 10, 100, 120, 145, 145, 555, 444, 333, 333, 333, 333, 333]
    #print(performPettittTest(data))