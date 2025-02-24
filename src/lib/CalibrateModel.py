import numpy as np
from datetime import date

## NOTE TO READERS: THIS FILE **DOES NOT** WORK

def calibrateModel(applyStepwise, modelType, detrendOption, parmOpt, autoRegression):
    """
        Core Calibrate Model Function (v0.1.0)
    """

    ##Real comments will be added later

    #------------------------
    # FUNCTION DEFINITITIONS:
    #------------------------


    ## Globals:
    GlobalMissingCode = -1
    NPredictors = 12

    ## (Temp) Parameters
    ApplyStepwise = True
    modelType = 0
    globalStartDate = date(2024, 8, 5)
    globalEndDate = date(2025, 1, 7)
    fsDate = date(2025, 1, 8)
    detrendOption = True
    parmOpt = True  ## Whether Conditional or Unconditional. True = Cond, False = Uncond. 
    ##ParmOpt(1) = Uncond = False
    ##ParmOpt(0) = Cond = True
    autoRegression = True ## Replaces AutoRegressionCheck

    ## Other Vars:
    progValue = 0 ## Progress Bar
    thresh = 0 ## ???
    modelTrans = 1 ## Defined in main as Public ModelTrans As Single -> 'Model transformation; 1=none, 2=4root, 3=ln, 4=Inv Normal, 5=box cox
    ##Will copy whomever defined it...

    ## Idea: Could define commonly used ranges here so that we don't keep recreating them each time.

    
    #------------------------
    #------ SECTION #1 ------ Error Checking & Validation
    #------------------------

    ##not used rn -> will add later
    ##i have notes trust me
    
    if true:
        #------------------------
        #------ SECTION #2 ------ Unknown/Initialisation?
        #------------------------

        
        xValidationResults = np.ndarray(12, 6).fill(GlobalMissingCode) ## Original array is XValidationResults(1 To 13, 1 To 7) As Double
        xValidMessageShown = False

        #if ApplyStepwise:
            ## Add msg
    
        lambdaArray = np.zeros(11,1) ## Lamda array originally "LamdaArray(1 To 12, 1 To 2) As Double"

        processTerminated = False

        statsSummary = np.zeros(25,4) ## Originally StatsSummary(1 To 26, 1 To 5) As Double

        dependMgs = False

        #-----------------
        ##CLOSE FILES HERE -> idk why, likely contingency / prep
        #-----------------

        ## Reading in data from files?
        ##idk how to do that rn, will revisit

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


        FSDateBaseline = ndarray.zeros((11)) ## Original: FSDateBaseline(1 To 12) As Long
        workingDate = globalStartDate.copy() ## It appears Current Day/Month/Year were split to make incrementing it easier.
        totalNumbers = 0

        while (FSDate - workingDate).days > 0:
            if seasonCode == 1:
                FSDateBaseline[0] += 1
            elif seasonCode == 4:
                FSDateBaseline[GetSeason(workingDate.month)] += 1
            else: ##Assume seasonCode = 12:
                FSDateBaseline[workingDate.month] += 1

            ##########################################
            ## What is "DoEvents"?
            ##########################################

            #for i in range(NPredictors + 1):
                ##Load in files?

            totalNumbers += 1
            ##Call IncreaseDate
            progValue = np.floor((totalNumbers / totalToSkip) * 100)
            ##Update progress bar with progValue

        ## END While

        #------------------------
        #------ SECTION #4 ------ ???
        #------------------------

        if seasonCode == 1:
            dataReadIn = np.zeros((0, NPredictors, nDaysR))
        elif seasonCode == 4:
            dataReadIn = np.zeros((3, NPredictors, ((noOfDays2Fit / 4) + 100)))
        else: ## Assume seasonCode = 12
            dataReadIn = np.zeros((11, NPredictors, ((noOfDays2Fit / 12) + 100)))

        sizeOfDataArray = np.zeros((11))

        totalNumbers = 0
        missingRows = 0
        anyMissing = False
    
        ## Progress Bar Update Stuff

        ## Revisit the following - Something feels off... ##

        noOfSections = np.zeros((11))
        startFound = False

        while not startFound:
            startFound = True
            #for i in range(NPredictors + 1):
                ## input #j, tempReadin(j)
                ## if tempReadin(j) = GlobalMissingCode: startFound = False
            
            totalNumbers += 1
            progValue = np.floor((totalNumbers / noOfDays2Fit) * 100)
            #call newProgressBar

        lastDate = workingDate.copy()
        if seasonCode == 1:
            currentPeriod = 1
        elif seasonCode == 4:
            noOfSections[currentSeason] = 1
            sectionSizes[currentSeason, 1] = 0
            currentPeriod = currentSeason
        else: ##Assume seasonCode = 12
            noOfSections[currentMonth] = 1
            sectionSizes[currentMonth, 1] = 0
            currentPeriod = currentMonth

        sizeOfDataArray[currentPeriod] += 1
        for i in range(NPredictors + 1):
            dataReadIn[currentPeriod, i, sizeOfDataArray(currentPeriod)] = tempReadin(i)

        if seasonCode != 1:
            sectionSizes[currentPeriod, noOfSections[currentPeriod]] += 1

        #------------------------
        #------ SECTION #5 ------
        #------------------------

        #call increasedate

        #Do Until (DateDiff("d", DateSerial(CurrentYear, CurrentMonth, CurrentDay), FSDate)) <= 0

        while (FEDate - workingDate).days >= 0:
            #Do Events, whatever that means
            ##Maybe Exit???

            anyMissing = False
            #for i in range(NPredictors + 1):
                ## input #j, tempReadin(j)
                ## if tempReadin(j) = GlobalMissingCode: anyMissing = True
            
            totalNumbers += 1
            if seasonCode == 1:
                currentPeriod = 1
            elif seasonCode == 4:
                currentPeriod = currentSeason
            else: ##Assume seasonCode = 12
                currentPeriod = currentMonth
            
            if anyMissing:
                missingRows += 1
            else:
                sizeOfDataArray[currentPeriod] += 1
                for i in range(NPredictors + 1):
                    dataReadIn[currentPeriod, i, sizeOfDataArray(currentPeriod)] = tempReadin(i)

            if ((seasonCode == 4) and (currentPeriod != lastSeason)) or ((seasonCode == 12) and (currentPeriod != lastMonth)):
                noOfSections[currentPeriod] += 1
                if anyMissing:
                    sectionSizes[currentPeriod, noOfSections[currentPeriod]] = 0
                else:
                    sectionSizes[currentPeriod, noOfSections[currentPeriod]] = 1
            elif (seasonCode != 1) and not anyMissing:
                sectionSizes[currentPeriod, noOfSections[currentPeriod]] += 1
            
            lastMonth = currentMonth
            lastSeason = currentSeason

            #call increasedate
            progValue = np.floor((totalNumbers / noOfDays2Fit) * 100)

        ##End while

        #################
        ## Close Files ##
        #################

        #------------------------
        #----- SECTION #6.0 ----- 
        #------------------------

        anyMissing = False
        for i in range(0, seasonCode):
            if sizeOfDataArray(i) < 10:
                anyMissing = True

        if anyMissing:
            #error here
            do_nothing() ## prevent indentation error
        else:
            xMatrix = None
            yMatrix = None
            yMatrixAboveThreshPos = None
            residualArray = np.array((1, TotalNumbers))
            noOfResiduals = 0

            #------------------------
            #---- SECTION #6.1.0 ---- SeasonCode 1 -> Annuals
            #------------------------

            ## uwu
            ## Double check for arrays with too many / little values...

            if seasonCode == 1:
                periodWorkingOn = 1
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
                    xMatrix = np.array((sizeOfDataArray[0], NPredictors))
                    yMatrix = np.array(sizeOfDataArray[0])
                    yMatrixAboveThreshPos = np.array(sizeOfDataArray[0])
                    for i in range(sizeOfDataArray[0]):
                        yMatrix[i] = dataReadIn[0, 0, i]
                        #xMatrix[i, 0] = 1# --> What does this meen?
                        for j in range(NPreedictors):
                            #xMatrix[i, j] = dataReadIn[0, j+1, i]
                            do_nothing()
                else:
                    xMatrix = np.ndarray((sizeOfDataArray[0] - 1, NPredictors + 1))
                    yMatrix = np.array(sizeOfDataArray[0] - 1)
                    for i in range(sizeOfDataArray[0] - 1):
                        yMatrix[i] = dataReadIn(0, 0, i + 1)
                        #xMatrix[i, 0] = 1#
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
                #---- SECTION #6.1.1 ---- 
                #------------------------

                if (not detrendOption and not parmOpt):
                    ##call detrendData(periodWorkingOn, False)
                    detrendData()

                savedYMatrix = yMatrix.clone()
                if parmOpt:
                    ##call PropogateUnConditional
                    propogateUnconditional()

                if xValidationCheck:
                    ##call xValUnConditional
                    xValUnconditional()

                conditionalPart = False ##Needed for CalcParameters

                if applyStepwise:
                    ##call stepwise_regression(parmOpt)
                    stepWiseRegression() ##very wise
                else:
                    ##call CalculateParameters(parmOpt)
                    calculateParameters()
                ##endif

                if processTerminated:
                    ##call mini_reset
                    do_nothing()

                yMatrix = savedYMatrix.clone()

                for i in range(12):  ## 0-11 inclusive
                    for j in range(NPredictors + 1): ## 0-NPred inclusive
                        parameterResultsArray[i, j] = beetaMatrix[j, 0]
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
                #---- SECTION #6.1.2 ---- Conditional Part
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
                        xMatrixClone = xMatrix.clone()
                        #xmatrix size
                        #for loop
                        #extra for loop
                        #somethign else...
                    ##endif

                    #call PropogateConditional
                    propogateConditional() 

                    if xValidationCheck == 1:
                        #call xvalConditional
                        xValConditional()

                    #call TransformData
                    transformData()
                    ##if errored then exit

                    if detrendOption:
                        ##call DetrendData
                        detrendData()

                    if modelTrans == 5:
                        for i in range(12):
                            lamdaArray[i, 0] = lamda
                            lamdaArray[i, 1] = shiftRight

                    ##Can we move the following above, to make it an elif?
                    conditionalPart = True
                    #call CalculateParameters(true)
                    calculateParameters()
                    
                    if processTerminated:
                        ##exit
                        do_nothing()
                    if modelTrans == 4:
                        for i in range(12):
                            biasCorrection[i] = CalculateBiasCorrection()
                    
                    for i in range(12, 24):
                        for j in range(NPredictors + 1):
                            parameterResultsArray[i, j] = betaMatrix[j, 0]
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
                    #---- SECTION #6.1.3 ---- DW calculations
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
                #---- SECTION #6.2.0 ---- (season/month)
                #------------------------
            else:
                for periodWorkingOn in range(1, SeasonCode + 1):
                    #progValue = ##progress bar stuff
                    ##call newprogressbar

                    ## Copied from above section (SeasonCode == 1), but sizeOfDataArray swapped for periodWorkingOn
                    if not autoRegression:
                        xMatrix = np.array((periodWorkingOn, NPredictors))
                        yMatrix = np.array(periodWorkingOn)
                        yMatrixAboveThreshPos = np.array(sizeOfDataArray[0])
                        for i in range(sizeOfDataArray[periodWorkingOn]):
                            yMatrix[i] = dataReadIn[0, 0, i]
                            #xMatrix[i, 0] = 1# --> What does this meen?
                            for j in range(NPreedictors):
                                #xMatrix[i, j] = dataReadIn[0, j+1, i]
                                do_nothing()
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
                        binsTotal = binsTotal - okSectionCount
                        ##xMatrix resize 
                        ##yMatrix resize
                        tempCounter = 0
                        progressTHroughData = 1
                        for i in range(noOfSections[periodWorkingOn]):
                            if sectionSizes[periodWorkingOn, i] > 1:
                                for j in range(sectionSizes[periodWorkingOn, i]):
                                    yMatrix[tempCounter] = dataReadIn[periodWorkingOn, 0, ]
                                    for subloop in range(NPredictors - 1):
                                        xMatrix[tempCounter, subloop] = dataReadIn[periodWorkingON, subloop, j+progressThroughData]
                                    ##next (subloop)
                                    ##xmatrix[tempCounter, 0] = 1#
                                    if parmOpt:
                                        if dataREadIn[periodWorkingOn, 0, j + progressThroughData - 1] > thresh:
                                            xMatrix[tempCounter, NPredictors] = 1
                                        else:
                                            xMatrix[tempCounter, NPredictors] = 0
                                        ##endif
                                    else:
                                        xMatrix[tempCounter, NPredictors] = dataReadIn[periodWorkingON, 0, j+progressThroughData - 1]
                                    ##endif
                                    tempCounter += 1
                                ##next j
                            ##endif
                            progressThroughData += sectionSizes[periodWorkingOn, i]
                        ##next i
                    ##endif

                    #------------------------
                    #---- SECTION #6.2.1 ---- 
                    #------------------------

                    if (not detrendOption and not parmOpt):
                        ##call detrendData(periodWorkingOn, False)
                        detrendData()
                        
                    savedYMatrix = yMatrix.clone()

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

                    yMatrix = savedYMatrix.clone()

                    if seasonCode == 4:
                        for i in range(3):
                            for j in range(NPredictors):
                                parameterResultsArray[seasonMonths[periodWorkingOn, i], j] = betaMatrix[i, 0]
                            ##next j
                            parameterResultsArray[seasonMonths[periodWorkingOn, i], NPredictors + 1] = SE
                            parameterResultsArray[seasonMonths[periodWorkingON, i], NPredictors + 2] = rSquared
                            statsSummary[seasonMonths[periodWorkingOn, i], 0] = rSquared
                            statsSummary[seasonMonths[periodWorkingOn, i], 1] = SE
                            statsSummary[seasonMonths[periodWorkingOn, i], 3] = chowStat
                            statsSummary[seasonMonths[periodWorkingOn, i], 4] = fRatio
                        ##next i
                    else: ##Monthly?
                        for i in range(NPredictors + 1):
                            parameterResultsArray[periodWorkingOn, i] = betaMatrix[i, 0]
                        ##next
                        parameterResultsArray[periodWorkingON, NPredictors + 1] = SE
                        parameterResultsArray[periodWorkingOn, NPredictors + 2] = rSquared
                        statsSummary[periodWorkingOn, 0] = rSquared
                        statsSummary[periodWorkingOn, 1] = SE
                        statsSummary[periodWorkingOn, 3] = chowStat
                        statsSummary[periodWorkingOn, 4] = fRatio
                    ##endif

                    #------------------------
                    #---- SECTION #6.2.2 ---- (Conditional Part)
                    #------------------------

                    if autoRegression:
                        NPredictors -= 1

                    if parmOpt:
                        ## From Section #6.2.3 (Originally came before #6.2.2)
                        if seasonCode == 12:
                            statsSummary[periodWorkingOn, 2] = CondPropCorrect
                        else:
                            for i in range(3):
                                statsSummary[seasonMonths[periodWorkingOn, i], 2] = CondPropCorrect
                            ##next
                        ##endif

                        if autoRegression:
                            ##Funky resize stuffs here - come back later...
                            xMatrixClone = xMatrix.clone()
                            #xmatrix size
                            #for loop
                            #extra for loop
                            #somethign else...
                        ##endif

                        #call PropogateConditional
                        propogateConditional()

                        if xValidationCheck == 1:
                            #call xValConditional
                            xValConditional()
                        
                        #call TransformData
                        transformData()
                        #if errored then exit

                        if detrendOption:
                            ##call DetrendData
                            detrendData()

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
                        calculateParameters()
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
                                    parameterResultsArray[seasonMonths[periodWorkingOn, i] + 12, j] = betaMatrix[j, 0]
                                ##next j
                                parameterResultsArray[seasonMonths[periodWorkingOn, i] + 12, NPredictors + 1] = SE
                                parameterResultsArray[seasonMonths[periodWorkingOn, i] + 12, NPredictors + 2] = rSquared
                                statsSummary[seasonMonths[periodWorkingOn, i] + 12, 0] = rSquared
                                statsSummary[seasonMonths[periodWorkingOn, i] + 12, 1] = SE
                                statsSummary[seasonMonths[periodWorkingOn, i] + 12, 3] = chowStat
                                statsSummary[seasonMonths[periodWorkingOn, i] + 12, 4] = fRatio
                            ##next i
                        else:
                            for j in range(NPredictors + 1):
                                parameterResultsArray[periodWorkingOn + 12, j] = betaMatrix[j, 0]
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
                        #---- SECTION #6.2.3 ---- (DW Calculations)
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
            #----- SECTION #7.0 ----- Printing to Scream?
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
                "YearIndicator": yearIndicator,
                "GlobalStartDate": globalSDate,
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
                printTrendParms() ##???
            #call newProgressBar

            #------------------------
            #----- SECTION #7.1 ----- something something load calibResultsFrm
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

def detrendData():
    """
    Detrend Data Function
    -- Currently a placeholder
    """

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

def transformData():
    """
    Transform Data function
    -- Currently a placeholder
    """