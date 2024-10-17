import math
from PyQt5.QtWidgets import QApplication, QFileDialog
import datetime
import os 
import re
import numpy as np

predictorSelected = ['C:/Code/SDSM/SDSM-Refresh/predictor files/test_dswr.dat'] #todo remove default
predictandSelected = ['C:/Code/SDSM/SDSM-Refresh/predictand/NoviSadPrecOBS.dat'] #todo remove default
globalSDate = datetime.datetime(1948, 1, 1)
fSDate = datetime.datetime(1948, 1, 1)
fEDate = datetime.datetime(2015, 12, 31)
analysisPeriod = ["Annual", "Winter", "Spring", "Summer", "Autumn", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
analysisPeriodChosen = 0

def PCorr(A, B, n, CrossCorr, CorrArrayList):
    # Calculates partial correlation of the form r12.34567 etc.
    # In the form; rab.CorrArrayList(n); where n signifies how many terms we want from global array
    results, r13, r23, denom = float()
    if n == 1:
        result = CrossCorr(A, B) - (CrossCorr(A, CorrArrayList(1)) * CrossCorr(B, CorrArrayList(1)))
        denom = (1 - CrossCorr(A, CorrArrayList(1)) ^ 2) * (1 - CrossCorr(B, CorrArrayList(1)) ^ 2)
    else:                #r12.34567etc... case - calculate r12.3456, r17.3456, r27.3456 for example
        result = PCorr(A, B, n - 1)     #r12.3456 for r12.34567 for example
        r13 = PCorr(A, CorrArrayList(n), n - 1) #r17.3456 for r12.34567 for example
        r23 = PCorr(B, CorrArrayList(n), n - 1) #r27.3456 for r12.34567 for example
        result = result - (r13 * r23)
        denom = (1 - r13 ^ 2) * (1 - r23 ^ 2)

    if denom <= 0:                          #Trap errors - return -1 if a problem occurs
        PCorr = -1
    else:
        PCorr = result / math.sqrt(denom)

""""
def Correlation():                       #Calculates correlations and partial correlations
    predictorfileNo, subloop, i, j, k = int()
    tempResult = float()
    x(21, 52000) = float()
    dummy =  float()                        #Dummy to read in unwanted values
    ProgValue = int()                     # for the progress bar
    Sum = "None" * 21
    sd(21)
    XBAR(21)
    resid(21)
    sumresid(21)
    sqresid(21)
    prodresid(21, 21)
    TTestValue = float()
    PrValue = float()
    MissingRows = int()       #Missing rows for all data
    MissingFlag = bool()            #Missing marker
    TotalMissing = int()            #Total missing altogether was long now int
    BelowThresh = int()              #Total values read in below desired threshold
    NVariables = int()             #number of variables to analyse = predictors+predictand
    
    if PTandFile == "":            #No predictand selected
        print("You must select a predictand.", 0 + vbCritical, "Error Message")
    elif NPredictors < 1:         #No predictors selected
        print("You must select at least one predictor.", 0 + vbCritical, "Error Message")
        File2.SetFocus
    elif NPredictors > 12:         #No predictors selected
        print( "Sorry - you are allowed a maximum of 12 predictors only.", 0 + vbCritical, "Error Message")
        File2.SetFocus
    else:
        #todo make the mouse pointer look like an hour glass
        # ScreenVarsFrm.MousePointer = 11     #Hour glass
        for i in range(21):                     #Sum of each input variable
            i += i
        for i in range(50):                     #Make sure all files are closed
            #todo close files
            print("close files")
        
        Open PTandRoot for Input As 1      #Predictand file
        FileList.Clear                      #Remove any predictors from FileList just in case
        predictorfileNo = 2                 #File # of predictor file starts at 2
        for subloop in File2:  #Check for selected files
            if File2.Selected(subloop):     #if file is selected
                FileList.AddItem File2.List(subloop)    #Add to list of selected files
                Open File2.Path & "\" & File2.List(subloop) for Input As #predictorfileNo
                predictorfileNo = predictorfileNo + 1
        
        NVariables = NPredictors + 1                    #1 predictand plus all predictors

        TotalToreadIn = DateDiff("d", GlobalSDate, FSDate)       #Maximum values likely to read in at start
        if TotalToreadIn > 0:                          #Need to discard some values so show progress bar
            ProgressPicture.Visible = True                 #Show progress bar
            NewProgressBar(ProgressPicture, 0, 100, "Skipping Unnecessary Data")
        
            
        CurrentDay = Day(GlobalSDate)
        CurrentMonth = Month(GlobalSDate)
        CurrentYear = Year(GlobalSDate)
        TotalNumbers = 0                                    #Total data read in so far
        
        #This block reads in unwanted data from start of file

        while (DateDiff("d", DateSerial(CurrentYear, CurrentMonth, CurrentDay), FSDate)) <= 0:
        #---------------------
            DoEvents                                        #Check if user wants to escape processing
            if ExitAnalyses:
                miniReset()
                # exit function todo
        #---------------------
            
            for i in NVariables:
                Input #i, dummy                        #todo Read in unwanted values

            TotalNumbers = TotalNumbers + 1
            increaseDate()                           #Increase current date
            ProgValue = CInt((TotalNumbers / TotalToreadIn) * 100)
            newProgressBar(ProgressPicture, ProgValue, 100, "Skipping Unnecessary Data")
        Loop
        #------------------------------
 
        TotalToreadIn = (DateDiff("d", FSDate, FEdate)) + 1     #Max values to possibly read in now
        ProgressPicture.Visible = True                          #Show progress bar
        newProgressBar(ProgressPicture, 0, 100, "Calculating Correlation Statistics")
        CurrentDay = Day(FSDate)                                #Marker to date currently reading in
        CurrentMonth = Month(FSDate)
        CurrentYear = Year(FSDate)

        #Get maximum likely size for progress bar
        if DatesCombo.ListIndex == 0:                           #Case 0 - annual - need all data
            ProgressBarMaximum = TotalToreadIn
        elif DatesCombo.ListIndex in (1,2,3,4):                 #Seasonal - need 1/4 data
            ProgressBarMaximum = TotalToreadIn / 4              #Rough estimate of max size
        else:                                                   #Months - need 1/12 data
            ProgressBarMaximum = TotalToreadIn / 12             #Rough estimate of max size

        TotalNumbers = 0                                        #Total number we want to use
        TotalMissing = 0
        MissingRows = 0
        BelowThresh = 0
        while (DateDiff("d", DateSerial(CurrentYear, CurrentMonth, CurrentDay), FEdate)) < 0:

            DoEvents                                        #Check if user wants to escape processing
            if ExitAnalyses:
                miniReset()
                #todo pexit function
            
            if DateWanted():                            #Do we want this datum (eg January point)
                TotalNumbers = TotalNumbers + 1
                
                MissingFlag = False
                for i in NVariables:
                    Input i, x(i, TotalNumbers)
                    if x(i, TotalNumbers) == GlobalMissingCode:
                        MissingFlag = True
                        TotalMissing = TotalMissing + 1
                
                if ((x(1, TotalNumbers) <= Thresh) and (ParamOpt(0).value)) and (x(1, TotalNumbers) != GlobalMissingCode):
                    BelowThresh = BelowThresh + 1
                
                if MissingFlag: 
                    MissingRows = MissingRows + 1
                
                if ((ParmOpt(0).value) and (x(1, TotalNumbers) > Thresh)) or !(ParmOpt(0).value): 
                    for i in NVariables:
                        if not MissingFlag:
                            i = i + x(i, TotalNumbers)
                
            else                                            #Else if date not wanted
                for i in NVariables:                     #Date not needed so read in unwanted data
                    Input i, dummy #todo what does this even do
            
            
            increaseDate()                               #Increase date by one day
            
            ProgValue = CInt((TotalNumbers / ProgressBarMaximum) * 100)
            newProgressBar(ProgressPicture, ProgValue, 100, "Calculating Correlation Statistics")                                            #Read in next data
           
        #All data now read in to x(i,j)
        
        
        for i in NVariables:
            Close i #todo fix this
        
        if AutoregressionTick.value == 1:            #does the user want to calculate autoregressive component
            NVariables = NVariables + 1
            x(NVariables, 1) = 0        #not sure ??
            for i in TotalNumbers[2:]:
                x(NVariables, i) = x(1, i - 1) #only add in last value if valid
            if (x(1, TotalNumbers) != GlobalMissingCode) and not (x(1, TotalNumbers) <= Thresh) and (ParmOpt(0).value):
                Sum(NVariables) = Sum(1) - x(1, TotalNumbers)
            else:
                Sum(NVariables) = Sum(1)
            
            FileList.AddItem "Autoregression"
        
        
        Rem ** compute variable mean and sd **

        for i in NVariables:
            XBAR(i) = Sum(i) / (TotalNumbers - MissingRows - BelowThresh)

        for i in TotalNumbers:
            MissingFlag = False
            for j in NVariables:
                if x(j, i) == GlobalMissingCode: 
                    MissingFlag = True
            
            for j in NVariables:
                if ((ParmOpt(0).value) and (x(1, i) > Thresh)) or not (ParmOpt(0).value):
                    if Not (MissingFlag):
                        resid(j) = x(j, i) - XBAR(j)
                        sumresid(j) = sumresid(j) + resid(j)
                        sqresid(j) = sqresid(j) + (resid(j) ^ 2)
            
            for j in NVariables:
                if ((ParmOpt(0).value) and (x(1, i) > Thresh)) or (Not (ParmOpt(0).value)):
                    if Not (MissingFlag):
                        for k in NVariables@
                            prodresid(j, k) = prodresid(j, k) + (resid(j) * resid(k))
                    
    
        for j in NVariables:
            sd(j) = (sqresid(j) / (TotalNumbers - 1 - MissingRows - BelowThresh)) ^ 0.5
        
        Load ResultsFrm
        ResultsFrm.ResPicture.Cls
        ResultsFrm.HelpContext.Text = 2200      #Help context for correlation results
    
        ScreenVarsFrm.MousePointer = 0
        ProgressPicture.Visible = False                     #Hide progress bar

        for i in range(4):                        #Clear top menu bar
            ResultsFrm.ResPicture.Print
        
        setSeason()                          #Set ChosenSeason string
        ResultsFrm.ResPicture.Print "CorRELATION MATRIX"
        ResultsFrm.ResPicture.Print
        ResultsFrm.ResPicture.Print "Analysis Period: "; FSDate; " - "; FEdate; " ("; ChosenSeason; ")"
        ResultsFrm.ResPicture.Print
        ResultsFrm.ResPicture.Print "Missing values: "; TotalMissing
        ResultsFrm.ResPicture.Print "Missing rows: "; MissingRows
        if (ParmOpt(0).value):
            ResultsFrm.ResPicture.Print "Values less than or equal to threshold: "; BelowThresh
        
        ResultsFrm.ResPicture.Print
        ResultsFrm.ResPicture.foreColor = 500
        for j in NVariables:
            ResultsFrm.ResPicture.Print Tab((16 + (j * 8))); j;
        ResultsFrm.ResPicture.Print
        
        for j in NVariables:
            
            if j == 1:
                ResultsFrm.ResPicture.foreColor = 500
                ResultsFrm.ResPicture.Print j;
                ResultsFrm.ResPicture.foreColor = 0
                ResultsFrm.ResPicture.Print Tab(6); PTandFile;
            
            if j > 1:
                ResultsFrm.ResPicture.foreColor = 500
                ResultsFrm.ResPicture.Print j;
                ResultsFrm.ResPicture.foreColor = 0
                ResultsFrm.ResPicture.Print Tab(6); FileList.List(j - 2);
            
            for k in NVariables:
                CrossCorr(j, k) = prodresid(j, k) / ((TotalNumbers - 1 - MissingRows - BelowThresh) * sd(j) * sd(k))
                tempY = format(CrossCorr(j, k), "0.000")
                if k = j: tempY = format(1, "0")
                ResultsFrm.ResPicture.Print Tab((16 + (k * 8))); tempY;
            ResultsFrm.ResPicture.Print
        ResultsFrm.ResPicture.Print
        ResultsFrm.ResPicture.Print
        
        if NVariables < 3:
            ResultsFrm.ResPicture.Print "NO PARTIAL CorRELATIONS TO CALCULATE"
        else:
            ResultsFrm.ResPicture.Print "PARTIAL CorRELATIONS WITH ";
            ResultsFrm.ResPicture.Print PTandFile
            ResultsFrm.ResPicture.Print
            ResultsFrm.ResPicture.Print Tab(24); "Partial r"; Tab(36); "P value"
           # ResultsFrm.ResPicture.Print
        
            for i in NVariables[2:]:
                arraycount = 1
                for j in NVariables[2:]:
                    if i != j:
                        CorrArrayList(arraycount) = j
                        arraycount = arraycount + 1
                    
                ResultsFrm.ResPicture.Print FileList.List(i - 2); Tab(24);
                tempResult = PCorr(1, i, NVariables - 2)
                if Abs(tempResult) < 0.999:                   #Trap division by zero error
                    TTestValue = (tempResult * Sqr(TotalNumbers - 2 - MissingRows - BelowThresh)) / Sqr(1 - (tempResult ^ 2))
                    PrValue = (((1 + ((TTestValue ^ 2) / (TotalNumbers - MissingRows - BelowThresh))) ^ -((TotalNumbers + 1 - MissingRows - BelowThresh) / 2))) / (Sqr(((TotalNumbers - MissingRows - BelowThresh) * PI)))
                    PrValue = PrValue * Sqr(TotalNumbers - MissingRows - BelowThresh)      #Correction for large N
                else:
                    TTestValue = 0
                    PrValue = 1
                    tempResult = 0
                
                tempY = format(tempResult, "0.000")
                ResultsFrm.ResPicture.Print tempY; Tab(36);
                tempY = format(PrValue, "0.0000")
                ResultsFrm.ResPicture.Print tempY

        
        ResultsFrm.Show vbModal
    
    ScreenVarsFrm.MousePointer = 0
"""

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

def increaseDate(currentDate): #todo check if the leap year thing was important
    currentDate += datetime.timedelta(days=1)
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

def correlation(predictandSelected, nVariables, fSDate, fEDate, predictorSelected):
    if predictandSelected == "":
        print("You must select a predictand.") # todo proper error message
    elif len(predictorSelected) < 1:
        print("You must select at least one predictor.") # todo proper error message
    elif len(predictorSelected) > 12:
        print("Sorry - you are allowed a maximum of 12 predictors only.") #todo proper error message
    else:
        predictor = np.loadtxt(predictorSelected[0])
        print(predictor[0])
        print(np.argwhere(predictor == 999))
        nVariables = len(predictorSelected) + 1
        dateOfLoop = fSDate

        loadedFiles = []
        loadedFiles = loadFilesIntoMemory(predictorSelected, predictandSelected)
        
        #skip unwanted date
        firstValid = findDataStart(loadedFiles[0])
        #todo progress bar
 
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
    DateWanted = answer


loadedFiles = []
loadedFiles = loadFilesIntoMemory(predictorSelected, predictandSelected)
firstValid = findDataStart(loadedFiles[0])
print(loadedFiles[0][firstValid])
#print(len(loadFilesIntoMemory(predictorSelected, predictandSelected)))
#correlation("hi", 3, 4, datetime.datetime(1948, 1, 1), datetime.datetime.now(), predictorSelected)



def miniReset():
    print("haha die")

def newProgressBar(ProgressPicture, ProgValue, number, text):
    print("haha die")

def setSeason():
    print("haha die")
