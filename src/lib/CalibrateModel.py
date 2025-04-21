import numpy as np
from datetime import date as realdate
from src.lib.utils import loadFilesIntoMemory, increaseDate, thirtyDate, getSettings
from copy import deepcopy
import src.core.data_settings
#from scipy.stats import spearmanr

## NOTE TO READERS: THIS FILE **DOES** WORK
## The debugRun test function should give an example configuration

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
    elif mT == '4th Root':
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
        
def debugRun():
    calibrateModelDefaultExperience()

def calibrateModelDefaultExperience():
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
    #feDate = date(1996, 12, 31)
    #feDate = date(1997, 12, 31)
    feDate = date(2015, 12, 31)
    modelType = 0 #0
    parmOpt = True  ## Whether Conditional or Unconditional. True = Cond, False = Uncond. 
    ##ParmOpt(1) = Uncond = False
    ##ParmOpt(0) = Cond = True
    autoRegression = False ## Replaces AutoRegressionCheck -> Might be mutually exclusive with parmOpt - will check later...
    includeChow = True
    detrendOption = 0 #0, 1 or 2...
    doCrossValidation = True
    crossValFolds = 7

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
        "p__f", "p__u", "p__v", "p__z"
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

    ## Output for similar results to the OG software:
    print(f"FINAL RESULTS:")
    debugMsg(f"Debug data:")
    debugMsg(f"Fit Start Date: {fsDate}")
    debugMsg(f"Fit End Date: {feDate}")
    #print(f"Predictand: {PTandRoot}")
    print(f"\nPredictors:\n")
    for i in fileList:
        print(i)
            
    ##Useful info on how to display/format the resutls...
    #from calendar import month_name
    ## Better formatted Month Names so they are all same length
    month_name = [
        "January  ",
        "February ",
        "March    ",
        "April    ",
        "May      ",
        "June     ",
        "July     ",
        "August   ",
        "September",
        "October  ",
        "November ",
        "December ",
        "MEAN VALS",
        ]
    u = "Unconditional"
    c = "Conditional"
    x = "xValidation"
    cycle = range(13)
    #cycle = {0,1,2,3,4,5,6,7,8,9,10,11,'Mean'}
    ##Iterating through 0-12 is easier
    for n in ({u, c} if parmOpt else {u}):
        results[n][12] = results[n]['Mean']
        if doCrossValidation:
            results[n][x][12] = results[n][x]['Mean']
        
    print(f"\nUnconditional Statistics:")
    print(f"\nMonth\t\tRSquared\tSE\t\tFRatio\t\t{'D-Watson' if not parmOpt else 'Prop Correct'}\t{'Chow' if includeChow else ''}")
    if not parmOpt:
        for i in cycle:
            if includeChow:
                print(f"{month_name[i]}\t{results[u][i]['RSquared']:.4f}\t\t{results[u][i]['SE']:.4f}\t\t{results[u][i]['FRatio']:.2f}\t\t{results[u][i]['D-Watson']:.4f}\t\t{results[u][i]['Chow']:.4f}")
            else:
                print(f"{month_name[i]}\t{results[u][i]['RSquared']:.4f}\t\t{results[u][i]['SE']:.4f}\t\t{results[u][i]['FRatio']:.2f}\t\t{results[u][i]['D-Watson']:.4f}")
        if doCrossValidation:
            print(f"\nCross Validation Results:")
            print(f"\nMonth\t\tRSquared\tSE\t\tD-Watson\tSpearman\tBias")
            for i in cycle:
                print(f"{month_name[i]}\t{results[u][x][i]['RSquared']:.4f}\t\t{results[u][x][i]['SE']:.4f}\t\t{results[u][x][i]['D-Watson']:.4f}\t\t{results[u][x][i]['SpearmanR']:.4f}\t\t{results[u][x][i]['Bias']:.4f}")

    else:
        for i in cycle:
            if includeChow:
                print(f"{month_name[i]}\t{results[u][i]['RSquared']:.4f}\t\t{results[u][i]['SE']:.4f}\t\t{results[u][i]['FRatio']:.4f}\t\t{results[u][i]['PropCorrect']:.4f}\t\t{results[u][i]['Chow']:.4f}")
            else:
                print(f"{month_name[i]}\t{results[u][i]['RSquared']:.4f}\t\t{results[u][i]['SE']:.4f}\t\t{results[u][i]['FRatio']:.4f}\t\t{results[u][i]['PropCorrect']:.4f}")
        if doCrossValidation:
            print(f"\nCross Validation Results:")
            print(f"\nMonth\t\tRSquared\tSE\t\tProp Correct")
            for i in cycle:
                print(f"{month_name[i]}\t{results[u][x][i]['RSquared']:.4f}\t\t{results[u][x][i]['SE']:.4f}\t\t{results[u][x][i]['PropCorrect']:.4f}")
        print(f"\nConditional Statistics:")
        print(f"\nMonth\t\tRSquared\tSE\t\tFRatio\t\t{'Chow' if includeChow else ''}")
        for i in cycle:
            if includeChow:
                print(f"{month_name[i]}\t{results[c][i]['RSquared']:.4f}\t\t{results[c][i]['SE']:.4f}\t\t{results[c][i]['FRatio']:.4f}\t\t{results[c][i]['Chow']:.4f}")
            else:
                print(f"{month_name[i]}\t{results[c][i]['RSquared']:.4f}\t\t{results[c][i]['SE']:.4f}\t\t{results[c][i]['FRatio']:.4f}")
        if doCrossValidation:
            print(f"\nCross Validation (Conditional Part) Results:")
            print(f"\nMonth\t\tRSquared\tSE\t\tSpearman")
            for i in cycle:
                print(f"{month_name[i]}\t{results[c][x][i]['RSquared']:.4f}\t\t{results[c][x][i]['SE']:.4f}\t\t{results[c][x][i]['SpearmanR']:.4f}")
        
        
            
        
        #print(f"\nConditional Statistics:")
        #print(f"\nMonth\t\tRSquared\tSE\t\tFRatio\t\t{'D-Watson' if not parmOpt else 'Prop Correct'}\t{'Chow' if includeChow else 0}")

    #debugMsg(f"TotalNumbers: {totalNumbers}, Missing Days: {noOfDays2Fit - totalNumbers}")

def calibrateModel(fileList, PARfilePath, fsDate, feDate, modelType=2, parmOpt=False, autoRegression=False, includeChow=False, detrendOption=0, doCrossValidation=False, crossValFolds=2):
    """
        Core Calibrate Model Function (v0.4.1)
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
        CalibrateModel (will in the future) also reads the following from the Global Setings:
        > globalStartDate & globalEndDate -> "Standard" start / end date
        > thresh -> Event Threshold
        > globalMissingCode -> "Missing Data Identifier"
        And also reads the following from the Advanced Settings:
        > modelTrans -> Model transformation: 1-> none, 2-> 4th root, 3-> Nat log (ln), 4-> Inverse Normal, 5-> box cox
        > applyStepwise -> Stepwise Tickbox
        > optimisationChoice -> Defined in advanced settings - 0 for "Ordinary" least squares, 1 for Dual Simplex 
    """

    ##Real comments will be added later

    ##NEW in v0.2.0:
    ## Readded LastSeason & LastMonth
    ## Replaced all instances of np.array with np.ndarray
    ## Added IncreaseDate back where necessary
    ## Corrected periodWorkingOn to be within 0-11 rather than 1-12
    ## Fixed section #5.2.0 such that it now runs without crashing

    ##In v0.2.1:
    ## detrendOption correctly uses 0, 1 & 2 rather than bool
    ## Adjusted DetrendData to use detrendOption as parameter

    ## In v0.2.2:
    ## Propogate Conditional & Unconditional functions 
    
    ## In v0.3.0:
    ## Calculate Parms & Calc Parms #2 implemented
    ## calcPropCorrect & calcRSQR helper functions added
    ## new parameter "optimisationChoice" (is int, might want bool or tiny int...)
    ## new parameter includeChow (is bool)

    ## In v0.4.0:
    ## Various corrections so that the correct output is consistenty given for default parameters
    ## - (Annual, 4 Predictor files, Conditional process, no autoregression or xvalidation, any date)
    ## Corrections include adjustments to PTandRoot & FileList, calcRSQR, certain range() arrays, 
    ##  matrix resizing in propogateConditional, corrections to transformData, calcParams1 and 2, 
    ##  and finally fixing the issue regarding not all data being read in
    ## Now gives correct output (i.e. identical to the original SDSM tool)

    ## In v0.4.1
    ## Revised parameters for CalibrateModel
    ## Explicitly separated parameters read from the settings
    ## Adjusted output format

    ## In v0.5.0
    ## Finished implementation of:
    ## - Autoregression
    ## - ChowStat
    ## - Annual/Monthly/Season options
    ## - parmOpt

    ## In v0.5.1
    ## Fixed bug regarding residualArrays being calculated twice during Conditional, and never during uncond
    ## Removed PTandRoot - Will be handled externally. Assume that its been merged into the filelist

    ## In v0.6.0
    ## Finished implementation of CrossValidation

    ## In v0.6.1
    ## Added crossValFolds parameter

    ## In v0.7.0
    ## Imported Globals from settings via getSettings

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
    
    if True:
        #------------------------
        #------ SECTION #2 ------ Unknown/Initialisation?
        #------------------------
        
        #xValidationResults = np.ndarray((13, 7)).fill(globalMissingCode) ## Original array is XValidationResults(1 To 13, 1 To 7) As Double
        xValidationOutput = {"Unconditional": {}, "Conditional": {}}
        xValidMessageShown = False

        #if ApplyStepwise:
            ## Add msg
    
        lambdaArray = np.zeros((12,2)) ## Lamda array originally "LamdaArray(1 To 12, 1 To 2) As Double"

        processTerminated = False

        statsSummary = np.zeros((26,5)) ## Originally StatsSummary(1 To 26, 1 To 5) As Double

        dependMgs = False

        #-----------------
        ##CLOSE FILES HERE -> idk why, likely contingency / prep
        #-----------------

        ## Reading in data from files?
        ## FileList is the selected files from 
        loadedFiles = loadFilesIntoMemory(fileList) 

        """
                                            'Open selected files
        Open PTandRoot For Input As #1      'Predictand file
 
        Do Until FileList.ListCount = 0      'Remove any predictors from FileList just in case
            FileList.RemoveItem 0
        Loop
        predictorfileNo = 2                 'File # of predictor file starts at 2
        For subloop = 0 To File2.ListCount - 1  'Check for selected files
            If File2.Selected(subloop) Then     'If file is selected
                FileList.AddItem File2.List(subloop)    'Add to list of selected files
                Open File2.Path & "\" & File2.List(subloop) For Input As #predictorfileNo
                predictorfileNo = predictorfileNo + 1
            End If
        Next subloop
        outputFileNo = NPredictors + 2  '# for output file set
        """

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

            ##########################################
            ## What is "DoEvents"?
            ##########################################

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
            debugMsg(f"ERROR: Insufficient Data")
            exit()
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
                    detrendData(yMatrix, yMatrixAboveThreshPos, detrendOption, periodWorkingOn, False)

                savedYMatrix = deepcopy(yMatrix)

                if parmOpt:
                    ##call PropogateUnConditional
                    propogateUnconditional(yMatrix, thresh)

                if doCrossValidation:
                    ##call xValUnConditional
                    #xValUnConditional()
                    xValResults = xValidation(xMatrix, yMatrix, crossValFolds, parmOpt)
                    for i in range(12):
                        xValidationOutput["Unconditional"][i] = xValResults


                conditionalPart = False ##Needed for CalcParameters

                if applyStepwise:
                    ##call stepwise_regression(parmOpt)
                    stepWiseRegression() ##very wise #betamatrix defined here
                else:
                    ##call CalculateParameters(parmOpt)
                    params = calculateParameters(xMatrix, yMatrix, NPredictors, includeChow, conditionalPart, parmOpt, not parmOpt, residualArray)   #betamatrix defined here
                ##endif

                if processTerminated:
                    ##call mini_reset
                    do_nothing()

                yMatrix = savedYMatrix

                for i in range(12):  ## 0-11 inclusive
                    for j in range(NPredictors): ## 0-NPred inclusive
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
                        #End If
                    #Next i
                    xMatrix = np.delete(xMatrix, rejectedIndex, 0)
                    yMatrix = np.delete(yMatrix, rejectedIndex)

                    ### End of propogateConditional Code ###
                    
                    if doCrossValidation:
                        #call xvalConditional
                        #xValConditional()
                        xValResults = xValidation(xMatrix, yMatrix, crossValFolds, parmOpt, True)
                        for i in range(12):
                            xValidationOutput["Conditional"][i] = xValResults

                    #call TransformData
                    transformData(xMatrix, yMatrix, yMatrixAboveThreshPos, modelTrans)
                    ##if errored then exit

                    if detrendOption != 0:
                        ##call DetrendData
                        detrendData(yMatrix, yMatrixAboveThreshPos, detrendOption, periodWorkingOn, True)


                    if modelTrans == 5:
                        for i in range(12):
                            lamdaArray[i, 0] = lamda
                            lamdaArray[i, 1] = shiftRight

                    ##Can we move the following above, to make it an elif?
                    conditionalPart = True
                    #call CalculateParameters(true)
                    params = calculateParameters(xMatrix, yMatrix, NPredictors, includeChow, conditionalPart, parmOpt, True, residualArray) #betaMatrix defined here

                    if processTerminated:
                        ##exit
                        do_nothing()
                    if modelTrans == 4:
                        for i in range(12):
                            biasCorrection[i] = CalculateBiasCorrection()
                    
                    for i in range(12, 24):
                        for j in range(NPredictors):
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
                        yMatrixAboveThreshPos = np.ndarray((sizeOfDataArray[0]))
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
                        detrendData(yMatrix, yMatrixAboveThreshPos, detrendOption, periodWorkingOn, False)
                       
                    savedYMatrix = deepcopy(yMatrix)

                    if parmOpt:
                        ###call PropogateUnconditional
                        propogateUnconditional(yMatrix, thresh)
                    
                    conditionalPart = False
                    
                    if doCrossValidation:
                        ##call xValUnconditional
                        #xValUnConditional()
                        xValResults = xValidation(xMatrix, yMatrix, crossValFolds, parmOpt)
                        if seasonCode == 4:
                            for i in range(3):
                                xValidationOutput["Unconditional"][seasonMonths[periodWorkingOn][i]] = xValResults
                        else: #Assume monthly
                            xValidationOutput["Unconditional"][periodWorkingOn] = xValResults

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
                            for j in range(NPredictors):
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
                        for i in range(NPredictors):
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

                        rejectedIndex = []
                        for i in range(len(yMatrix)):
                            if yMatrix[i] <= thresh:
                                ## NEW AND IMPROVED RESIZE CODE HERE:
                                rejectedIndex.append(i)
                                #yMatrixAboveThreshPos
                            #End If
                        #Next i
                        xMatrix = np.delete(xMatrix, rejectedIndex, 0)
                        yMatrix = np.delete(yMatrix, rejectedIndex)

                        ### End of propogateConditional Code ###

                        if doCrossValidation:
                            #call xValConditional
                            #xValConditional()
                            xValResults = xValidation(xMatrix, yMatrix, crossValFolds, parmOpt, True)
                            if seasonCode == 4:
                                for i in range(3):
                                    xValidationOutput["Conditional"][seasonMonths[periodWorkingOn][i]] = xValResults
                            else: #Assume monthly
                                xValidationOutput["Conditional"][periodWorkingOn] = xValResults
                        
                        #call TransformData
                        transformData(xMatrix, yMatrix, yMatrixAboveThreshPos, modelTrans)
                        #if errored then exit

                        if detrendOption != 0:
                            ##call DetrendData
                            detrendData(yMatrix, yMatrixAboveThreshPos, detrendOption, periodWorkingOn, True)

                        if modelTrans == 5:
                            if seasonCode == 12:
                                lamdaArray[periodWorkingOn, 0] = lamda
                                lamdaArray[periodWorkingOn, 1] = shiftRight
                            else:
                                if periodWorkingOn == 0:
                                    lamdaArray[0, 0] = lamda
                                    lamdaArray[1, 0] = lamda
                                    lamdaArray[11, 0] = lamda
                                    lamdaArray[0, 1] = shiftRight
                                    lamdaArray[1, 1] = shiftRight
                                    lamdaArray[11, 1] = shiftRight
                                elif periodWorkingOn == 1:
                                    lamdaArray[2, 0] = lamda
                                    lamdaArray[3, 0] = lamda
                                    lamdaArray[4, 0] = lamda
                                    lamdaArray[2, 1] = shiftRight
                                    lamdaArray[3, 1] = shiftRight
                                    lamdaArray[4, 1] = shiftRight
                                elif periodWorkingOn == 2:
                                    lamdaArray[5, 0] = lamda
                                    lamdaArray[6, 0] = lamda
                                    lamdaArray[7, 0] = lamda
                                    lamdaArray[5, 1] = shiftRight
                                    lamdaArray[6, 1] = shiftRight
                                    lamdaArray[7, 1] = shiftRight
                                elif periodWorkingOn == 3:
                                    lamdaArray[8, 0] = lamda
                                    lamdaArray[9, 0] = lamda
                                    lamdaArray[10, 0] = lamda
                                    lamdaArray[8, 1] = shiftRight
                                    lamdaArray[9, 1] = shiftRight
                                    lamdaArray[10, 1] = shiftRight
                                ##endif
                            ##endif
                        ##endif
                        conditionalPart = True
                        ##call CalculateParameters(true)
                        params = calculateParameters(xMatrix, yMatrix, NPredictors, includeChow, conditionalPart, parmOpt, True, residualArray) #BetaMatrix defined here
                        if processTerminated:
                            ##exit
                            do_nothing()
                        if modelTrans == 4:
                            if seasonCode == 4:
                                for i in range(1,4): ##???
                                    biasCorrection[seasonMonths[periodWorkingOn][i]] = calculateBiasCorrection()
                                ##next i
                            else:
                                biasCorrection[periodWorkingOn] = calculateBiasCorrection()
                            ##endif
                        ##endif

                        if seasonCode == 4:
                            for i in range(3): ##???
                                for j in range(NPredictors):
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
                            for j in range(NPredictors):
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
            #----- SECTION #6.0 ----- Printing to Scream?
            #------------------------

            ##what is PARROOT FOR OUTPUT???

            ##this might be the certified export parameters moment...
            tempNPred = 0
            if detrendOption != 0:
                #print NPredictors
                tempNPRed = NPredictors
            else:
                #print -Npredictors -> what
                tempNPred = -NPredictors
            #endif
            #print seasonCode
            #print yearIndicator
            #print globalSDate
            #print nDaysR
            #print FSDate.text(?)
            #print noOfDays2Fit
            #write parmOpt
            #write modelTrans
            #print 1
            #if autoRegression: ##Less than worthless
                #print True
            #else:
                #print False
            #endif
            #for subloop in range(NPredictors): ##may remove in favour of the approach below...
                #print FileList.List(subloop) ##No clue on this one...

            #next subloop

            ##Vars "Written" to PAR file:
            PARfileOutput = {
                "NPredictors": NPredictors if detrendOption == 0 else -NPredictors,
                "SeasonCode": seasonCode,
                #"YearIndicator": yearIndicator,
                "GlobalStartDate": globalStartDate,
                "NDaysR": nDaysR,
                "FitStartDate": fsDate,
                "NoOfDays2Fit": noOfDays2Fit,
                "RainfallParameter":parmOpt,
                "ModelTrans": modelTrans,
                "1":1, ##Idk what to do with this
                "AutoRegression": autoRegression,
                #"Predictand File": "your_predictand_file.dat"
            }

            ##OUTPUTS:
            #showPARRout = True
            if debug:
                print()
                print("#####################################")
                print("########## PARFILE OUTPUTS ##########")
                print("#####################################")
                if detrendOption == 0:
                    print(f"NPredictors: {NPredictors}")
                else:
                    print(f"NPredictors: {-NPredictors} (Detrend option selected)")
                ##endif
                print(f"Season Code: {seasonCode}")
                print(f"Year Indicator: unknown") #yearIndicator
                print(f"Record Start Date: {globalStartDate}")
                print(f"Record Length: {nDaysR}")
                print(f"Fit Start Date: {fsDate}")
                print(f"No of days in fit: {noOfDays2Fit}")
                print(f"Set Rainfall Parameter: {parmOpt}")
                print(f"Model Transformation option: {modelTrans}")
                print(f"1")
                print(f"Autoregression: {autoRegression}")

                print("#####################################")
                print("########## END OF PARFILE ###########")
                print("#####################################")
                print()


            ##real change here:
            #from calendar import month_name as months

            output = {"Predictand": fileList[0]}
            for subloop in range(1, NPredictors + 1):
                output[f"Predictor#{subloop}"] = fileList[subloop]
            #for i in range(1, 13):
            #    output[months[i]] = {} # Initialize month associative array / dict
            #    output[months[i]]["RSquared"] = statsSummary[i,0]
            #    output[months[i]]["SE"] = statsSummary[i,1]
            #    output[months[i]]["FRatio"] = statsSummary[i,4]
            #    output[months[i]]["D-Watson"] = statsSummary[i,2]
            #    output[months[i]]["Chow"] = None ##Coming soon!
            u = "Unconditional"
            c = "Conditional"
            output[u] = {}
            for i in range(12):
                output[u][i] = {} # Initialize month associative array / dict
                output[u][i]["RSquared"] = statsSummary[i,0]
                output[u][i]["SE"] = statsSummary[i,1]
                output[u][i]["FRatio"] = statsSummary[i,4]
            if includeChow:
                for i in range(12):
                    output[u][i]["Chow"] = statsSummary[i, 3]
            if not parmOpt:
                for i in range(12):
                    output[u][i]["D-Watson"] = statsSummary[i,2]
            else:
                for i in range(12):
                    output[u][i]["PropCorrect"] = statsSummary[i,2]
                for i in range(12):
                    output[c] = {}
                for i in range(12):
                    output[c][i] = {} # Initialize month associative array / dict
                    output[c][i]["RSquared"] = statsSummary[i + 12,0]
                    output[c][i]["SE"] = statsSummary[i + 12,1]
                    output[c][i]["FRatio"] = statsSummary[i + 12,4]
                if includeChow:
                    for i in range(12):
                        output[c][i]["Chow"] = statsSummary[i + 12, 3]
            if doCrossValidation:
                output[u]["xValidation"] = xValidationOutput[u]
                if parmOpt:
                    output[c]["xValidation"] = xValidationOutput[c]
            ##Done with "prelim data"

            ##Mean Summaries:
            ##Loop saves cloning the summary code
            for n in ({u, c} if parmOpt else {u}):
                output[n]['Mean'] = {}
                for key in output[n][0]:
                    output[n]['Mean'][key] = 0
                    for i in range(12):
                        output[n]['Mean'][key] += output[n][i][key]
                    output[n]['Mean'][key] /= 12
                if doCrossValidation:
                    output[n]["xValidation"]['Mean'] = {}
                    for key in output[n]["xValidation"][0]:
                        output[n]["xValidation"]['Mean'][key] = 0
                        for i in range(12):
                            output[n]["xValidation"]['Mean'][key] += output[n]["xValidation"][i][key]
                        output[n]["xValidation"]['Mean'][key] /= 12

            #call PrintResults
            #print PTandRoot
            if detrendOption != 0:   ##Will need to double check and standardise this parameter
                #call PrintTrendParms
                #printTrendParms() ##???
                do_nothing()
            #call newProgressBar
            

            #------------------------
            #----- SECTION #6.1 ----- something something load calibResultsFrm
            #------------------------

            ##This section is dedicated to the absolutely horrendous layout of the OG SDSM-DC application
            ##Can safely ignore (i think) -> more useful to output the results to the parent GUI object and handle it there, better, from scratch...

            return output

def do_nothing():
    """
    Function that does nothing (it returns True)
    Used only to prevent Python warnings due to indentation errors
    when code blocks are empty
    """
    return True

##Core functions called directly from calibrateModel()

def detrendData(yMatrix: np.array, yMatrixAboveThreshPos: np.array, detrendOption: int, period: int, conditional: bool):
    """"
    Detrend Data Function v1.1
    -- May or may not work - Find out soon!
    DetrendOption: 0 = none, 1 = Linear, 2 = power function
    Requires yMatrixAboveThreshPos to be set (generally configured in TransformData)
    """



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
            xValues[i, 1] += fsDateBaseline[period]
        ##endif
    ##next i

    if detrendOption == 1: #linear regression
        tempMatrix1 = np.linalg.inv(np.matmul(xValues.transpose, xValues))
        tempMatrix2 = np.matmul(xValues.transpose, yMatrix)
        betaValues = np.matmul(tempMatrix1, tempMatrix2)
        betaTrend[period, 0] = betaValues[0] #,0]
        betaTrend[period, 1] = betaValues[1] #,0]

        for i in range(len(yMatrix)):
            yMatrix[i] -= (xValues[i,1] * betaValues[1]) #,0])
        ##next i

    elif detrendOption == 2: #Power function
        xLogged = deepcopy(xValues)
        #minY = 99999
        #for i in range(len(yMatrix)):
        #    if yMatrix[i] < minY:
        #        minY = yMatrix[i]
        ##next
        minY = np.min(yMatrix)
        if minY > 0: minY = 0
        for i in range(len(yMatrix)):
            tempYMatrix[i] = yMatrix[i] + np.abs(minY) + 0.001

        for i in range(len(yMatrix)):
            tempYMatrix[i] = np.log(tempYMatrix[i])
            xLogged[i] = np.log(xValues[i, 1])

        #tempMatrix1 = xLogged.transpose
        tempMatrix1 = np.linalg.inv(np.matmul(xLogged.transpose, xLogged))
        tempMatrix2 = np.matmul(xLogged.transpose, tempYMatrix)
        betaValues = np.matmul(tempMatrix1, tempMatrix2)
        betaValues[0] = np.exp(betaValues[0]) #,0] = np.exp(betaBalues(0,0))
        betaTrend[period, 0] = betaValues[0]
        betaTrend[period, 1] = betaValues[1]
        betaTrend[period, 2] = minY

        for i in range(len(yMatrix)):
            yMatrix[i] -= (betaValues[0,0] * (xValues[i, 1] ** betaValues[1,0])) - np.abs(minY) - 0.001
        
    else:
        debugMsg("Error: Invalid Detrend Option")

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

def xValUnConditional():
    """
    Cross Validation: Unconditional
    -- Currently a placeholder
    ----> Coming Soon
    """
def xValConditional():
    """
    Cross Validation: Conditional
    -- Currently a placeholder
    -- VERY similar functionality to xValUncond
    ----> Might merge code if possible
    ----> Coming Soon
    """

def xValidation(xMatrix: np.ndarray, yMatrix: np.ndarray, noOfFolds, parmOpt, conditionalPart=False):
    """
    Cross Validation - Combined Function
    Currently has a minor issue in Section #1, leading to innacuracy after 3dp for all values
    - Error may be larger for more data
    """

    ### GOLBALS ###
    xValidMessageShown = False
    thresh = _globalSettings['thresh'] #--> Import later...
    globalMissingCode = _globalSettings['globalmissingcode']
    ### ####### ###  

    #------------------------
    #------ SECTION #1 ------ Modelled Matrix generation
    #------------------------

    blockSize = len(yMatrix) // noOfFolds           #'calculate the size of a block (this is rounded down so 428/5 = 85 block size. 85x5=425 so 3 values lost at end)
    maxEnd = noOfFolds * blockSize - 1          #'index of max value - make sure we don't go over this (eg 424 for example above: lose values 425,426,427)
    modMatrix = np.zeros((maxEnd + 1))
    #Set ModelledMatrix = New Matrix
    #modelledMatrix.Size (maxEnd + 1), 1         #'stores untransformed modelled values to compare with YMatrix observed values
    
    if blockSize < 10:
        #Error: not enough data
        exit()
    #End If

    for foldOn in range(noOfFolds):      #'loop through creating appropriate blocks for each block based on other excluded blocks to determine parameters using OLS
        blockStart = (foldOn) * blockSize            #'work out INDEX of block start and end (index starts at zero)
        blockEnd = blockStart + blockSize - 1           #'INDEX of block end eg 0-84,85-169,170-254 etc
        tempXMatrix = np.zeros((maxEnd - blockSize + 1, xMatrix.shape[1]))
        tempYMatrix = np.zeros((maxEnd - blockSize + 1))
        rowCount = 0
        for j in range(maxEnd + 1):                       #'now set up temporary x and y arrays with all data except excluded fold
            if (j < blockStart) or (j > blockEnd):
                rowCount = rowCount + 1
                for k in range(xMatrix.shape[1]):
                    tempXMatrix[rowCount - 1, k] = xMatrix[j, k]
                #Next k
                tempYMatrix[rowCount - 1] = yMatrix[j]
            #End If
        #Next j
        #'tempXMatrix and tempYMatrix now have all data except excluded fold.
        
        if conditionalPart: ##IF we be doin conditional crossvalidation, we need to transform the data first
            ##fn TransformDataForXValidation()
            if len(tempYMatrix) < 10:           #make sure we still have enough data after transformation
                if not (xValidMessageShown):
                    xValidMessageShown = True       #'make sure message only shows once
                    #MsgBox "Sorry - insufficient data for all cross validation metrics to be calculated.", 0 + vbCritical, "Error Message"
                #End If
                exit() #Exit Sub                         'make sure we have enough data to work with
        #End If

        ##Generate Beta Matrix

        xTransY = np.matmul(tempXMatrix.transpose(), tempYMatrix)
        xTransXInv = np.linalg.inv(np.matmul(tempXMatrix.transpose(), tempXMatrix))
        xBetaMatrix = np.matmul(xTransXInv, xTransY)
        
        #                 'now cycle through calculating modelled y (transformed value) for excluded block

        for j in range(blockStart, blockEnd +1): #PC: Do we need +1 here?
            for k in range(xMatrix.shape[1]):               #'calculate values
                modMatrix[j] += (xBetaMatrix[k] * xMatrix[j][k])
            #Next k
        #Next j7

        if conditionalPart & parmOpt:
            pass
            # unTransformDataInXVal(blockStart, blockEnd)
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

    output = {}
    
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
            residualMatrix = np.zeros((maxEnd + 1))
            for i in range(maxEnd + 1):
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
            for i in range(maxEnd + 1):
                if yMatrix[i] == 0 and modMatrix[i] < 0.5:
                    correctCount += 1
                elif yMatrix[i] == 1 and modMatrix[i] >= 0.5:
                    correctCount += 1
            propCorrect = correctCount / len(yMatrix)
            output["PropCorrect"] = propCorrect
            #Consider switching to the calcPropCorrect function later...
        #else #Conditional Part does not have any extra features

    elif not conditionalPart: ##Unconditional part is happy to provide missing values
        output["SE"] = globalMissingCode
        output["RSquared"] = globalMissingCode
        if parmOpt:
            output["PropCorrect"] = globalMissingCode
        else:
            output["D-Watson"] = globalMissingCode
            output["Bias"] = globalMissingCode
    else: #Lo Data, Crash now...
        print("Error: Not enough data for the conditional part of xValidation")
        exit()

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

def stepWiseRegression(xMatrix: np.ndarray, yMatrix: np.ndarray, NPredictors: int, includeChow: bool, conditionalPart: bool, parmOpt: bool, propResiduals:bool, residualArray:np.ndarray):
    """
    Stepwise Regression function
    -- Currently a placeholder
    """

    aicWanted = False
    jMatrix = np.ones((len(yMatrix, len(yMatrix))))

    determinePermutations(NPredictors)

    for i in range(totalPerms):
        ##Update ProgressBar

        ##DoEvents

        noOfCols = 1
        for j in range(9):
            if permArray[i, j] > 0:
                noOfCols += 1
            #endif
        #next j

        newXMatrix = np.ones((len(yMatrix), noOfCols))
        for j in range(1, noOfCols - 1):
            for k in range(len(yMatrix) - 1):
                newXMatrix[k, j] = xMatrix[k, permArray[i, j]]
            #next k
        #next j

        results = calculateParameters2(newXMatrix, newYMatrix, optimisatinonChoice, NPredictors)

        #if not terminated

        SSR = np.matmul(results["betaMatrix"].transpose(), np.matmul(newXMatrix.transpose(), newYMatrix))[0,0]
        SSRMinus = np.matmul(newYMatrix.transpose(), np.matmul(jMatrix, newYMatrix))[0,0]
        RMSE = np.sqrt(SSR / len(newYMatrix))
        if aicWanted:
            PermErrors[i] = (newXMatrix.shape[0] * np.log(RMSE)) + ((newXMatrix.shape[1] - 1) * 2)
        else:
            PermErrors[i] = (newXMatrix.shape[0] * np.log(RMSE)) + ((newXMatrix.shape[1] - 1) * np.log(newXMatrix.shape[0]))

        ##Stop using newXMatrix now

        maxError = -99999
        maxLocation = 1
        for i in range(totalPerms):
            pass
        

def determinePermutations(numbers):
    """
    Returns totalPerms, permArray, and Numbers?
    """
    permArray = np.zeros((500, 9))
    totalPerms = numbers #0
    for i in range(numbers):
        #totalPerms += 1
        permArray[i, 0] = i
    #next i
    if numbers > 1:
        totalPerms += 1
        for i in range(numbers):
            permArray[totalPerms, i] = i #seems like a fair bit of redundancy imo
        #next i
    #endif
    
    ##The following looks like loop hell
    ##Must be a more efficient way of doing things
    ##Also, how is this not going to overflow
    if numbers > 2:
        for i in range(1, numbers - 1):
            generateIfromN(i, numbers, "")

    return {
        "TotalPerms": totalPerms,
        "permArray": permArray
        }

def generateIfromN(sizeToPermute, numbers, appendString, totalPerms, permArray):
    """
    Curious Description
    Genuinely not sure what this is supposed to do...
    """
    #what the fuck
    valueString = ""
    if sizeToPermute == numbers:
        for i in range(numbers):
            valueString += str(i+1) ## Trying to stay true to the original code
        #next i
        valueString += appendString.strip()
        totalPerms += 1
        for i in range(len(valueString)):
            permArray[totalPerms, i] = int(valueString[i])
        #next i
    elif sizeToPermute == 1:
        for i in range(numbers):
            totalPerms += 1
            valueString = (str(i) + appendString).strip()
            for j in range(len(valueString)):
                permArray[totalPerms, j] = int(valueString[j])
            #next j
        #next i
    elif sizeToPermute > 1:
        generateIfromN(sizeToPermute, numbers - 1, appendString, totalPerms, permArray)
        valueString = (str(numbers) + appendString)
        generateIfromN(sizeToPermute - 1, numbers - 1, valueString, totalPerms, permArray)
    #endif




def calculateParameters(xMatrix: np.ndarray, yMatrix: np.ndarray, NPredictors: int, includeChow: bool, conditionalPart: bool, parmOpt: bool, propResiduals:bool, residualArray:np.ndarray):
    """
    Calculate Parameters function v1.1
    -- Presumably calculates parameters
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
    modMatrix2Test = np.ndarray((len(yMatrix)))

    for i in range(len(yMatrix)):
        modMatrix2Test[i] = 0
        for j in range(xMatrix.shape[1]):
            modMatrix2Test[i] += betaMatrix[j] * xMatrix[i, j]
        #next j
    #next i

    if parmOpt:
        if conditionalPart:
            ##call untransformdata
            ##Useful when processing Transformed Data
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

def transformData(xMatrix: np.ndarray, yMatrix: np.array, yMatrixAboveThreshPos: np.array, modelTrans):
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
    if modelTrans == 2 or modelTrans == 3: #4th Root or Log selected
        missing = 0
        for i in range(len(yMatrix)):
            #[arr[1] for arr in masterarr if cond = ???]
            ##max(values, key=len)
            if yMatrix[i] >= 0:
                if modelTrans == 2:
                    yMatrix[i] = yMatrix[i] ^ 0.25
                else:
                    yMatrix[i] = np.log(yMatrix[i])
            else:
                yMatrix[i] = globalMissingCode #-> Global var that needs importing
                yMatrixAboveThreshPos[i] = globalMissingCode   #     'this resords position of y values for detrend option - needs reducing too
                missing += 1
        #next i
        
        if missing > 0:  #Remove missing valus
            ##NB - Will be much easier to clone yMat and xMat and delete records,
            ##     rather than this "selective copying"
            if len(yMatrix) - missing > 10:   #'make sure there are enough data
                newYMatrix = np.ndarray((len(yMatrix) - missing))
                newXMatrix = np.ndarray((xMatrix.shape[0] - missing, xMatrix.shape[1]))
                newYMatrixAbove = np.ndarray((len(yMatrixAboveThreshPos) - missing))
                count = 0
                for i in range(len(yMatrix)): ##Drop unwanted arrayz
                    if yMatrix[i] != globalMissingCode:
                        newYMatrix[count] = yMatrix[i]
                        newYMatrixAbove[count] = yMatrixAboveThreshPos[i]
                        for j in range(len(xMatrix[0])): #XCols
                            newXMatrix[count, j] = xMatrix[i, j]
                        #Next j
                        count += 1

                    #End If
                #Next i              'newXMatrix and newYMatrix and newYMatrixAbove now have good data in them
                yMatrix = deepcopy(newYMatrix)
                xMatrix = deepcopy(newXMatrix)
                yMatrixAboveThreshPos = deepcopy(newYMatrixAbove)
        #End If
        
    elif modelTrans == 5: #          'box cox - so need to find best lamda of YMatrix
        #x = PeriodWorkingOn         'for testing!
        #minSoFar = 9999                 #'establish right shift for box cox transform as min value in y matrix if -ve.  Makes all values +ve
        #for i in range(1,len(yMatrix)):
        #    if yMatrix[i] < minSoFar:
        #        minSoFar = yMatrix[i]
        #Next i
        minSoFar = np.min(yMatrix)
        if minSoFar >= 0: 
            ShiftRight = 0
        else:
            ShiftRight = np.abs(minSoFar)

        for i in range(1, len(yMatrix)):              #'now shift all Y matrix data right to make sure it's +ve before we calculate lamda
            yMatrix[i] += ShiftRight
        #Next i

        ################
        ## Lamda Calc ##
        ################

        insufficientData = False    #'assume enough data unless FindMinLamda tells us otherwise
        lamda = findMinLamda(-2, 2, 0.25, yMatrix)  #'find a value between -2 to +2

        if lamda != globalMissingCode: #  'now home in a bit more
            lamda = findMinLamda((lamda - 0.25), (lamda + 0.25), 0.1, yMatrix)
        else:
            message = "Sorry an error has occurred calculating the optimum lamda transform."
            if insufficientData: message = message & " There are insufficient data for a Box Cox transformation.  Try an alternative transformation."
            #MsgBox message, 0 + vbCritical, "Error Message"
            #insert error here
        #End If
        if lamda != globalMissingCode: #'home in a bit further
            lamda = findMinLamda((lamda - 0.1), (lamda + 0.1), 0.01, yMatrix)
        else:
            message = "Sorry an error has occurred calculating the optimum lamda transform."
            if insufficientData: message = message & " There are insufficient data for a Box Cox transformation.  Try an alternative transformation."
            #MsgBox message, 0 + vbCritical, "Error Message"
            #insert error here
        #End If

        if lamda == globalMissingCode:
            message = "Sorry an error has occurred calculating the optimum lamda transform."
            if insufficientData: message = message & " There are insufficient data for a Box Cox transformation.  Try an alternative transformation."
            #MsgBox message, 0 + vbCritical, "Error Message"
            #insert error here
        #End If

        #######################
        ## End of Find Lamda ##
        #######################

        for i in range(len(yMatrix)):
            if lamda == 0:                          # 'apply box cox lamda transform - do some checks for division by zero first
                if yMatrix[i] != 0:
                    yMatrix[i] = np.log(yMatrix[i]) - ShiftRight         #'shift it back to left after transform
                else:
                    yMatrix[i] = -5 - ShiftRight     #'cannot log zero so -5 represents log of a very small number
                #End If
            else:
                yMatrix[i] = (((yMatrix[i] ^ lamda) - 1) / lamda) - ShiftRight     #'shift it back to left after transform
            #End If
        #Next i

    else:        #'Inverse normal selected: model trans=4

        def fxNormal(fx):
            return np.exp(-(fx ** 2) / 2) / np.sqrt(2 * np.pi)

        
        rankMatrix = np.zeros((2, len(yMatrix))) #'add an extra column     ##In this era, for the sake of storage, these matricies are stored horizontally. Mechanically adding another row..
        rankMatrix[0] = deepcopy(yMatrix)      #'copy Y matrix into RankMatrix
        #Set ReSampleMatrix = New Matrix         'save these data in global matrix so can be resampled when untransforming
        #Set ReSampleMatrix = YMatrix.Clone
        reSampleMatrix = deepcopy(yMatrix)

        for i in range(len(rankMatrix)):        #'set column two to a running count
            rankMatrix[1, i] = i + 1
        #Next i
        
        rankMatrix.sort(0)              #'sort ascending on first column ie. on data column
        
        #            'Locate lower bound to begin estimation of cdf
        #            'cdf is computed as r/(n+1) where r is the rank and n is sample size
        zStart = 1 / (len(rankMatrix) + 1)
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
        rankMatrix[0, 0] = limit
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
                area = area + (delta * 0.5 * (fxOld + fxNew))
                fxOld = fxNew
                if area >= cp:
                    rankMatrix[0, i] = fx
                j += 1
            #Wend
        #Next i
        
        rankMatrix.sort(1)       #'sort back into temporal sequence and copy data back to YMatrix
        yMatrix = deepcopy(rankMatrix[0])
        #For i = 1 To RankMatrix.Rows
        #    YMatrix(i - 1, 0) = RankMatrix(i - 1, 0)
        #Next i

    #End If
    
    #return Something here



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
##