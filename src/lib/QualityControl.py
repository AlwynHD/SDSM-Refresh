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

standardDeviationLimits = 1

#region old stuff

def checkThreshold(value):
    return not applyThresh or value > thresh

def dailyMeans(selectedFile):
    if not checkForFile(selectedFile, "You must select a file to check first"):
        return
    
    checkIfFileFormatted(selectedFile)

    #returnOutput = [] this is here for if we decide to change how its displayed in GUI

    #Initialise results to zero
    dailyStats = np.zeros((7, 4), float)
    """
    dailyStats[i][0] is running sum
    dailyStats[i][1] is count
    dailyStats[i][2] is standard deviation
    dailyStats[i][3] is mean
    """

    dayWorkingOn = globalSDate.weekday()

    #Read file and add values to array
    #TODO open file
    loadedFiles = loadFilesIntoMemory([selectedFile])[0]

    for datapoint in loadedFiles:
        if datapoint != globalMissingCode and checkThreshold(datapoint):
            dailyStats[dayWorkingOn][0] += datapoint #Add to cumulative sum
            dailyStats[dayWorkingOn][1] += 1           #Increase count for that day

        #Iterate dayWorkingOn
        dayWorkingOn = (dayWorkingOn + 1) % 7

    #Calulcate means for each day

    for stat in dailyStats:
        stat[3] = stat[0] / stat[1] if stat[1] > 0 else globalMissingCode

    #Calculate standard deviation
    dayWorkingOn = globalSDate.weekday()

    for datapoint in loadedFiles:
            if datapoint != globalMissingCode and dailyStats[dayWorkingOn][3] != globalMissingCode and checkThreshold(datapoint):
                dailyStats[dayWorkingOn][2] += (datapoint - dailyStats[dayWorkingOn][3]) ** 2

            #Iterate dayWorkingOn
            dayWorkingOn = (dayWorkingOn + 1) % 7
    


    for stat in dailyStats:
        stat[2] = math.sqrt(stat[2] / stat[1]) if stat[1] > 0 else globalMissingCode

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
    
    loadedFiles = loadFilesIntoMemory([selectedFile])[0]

    for datapoint in loadedFiles:
        if datapoint != str(globalMissingCode) and checkThreshold(datapoint):
                sum += datapoint
                count += 1
    """old code
        #TODO open file
        with open(selectedFile, "r") as file:
            for line in file:
                line = line.rstrip('\n')
                if line != str(globalMissingCode) and checkThreshold(float(line)):
                    sum += float(line)
                    count += 1

        file.close()"""

    if count > 0:
        mean = sum / count
    else:
        mean = globalMissingCode


    #Calculate standard deviation
    standardDeviation = 0

    if mean != globalMissingCode:
        for datapoint in loadedFiles:
            if datapoint != globalMissingCode and checkThreshold(datapoint):
                standardDeviation += (datapoint - mean) ** 2

        

        """old code
        with open(selectedFile, "r") as file:
            for line in file:
                line = line.rstrip('\n')
                if line != str(globalMissingCode):
                    if checkThreshold(line):
                        standardDeviation += (float(line) - mean) ** 2

        file.close()"""

        standardDeviation = math.sqrt(standardDeviation / count)
    else:
        standardDeviation = globalMissingCode

    #Go through data to pick outliers
    standardDeviationRange = standardDeviation * standardDeviationLimits
    outlierCount = 0
    counter = 1

    
    for datapoint in loadedFiles:
        if datapoint != globalMissingCode and checkThreshold(datapoint):
            if datapoint > (mean + standardDeviationRange) or datapoint < (mean - standardDeviationRange):
                #TODO figure out if this needs to change
                outFile = open(outlierFile, "a")
                outFile.write(str(counter) + "\t" * 3 + str(datapoint))
                outFile.close()
                outlierCount += 1
        counter += 1

    """old code
    with open(selectedFile, "r") as file:
        for line in file:
            if line != str(globalMissingCode):
                if checkThreshold(float(line)):
                    if float(line) > (mean + standardDeviationRange) or float(line) < (mean - standardDeviationRange):
                        outFile = open(outlierFile, "a")
                        outFile.write(str(counter) + "\t" * 3 + line)
                        outFile.close()
                        outlierCount += 1
            counter += 1"""

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
    
    loadedFiles = loadFilesIntoMemory([selectedFile])[0]

    for datapoint in loadedFiles:
        inputValue = datapoint
        
        petArray.append(inputValue)
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


    """ 
    old code
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
    """

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

    print("Min: " + str(min) + "\nMax: " + str(max) + "\nMean: " + str(mean) + "\nValues in file: " + str(count + missing) + "\nMissing Values: " + str(missing) + "\nGood Values: " + str(count) + "\nMax Difference: " + str(maxDifference) + "\nMax Differenece Value 1: " + str(maxDiffValue1) + "\nMax Differenece Value 2: " + str(maxDiffValue2) + "\nValues above threshold: " + str(threshCount) + "\nPettitt: " + str(pettitt) + "\nPettitt Max Pos: " + str(0) + "\nGlobal Missing Code: " + str(globalMissingCode) + "\nEvent Threshold: " + str(thresh))
    return str(min), str(max), str(count), str(missing), str(mean),  str(maxDifference), str(maxDiffValue1), str(maxDiffValue2), str(threshCount), str(pettitt), str(0), str(globalMissingCode), str(thresh)

def pettittTest(pettittArray, ptPercent):
    #todo Ask for Chris help, things seem very wrong.
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

        currentDate = increaseDate(currentDate, 1, leapYear)
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
        test = []
        yearsOk = 0
        for i in range(yearIndex):
            if annualMeans[i] != globalMissingCode:
                test.append(annualMeans[i])
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
        print("pettitt Value: " + str(pettitt))

        if pettitt < 0.05:
            print("max position: " + str(petMatrix[maxPos][5]))

#endregion

def valueIsValid(value, applyThresh):
    return value != globalMissingCode and (not applyThresh or value > thresh)

def dailyMeansNew(data, applyThresh):
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

def getOutliersNew(data, sdFilterValue, applyThresh):
    #todo return location of data
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

    outputData = []
    for i in range(len(outliers)):
        outputData.append([index[i], outliers[i]])

    infoString = str(len(outliers)) + " outliers identified and written to file."
    return outputData, infoString

if __name__ == '__main__':
    file = selectFile()
    data = loadFilesIntoMemory(file)[0]
    pettittPercent = 90
    applyThresh = False
    standardDeviations = 5