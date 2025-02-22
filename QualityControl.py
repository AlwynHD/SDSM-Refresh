import calendar
import datetime
import math
import numpy as np
from ScreenVars import loadFilesIntoMemory, increaseDate

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

def dailyMeans():
    if not checkForFile(selectedFile, "You must select a file to check first"):
        return
    
    checkIfFileFormatted(selectedFile)

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
    
    print(output)

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

    print("Min: " + str(min) + "\nMax: " + str(max) + "\nTotal Values: " + str(count) + "\nMissing Values: " + str(missing) + "\nMean: " + str(mean))
    return str(min), str(max), str(count), str(missing), str(mean)

def pettittTest(pettittArray, ptPercent):
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

    yearsOk = 0
    for i in range(yearIndex):
        if annualCount[i] > 0 and annualCount[i] >= (ptPercent * 3.65):
            annualMeans[i] /= annualCount[i]
            yearsOk += 1
        else:
            annualMeans[i] = globalMissingCode
    
    if yearsOk < 5:
        pettitt = globalMissingCode
    else:
        petMatrix = np.zeros((yearsOk, 7), float) 
        yearsOk = 0
        for i in range(yearIndex):
            if annualMeans[i] != globalMissingCode:
                petMatrix[yearsOk][0] = annualMeans[i]
                petMatrix[yearsOk][1] = yearsOk
                petMatrix[yearsOk][5] = i + globalSDate.year
                yearsOk += 1
        
        petMatrix[petMatrix[:, 0].argsort()]
        #sort data on itself

        for i in range(yearsOk):
            petMatrix[i][2] = i + 1
        
        for i in range(1, yearsOk):
            if petMatrix[i][0] == petMatrix[i - 1][0]:
                petMatrix[i][2] = petMatrix[i][2]
        
        petMatrix[petMatrix[:, 1].argsort()]
        #sort data back to original order

        for i in range(yearsOk):
            petMatrix[i][3] = yearsOk + 1 - (2 * petMatrix[i][2])
            #create vi value

        #create ui value:
        petMatrix[0][4] = petMatrix[0][3]
        for i in range(1, yearsOk - 1):
            petMatrix[i][4] = petMatrix[i - 1][4] + petMatrix[i][3]

        for i in range(yearsOk):
            petMatrix[i][4] = abs(petMatrix[i][4])

        kn = -1
        maxPos = 0
        for i in range(yearsOk):
            if petMatrix[i][4] > kn:
                kn = petMatrix[i][4]
                maxPos = i

        pettitt = 2 * math.pow(math.e, ((-6 * kn ** 2) / ((yearsOk ** 3) + yearsOk ** 2)))
        #todo, fix calculation
        print("pettitt Value: " + str(pettitt))

        if pettitt < 0.05:
            print("max position: " + str(petMatrix[maxPos][5]))
if __name__ == '__main__':
    #Module tests go here
    qualityCheck(selectedFile)