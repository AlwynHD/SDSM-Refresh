import datetime
import math
import calendar

#region Global Variables

#Currently accessing local file, change as needed for your own version.
selectedFile = r"C:\Users\ajs25\Downloads\test.txt"
outlierFile = r"C:\Users\ajs25\Downloads\outlier.txt"

globalSDate = datetime.datetime(1948, 1, 1)
globalMissingCode = -999

applyThresh = False
thresh = 0

standardDeviationLimits = 0

#endregion

#region New Functions

def checkForFile(selectedFile, errorMessage):
    if selectedFile is None:
        print(errorMessage)
        return False
    else:
        return True
    
def checkThreshold(value):
    return value > thresh or not applyThresh

#endregion

#Reset All
    #Reset all fields on the form to their default values

def dailyMeans():
    if not checkForFile(selectedFile, "You must select a file to check first"):
        return
    
    #todo In original VB code, file is checked to see if it contains multiple columns or linux line break. This is done by checking the first line only, unsure of how to convert.

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
            if line != str(globalMissingCode): #Unsure if cast is needed, could just write globalMissingCode as string
                if checkThreshold(line):
                    dailyStats[dayWorkingOn][0] += float(line) #Add to cumulative sum
                    dailyStats[dayWorkingOn][1] += 1         #Increase count of 'good' values read in on that day    

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
    dayWorkingOn = globalSDate.weekday() #reset dayWorkingOn

    with open(selectedFile, "r") as file:
        for line in file:
            line = line.rstrip('\n')
            if line != str(globalMissingCode) and dailyStats[dayWorkingOn][3] != globalMissingCode:
                if checkThreshold(line):
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
    if not checkForFile(outlierFile, "You must select a file to save outliers to"):
        return
    elif outlierFile is None:
        print("You must select a file to save outliers to.")
        return
    
    #todo Same process of checking if the file is formatted properly as in dailyMeans.

    #Calculate mean
    sum = 0
    goodCount = 0

    with open(selectedFile, "r") as file:
        for line in file:
            line = line.rstrip('\n')
            if line != str(globalMissingCode):
                if checkThreshold(line):
                    sum += float(line)
                    goodCount += 1

    file.close()

    if goodCount > 0:
        mean = sum / goodCount
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

        standardDeviation = math.sqrt(standardDeviation / goodCount)
    else:
        standardDeviation = globalMissingCode

    #Go through data to pick outliers
    standardDeviationRange = standardDeviation * standardDeviationLimits
    outlierCount = 0
    counter = 1
    with open(selectedFile, "r") as file:
        for line in file:
            if line != str(globalMissingCode):
                if checkThreshold(line):
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
    
    #Todo Check if file is formatted correctly.

def pettittTest(petArray, totalOk, totalNumbers):
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
            #todo placeholder numbers, will correct later
    
    

def increaseDate(currentDate, noDays): #todo check if the leap year thing was important
    """increases datatime object by noDays"""
    #Taken from ScreenVars
    currentDate += datetime.timedelta(days=noDays)
    return currentDate