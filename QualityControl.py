import calendar
import datetime
import math
import numpy as np
from src.lib.utils import loadFilesIntoMemory, increaseDate

#Local version
predictorSelected = ['predictor files/ncep_dswr.dat']
predictandSelected = ['predictand files/NoviSadPrecOBS.dat']

#Currently accessing local file, change as needed for your own version.
selectedFile = "predictand files/NoviSadPrecOBS.dat"
outlierFile = "outlier.txt"

#Variables obtained from global settings
globalSDate = datetime.datetime(1948, 1, 1)
globalMissingCode = -999
applyThresh = False
thresh = 0

standardDeviationLimits = 1

#endregion

#region New Functions

def checkForFile(file, errorMessage):
    if file is None:
        print(errorMessage)
        return False
    else:
        return True
    
def checkIfFileFormatted(file):
    #Only checks the first line, not ideal but this is how it's done in the original
    with open(file) as f:
        firstLine = f.readline()
        if len(firstLine) > 15:
            print("File may contain multiple columns or non-Windows line breaks / carriage returns. This may cause problems in SDSM later.")
    
    f.close()
    return

def checkThreshold(value):
    return not applyThresh or value > thresh

#endregion

def dailyMeans(selectedFile):
    if not checkForFile(selectedFile, "You must select a file to check first"):
        return
    
    checkIfFileFormatted(selectedFile)

    #returnOutput = [] this is here for if we decide to change how its displayed in GUI

    #Initialise results to zero
    dailyStats = np.zeros((7, 4), float)
    #dailyStats[i][0] is running sum
    #dailyStats[i][1] is count
    #dailyStats[i][2] is standard deviation
    #dailyStats[i][3] is mean

    dayWorkingOn = globalSDate.weekday()

    #Read file and add values to array
    with open(selectedFile, "r") as file:
        for line in file:
            line = line.rstrip('\n')
            if line != str(globalMissingCode) and checkThreshold(float(line)):
                dailyStats[dayWorkingOn][0] += float(line) #Add to cumulative sum
                dailyStats[dayWorkingOn][1] += 1           #Increase count for that day

            #Iterate dayWorkingOn
            if dayWorkingOn == 6:
                dayWorkingOn = 0
            else:
                dayWorkingOn += 1

    file.close()

    #Calulcate means for each day
    for i in range(7):
        if dailyStats[i][1] > 0:
            dailyStats[i][3] = dailyStats[i][0] / dailyStats[i][1]
        else:
            dailyStats[i][3] = globalMissingCode
    
    #Calculate standard deviation
    dayWorkingOn = globalSDate.weekday()

    with open(selectedFile, "r") as file:
        for line in file:
            line = line.rstrip('\n')
            if line != str(globalMissingCode) and dailyStats[dayWorkingOn][3] != globalMissingCode and checkThreshold(float(line)):
                dailyStats[dayWorkingOn][2] += (float(line) - dailyStats[dayWorkingOn][3]) ** 2

            #Iterate dayWorkingOn
            if dayWorkingOn == 6:
                dayWorkingOn = 0
            else:
                dayWorkingOn += 1

    file.close()

    for i in range(7):
        if dailyStats[i][1] > 0:
            dailyStats[i][2] = math.sqrt(dailyStats[i][2] / dailyStats[i][1])
        else:
            dailyStats[i][2] = globalMissingCode

    output = ""
    for i in range(7):
        output += str(calendar.day_name[i]) + ": Mean: " + str(round(dailyStats[i][3], 2)) + " SD: " + str(round(dailyStats[i][2], 2)) + "\n"
        #returnOutput.append(str(calendar.day_name[i]) + ": Mean: " + str(round(dailyStats[i][3], 2)) + " SD: " + str(round(dailyStats[i][2], 2)))
    
    print(output)
    return output

def outliersID(selectedFile, outlierFile):
    #todo change python lists to numpy arrays

    if not checkForFile(selectedFile, "You must select a file to check first"):
        return
    elif not checkForFile(outlierFile, "You must select a file to save outliers to"):
        return
    
    checkIfFileFormatted(selectedFile)

    #Calculate mean
    sum = 0
    count = 0

    with open(selectedFile, "r") as file:
        for line in file:
            line = line.rstrip('\n')
            if line != str(globalMissingCode) and checkThreshold(float(line)):
                sum += float(line)
                count += 1

    file.close()

    if count > 0:
        mean = sum / count
    else:
        mean = globalMissingCode


    #Calculate standard deviation
    standardDeviation = 0

    if mean != globalMissingCode:
        with open(selectedFile, "r") as file:
            for line in file:
                line = line.rstrip('\n')
                if line != str(globalMissingCode):
                    if checkThreshold(line):
                        standardDeviation += (float(line) - mean) ** 2

        file.close()

        standardDeviation = math.sqrt(standardDeviation / count)
    else:
        standardDeviation = globalMissingCode

    #Go through data to pick outliers
    standardDeviationRange = standardDeviation * standardDeviationLimits
    outlierCount = 0
    counter = 1

    with open(selectedFile, "r") as file:
        for line in file:
            if line != str(globalMissingCode):
                if checkThreshold(float(line)):
                    if float(line) > (mean + standardDeviationRange) or float(line) < (mean - standardDeviationRange):
                        outFile = open(outlierFile, "a")
                        outFile.write(str(counter) + "\t" * 3 + line)
                        outFile.close()
                        outlierCount += 1
            counter += 1

    message = str(outlierCount) + " outliers identified and saved to file."
    print(message)
    return message
    

def qualityCheck(selectedFile):
    if not checkForFile(selectedFile, "You must select a file to check first."):
        return
    
    petArray = []
    max = -9999
    min = 9999
    totalNumbers = 0
    missing = 0
    count = 0
    sum = 0
    prevValue = globalMissingCode
    maxDifference = 0
    threshCount = 0
    
    
    with open(selectedFile, "r") as file:
        for line in file:
            inputValue = float(line)

            petArray.append(float(inputValue))
            totalNumbers += 1

            if inputValue == globalMissingCode:
                missing += 1
            else:
                count += 1
                if checkThreshold(inputValue):
                    sum += inputValue

                    if inputValue > max:
                        max = inputValue

                    if inputValue < min:
                        min = inputValue

                    if inputValue > thresh:
                        threshCount += 1
            
            if prevValue != globalMissingCode and inputValue != globalMissingCode:
                if checkThreshold(inputValue) and abs(prevValue - inputValue) > maxDifference:
                    maxDifference = abs(prevValue - inputValue)
                    maxDiffValue1 = prevValue
                    maxDiffValue2 = inputValue

            if checkThreshold(inputValue):
                prevValue = inputValue

    file.close()

    if applyThresh:
        if threshCount > 0:
            mean = round(sum / threshCount, 5)
        else:
            mean = globalMissingCode
    else:
        if count > 0:
            mean = round(sum / count, 5)
        else:
            mean = globalMissingCode

    if count < 10 or applyThresh and threshCount < 10:
        pettitt = globalMissingCode
    else:
        pettitt = pettittTest(petArray, 90)

    #print("Min: " + str(min) + "\nMax: " + str(max) + "\nMean: " + str(mean) + "\nValues in file: " + str(count + missing) + "\nMissing Values: " + str(missing) + "\nGood Values: " + str(count) + "\nMean: " + str(mean) + "\nMax Difference: " + str(maxDifference) + "\nMax Differenece Value 1: " + str(maxDiffValue1) + "\nMax Differenece Value 2: " + str(maxDiffValue2) + "\nValues above threshold: " + str(threshCount) + "\nPettitt: " + str(pettitt) + "\nPettitt Max Pos: " + str(0) + "\nGlobal Missing Code: " + str(globalMissingCode) + "\nEvent Threshold: " + str(thresh))
    return str(min), str(max), str(count), str(missing), str(mean)

def runPettittTest(data):
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
    print(petMatrix)
    return 2 * np.e ** ((-6 * max(petMatrix[:, 3]) ** 2) / ((20 ** 3) + (20 ** 2)))
    currentDate = globalSDate

    annualMeans = [0] * 120
    annualCount = [0] * 120
    #I think it has 120 values is a placeholder for a range of 120 years
    #Could probably be clever and do this in a list for potentially infinite range

    yearIndex = 0
    for i in range(len(pettittArray)):
        value = pettittArray[i]
        if value != globalMissingCode and checkThreshold(value):
            annualMeans[yearIndex] += value
            annualCount[yearIndex] += 1

        currentDate = increaseDate(currentDate, 1)
        yearIndex = currentDate.year - globalSDate.year

    del annualMeans[yearIndex:120]
    del annualCount[yearIndex:120]
    
    yearsOk = 0
    for i in range(yearIndex):
        if annualCount[i] > 0 and annualCount[i] >= (ptPercent * 3.65):
            annualMeans[i] /= annualCount[i]
            yearsOk += 1
        else:
            annualMeans[i] = globalMissingCode
    
    if yearsOk < 5:
        return globalMissingCode


    petMatrix = np.zeros((yearsOk, 4), float)
    yearsOk = 0
    
    for i in range(yearIndex):
        if annualMeans[i] != globalMissingCode:
            petMatrix[yearsOk][1] = annualMeans[i]
            petMatrix[yearsOk][0] = yearsOk + 1
            yearsOk += 1

    validMeans = [mean for mean in annualMeans if mean != globalMissingCode]
    validMeans.sort()

    for i in range(len(validMeans)):
        for j in range(yearsOk):
            if petMatrix[j][1] == validMeans[i] and petMatrix[j][2] == 0:
                petMatrix[j][2] = i + 1

    sum = 0
    for i in range(yearsOk):
        sum += petMatrix[i][2]
        petMatrix[i][3] = (2 * sum) - ((i + 1) * (yearsOk + 1))

    petMatrix[:, 3] = np.abs(petMatrix[:, 3])
    print(petMatrix)
    return 2 * np.e ** ((-6 * max(petMatrix[:, 3]) ** 2) / ((20 ** 3) + (20 ** 2)))

def pettittTest(pettittArray, ptPercent):
    currentDate = globalSDate

    annualMeans = [0] * 120
    annualCount = [0] * 120
    #120 arbitary, means program can only handle a range of 120 years

    yearIndex = 0
    for entry in pettittArray:
        if entry != globalMissingCode and checkThreshold(entry):
            annualMeans[yearIndex] += entry
            annualCount[yearIndex] += 1
        
        currentDate = increaseDate(currentDate, 1)
        yearIndex = currentDate.year - globalSDate.year

    del(annualMeans[yearIndex:120])
    del(annualCount[yearIndex:120])

    yearsOk = 0
    for i in range(yearIndex):
        if annualCount[i] >= ptPercent * 3.65 and annualCount[i] > 0:
            annualMeans[i] = annualMeans[i] / annualCount[i]
            yearsOk += 1
        else:
            annualMeans[i] = globalMissingCode
    
    if yearsOk < 5:
        return globalMissingCode
    else:
        pettittData = []
        for entry in annualMeans:
            if entry != globalMissingCode:
                pettittData.append(entry)
        print(runPettittTest(pettittData))

if __name__ == '__main__':
    #Module tests go here
    print(qualityCheck(selectedFile))
    #qualityCheck("C:\\Users\\ajs25\\Downloads\\Dummy Annual.txt")
    #runPettittTest([2, 3, 4, 5, 6, 7, 8, 9, 10, 100, 120, 145, 145, 555, 444, 333, 333, 333, 333, 333])