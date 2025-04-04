import numpy as np
from datetime import date
from src.lib.utils import loadFilesIntoMemory, increaseDate
from copy import deepcopy

## NOTE TO READERS: THIS FILE **DOES NOT** WORK

def calibrateModel(applyStepwise, modelType, detrendOption, parmOpt, autoRegression):
    """
        Core Calibrate Model Function (v0.1.1)
        applyStepwise -> Stepwise Tickbox
        modelType -> Monthly/Seasonal/Annual (0/1/2), can change easily according to the will of the GUI Developer Gods
        detrendOption -> Detrend Options. 0-> None, 1/2 -> Options. Code currently (falsely) assumes boolean input
        parmOpt -> Conditional / Unconditional model, True / False respectively
        autoRegression -> Autoregression tickbox
        ----------------------------------------
        More parameters coming soon!
    """

    ##Real comments will be added later

    ##NEW in v0.2.0:
    ## Readded LastSeason & LastMonth
    ## Replaced all instances of np.array with np.ndarray
    ## Added IncreaseDate back where necessary
    ## Corrected periodWorkingOn to be within 0-11 rather than 1-12
    ## Fixed section #5.2.0 such that it now runs without crashing

    #------------------------
    # FUNCTION DEFINITITIONS:
    #------------------------

    ## Globals:
    GlobalMissingCode = 999
    NPredictors = 12

    ## (Temp) Parameters
    ApplyStepwise = True
    modelType = 0
    globalStartDate = date(2004, 8, 5)
    globalEndDate = date(2025, 1, 7)
    fsDate = date(2005, 1, 8)
    feDate = deepcopy(globalEndDate)
    detrendOption = False #True
    parmOpt = True  ## Whether Conditional or Unconditional. True = Cond, False = Uncond. 
    ##ParmOpt(1) = Uncond = False
    ##ParmOpt(0) = Cond = True
    autoRegression = True ## Replaces AutoRegressionCheck
    xValidation = True
    PTandRoot = ["predictand files/NoviSadPrecOBS.dat"] ##Predictand file
    #fileList = ["Chumbus", "Glaucose", "Jhomcy"]
    fileList = [
        "temp", "mslp", "p500", "p850", "rhum", 
        "r500", "r850", "p__f", "p__z", 
        "p__v", "p__u", "p_th", "p_zh", "p5_f", 
        "p5_z", "p5_v", "p5_u", "p5th", "p5zh", 
        "p8_f", "p8_z", "p8_v", "p8_u","p8th", 
        "p8zh", "shum", "dswr", 
        "lftx", "pottmp", "pr_wtr",
    ]
    for i in range(len(fileList)):
        fileList[i] = "predictor files/ncep_" + fileList[i] + ".dat"
    debugMsg(fileList)
    ## Other Vars:
    progValue = 0 ## Progress Bar
    thresh = 0 ## ???
    modelTrans = 1 ## No idea - never defined. Assumed 1-5, not starting 0
    ##Actuamalaly defined in main as Public ModelTrans As Single -> 'Model transformation; 1=none, 2=4root, 3=ln, 4=Inv Normal, 5=box cox
    ##Will copy whomever defined it...


    ## True Temps:
    rSquared = 0
    SE = 0
    chowStat = 0
    fRatio = 0
    parameterResultsArray = np.zeros((24,50))
    CondPropCorrect = 5

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
        loadedFiles = loadFilesIntoMemory(fileList, PTandRoot) 

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

        nDaysR = (globalEndDate - globalStartDate).days
        #noOfDays2Fit = nDaysR ## What is the point of this variable (at least, in python)?

        #------------------------
        #------ SECTION #3 ------ Filtration?
        #------------------------
        
        totalToSkip = (fsDate - globalStartDate)
        #if totalToSkip > 0:
            ## Progress Bar Stuff


        fsDateBaseline = np.zeros((12)) ## Original: FSDateBaseline(1 To 12) As Long
        workingDate = deepcopy(globalStartDate) ## It appears Current Day/Month/Year were split to make incrementing it easier.
        totalNumbers = 0

        while (fsDate - workingDate).days > 0: ##Infinite Loop Bug
            debugMsg("Loop0")
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

            totalNumbers += 1
            ##Call IncreaseDate
            workingDate = increaseDate(workingDate, 1)
            progValue = np.floor((totalNumbers / totalToSkip) * 100)
            ##Update progress bar with progValue

        ## END While

        #------------------------
        #----- SECTION #4.0 ----- ???
        #------------------------

        if seasonCode == 1:
            dataReadIn = np.zeros((1, NPredictors + 1, nDaysR))
        elif seasonCode == 4:
            dataReadIn = np.zeros((4, NPredictors + 1, ((nDaysR // 4) + 100)))
        else: ## Assume seasonCode = 12
            dataReadIn = np.zeros((12, NPredictors + 1, ((nDaysR // 12) + 100)))

        sizeOfDataArray = np.zeros((12), dtype=int)

        totalNumbers = 0
        missingRows = 0
        anyMissing = False
    
        ## Progress Bar Update Stuff

        currentMonth = workingDate.month - 1
        currentSeason = getSeason(workingDate.month)

        #------------------------
        #----- SECTION #4.1 ----- (Finding the Start Pos)
        #------------------------

        ## Revisit the following - Something feels off... ##

        noOfSections = np.zeros((12), dtype=int)
        startFound = False
        searchPos = 0

        while not startFound:
            debugMsg("Loop1")
            startFound = True
            for i in range(NPredictors + 1):
                #tempReadin[i] = loadedFiles[i]
                #if tempReadin[i] == GlobalMissingCode: startFound = False
                if loadedFiles[i][searchPos] == GlobalMissingCode: 
                    startFound = False
                #else:
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

        sizeOfDataArray[currentPeriod] += 1
        debugMsg(noOfSections)
        debugMsg(max(noOfSections))
        sectionSizes = np.zeros((12, 200), dtype=int) #sectionSizes = np.zeros((12, max(noOfSections)))
        for i in range(NPredictors + 1):
            dataReadIn[currentPeriod, i, sizeOfDataArray[currentPeriod]] = loadedFiles[i][searchPos]#tempReadin(i)

        if seasonCode != 1:
            debugMsg(noOfSections[currentPeriod])
            sectionSizes[currentPeriod, 0] += 1
            #sectionSizes[currentPeriod, noOfSections[currentPeriod]] += 1

        #------------------------
        #----- SECTION #4.2 ----- Finding evidence of missing values(?)
        #------------------------

        #call increasedate

        #Do Until (DateDiff("d", DateSerial(CurrentYear, CurrentMonth, CurrentDay), FSDate)) <= 0

        while (feDate - workingDate).days >= 0:
            debugMsg("Loop2")
            #Do Events, whatever that means
            ##Maybe Exit???

            anyMissing = False
            for i in range(NPredictors + 1):
                #tempReadin[i] = loadedFiles[i] ## input #j, tempReadin(j)
                #if tempReadin[j] == GlobalMissingCode: anyMissing = True
                if loadedFiles[i][searchPos] == GlobalMissingCode:
                    anyMissing = True
                #else:
            searchPos += 1
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
            else:
                sizeOfDataArray[currentPeriod] += 1
                for i in range(NPredictors + 1):
                    dataReadIn[currentPeriod, i, sizeOfDataArray[currentPeriod]] = loadedFiles[i]#tempReadin(i)
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
            workingDate = increaseDate(workingDate, 1)
            currentMonth = workingDate.month - 1
            currentSeason = getSeason(workingDate.month)
            progValue = np.floor((totalNumbers / nDaysR) * 100)

        ##End while

        #################
        ## Close Files ##
        #################

        #------------------------
        #----- SECTION #5.0 ----- 
        #------------------------

        anyMissing = False
        for i in range(0, seasonCode):
            if sizeOfDataArray[i] < 10:
                anyMissing = True

        if anyMissing:
            #error here
            do_nothing()
        else:
            xMatrix = None
            yMatrix = None
            yMatrixAboveThreshPos = None
            residualArray = np.array((1, TotalNumbers))
            noOfResiduals = 0

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
                    xMatrix = np.ndarray((sizeOfDataArray[0], NPredictors))
                    yMatrix = np.ndarray((sizeOfDataArray[0]))
                    yMatrixAboveThreshPos = np.ndarray((sizeOfDataArray[0]))
                    for i in range(sizeOfDataArray[0]):
                        yMatrix[i] = dataReadIn[0, 0, i]
                        #xMatrix[i, 0] = 1# --> What does this meen?
                        xMatrix[i, 0] = loadedFiles[0]
                        for j in range(NPreedictors):
                            xMatrix[i, j] = dataReadIn[0, j+1, i]
                            #do_nothing()
                else:
                    xMatrix = np.ndarray((sizeOfDataArray[0] - 1, NPredictors + 1))
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

                if (not detrendOption and not parmOpt):
                    ##call detrendData(periodWorkingOn, False)
                    detrendData(yMatrix, yMatrixAboveThreshPos, periodWorkingOn, False)

                savedYMatrix = deepcopy(yMatrix)
                if parmOpt:
                    ##call PropogateUnConditional
                    propogateUnconditional()

                if xValidation:
                    ##call xValUnConditional
                    xValUnconditional()

                conditionalPart = False ##Needed for CalcParameters

                if applyStepwise:
                    ##call stepwise_regression(parmOpt)
                    stepWiseRegression() ##very wise #betamatrix defined here
                else:
                    ##call CalculateParameters(parmOpt)
                    calculateParameters()   #betamatrix defined here
                ##endif

                if processTerminated:
                    ##call mini_reset
                    do_nothing()

                yMatrix = savedYMatrix

                for i in range(12):  ## 0-11 inclusive
                    for j in range(NPredictors + 1): ## 0-NPred inclusive
                        #parameterResultsArray[i, j] = betaMatrix[j, 0]
                        do_nothing()
                    ##next
                    ##Dim ParameterResultsArray(1 To 24, 1 To 50) As Double   'stores beta parmeters etc from calulations as going along - printed to file in the end
                    parameterResultsArray[i, NPredictors + 1] = SE
                    parameterResultsArray[i, NPredictors + 2] = RSquared
                    ##Dim StatsSummary(1 To 26, 1 To 5) As Double 'stores summary stats for each month;1=R2, 2=SE; 3=DW; 4=Chow; 5=FRatio (1 to 24 for months -cond and uncond - 25,26 are the means)
                    statsSummary[i, 0] = rSquared
                    statsSummary[i, 1] = SE
                    statsSummary[i, 3] = chowStat
                    statsSummary[i, 5] = fRatio
                ##next

                #------------------------
                #---- SECTION #5.1.2 ---- Conditional Part
                #------------------------

                if autoRegression:
                    NPredictors -= 1

                if parmOpt:
                    ## From Section #6.1.3 (Originally came before #6.1.2)
                    for i in range(12):
                        statsSummary[i, 2] = CondPropCorrect
                    ##next


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
                    propogateConditional() 

                    if xValidation:
                        #call xvalConditional
                        xValConditional()

                    #call TransformData
                    transformData()
                    ##if errored then exit

                    if detrendOption:
                        ##call DetrendData
                        detrendData(yMatrix, yMatrixAboveThreshPos, periodWorkingOn, True)


                    if modelTrans == 5:
                        for i in range(12):
                            lamdaArray[i, 0] = lamda
                            lamdaArray[i, 1] = shiftRight

                    ##Can we move the following above, to make it an elif?
                    conditionalPart = True
                    #call CalculateParameters(true)
                    calculateParameters() #betaMatrix defined here
                    
                    if processTerminated:
                        ##exit
                        do_nothing()
                    if modelTrans == 4:
                        for i in range(12):
                            biasCorrection[i] = CalculateBiasCorrection()
                    
                    for i in range(12, 24):
                        for j in range(NPredictors + 1):
                            #parameterResultsArray[i, j] = betaMatrix[j, 0]
                            do_nothing()
                        ##next
                        parameterResultsArray[i, NPredictors + 1] = SE
                        parameterResultsArray[i, NPredictors + 2] = rSquared
                        statsSummary[i, 0] = rSquared
                        statsSummary[i, 1] = SE
                        statsSummary[i, 3] = chowStat
                        statsSummary[i, 4] = fRatio
                    ##next
                else:
                    #------------------------
                    #---- SECTION #5.1.3 ---- DW calculations
                    #------------------------

                    DWNumerator = 0
                    DWDenom = 0
                    ##Need to properly calc residualMatrixRows
                    residualMatrixRows = 1
                    for i in range(1, residualMatrixRows):
                        DWNumerator += (residualMatrix[i,0] - residualMatrix[i - 1, 0]) ** 2
                    ##next
                    for i in range(residualMatrixRows):
                        DWDenom += residualMatrix[i, 0] ** 2
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
                        xMatrix = np.ndarray((periodWorkingOn + 1, NPredictors))
                        yMatrix = np.ndarray((periodWorkingOn + 1))
                        yMatrixAboveThreshPos = np.ndarray((sizeOfDataArray[0]))
                        for i in range(sizeOfDataArray[periodWorkingOn]):
                            yMatrix[i] = dataReadIn[0, 0, i]
                            #xMatrix[i, 0] = 1# --> What does this meen?
                            xMatrix[i, 0] = loadedFiles[0]
                            for j in range(NPreedictors):
                                xMatrix[i, j] = dataReadIn[0, j+1, i]
                                #do_nothing()
                        ###### End of Sorta Copy ######
                    else:
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

                    if (not detrendOption and not parmOpt):
                        ##call detrendData(periodWorkingOn, False)
                        detrendData(yMatrix, yMatrixAboveThreshPos, periodWorkingOn, False)
                        
                    savedYMatrix = deepcopy(yMatrix)

                    if parmOpt:
                        ###call PropogateUnconditional
                        propogateUnconditional()
                    
                    if xValidationCheck:
                        ##call xValUnconditional
                        xValUnconditional()

                    conditionalPart = False

                    ###until now, #6.2.1 is near identical to #6.1.1,
                    ###but is notably missing the ApplyStepwise condition for CalcualteParameters

                    ##call CalculateParameters(parmOpt) ##Adjust to make sure its correct...?
                    calculateParameters()

                    if processTerminated:
                        ##call mini_reset
                        do_nothing()

                    yMatrix = savedYMatrix

                    if seasonCode == 4:
                        for i in range(3):
                            for j in range(NPredictors):
                                #parameterResultsArray[seasonMonths[periodWorkingOn, i], j] = betaMatrix[i, 0]
                                do_nothing()
                            ##next j
                            parameterResultsArray[seasonMonths[periodWorkingOn, i], NPredictors + 1] = SE
                            parameterResultsArray[seasonMonths[periodWorkingOn, i], NPredictors + 2] = rSquared
                            statsSummary[seasonMonths[periodWorkingOn, i], 0] = rSquared
                            statsSummary[seasonMonths[periodWorkingOn, i], 1] = SE
                            statsSummary[seasonMonths[periodWorkingOn, i], 3] = chowStat
                            statsSummary[seasonMonths[periodWorkingOn, i], 4] = fRatio
                        ##next i
                    else: ##Monthly?
                        for i in range(NPredictors + 1):
                            #parameterResultsArray[periodWorkingOn, i] = betaMatrix[i, 0]
                            do_nothing()
                        ##next
                        parameterResultsArray[periodWorkingOn, NPredictors + 1] = SE
                        parameterResultsArray[periodWorkingOn, NPredictors + 2] = rSquared
                        statsSummary[periodWorkingOn, 0] = rSquared
                        statsSummary[periodWorkingOn, 1] = SE
                        statsSummary[periodWorkingOn, 3] = chowStat
                        statsSummary[periodWorkingOn, 4] = fRatio
                    ##endif

                    #------------------------
                    #---- SECTION #5.2.2 ---- (Conditional Part)
                    #------------------------

                    if autoRegression:
                        NPredictors -= 1

                    if parmOpt:
                        ## From Section #5.2.3 (Originally came before #5.2.2)
                        if seasonCode == 12:
                            statsSummary[periodWorkingOn, 2] = CondPropCorrect
                        else:
                            for i in range(3):
                                statsSummary[seasonMonths[periodWorkingOn, i], 2] = CondPropCorrect
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
                        propogateConditional()

                        if xValidation:
                            #call xValConditional
                            xValConditional()
                        
                        #call TransformData
                        transformData()
                        #if errored then exit

                        if detrendOption:
                            ##call DetrendData
                            detrendData(yMatrix, yMatrixAboveThreshPos, periodWorkingOn, True)

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
                        calculateParameters() #BetaMatrix defined here
                        if processTerminated:
                            ##exit
                            do_nothing()
                        if modelTrans == 4:
                            if seasonCode == 4:
                                for i in range(3):
                                    biasCorrection[seasonMonths[periodWorkingOn, i]] = calculateBiasCorrection()
                                ##next i
                            else:
                                biasCorrection[periodWorkingOn] = calculateBiasCorrection()
                            ##endif
                        ##endif

                        if seasonCode == 4:
                            for i in range(3):
                                for j in range(NPredictors + 1):
                                    #parameterResultsArray[seasonMonths[periodWorkingOn, i] + 12, j] = betaMatrix[j, 0]
                                    do_nothing()
                                ##next j
                                parameterResultsArray[seasonMonths[periodWorkingOn, i] + 11, NPredictors + 1] = SE
                                parameterResultsArray[seasonMonths[periodWorkingOn, i] + 11, NPredictors + 2] = rSquared
                                statsSummary[seasonMonths[periodWorkingOn, i] + 11, 0] = rSquared
                                statsSummary[seasonMonths[periodWorkingOn, i] + 11, 1] = SE
                                statsSummary[seasonMonths[periodWorkingOn, i] + 11, 3] = chowStat
                                statsSummary[seasonMonths[periodWorkingOn, i] + 11, 4] = fRatio
                            ##next i
                        else:
                            for j in range(NPredictors + 1):
                                #parameterResultsArray[periodWorkingOn + 12, j] = betaMatrix[j, 0]
                                do_nothing()
                            ##next j
                            parameterResultsArray[periodWorkingOn + 12, NPredictors + 1] = SE
                            parameterResultsArray[periodWorkingOn + 12, NPredictors + 2] = rSquared
                            statsSummary[periodWorkingOn + 12, 0] = rSquared
                            statsSummary[periodWorkingOn + 12, 1] = SE
                            statsSummary[periodWorkingOn + 12, 3] = chowStat
                            statsSummary[periodWorkingOn + 12, 4] = fRatio
                        ##endif  
                    else:             
                        #------------------------
                        #---- SECTION #5.2.3 ---- (DW Calculations)
                        #------------------------

                        DWNumerator = 0
                        DWDenom = 0
                        positionStart = 0 ##Ooh this is new...
                        for i in range(noOfSections[periodWorkingOn]):
                            sectionSize = sectionSizes[periodWorkingOn, i]
                            if sectionSize > 1:
                                if autoRegression:
                                    sectionSize -= 1

                                for j in range(sectionSize - 1):
                                    ##curious
                                    DWNumerator += (residualMatrix[j + positionStart, 0] - residualMatrix[j + positionStart - 1, 0]) ** 2
                                #next j
                                positionStart += sectionSize
                            #endif
                        #next i
                        for i in range(noOfSections[periodWorkingOn]):
                            sectionSize = sectionSizes[periodWorkingOn, i]
                            if sectionSize > 1:
                                if autoRegression:
                                    sectionSize -= 1

                                for j in range(sectionSize - 1):
                                    ##curious+
                                    DWDenom += residualMatrix[j + positionStart, 0] ** 2
                                #next j
                                positionStart += sectionSize
                            #endif
                        #next i
                        if DWDenom > 0:
                            if seasonCode == 12:
                                statsSummary[periodWorkingOn, 2] = DWNumerator / DWDenom
                            else:
                                for i in range(3):
                                    statsSummary[seasonMonths[periodWorkingOn, i], 2] = DWNumerator / DWDenom
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
            if detrendOption:
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

            ##real change here:
            output = {
                "SeasonCode": seasonCode,
                #"YearIndicator": yearIndicator,
                "GlobalStartDate": globalStartDate,
                "NDaysR": nDaysR,
                "1":1, ##Idk what to do with this
                "AutoRegression": autoRegression 
            }
            for subloop in range(NPredictors):
                output[f"FileList#{subloop}"] = fileList[subloop]
            ##Vars "Written":
            output2 = {
                "ParmOpt": parmOpt,
                "ModelTrans":modelTrans
            }

            ##Done with "prelim data"
            
            #call PrintResults
            #print PTandRoot
            if detrendOption:   ##Will need to double check and standardise this parameter
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

def detrendData(yMatrix: np.array, yMatrixAboveThreshPos: np.array, period: int, conditional: bool):
    """
    Detrend Data Function
    -- Currently a placeholder
    ----> Might be Coming Soon
    ----> Hard dependency on TransformData (Needs yMatrixAboveThreshPos)
    """
    ##DetrendOption: 0 = none, 1 = Linear, 2 = power function

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

    if detrendOption == 1:
        tempMatrix1 = np.linalg.inv(np.multiply(xValues.transpose, xValues))
        tempMatrix2 = np.multiply(xValues.transpose, yMatrix)
        betaValues = np.multiply(tempMatrix1, tempMatrix2)
        betaTrend[period, 0] = betaValues[0] #,0]
        betaTrend[period, 1] = betaValues[1] #,0]

        for i in range(len(yMatrix)):
            yMatrix[i] -= (xValues[i,1] * betaValues[1]) #,0])
        ##next i

    else:
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
        tempMatrix1 = np.linalg.inv(np.multiply(xLogged.transpose, xLogged))
        tempMatrix2 = np.multiply(xLogged.transpose, tempYMatrix)
        betaValues = np.multiply(tempMatrix1, tempMatrix2)
        betaValues[0] = np.exp(betaValues[0]) #,0] = np.exp(betaBalues(0,0))
        betaTrend[period, 0] = betaValues[0]
        betaTrend[period, 1] = betaValues[1]
        betaTrend[period, 2] = minY

        for i in range(len(yMatrix)):
            yMatrix[i] -= (betaValues[0,0] * (xValues[i, 1] ** betaValues[1,0])) - np.abs(minY) - 0.001
        



def propogateUnconditional():
    """Propogate Unconditional Function
    -- Currently a placeholder
    """
def propogateConditional():
    """ Propogate: Conditional Function
    -- Currently a placeholder
    -- VERY similar functionality to propUncond
    ----> Might merge code if possible
    """

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

def calculateParameters():
    """
    Calculate Parameters function
    -- Currently a placeholder
    -- Presumably calculates parameters
    """

def transformData(modelTrans, yMatrix):
    """
        Transform data?
        transforms data in Y Matrix according to transformation required.  Amends (reduces) X matrix too if some values are missing
        modelTrans ->  Option from None (1), 4th Root (2), Natural Log (3), Inverse Normal (4), Box Con (5)
        yMatrix -> 'Y Matrix - X declared globally so registration code entered
        Likely doesn't work - was done right at the start
    """
    ## N.B. Multiple brackets need changing from () to []

    ### GLOBALS ###
    GlobalMissingCode = -999
    yMatrixAboveThreshPos = np.array()
    xMatrix = np.array()
    ### ####### ###

    #If modelTrans = 1 then do nothing -> no transformation
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
                yMatrix[i] = GlobalMissingCode
                yMatrixAboveThreshPos[i] = GlobalMissingCode   #     'this resords position of y values for detrend option - needs reducing too
                missing = missing + 1
            #next i
        if missing > 0:  #Remove missing valus
            if len(yMatrix) - missing > 10:   #'make sure there are enough data
                newYMatrix = np.ndarray((len(yMatrix) - missing))
                newXMatrix = np.array()
                newYMatrixAbove = np.array()
                count = 0
                for i in range(len(yMatrix)): ##Drop unwanted arrayz
                    if yMatrix[i] != GlobalMissingCode:
                        newYMatrix[count] = yMatrix[i]
                        newYMatrixAbove[count] = yMatrixAboveThreshPos[i]
                        for j in range(len(xMatrix[0])): #XCols
                            newXMatrix[count, j] = xMatrix(i, j)
                       #Next j
                        count += 1
                    #End If
                #Next i              'newXMatrix and newYMatrix and newYMatrixAbove now have good data in them
                
                yMatrix = newYMatrix.copy()
                xMatrix = newXMatrix.copy()
                yMatrixAboveThreshPos = newYMatrixAbove.copy()
        
        #End If
    elif modelTrans == 5: #          'box cox - so need to find best lamda of YMatrix
        #x = PeriodWorkingOn         'for testing!
        minSoFar = 9999                 #'establish right shift for box cox transform as min value in y matrix if -ve.  Makes all values +ve
        for i in range(1,len(yMatrix.Rows)):
            if yMatrix[i, 0] < minSoFar:
                minSoFar = yMatrix[i, 0]
        #Next i
        if minSoFar >= 0: 
            ShiftRight = 0
        if minSoFar < 0:
            ShiftRight = np.abs(minSoFar)
        for i in range(1, len(yMatrix)):              #'now shift all Y matrix data right to make sure it's +ve before we calculate lamda
            yMatrix[i, 0] = yMatrix[i, 0] + ShiftRight
        #Next i
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
        
        for value in yMatrix:
            if lamda == 0:                          # 'apply box cox lamda transform - do some checks for division by zero first
                if value != 0:
                    value = np.log(value) - ShiftRight         #'shift it back to left after transform
                else:
                    value = -5 - ShiftRight     #'cannot log zero so -5 represents log of a very small number
                #End If
            else:
                value = (((value ^ lamda) - 1) / lamda) - ShiftRight     #'shift it back to left after transform
            #End If
        #Next i
    else:        #'Inverse normal selected: model trans=4
        
        rankMatrix = np.zeros(2, len(yMatrix)) #'add an extra column     
        rankMatrix[0] = yMatrix.copy()      #'copy Y matrix into RankMatrix
        reSampleMatrix = yMatrix.copy()     #'save these data in global matrix so can be resampled when untransforming

        for i in range(1, len(rankMatrix)):        #'set column two to a running count
            rankMatrix[1, i - 1] = i
        #Next i
        
        rankMatrix.sort(0)              #'sort ascending on first column ie. on data column
        
        #            'Locate lower bound to begin estimation of cdf
        #            'cdf is computed as r/(n+1) where r is the rank and n is sample size
        zStart = 1 / (len(rankMatrix) + 1)
        delta = 0.0001
        area = 0.5
        fx = 0
        fxOld = np.exp(-(fx ^ 2) / 2) / np.sqrt(2 * np.pi)         #'normal
        i = 1 #Counter
        while ((i <= 50000) and (area > zStart)):
            fx = fx - delta
            fxNew = np.exp(-(fx ^ 2) / 2) / np.sqrt(2 * np.pi)         #'normal
            area = area - (delta * 0.5 * (fxOld + fxNew))
            fxOld = fxNew
            i = i + 1
        #endwhile

        #'Compute cdf between lower and upper limit
        limit = fx
        area = zStart
        rankMatrix[0, 0] = limit
        percentileChange = (1 - (area * 2)) / (len(rankMatrix[0]) - 1)
        cp = area
        fxOld = np.exp(-(fx ^ 2) / 2) / np.sqrt(2 * np.pi)         #'normal

        for i in range(2, len(rankMatrix[0])): #2 To RankMatrix.Rows
            cp = cp + percentileChange
            j = 1
            while ((j <= 50000) and (area < cp)):
                fx = fx + delta
                fxNew = np.exp(-(fx ^ 2) / 2) / np.sqrt(2 * np.pi)         #'normal
                area = area + (delta * 0.5 * (fxOld + fxNew))
                fxOld = fxNew
                if area >= cp:
                    rankMatrix[0, i - 1] = fx
                j = j + 1
            #Wend
        #Next i
        
        rankMatrix.sort(1)       #'sort back into temporal sequence and copy data back to YMatrix
        yMatrix = rankMatrix[0].copy
        #For i = 1 To RankMatrix.Rows
        #    YMatrix(i - 1, 0) = RankMatrix(i - 1, 0)
        #Next i

    #End If
    
    #return Something here