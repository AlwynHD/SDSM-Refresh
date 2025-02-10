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

#Reset All
    #Reset all fields on the form to their default values

def dailyMeans():
    if selectedFile is None:
        #Display error message asking user to select a file
        print("You must select a file to check first.")
        return
    
    #In original VB code, file is checked to see if it contains multiple columns or linux line breaks
    #This is done by checking the first line only, unsure of how to convert.

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
                if not applyThresh or line > thresh:
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
                if not applyThresh or line > thresh:
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
    if selectedFile is None:
        #Display error message asking user to select a file
        print("You must select a file to check first.")
        return
    elif outlierFile is None:
        print("You must select a file to save outliers to.")
        return
    
    #Same process of checking if the file is formatted properly as in dailyMeans.

    #Calculate mean
    sum = 0
    goodCount = 0

    with open(selectedFile, "r") as file:
        for line in file:
            line = line.rstrip('\n')
            if line != str(globalMissingCode):
                if not applyThresh or line > thresh:
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
                    if not applyThresh or line > thresh:
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
                if not applyThresh or line > thresh:
                    if float(line) > (mean + standardDeviationRange) or float(line) < (mean - standardDeviationRange):
                        outFile = open(outlierFile, "a")
                        outFile.write(str(counter) + "\t" * 3 + line)
                        outFile.close()
                        outlierCount += 1
            counter += 1

    message = str(outlierCount) + " outliers identified and saved to file."
    print(message)

#QualityCheck --> Check File

#PettittTest --> Called when check file is run

#IncreaseDate --> Called in PettittTest