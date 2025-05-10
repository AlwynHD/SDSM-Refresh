import math
from math import gamma
import configparser
from datetime import datetime, date
import os
from collections import defaultdict
import numpy as np
from typing import List, Tuple, Optional

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


def increaseObsDate(currentDay, currentMonth, currentYear, currentSeason):
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
    #global currentDay, currentMonth, currentYear, currentSeason

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

    return currentDay, currentMonth, currentYear, currentSeason


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
    Strips missing data from the frequency analysis matrix,
    mirroring the VB StripMissing logic exactly.
    
    Parameters:
        freqAnalData (list of lists): side-by-side [rp, obs, mod, lowerPct, upperPct, ...]
        obsYears (int): number of observed-year rows
        modYears (int): number of modelled-year rows
        noOfXCols (int): total columns in freqAnalData (4 or 8)
    
    Returns:
        (newFreqAnalData, totalCount)
    """
    maxRows = obsYears + modYears
    # 1) allocate workingMatrix[maxRows][5]
    workingMatrix = [[globalMissingCode]*5 for _ in range(maxRows)]
    
    # 2) fill observed rows
    for i in range(obsYears):
        workingMatrix[i][0] = freqAnalData[i][0]  # RP
        workingMatrix[i][1] = freqAnalData[i][1]  # Obs
        # Mod stays missing (globalMissingCode)
        if noOfXCols == 8:
            workingMatrix[i][3] = globalMissingCode
            workingMatrix[i][4] = globalMissingCode
    
    # 3) fill modelled rows (note: src from freqAnalData[i], not [obsYears+i])
    for i in range(modYears):
        outIdx = obsYears + i
        src = freqAnalData[i]
        workingMatrix[outIdx][0] = src[2]  # RP from mod column
        workingMatrix[outIdx][2] = src[3]  # Mod
        # Obs stays missing
        if noOfXCols == 8:
            workingMatrix[outIdx][3] = src[5]  # lower%
            workingMatrix[outIdx][4] = src[7]  # upper%
    
    # 4) sort by RP descending
    workingMatrix.sort(key=lambda row: row[0], reverse=True)
    
    # 5) collapse duplicates, merging Obs/Mod into the same RP row
    workingMatrix2 = []
    prevRp = None
    for row in workingMatrix:
        rp = row[0]
        if rp == prevRp:
            last = workingMatrix2[-1]
            # if last.obs missing, fill from this row
            if last[1] == globalMissingCode and row[1] != globalMissingCode:
                last[1] = row[1]
            # if last.mod missing, fill from this row
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
    
    # 6) rebuild into newFreqAnalData with VB's column layout
    newCols = 8 if noOfXCols == 8 else 4
    newFreqAnalData = [[globalMissingCode]*newCols for _ in range(totalCount)]
    for i, row in enumerate(workingMatrix2):
        newFreqAnalData[i][0] = row[0]  # RP
        newFreqAnalData[i][1] = row[1]  # Obs
        newFreqAnalData[i][2] = row[0]  # RP
        newFreqAnalData[i][3] = row[2]  # Mod
        if newCols == 8:
            newFreqAnalData[i][4] = row[0]  # RP
            newFreqAnalData[i][5] = row[3]  # lower%
            newFreqAnalData[i][6] = row[0]  # RP
            newFreqAnalData[i][7] = row[4]  # upper%
    
    return newFreqAnalData, totalCount

def empiricalAnalysis(
    obsDates, observedData,
    modDatesList, modelledData,
    noOfEnsembles,
    useThresh, thresh,
    file1Used, file2Used,
    defaultDir,
    noOfXCols, file2ColStart,
    percentileWanted,
    globalMissingCode
):
    """
    Calculates the empirical return‐period vs. annual‐max table,
    matching the VB EmpiricalAnalysis exactly: skips empty years,
    sorts each ensemble descending, uses nearest‐rank percentiles,
    and duplicates RP next to every statistic column.
    Returns (success: bool, freqAnalData: List[List], noOfXDataPoints: int).
    """
    try:
        # 1) OBSERVED: bucket by calendar year
        if file1Used:
            byYear = defaultdict(lambda: -12344)
            for dt, val in zip(obsDates, observedData):
                if (useThresh == 0 or val > thresh) and val != globalMissingCode:
                    y = dt.year
                    if val > byYear[y]:
                        byYear[y] = val
            # skip any year with no valid days
            obsMaxSeries = [v for v in byYear.values() if v != -12344]
            obsYearsAvailable = len(obsMaxSeries)
            if obsYearsAvailable < 10:
                return False, None, 0
        else:
            obsYearsAvailable = 0

        # 2) MODELLED: same, per ensemble, then sort descending
        if file2Used:
            modMaxSeries = [[] for _ in range(noOfEnsembles)]
            yearCounts = []
            for j in range(noOfEnsembles):
                byYear = defaultdict(lambda: -12344)
                for dt, val in zip(modDatesList[j], modelledData[j]):
                    if (useThresh == 0 or val > thresh) and val != globalMissingCode:
                        y = dt.year
                        if val > byYear[y]:
                            byYear[y] = val
                series = [v for v in byYear.values() if v != -12344]
                series.sort(reverse=True)              # ← match VB.SortRows Descending
                modMaxSeries[j] = series
                yearCounts.append(len(series))

            maxModYears = max(yearCounts)
            minModYears = min(yearCounts)
            if maxModYears < 10 or maxModYears != minModYears:
                return False, None, 0
            modYearsAvailable = maxModYears
        else:
            modYearsAvailable = 0

        # 3) Prepare output matrix
        maxYears = max(obsYearsAvailable, modYearsAvailable)
        freqAnalData = [[None]*noOfXCols for _ in range(maxYears)]
        noOfXDataPoints = maxYears

        # 4) Fill observed columns (RP & max)
        if file1Used:
            sortedObs = sorted(obsMaxSeries, reverse=True)
            for i, v in enumerate(sortedObs):
                freqAnalData[i][0] = obsYearsAvailable / (i+1)
                freqAnalData[i][1] = v

        # 5) Fill modelled columns (RP, median, Upper, Lower),
        #    duplicating RP next to each statistic
        if file2Used:
            # compute Python indices for VB columns
            rp_idx1 = file2ColStart - 2       # VB: File2ColStart-1
            med_idx  = file2ColStart - 1       # VB: File2ColStart
            up_idx   = file2ColStart + 1       # VB: File2ColStart+2
            rp_idx2  = file2ColStart           # VB: File2ColStart+1
            rp_idx3  = file2ColStart + 2       # VB: File2ColStart+3
            lo_idx   = file2ColStart + 3       # VB: File2ColStart+4

            for i in range(modYearsAvailable):
                yearVals = [modMaxSeries[j][i] for j in range(noOfEnsembles)]
                rp  = modYearsAvailable / (i+1)
                med = calcPercentile(yearVals, 50)

                # write RP & median
                freqAnalData[i][rp_idx1] = rp
                freqAnalData[i][med_idx]  = med
                
                if noOfEnsembles > 1 and percentileWanted:
                    up = calcPercentile(yearVals, 100 - percentileWanted/2)
                    lo = calcPercentile(yearVals,     percentileWanted/2)
                    # write upper bound + its RP
                    freqAnalData[i][up_idx]  = up
                    freqAnalData[i][rp_idx2] = rp
                    # write lower bound + its RP
                    freqAnalData[i][lo_idx]  = lo
                    freqAnalData[i][rp_idx3] = rp

        # 6) Pad the shorter series so plots stay continuous
        if file1Used and file2Used:
            if modYearsAvailable > obsYearsAvailable:
                lastObs = freqAnalData[obsYearsAvailable-1][:2]
                for k in range(modYearsAvailable - obsYearsAvailable):
                    freqAnalData[obsYearsAvailable + k][0:2] = lastObs
            elif obsYearsAvailable > modYearsAvailable:
                lastMod = freqAnalData[modYearsAvailable-1][:2]
                for k in range(obsYearsAvailable - modYearsAvailable):
                    freqAnalData[modYearsAvailable + k][0:2] = lastMod

        return True, freqAnalData, noOfXDataPoints

    except Exception:
        return False, None, 0

def gevAnalysis(
    obsDates, observedData,
    modDatesList, modelledData,
    noOfEnsembles,
    useThresh, thresh,
    file1Used, file2Used,
    defaultDir,
    noOfXCols, file2ColStart,
    percentileWanted,
    globalMissingCode
):
    """
    GEV analysis on observed and modelled AMS.
    Returns (success, freqAnalData, noOfXDataPoints).
    """
    try:
        # ----- (A) OBSERVED: bucket by calendar year
        if file1Used:
            byYear = defaultdict(lambda: globalMissingCode)
            for dt, v in zip(obsDates, observedData):
                if v != globalMissingCode and (useThresh == 0 or v >= thresh):
                    y = dt.year
                    if v > byYear[y]:
                        byYear[y] = v
            obsMaxSeries = [val for val in byYear.values() if val != globalMissingCode]
            obsYearsAvailable = len(obsMaxSeries)
            if obsYearsAvailable < 3:
                return False, None, 0, None, None, None
        else:
            obsYearsAvailable = 0

        # ----- (B) MODELLED: same, per ensemble
        if file2Used:
            ModMaxSeries = []
            MinModAvailable = float('inf')
            for j in range(noOfEnsembles):
                byYear = defaultdict(lambda: globalMissingCode)
                for dt, v in zip(modDatesList[j], modelledData[j]):
                    if v != globalMissingCode and (useThresh == 0 or v >= thresh):
                        y = dt.year
                        if v > byYear[y]:
                            byYear[y] = v
                series = [val for val in byYear.values() if val != globalMissingCode]
                ModMaxSeries.append(series)
                count = len(series)
                MinModAvailable = min(MinModAvailable, count)
                if count < 3:
                    return False, None, 0, None, None, None

            noOfXDataPoints = 10 + (2 if MinModAvailable > 100 else 0)
        else:
            ModMaxSeries = []
            noOfXDataPoints = 10

        # ----- (C) set up return periods & output matrix
        returnPeriods = [2,3,4,5,10,15,20,30,50,100]
        if noOfXDataPoints == 12:
            returnPeriods += [500,1000]
        freqAnalData = [[None]*noOfXCols for _ in range(noOfXDataPoints)]
        for i, rp in enumerate(returnPeriods):
            freqAnalData[i][0] = rp

        # ----- (D) OBSERVED: fit GEV to obsMaxSeries
        if file1Used:
            LM1 = lMoment(obsMaxSeries, 1)
            LM2 = lMoment(obsMaxSeries, 2)
            LM3 = lMoment(obsMaxSeries, 3)
            if 0 in (LM1, LM2, LM3):
                return False, None, 0, None, None, None

            zed = 3 + (LM3/LM2)
            zed = 2/zed - (math.log(2)/math.log(3))
            kay = 7.859*zed + 2.9554*(zed**2)

            if abs(kay) > 0.005:
                gammaVal = gamma(1 + kay)
                if gammaVal in (0, globalMissingCode):
                    return False, None, 0, None, None, None
                beta = (LM2*kay)/((1 - 2**(-kay))*gammaVal)
                eta  = beta*(gammaVal - 1)/kay + LM1
                for idx, rp in enumerate(returnPeriods):
                    freqAnalData[idx][1] = calcGEVValue(beta, eta, kay, rp)
            else:
                beta = LM2/math.log(2)
                eta  = LM1 - (0.557215665*LM2/math.log(2))
                for idx, rp in enumerate(returnPeriods):
                    freqAnalData[idx][1] = calcGEVSmallKay(beta, eta, rp)

        # ----- (E) MODELLED: fit each ensemble, then aggregate
        if file2Used:
            # 1) per-ensemble GEV curves
            ModYearsData = [[None]*len(returnPeriods) for _ in range(noOfEnsembles)]
            for j, series in enumerate(ModMaxSeries):
                LM1 = lMoment(series, 1)
                LM2 = lMoment(series, 2)
                LM3 = lMoment(series, 3)
                if 0 in (LM1, LM2, LM3):
                    return False, None, 0

                zed = 3 + (LM3/LM2)
                zed = 2/zed - (math.log(2)/math.log(3))
                kay = 7.859*zed + 2.9554*(zed**2)

                if abs(kay) > 0.005:
                    gammaVal = gamma(1 + kay)
                    if gammaVal in (0, globalMissingCode):
                        return False, None, 0, None, None, None
                    beta = (LM2*kay)/((1 - 2**(-kay))*gammaVal)
                    eta  = beta*(gammaVal - 1)/kay + LM1
                    for idx, rp in enumerate(returnPeriods):
                        ModYearsData[j][idx] = calcGEVValue(beta, eta, kay, rp)
                else:
                    beta = LM2/math.log(2)
                    eta  = LM1 - (0.557215665*LM2/math.log(2))
                    for idx, rp in enumerate(returnPeriods):
                        ModYearsData[j][idx] = calcGEVSmallKay(beta, eta, rp)

            # 2) aggregate into median & percentile columns
            med_idx = file2ColStart - 1
            up_idx  = file2ColStart + 1
            lo_idx  = file2ColStart + 3

            for idx in range(len(returnPeriods)):
                vals = [ModYearsData[j][idx] for j in range(noOfEnsembles)]
                freqAnalData[idx][med_idx] = calcPercentile(vals, 50)
                if noOfEnsembles > 1 and percentileWanted:
                    freqAnalData[idx][up_idx] = calcPercentile(vals, 100 - (percentileWanted/2))
                    freqAnalData[idx][lo_idx] = calcPercentile(vals,     percentileWanted/2)

        # ----- (F) duplicate RP in extra stat columns
        if noOfXCols > 2:
            for col in range(2, noOfXCols, 2):
                for i, rp in enumerate(returnPeriods):
                    freqAnalData[i][col] = rp

        return True, freqAnalData, noOfXDataPoints, beta, eta, kay

    except Exception:
        return False, None, 0

def gumbelAnalysis(
    obsDates, observedData,
    modDatesList, modelledData,
    noOfEnsembles,
    useThresh, thresh,
    file1Used, file2Used,
    defaultDir,
    noOfXCols, file2ColStart,
    percentileWanted,
    globalMissingCode
):
    """
    Performs Gumbel analysis on observed and modelled AMS using calendar-year bucketing.

    Returns:
        (success: bool, freqAnalData: List[List], noOfXDataPoints: int)
    """
    try:
        # (A) Extract observed AMS by calendar year
        if file1Used:
            byYear = defaultdict(lambda: globalMissingCode)
            for dt, v in zip(obsDates, observedData):
                if v != globalMissingCode and (useThresh == 0 or v >= thresh):
                    y = dt.year
                    if v > byYear[y]:
                        byYear[y] = v
            obsMaxSeries = [val for val in byYear.values() if val != globalMissingCode]
            if len(obsMaxSeries) < 3:
                print("Error: need ≥3 obs years")
                return False, None, 0
            # compute observed mean & SD
            mean_obs = sum(obsMaxSeries) / len(obsMaxSeries)
            sd_obs   = math.sqrt(
                sum((x - mean_obs)**2 for x in obsMaxSeries) / (len(obsMaxSeries)-1)
            ) if len(obsMaxSeries) > 1 else 0.0
        else:
            mean_obs = sd_obs = None

        # (B) Extract modelled AMS by calendar year, per ensemble
        if file2Used:
            ModMaxSeries = []
            minModAvailable = float('inf')
            for series_dates, series_vals in zip(modDatesList, modelledData):
                byYear = defaultdict(lambda: globalMissingCode)
                for dt, v in zip(series_dates, series_vals):
                    if v != globalMissingCode and (useThresh == 0 or v >= thresh):
                        y = dt.year
                        if v > byYear[y]:
                            byYear[y] = v
                series = [val for val in byYear.values() if val != globalMissingCode]
                ModMaxSeries.append(series)
                minModAvailable = min(minModAvailable, len(series))
            if minModAvailable < 3:
                print("Error: need ≥3 mod years")
                return False, None, 0
        else:
            ModMaxSeries = []
            minModAvailable = 0

        # (C) Set up output matrix
        noOfXDataPoints = 10
        freqAnalData = [[None]*noOfXCols for _ in range(noOfXDataPoints)]
        fixedRPs = [2,3,4,5,10,15,20,30,50,100]
        for i, rp in enumerate(fixedRPs):
            freqAnalData[i][0] = rp

        # (D) Populate observed flood-event estimates
        if file1Used:
            multipliers = [
                -0.16427, 0.25381, 0.52138, 0.71946,
                 1.30456, 1.63467, 1.86581, 2.18868,
                 2.59229, 3.13668
            ]
            for i, m in enumerate(multipliers):
                freqAnalData[i][1] = mean_obs + sd_obs * m

        # (E) Process modelled flood-event estimates and aggregate
        if file2Used:
            multipliers = [
                -0.16427, 0.25381, 0.52138, 0.71946,
                 1.30456, 1.63467, 1.86581, 2.18868,
                 2.59229, 3.13668
            ]
            modFloodEventsAll = []
            for series in ModMaxSeries:
                wm = sorted(series)
                mean_j = sum(wm) / len(wm)
                sd_j   = math.sqrt(
                    sum((x - mean_j)**2 for x in wm) / (len(wm)-1)
                ) if len(wm) > 1 else 0.0
                row = [mean_j + sd_j * m for m in multipliers]
                modFloodEventsAll.append(row)

            # median and percentile bounds across ensembles
            for i in range(noOfXDataPoints):
                vals = sorted(ens[i] for ens in modFloodEventsAll)
                m = len(vals)
                # median
                freqAnalData[i][file2ColStart - 1] = (
                    vals[m//2] if m % 2 else 0.5*(vals[m//2 - 1] + vals[m//2])
                )
                # upper / lower bounds
                if m > 1 and percentileWanted > 0:
                    high = calcPercentile(vals, 100 - percentileWanted/2)
                    low  = calcPercentile(vals, percentileWanted/2)
                    if high != globalMissingCode and low != globalMissingCode:
                        # place upper at file2ColStart+1, lower at file2ColStart+3
                        freqAnalData[i][file2ColStart + 1] = high
                        freqAnalData[i][file2ColStart + 3] = low

        # (F) Fill extra RP columns if present
        if noOfXCols > 2:
            for col in range(2, noOfXCols, 2):
                for i, rp in enumerate(fixedRPs):
                    freqAnalData[i][col] = rp

        return True, freqAnalData, noOfXDataPoints

    except Exception as e:
        #print("❌ Exception in gumbelAnalysis:", e)
        return False, None, 0

def stretchedAnalysis(
    obsDates: List,
    observedData: List[float],
    modDatesList: List[List],
    modelledData: List[List[float]],
    noOfEnsembles: int,
    useThresh: bool,
    thresh: float,
    freqThresh: float,
    file1Used: bool,
    file2Used: bool,
    defaultDir: str,
    noOfXCols: int,
    file2ColStart: int,
    percentileWanted: float,
    globalMissingCode: float,
    debug: bool = False
) -> Tuple[bool, Optional[List[List[float]]], int]:
    """
    Returns (success, freqAnalData, noOfXDataPoints).
    If debug=True you get printouts of key internals.
    """

    # 1) Filter missing / below-threshold
    if file1Used:
        obsClean = [
            v for v in observedData
            if v != globalMissingCode
               and (not useThresh or v >= thresh)
        ]
        if debug:
            print("OBS: after thresh filter:", len(obsClean), "points")
        if len(obsClean) < 10:
            return False, None, 0

    if file2Used:
        modClean = []
        for j in range(noOfEnsembles):
            thisClean = [
                v for v in modelledData[j]
                if v != globalMissingCode
                   and (not useThresh or v >= thresh)
            ]
            modClean.append(thisClean)
        if debug:
            lengths = [len(lst) for lst in modClean]
            print("MOD: ensemble lengths after thresh filter:", lengths)
        if max(len(lst) for lst in modClean) < 10:
            return False, None, 0

    # 2) Determine return‐periods and how many X‐points
    returnPeriods = [2, 3, 4, 5, 10, 15, 20, 30, 50, 100]
    noOfXDataPoints = len(returnPeriods)

    # 3) Figure out minimal needed columns
    minCols = 1                # at least the RP column
    if file1Used:
        minCols = max(minCols, 2)
    if file2Used:
        # always need median at file2ColStart
        minCols = max(minCols, file2ColStart + 1)
        # if upper & lower percentiles
        if percentileWanted > 0 and noOfEnsembles > 1:
            minCols = max(minCols, file2ColStart + 5)
    actualCols = max(noOfXCols, minCols)

    # 4) Build output array
    freqAnalData = [[0.0]*actualCols for _ in range(noOfXDataPoints)]
    for i, rp in enumerate(returnPeriods):
        freqAnalData[i][0] = float(rp)

    # 5) Observed‐only block
    if file1Used:
        totObsWet = sum(1 for v in obsClean if v > thresh)
        sumObsWet = sum(v for v in obsClean if v > thresh)
        r0 = (sumObsWet / totObsWet) if totObsWet>0 else 0.0
        prObsWet = totObsWet / len(obsClean)

        if debug:
            print(f"OBS: totObsWet={totObsWet}, R0={r0:.3f}, prObsWet={prObsWet:.3f}")

        workingObs = [v for v in obsClean if v > freqThresh]
        if len(workingObs) < 10:
            return False, None, 0
        workingObs.sort()

        nObs = len(workingObs)
        Xobs = np.ones((nObs, 2))
        yobs = np.zeros((nObs, 1))
        for j, val in enumerate(workingObs):
            N = nObs - j
            Pr = N / (totObsWet + 1)
            yobs[j, 0] = math.log(-math.log(Pr))
            Xobs[j, 1] = math.log(val / r0)

        betaObs = np.linalg.inv(Xobs.T @ Xobs) @ (Xobs.T @ yobs)
        cValueObs = float(betaObs[1, 0])
        if debug:
            print(f"OBS: cValueObs = {cValueObs:.4f}")

        for i, rp in enumerate(returnPeriods):
            freqAnalData[i][1] = calcStretchedValue(cValueObs, rp, r0, prObsWet)

    # 6) Modelled‐only block
    if file2Used:
        # collect flood‐event arrays
        modEvents = [[0.0]*noOfXDataPoints for _ in range(noOfEnsembles)]

        for j in range(noOfEnsembles):
            dataJ = modClean[j]
            totModWet = sum(1 for v in dataJ if v > thresh)
            sumModWet = sum(v for v in dataJ if v > thresh)
            r0Mod = (sumModWet / totModWet) if totModWet>0 else 0.0
            prModWet = totModWet / len(dataJ)

            workingMod = [v for v in dataJ if v > freqThresh]
            workingMod.sort()
            nMod = len(workingMod)
            if nMod < 10:
                return False, None, 0
            
            if debug:
                print(f"[ENSEMBLE #{j+1}] raw count={len(modelledData[j])}, "
                f"postThresh count={len(modClean[j])}, "
                f"totModWet={totModWet}, R0={r0Mod:.4f}, pWet={prModWet:.4f}, "
                f"workingCount={len(workingMod)}")

            Xmod = np.ones((nMod, 2))
            ymod = np.zeros((nMod, 1))
            for k, val in enumerate(workingMod):
                N = nMod - k
                Pr = N / (totModWet + 1)
                ymod[k, 0] = math.log(-math.log(Pr))
                Xmod[k, 1] = math.log(val / r0Mod)

            betaMod = np.linalg.inv(Xmod.T @ Xmod) @ (Xmod.T @ ymod)
            cValueMod = float(betaMod[1, 0])
            if debug:
                print(f"MOD #{j+1}: cValueMod = {cValueMod:.4f}")

            for i, rp in enumerate(returnPeriods):
                modEvents[j][i] = calcStretchedValue(cValueMod, rp, r0Mod, prModWet)

        # write medians and percentiles
        for i in range(noOfXDataPoints):
            row = [modEvents[j][i] for j in range(noOfEnsembles)]
            freqAnalData[i][file2ColStart-1] = calcPercentile(row, 50)
            if percentileWanted > 0 and noOfEnsembles > 1:
                freqAnalData[i][file2ColStart+1] = calcPercentile(row, 100-(percentileWanted/2))
                freqAnalData[i][file2ColStart+3] = calcPercentile(row, percentileWanted/2)

    # 7) Extra X‐columns (RP repeats)
    if actualCols > 2:
        for col in range(2, actualCols, 2):
            for i, rp in enumerate(returnPeriods):
                freqAnalData[i][col] = float(rp)

    return True, freqAnalData, noOfXDataPoints