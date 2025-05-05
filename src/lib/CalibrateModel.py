import numpy as np
from datetime import date as realdate
from src.lib.utils import loadFilesIntoMemory, increaseDate, thirtyDate, getSettings, fSDateOK, fEDateOK
from copy import deepcopy
import src.core.data_settings
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QTabWidget, QWidget, QMessageBox
from PyQt5.QtGui import QFont
#from scipy.stats import spearmanr

## NOTE TO READERS: THIS FILE **DOES** WORK
## The debugRun test function should give an example configuration

months = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"]
            

##DEBUGGING FUNCTIONS:
debug = False
def debugMsg(msg):
    if debug == True:
        print(msg)

_globalSettings = {}

## Bewrae of Matricies being incorrectly "orientated"

def date(y: int, m: int, d: int):
    """
    Dynamic Local Date Function
    if thirtydate is enabled, uses the thirtydate date object
    otherwise uses the normal date object that normal people use
    """

    thirtydate = _globalSettings['thirtyDay']
    if not thirtydate:
        return realdate(y, m, d)
    else:
        return thirtyDate(y, m, d)
#else:

def reloadGlobals():
    """
    Reloads global variables (read-only parameters from settings) for this module 
    in the unlikely event that they changed between loading this module and running it
    Also maps Model Transformation and Optimisation Algorithm choice to integers
    """

    global _globalSettings
    _globalSettings = getSettings()

    ##Map Model Transformation from String to Int
    mT = _globalSettings['modeltransformation']
    #Model transformation; 1=none, 2=4root, 3=ln, 4=Inv Normal, 5=box cox
    if mT == 'None':
        _globalSettings['modelTrans'] = 1
    elif mT == 'Fourth root':
        _globalSettings['modelTrans'] = 2
    elif mT == 'Natural log':
        _globalSettings['modelTrans'] = 3
    elif mT == 'Inverse Normal':
        _globalSettings['modelTrans'] = 4
    elif mT == 'Box Cox':
        _globalSettings['modelTrans'] = 5
    else:
        debugMsg("[Error]: Invalid Model Trans option. Using 'None' option")
        _globalSettings['modelTrans'] = 1

    ##Map Optimisation Algorithm from String to Int
    oC = _globalSettings['optimizationalgorithm']
    if oC == 'Ordinary Least Squares':
        _globalSettings['optAlg'] = 0
    elif oC == 'Dual Simplex':
        _globalSettings['optAlg'] = 1
    else:
        debugMsg("[Error]: Invalid Optimisation choice. Using 'Ordinary Least Squares' option")
        _globalSettings['optAlg'] = 0

    criteria = _globalSettings['criteriatype']
    if criteria == 'AIC Criteria':
        _globalSettings['aicWanted'] = True
    elif criteria == 'BIC Criteria':
        _globalSettings['aicWanted'] = False
    else:
        debugMsg("[Error]: Invalid Stepwise Criteria choice. Using 'AIC' option")
        _globalSettings['aicWanted'] = True
        
        
def debugRun():
    calibrateModelDefaultExperience()

def calibrateModelDefaultExperience(modelType):
    """
    CALIBRATE MODEL TESTING FUNCTION
    Also gives an idea of what to expect using it
    """
    #global _globalSettings
    reloadGlobals()
    #_globalSettings['globalsdate'] = date(1948, 1, 1) #date(2004, 8, 5)
    #_globalSettings['globaledate'] = date(2017, 12, 31) #date(1961, 1, 10) #date(2017, 12, 31)#date(2025, 1, 7)

    ## Parameters
    #fsDate = deepcopy(globalStartDate)
    fsDate = date(1948, 1, 1)
    #fsDate = date(1961, 1, 1)
    #feDate = deepcopy(globalEndDate)
    #feDate = date(1961, 1, 10)
    #feDate = date(1965, 1, 10)
    feDate = date(1996, 12, 31)
    #feDate = date(1997, 12, 31)
    #feDate = date(2015, 12, 31)
    #modelType = 0 #0
    parmOpt = False  ## Whether Conditional or Unconditional. True = Cond, False = Uncond. 
    ##ParmOpt(1) = Uncond = False
    ##ParmOpt(0) = Cond = True
    autoRegression = False ## Replaces AutoRegressionCheck -> Might be mutually exclusive with parmOpt - will check later...
    includeChow = False
    detrendOption = 0 #0, 1 or 2...
    doCrossValidation = False
    crossValFolds = 2

    ##Edit Settings for Testing
    #_globalSettings['modelTrans'] = 5 #Model transformation; 1=none, 2=4root, 3=ln, 4=Inv Normal, 5=box cox
    _globalSettings['stepwiseregression'] = True

    print(f"Testing with 'modelTrans' == {_globalSettings['modelTrans']}")

    #if PTandRoot == None:
    PTandRoot = "predictand files/NoviSadPrecOBS.dat" ##Predictand file
    #if fileList == []:

    fileList = [
    #    "temp", "mslp", "p500", "p850", "rhum", 
    #    "r500", "r850", "p__f", "p__z", 
    #    "p__v", "p__u", "p_th", "p_zh", "p5_f", 
    #    "p5_z", "p5_v", "p5_u", "p5th", "p5zh", 
    #    "p8_f", "p8_z", "p8_v", "p8_u","p8th", 
    #    "p8zh", "shum", "dswr", 
    #    "lftx", #"pottmp", "pr_wtr",
        "p__f", "p__u", "p__v", "p__z",
        "p_th", "p_zh"
    #"p5th"
    ] #note - ncep_prec.dat is absent - nice round number of 30
    for i in range(len(fileList)):
        fileList[i] = "predictor files/ncep_" + fileList[i] + ".dat"
    PARfilePath = "JOHN_PARFILE.PAR"
    ## Predictor files should be in the format [path/to/predictor/file.dat]
    ## Files usually begin with ncep_

    ## NOTE: FOR OPTIMAL PERFORMANCE, MERGE PTandRoot with fileList:
    fileList.insert(0, PTandRoot)
    
    results = calibrateModel(fileList, PARfilePath, fsDate, feDate, modelType, parmOpt, autoRegression, includeChow, detrendOption, doCrossValidation, crossValFolds)
    
    return results

    ## Output for similar results to the OG software:
    print(f"FINAL RESULTS:")
    debugMsg(f"Debug data:")
    debugMsg(f"Fit Start Date: {fsDate}")
    debugMsg(f"Fit End Date: {feDate}")
    #print(f"Predictand: {PTandRoot}")
    print(f"\nPredictors:\n")
    for i in fileList:
        print(i)

    month_name = {
        "January":"January  ",
        "February":"February ",
        "March":"March    ",
        "April":"April    ",
        "May":"May      ",
        "June":"June     ",
        "July":"July     ",
        "August":"August   ",
        "September":"September",
        "October":"October  ",
        "November":"November ",
        "December":"December ",
        "Mean":"Mean     "
    }

            
    ##Useful info on how to display/format the resutls...
    #from calendar import month_name
    ## Better formatted Month Names so they are all same length
    months2 = deepcopy(months)
    months2.append("Mean")
    u = "Unconditional"
    c = "Conditional"
    x = "xValidation"      
    print(f"\nUnconditional Statistics:")
    print(f"\nMonth\t\tRSquared\tSE\t\tFRatio\t\t{'D-Watson' if not parmOpt else 'Prop Correct'}\t{'Chow' if includeChow else ''}")
    if not parmOpt:
        for i in months2:
            if includeChow:
                print(f"{month_name[i]}\t{results[u][i]['RSquared']:.4f}\t\t{results[u][i]['SE']:.4f}\t\t{results[u][i]['FRatio']:.2f}\t\t{results[u][i]['D-Watson']:.4f}\t\t{results[u][i]['Chow']:.4f}")
            else:
                print(f"{month_name[i]}\t{results[u][i]['RSquared']:.4f}\t\t{results[u][i]['SE']:.4f}\t\t{results[u][i]['FRatio']:.2f}\t\t{results[u][i]['D-Watson']:.4f}")
        if doCrossValidation:
            print(f"\nCross Validation Results:")
            print(f"\nMonth\t\tRSquared\tSE\t\tD-Watson\tSpearman\tBias")
            for i in months2:
                print(f"{month_name[i]}\t{results[u][x][i]['RSquared']:.4f}\t\t{results[u][x][i]['SE']:.4f}\t\t{results[u][x][i]['D-Watson']:.4f}\t\t{results[u][x][i]['SpearmanR']:.4f}\t\t{results[u][x][i]['Bias']:.4f}")

    else:
        for i in months2:
            if includeChow:
                print(f"{month_name[i]}\t{results[u][i]['RSquared']:.4f}\t\t{results[u][i]['SE']:.4f}\t\t{results[u][i]['FRatio']:.4f}\t\t{results[u][i]['PropCorrect']:.4f}\t\t{results[u][i]['Chow']:.4f}")
            else:
                print(f"{month_name[i]}\t{results[u][i]['RSquared']:.4f}\t\t{results[u][i]['SE']:.4f}\t\t{results[u][i]['FRatio']:.4f}\t\t{results[u][i]['PropCorrect']:.4f}")
        if doCrossValidation:
            print(f"\nCross Validation Results:")
            print(f"\nMonth\t\tRSquared\tSE\t\tProp Correct")
            for i in months2:
                print(f"{month_name[i]}\t{results[u][x][i]['RSquared']:.4f}\t\t{results[u][x][i]['SE']:.4f}\t\t{results[u][x][i]['PropCorrect']:.4f}")
        print(f"\nConditional Statistics:")
        print(f"\nMonth\t\tRSquared\tSE\t\tFRatio\t\t{'Chow' if includeChow else ''}")
        for i in months2:
            if includeChow:
                print(f"{month_name[i]}\t{results[c][i]['RSquared']:.4f}\t\t{results[c][i]['SE']:.4f}\t\t{results[c][i]['FRatio']:.4f}\t\t{results[c][i]['Chow']:.4f}")
            else:
                print(f"{month_name[i]}\t{results[c][i]['RSquared']:.4f}\t\t{results[c][i]['SE']:.4f}\t\t{results[c][i]['FRatio']:.4f}")
        if doCrossValidation:
            print(f"\nCross Validation (Conditional Part) Results:")
            print(f"\nMonth\t\tRSquared\tSE\t\tSpearman")
            for i in months2:
                print(f"{month_name[i]}\t{results[c][x][i]['RSquared']:.4f}\t\t{results[c][x][i]['SE']:.4f}\t\t{results[c][x][i]['SpearmanR']:.4f}")
        
        
            
        
        #print(f"\nConditional Statistics:")
        #print(f"\nMonth\t\tRSquared\tSE\t\tFRatio\t\t{'D-Watson' if not parmOpt else 'Prop Correct'}\t{'Chow' if includeChow else 0}")

    #debugMsg(f"TotalNumbers: {totalNumbers}, Missing Days: {noOfDays2Fit - totalNumbers}")

def calibrateModel(fileList, PARfilePath, fsDate, feDate, modelType=2, parmOpt=False, autoRegression=False, includeChow=False, detrendOption=0, doCrossValidation=False, crossValFolds=2):
    """
        Core Calibrate Model Function (v0.7.1)
        fileList -> Array of predictor file paths. First entry should be the predictand file
        PARfilePath -> Save path for the output file (PARfile)
        fsDate -> Fit start date (currently accepts Date object, may adjust to accept string)
        feDate -> Fit end date
        modelType -> Monthly/Seasonal/Annual (0/1/2), can change easily according to the will of the GUI Developer Gods
        parmOpt -> Conditional / Unconditional model, True / False respectively
        autoRegression -> Autoregression tickbox
        includeChow -> Chow Test Tickbox
        detrendOption -> Detrend Options: 0-> None, 1-> Linear, 2-> Power function.
        doCrossValidation -> Cross Validation Tickbox
        crossValFolds -> Number of folds for CrossValidation
        ----------------------------------------
        CalibrateModel also reads the following from the Global Setings:
        > globalStartDate & globalEndDate -> "Standard" start / end date
        > thresh -> Event Threshold
        > globalMissingCode -> "Missing Data Identifier"
        And also reads the following from the Advanced Settings:
        > modelTrans -> Model transformation: 1-> none, 2-> 4th root, 3-> Nat log (ln), 4-> Inverse Normal, 5-> box cox
        > applyStepwise -> Stepwise Tickbox
        > optimisationChoice -> Defined in advanced settings - 0 for "Ordinary" least squares, 1 for Dual Simplex 
    """

    ##Real comments will be added later

    ## In v0.7.1
    ## DetrendOption sorta working...

    ## In v0.8.1
    ## ModelTrans sorta working...

    #------------------------
    # FUNCTION DEFINITITIONS:
    #------------------------



    ## Globals: import from settings
    reloadGlobals()
    globalMissingCode = _globalSettings['globalmissingcode']
    globalStartDate = _globalSettings['globalsdate']
    globalEndDate = _globalSettings['globaledate']
    thresh = _globalSettings['thresh'] #Event thresh should be 0 by default...
    ## Import from "Advanced Settings"
    modelTrans = _globalSettings['modelTrans'] #Model transformation; 1=none, 2=4root, 3=ln, 4=Inv Normal, 5=box cox
    applyStepwise = _globalSettings['stepwiseregression']
    ## Location Unknown:
    countLeapYear = _globalSettings['leapYear']
    ## End of Settings Imports (Default Values for now)

    NPredictors = len(fileList) - 1
    debugMsg(fileList)
    ## Other Vars:
    progValue = 0 ## Progress Bar

    betaTrend = {}

    ##???
    #propResiduals = False
    #if propResiduals:
    #    residualArray = np.ndarray

    ## True Temps:
    #rSquared = 0
    #SE = 0
    #chowStat = 0
    #fRatio = 0
    parameterResultsArray = np.zeros((24,50))
    biasCorrection = np.ones(12)
    #CondPropCorrect = 5

    seasonMonths = [ ##Necesary for Season Month Lookups
        [0, 1, 11], #Winter
        [2, 3, 4], #Spring
        [5, 6, 7], #Summer
        [8, 9, 10]] #Autumn

    ## Note: The following vars were not adjusted to use 0 as their base:
    # ModelTrans
    # SeasonCode
    # NB: ModelType starts from 0
    # NB: Swap WorkingDate.Month to CurrentMonth

    ## Idea: Could define commonly used ranges here so that we don't keep regenerating them each time.

    #------------------------
    #------ SECTION #1 ------ Error Checking & Validation
    #------------------------

    ##not used rn -> will add later
    ##i have notes trust me
    if fileList[0] == "":
        raise ValueError("You must select a predictand")
    elif len(fileList) < 2:
        raise ValueError("You must select at least one predictor")
    elif applyStepwise and NPredictors > 8:
        raise ValueError("You cannot select more than 8 predictors for the stepwise approach")
    elif applyStepwise and doCrossValidation:
        raise ValueError("You cannot perform a cross validation with the stepwise approach")
    elif applyStepwise and modelType != 2:
        raise ValueError("You can only select an annual model for the stepwise approach")
    elif applyStepwise and parmOpt:
        raise ValueError("You can only select an unconditional model for the stepwise approach")
    elif PARfilePath == "":
        raise ValueError("You must enter an appropriate output (PAR) file name")
    elif not fSDateOK(fsDate, feDate, globalStartDate):
        raise ValueError("Invalid start date, see logs for more information")
    elif not fEDateOK(fsDate, feDate, globalEndDate):
        raise ValueError("Invalid end date, see logs for more information")
    else:

    #if True:
        #------------------------
        #------ SECTION #2 ------ Unknown/Initialisation?
        #------------------------
        
        #xValidationResults = np.ndarray((13, 7)).fill(globalMissingCode) ## Original array is XValidationResults(1 To 13, 1 To 7) As Double
        xValidationOutput = {"Unconditional": {}, "Conditional": {}}
        xValidMessageShown = False

        #if ApplyStepwise:
            ## Add msg
    
        lamdaArray = np.zeros((12,2)) ## Lamda array originally "LamdaArray(1 To 12, 1 To 2) As Double"

        processTerminated = False

        statsSummary = np.zeros((26,5)) ## Originally StatsSummary(1 To 26, 1 To 5) As Double

        dependMgs = False

        #-----------------
        ##CLOSE FILES HERE -> idk why, likely contingency / prep
        #-----------------

        ## Reading in data from files?
        ## FileList is the selected files from 
        loadedFiles = loadFilesIntoMemory(fileList) 

        ## Season Code thingy
        ## Move and calculate in the widget later
        if modelType == 0:
            seasonCode = 12
        elif modelType == 1:
            seasonCode = 4
        else:
            seasonCode = 1

        nDaysR = (globalEndDate - globalStartDate).days + 1
        noOfDays2Fit = (feDate - fsDate).days + 1
        
        #------------------------
        #------ SECTION #3 ------ Filtration?
        #------------------------
        
        totalToSkip = (fsDate - globalStartDate)
        #if totalToSkip > 0:
            ## Progress Bar Stuff


        fsDateBaseline = np.zeros((12)) ## Original: FSDateBaseline(1 To 12) As Long
        workingDate = deepcopy(globalStartDate) ## It appears Current Day/Month/Year were split to make incrementing it easier.
        totalNumbers = 0

        searchPos = 0

        while (fsDate - workingDate).days > 0: ##Infinite Loop Bug
            #debugMsg("Loop0")
            if seasonCode == 1:
                fsDateBaseline[0] += 1
            elif seasonCode == 4:
                fsDateBaseline[getSeason(workingDate.month)] += 1
            else: ##Assume seasonCode = 12:
                fsDateBaseline[workingDate.month -1] += 1

            #for i in range(NPredictors + 1):
                ##Load in files?
            searchPos += 1

            totalNumbers += 1
            ##Call IncreaseDate
            workingDate = increaseDate(workingDate, 1, countLeapYear)
            progValue = np.floor((totalNumbers / totalToSkip.days) * 100)
            ##Update progress bar with progValue

        ## END While

        #------------------------
        #----- SECTION #4.0 ----- ???
        #------------------------

        if seasonCode == 1:
            dataReadIn = np.zeros((1, NPredictors + 1, noOfDays2Fit))
        elif seasonCode == 4:
            dataReadIn = np.zeros((4, NPredictors + 1, ((noOfDays2Fit // 4) + 100)))
        else: ## Assume seasonCode = 12
            dataReadIn = np.zeros((12, NPredictors + 1, ((noOfDays2Fit // 12) + 100)))

        sizeOfDataArray = np.zeros((12), dtype=int)

        totalNumbers = 0
        missingRows = 0
        anyMissing = False
    
        ## Progress Bar Update Stuff

        workingDate = deepcopy(fsDate)
        currentMonth = workingDate.month - 1
        currentSeason = getSeason(workingDate.month)


        #------------------------
        #----- SECTION #4.1 ----- (Finding the Start Pos)
        #------------------------

        ## Revisit the following - Something feels off... ##

        noOfSections = np.zeros((12), dtype=int)
        startFound = False
        debugMsg(f"Initial Search Pos: {searchPos}")

        while not startFound:
            #debugMsg("Loop1")
            startFound = True
            for i in range(NPredictors + 1):
                #tempReadin[i] = loadedFiles[i]
                #if tempReadin[i] == globalMissingCode: startFound = False
                if loadedFiles[i][searchPos] == globalMissingCode: 
                    startFound = False
                    #debugMsg(f"Missing Value detected at searchPos: {searchPos} in file {fileList[i]}")
                #else:
            if not startFound:
                workingDate = increaseDate(workingDate, 1, countLeapYear)
            searchPos += 1
            #next i
            totalNumbers += 1
            progValue = np.floor((totalNumbers / nDaysR) * 100)
            #call newProgressBar

        #lastDate = deepcopy(workingDate)
        lastMonth = workingDate.month - 1 #currentMonth
        lastSeason = getSeason(workingDate.month)
        if seasonCode == 1:
            currentPeriod = 0
        elif seasonCode == 4:
            noOfSections[currentSeason] = 1
            #sectionSizes[currentSeason, 1] = 0
            currentPeriod = currentSeason
        else: ##Assume seasonCode = 12
            noOfSections[currentMonth] = 1
            #sectionSizes[currentMonth, 1] = 0
            currentPeriod = currentMonth

        sectionSizes = np.zeros((12, 200), dtype=int) #sectionSizes = np.zeros((12, max(noOfSections)))
        for i in range(NPredictors + 1):
            dataReadIn[currentPeriod, i, sizeOfDataArray[currentPeriod]] = loadedFiles[i][searchPos - 1]#tempReadin(i)
        sizeOfDataArray[currentPeriod] += 1
        
        if seasonCode != 1:
            sectionSizes[currentPeriod, 0] += 1

        #------------------------
        #----- SECTION #4.2 ----- Finding evidence of missing values(?)
        #------------------------

        #call increasedate
        workingDate = increaseDate(workingDate, 1, countLeapYear)
        

        #Do Until (DateDiff("d", DateSerial(CurrentYear, CurrentMonth, CurrentDay), FSDate)) <= 0

        while (feDate - workingDate).days >= 0:
            #debugMsg("Loop2")
            #Do Events, whatever that means
            ##Maybe Exit???

            #debugMsg(f"Day Diff: {(feDate - workingDate).days}, Val: {loadedFiles[0][searchPos]}")

            anyMissing = False
            for i in range(NPredictors + 1):
                #tempReadin[i] = loadedFiles[i] ## input #j, tempReadin(j)
                #if tempReadin[j] == globalMissingCode: anyMissing = True
                if loadedFiles[i][searchPos] == globalMissingCode:
                    anyMissing = True
                #else:
            #next i
            
            totalNumbers += 1
            if seasonCode == 1:
                currentPeriod = 0
            elif seasonCode == 4:
                currentPeriod = currentSeason
            else: ##Assume seasonCode = 12
                currentPeriod = currentMonth
            
            if anyMissing:
                missingRows += 1
                debugMsg(f"Missing Value detected at searchPos: {searchPos}")
            else: 
                for i in range(NPredictors + 1):
                    #debugMsg(f"CurrentPeriod: {currentPeriod}, i: {i}, sizeOf[Period]: {sizeOfDataArray[currentPeriod]}, searchPos: {searchPos}")
                    dataReadIn[currentPeriod, i, sizeOfDataArray[currentPeriod]] = loadedFiles[i][searchPos] #tempReadin(i)
                sizeOfDataArray[currentPeriod] += 1
            ####################################
            ## Revisit - Should be unnecesary ##
            ####################################
            if ((seasonCode == 4) and (currentPeriod != lastSeason)) or ((seasonCode == 12) and (currentPeriod != lastMonth)):
                noOfSections[currentPeriod] += 1
                if anyMissing:
                    sectionSizes[currentPeriod, noOfSections[currentPeriod] - 1] = 0
                else:
                    sectionSizes[currentPeriod, noOfSections[currentPeriod] - 1] = 1
            elif (seasonCode != 1) and not anyMissing:
                sectionSizes[currentPeriod, noOfSections[currentPeriod] - 1] += 1
            #endif
            lastMonth = workingDate.month - 1 #currentMonth
            lastSeason = getSeason(workingDate.month)
            #call increasedate
            workingDate = increaseDate(workingDate, 1, countLeapYear)
            currentMonth = workingDate.month - 1
            currentSeason = getSeason(workingDate.month)
            progValue = np.floor((totalNumbers / nDaysR) * 100)
            searchPos += 1

        ##End while

        #################
        ## Close Files ##
        #################

        #------------------------
        #----- SECTION #5.0 ----- 
        #------------------------

        anyMissing = False
        for i in range(0, seasonCode):
            debugMsg(f"sizeOfDataArray[{i}]: is {sizeOfDataArray[i]} < 10?")
            if sizeOfDataArray[i] < 10:
                anyMissing = True

        if anyMissing:
            #error here
            raise ValueError("Insufficient data available to build a model")
        else:
            xMatrix = None
            yMatrix = None
            yMatrixAboveThreshPos = None
            residualArray = {
                "predicted": np.zeros((totalNumbers)),
                "residual": np.zeros((totalNumbers)),
                "noOfResiduals": 0
            }
            #------------------------
            #---- SECTION #5.1.0 ---- SeasonCode 1 -> Annuals
            #------------------------

            ## uwu
            ## Double check for arrays with too many / little values...

            if seasonCode == 1:
                periodWorkingOn = 0
                if applyStepwise:
                    #call newprogressbar
                    do_nothing()
                elif parmOpt:
                    #call newprogressbar
                    do_nothing()
                elif not parmOpt:
                    #call newprogressbar
                    do_nothing()
                
                if not autoRegression:
                    xMatrix = np.ndarray((sizeOfDataArray[0], NPredictors + 1)) #Needs an extra column of 1s (Represents the Predictand i guess?)
                    yMatrix = np.ndarray((sizeOfDataArray[0]))
                    yMatrixAboveThreshPos = np.ndarray((sizeOfDataArray[0]))
                    for i in range(sizeOfDataArray[0]):
                        yMatrix[i] = dataReadIn[0, 0, i]
                        #debugMsg(f"YMatrix Value #{i} Loaded: {dataReadIn[0, 0, i]}")
                        #xMatrix[i, 0] = 1# --> What does this meen?
                        xMatrix[i, 0] = 1 #loadedFiles[0]
                        for j in range(1, NPredictors + 1): #MODEL? ##+1 bc Range is not INCLUSIVE
                            xMatrix[i, j] = dataReadIn[0, j, i]
                            #debugMsg(f"XMatrix C#{j} Value #{i} Loaded: {dataReadIn[0, j, i]}")
                else: ## Autoregression option
                    xMatrix = np.ndarray((sizeOfDataArray[0] - 1, NPredictors + 2))
                    yMatrix = np.ndarray((sizeOfDataArray[0] - 1))
                    for i in range(sizeOfDataArray[0] - 1):
                        yMatrix[i] = dataReadIn[0, 0, i + 1]
                        xMatrix[i, 0] = 1
                        for j in range(1, NPredictors + 1):
                            xMatrix[i, j] = dataReadIn[0, j, i + 1]
                        ##next
                        if parmOpt:
                            if dataReadIn[0, 0, i] > thresh:
                                xMatrix[i, NPredictors + 1] = 1
                            else:
                                xMatrix[i, NPredictors + 1] = 0
                            ##endif
                        else:
                            xMatrix[i, NPredictors + 1] = dataReadIn[0, 0, i]
                        ##endif
                    ##next
                    NPredictors += 1
                ##endif
                
                #------------------------
                #---- SECTION #5.1.1 ---- 
                #------------------------

                if (detrendOption != 0 and not parmOpt):
                    ##call detrendData(periodWorkingOn, False)
                    dResults = detrendData(yMatrix, yMatrixAboveThreshPos, detrendOption, fsDateBaseline[periodWorkingOn], False)
                    yMatrix = dResults["yMatrix"]
                    betaTrend[periodWorkingOn] = dResults["betaValues"]

                savedYMatrix = deepcopy(yMatrix)

                if parmOpt:
                    ##call PropogateUnConditional
                    propogateUnconditional(yMatrix, thresh)

                if doCrossValidation:
                    ##call xValUnConditional
                    #xValUnConditional()
                    try:
                        xValResults = xValidation(xMatrix, yMatrix, crossValFolds, parmOpt)
                    except Exception as e: 
                        if not xValidMessageShown:
                            xValidMessageShown = True
                            displayError(e)
                    else:
                        for i in range(12):
                            xValidationOutput["Unconditional"][months[i]] = xValResults


                conditionalPart = False ##Needed for CalcParameters

                if applyStepwise:
                    ##call stepwise_regression(parmOpt)
                    stepAdjust = stepWiseRegression(xMatrix, yMatrix, NPredictors) ##very wise
                    newFileList = [fileList[0]] 
                    for i in stepAdjust['newFileList']:
                        newFileList += [fileList[i]]
                    fileList = newFileList
                    NPredictors = stepAdjust['NPredictors']
                    xMatrix = stepAdjust['xMatrix']
                    params = calculateParameters(xMatrix, yMatrix, NPredictors, includeChow, conditionalPart, parmOpt, not parmOpt, residualArray) #betamatrix defined here

                else:
                    ##call CalculateParameters(parmOpt)
                    params = calculateParameters(xMatrix, yMatrix, NPredictors, includeChow, conditionalPart, parmOpt, not parmOpt, residualArray)   #betamatrix defined here
                ##endif

                yMatrix = savedYMatrix

                for i in range(12):  ## 0-11 inclusive
                    for j in range(NPredictors + 1): ## 0-NPred inclusive
                        parameterResultsArray[i, j] = params["betaMatrix"][j]
                    ##next
                    ##Dim ParameterResultsArray(1 To 24, 1 To 50) As Double   'stores beta parmeters etc from calulations as going along - printed to file in the end
                    parameterResultsArray[i, NPredictors + 1] = params["SE"]
                    parameterResultsArray[i, NPredictors + 2] = params["RSQR"]
                    ##Dim StatsSummary(1 To 26, 1 To 5) As Double 'stores summary stats for each month;1=R2, 2=SE; 3=DW; 4=Chow; 5=FRatio (1 to 24 for months -cond and uncond - 25,26 are the means)
                    statsSummary[i, 0] = params["RSQR"]
                    statsSummary[i, 1] = params["SE"]
                    statsSummary[i, 3] = params["chowStat"]
                    statsSummary[i, 4] = params["fRatio"]
                ##next

                #------------------------
                #---- SECTION #5.1.2 ---- Conditional Part
                #------------------------

                if autoRegression:
                    NPredictors -= 1

                if parmOpt:
                    ## From Section #6.1.3 (Originally came before #6.1.2)
                    for i in range(12):
                        statsSummary[i, 2] = params["condPropCorrect"]                    ##next


                    ##call newprogressbar
                    if autoRegression:
                        ##Funky resize stuffs here - come back later...
                        #xMatrixClone = deepcopy(xMatrix)
                        xMatrix = np.delete(xMatrix, NPredictors + 2, 1)
                    ##endif

                    #call PropogateConditional
                    #propogateConditional(xMatrix, yMatrix, yMatrixAboveThreshPos, thresh, NPredictors) 
                    
                    ### propogateConditional Code ###

                    rejectedIndex = []
                    for i in range(len(yMatrix)):
                        if yMatrix[i] <= thresh:
                            ## NEW AND IMPROVED RESIZE CODE HERE:
                            rejectedIndex.append(i)
                        else:
                            yMatrixAboveThreshPos[i] = i+1
                        #End If
                    #Next i
                    xMatrix = np.delete(xMatrix, rejectedIndex, 0)
                    yMatrix = np.delete(yMatrix, rejectedIndex)
                    yMatrixAboveThreshPos = np.delete(yMatrixAboveThreshPos, rejectedIndex)

                    ### End of propogateConditional Code ###
                    
                    if doCrossValidation:
                        #call xvalConditional
                        #xValConditional()
                        try:
                            xValResults = xValidation(xMatrix, yMatrix, crossValFolds, parmOpt, True)
                        except Exception as e:
                            if not xValidMessageShown:
                                xValidMessageShown = True
                                displayError(e)
                        else:
                            for i in range(12):
                                xValidationOutput["Conditional"][months[i]] = xValResults

                    #call TransformData
                    tResults = transformData(xMatrix, yMatrix, [yMatrixAboveThreshPos], modelTrans)
                    ##if errored then exit
                    if modelTrans != 1:
                        xMatrix = tResults['xMatrix']
                        yMatrix = tResults['yMatrix']
                        yMatrixAboveThreshPos = tResults['extraArrays'][0]
                        tResults = tResults['tResults'] 
                        #We don't need tResults to point to the other matricies 
                        # -> they have their own dedicated variables

                    if detrendOption != 0:
                        ##call DetrendData
                        dResults = detrendData(yMatrix, yMatrixAboveThreshPos, detrendOption, periodWorkingOn, True)
                        yMatrix = dResults["yMatrix"]
                        betaTrend[periodWorkingOn] = dResults["betaValues"]



                    if modelTrans == 5:
                        for i in range(12):
                            lamdaArray[i, 0] = tResults['lamda']
                            lamdaArray[i, 1] = tResults['shiftRight']

                    ##Can we move the following above, to make it an elif?
                    conditionalPart = True
                    #call CalculateParameters(true)
                    params = calculateParameters(xMatrix, yMatrix, NPredictors, includeChow, conditionalPart, parmOpt, True, residualArray, tResults) #betaMatrix defined here

                    if processTerminated:
                        ##exit
                        do_nothing()
                    if modelTrans == 4:
                        yDash = np.sum(np.matmul(xMatrix, params['betaMatrix']))
                        biasCorrect = 0 if yDash == 0 else (np.sum(yMatrix) / yDash)
                        for i in range(12):
                            biasCorrection[i] = biasCorrect
                    
                    for i in range(12, 24):
                        for j in range(NPredictors + 1):
                            parameterResultsArray[i, j] = params["betaMatrix"][j]
                        ##next
                        parameterResultsArray[i, NPredictors + 1] = params["SE"]
                        parameterResultsArray[i, NPredictors + 2] = params["RSQR"]
                        statsSummary[i, 0] = params["RSQR"]
                        statsSummary[i, 1] = params["SE"]
                        statsSummary[i, 3] = params["chowStat"]
                        statsSummary[i, 4] = params["fRatio"]
                    ##next
                else:
                    #------------------------
                    #---- SECTION #5.1.3 ---- DW calculations
                    #------------------------

                    ##Need to properly calc residualMatrixRows
                    residualMatrix = params["residualMatrix"]
                    dw = calcDW(residualMatrix)
                    for i in range(12):
                        statsSummary[i, 2] = dw
                       

                ##next

                #Call NewProgressBar(ProgressPicture, 100, 100, "Calibrating Model")

                #------------------------
                #---- SECTION #5.2.0 ---- (season/month)
                #------------------------
            else:
                for periodWorkingOn in range(seasonCode):
                    #progValue = ##progress bar stuff
                    ##call newprogressbar

                    ## Copied from above section (SeasonCode == 1), but sizeOfDataArray swapped for periodWorkingOn
                    if not autoRegression:
                        xMatrix = np.ndarray((sizeOfDataArray[periodWorkingOn], NPredictors + 1))
                        yMatrix = np.ndarray((sizeOfDataArray[periodWorkingOn]))
                        yMatrixAboveThreshPos = np.ndarray((sizeOfDataArray[periodWorkingOn]))
                        for i in range(sizeOfDataArray[periodWorkingOn]):
                            yMatrix[i] = dataReadIn[periodWorkingOn, 0, i]
                            xMatrix[i, 0] = 1
                            for j in range(1, NPredictors + 1):
                                xMatrix[i, j] = dataReadIn[periodWorkingOn, j, i]
                        ###### End of Sorta Copy ######
                    else: ## Autoregression option
                        NPredictors += 1
                        binsTotal = sizeOfDataArray[periodWorkingOn]
                        okSectionCount = 0
                        for i in range(noOfSections[periodWorkingOn]):
                            if sectionSizes[periodWorkingOn, i] > 1:
                                okSectionCount += 1
                            ##endif
                        ##next
                        binsTotal -= okSectionCount
                        ##xMatrix resize 
                        ##yMatrix resize
                        xMatrix = np.zeros((binsTotal, NPredictors + 1))
                        yMatrix = np.zeros((binsTotal))

                        tempCounter = 0
                        progressThroughData = 0
                        for section in range(noOfSections[periodWorkingOn]):
                            if sectionSizes[periodWorkingOn, section] > 1:
                                for i in range(sectionSizes[periodWorkingOn, section] - 1):
                                    yMatrix[tempCounter] = dataReadIn[periodWorkingOn, 0, i + progressThroughData + 1]
                                    xMatrix[tempCounter, 0] = 1
                                    for j in range(1, NPredictors):
                                        xMatrix[tempCounter, j] = dataReadIn[periodWorkingOn, j, i + progressThroughData + 1]
                                    ##next (j)
                                    if parmOpt:
                                        if dataReadIn[periodWorkingOn, 0, i + progressThroughData] > thresh:
                                            xMatrix[tempCounter, NPredictors] = 1
                                        else:
                                            xMatrix[tempCounter, NPredictors] = 0
                                        ##endif
                                    else:
                                        xMatrix[tempCounter, NPredictors] = dataReadIn[periodWorkingOn, 0, i + progressThroughData]
                                    ##endif
                                    tempCounter += 1
                                ##next i
                            ##endif
                            progressThroughData += sectionSizes[periodWorkingOn, section]
                        ##next section
                    ##endif

                    #------------------------
                    #---- SECTION #5.2.1 ---- 
                    #------------------------

                    if (detrendOption != 0 and not parmOpt):
                        ##call detrendData(periodWorkingOn, False)
                        dResults = detrendData(yMatrix, yMatrixAboveThreshPos, detrendOption, periodWorkingOn, False)
                        yMatrix = dResults["yMatrix"]
                        betaTrend[periodWorkingOn] = dResults["betaValues"]

                       
                    savedYMatrix = deepcopy(yMatrix)

                    if parmOpt:
                        ###call PropogateUnconditional
                        propogateUnconditional(yMatrix, thresh)
                    
                    conditionalPart = False
                    
                    if doCrossValidation:
                        ##call xValUnconditional
                        #xValUnConditional()
                        try:
                            xValResults = xValidation(xMatrix, yMatrix, crossValFolds, parmOpt)
                        except Exception as e: 
                            if not xValidMessageShown:
                                xValidMessageShown = True
                                displayError(e)
                        else:
                            if seasonCode == 4:
                                for i in range(3):
                                    xValidationOutput["Unconditional"][months[seasonMonths[periodWorkingOn][i]]] = xValResults
                            else: #Assume monthly
                                xValidationOutput["Unconditional"][months[periodWorkingOn]] = xValResults

                    ###until now, #6.2.1 is near identical to #6.1.1,
                    ###but is notably missing the ApplyStepwise condition for CalcualteParameters

                    ##call CalculateParameters(parmOpt) ##Adjust to make sure its correct...?
                    params = calculateParameters(xMatrix, yMatrix, NPredictors, includeChow, conditionalPart, parmOpt, not parmOpt, residualArray)     #betaMatrix Defined Here

                    if processTerminated:
                        ##call mini_reset
                        do_nothing()

                    yMatrix = savedYMatrix

                    if seasonCode == 4:
                        for i in range(3):
                            for j in range(NPredictors + 1):
                               parameterResultsArray[seasonMonths[periodWorkingOn][i], j] = params["betaMatrix"][j]
                            ##next j
                            parameterResultsArray[seasonMonths[periodWorkingOn][i], NPredictors + 1] = params["SE"]
                            parameterResultsArray[seasonMonths[periodWorkingOn][i], NPredictors + 2] = params["RSQR"]
                            statsSummary[seasonMonths[periodWorkingOn][i], 0] = params["RSQR"]
                            statsSummary[seasonMonths[periodWorkingOn][i], 1] = params["SE"]
                            statsSummary[seasonMonths[periodWorkingOn][i], 3] = params["chowStat"]
                            statsSummary[seasonMonths[periodWorkingOn][i], 4] = params["fRatio"]
                        ##next i
                    else: ##Monthly?
                        for i in range(NPredictors + 1):
                            parameterResultsArray[periodWorkingOn, i] = params["betaMatrix"][i]
                        ##next
                        parameterResultsArray[periodWorkingOn, NPredictors + 1] = params["SE"]
                        parameterResultsArray[periodWorkingOn, NPredictors + 2] = params["RSQR"]
                        statsSummary[periodWorkingOn, 0] = params["RSQR"]
                        statsSummary[periodWorkingOn, 1] = params["SE"]
                        statsSummary[periodWorkingOn, 3] = params["chowStat"]
                        statsSummary[periodWorkingOn, 4] = params["fRatio"]
                    ##endif

                    #------------------------
                    #---- SECTION #5.2.2 ---- (Conditional Part)
                    #------------------------

                    if autoRegression:
                        NPredictors -= 1

                    if parmOpt:
                        ## From Section #5.2.3 (Originally came before #5.2.2)
                        if seasonCode == 12:
                            statsSummary[periodWorkingOn, 2] = params["condPropCorrect"]
                        else:
                            for i in range(3):
                                statsSummary[seasonMonths[periodWorkingOn][i], 2] = params["condPropCorrect"]
                            ##next
                        ##endif

                        if autoRegression:
                            ##Funky resize stuffs here - come back later...
                            xMatrixClone = deepcopy(xMatrix)
                            #xMatrix = np.delete(xMatrix, NPredictors + 2, 1)
                        ##endif

                        #call PropogateConditional
                        #propogateConditional(xMatrix, yMatrix, yMatrixAboveThreshPos, thresh, NPredictors) 

                        ### propogateConditional Code ###

                        print(f"Len yMat: {len(yMatrix)}")
                        print(f"Len yMatAbove: {len(yMatrixAboveThreshPos)}")
                        rejectedIndex = []
                        for i in range(len(yMatrix)):
                            if yMatrix[i] <= thresh:
                                ## NEW AND IMPROVED RESIZE CODE HERE:
                                rejectedIndex.append(i)
                            else:
                                yMatrixAboveThreshPos[i] = i+1
                            #End If
                        #Next i
                        xMatrix = np.delete(xMatrix, rejectedIndex, 0)
                        yMatrix = np.delete(yMatrix, rejectedIndex)
                        yMatrixAboveThreshPos = np.delete(yMatrixAboveThreshPos, rejectedIndex)

                        ### End of propogateConditional Code ###

                        if doCrossValidation:
                            #call xValConditional
                            #xValConditional()
                            try:
                                xValResults = xValidation(xMatrix, yMatrix, crossValFolds, parmOpt, True)
                            except Exception as e: 
                                if not xValidMessageShown:
                                    xValidMessageShown = True
                                    displayError(e)
                            else:
                                if seasonCode == 4:
                                    for i in range(3):
                                        xValidationOutput["Conditional"][months[seasonMonths[periodWorkingOn][i]]] = xValResults
                                else: #Assume monthly
                                    xValidationOutput["Conditional"][months[periodWorkingOn]] = xValResults
                        
                        #call TransformData
                        tResults = transformData(xMatrix, yMatrix, [yMatrixAboveThreshPos], modelTrans)
                        #if errored then exit
                        if modelTrans != 1:
                            xMatrix = tResults['xMatrix']
                            yMatrix = tResults['yMatrix']
                            yMatrixAboveThreshPos = tResults['extraArrays'][0]
                            tResults = tResults['tResults'] 
                            #We don't need tResults to point to the other matricies 
                            # -> they have their own dedicated variables


                        if detrendOption != 0:
                            ##call DetrendData
                            dResults = detrendData(yMatrix, yMatrixAboveThreshPos, detrendOption, periodWorkingOn, True)
                            yMatrix = dResults["yMatrix"]
                            betaTrend[periodWorkingOn] = dResults["betaValues"]


                        if modelTrans == 5:
                            if seasonCode == 4:
                                for i in range(3):
                                    lamdaArray[seasonMonths[periodWorkingOn][i], 0] = tResults['lamda']
                                    lamdaArray[seasonMonths[periodWorkingOn][i], 1] = tResults['shiftRight']
                            else: #assume seasonCode == 12:
                                lamdaArray[periodWorkingOn, 0] = tResults['lamda']
                                lamdaArray[periodWorkingOn, 1] = tResults['shiftRight']
                            ##endif
                        ##endif
                        conditionalPart = True
                        ##call CalculateParameters(true)
                        params = calculateParameters(xMatrix, yMatrix, NPredictors, includeChow, conditionalPart, parmOpt, True, residualArray, tResults) #BetaMatrix defined here
                        if processTerminated:
                            ##exit
                            do_nothing()
                        if modelTrans == 4:
                            yDash = np.sum(np.matmul(xMatrix, params['betaMatrix']))
                            biasCorrect = 0 if yDash == 0 else (np.sum(yMatrix) / yDash)

                            if seasonCode == 4:
                                for i in range(4): ##???
                                    biasCorrection[seasonMonths[periodWorkingOn][i]] = biasCorrect
                                ##next i
                            else:
                                biasCorrection[periodWorkingOn] = biasCorrect
                            ##endif
                        ##endif

                        if seasonCode == 4:
                            for i in range(3): ##???
                                for j in range(NPredictors + 1):
                                    parameterResultsArray[seasonMonths[periodWorkingOn][i] + 12, j] = params["betaMatrix"][j]
                                ##next j
                                parameterResultsArray[seasonMonths[periodWorkingOn][i] + 12, NPredictors + 1] = params["SE"]
                                parameterResultsArray[seasonMonths[periodWorkingOn][i] + 12, NPredictors + 2] = params["RSQR"]
                                statsSummary[seasonMonths[periodWorkingOn][i] + 12, 0] = params["RSQR"]
                                statsSummary[seasonMonths[periodWorkingOn][i] + 12, 1] = params["SE"]
                                statsSummary[seasonMonths[periodWorkingOn][i] + 12, 3] = params["chowStat"]
                                statsSummary[seasonMonths[periodWorkingOn][i] + 12, 4] = params["fRatio"]
                            ##next i
                        else:
                            for j in range(NPredictors + 1):
                                parameterResultsArray[periodWorkingOn + 12, j] = params["betaMatrix"][j]
                            ##next j
                            parameterResultsArray[periodWorkingOn + 12, NPredictors + 1] = params["SE"]
                            parameterResultsArray[periodWorkingOn + 12, NPredictors + 2] = params["RSQR"]
                            statsSummary[periodWorkingOn + 12, 0] = params["RSQR"]
                            statsSummary[periodWorkingOn + 12, 1] = params["SE"]
                            statsSummary[periodWorkingOn + 12, 3] = params["chowStat"]
                            statsSummary[periodWorkingOn + 12, 4] = params["fRatio"]
                        ##endif      
                    else:             
                        #------------------------
                        #---- SECTION #5.2.3 ---- (DW Calculations)
                        #------------------------

                        residualMatrix = params["residualMatrix"]
                        DWNumerator = 0
                        DWDenom = 0
                        positionStart = 0 ##Ooh this is new...
                        for i in range(noOfSections[periodWorkingOn]):
                            sectionSize = sectionSizes[periodWorkingOn, i]
                            if sectionSize > 1:
                                if autoRegression:
                                    sectionSize -= 1

                                for j in range(1, sectionSize):
                                    ##curious
                                    DWNumerator += (residualMatrix[j + positionStart] - residualMatrix[j + positionStart - 1]) ** 2
                                #next j
                                positionStart += sectionSize
                            #endif
                        #next i

                        positionStart = 0
                        for i in range(noOfSections[periodWorkingOn]):
                            sectionSize = sectionSizes[periodWorkingOn, i]
                            if sectionSize > 1:
                                if autoRegression:
                                    sectionSize -= 1

                                for j in range(1, sectionSize):
                                    ##curious+
                                    #debugMsg(f"sectionSize: {sectionSize}, residualMatrix size: {len(residualMatrix)}, j ({j}) + positionStart ({positionStart}) = {j + positionStart} < {sectionSize}")
                                    DWDenom += residualMatrix[j + positionStart] ** 2
                                #next j
                                positionStart += sectionSize
                            #endif
                        #next i
                        if DWDenom > 0:
                            if seasonCode == 12:
                                statsSummary[periodWorkingOn, 2] = DWNumerator / DWDenom
                            else:
                                for i in range(3):
                                    statsSummary[seasonMonths[periodWorkingOn][i], 2] = DWNumerator / DWDenom
                            ##endif
                        ##endif
                    ##endif
                ##next periodWorkingOn
            ##endif
                
            #------------------------
            #----- SECTION #6.0 ----- PARfile Output
            #------------------------

            ##Vars "Written" to PAR file:
            print("GlobalSettings:")
            for i in _globalSettings:
                print(f"{i}: {_globalSettings[i]}")
            PARfileOutput = [
                f"{NPredictors if detrendOption == 0 else -NPredictors}", #NPredictors
                f"{seasonCode}", #Season Code
                "360" if _globalSettings['thirtyDay'] else ("366" if countLeapYear else "365"), #"YearIndicator": 
                f"{globalStartDate}", #"Record Start Date": 
                f"{nDaysR}", #"Record Length": 
                f"{fsDate}", #"Fit start date": 
                f"{noOfDays2Fit}", #"No of days in fit": 
                #f"{int(parmOpt)}", #"Set Rainfall Parameter": ?
                f"{parmOpt}",
                f"{modelTrans}", #"Model Transformation option": 
                "1", #"Ensemble size set to 1":#Idk what to do with this
                #f"{int(autoRegression)}", #"Autoregression": 
                f"{autoRegression}",
            ]
            for file in fileList:    
                PARfileOutput.append(file) #Save predictand & predictor file names
            PARfileOutput = "\n".join(PARfileOutput) + "\n"

            #call PrintResults
            PARfileOutput += printResults(parameterResultsArray, NPredictors, parmOpt, biasCorrection, autoRegression, modelTrans, lamdaArray)
 
            #print PTandRoot
            if detrendOption != 0:   ##Will need to double check and standardise this parameter
                #call PrintTrendParms]
                PARfileOutput += printTrendParms(detrendOption, betaTrend, seasonCode)
            #call newProgressBar

            #Write to file
            with open(PARfilePath, "w") as f:
                print(PARfileOutput, file=f)
                f.close()

            #------------------------
            #----- SECTION #6.1 ----- Results Screen output
            #------------------------
            
            #from calendar import month_name as months

            output = {"Predictand": fileList[0]}

            output['Predictors'] = fileList[1:]
            for subloop in range(1, NPredictors + 1):
                output[f"Predictor#{subloop}"] = fileList[subloop]

            u = "Unconditional"
            c = "Conditional"

            output[u] = {}
            for i in range(12):
                output[u][months[i]] = {} # Initialize month associative array / dict
                output[u][months[i]]["RSquared"] = statsSummary[i,0]
                output[u][months[i]]["SE"] = statsSummary[i,1]
                output[u][months[i]]["FRatio"] = statsSummary[i,4]
            if includeChow:
                for i in range(12):
                    output[u][months[i]]["Chow"] = statsSummary[i, 3]
            if not parmOpt:
                for i in range(12):
                    output[u][months[i]]["D-Watson"] = statsSummary[i,2]
            else:
                for i in range(12):
                    output[u][months[i]]["PropCorrect"] = statsSummary[i,2]
                for i in range(12):
                    output[c] = {}
                for i in range(12):
                    output[c][months[i]] = {} # Initialize month associative array / dict
                    output[c][months[i]]["RSquared"] = statsSummary[i + 12,0]
                    output[c][months[i]]["SE"] = statsSummary[i + 12,1]
                    output[c][months[i]]["FRatio"] = statsSummary[i + 12,4]
                if includeChow:
                    for i in range(12):
                        output[c][months[i]]["Chow"] = statsSummary[i + 12, 3]
            if doCrossValidation:
                output[u]["xValidation"] = xValidationOutput[u]
                if parmOpt:
                    output[c]["xValidation"] = xValidationOutput[c]
            ##Done with "prelim data"

            ##Mean Summaries:
            iterator = []
            if modelType == 0: #Monthly - All Values
                iterator = range(12)
            elif modelType == 1: #Seasonally = Only sum 4 values
                iterator = [0,3,6,9]
            else: #Annually - Skip summing (or be lazy and iterate once)
                iterator = [0]

            ##Loop saves cloning the summary code
            for n in ({u, c} if parmOpt else {u}):
                output[n]['Mean'] = {}
                for key in output[n][months[0]]:
                    output[n]['Mean'][key] = 0
                    for i in iterator:
                        output[n]['Mean'][key] += output[n][months[i]][key]
                    output[n]['Mean'][key] /= len(iterator)
                if doCrossValidation:
                    output[n]['xValidation']['Mean'] = {}
                    for key in output[n]['xValidation'][months[0]]:
                        output[n]['xValidation']['Mean'][key] = 0
                        for i in iterator:
                            output[n]['xValidation']['Mean'][key] += output[n]['xValidation'][months[i]][key]
                        output[n]['xValidation']['Mean'][key] /= len(iterator)

            #------------------------
            #----- SECTION #6.2 ----- last minute information appends / info not directly displayed
            #------------------------
            
            analysisPeriod = ['Monthly', 'Seasonal', 'Annual']
            output['analysisPeriod'] = {
                'startDate': fsDate,
                'endDate': feDate,
                'periodName': analysisPeriod[modelType],
                'periodIndex': modelType
            }
            output['autoregression'] = autoRegression
            output['ifXVal'] = doCrossValidation

            #Plot Residual Graph?
            #if residualAnalysis == 1:
                #Show Scatter:
            #plotScatter(residualArray)
            output['residualArray'] = residualArray

            return output

def do_nothing():
    """
    Function that does nothing (it returns True)
    Used only to prevent Python warnings due to indentation errors
    when code blocks are empty
    """
    return True

##Core functions called directly from calibrateModel()

def detrendData(yMatrix: np.array, yMatrixAboveThreshPos: np.array, detrendOption: int, fsDateBaseline: int, conditional: bool):
    """"
    Detrend Data Function v1.1
    -- May or may not work - Find out soon!
    DetrendOption: 0 = none, 1 = Linear, 2 = power function
    Requires yMatrixAboveThreshPos to be set (generally configured in TransformData)
    """

    #Dim BetaTrend(1 To 12, 1 To 3) As Double    
    # 'holds parameters of de trend funtion if detrend option is selected;
    # '1 to 12 for each month or season; for linear model (y=mx+b) 1=intercept b, 2= gradient m
    # 'for power function (y=ax^b;log y = log a + b log x ) 1=a, 2=b , 3=minimum applied before logs could be applied


    print(f"Len yMat: {len(yMatrix)}")
    print(f"Len YABOVE: {len(yMatrixAboveThreshPos)}")

    debugMsg(yMatrix)
    xValues = np.ndarray((len(yMatrix), 2))
    #betaValues = np.array((2))
    tempMatrix1 = np.ndarray
    tempMatrix2 = np.ndarray
    tempYMatrix = deepcopy(yMatrix)
    for i in range(len(yMatrix)):
        xValues[i, 0] = 1
        if conditional:
            xValues[i, 1] = yMatrixAboveThreshPos[i]
        else:
            xValues[i, 1] = i
        ##endif
        if detrendOption == 2:
            xValues[i, 1] += fsDateBaseline
        ##endif
    ##next i

    if detrendOption == 1: #linear regression
        xTransY = np.matmul(xValues.transpose(), yMatrix)
        xTransXInv = np.linalg.inv(np.matmul(xValues.transpose(), xValues))
        betaValues = np.matmul(xTransXInv, xTransY)

        for i in range(len(yMatrix)):
            yMatrix[i] -= (xValues[i,1] * betaValues[1]) #,0])
        ##next i

        return {"betaValues": [betaValues[0], betaValues[1]],
                "yMatrix": yMatrix}

    elif detrendOption == 2: #Power function
        xLogged = deepcopy(xValues)

        minY = np.min(yMatrix)
        if minY > 0: minY = 0
        for i in range(len(yMatrix)):
            tempYMatrix[i] = yMatrix[i] + np.abs(minY) + 0.001

        for i in range(len(yMatrix)):
            tempYMatrix[i] = np.log(tempYMatrix[i])
            xLogged[i, 1] = np.log(xValues[i, 1])

        xTransY = np.matmul(xLogged.transpose(), tempYMatrix)
        xTransXInv = np.linalg.inv(np.matmul(xLogged.transpose(), xLogged))
        betaValues = np.matmul(xTransXInv, xTransY)
        betaValues[0] = np.exp(betaValues[0]) 

        for i in range(len(yMatrix)):
            yMatrix[i] -= (betaValues[0] * (xValues[i][1] ** betaValues[1])) - np.abs(minY) - 0.001

        return {"betaValues": [betaValues[0], betaValues[1], minY],
                "yMatrix": yMatrix}
        
    else:
        raise ValueError("Invalid Detrend Option")

def propogateUnconditional(yMatrix: np.array, thresh):
    """Propogate: Unconditional Function v1.0
    -- yMatrix is an array / Matrix of size (x, 1)
    -- Thresh is the Threshold Value (originally defined as Single)
    """
    for i in range(len(yMatrix)):
        if yMatrix[i] > thresh:
            yMatrix[i] = 1
        else:
            yMatrix[i] = 0

def propogateConditional(xMatrix: np.ndarray, yMatrix: np.ndarray, yMatrixAboveThreshPos: np.ndarray, thresh, NPredictors: int):
    """ 
    Propogate: Conditional Function v1.1
    Reduces X and Y matrices into above threshold values only - adjusts size of X and Y too
    """

    ### GLOBALS ###
    #thresh = 0
    #NPredictors = 21
    #yMatrixAboveThreshPos = np.array()
    #xMatrix = np.array()
    ### ####### ###

    #tempCounter = 0
    rejectedIndex = []
    for i in range(len(yMatrix)):
        if yMatrix[i] > thresh:
            ## NEW AND IMPROVED RESIZE CODE HERE:
            rejectedIndex.append(i)
        #End If
    #Next i

    xMatrix = np.delete(xMatrix, rejectedIndex, 0)
    yMatrix = np.delete(yMatrix, rejectedIndex)

    return 

##XValidation + Helper functions
def xValidation(xMatrix: np.ndarray, yMatrix: np.ndarray, noOfFolds, parmOpt, conditionalPart=False):
    """
    Cross Validation - Combined Function
    """

    ### GOLBALS ###
    thresh = _globalSettings['thresh']
    globalMissingCode = _globalSettings['globalmissingcode']
    modelTrans = _globalSettings['modelTrans']
    ### ####### ###  

    #Generic xVal Error Msg bc I'm lazy
    gErrMsg = "Not all cross validation metrics can be calculated"

    #------------------------
    #------ SECTION #1 ------ Modelled Matrix generation
    #------------------------

    blockSize = len(yMatrix) // noOfFolds           #'calculate the size of a block (this is rounded down so 428/5 = 85 block size. 85x5=425 so 3 values lost at end)
    maxEnd = noOfFolds * blockSize          #'index of max value - make sure we don't go over this (eg 424 for example above: lose values 425,426,427)
    modMatrix = np.zeros((maxEnd))
    #Set ModelledMatrix = New Matrix
    #modelledMatrix.Size (maxEnd + 1), 1         #'stores untransformed modelled values to compare with YMatrix observed values
    
    if blockSize < 10:
        #Error: not enough data
        raise ValueError("Insufficient data for all cross validation metrics to be calculated")
    #End If

    for foldOn in range(noOfFolds):      #'loop through creating appropriate blocks for each block based on other excluded blocks to determine parameters using OLS
        blockStart = (foldOn) * blockSize            #'work out INDEX of block start and end (index starts at zero)
        blockEnd = blockStart + blockSize           #'INDEX of block end eg 0-84,85-169,170-254 etc
        tempXMatrix = np.zeros((maxEnd - blockSize, xMatrix.shape[1]))
        tempYMatrix = np.zeros((maxEnd - blockSize))
        rowCount = 0
        for j in range(maxEnd):                       #'now set up temporary x and y arrays with all data except excluded fold
            if (j < blockStart) or (j >= blockEnd):
                for k in range(xMatrix.shape[1]):
                    tempXMatrix[rowCount, k] = xMatrix[j, k]
                #Next k
                tempYMatrix[rowCount] = yMatrix[j]
                rowCount = rowCount + 1
            #End If
        #Next j
        #tempXMatrix = np.array([xMatrix[i] for i in range(maxEnd) if i not in range(blockStart, blockEnd)]) #xMatrix[:blockStart] + xMatrix[blockEnd:]
        #tempYMatrix = np.array([yMatrix[i] for i in range(maxEnd) if i not in range(blockStart, blockEnd)]) #yMatrix[:blockStart] + yMatrix[blockEnd:]
        #'tempXMatrix and tempYMatrix now have all data except excluded fold.
        
        
        if conditionalPart: ##IF we be doin conditional crossvalidation, we need to transform the data first
            ##fn TransformDataForXValidation()
            tResults = transformData(tempXMatrix, tempYMatrix, [], modelTrans)
            tempXMatrix = tResults['xMatrix']
            tempYMatrix = tResults['yMatrix']
            tResults = tResults['tResults']
            
            if len(tempYMatrix) < 10:           #make sure we still have enough data after transformation
                raise RuntimeError(gErrMsg)
                
        #End If

        ##Generate Beta Matrix

        xTransY = np.matmul(tempXMatrix.transpose(), tempYMatrix)
        xTransXInv = np.linalg.inv(np.matmul(tempXMatrix.transpose(), tempXMatrix))
        xBetaMatrix = np.matmul(xTransXInv, xTransY)
        
        #                 'now cycle through calculating modelled y (transformed value) for excluded block

        for j in range(blockStart, blockEnd): #PC: Do we need +1 here?
            for k in range(xMatrix.shape[1]):               #'calculate values
                modMatrix[j] += (xBetaMatrix[k] * xMatrix[j][k])
            #Next k
        #Next j7

        if conditionalPart and parmOpt:
            untransformData([modMatrix[blockStart:blockEnd]], tResults)
            #pass
    #next foldon


    #------------------------
    #------ SECTION #2 ------ Preprocessing
    #------------------------
    
    #Clip the ends off yMatrix if its larger than modMatrix
    #Useful for Spearman Rank calculations
    if len(yMatrix) > len(modMatrix):
        #Don't want to keep this... I dont think?
        removeIndex = [i + len(modMatrix) for i in range(len(yMatrix) - len(modMatrix))] 
        #for i in range(len(yMatrix) - len(modMatrix)):
        #    removeIndex.append(len(modMatrix) + i)
        yMatrix = np.delete(yMatrix, removeIndex)

    
    #if not parmOpt: ##If Unconditional, do spearman before filtering out erroneous values?
    #    debugMsg("not parmOpt")
    #    debugMsg(f"modMatrix size: {modMatrix.size}, yMatrix size: {yMatrix.size}")
    #    output["SpearmanR"] = spearmanr(modMatrix, yMatrix)
    
    ## "Cleanse" yMat and modMat arrays (filter out missing values, and values below the threshold for the conditional part)
    removeIndex = []
    if parmOpt and conditionalPart:
        removeIndex = [i for i in range(len(modMatrix)) if (yMatrix[i] <= thresh or modMatrix[i] <= thresh or yMatrix[i] == globalMissingCode or modMatrix[i] == globalMissingCode)]
    else:
        removeIndex = [i for i in range(len(modMatrix)) if (yMatrix[i] == globalMissingCode or modMatrix[i] == globalMissingCode)]
    #xMatrix = np.delete(xMatrix, rejectedIndex, 0)
    yMatrix = np.delete(yMatrix, removeIndex)
    modMatrix = np.delete(modMatrix, removeIndex)
    values = len(modMatrix) #number of valid values (shortcut bc lazy)
    
    #------------------------
    #------ SECTION #3 ------ Calculate Statistics
    #------------------------

    output = {"RSquared":None, "SE":None}
    
    if conditionalPart or not parmOpt: ## If Unconditional, or Conditional part of the Conditional process, calc Spearman Rank
        #if parmOpt and conditionalPart: ##If Conditional Part of conditional process, do spearman after filtering out values
        output["SpearmanR"] = spearmanr(modMatrix, yMatrix)

    ## Calculate Statistics
    if (conditionalPart and values > 10) or (not conditionalPart and values >= 2): #Conditional needs at least 10 values, unconditional apparently only needs 2

        ##SERROR
        SError = 0
        for i in range(values):
            SError += (modMatrix[i] - yMatrix[i]) ** 2 ##Order matters not because square
        SError = SError / (values - 1)
        SError = np.sqrt(SError)
        output["SE"] = SError
        
        ##RSQR
        limit = len(modMatrix) #maxEnd + 1 (-1)...?
        checkMissing = False #because pre-filtered
        missingLim = limit #because missing < maxEnd + 1
        rsqr = calcRSQR(modMatrix, yMatrix, limit, checkMissing, missingLim)
        output["RSquared"] = rsqr

        
        if not parmOpt: #If Unconditional
            ##Durbin Watson Calculations
            ##First generate the residual array
            residualMatrix = np.zeros((maxEnd))
            for i in range(maxEnd):
                residualMatrix[i] = yMatrix[i] - modMatrix[i]
            ##Calc Durbin Watson:
            xvDW = calcDW(residualMatrix)
            output["D-Watson"] = xvDW

            #Calculate Bias:
            meanModelled = np.sum(modMatrix)
            meanObserved = np.sum(yMatrix)
            if meanObserved != 0:
                bias = (meanModelled - meanObserved) / meanObserved
            else:
                bias = globalMissingCode
            output["Bias"] = bias

        elif parmOpt and not conditionalPart: #If Unconditional part of Conditional process
            #Calculate Occurance Stats
            correctCount = 0
            for i in range(maxEnd):
                if yMatrix[i] == 0 and modMatrix[i] < 0.5:
                    correctCount += 1
                elif yMatrix[i] == 1 and modMatrix[i] >= 0.5:
                    correctCount += 1
            propCorrect = correctCount / len(yMatrix)
            output["PropCorrect"] = propCorrect
            #Consider switching to the calcPropCorrect function later...
        #else #Conditional Part does not have any extra features

    elif not conditionalPart: ##Unconditional part is happy to provide missing values
        output["RSquared"] = globalMissingCode
        output["SE"] = globalMissingCode
        if parmOpt:
            output["PropCorrect"] = globalMissingCode
        else:
            output["D-Watson"] = globalMissingCode
            output["Bias"] = globalMissingCode
    else: #Lo Data, Crash now...
        if conditionalPart:
            #else: Sorry - an error has occurred in the cross validation.  Not all cross validation metrics can be calculated as insufficient data can be inverse transformed.", 0 + vbCritical, "Error Message"
            #print("Error: Not enough data for the conditional part of xValidation")
            raise ArithmeticError("Not all cross validation metrics can be calculated as insufficient data can be inverse transformed")
        else:
            #if uncond: Sorry - an error has occurred in the cross validation.  Not all cross validation metrics can be calculated
            raise RuntimeError(gErrMsg)

    return output

def spearmanr(modMatrix, yMatrix):
    """
    Calculates Spearman Rank R Value
    - Uses Same technique as original SDSM code
    - Assumes Clean Data (no missing values)
    """

    ##Init
    spearMod = np.zeros((3, len(modMatrix)))
    spearMod[0] = modMatrix
    spearMod[1] = np.array(range(len(modMatrix)))
    spearObs = np.zeros((3, len(yMatrix)))
    spearObs[0] = yMatrix
    spearObs[1] = np.array(range(len(yMatrix)))

    ##Sort Rows
    argSortMod = np.argsort(modMatrix)
    spearMod[0] = spearMod[0][argSortMod]
    spearMod[1] = spearMod[1][argSortMod]
    argSortObs = np.argsort(yMatrix)
    spearObs[0] = spearObs[0][argSortObs]
    spearObs[1] = spearObs[1][argSortObs]

    spearMod[2] = np.array(range(len(modMatrix)))
    spearObs[2] = np.array(range(len(yMatrix)))

    for i in range(1, len(modMatrix)):
        if spearMod[0][i] == spearMod[0][i-1]:
            spearMod[2][i] = spearMod[2][i-1]
        if spearObs[0][i] == spearObs[0][i-1]:
            spearObs[2][i] = spearObs[2][i-1]

    ##Sort back to normal
    ##sorting sounds##
    argSortMod = np.argsort(spearMod[1])
    argSortObs = np.argsort(spearObs[1])
    spearMod[2] = spearMod[2][argSortMod]
    spearObs[2] = spearObs[2][argSortObs]

    d = 0
    for i in range(len(modMatrix)):
        d += (spearMod[2][i] - spearObs[2][i]) ** 2
    denom = ((len(modMatrix) ** 2)- 1) * len(modMatrix)
    d = 1 - ((6 * d) / denom)
    
    return d

def calcDW(residualMatrix: np.ndarray):
    """
    Durbin Watson Shared Code for XValidation and CalibrateModel (Unconditional)
    - ASSUMES CLEAN DATA
    """

    numerator = 0
    denom = 0
    for i in range(len(residualMatrix) - 1):
        numerator += (residualMatrix[i + 1] - residualMatrix[i]) ** 2
    #Next i
    for i in range(len(residualMatrix)):
        denom += residualMatrix[i] ** 2
    #Next i
    if denom > 0:
        return (numerator / denom)
    #Next i
    else:
        return globalMissingCode
    #Next i   

##Stepwise Regression + Helper Functions
def stepWiseRegression(xMatrix: np.ndarray, yMatrix: np.ndarray, NPredictors: int):
    """
    Stepwise Regression function
    """
    globalMissingCode = _globalSettings['globalmissingcode']
    aicWanted = _globalSettings['aicWanted']
    jMatrix = np.ones((len(yMatrix), len(yMatrix)))

    results = determinePermutations(NPredictors)
    permArray = results
    totalPerms = len(results) 
    permErrors = np.zeros((totalPerms))
    
    for i in range(totalPerms):
        ##Update ProgressBar

        noOfCols = len(permArray[i]) + 1
        

        newXMatrix = np.ones((len(yMatrix), noOfCols))

        for j in range(1, noOfCols):
            for k in range(len(yMatrix)):
                newXMatrix[k][j] = xMatrix[k][int(permArray[i][j - 1])]
            #next k
        #next j

        try:
            results = calculateParameters2(newXMatrix, yMatrix, NPredictors)
        except: #'if we couldn't calc parms then ignore this permutation
            return globalMissingCode
        else:
            #if not terminated
            SSR = np.matmul(results["betaMatrix"].transpose(), np.matmul(newXMatrix.transpose(), yMatrix))
            SSRMinus = np.matmul(yMatrix.transpose(), np.matmul(jMatrix, yMatrix))
            RMSE = np.sqrt(SSR / len(yMatrix))
            if aicWanted:
                permErrors[i] = (newXMatrix.shape[0] * np.log(RMSE)) + ((newXMatrix.shape[1] - 1) * 2)
            else:
                permErrors[i] = (newXMatrix.shape[0] * np.log(RMSE)) + ((newXMatrix.shape[1] - 1) * np.log(newXMatrix.shape[0]))
            #endif
        #end try

        ##Stop using newXMatrix now
    #next i

    maxError = -99999
    maxLocation = 1
    for i in range(totalPerms):
        if permErrors[i] > maxError:
            maxError = permErrors[i]
            maxLocation = i
        #endif
    #next i

    if maxError == -99999:
        RuntimeError("Unable to determine an optimum set of predictors from those selected. Please try an alternative")

    noOfCols = len(permArray[maxLocation]) + 1
    
    NPredictors = noOfCols - 1
    newXMatrix = np.ones((len(yMatrix), noOfCols))

    for j in range(1, noOfCols):
        for k in range(len(yMatrix)):
            newXMatrix[k][j] = xMatrix[k][int(permArray[maxLocation][j - 1])]
        #next k
    #next j

    newFileList = []
    for j in range(noOfCols - 1):
        newFileList.append(int(permArray[maxLocation][j]))
        print(f"ADDED FILE {permArray[maxLocation][j]}")


    return {"newFileList": newFileList,
            "noOfCols": noOfCols,
            "NPredictors":NPredictors,
            "xMatrix":newXMatrix
    }
        
def determinePermutations(n: int):
    from itertools import combinations
    THE_LIST = []
    #THE_LIST_JR = np.array(range(n))
    for i in range(n):
        THE_LIST += list(combinations(range(1, n+1), i+1))

    return THE_LIST

def calculateParameters(xMatrix: np.ndarray, yMatrix: np.ndarray, NPredictors: int, includeChow: bool, conditionalPart: bool, parmOpt: bool, propResiduals: bool, residualArray: np.ndarray, lamdaValues = []):
    """
    Calculate Parameters function v1.1
    -- Presumably calculates parameters
    -- LamdaValues and yMatrixAboveThreshPos are only necessary when modelTrans == 4 and ConditionalPart == True
    """
    ### GLOBALS ###
    globalMissingCode = _globalSettings['globalmissingcode']
    ### ####### ###

    #local vars
    chowStat = 0
    condPropCorrect = None

    #requireUntransform = True #ConditionalPart And ParmOpt(0).value

    if includeChow:
        #CalcParams does not modify xMatrix or yMatrix
        xtemp = xMatrix #deepcopy(xMatrix)
        ytemp = yMatrix #deepcopy(yMatrix)
        firstHalf = int(np.round(xMatrix.shape[0] / 2)) ##Should use the same rounding algorithm as original software
        #secondHalf = xMatrix.shape[0] - firstHalf ##Might be unnecesary
        isValid = (xMatrix.shape[0] // 2) > 10

        if (isValid): #Do we have enough data? Are both halves >10?
            ##Cool python hackz
            results = calculateParameters2(xtemp[:firstHalf], ytemp[:firstHalf], NPredictors) #ignore error
            RSS1 = results["RSS"]

            results = calculateParameters2(xtemp[firstHalf:], ytemp[firstHalf:],  NPredictors) #ignore error
            RSS2 = results["RSS"]
        #endif
    #endif

    results = calculateParameters2(xMatrix, yMatrix, NPredictors)
    RSSAll = results["RSS"]
    betaMatrix = results["betaMatrix"]

    if includeChow and isValid:
        chowDenom = RSS1 + RSS2
        if chowDenom > 0:
            chowStat = ((RSSAll - RSS1 - RSS2) / chowDenom)
            chowStat *= (xMatrix.shape[0] - (2* (xMatrix.shape[1] - 1))) / (xMatrix.shape[1] - 1)
            #
        #
    #endif

    yMatrix2Test = deepcopy(yMatrix)
    modMatrix2Test = np.zeros((len(yMatrix)))

    for i in range(len(yMatrix)):
        #modMatrix2Test[i] = 0
        for j in range(xMatrix.shape[1]):
            modMatrix2Test[i] += betaMatrix[j] * xMatrix[i, j]
        #next j
    #next i

    if parmOpt:
        if conditionalPart:
            #print("Conditional CalcParams:")
            untransformData([modMatrix2Test, yMatrix2Test], lamdaValues)
            ##call untransformdata
            ##Useful when processing Transformed Data
            ##only useful for the conditional part
            pass
        else: #i.e. Not conditionalPart
            condPropCorrect = calcPropCorrect(modMatrix2Test, yMatrix2Test, len(yMatrix2Test))
    #endif

    #Quick SError?
    if len(yMatrix) < 2:
        SE = globalMissingCode
    else:
        SE = np.sqrt(RSSAll / (len(yMatrix) - 1)) ##SQRT?
        SE = max(SE, 0.0001)
    #endif

    rsqr = calcRSQR(modMatrix2Test, yMatrix2Test, len(yMatrix2Test), True, (len(yMatrix2Test) - 2))
    ## Aka RSquared

    if propResiduals:
        nOfR = residualArray["noOfResiduals"]
        for i in range(len(results["residualMatrix"])):
            residualArray["predicted"][i + nOfR] = results["predictedMatrix"][i]
            residualArray["residual"][i + nOfR] = results["residualMatrix"][i]
        residualArray["noOfResiduals"] += len(results["residualMatrix"])
    #endif


    ##might be worth just joining the new stuff to the results array and returning that...
    return {"fRatio": results["fRatio"], 
            "betaMatrix":results["betaMatrix"], 
            "residualMatrix":results["residualMatrix"],
            "SE":SE, 
            "RSQR":rsqr, 
            "condPropCorrect":condPropCorrect, 
            "chowStat":chowStat
            }

def calculateParameters2(xMatrix: np.ndarray, yMatrix: np.ndarray, NPredictors: int):
    """
    Calculate Parameters #2 v1.1
    Component function for Calculate Parameters #1 and Stepwise Regression
    - Calculates MLR parameters for XMatrix and YMatrix
    - Calculates the global variables SE and rsquared for these particular arrays too and FRatio
    - Establishes BetaMatrix and ResidualMatrix
    """

    ##NB-Original Code had a parameter "PropResiduals" and "IgnoreError"
    #-> PropResiduals never read

    ### GLOBALS ###
    globalMissingCode = _globalSettings['globalmissingcode']
    dependMsg = True #No idea where this is supposed to be defined...
    optimisationChoice = _globalSettings['optAlg']
    ### ####### ###

    yBar = np.sum(yMatrix) / len(yMatrix)

    if optimisationChoice == 0:
        xTransY = np.matmul(xMatrix.transpose(), yMatrix)
        xTransXInverse = np.linalg.inv(np.matmul(xMatrix.transpose(), xMatrix))
        betaMatrix = np.matmul(xTransXInverse, xTransY)

    else:
        #Dual Simplex Approach
        ## INITIALISATION
        IMAX = xMatrix.shape[0] #+1
        JMAX = NPredictors #+1
        KPN = IMAX + JMAX
        KP1 = JMAX
        A = np.zeros((IMAX + 1, JMAX + 1))
        B = np.zeros((20))
        C = np.zeros((KPN))
        xBar = np.zeros((20))
        ISS = np.zeros((IMAX + 1), int)
        NB = np.array(range(JMAX + 1))
        TOL = 0.00000001

        for i in range(KP1, KPN):
            C[i] = 2
        xSum = np.sum(xMatrix, 0)
        for j in range(NPredictors):
            #I THINK
            xBar[j] = xSum[j] / len(xSum) ##My math senses tell me something's wrong here...
            for i in range(xMatrix.shape[0]):
                A[i + 1, j] = xMatrix[i, j] - xBar[j]
        
        for i in range(len(xSum)):
            ISS[i+ 1] = i + NPredictors
            A[i + 1, JMAX] = yMatrix[i] - yBar

        ##END OF INIT

        done = True
        while done != True: ##Condition irrelevant - loop exits via 'break' statement
            while True:
                H = -TOL
                ICAND = 0
                done = True
                for i in range(1, IMAX): 
                    if A[i, JMAX] < H:
                        done = False
                        H = A[i, JMAX]
                        ICAND = i
                ##next

                if done:
                    break
                else:
                    JCAND = 0
                    RATIO = -10000000000
                    for j in range(NPredictors):
                        IONE = 1
                        aa = A[ICAND, j]
                        if np.abs(aa) >= TOL:
                            RCOST = A[0, j]
                            if aa >= -TOL:
                                IONE = -1
                                if np.abs(NB[j]) > NPredictors:
                                    RCOST -= 2
                                ##end if
                            ##endif
                            r = RCOST / aa
                            if r > RATIO:
                                JCAND = j * IONE
                                RATIO = r
                                RSAVE = RCOST
                            #endif
                        #endif
                    #next j

                    IT = ISS[ICAND]
                    II = np.abs(IT)
                    CJ = C[II]
                    if RATIO > -CJ:
                        break
                    else:
                        ISS[ICAND] *= -1 #Make -ve or vice versa
                        for j in range(JMAX):
                            A[0, j] += CJ * A[ICAND, j] * -1
                            #A[]
                        #j
                    #endif
                #endif

            #end while
            if done:
                break

            oneFlipper = 1
            if JCAND <= 0:
                JCAND *= -1
                NB[JCAND] *= -1
                oneFlipper = -1
                A[0, JCAND] = RSAVE
            pivot = A[ICAND, JCAND] * oneFlipper
            for j in range(JMAX):
                A[ICAND, j] /= pivot
            #next j
            for i in range(IMAX):
                if i != ICAND:
                    AIJ = A[i, JCAND] * oneFlipper
                    if AIJ != 0:
                        for j in range(JMAX):
                            A[i, j] -= A[ICAND, j] * AIJ
                        #next j
                        A[i, JCAND] = -AIJ / pivot
                    #endif
                #endif
            #next i
            A[ICAND, JCAND] = 1 / pivot
            ISS[ICAND] = NB[JCAND]
            NB[JCAND] = IT

        #endwhile

        ALPHA = yBar
        for i in range(1, IMAX):
            oneFlipper = 1
            II = ISS[i]
            if np.abs(II) <= NPredictors:
                if II <= 0:
                    II *= -1
                    oneFlipper = -1
                #endif
                B[II] = oneFlipper * A[i, JMAX]
                ALPHA -= xBar[II] * B[II]
            #endif
        #next i

        betaMatrix = np.zeros((NPredictors))
        betaMatrix[0] = ALPHA
        for i in range(NPredictors):
            betaMatrix[i] = B[i]
        #next i
        xTransY = np.matmul(xMatrix.transpose(), yMatrix)

        dependencies = False
        for i in range(NPredictors):
            if np.abs(NB[i]) <= NPredictors:
                dependencies = True
                break

        if dependencies and not dependMsg:
            ##Warning error
            pass
        #endif
    #endif

    predictedMatrix = np.matmul(xMatrix, betaMatrix)
    residualMatrix = np.subtract(yMatrix, predictedMatrix)
    meanY = 0
    if len(yMatrix) > 0:
        meanY = yBar
    else:
        meanY = globalMissingCode

    RSS = 0
    for i in range(xMatrix.shape[0]):
        modelled = 0
        for j in range(xMatrix.shape[1]):
            modelled += betaMatrix[j] * xMatrix[i, j]
        #next j
        RSS += (modelled - yMatrix[i]) ** 2
    #next i
    RSS = max(RSS, 0.0001)
    
    if meanY != globalMissingCode:
        SSM = 0
        for i in range(xMatrix.shape[0]):
            modelled = 0
            for j in range(xMatrix.shape[1]):
                modelled += (betaMatrix[j] * xMatrix[i, j])
            #next j
            SSM += (modelled - meanY) ** 2
        #next i
        fRatio = (SSM / NPredictors) / (RSS / (xMatrix.shape[0] - NPredictors))
    else:
        fRatio = globalMissingCode
    #endif

    return {"fRatio":fRatio, "betaMatrix":betaMatrix, "residualMatrix":residualMatrix, "predictedMatrix":predictedMatrix, "RSS":RSS}

def transformData(xMatrix: np.ndarray, yMatrix: np.ndarray, extraArrays: np.ndarray, modelTrans: int):
    """
        Transform data v1.0
        transforms data in Y Matrix according to transformation required.  Amends (reduces) X matrix too if some values are missing
        modelTrans ->  Option from None (1), 4th Root (2), Natural Log (3), Inverse Normal (4), Box Con (5)
        yMatrix -> 'Y Matrix - X declared globally so registration code entered
    """
    ##Calls FindMinLambda

    ### GLOBALS ###
    globalMissingCode = _globalSettings['globalmissingcode']
    ### ####### ###

    #If modelTrans == 1 then do nothing -> no transformation
    if modelTrans == 1:
        return {'xMatrix':xMatrix, 'yMatrix':yMatrix, 'extraArrays':extraArrays, 'tResults':None}
    elif modelTrans == 2 or modelTrans == 3: #4th Root or Log selected
        ##First, remove missing valus
        if modelTrans == 2:
            rejectedIndex = [i for i in range(len(yMatrix)) if yMatrix[i] < 0]
        else: 
            rejectedIndex = [i for i in range(len(yMatrix)) if yMatrix[i] <= 0]
        xMatrix = np.delete(xMatrix, rejectedIndex, 0)
        yMatrix = np.delete(yMatrix, rejectedIndex)
        for i in range(len(extraArrays)):
            extraArrays[i] = np.delete(extraArrays[i], rejectedIndex)
        
        ##Apply Transformations
        if modelTrans == 2:
            yMatrix = [i ** 0.25 for i in yMatrix] ##4th root
        else:
            yMatrix = [np.log(i) for i in yMatrix] ##nat log
        
        return {'xMatrix':xMatrix, 'yMatrix':yMatrix, 'extraArrays':extraArrays, 'tResults':None}
        #endif
    elif modelTrans == 4:        #'Inverse normal selected: model trans=4
        #rankMatrix = np.zeros((2, len(yMatrix))) #'add an extra column     ##In this era, for the sake of storage, these matricies are stored horizontally. Mechanically adding another row..
        #rankMatrix[0] = deepcopy(yMatrix)      #'copy Y matrix into RankMatrix
        #Set ReSampleMatrix = New Matrix         'save these data in global matrix so can be resampled when untransforming
        #Set ReSampleMatrix = YMatrix.Clone
        reSampleMatrix = yMatrix
        rankMatrix = deepcopy(yMatrix) #TransformData will create a new array, not augment an existing one
        ordMatrix = np.array(range(len(yMatrix)))  #save initial ordering //ordMatrix
        argSort = np.argsort(rankMatrix, kind='stable')   #'sort ascending
        rankMatrix = rankMatrix[argSort]
        ordMatrix = ordMatrix[argSort]             
        
        #            'Locate lower bound to begin estimation of cdf
        #            'cdf is computed as r/(n+1) where r is the rank and n is sample size
        zStart = 1 / (len(yMatrix) + 1)
        delta = 0.0001
        area = 0.5
        fx = 0
        fxOld = fxNormal(fx)         #'normal
        i = 1 #Counter
        while ((i <= 50000) and (area > zStart)):
            #debugMsg("Loop3")
            fx -= delta
            fxNew = fxNormal(fx)         #'normal
            area -= (delta * 0.5 * (fxOld + fxNew))
            fxOld = fxNew
            i += 1
        #endwhile

        #'Compute cdf between lower and upper limit
        limit = fx
        area = zStart
        rankMatrix[0] = limit
        percentileChange = (1 - (area * 2)) / (len(yMatrix) - 1)
        cp = area
        fxOld = fxNormal(fx)         #'normal

        for i in range(1, len(yMatrix)): #2 To RankMatrix.Rows
            cp += percentileChange
            j = 1
            while ((j <= 50000) and (area < cp)):
                #debugMsg("Loop4")
                fx += delta
                fxNew = fxNormal(fx)         #'normal
                area += (delta * 0.5 * (fxOld + fxNew))
                fxOld = fxNew
                #if area >= cp:
                j += 1
            #print(f"j: {j}")
            rankMatrix[i] = fx
            #Wend
        #Next i
            
        argSort = np.argsort(ordMatrix)  #'sort back into temporal sequence and copy data back to YMatrix
        rankMatrix = rankMatrix[argSort]
        #rankMatrix[1] = rankMatrix[1][argSort] 
        #yMatrix = deepcopy(rankMatrix[0])
        #For i = 1 To RankMatrix.Rows
        #    YMatrix(i - 1, 0) = RankMatrix(i - 1, 0)
        #Next i

        return {'xMatrix':xMatrix, 'yMatrix':rankMatrix, 'extraArrays':extraArrays, 'tResults':reSampleMatrix}

    elif modelTrans == 5: #          'box cox - so need to find best lamda of YMatrix
        data_err = "There is insufficient data for a Box Cox transformation.  Try an alternative transformation"
        unknown_err = "Unknown error calculating the optimum lamda transform"
        minSoFar = np.min(yMatrix[1:])
        shiftRight = np.abs(min(minSoFar, 0))

        if shiftRight != 0: #No point shifting if = 0
            for i in range(1, len(yMatrix)):              #'now shift all Y matrix data right to make sure it's +ve before we calculate lamda
                yMatrix[i] += shiftRight
        #Next i

        ################
        ## Lamda Calc ##
        ################

        insufficientData = False    #'assume enough data unless FindMinLamda tells us otherwise
        lamda = findMinLamda(-2, 2, 0.25, yMatrix, insufficientData)  #'find a value between -2 to +2

        if lamda != globalMissingCode: #  'now home in a bit more
            lamda = findMinLamda((lamda - 0.25), (lamda + 0.25), 0.1, yMatrix, insufficientData)
        else:
            if insufficientData:
                raise ValueError(data_err) #Not enough data error
            else:
                raise RuntimeError(unknown_err)
        #End If
        if lamda != globalMissingCode: #'home in a bit further
            lamda = findMinLamda((lamda - 0.1), (lamda + 0.1), 0.01, yMatrix, insufficientData)
        else:
            if insufficientData:
                raise ValueError(data_err) #Not enough data error
            else:
                raise RuntimeError(unknown_err)
        #End If

        if lamda == globalMissingCode:
            if insufficientData:
                raise ValueError(data_err) #Not enough data error
            else:
                raise RuntimeError(unknown_err)
        #End If

        #######################
        ## End of Find Lamda ##
        #######################

        rejectedIndex = []
        for i in range(len(yMatrix)):
            if lamda == 0:                          # 'apply box cox lamda transform - do some checks for division by zero first
                if yMatrix[i] > 0:
                    yMatrix[i] = np.log(yMatrix[i]) - shiftRight         #'shift it back to left after transform
                elif yMatrix[i] == 0:
                    yMatrix[i] = -5 - shiftRight     #'cannot log zero so -5 represents log of a very small number
                else:
                    rejectedIndex.append(i)                    
                #End If
            else:
                yMatrix[i] = (((yMatrix[i] ** lamda) - 1) / lamda) - shiftRight     #'shift it back to left after transform
            #End If
        #Next i

        ##Remove missing values
        xMatrix = np.delete(xMatrix, rejectedIndex, 0)
        yMatrix = np.delete(yMatrix, rejectedIndex)
        for i in range(len(extraArrays)):
            extraArrays[i] = np.delete(extraArrays[i], rejectedIndex)
        

        return {'xMatrix':xMatrix, 'yMatrix':yMatrix, 'extraArrays':extraArrays, 'tResults':{'lamda':lamda, 'shiftRight':shiftRight}}

   

    #End If
    
    #return Something here
    return None

def findMinLamda(start: float, finish: float, stepSize: float, passedMatrix: np.ndarray, insufficientData: bool) -> int:
    #Start, Finish & Stepsize were previously of type "double" (equivalent to float?)
    """
        Find Min Lambda
        Idk
    """

    #'uses DosserCox transformation and tries different values of lamda
    #'until lowest result identified - where result is Hinkley (1977) equation
    #'tries lamda values from start to finish in steps of stepsize for passedMatrix
    #'passedMatrix has already been right shifted by shiftright to make sure it is all >=0
    #'returns either GlobalMissingCode if not found or minimum lamda value if it was
    GlobalMissingCode = -999
    #bestLamdaSoFar As Double  #'Best Lamda so far
    #Dim minResultSoFar As Double  #'Hinkley (1977) calculation for optimum lamda
    #Dim Mean As Double      #'mean of transformed values
    #Dim IQR As Double        #'Inter Quartile Range of transformed values
    #Dim upper As Long: Dim Lower As Long #'position of IQR values
    #Dim Median As Double    #'Median
    #Dim d As Double         #'d as per Hinkley
    #Dim tempMatrix As Matrix
    #Dim counter As Integer, Missing As Integer  #'missing counts number we can't transform
    bestLamdaSoFar = start  #'set best lamda to first point to try
    minResultSoFar = 99999  #'set minimum d value to big number to start

    #may need finish+1
    #for k in range(start, finish, stepSize):   #'try each value of lamda in turn
    #python doesn't like for range loops over floats
    
    k = start
    while k < finish:
        #Set tempMatrix = New Matrix
        tempMatrix = deepcopy(passedMatrix)    #'copy passedMatrix into tempmatrix so we don't disturb it just in case
        mean = 0                            #'ymatrix contains only values>=0
        counter = 0
        missing = 0                         #'count of numbers we can't transform
        for i in range(len(tempMatrix)):   #'set up temp matrix with transformed data
            if (k == 0) and (tempMatrix[i] == 0):
                tempMatrix[i] = -99999        #'can't log zero so set missing value to -99999 as these will be sorted to top later
                missing = missing + 1
            else:
                if k == 0:      #'ln transform for lamda = 0
                    tempMatrix[i] = np.log(tempMatrix[i])
                else:
                    tempMatrix[i] = ((tempMatrix[i] ** k) - 1) / k #'BoxCox transform
                #End If
            mean = mean + tempMatrix[i]
            counter = counter + 1
            #End If
        #Next i    'temp matrix set up with transformed data, mean has mean and counter number of valid values
        if counter >= 50:           #'do we have enough data to work with?
            mean = mean / counter
            tempMatrix.sort()         #'will put all -99999s to the top (there are missing of these)
            #' need to calculate median and SD
            median = tempMatrix[((counter // 2) + missing)]           #'add on missing so we only look at valid numbers
            lower = (counter // 4) + missing
            upper = (counter - lower) + missing
            
            IQR = tempMatrix[upper] - tempMatrix[lower]

            #'now calculate d as per Hinkley
            if IQR > 0:
                d = (mean - median) / IQR
            else:
                d = GlobalMissingCode
            #End If
            
            if (d != GlobalMissingCode) and (np.abs(d) < minResultSoFar):
                minResultSoFar = np.abs(d) #'keep track of best values so far
                bestLamdaSoFar = k
            #End If
        else:
            insufficientData = True
        #End If      ' end of check for sufficient data to calculate lamda
        k += stepSize
    #Next k  'try for all values of k
    
    if minResultSoFar == 99999:  #'haven't found anything
        return GlobalMissingCode
    else:
        return bestLamdaSoFar   #'return bestLamdaSoFar as this has lowest d value
    #End If

def untransformData(matricies: np.ndarray, tResults):
    """
    Untransform Data for Conditional Part
    -- tResults is the results array from the Transform Data function
    """

    ### GLOBALS ###
    globalMissingCode = _globalSettings['globalmissingcode']
    modelTrans = _globalSettings['modelTrans']
    ### ####### ###

    if modelTrans == 1: #no transform
        pass
    elif modelTrans == 2: #4th root
        for matrix in matricies:
            for i in range(len(matrix)):
                if matrix[i] != globalMissingCode:
                    matrix[i] **= 4
            #if yMatrix[i] != globalMissingCode:
            #    yMatrix[i] **= 4
    elif modelTrans == 3: #nat log
        for matrix in matricies:
            for i in range(len(matrix)):
                if matrix[i] != globalMissingCode:
                    matrix[i] = np.exp(matrix[i])
            #if yMatrix[i] != globalMissingCode:
            #    yMatrix[i] = np.exp(yMatrix[i])

    elif modelTrans == 4: #inverse normal 
        #transformResults = reSampleMatrix -> unsorted data to take resampling from
        ##SORT ROWS
        rsMatrix = np.sort(tResults, kind='stable')
        ## "Locate lower bound to begin estimation of cdf"
        error = False
        zStart = 1 / (len(rsMatrix) + 1) 
        delta = 0.0001
        area = 0.5
        fx = 0
        fxOld = fxNormal(fx)
        if fxOld == globalMissingCode: 
            #BombOut
            error = True
        if not error:
            for i in range(50000):
                fx -= delta
                fxNew = fxNormal(fx)
                if fxNew == globalMissingCode:
                    # Then BombOut
                    error = True
                    break
                area -= (delta * 0.5 * (fxOld + fxNew))
                if area <= zStart:
                    break
                fxOld = fxNew
            #Next i
        if error: #Untransform failed - inverse normal cannot be calculated
            debugMsg("[Error]: Inverse normal cannot be calculated")
            for matrix in matricies:
                for i in range(len(matrix)):
                    matrix[i] = globalMissingCode
                #yMatrix[i] = globalMissingCode
        else:
            ## "Compute area between lower and each z-score"
            limit = fx
            totalArea = (1 - (2 * zStart))

            for matrix in matricies:
                for i in range(len(matrix)): #'now use translator to convert all values
                    if matrix[i] != globalMissingCode:
                        matrix[i] = translator(matrix[i] , limit, totalArea, rsMatrix)
                #if yMatrix[i] != globalMissingCode:
                #    yMatrix[i] = translator(yMatrix[i], limit, totalArea, tResults)
            #next i
        #endif
    
    elif modelTrans == 5: #Box Cox
        #transformResults = {'lamda', 'shiftRight'}
        lamda = tResults['lamda']
        shift = tResults['shiftRight']
        for matrix in matricies:
            for i in range(len(matrix)):
                if matrix[i] != globalMissingCode:
                    tempValue = matrix[i] + shift #shift right for current period
                    if lamda == 0:
                        tempValue = np.exp(tempValue) - shift #log transform
                    else:
                        tempValue = (lamda * tempValue) + 1
                        if tempValue > 0:
                            tempValue = np.log(tempValue) / lamda
                            tempValue = np.exp(tempValue) - shift
                        else:
                            tempValue = globalMissingCode
                    matrix[i] = tempValue
           #next i
        #next matrix
    #endif

def translator(passedValue: float, limit: float, totalArea: float, reSampleMatrix) -> float:
    """
    Untransform Data: Inverse Normal helper function
    """

    ### GLOBALS ###
    globalMissingCode = _globalSettings['globalmissingcode']
    ### ####### ###

    if passedValue <= limit:
        return reSampleMatrix[0]
    else:
        try:
            fxOld = fxNormal(limit)
        except: #fxOld is invalid / cannot be caluclated
            return globalMissingCode
        else:
            interval = (passedValue - limit) / 100
            area = 0
            fx = limit
            for i in range(100):
                fx = fx + interval
                try: 
                    fxNew = fxNormal(fx)
                except:
                    return globalMissingCode
                else:
                    area += (interval * 0.5 * (fxOld + fxNew))
                    fxOld = fxNew
                #end catch
            #next i
            area = min(area, totalArea)
            locateValue = int(area * len(reSampleMatrix) / totalArea)
            locateValue = min(locateValue, (len(reSampleMatrix) - 1))
            return reSampleMatrix[locateValue]

def printResults(parameterResultsArray: np.ndarray, NPredictors: int, parmOpt: bool, biasCorrection, autoRegression: bool, modelTrans: int, tResults: list):
    """
    Collects data from output arrays and merges it into
     string form, ready to be written to the PARfile
    """
    #We want: parmOpt, parameterResultsArray, nPredictors, autoregrssion, lamdaArray, modelTrans, biascorrection
    giga_array = ""
    if parmOpt:
        for i in range(12):
            parameterResultsArray[i, NPredictors + 1 + int(autoRegression)] = 0
    for i in range(12):
        for j in range(NPredictors + 3 + int(autoRegression)):
            giga_array += f"{parameterResultsArray[i, j]:.3f}\t"
        #next j
        if modelTrans == 5:
            #tResults is the LamdaArray
            giga_array += f"{tResults[i, 0]:.3f}\t"
            giga_array += f"{tResults[i, 1]:.3f}"
        #endif
        giga_array += "\n"
    #next i
    if parmOpt:
        for i in range(12, 24):
            giga_array += f"{parameterResultsArray[i, 0]:.3f}\t"
            giga_array += f"{biasCorrection[i - 12]:.3f}\t"
            for j in range(1, NPredictors + 3):
                giga_array += f"{parameterResultsArray[i, j]:.3f}\t"
            #next j
            giga_array += "\n"
        #next i
    #endif

    return giga_array

    #Write to file
    #with open(parfile, "a") as f:
    #    print(giga_array, file=f)
    #    f.close()

def printTrendParms(detrendOption: int, betaTrend, seasonCode: int):
    """
    Collects data from the betaTrend array and returns it
     in string form, ready to be written to the PARfile
    """

    giga_array = ""
    if detrendOption == 1:
        giga_array += "1\n"
    else: #Assume option #2
        giga_array += "2\n"
    #endif

    #if seasonCode == 1:
    #    giga_array += f"{betaTrend[0,0]}\t{betaTrend[0,1]}"
    #    if detrendOption == 2:
    #        giga_array += f"\t{betaTrend[0,2]}\n"
    #    else:
    for i in range(seasonCode):
        giga_array += f"{betaTrend[i][0]}\t{betaTrend[i][1]}"
        if detrendOption == 2:
            giga_array += f"\t{betaTrend[i][2]}"
        giga_array += "\n"
    
    return giga_array

    #Write to file
    #with open(parfile, "a") as f:
    #    print(giga_array, file=f)
    #    f.close()
                
                


def plotScatter(residualArray):
    #mimicked from ScreenVariables
    import pyqtgraph as pg

    """
    On Error GoTo ErrorHandler
    Dim i As Long
    Load ScatterChartFrm
    ScatterChartFrm.HiddenXTitleText.Text = "Predicted Value (Y')"    'X axis label
    ScatterChartFrm.HiddenYTitleText.Text = "Residual"       'Y axis label
    ScatterChartFrm.Chart1.Plot.Axis(VtChAxisIdY).AxisTitle.Text = "Residual"
    ScatterChartFrm.Chart1.Plot.Axis(VtChAxisIdX).AxisTitle.Text = "Predicted Value (Y')"
    ScatterChartFrm.Chart1.ColumnCount = 2
    ScatterChartFrm.Chart1.rowCount = NoOfResiduals         'Maximum possible data to display
    
    For i = 1 To NoOfResiduals
        ScatterChartFrm.Chart1.DataGrid.SetData i, 2, ResidualArray(2, i), 0    'Insert the residual into this row - Y axis
        ScatterChartFrm.Chart1.DataGrid.SetData i, 1, ResidualArray(1, i), 0    'Insert Y' value onto X axis
    Next i
    ScatterChartFrm.Chart1.DataGrid.SetSize 0, 0, NoOfResiduals, 2   'Resize data grid to only show data wanted
    
    ScatterChartFrm.Chart1.Title = "Residual Plot"
    ScatterChartFrm.HiddenTitleText = "Residual Plot"
    ScatterChartFrm.Show   
    """
    #ResidualArray(1,i) is equivalent to residualArray['predicted'][i], and should go on the X axis
    #ResidualArray(2,i) is equivalent to residualArray['residual'][i], and should go on the Y axis
    #NoOfResiduals is equivalent to residualArray['noOfResiduals'] and should contain the length of the array

    plot = pg.plot()
    scatter = pg.ScatterPlotItem(size=10, brush=pg.mkBrush(255, 255, 255, 120))

    outputData = residualArray
    spots = [
        {"pos": [residualArray['predicted'][i], residualArray['residual'][i]]}
        for i in range(residualArray['noOfResiduals'])
    ]
    scatter.addPoints(spots)
    plot.addItem(scatter)

def plotHistogram(residualArray, noOfHistCats):

    minVal = np.min(residualArray['residual'])
    maxVal = np.max(residualArray['residual'])
    sizeOfCategories = (maxVal - minVal) / noOfHistCats
    
    for i in range(noOfHistCats):
        #???
        catMin = minVal + (i * sizeOfCategories)
        catMax = catMin + sizeOfCategories
        for j in range(residualArray['noOfResiduals']):
            if residualArray['residual'][j] >= catMin and residualArray['residual'] < catMax:
                ##residualHistData[i][2] + 1
                pass
        #next j
    #next i

    ##formatting....

    #residualHistData[1][1] = str(minVal:.3f)
    #residualHistData[noOfHistCats][1] = str(maxVal:.3f)

    #intermediate labels?
    #for i in range(1, noOfHistCats):
    #   catMin = minVal + (i * sizeOfCategories)
    #   residualHistData[i, 1] = str(catMin:.3f)
        
    

    """
    Private Sub PlotHistogram()       'plots a histogram of residuals
    On Error GoTo ErrorHandler
    ReDim ResidualHistogramData(1 To NoOfHistogramCats, 1 To 2)        'x=labels and data, y= data
    Dim MaxValue As Double, MinValue As Double, SizeOfCategories As Double
    Dim CatMin As Double, CatMax As Double
    MaxValue = -999          'calculate max and min in observed data
    MinValue = 999
    For i = 1 To NoOfResiduals
        If ResidualArray(2, i) > MaxValue Then MaxValue = ResidualArray(2, i)
        If ResidualArray(2, i) < MinValue Then MinValue = ResidualArray(2, i)
    Next i
    SizeOfCategories = (MaxValue - MinValue) / NoOfHistogramCats
                      
    For i = 1 To NoOfHistogramCats
        ResidualHistogramData(i, 2) = 0 'propogate column 2; col 1 for legend lables
    Next i
    
    For i = 1 To NoOfHistogramCats  'calculate number of points in each category
        CatMin = MinValue + ((i - 1) * SizeOfCategories)
        CatMax = CatMin + SizeOfCategories
        For j = 1 To NoOfResiduals
            If ((ResidualArray(2, j) >= CatMin) And (ResidualArray(2, j) < CatMax)) Then
                ResidualHistogramData(i, 2) = ResidualHistogramData(i, 2) + 1
            End If
        Next j
    Next i

    tempz = Format(MinValue, "####0.000")
    ResidualHistogramData(1, 1) = Str(tempz)
    tempz = Format(MaxValue, "####0.000")
    ResidualHistogramData(NoOfHistogramCats, 1) = Str(tempz)

    For i = 2 To NoOfHistogramCats - 1      'set up intermediate labels
        CatMin = MinValue + ((i - 1) * SizeOfCategories)
        tempz = Format(CatMin, "####0.000")
        ResidualHistogramData(i, 1) = Str(tempz)
    Next i

    SeriesDataFirstValue = ResidualHistogramData(1, 1) 'save first value in time series array
    Load HistogramFrm
    HistogramFrm.Reset_All
    HistogramFrm.Show
    Exit Sub
ErrorHandler:
    Call HandleError(Err.Number)
    Call Mini_Reset
    Exit Sub
End Sub
    """

##Helper Functions:

def calcRSQR(modMatrix: np.ndarray, yMatrix: np.ndarray, limit: int, checkMissing: bool, missingLim: int = None):
    """
    RSQR Shared code for xValidation & Calculate Params #1, neatly merged into one function
    modMatrix and yMatrix are both 1 dimensional slices of the original array
    limit is the length of the iterator / size of the matrix slice. Might be redundant
    checkMissing toggles whether missing values are ignored or not. True -> Ignore missing, False -> Count them
    --> CheckMissing might be redundant...
    """

    ### GLOBALS ###
    globalMissingCode = _globalSettings['globalmissingcode']
    ### ####### ###

    if missingLim == None:
        missingLim = limit

    sumX = sumY = sumXX = sumYY = sumXY = missing = 0

    for i in range(limit):
        if (modMatrix[i] != globalMissingCode and yMatrix[i] != globalMissingCode) or checkMissing == False:
            sumX += modMatrix[i]
            sumY += yMatrix[i]
            sumXX += modMatrix[i] ** 2
            sumYY += yMatrix[i] ** 2
            sumXY += modMatrix[i] * yMatrix[i]
        else:
            missing += 1
    ##end for

    rsqr = globalMissingCode
    if missing < missingLim: 
        totalVals = limit - missing
        denom = sumXX - (sumX ** 2 / totalVals)
        denom *= sumYY - (sumY ** 2 / totalVals)
        numerator = (sumXY - ((sumX * sumY) / totalVals)) ** 2

        if denom > 0:
            rsqr = numerator / denom
        elif denom < 0:
            ##Edge case testing
            debugMsg("Error: Edge Case Detected - denom < 0")
            #readline()
            rsqr = globalMissingCode
        else:
            rsqr = globalMissingCode

    debugMsg(f"calcRSQR: {rsqr}, only if {missing} < {missingLim}")
    
    return rsqr

def calcPropCorrect(modMatrix: np.ndarray, yMatrix: np.ndarray, limit: int):
    """
    Proportion Correct Shared code for xValidation:Unconditional (parmOpt=F) & Calculate Params #1
    """

    globalMissingCode = _globalSettings['globalmissingcode']

    correctCount = 0
    missing = 0
    for i in range(limit):
        if (modMatrix[i] != globalMissingCode and yMatrix[i] != globalMissingCode):
            if (yMatrix[i] == 0 and modMatrix[i] < 0.5):
                correctCount += 1
            elif (yMatrix[i] == 1 and modMatrix[i] >= 0.5):
                correctCount += 1
            #endif
        else:
            missing += 1
        #endif
    #next i
    if missing < limit:
        propCorrect = correctCount / (limit - missing)
    else:
        propCorrect = globalMissingCode
    
    return propCorrect

def getSeason(month):
    if month < 12 and month >= 9: #Months 9,10,11 (Autumn)
        return 3
    elif month < 9 and month >= 6: #Months 6,7,8 (Summer)
        return 2
    elif month < 6 and month >= 3: #Months 3,4,5 (Spring)
        return 1
    else: #Months 12,1,2 (Winter)
        return 0
    
def fxNormal(fx):
    #Exp(-(fx ^ 2) / 2) / Sqr(2 * 3.1415927)
    return np.exp(-(fx ** 2) / 2) / np.sqrt(2 * np.pi)

def displayError(error):
    messageBox = QMessageBox()
    messageBox.setIcon(QMessageBox.Critical)
    messageBox.setText(f"{type(error).__name__}:")
    messageBox.setInformativeText(str(error))
    messageBox.setWindowTitle("Error")
    messageBox.exec_()


def formatCalibrateResults(results):
    """
    Format Calibrate analysis results for display in a PyQt5 application.
    
    Parameters:
    results (dict): Dictionary containing Calibrate analysis results
    
    Returns:
    str: Formatted string representation of the Calibrate results
    """
    # Extract necessary data from results dictionary
    startDate = results['analysisPeriod']['startDate']
    endDate = results['analysisPeriod']['endDate']
    periodName = results['analysisPeriod']['periodName']
    
    # Statistics

    #conditional = results['settings_used']['conditionalAnalysis']
    
    # Data
    predictand = results['Predictand'].split('/')[-1]
    #fileNames = results['names']
    #crossCorr = results['crossCorrelation']
    #partialCorrelations = results['partialCorrelations'] if 'partialCorrelations' in results else None
    
    # Format output as a string
    output = []
    
    # Header section
    output.append("Predictand: " + predictand)
    output.append("")
    output.append("Predictors: ")
    for i in range(0, len(results['Predictors'])):
        x = results['Predictors'][i].split("/")[-1]
        output.append(f"{x}")
    if results['autoregression'] == True:
        output.append(f"Autoregression")
    output.append("")
    output.append(f"Analysis Period: {startDate} - {endDate} ({periodName})")
    output.append("")

    maxWidth = 12

    output.append("Unconditional Statistics")
    #Get all the keys in the first dictionary within unconditional results
    unconditionalResultsList = list(results['Unconditional'].keys())
    firstUnconditionalEntryKey = unconditionalResultsList[0]
    unconditionalKeyList = list(results['Unconditional'][firstUnconditionalEntryKey].keys())
    
     # Calculate the maximum length of keys for formatting
    if results['ifXVal']:
        line = ""
        line += (f"{'':{maxWidth*(len(unconditionalKeyList)+1)}}")
        line += ("Cross Validation Results")
        output.append(line)

    else:
        output.append("")
    # Cross-correlation matrix header
    headerRow = ""
    headerRow+= f"{'Month':{maxWidth}}"
    for j in range(len(unconditionalKeyList)):
        headerRow += f"{unconditionalKeyList[j]:{maxWidth}}"
    

    if "xValidation" in results['Unconditional']:
        xValidationDict = results['Unconditional']["xValidation"]
        xValidationKeys = list(xValidationDict.keys()) #Months
        xValidationResultsKeys = list(xValidationDict[xValidationKeys[0]].keys()) #Results within the month
        for key in xValidationResultsKeys:
            headerRow += f"{key:{maxWidth}}"
    output.append(headerRow)

        

    for i in unconditionalResultsList:
        result = ""
        if i != "xValidation":
            result += f"{i:{maxWidth}}"
        resultsList = list(results['Unconditional'][i].keys())
        for j in resultsList:
            if i != "xValidation":
                result += f"{str(round(float(results['Unconditional'][i][j]),5)):{maxWidth}}"
        if results['ifXVal']:
            #xValidation is a dictionary, so go into the months, then get the results from that
            #print("\n\n\n\n\n\n")
            for k in xValidationResultsKeys:
                if i != "xValidation":
                    xValidation = xValidationDict[i][k]
                    result += f"{str(round(float(xValidation),5)):{maxWidth}}"
        
        output.append(result)
    output.append("")
    if "Conditional" in results:
        #Get all the keys in the first dictionary within unconditional results
        conditionalResultsList = list(results['Conditional'].keys())
        firstConditionalEntryKey = conditionalResultsList[0]
        conditionalKeyList = list(results['Conditional'][firstConditionalEntryKey].keys())
        output.append("Conditional Statistics")
        if results['ifXVal']:
            line = ""
            line += (f"{'':{maxWidth*(len(conditionalKeyList)+1)}}")
            line += ("Cross Validation Results")
            output.append(line)

        else:
            output.append("")
        # Conditional statistics header
        headerRow = ""
        headerRow += f"{'Month':{maxWidth}}"
        for j in range(len(conditionalKeyList)):
            headerRow += f"{conditionalKeyList[j]:{maxWidth}}"
        if "xValidation" in results['Conditional']:
            xValidationDict = results['Conditional']["xValidation"]
            xValidationKeys = list(xValidationDict.keys()) #Months
            xValidationResultsKeys = list(xValidationDict[xValidationKeys[0]].keys()) #Results within the month
            for key in xValidationResultsKeys:
                headerRow += f"{key:{maxWidth}}"
        output.append(headerRow)
        for i in conditionalResultsList:
            result = ""
            if i != "xValidation":
                result += f"{i:{maxWidth}}"
                resultsList = list(results['Conditional'][i].keys())
                for j in resultsList:
                    result += f"{str(round(float(results['Conditional'][i][j]),5)):{maxWidth}}"

                if results['ifXVal']:
                #xValidation is a dictionary, so go into the months, then get the results from that
                    for k in xValidationResultsKeys:
                        if i != "xValidation":
                            xValidation = xValidationDict[i][k]
                            result += f"{str(round(float(xValidation),5)):{maxWidth}}"
                output.append(result)

    '''
    # Cross-correlation matrix rows
    for j in range(nVariables):
        row = f"{j+1} {fileNames[j]:{maxLength}}"
        
        for k in range(nVariables):
            corrValue = crossCorr[j][k]
            if k == j:
                tempY = "1"
            else:
                tempY = f"{corrValue:.3f}"
            row += f"{tempY:{maxLength + 2}}"
        
        output.append(row)
    
    output.append("")
    
    # Partial correlations section
    if nVariables < 3:
        output.append("NO PARTIAL CORRELATIONS TO CALCULATE")
    else:
        output.append(f"PARTIAL CORRELATIONS WITH {fileNames[0]}")
        output.append("")
        output.append(" " * 24 + f"{'Partial r':12}{'P value':12}")
        output.append("")
        
        # Add partial correlation results if available
        if partialCorrelations:
            for i in range(1, nVariables):
                if i-1 < len(partialCorrelations):
                    partialR = partialCorrelations[i-1]['correlation']
                    pValue = partialCorrelations[i-1]['p_value']
                    output.append(f"{fileNames[i]:24}{partialR:<12.3f}{pValue:<12.3f}")
    
    # Join all lines with newlines '''

    return "\n".join(output)


def displayCorrelationResultsQt(results, textWidget):
    """
    Display correlation results in a PyQt5 text widget.
    
    Parameters:
    results (dict): Dictionary containing correlation analysis results
    textWidget (QTextEdit/QPlainTextEdit): PyQt5 text widget to display the results
    """
    # Format the results
    formattedText = formatCalibrateResults(results)
    
    # Set the font to a monospaced font for proper alignment
    font = QFont("Courier New", 10)
    textWidget.setFont(font)
    
    # Display the formatted text
    textWidget.setPlainText(formattedText)

class CalibrateAnalysisApp(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Correlation Analysis")
            self.resize(800, 600)
            
            # Create a tab widget for different views
            self.tabWidget = QTabWidget()
            
            # Text view tab
            self.textWidget = QTextEdit()
            self.textWidget.setReadOnly(True)
            self.tabWidget.addTab(self.textWidget, "Text View")
            
            # Set the central widget
            self.setCentralWidget(self.tabWidget)
        
        def loadResults(self, results):
            # Display text format
            displayCorrelationResultsQt(results, self.textWidget)
            print()
            # Create and add table view
            #tableWidget = createCorrelationTableWidget(results)
            #self.tabWidget.addTab(tableWidget, "Table View")

        
##