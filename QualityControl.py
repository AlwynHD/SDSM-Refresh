import datetime
import math
import calendar

#region Global Variables

#Currently accessing local file, change as needed for your own version.
selectedFile = "predictand files/NoviSadPrecOBS.dat"
outlierFile = "outlier.txt"

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
        
    return

def checkThreshold(value):
    return not applyThresh or value > thresh

#endregion

def dailyMeans():
    if not checkForFile(selectedFile, "You must select a file to check first"):
        return
    
    checkIfFileFormatted(selectedFile)

    #Initialise results to zero
    dailyStats = []
    for i in range(0, 7):
        dailyStats.append([0, 0, 0, 0])
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

def outliersID():
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

def qualityCheck():
    if not checkForFile(selectedFile, "You must select a file to check first."):
        return
    
    petArray = []
    sum = 0
    max = 0
    min = 0
    threshCount = 0
    prevValue = globalMissingCode
    maxDifference = 0
    totalNumbers = 0
    count = 0
    missing = 0
    
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

                    #Is there a way to do these if statements in one line?
            
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

    #Call pettittTest

    print("Min: " + str(min) + "\nMax: " + str(max) + "\nTotal Values: " + str(count) + "\nMissing Values: " + str(missing) + "\nMean: " + str(mean))

def pettittTest(petArray, totalOk, totalNumbers, ptPercent):
    if (not applyThresh and totalOk < 10) or (applyThresh and thresh < 10):
        pettitt = globalMissingCode
        return
    
    currentDay = globalSDate.day
    currenMonth = globalSDate.month
    currentYear = globalSDate.year

    annualMeans = []
    annualCount = []

    yearIndex = 1
    for i in range(totalNumbers):
        if petArray[i] != globalMissingCode:
            if checkThreshold(petArray[i]):
                annualMeans[yearIndex] += petArray[i]
                annualCount[yearIndex] += 1

        if i < totalNumbers:
            increaseDate(currentDay, 1)
            yearIndex = currentYear - globalSDate.year
            #todo placeholder numbers, will correct later

        yearsOk = 0
        for i in range(yearIndex):
            if annualCount[i] >= 3.65 * ptPercent and annualCount[i] > 0:
                annualMeans[i] = annualMeans / annualCount[i]
                yearsOk += 1
            else:
                annualMeans[i] = globalMissingCode

        if yearsOk < 5:
            pettitt = globalMissingCode
        else:
            petMatrix = []
            yearsOk = 0
            for i in range(yearIndex):
                if annualMeans != globalMissingCode:
                    petMatrix[yearsOk][0] = annualMeans[i]
                    petMatrix[yearsOk][1] = yearsOk + 1
                    petMatrix[yearsOk][5] = i + globalSDate.year #Might need to minus 1 from this

                    yearsOk += 1

            petMatrix.sort() #Need to compare how python and VB do sorting
            for i in range(yearsOk - 1):
                petMatrix[i][2] = i + 1
                
            for i in range(yearsOk - 1):
                if petMatrix[i][0] == petMatrix[i - 1][0]:
                    petMatrix[i][2] = petMatrix[i - 1][2]
            
            petMatrix.sort() #todo sort matrix by 2nd column

            for i in range(yearsOk - 1):
                petMatrix[i][3] = yearsOk + 1 - (2 * petMatrix(i, 2))

            petMatrix[0][4] = petMatrix[0][3]

            for i in range(yearsOk - 1):
                petMatrix[i][4] = petMatrix[i - 1][4] + petMatrix[i][3]

            for i in range(yearsOk - 1):
                petMatrix[i][4] = abs(petMatrix[i][4])

            kn = -1
            maxPos = 0
            for i in range(yearsOk - 1):
                if petMatrix[i][4] > kn:
                    kn = petMatrix[i][4]
                    maxPos = i

            pettitt = 2 * math.e ** ((-6 * (kn ** 2)) / ((yearsOk ** 3) + (yearsOk ** 2)))
            #todo check this to ensure I wrote this formula correctly

            #todo update results screen with all the data calculated
    

def increaseDate(currentDate, noDays): #todo check if the leap year thing was important
    """increases datatime object by noDays"""
    #Taken from ScreenVars
    currentDate += datetime.timedelta(days=noDays)
    return currentDate

outliersID()