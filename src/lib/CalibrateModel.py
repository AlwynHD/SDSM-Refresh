import numpy as np
from datetime import date as realdate
from src.lib.utils import loadFilesIntoMemory, increaseDate, thirtyDate
from copy import deepcopy
import src.core.data_settings

## NOTE TO READERS: THIS FILE **DOES NOT** WORK
## It does if you run the debugRun test configuration

##DEBUGGING FUNCTIONS:
debug = True
def debugMsg(msg):
    if debug == True:
        print(msg)

#GLOBALS:
thirtydate = False
if not thirtydate:
    def date(y: int, m: int, d: int):
        return realdate(y, m, d)
else:
    def date(y: int, m: int, d: int):
        return thirtyDate(y, m, d)
#else:

## Bewrae of Matricies being incorrectly "orientated"

def debugRun():
    #xmat = np.zeros((5,5))
    #for i in range(5):
    #    xmat[i,i] = 1
    #ymat = np.zeros((5))

    #calculateParameters2(xmat, ymat, 0, 5)
    calibrateModelDefaultExperience()

def calibrateModelDefaultExperience():
    """
    CALIBRATE MODEL TESTING FUNCTION
    Also gives an idea of what to expect using it
    """

    ## Parameters
    #fsDate = deepcopy(globalStartDate)
    fsDate = date(1948, 1, 1)
    #feDate = deepcopy(globalEndDate)
    feDate = date(1965, 1, 10)
    modelType = 1 #0
    parmOpt = False  ## Whether Conditional or Unconditional. True = Cond, False = Uncond. 
    ##ParmOpt(1) = Uncond = False
    ##ParmOpt(0) = Cond = True
    autoRegression = False ## Replaces AutoRegressionCheck
    includeChow = False
    detrendOption = 0 #0, 1 or 2...
    xValidation = False

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
    ] #note - ncep_prec.dat is absent - nice round number of 30
    for i in range(len(fileList)):
        fileList[i] = "predictor files/ncep_" + fileList[i] + ".dat"
    PARfilePath = "JOHN_PARFILE.PAR"
    ## Predictor files should be in the format [path/to/predictor/file.dat]
    ## Files usually begin with ncep_
    results = calibrateModel(PTandRoot, fileList, PARfilePath, fsDate, feDate, modelType, parmOpt, autoRegression, includeChow, detrendOption, xValidation)

    ## Output for similar results to the OG software:
    print(f"FINAL RESULTS (Assumes Default):")
    debugMsg(f"Debug data:")
    debugMsg(f"Fit Start Date: {fsDate}")
    debugMsg(f"Fit End Date: {feDate}")
    #print(f"Predictand: {PTandRoot}")
    print(f"\nPredictors:\n")
    for i in fileList:
        print(i)
            
    print(f"\nUnconditional Statistics:")
    print(f"\nMonth\t\tRSquared\tSE\t\tFRatio\t\tD-Watson")

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
        ]
    for i in range(12):
        print(f"{month_name[i]}\t{results[i]['RSquared']:.4f}\t\t{results[i]['SE']:.4f}\t\t{results[i]['FRatio']:.2f}\t\t{results[i]['D-Watson']:.4f}\t")
    #debugMsg(f"TotalNumbers: {totalNumbers}, Missing Days: {noOfDays2Fit - totalNumbers}")

def calibrateModel(PTandRoot, fileList, PARfilePath, fsDate, feDate, modelType=2, parmOpt=False, autoRegression=False, includeChow=False, detrendOption=0, xValidation=False):
    """
        Core Calibrate Model Function (v0.4.1)
        PTandRoot -> Predictand file path
        fileList -> Array of predictor file paths
        fsDate -> Fit start date (currently accepts Date object, may adjust to accept string)
        feDate -> Fit end date
        modelType -> Monthly/Seasonal/Annual (0/1/2), can change easily according to the will of the GUI Developer Gods
        parmOpt -> Conditional / Unconditional model, True / False respectively
        autoRegression -> Autoregression tickbox
        includeChow -> Chow Test Tickbox
        detrendOption -> Detrend Options: 0-> None, 1-> Linear, 2-> Power function.
        xValidation -> Cross Validation Tickbox
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

    #------------------------
    # FUNCTION DEFINITITIONS:
    #------------------------

    ## Globals: import from settings
    GlobalMissingCode = -999
    globalStartDate = date(1948, 1, 1) #date(2004, 8, 5)
    globalEndDate = date(2017, 12, 31) #date(1961, 1, 10) #date(2017, 12, 31)#date(2025, 1, 7)
    thresh = 0 ## ??? - Need to import from another file. Event thresh is 0 by default...
    ## Import from "Advanced Settings"
    modelTrans = 1 ## Model transformation; 1=none, 2=4root, 3=ln, 4=Inv Normal, 5=box cox
    applyStepwise = False
    optimisationChoice = 1 ## 0 caused errror -> double check
    ## Location Unknown:
    countLeapYear = True
    ## End of Settings Imports (Default Values for now)

    NPredictors = len(fileList)
    debugMsg(fileList)
    ## NOTE: FOR OPTIMAL PERFORMANCE, MERGE PTandRoot with fileList:
    fileList.insert(0, PTandRoot)
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
        
        xValidationResults = np.ndarray((13, 7)).fill(GlobalMissingCode) ## Original array is XValidationResults(1 To 13, 1 To 7) As Double
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
                #if tempReadin[i] == GlobalMissingCode: startFound = False
                if loadedFiles[i][searchPos] == GlobalMissingCode: 
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
                #if tempReadin[j] == GlobalMissingCode: anyMissing = True
                if loadedFiles[i][searchPos] == GlobalMissingCode:
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
                        yMatrix[i] = dataReadIn(0, 0, i + 1)
                        #xMatrix[i, 0] = 1#
                        xMatrix[i, 0] = loadedFiles[0]
                        for j in range(NPredictors):
                            xMatrix[i, j] = dataReadIn[0, j+1, i]
                        ##next
                        if parmOpt:
                            if dataReadIn[0, 0, i] > thresh:
                                xMatrix[i, NPredictors] = 1
                            else:
                                xMatrix[i, NPredictors] = 0
                            ##endif
                        else:
                            xMatrix[i, NPredictors] = dataReadIn[0, 0, i-1]
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

                if xValidation:
                    ##call xValUnConditional
                    xValUnConditional()

                conditionalPart = False ##Needed for CalcParameters

                if applyStepwise:
                    ##call stepwise_regression(parmOpt)
                    stepWiseRegression() ##very wise #betamatrix defined here
                else:
                    ##call CalculateParameters(parmOpt)
                    params = calculateParameters(xMatrix, yMatrix, optimisationChoice, NPredictors, includeChow, conditionalPart, parmOpt, parmOpt, residualArray)   #betamatrix defined here
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
                        xMatrixClone = deepcopy(xMatrix)
                        #xmatrix size
                        #for loop
                        #extra for loop
                        #somethign else...
                    ##endif

                    #call PropogateConditional
                    propogateConditional(xMatrix, yMatrix, yMatrixAboveThreshPos, thresh, NPredictor) 

                    if xValidation:
                        #call xvalConditional
                        xValConditional()

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
                    params = calculateParameters(xMatrix, yMatrix, optimisationChoice, NPredictors, includeChow, conditionalPart, parmOpt, True, residualArray) #betaMatrix defined here

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

                    DWNumerator = 0
                    DWDenom = 0
                    ##Need to properly calc residualMatrixRows
                    residualMatrix = params["residualMatrix"]
                    for i in range(1, len(residualMatrix)):
                        DWNumerator += (residualMatrix[i] - residualMatrix[i - 1]) ** 2
                    ##next
                    for i in range(len(residualMatrix)):
                        DWDenom += residualMatrix[i] ** 2
                    ##next
                    if DWDenom > 0:
                        for i in range(12):
                            statsSummary[i, 2] = DWNumerator / DWDenom
                        ##next
                    else:
                        for i in range(12):
                            statsSummary[i, 2] = GlobalMissingCode
                        ##next
                    ##endif

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
                        xMatrix = np.zeros((binsTotal + 1, NPredictors))
                        yMatrix = np.zeros((binsTotal + 1))

                        tempCounter = 0
                        progressThroughData = 1
                        for i in range(noOfSections[periodWorkingOn]):
                            if sectionSizes[periodWorkingOn, i] > 1:
                                for j in range(sectionSizes[periodWorkingOn, i] - 1):
                                    yMatrix[tempCounter] = dataReadIn[periodWorkingOn, 0, i]
                                    for subloop in range(NPredictors - 1):
                                        xMatrix[tempCounter, subloop] = dataReadIn[periodWorkingOn, subloop, j+progressThroughData]
                                    ##next (subloop)
                                    ##xmatrix[tempCounter, 0] = 1#
                                    xMatrix[tempCounter, 0] = 1 #loadedFiles[0] - Whoops, actually just a 1
                                    if parmOpt:
                                        if dataReadIn[periodWorkingOn, 0, j + progressThroughData - 1] > thresh:
                                            xMatrix[tempCounter, NPredictors - 1] = 1
                                        else:
                                            xMatrix[tempCounter, NPredictors - 1] = 0
                                        ##endif
                                    else:
                                        xMatrix[tempCounter, NPredictors - 1] = dataReadIn[periodWorkingOn, 0, j+progressThroughData - 1]
                                    ##endif
                                    tempCounter += 1
                                ##next j
                            ##endif
                            progressThroughData += sectionSizes[periodWorkingOn, i]
                        ##next i
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
                    
                    if xValidation:
                        ##call xValUnconditional
                        xValUnConditional()

                    conditionalPart = False

                    ###until now, #6.2.1 is near identical to #6.1.1,
                    ###but is notably missing the ApplyStepwise condition for CalcualteParameters

                    ##call CalculateParameters(parmOpt) ##Adjust to make sure its correct...?
                    params = calculateParameters(xMatrix, yMatrix, optimisationChoice, NPredictors, includeChow, conditionalPart, parmOpt, parmOpt, residualArray)     #betaMatrix Defined Here

                    if processTerminated:
                        ##call mini_reset
                        do_nothing()

                    yMatrix = savedYMatrix

                    if seasonCode == 4:
                        for i in range(3):
                            for j in range(NPredictors):
                                debugMsg(f"periodW: {periodWorkingOn}, i: {i}, j: {j}")
                                debugMsg(f"seasonMonths: {seasonMonths[periodWorkingOn][i]}")
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
                            #xmatrix size
                            #for loop
                            #extra for loop
                            #somethign else...
                        ##endif

                        #call PropogateConditional
                        propogateConditional(xMatrix, yMatrix, yMatrixAboveThreshPos, thresh, NPredictor) 

                        if xValidation:
                            #call xValConditional
                            xValConditional()
                        
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
                        params = calculateParameters(xMatrix, yMatrix, optimisationChoice, NPredictors, includeChow, conditionalPart, parmOpt, True, residualArray) #BetaMatrix defined here
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

            output = {"Predictand": PTandRoot}
            for subloop in range(NPredictors):
                output[f"Predictor#{subloop}"] = fileList[subloop]
            #for i in range(1, 13):
            #    output[months[i]] = {} # Initialize month associative array / dict
            #    output[months[i]]["RSquared"] = statsSummary[i,0]
            #    output[months[i]]["SE"] = statsSummary[i,1]
            #    output[months[i]]["FRatio"] = statsSummary[i,4]
            #    output[months[i]]["D-Watson"] = statsSummary[i,2]
            #    output[months[i]]["Chow"] = None ##Coming soon!
            for i in range(12):
                output[i] = {} # Initialize month associative array / dict
                output[i]["RSquared"] = statsSummary[i,0]
                output[i]["SE"] = statsSummary[i,1]
                output[i]["FRatio"] = statsSummary[i,4]
                output[i]["D-Watson"] = statsSummary[i,2]
                output[i]["Chow"] = None ##Coming soon!

            ##Done with "prelim data"
            
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

    np.delete(xMatrix, rejectedIndex, 0)
    np.delete(yMatrix, rejectedIndex)

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

def stepWiseRegression():
    """
    Stepwise Regression function
    -- Currently a placeholder
    """

def calculateParameters(xMatrix: np.ndarray, yMatrix: np.ndarray, optimisationChoice: int, NPredictors: int, includeChow: bool, conditionalPart: bool, parmOpt: bool, propResiduals:bool, residualArray:np.ndarray):
    """
    Calculate Parameters function v1.1
    -- Presumably calculates parameters
    """
     ### GLOBALS ###
    GlobalMissingCode = -999
    ### ####### ###

    #local vars
    chowStat = 0
    condPropCorrect = None

    #requireUntransform = True #ConditionalPart And ParmOpt(0).value

    if includeChow:
        #CalcParams does not modify xMatrix or yMatrix
        xtemp = xMatrix #deepcopy(xMatrix)
        ytemp = yMatrix #deepcopy(yMatrix)
        firstHalf = np.round(xMatrix.shape[0] / 2) ##Should use the same rounding algorithm as original software
        #secondHalf = xMatrix.shape[0] - firstHalf ##Might be unnecesary
        isValid = (xMatrix.shape[0] // 2) > 10

        if (isValid): #Do we have enough data? Are both halves >10?
            ##Cool python hackz

            results = calculateParameters2(xtemp[:firstHalf], ytemp[:firstHalf], optimisationChoice, NPredictors) #ignore error
            RSS1 = results["RSS"]

            results = calculateParameters2(xtemp[firstHalf:], ytemp[firstHalf:], optimisatioChoice, NPredictors) #ignore error
            RSS2 = results["RSS"]
        #endif
    #endif

    results = calculateParameters2(xMatrix, yMatrix, optimisationChoice, NPredictors)
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
            pass
        else: #i.e. Not conditionalPart
            condPropCorrect = calcPropCorrect(modMatrix2Test, yMatrix2Test, len(yMatrix2Test))
    #endif

    #Quick SError?
    if len(yMatrix) < 2:
        SE = GlobalMissingCode
    else:
        SE = np.sqrt(RSSAll / (len(yMatrix) - 1)) ##SQRT?
        SE = max(SE, 0.0001)
    #endif

    rsqr = calcRSQR(modMatrix2Test, yMatrix2Test, len(yMatrix2Test), True, (len(yMatrix2Test) - 2))
    ## Aka RSquared

    if propResiduals:
        for i in range(len(results["residualMatrix"])):
            nOfR = residualArray["noOfResiduals"]
            debugMsg(f"i + nOfR: {i} + {nOfR} ({i + nOfR}) < len(residualArray): {len(residualArray['predicted'])}")
            debugMsg(f"i: {i} < len(resultsPredicted): {len(results['predictedMatrix'])}")
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

def calculateParameters2(xMatrix: np.ndarray, yMatrix: np.ndarray, optimisationChoice: int, NPredictors: int):
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
    GlobalMissingCode = -999
    dependMsg = True #No idea where this is supposed to be defined...
    ### ####### ###

    yBar = np.sum(yMatrix) / len(yMatrix)

    if optimisationChoice == 1:
        debugMsg("Oridanry LeastSquares")
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
        meanY = GlobalMissingCode

    RSS = 0
    for i in range(xMatrix.shape[0]):
        modelled = 0
        for j in range(xMatrix.shape[1]):
            modelled += betaMatrix[j] * xMatrix[i, j]
        #next j
        RSS += (modelled - yMatrix[i]) ** 2
    #next i
    RSS = max(RSS, 0.0001)
    
    if meanY != GlobalMissingCode:
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
        fRatio = GlobalMissingCode
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
    GlobalMissingCode = -999
    #yMatrixAboveThreshPos = np.array()
    #xMatrix = np.ndarray()
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
                yMatrix[i] = GlobalMissingCode #-> Global var that needs importing
                yMatrixAboveThreshPos[i] = GlobalMissingCode   #     'this resords position of y values for detrend option - needs reducing too
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
                    if yMatrix[i] != GlobalMissingCode:
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

        if lamda != GlobalMissingCode: #  'now home in a bit more
            lamda = findMinLamda((lamda - 0.25), (lamda + 0.25), 0.1, yMatrix)
        else:
            message = "Sorry an error has occurred calculating the optimum lamda transform."
            if insufficientData: message = message & " There are insufficient data for a Box Cox transformation.  Try an alternative transformation."
            #MsgBox message, 0 + vbCritical, "Error Message"
            #insert error here
        #End If
        if lamda != GlobalMissingCode: #'home in a bit further
            lamda = findMinLamda((lamda - 0.1), (lamda + 0.1), 0.01, yMatrix)
        else:
            message = "Sorry an error has occurred calculating the optimum lamda transform."
            if insufficientData: message = message & " There are insufficient data for a Box Cox transformation.  Try an alternative transformation."
            #MsgBox message, 0 + vbCritical, "Error Message"
            #insert error here
        #End If

        if lamda == GlobalMissingCode:
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
            debugMsg("Loop3")
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
                debugMsg("Loop4")
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
    GlobalMissingCode = -999
    ### ####### ###

    if missingLim == None:
        missingLim = limit

    sumX = sumY = sumXX = sumYY = sumXY = missing = 0

    for i in range(limit):
        if (modMatrix[i] != GlobalMissingCode and yMatrix[i] != GlobalMissingCode) or checkMissing == False:
            sumX += modMatrix[i]
            sumY += yMatrix[i]
            sumXX += modMatrix[i] ** 2
            sumYY += yMatrix[i] ** 2
            sumXY += modMatrix[i] * yMatrix[i]
        else:
            missing += 1
    ##end for

    rsqr = GlobalMissingCode
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
            rsqr = GlobalMissingCode
        else:
            rsqr = GlobalMissingCode

    debugMsg(f"calcRSQR: {rsqr}, only if {missing} < {missingLim}")
    
    return rsqr

def calcPropCorrect(modMatrix: np.ndarray, yMatrix: np.ndarray, limit: int):
    """
    Proportion Correct Shared code for xValidation:Unconditional (parmOpt=F) & Calculate Params #1
    """

    GlobalMissingCode = -999

    correctCount = 0
    missing = 0
    for i in range(limit):
        if (modMatrix != GlobalMissingCode and yMatrix != GlobalMissingCode):
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
        propCorrect = GlobalMissingCode
    
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