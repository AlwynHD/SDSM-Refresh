import math
import configparser
from datetime import datetime, date
import os

def convertValue(key, value):
    if key in ('globalsdate', 'globaledate'):
        return datetime.strptime(value, '%d/%m/%Y').date()
    if key == 'yearindicator':
        return int(value)
    if key == 'globalmissingcode':
        try:
            return int(value)
        except ValueError:
            return float(value)
    if key in ('thresh', 'fixedthreshold'):
        return float(value)
    if key in ('varianceinflation', 'biascorrection'):
        return int(value)
    if key in ('allowneg', 'randomseed'):
        return value.strip().lower() in ('true', '1', 'yes')
    if key == 'months':
        return [int(x) for x in value.split(',') if x.strip()]
    return value

def loadSettings(configPath='src/lib/settings.ini'):
    parser = configparser.ConfigParser()
    parser.read(configPath)
    raw = parser['Settings']
    # convert each setting
    settings = {k: convertValue(k, v) for k, v in raw.items()}
    # wrap non-list values in a list
    settingsAsArrays = {
        k: (v if isinstance(v, list) else [v])
        for k, v in settings.items()
    }
    return settings, settingsAsArrays

settings, settingsAsArrays = loadSettings()
globalMissingCode = settingsAsArrays['globalmissingcode'][0]

def nCk(n, k):
    """
    Compute the binomial coefficient (n choose k).
    Returns globalMissingCode for invalid inputs.
    """
    if n < k or n < 1 or k < 0:
        return globalMissingCode
    # math.comb returns an int
    return float(math.comb(n, k))

def bL(data, l):
    """
    Compute the l-th probability-weighted moment (b_l).
    """
    n = len(data)
    if n == 0 or l < 0 or l >= n:
        raise ValueError(f'Invalid l={l} for data length={n}')
    if l == 0:
        return sum(data) / n

    x = sorted(data)
    def perm(a, b):
        p = 1.0
        for i in range(a, a - b, -1):
            p *= i
        return p

    denom = perm(n - 1, l)
    total = sum((perm(i - 1, l) / denom) * x[i - 1] for i in range(1, n + 1))
    return total / n

def gamma(z):
    """
    Approximate Γ(z) via (n!·n**z) / [z·(z+1)·…·(z+n)], n=50.
    Returns globalMissingCode if z == 0.
    """
    if z == 0:
        return globalMissingCode

    n = 50
    num = math.factorial(n) * (n ** z)
    den = z
    for i in range(1, n + 1):
        den *= (z + i)
    return num / den

def getSeason(month):
    """
    Determine the meteorological season from a month number.

    Season codes:
      1 → Winter  (Dec, Jan, Feb)
      2 → Spring  (Mar, Apr, May)
      3 → Summer  (Jun, Jul, Aug)
      4 → Autumn  (Sep, Oct, Nov)

    Parameters
    ----------
    month : int
        Month as an integer, 1 through 12.

    Returns
    -------
    int
        The season code (1–4).

    Raises
    ------
    ValueError
        If `month` is not in the range 1–12.
    """
    if month in (12, 1, 2):
        return 1
    elif month in (3, 4, 5):
        return 2
    elif month in (6, 7, 8):
        return 3
    elif month in (9, 10, 11):
        return 4
    else:
        raise ValueError(f"Invalid month ({month!r}); must be between 1 and 12.")

def isLeap(year):
    """
    Determine whether a given year is a leap year.

    A year is a leap year if:
      - It is divisible by 4, and
      - Not divisible by 100 unless also divisible by 400.

    Parameters
    ----------
    year : int
        The year to test.

    Returns
    -------
    bool
        True if `year` is a leap year, False otherwise.
    """
    return (year % 4 == 0) and (year % 100 != 0 or year % 400 == 0)

def daysInMonth(month, yearLength):
    """
    Get the number of days in a given month.

    Parameters
    ----------
    month : int
        Month as an integer, 1 through 12.
    yearLength : int
        A flag from the original VB code (unused here).
        Leap‑year adjustments are performed separately.

    Returns
    -------
    int
        Number of days in the specified month. Defaults to 31 if `month` is out of range.
    """
    daysMap = {
        1: 31,
        2: 28,
        3: 31,
        4: 30,
        5: 31,
        6: 30,
        7: 31,
        8: 31,
        9: 30,
        10: 31,
        11: 30,
        12: 31,
    }
    return daysMap.get(month, 31)


def isDate(dateText, fmt="%Y-%m-%d"):
    """
    Check whether a string can be parsed as a date in the given format.

    Parameters
    ----------
    dateText : str
        The date string to validate.
    fmt : str, optional
        The date format to validate against (default ISO "YYYY-MM-DD").

    Returns
    -------
    bool
        True if `dateText` matches the format, False otherwise.
    """
    try:
        datetime.strptime(dateText, fmt)
        return True
    except ValueError:
        return False
    
def dateSerial(year: int, month: int, day: int) -> date:
    return date(year, month, day)

def dateDiff(start, end):
    """
    Difference in days between two date strings.
    Raises ValueError on invalid input.
    """
    return (end - start).days

def dateDiffDays(startDateText, endDateText, fmt="%Y-%m-%d"):
    """
    Difference in days between two date strings.
    Raises ValueError on invalid input.
    """
    start = datetime.strptime(startDateText, fmt).date()
    end   = datetime.strptime(endDateText, fmt).date()
    return (end - start).days


def dateDiffYears(startDateText, endDateText, fmt="%Y-%m-%d"):
    """
    Difference in integer years between two dates.
    Raises ValueError on invalid input.
    """
    start = datetime.strptime(startDateText, fmt).date()
    end   = datetime.strptime(endDateText, fmt).date()
    return end.year - start.year

def calcPercentile(data, ptile):
    """
    Calculate the P-th percentile of a dataset via linear interpolation,
    mirroring the VBA CalcPercentile logic (where ptile is 0–100).

    Parameters
    ----------
    data : list of float
        The sample values.
    ptile : float
        Desired percentile (0 to 100).

    Returns
    -------
    float
        The interpolated percentile value, or globalMissingCode if data is empty.

    Examples
    --------
    >>> calcPercentile([10, 20, 30], 50)
    20.0
    >>> calcPercentile([10, 20, 30], 90)
    28.0  # 1 + 90*(2)/100 = 2.8 → lower=2, upper=3 → 20 + (30-20)*0.8 = 28
    """
    n = len(data)
    if n == 0:
        return globalMissingCode
    if n == 1:
        return data[0]

    # sort ascending
    x = sorted(data)

    # position in 1-based indexing
    pos = 1 + ptile * (n - 1) / 100.0
    lower = int(pos)
    upper = lower + 1
    # cap upper to n to avoid index overflow
    if upper > n:
        upper = n

    proportion = pos - lower
    lowerVal = x[lower - 1]
    upperVal = x[upper - 1]

    return lowerVal + (upperVal - lowerVal) * proportion

def lMoment(data, k):
    """
    Compute the k-th L‑moment of the sample `data`.

    L‑moments are defined by:
      λ₁ = mean(data)
      λ_k = sum_{l=0 to k-1} [ C(k-1, l) * C(k+l-1, l) * (–1)^(k-l-1) * b_l ]  

    where b_l is the l-th probability‑weighted moment of the same data.

    Parameters
    ----------
    data : list of float
        The sample values.
    k : int
        The order of the L‑moment (1, 2, 3, …).

    Returns
    -------
    float
        The k-th L‑moment, or globalMissingCode if:
          - data is empty,
          - k < 1,
          - any intermediate coefficient or b_l returns missing.

    Examples
    --------
    >>> sample = [10, 20, 30, 40, 50]
    >>> lMoment(sample, 1)
    30.0
    >>> lMoment(sample, 2)
    # (you can compute manually or compare with another implementation)
    """
    n = len(data)
    # invalid inputs
    if n == 0 or k < 1:
        return globalMissingCode

    # first L‑moment is the mean
    if k == 1:
        return sum(data) / n

    total = 0.0
    for l in range(k):
        coeff1 = nCk(k - 1, l)
        coeff2 = nCk(k + l - 1, l)
        sign    = (-1) ** (k - l - 1)
        moment  = bL(data, l)

        # propagate missing if any
        if (
            coeff1 == globalMissingCode or
            coeff2 == globalMissingCode or
            sign   == globalMissingCode or
            moment == globalMissingCode
        ):
            return globalMissingCode

        total += coeff1 * coeff2 * sign * moment

    return total


def increaseObsDate():
    """
    Advance the observed date by one day, accounting for leap years.

    Globals updated:
      - currentDay, currentMonth, currentYear, currentSeason

    Logic:
      1. Increment the day.
      2. If February in a leap year, allow one extra day.
      3. If day exceeds daysInMonth + leap adjustment, roll to next month.
      4. If month rolls past December, roll to January of next year.
      5. Update currentSeason via getSeason().
    """
    global currentDay, currentMonth, currentYear, currentSeason

    # 1) Next day
    currentDay += 1

    # 2) Leap adjustment
    leap = 1 if (currentMonth == 2 and isLeap(currentYear)) else 0

    # 3) Month roll‑over?
    if currentDay > daysInMonth(currentMonth, 1) + leap:
        currentMonth += 1
        currentDay = 1

    # 4) Year roll‑over?
    if currentMonth > 12:
        currentMonth = 1
        currentYear += 1

    # 5) Update season
    currentSeason = getSeason(currentMonth)


def increaseDate(currentDay, currentMonth, currentYear, currentSeason, yearLength, leapValue):
    """
    Advance the current date by one day, using a user‑defined leap‑day flag.

    Globals updated:
      - currentDay, currentMonth, currentYear, currentSeason
      - yearLength, leapValue (used to control whether to apply the leap day)

    Logic:
      1. Increment the day.
      2. If February in a leap year AND yearLength == 1, allow leapValue extra days.
      3. If day exceeds daysInMonth + leap adjustment, roll to next month.
      4. If month rolls past December, roll to January of next year.
      5. Update currentSeason via getSeason().
    """
    #global currentDay, currentMonth, currentYear, currentSeason, yearLength, leapValue

    # 1) Next day
    currentDay += 1

    # 2) Conditional leap adjustment
    leap = 0
    if currentMonth == 2 and isLeap(currentYear) and yearLength == 1:
        leap = leapValue

    # 3) Month roll‑over?
    if currentDay > daysInMonth(currentMonth, yearLength) + leap:
        currentMonth += 1
        currentDay = 1

    # 4) Year roll‑over?
    if currentMonth > 12:
        currentMonth = 1
        currentYear += 1

    # 5) Update season
    currentSeason = getSeason(currentMonth)

    return currentDay, currentMonth, currentYear, currentSeason, yearLength, leapValue

def calcGEVValue(beta, eta, kay, year):
    """
    Calculate the Generalized Extreme Value (GEV) return level for a given year.

    Implements the VB steps:
      1. pr     = 1 / year
      2. result = -ln(1 - pr)
      3. result = kay * ln(result)
      4. result = 1 - exp(result)
      5. result = (result * beta) / kay
      6. result = result + eta

    Returns:
        float: The GEV value, or globalMissingCode if inputs are invalid
               (e.g. year < 2, log of non-positive, division by zero, etc.).
    """
    # only valid for return periods ≥ 2
    if year < 2:
        return globalMissingCode

    try:
        pr = 1.0 / year
        # step 2
        tmp = 1.0 - pr
        if tmp <= 0.0:
            return globalMissingCode
        result = -math.log(tmp)
        # step 3
        if result <= 0.0:
            return globalMissingCode
        result = kay * math.log(result)
        # step 4
        result = 1.0 - math.exp(result)
        # step 5 & 6
        return (result * beta) / kay + eta

    except (ValueError, ZeroDivisionError):
        return globalMissingCode
    

def calcGEVSmallKay(beta, eta, year):
    """
    Calculate the GEV return level for small shape parameter (κ→0) via a
    limiting form of the full GEV formula.

    VB steps:
      1. pr     = 1 / year
      2. result = –ln(1 – pr)
      3. result = –ln(result) * beta
      4. result = result + eta

    Returns:
        float: The computed value, or globalMissingCode if inputs are invalid
               (e.g. year < 2, log of non‑positive, division by zero, etc.).
    """
    # only valid for return periods ≥ 2
    if year < 2:
        return globalMissingCode

    try:
        pr = 1.0 / year

        # Step 2: first log must be of a strictly positive argument
        a = 1.0 - pr
        if a <= 0.0:
            return globalMissingCode
        tmp = -math.log(a)

        # Step 3: second log must also be of a strictly positive argument
        if tmp <= 0.0:
            return globalMissingCode
        result = -math.log(tmp) * beta

        # Step 4: add the location parameter
        return result + eta

    except (ValueError, ZeroDivisionError):
        return globalMissingCode
    
def calcStretchedValue(cValue, year, r0, pWet):
    """
    Calculate the stretched‑exponential return level.

    Implements the VB steps exactly:
      1. pr      = 1 / (pWet * year * 365.25)
      2. result  = –ln(pr)
      3. result  = result**(1/cValue)
      4. result  = result * r0

    Returns:
        float: stretched value, or globalMissingCode on error.
    """
    try:
        pr = 1.0 / (pWet * year * 365.25)
        tmp = -math.log(pr)
        # exponent must be positive
        val = tmp ** (1.0 / cValue)
        return val * r0
    except Exception:
        return globalMissingCode

def doWeWantThisDatum(datesComboIndex, currentMonth):
    """
    Decide if data for the given month should be used, based on user selection.

    Parameters
    ----------
    datesComboIndex : int
        0   → Annual (accept all months)
        1–12 → Specific month
        13  → Winter (Dec, Jan, Feb)
        14  → Spring (Mar, Apr, May)
        15  → Summer (Jun, Jul, Aug)
        16  → Autumn (Sep, Oct, Nov)
    currentMonth : int (1–12)

    Returns
    -------
    bool
        True if data for currentMonth should be included.
    """
    # Annual
    if datesComboIndex == 0:
        return True

    # Specific month
    if 1 <= datesComboIndex <= 12:
        return currentMonth == datesComboIndex

    # Seasons
    if datesComboIndex == 13:  # Winter: Dec, Jan, Feb
        return currentMonth in (12, 1, 2)
    if datesComboIndex == 14:  # Spring: Mar, Apr, May
        return currentMonth in (3, 4, 5)
    if datesComboIndex == 15:  # Summer: Jun, Jul, Aug
        return currentMonth in (6, 7, 8)
    if datesComboIndex == 16:  # Autumn: Sep, Oct, Nov
        return currentMonth in (9, 10, 11)

    # Anything else → exclude
    return False


def fsDateOk(fsDate: date, feDate: date, backupFsDate: date):
    """
    Validate the analysis start date.
    
    Returns (isValid, correctedFsDate, noOfDays):
      - isValid         : bool
      - correctedFsDate : either fsDate (if valid) or backupFsDate
      - noOfDays        : integer days between fsDate and feDate (inclusive), or None
    """
    # 1) Type check
    if not isinstance(fsDate, date):
        return False, backupFsDate, None

    # 2) Chronology
    delta = (feDate - fsDate).days
    if delta < 0:
        return False, backupFsDate, None

    # 3) ≤150 years
    years = feDate.year - fsDate.year
    if (feDate.month, feDate.day) < (fsDate.month, fsDate.day):
        years -= 1
    if years > 150:
        return False, backupFsDate, None

    # 4) All good
    return True, fsDate, delta + 1


def feDateOk(fsDate: date, feDate: date, backupFeDate: date):
    """
    Validate the analysis end date.
    
    Returns (isValid, correctedFeDate, noOfDays):
      - isValid         : bool
      - correctedFeDate : either feDate (if valid) or backupFeDate
      - noOfDays        : integer days between fsDate and feDate (inclusive), or None
    """
    # 1) Type check
    if not isinstance(feDate, date):
        return False, backupFeDate, None

    # 2) Chronology
    delta = (feDate - fsDate).days
    if delta < 0:
        return False, backupFeDate, None

    # 3) ≤150 years
    years = feDate.year - fsDate.year
    if (feDate.month, feDate.day) < (fsDate.month, fsDate.day):
        years -= 1
    if years > 150:
        return False, backupFeDate, None

    # 4) All good
    return True, feDate, delta + 1


def ensembleNumberOK(ensembleOptionSelected, ensembleNumberText, ensembleWanted):
    """
    Validate the ensemble‐member input.

    Parameters
    ----------
    ensembleOptionSelected : bool
        True if the “use ensemble” option is active.
    ensembleNumberText : str
        The text the user entered for the ensemble member.
    ensembleWanted : str
        Backup text to revert to if the entry is invalid.

    Returns
    -------
    tuple
        (is_valid, correctedText, updatedWanted)
        - is_valid (bool): True if either option is off or the entry is 1–100 whole number.
        - correctedText (str): The ensembleNumberText coerced to an integer string, or ensembleWanted.
        - updatedWanted (str): The new “wanted” value on success, or unchanged backup on failure.
    """
    # If the ensemble option isn’t on, we don’t need to validate
    if not ensembleOptionSelected:
        return True, ensembleNumberText, ensembleWanted

    # Try parse to float
    try:
        val = float(ensembleNumberText)
    except (ValueError, TypeError):
        # non‑numeric
        return False, ensembleWanted, ensembleWanted

    # Must be between 1 and 100
    if val < 1 or val > 100:
        return False, ensembleWanted, ensembleWanted

    # Coerce to integer string
    valInt = int(val)
    txt = str(valInt)
    return True, txt, txt

def stripMissing(freqAnalData, obsYears, modYears, noOfXCols):
    """
    Strips missing data from the frequency analysis matrix.
    
    Parameters:
        freqAnalData (list of lists): 
            2D array where each row is:
              [rp, obs, mod, lowerPct, upperPct, ...] or flattened into 8 cols.
        obsYears (int): number of observed‐years rows in freqAnalData.
        modYears (int): number of modelled‐years rows in freqAnalData.
        noOfXCols (int): if 8, percentiles are present.
    
    Returns:
        tuple: (newFreqAnalData, totalCount)
    """
    # 1) allocate workingMatrix
    maxRows = obsYears + modYears
    workingMatrix = [[globalMissingCode]*5 for _ in range(maxRows)]
    
    # 2) fill observed rows
    for i in range(obsYears):
        workingMatrix[i][0] = freqAnalData[i][0]  # return period
        workingMatrix[i][1] = freqAnalData[i][1]  # observed
        # mod stays missing
        if noOfXCols == 8:
            workingMatrix[i][3] = workingMatrix[i][4] = globalMissingCode
    
    # 3) fill modelled rows
    for i in range(modYears):
        outIdx = obsYears + i
        src = freqAnalData[outIdx]
        workingMatrix[outIdx][0] = src[2]         # return period from col 3
        workingMatrix[outIdx][2] = src[3]         # modelled from col 4
        # obs stays missing
        if noOfXCols == 8:
            workingMatrix[outIdx][3] = src[5]     # lower% from col 6
            workingMatrix[outIdx][4] = src[7]     # upper% from col 8
    
    # 4) sort by return period descending
    workingMatrix.sort(key=lambda row: row[0], reverse=False)
    
    # 5) collapse duplicates
    workingMatrix2 = []
    prevRp = None
    for row in workingMatrix:
        rp = row[0]
        if rp == prevRp:
            last = workingMatrix2[-1]
            # merge obs/mod
            if last[1] == globalMissingCode and row[1] != globalMissingCode:
                last[1] = row[1]
            if last[2] == globalMissingCode and row[2] != globalMissingCode:
                last[2] = row[2]
            if noOfXCols == 8:
                if last[3] == globalMissingCode and row[3] != globalMissingCode:
                    last[3] = row[3]
                if last[4] == globalMissingCode and row[4] != globalMissingCode:
                    last[4] = row[4]
        else:
            workingMatrix2.append(row.copy())
            prevRp = rp
    
    totalCount = len(workingMatrix2)
    
    # 6) build new frequency array
    newCols = 8 if noOfXCols == 8 else 4
    newFreqAnalData = [[globalMissingCode]*newCols for _ in range(totalCount)]
    
    for i, row in enumerate(workingMatrix2):
        newFreqAnalData[i][0] = row[0]            # col 1 = rp
        newFreqAnalData[i][1] = row[1]            # col 2 = obs
        newFreqAnalData[i][2] = row[0]            # col 3 = rp
        newFreqAnalData[i][3] = row[2]            # col 4 = mod
        if newCols == 8:
            newFreqAnalData[i][4] = row[0]        # col 5 = rp
            newFreqAnalData[i][5] = row[3]        # col 6 = lower%
            newFreqAnalData[i][6] = row[0]        # col 7 = rp
            newFreqAnalData[i][7] = row[4]        # col 8 = upper%
    
    return newFreqAnalData, totalCount

def empiricalAnalysis(
    observedData,
    modelledData,
    noOfObserved,
    noOfEnsembles,
    noOfModelledList,
    endOfSection,
    useThresh,
    thresh,
    file1Used,
    file2Used,
    defaultDir,
    noOfXCols,
    file2ColStart,
    percentileWanted
):
    """
    Performs the empirical analysis, producing a return-period vs. annual-max matrix
    for observed and modelled ensemble data.

    Returns:
        (success: bool, freqAnalData: list[list], noOfXDataPoints: int)
    """
    try:
        # (A) Prepare annual-max storage
        obsMaxSeries = []
        modMaxSeries = [[] for _ in range(noOfEnsembles)]

        obsYearsAvailable = 0
        modYearsAvailable = 0
        minModYearsAvailable = float('inf')
        maxModYearsAvailable = 0

        # (B) Extract observed annual maxima
        if file1Used:
            yearCounter = 0
            yearMax = -12344
            for i in range(noOfObserved):
                val = observedData[i]
                if val == endOfSection:
                    if yearMax != -12344:
                        yearCounter += 1
                        obsMaxSeries.append(yearMax)
                    yearMax = -12344
                else:
                    if useThresh == 0 or (useThresh == 1 and val > thresh):
                        if val != globalMissingCode and val > yearMax:
                            yearMax = val
            obsYearsAvailable = yearCounter
            if obsYearsAvailable < 10:
                return False, None, 0

        # (C) Extract modelled annual maxima
        if file2Used:
            for j in range(noOfEnsembles):
                yearCounter = 0
                yearMax = -12344
                for i in range(noOfModelledList[j]):
                    val = modelledData[j][i]
                    if val == endOfSection:
                        if yearMax != -12344:
                            yearCounter += 1
                            modMaxSeries[j].append(yearMax)
                        yearMax = -12344
                    else:
                        if useThresh == 0 or (useThresh == 1 and val > thresh):
                            if val != globalMissingCode and val > yearMax:
                                yearMax = val
                maxModYearsAvailable = max(maxModYearsAvailable, yearCounter)
                minModYearsAvailable = min(minModYearsAvailable, yearCounter)

            modYearsAvailable = maxModYearsAvailable
            if modYearsAvailable < 10:
                return False, None, 0
            if maxModYearsAvailable != minModYearsAvailable:
                return False, None, 0

        # (D) Determine how many rows we’ll output
        maxYearsAvailable = max(obsYearsAvailable, modYearsAvailable)

        # Prepare containers
        sortingMatrix = [[None] for _ in range(maxYearsAvailable)]
        freqAnalData = [[None] * noOfXCols for _ in range(maxYearsAvailable)]
        noOfXDataPoints = maxYearsAvailable

        # (E) Fill in observed return-period vs max
        if file1Used:
            for i in range(obsYearsAvailable):
                sortingMatrix[i][0] = obsMaxSeries[i]
            sortedObs = sorted(sortingMatrix[:obsYearsAvailable],
                               key=lambda r: r[0],
                               reverse=True)
            for idx, row in enumerate(sortedObs):
                freqAnalData[idx][0] = obsYearsAvailable / (idx + 1)
                freqAnalData[idx][1] = row[0]

        # (F) Fill in modelled + percentiles
        if file2Used:
            # File-output block left in place but disabled
            if False:
                drive = os.path.splitdrive(defaultDir)[0]
                tempFile = os.path.join(drive + os.sep, "SDSMEmpResults.txt")
                with open(tempFile, "w") as fout:
                    fout.write("Empirical Results\n\t\t\t\tReturn Period\nEnsemble\t")
                    for y in range(modYearsAvailable, 0, -1):
                        fout.write(f"{round(modYearsAvailable / y, 1)}\t")
                    fout.write("\n")
                    # … etc. …

            # Compute medians & return periods
            for i in range(modYearsAvailable):
                series_i = [modMaxSeries[j][i] for j in range(noOfEnsembles)]
                # median
                freqAnalData[i][file2ColStart - 1] = calcPercentile(series_i, 50)
                # return period
                freqAnalData[i][file2ColStart - 2] = modYearsAvailable / (i + 1)

                # percentile bounds
                if noOfEnsembles > 1 and percentileWanted > 0:
                    upp = calcPercentile(series_i, 100 - percentileWanted / 2)
                    low = calcPercentile(series_i, percentileWanted / 2)
                    if upp != globalMissingCode and low != globalMissingCode:
                        rp = modYearsAvailable / (i + 1)
                        freqAnalData[i][file2ColStart]     = upp
                        freqAnalData[i][file2ColStart - 3] = low
                        freqAnalData[i][file2ColStart - 1] = rp
                        freqAnalData[i][file2ColStart - 4] = rp

        # (G) “Pack” if one series is shorter
        if file1Used and file2Used:
            if modYearsAvailable > obsYearsAvailable:
                last = freqAnalData[obsYearsAvailable - 1]
                for k in range(modYearsAvailable - obsYearsAvailable):
                    freqAnalData[obsYearsAvailable + k][0] = last[0]
                    freqAnalData[obsYearsAvailable + k][1] = last[1]
            elif obsYearsAvailable > modYearsAvailable:
                last = freqAnalData[modYearsAvailable - 1]
                for k in range(obsYearsAvailable - modYearsAvailable):
                    freqAnalData[modYearsAvailable + k][0] = last[0]
                    freqAnalData[modYearsAvailable + k][1] = last[1]

        return True, freqAnalData, noOfXDataPoints

    except Exception:
        return False, None, 0

if __name__ == "__main__":
    # --- PARAMETERS FOR TEST ---
    endOfSection     = None
    useThresh        = 0
    thresh           = 0.0
    file1Used        = True
    file2Used        = True
    defaultDir       = "C:\\"
    noOfXCols        = 4
    file2ColStart    = 3   # so columns are: [0]=RP_obs, [1]=max_obs, [2]=RP_mod, [3]=max_mod
    percentileWanted = 90

    # --- SYNTHETIC OBSERVED DATA: 5 YEARS ---
    observedData = []
    for year in range(1, 13):
        # make daily-values so that the max of each “year” is exactly year*100
        for day in range(365):
            observedData.append(year * 100 - day)
        observedData.append(endOfSection)
    noOfObserved = len(observedData)

    # --- SYNTHETIC MODELLED DATA: 2 ENSEMBLES, SAME STRUCTURE ---
    modelledData    = []
    noOfModelledList = []
    for ensemble in range(2):
        seq = []
        for year in range(1, 13):
            for day in range(365):
                # give a slight offset per ensemble
                seq.append(year * 100 + ensemble - day)
            seq.append(endOfSection)
        modelledData.append(seq)
        noOfModelledList.append(len(seq))
    noOfEnsembles = len(modelledData)

    # --- CALL THE FUNCTION ---
    success, freqMat, rows = empiricalAnalysis(
        observedData,
        modelledData,
        noOfObserved,
        noOfEnsembles,
        noOfModelledList,
        endOfSection,
        useThresh,
        thresh,
        file1Used,
        file2Used,
        defaultDir,
        noOfXCols,
        file2ColStart,
        percentileWanted
    )

    # --- PRINT RESULTS ---
    print(f"Success: {success}")
    print(f"Rows:    {rows}")
    print(" RP_obs | max_obs | RP_mod | max_mod")
    print("--------------------------------------")
    if success:
        for row in freqMat:
            print(f"{row[0]:7.2f} | {row[1]:7.2f} | {row[2]:7.2f} | {row[3]:7.2f}")
    else:
        print("→ empiricalAnalysis returned False; no data to display.")
