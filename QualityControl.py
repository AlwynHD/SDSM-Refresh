import datetime

#region Global Variables

#Currently accessing local file, change as needed for your own version.
selectedFile = r"C:\Users\ajs25\Downloads\test.txt"

globalSDate = datetime.datetime(1948, 1, 1)
globalMissingCode = -999

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
                if True: #There exist conditions in the original program that should be checked here. Need to update soon.
                    dailyStats[dayWorkingOn][0] += int(line) #Add to cumulative sum
                    dailyStats[dayWorkingOn][1] += 1         #Increase count of 'good' values read in on that day    

            #Iterate dayWorkingOn
            if dayWorkingOn == 6:
                dayWorkingOn = 0
            else:
                dayWorkingOn += 1

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
            if line != str(globalMissingCode) and dailyStats[dayWorkingOn] != globalMissingCode:
                if True: #If we are applying a threshold, check the input value is above it.
                    dailyStats[dayWorkingOn][2] += (int(line) - dailyStats[dayWorkingOn][3]) ** 2

            #Iterate dayWorkingOn
            if dayWorkingOn == 6:
                dayWorkingOn = 0
            else:
                dayWorkingOn += 1

    for i in range(7):
        if dailyStats[i][1] > 0:
            dailyStats[i][2] = dailyStats[i][2] / dailyStats[i][1]
        else:
            dailyStats[i][2] = globalMissingCode

    output = "Sunday: Mean: " + str(round(dailyStats[6][3], 2)) + " SD: " + str(round(dailyStats[6][2], 2)) + "\n" +\
             "Monday: Mean: " + str(round(dailyStats[0][3], 2)) + " SD: " + str(round(dailyStats[0][2], 2)) + "\n" +\
             "Tuesday: Mean: " + str(round(dailyStats[1][3], 2)) + " SD: " + str(round(dailyStats[1][2], 2)) + "\n" +\
             "Wednesday: Mean: " + str(round(dailyStats[2][3], 2)) + " SD: " + str(round(dailyStats[2][2], 2)) + "\n" +\
             "Thursday: Mean: " + str(round(dailyStats[3][3], 2)) + " SD: " + str(round(dailyStats[3][2], 2)) + "\n" +\
             "Friday: Mean: " + str(round(dailyStats[4][3], 2)) + " SD: " + str(round(dailyStats[4][2], 2)) + "\n" +\
             "Saturday: Mean: " + str(round(dailyStats[5][3], 2)) + " SD: " + str(round(dailyStats[5][2], 2)) + "\n"
    
    print(output)

dailyMeans()

#OutliersID --> Calulcate outliers

#QualityCheck --> Check File

#PettittTest --> Called when check file is run

#IncreaseDate --> Called in PettittTest