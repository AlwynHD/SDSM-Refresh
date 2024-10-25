import math
from PyQt5.QtWidgets import QApplication, QFileDialog
import datetime
import os 
import re
import numpy as np

predictorSelected = ['C:/Code/SDSM/SDSM-Refresh/predictor files/ncep_dswr.dat'] #todo remove default
predictandSelected = ['C:/Code/SDSM/SDSM-Refresh/predictand files/NoviSadPrecOBS.dat'] #todo remove default
nameOfFiles = ["NoviSadPrecOBS", "ncep_dswr"]
globalSDate = datetime.datetime(1948, 1, 1)
fSDate = datetime.datetime(1948, 1, 1)
fEDate = datetime.datetime(2015, 12, 31)
analysisPeriod = ["Annual", "Winter", "Spring", "Summer", "Autumn", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
analysisPeriodChosen = 0
autoRegressionTick = True

def partialCorrelation(A, B, n, crossCorr, corrArrayList):
    #print(f"A: {A} B: {B}, n: {n}, \n crossCorr: {crossCorr} \n CorrArrayList: {corrArrayList}")
    # Calculates partial correlation of the form r12.34567 etc.
    # In the form; rab.corrArrayList(n); where n signifies how many terms we want from global array
    r13 = 0
    r23 = 0
    denom = 0
    result = ""
    if n == 1:
        result = crossCorr[A][B] - ( crossCorr[A][int(corrArrayList[0])] * crossCorr[B][int(corrArrayList[0])] )
        denom = (1 - crossCorr[A][int(corrArrayList[0])] ** 2) * (1 - crossCorr[B][int(corrArrayList[0])] ** 2)
    else:                #r12.34567etc... case - calculate r12.3456, r17.3456, r27.3456 for example
        result = partialCorrelation(A, B, n - 1, crossCorr, corrArrayList)     #r12.3456 for r12.34567 for example
        r13 = partialCorrelation(A, int(corrArrayList[n]), n - 1, crossCorr, corrArrayList) #r17.3456 for r12.34567 for example
        r23 = partialCorrelation(B, int(corrArrayList[n]), n - 1, crossCorr, corrArrayList) #r27.3456 for r12.34567 for example
        result = result - (r13 * r23)
        denom = (1 - r13 ** 2) * (1 - r23 ** 2)

    if denom <= 0:                          #Trap errors - return -1 if a problem occurs
        return -1
    else:
        return result / math.sqrt(denom)

def displayFiles(fileSelected):
    selected_files = selectFile()
    if selected_files:
        for file in selected_files:
            fileName = os.path.basename(file)
            print("Selected file: ", {fileName})
            fileSelected.append(file)
    else:
        print("No file selected.")
    return fileSelected

def selectFile():
    app = QApplication([])
    file_dialog = QFileDialog()
    file_dialog.setFileMode(QFileDialog.ExistingFiles)
    file_dialog.setNameFilter("DAT files (*.DAT)")
    if file_dialog.exec_():
        files = file_dialog.selectedFiles()
        return files

def filesNames(fileName):
    
    # file name is the (i,0) and description is (i,1)

    fileDescriptionList = [["temp", "Mean temperature at 2m"], ["mslp", "Mean sea level pressure"], ["p500", "500 hPa geopotential height"], ["p850", "850 hPa geopotential height"],
                       ["rhum", "Near surface relative humidity"], ["r500", "Relative humidity at 500 hPa"], ["r850", "Relative humidity at 850 hPa"], ["sphu", "Near surface specific humidity"],
                       ["p__f", "Surface airflow strength"], ["p__z", "Surface vorticity"], ["p__v", "Surface meridional velocity"], ["p__u", "Surface zonal velocity"],
                       ["p_th", "Surface wind direction"], ["p_zh", "Surface divergence"], ["p5_f", "500 hPa airflow strength"], ["p5_z", "500 hPa vorticity"],
                       ["p5_v", "500 hPa meridional velocity"], ["p5_u", "500 hPa zonal velocity"], ["p5th", "500 hPa wind direction"], ["p5zh", "500 hPa divergence"],
                       ["p8_f", "850 hPa airflow strength"], ["p8_z", "850 hPa vorticity"], ["p8_v", "850 hPa meridional velocity"], ["p8_u", "850 hPa zonal velocity"],
                       ["p8th", "850 hPa wind direction"], ["p8zh", "850 hPa divergence"], ["shum", "Surface specific humidity"], ["s850", "Specific humidity at 850 hPa"],
                       ["s500", "Specific humidity at 500 hPa"], ["dswr", "Solar radiation"], ["lftx", "Surface lifted index"], ["pottmp", "Potential temperature"],
                       ["pr_wtr", "Precipitable water"]]

    # will return file description e.g. Mean temperature at 2m if the fileName is found in the list file Description will be empty if it's not there
    fileDescription = [record[1] for record in fileDescriptionList if re.search(re.compile(record[0]),fileName) != None] # regex

    return fileDescription

def resetFiles(predictorSelected):
    return predictorSelected.clear()

def increaseDate(currentDate, noDays): #todo check if the leap year thing was important
    currentDate += datetime.timedelta(days=noDays)
    return currentDate

def sigLevel_OK():
    correctSigValue = False
    sigLevelInput = 0.05 #todo get this from the user
    if sigLevelInput == "" or not type(sigLevelInput) is int:              #SigLevelText is the input from the user
        #todo error message to user orgianl: MsgBox "Significance level must be a value.", 0 + vbCritical, "Error Message" 
        sigLevelInput.Text = 0.05
    else:
        if sigLevelInput > 0.999 or sigLevelInput < 0:
            #todo error message to user orginal: MsgBox "Significance level must be positive and less than 1.", 0 + vbCritical, "Error Message"
            sigLevelInput = 0.05
        else:
            if sigLevelInput == 0.1111:
                print("BlankFrm.Show") #todo figure out why this is here in the first place and what BlankFrm.Show does in vb
            else:
                sigLevel = sigLevelInput
                correctSigValue = True
    return correctSigValue

def fSDateOK(fSDate, feDate, globalDate):

    output = False
    if not isinstance(fSDate, datetime.datetime):
        #todo error message to user about correct date orginal MsgBox "Start date is invalid - it must be in the format dd/mm/yyyy.", 0 + vbCritical, "Error Message"
        fSDate = datetime.datetime.now() #todo figure out what GlobalSDate is pretty sure it might be record start date
    elif (fSDate - feDate).days < 1:
        #todo error message to user about correct date orginal MsgBox "End date must be later than start date.", 0 + vbCritical, "Error Message"
        fSDate = fSDate = datetime.datetime.now() #todo figure out what GlobalSDate is 
    elif (fSDate - globalDate).days < 0:
        #todo error message to user about correct date orginal MsgBox "Fit start date must be later than record start date.", 0 + vbCritical, "Error Message"
        fSDate = fSDate = datetime.datetime.now() #todo figure out what GlobalSDate is 
    else:
        ouput = True 
    return output

def correlation(predictandSelected, predictorSelected, fSDate, fEDate, autoRegressionTick):
    if predictandSelected == "":
        print("You must select a predictand.") # todo proper error message
    elif len(predictorSelected) < 1:
        print("You must select at least one predictor.") # todo proper error message
    elif len(predictorSelected) > 12:
        print("Sorry - you are allowed a maximum of 12 predictors only.") #todo proper error message
    else:
        nVariables = len(predictorSelected) + 1

        loadedFiles = []
        loadedFiles = loadFilesIntoMemory(predictorSelected, predictandSelected)
        
        #skip unwanted date
        # not needed here firstValid = findDataStart(loadedFiles[0])
        #todo progress bar

        totalNumbers = 0
        totalMissing = 0 
        totalMissingRows = 0
        totalBelowThreshold = 0

        #todo imporant from settings
        threshold = 0 
        missingCode = -999
        workingDate = fSDate
        conditional = False

        inputData = []
        sumData = np.zeros(nVariables)

        for i in range((fEDate - fSDate).days):
        #for i in range(5000, 5010):
            if dateWanted(workingDate, 0):
                totalNumbers += 1    
                row = [file[i] for file in loadedFiles]

                missingNumber = row.count(missingCode)

                # there are missingCodes
                if missingNumber > 0:
                    totalMissingRows += 1
                    totalMissing += missingNumber

                # there is no missingCodes
                elif (conditional and row[0] > threshold) or not conditional:
                    sumData += row

                # the threshold only applies to the predictand file not the predictor files
                if row[0] <= threshold and conditional and row[0] != missingCode:
                    totalBelowThreshold +=1

                # old code kept until proof current code is what was actually meant
                # totalBelowThreshold += len([num for num in row if num <= threshold and conditional == True and num != missingCode])

                inputData.append(row)
            increaseDate(workingDate, 1)

        inputData = np.array(inputData)
        print(totalNumbers, totalMissing, totalMissingRows, totalBelowThreshold)

        
        if autoRegressionTick:
            nVariables +=1
            first_column = inputData[:, 0]

            # create a new column for position 3 with the first element shifted down
            new_column = np.roll(first_column, 1)
            new_column[0] = 0  # Replace the first element with 0 or any placeholder value
            
            # Append the new column to the original array
            inputData = np.hstack((inputData, new_column.reshape(-1, 1)))
            
            if inputData[totalNumbers - 1, 0] != missingCode and (not (inputData[totalNumbers - 1, 0] <= threshold) and conditional):
                sumData = np.append(sumData, inputData[totalNumbers - 1, 0])
                
            else:
                sumData = np.append(sumData, sumData[0])
                nameOfFiles.append("Autoregression")
            # FileList.AddItem "Autoregression"    


        xBar = np.array([total/(totalNumbers - totalMissingRows - totalBelowThreshold) for total in sumData])

        sumresid = sqresid = np.zeros(nVariables)
        prodresid = np.zeros((nVariables, nVariables))

        for i in range(totalNumbers):
            row = inputData[i]

            if not (missingCode in row) and ((conditional and row[0] > threshold) or not conditional):
                sumData += row
                resid = np.array([row[i]-xBar[i] for i in range(row.size)])
                sumresid += resid
                sqresid += [res**2 for res in resid]
                prodresid += np.outer(resid, resid)
        
        sd = np.array([(number/(totalNumbers - 1 - totalMissingRows - totalBelowThreshold)) ** 0.5 for number in sqresid])

        # Print Header Information
        print("CORRELATION MATRIX")
        print()
        print(f"Analysis Period: {fSDate} - {fEDate} ({analysisPeriod[analysisPeriodChosen]})")
        print()
        print(f"Missing values: {totalMissing}")
        print(f"Missing rows: {totalMissingRows}")
        if conditional:
            print(f"Values less than or equal to threshold: {totalBelowThreshold}")
        print()

        max_length = max(len(file) for file in nameOfFiles) + 1

        # Print column headers
        print(" ", end="")
        for j in range(1, nVariables + 1):
            print(f" {j:{max_length + 1}}", end="")
        print()

        # Print Cross Correlation Matrix
        crossCorr = np.zeros((nVariables, nVariables))
        for j in range(nVariables):
            print(f"{j+1} ", end="")
            print(f"{nameOfFiles[j]:{max_length}}", end="")
            
            for k in range(nVariables):
                crossCorr[j, k] = prodresid[j, k] / ((totalNumbers - 1 - totalMissingRows - totalBelowThreshold) * sd[j] * sd[k])
                tempY = f"{crossCorr[j, k]:.3f}"
                if k == j:
                    tempY = "1"
                print(f"{tempY:{max_length + 2}}", end="")
            print()
        print()

        # Check Partial Correlations
        if nVariables < 3:
            print("NO PARTIAL CORRELATIONS TO CALCULATE")
        else:
            print("PARTIAL CORRELATIONS WITH", nameOfFiles[0])
            print()

            print(" " *24, end="")
            print(f"{'Partial r':12}{'P value':12}")
            print()
            
            for i in range(1, nVariables):
                corrArrayList = np.zeros(nVariables + 1)
                arrayCount = 0
                for j in range(1, nVariables):
                    if i != j:
                        corrArrayList[arrayCount] = j
                        arrayCount += 1
                
                tempResult = partialCorrelation(0, i, nVariables-2, crossCorr, corrArrayList)
                
                if abs(tempResult) < 0.999:
                    TTestValue = (tempResult * np.sqrt(totalNumbers - 2 - totalMissingRows - totalBelowThreshold)) / np.sqrt(1 - (tempResult ** 2))
                    PrValue = (((1 + ((TTestValue ** 2) / (totalNumbers - totalMissingRows - totalBelowThreshold))) ** -((totalNumbers + 1 - totalMissingRows - totalBelowThreshold) / 2))) / (np.sqrt((totalNumbers - totalMissingRows - totalBelowThreshold) * np.pi))
                    PrValue = PrValue * np.sqrt(totalNumbers - totalMissingRows - totalBelowThreshold)  # Correction for large N
                else:
                    TTestValue = 0
                    PrValue = 1
                    tempResult = 0

                print(f"{nameOfFiles[i]:24}{tempResult:<12.3f}{PrValue:<12.3f}")
                
                


 
def loadFilesIntoMemory(predictorSelected, predictandSelected):
    loadedFiles = []
    loadedFiles.append(np.loadtxt(predictandSelected[0]))
    for fileLocation in predictorSelected:
        loadedFiles.append(np.loadtxt(fileLocation))
    return loadedFiles
    
def findDataStart(predictandFile): # gets predictand numpy array then gets the position of the first data position
    firstData = predictandFile[predictandFile != -999]
    if firstData.size == 0:
        return None  # All values are errors
    return np.where(predictandFile == firstData[0])[0][0]

def dateWanted(date, analysisPeriodChosen):
    answer = False
    if analysisPeriodChosen == 0:                #Annual selected so want all data
        answer = True
    elif analysisPeriodChosen == 1:            #Winter - DJF
        if date.month == 12 or date.month == 1 or date.month == 2:
            answer = True
    elif analysisPeriodChosen == 2:            #Spring - MAM
        if date.month == 3 or date.month == 4 or date.month == 5:
            answer = True
    elif analysisPeriodChosen == 3:             #Summer - JJA
        if date.month == 6 or date.month == 7 or date.month == 8:
            answer = True
    elif analysisPeriodChosen == 4:            #Autumn - SON
        if date.month == 9 or date.month == 10 or date.month == 11:
            answer = True
    else:
        if date == (analysisPeriodChosen - 4):
            answer = True     #Individual months
    return answer


loadedFiles = []
loadedFiles = loadFilesIntoMemory(predictorSelected, predictandSelected)
firstValid = findDataStart(loadedFiles[0])
correlation(predictandSelected, predictorSelected, fSDate, fEDate, autoRegressionTick)



def miniReset():
    print("haha die")

def newProgressBar(ProgressPicture, ProgValue, number, text):
    print("haha die")

def setSeason():
    print("haha die")
