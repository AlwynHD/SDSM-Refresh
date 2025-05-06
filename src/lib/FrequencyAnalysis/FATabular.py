import math
import numpy as np  # Optional: if you prefer using numpy.nan for missing codes
import sys
from datetime import datetime
import os

# Define a global missing code (you can change this to any value you like)
GLOBAL_MISSING_CODE = -999
EndOfSection = -99999

# Global variable to simulate a flag (equivalent to VB's GlobalKopOut)
GlobalKopOut = True

# List to store open file objects (simulating file handles)
open_file_handles = []  # In your application, add open file objects to this list.

# Temporary variables to prevent errors.
PercentileMatrix = []
File2ColStart = 0
EndOfSection = ""

class MatrixWrapper:
    def __init__(self, data):
        self.data = np.array(data)
    
    @property
    def Rows(self):
        return self.data.shape[0]
    
    def ColSum(self, col):
        return np.sum(self.data[:, col])
    
    def __getitem__(self, idx):
        return self.data[idx]
    
sortingMatrix = MatrixWrapper([[1, 2], [3, 4], [5, 6]])

def mini_reset():
    """
    Mimics the VB Mini_Reset routine without UI components:
      - Closes any open file handles.
      - Resets a global flag.
      
    Note: UI elements such as key preview settings, mouse pointer states, and progress picture 
          visibility are not handled here. Insert your own UI reset logic where indicated.
    """
    # Close any open file handles.
    for f in open_file_handles:
        try:
            f.close()
        except Exception as e:
            print(f"Error closing file: {e}", file=sys.stderr)
    # Clear the list after closing the files.
    open_file_handles.clear()
    
    # Reset the global flag.
    global GlobalKopOut
    GlobalKopOut = False
    
    # --- UI Related Actions ---
    # In the original VB code, the following UI elements would be reset:
    # Diagnostics.KeyPreview = False         # Prevent processing of escape key.
    # Diagnostics.MousePointer = 0           # Set to the ordinary mouse pointer.
    # ProgressPicture.Visible = False        # Hide the progress picture.
    # ---------------------------
    # Insert your UI reset/update code here if needed.
    
def nCk(n, k):
    """
    Compute the binomial coefficient (n choose k).

    This function mimics the VB function logic:
      - Returns GLOBAL_MISSING_CODE if n < k, n < 1, or k < 0.
      - Returns 1 if n equals k.
      - Otherwise, calculates nCk as n! / (k! * (n-k)!)
    
    Parameters:
        n (int): The total number of items.
        k (int): The number of items chosen.
    
    Returns:
        float: The computed binomial coefficient,
               or GLOBAL_MISSING_CODE if the inputs are invalid or an error occurs.
    """
    try:
        # Check for invalid conditions (matching the VB error handling)
        if (n < k) or (n < 1) or (k < 0):
            return GLOBAL_MISSING_CODE
        elif n == k:
            return 1
        # Calculate the denominator (k! * (n-k)!)
        denominator = math.factorial(k) * math.factorial(n - k)
        # Calculate and return the result as a float
        result = math.factorial(n) / denominator
        return result
    except Exception:
        # In case of an error, mimic VB's error handler:
        mini_reset()
        return GLOBAL_MISSING_CODE
    
def bL(l):
    """
    Calculate bL from Kysely 2002.

    This function computes bL based on the parameter l:
      - If l == 0, it returns the sum of the first column from sortingMatrix.
      - Otherwise, it calculates a weighted sum for each row.

    The calculation follows the VB logic:
      For each row index i (1-indexed in VB):
        Numerator = product of j for j from (i-1) downto (i-l) inclusive.
        Denom   = product of j for j from (n-1) downto (n-l) inclusive.
        Sum   += (Numerator / Denom) * sortingMatrix[i-1, 0]
      Returns bL = Sum / n

    Assumes a global object 'sortingMatrix' with:
      - sortingMatrix.Rows: number of rows.
      - sortingMatrix.ColSum(0): sum of the first column.
      - sortingMatrix[i, 0]: element at row i and column 0.
      
    In case of an error, mini_reset() is called and GLOBAL_MISSING_CODE is returned.

    Parameters:
        l (int): parameter for calculation.

    Returns:
        float: Computed bL value or GLOBAL_MISSING_CODE on error.
    """
    try:
        total_sum = 0.0
        n = sortingMatrix.Rows  # Assumes sortingMatrix is defined globally.
        
        if l == 0:
            total_sum = sortingMatrix.ColSum(0)
        else:
            # Loop over rows (using 1-index as in VB; adjust index for 0-indexing)
            for i in range(1, n + 1):
                numerator = 1.0
                # Loop from j = (i - 1) downto (i - l) (inclusive)
                for j in range(i - 1, i - l - 1, -1):
                    numerator *= j
                denominator = 1.0
                # Loop from j = (n - 1) downto (n - l) (inclusive)
                for j in range(n - 1, n - l - 1, -1):
                    denominator *= j
                # Access matrix element: VB uses (i - 1, 0) because VB is 1-indexed here.
                total_sum += (numerator / denominator) * sortingMatrix[i - 1, 0]
        return total_sum / n
    except Exception as e:
        # In case of an error, call mini_reset() and return the global missing code.
        mini_reset()
        return GLOBAL_MISSING_CODE

def gamma_func(z):
    """
    Approximates the Gamma function (Γ(z)) using the algorithm from VB:
    
      Γ(z) ≈ [ Factorial(n) * (n ** z) ] / [ z * (z + 1) * ... * (z + n) ]
      
    where n is set to 50 (a fixed value for an approximation; ideally, n→∞ for the exact result).
    
    If z equals 0, the function returns GLOBAL_MISSING_CODE.
    
    Parameters:
        z (float): Input value for which the Gamma function is computed.
    
    Returns:
        float: The approximated Gamma function value or GLOBAL_MISSING_CODE if an error occurs.
    """
    try:
        if z == 0:
            return GLOBAL_MISSING_CODE
        n = 50  # Fixed value; higher values yield a closer approximation to the true Gamma function.
        numerator = math.factorial(n) * (n ** z)
        denominator = z
        for i in range(1, n + 1):
            denominator *= (z + i)
        return numerator / denominator
    except Exception as e:
        mini_reset()
        return GLOBAL_MISSING_CODE
    
def get_season(month):
    """
    Determines the season based on the month number.

    Season mapping:
        - 1 (Winter): December, January, February
        - 2 (Spring): March, April, May
        - 3 (Summer): June, July, August
        - 4 (Autumn): September, October, November

    Parameters:
        month (int): Month number (1 through 12).

    Returns:
        int: The season corresponding to the month.
    
    Raises:
        ValueError: If the month is not between 1 and 12.
    """
    if month in [12, 1, 2]:
        return 1  # Winter
    elif month in [3, 4, 5]:
        return 2  # Spring
    elif month in [6, 7, 8]:
        return 3  # Summer
    elif month in [9, 10, 11]:
        return 4  # Autumn
    else:
        raise ValueError("Invalid month. Month must be between 1 and 12.")
    
def is_leap(year):
    """
    Standard check for a leap year.
    A year is a leap year if it is divisible by 4,
    except for years divisible by 100 but not by 400.
    
    Parameters:
        year (int): The year to test.
    
    Returns:
        bool: True if leap year, otherwise False.
    """
    return (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0))

def days(month, year_length):
    """
    Returns the number of days in a given month.  
    The parameter `year_length` can be used to modify the behavior if needed.
    
    Parameters:
        month (int): The month number (1-12).
        year_length (int): A flag used in the original VB code to adjust February days.
                           (Typically 1 indicates standard mode.)
    
    Returns:
        int: Number of days in the specified month.
    
    Note:
        For February, this function returns 28 by default.
        Leap adjustments are handled externally by the calling routines.
    """
    month_days = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30,
                  7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}
    return month_days.get(month, 31)

def is_date(date_text, fmt="%Y-%m-%d"):
    """
    Checks if a given string can be parsed as a date.
    Default format is ISO ("YYYY-MM-DD"). Change fmt if needed.
    """
    try:
        datetime.strptime(date_text, fmt)
        return True
    except ValueError:
        return False

def date_diff_days(start_date_text, end_date_text, fmt="%Y-%m-%d"):
    """
    Returns the difference in days between two date strings.
    """
    start = datetime.strptime(start_date_text, fmt)
    end = datetime.strptime(end_date_text, fmt)
    return (end - start).days

def date_diff_years(start_date_text, end_date_text, fmt="%Y-%m-%d"):
    """
    Returns the integer difference in years between two date strings.
    """
    start = datetime.strptime(start_date_text, fmt)
    end = datetime.strptime(end_date_text, fmt)
    return end.year - start.year

def calc_percentile(ptile):
    """
    Calculates the desired percentile from PercentileMatrix.
    
    The VB routine performs the following:
      - Clones the PercentileMatrix.
      - If there are no rows, returns GLOBAL_MISSING_CODE.
      - If only one row exists, returns the sole value.
      - Otherwise, sorts the matrix (ascending by column 0) and
        computes a percentile using linear interpolation between adjacent values.
    
    Parameters:
        ptile (float): The desired percentile (presumably between 0 and 100).
    
    Returns:
        float: The calculated percentile value or GLOBAL_MISSING_CODE on error.
    
    Note:
        This function assumes that the global object PercentileMatrix exists
        and implements:
          - A property .Rows that returns the number of rows.
          - A method clone() that returns a deep copy.
          - A method sort_rows(col_index) to sort rows by a specified column.
          - 2D indexing such that `matrix[i, 0]` returns the value in column 0 of row i.
    """
    try:
        # Clone the PercentileMatrix.
        matrix_clone = PercentileMatrix.clone()  
        n_rows = matrix_clone.Rows

        if n_rows == 0:
            return GLOBAL_MISSING_CODE
        elif n_rows == 1:
            return matrix_clone[0, 0]
        else:
            # Sort the matrix rows in ascending order based on column 0.
            matrix_clone.sort_rows(0)
            # Calculate the position using the formula from VB.
            # Note: VB uses 1-indexing for calculation.
            position = 1 + (ptile * (n_rows - 1) / 100.0)
            lower_bound = int(position)  # Truncate toward zero (suitable for positive numbers).
            upper_bound = lower_bound + 1
            proportion = position - lower_bound
            # Adjust indices back to 0-indexing (VB subtracts 1 from indices).
            lower_value = matrix_clone[lower_bound - 1, 0]
            upper_value = matrix_clone[upper_bound - 1, 0]
            range_val = upper_value - lower_value
            return lower_value + (range_val * proportion)
    except Exception as e:
        mini_reset()
        return GLOBAL_MISSING_CODE

def l_moment(k):
    """
    Calculates an L-moment as defined in the VB code.
    
    For k = 1, the moment is the column average of sortingMatrix (column 0).
    For k > 1, the routine sums products involving binomial coefficients,
    a power of -1, and the bL() function.
    
    Parameters:
        k (int): The order of the moment.
    
    Returns:
        float: The computed L-moment, or GLOBAL_MISSING_CODE on error.
    
    Note:
        This function assumes:
          - A global object `sortingMatrix` with properties:
              .Rows -- number of rows,
              and a method col_sum(col_index) to obtain the sum of a column.
          - The functions nCk() and bL() are available.
          - GLOBAL_MISSING_CODE, mini_reset(), and handle_error() are defined.
    """
    try:
        if k == 1:
            # Return the average of the values in the first column.
            return sortingMatrix.col_sum(0) / sortingMatrix.Rows
        else:
            total = 0.0
            # Loop over l = 0 to (k - 1)
            for l in range(0, k):
                value1 = nCk(k - 1, l)
                value2 = nCk(k + l - 1, l)
                # In VB, the ^ operator is exponentiation.
                value3 = (-1) ** (k - l - 1)
                value4 = bL(l)
                # Check if any value signals a missing-code.
                if (value1 == GLOBAL_MISSING_CODE or 
                    value2 == GLOBAL_MISSING_CODE or 
                    value3 == GLOBAL_MISSING_CODE or 
                    value4 == GLOBAL_MISSING_CODE):
                    mini_reset()
                    return GLOBAL_MISSING_CODE
                else:
                    total += value1 * value2 * value3 * value4
            return total
    except Exception as e:
        mini_reset()
        return GLOBAL_MISSING_CODE

def increase_obs_date():
    """
    Increases the current observed date.
    
    This function updates global variables CurrentDay, CurrentMonth, CurrentYear,
    and CurrentSeason based on a true calendar system (i.e. potentially including
    leap years with 366 days).
    
    VB logic:
      - Increment the day.
      - If the month is February and the year is leap, adjust the day limit.
      - If the day exceeds the number of days in the month (plus any leap day adjustment),
        increment the month and reset day to 1.
      - If the month exceeds 12, reset month to 1 and increment the year.
      - Update the season via GetSeason.
    
    Note:
      This version assumes that the following global variables are defined:
          CurrentDay, CurrentMonth, CurrentYear, CurrentSeason.
      It also assumes that:
          - is_leap(year) returns True if the year is a leap year.
          - days(month, flag) returns the number of days in a given month. (The second parameter
            is a flag; for IncreaseObsDate it is 1.)
          - get_season(month) returns an integer representing the season.
    """
    global CurrentDay, CurrentMonth, CurrentYear, CurrentSeason
    Leap = 0
    # Increment the day.
    CurrentDay += 1
    # Check for leap year in February.
    if CurrentMonth == 2:
        if is_leap(CurrentYear):
            Leap = 1
    # If the day exceeds the allowed days in the month (plus leap adjustment), increment the month.
    if CurrentDay > (days(CurrentMonth, 1) + Leap):
        CurrentMonth += 1
        CurrentDay = 1
    # If the month exceeds December, reset month and increment year.
    if CurrentMonth == 13:
        CurrentMonth = 1
        CurrentYear += 1
    # Update the season.
    CurrentSeason = get_season(CurrentMonth)

def increase_date():
    """
    Increases the current date.
    
    This function is similar to increase_obs_date() but includes a user-adjustable
    parameter for the leap day value.
    
    VB logic:
      - Increment the day.
      - If February and the year is leap, and if YearLength equals 1, then set Leap based on a
        user-specified Leapvalue.
      - If the day exceeds the allowed value (days in the month plus any leap adjustment),
        increment month and reset day.
      - If month exceeds 12, reset month and increment year.
      - Update the season via get_season().
    
    Note:
      This function relies on the following globals:
          CurrentDay, CurrentMonth, CurrentYear, CurrentSeason, YearLength, Leapvalue.
      Also required are:
          - is_leap(year): a function to determine leap years.
          - days(month, YearLength): returns the day count for the month considering YearLength.
          - get_season(month): returns an integer representing the season.
    """
    global CurrentDay, CurrentMonth, CurrentYear, CurrentSeason, YearLength, Leapvalue
    CurrentDay += 1
    Leap = 0
    if CurrentMonth == 2:
        if is_leap(CurrentYear):
            if YearLength == 1:
                Leap = Leapvalue
    if CurrentDay > (days(CurrentMonth, YearLength) + Leap):
        CurrentMonth += 1
        CurrentDay = 1
    if CurrentMonth == 13:
        CurrentMonth = 1
        CurrentYear += 1
    CurrentSeason = get_season(CurrentMonth)

def calc_gev_value(beta, eta, kay, year):
    """
    Calculates the rainfall amount from a GEV (Generalized Extreme Value) distribution
    for a given year return period.
    
    This function implements the VB logic:
      1. pr = 1 / year 
      2. result = -log(1 - pr)
      3. result = kay * log(result)
      4. result = 1 - exp(result)
      5. result = result * beta / kay
      6. result = result + eta
    
    Note: This function is only expected to be called for year >= 2.
    
    Parameters:
        beta (float): Scale parameter.
        eta (float): Location parameter.
        kay (float): Shape parameter.
        year (float): Return period in years.
    
    Returns:
        float: The calculated GEV value or GLOBAL_MISSING_CODE on error.
    """
    try:
        # Calculate probability
        pr = 1 / year  # If year==1, pr becomes 1 and subsequent log(0) will error.
        # Step-by-step calculation matching VB code:
        result = -math.log(1 - pr)
        result = kay * math.log(result)
        result = 1 - math.exp(result)
        result = (result * beta) / kay
        result = result + eta
        return result
    except Exception as e:
        mini_reset()
        return GLOBAL_MISSING_CODE

def calc_gev_small_kay(beta, eta, year):
    """
    Calculates the rainfall amount from a GEV distribution when the shape parameter Kay is small.
    
    VB logic:
      1. pr = 1 / year
      2. result = -log(1 - pr)
      3. result = -log(result) * beta
      4. result = result + eta
    
    Parameters:
        beta (float): Scale parameter.
        eta (float): Location parameter.
        year (float): Return period in years.
    
    Returns:
        float: The calculated GEV value for small kay or GLOBAL_MISSING_CODE on error.
    """
    try:
        pr = 1 / year
        result = -math.log(1 - pr)
        result = -math.log(result) * beta
        result = result + eta
        return result
    except Exception as e:
        mini_reset()
        return GLOBAL_MISSING_CODE

def calc_stretched_value(cvalue, year, r0, p_wet):
    """
    Calculates the stretched exponential value given a constant, mean rainfall (R0),
    the year (return period), and the probability of a wet day.
    
    VB logic:
      1. pr = 1 / (p_wet * year * 365.25)
      2. result = -log(pr)
      3. result = result^(1 / cvalue)    (i.e. result raised to the power of 1/cvalue)
      4. result = result * r0
    
    Parameters:
        cvalue (float): The stretching parameter.
        year (int or float): Return period (typically 1 to 100).
        r0 (float): Mean rainfall.
        p_wet (float): Probability of a wet day.
    
    Returns:
        float: The stretched value or GLOBAL_MISSING_CODE on error.
    """
    try:
        pr = 1 / (p_wet * year * 365.25)
        result = -math.log(pr)
        result = result ** (1 / cvalue)
        result = result * r0
        return result
    except Exception as e:
        mini_reset()
        return GLOBAL_MISSING_CODE

def do_we_want_this_datum(dates_combo_list_index, current_month):
    """
    Determines whether data for the current day/month/season should be used,
    based on the user’s selection (dates_combo_list_index) and the current month.
    
    Parameters:
        dates_combo_list_index (int): The user’s selection.
            - 0 indicates annual (i.e. all data).
            - 1-12 indicates a specific month.
            - 13: Winter (December, January, February)
            - 14: Spring (March, April, May)
            - 15: Summer (June, July, August)
            - 16: Autumn (September, October, November)
        current_month (int): The current month as an integer (1–12).

    Returns:
        bool: True if the current datum should be accepted; otherwise False.
    """
    if dates_combo_list_index == 0:
        return True
    elif current_month == dates_combo_list_index:
        return True
    elif dates_combo_list_index == 13:  # Winter: December, January, February
        return current_month in [12, 1, 2]
    elif dates_combo_list_index == 14:  # Spring: March, April, May
        return current_month in [3, 4, 5]
    elif dates_combo_list_index == 15:  # Summer: June, July, August
        return current_month in [6, 7, 8]
    elif dates_combo_list_index == 16:  # Autumn: September, October, November
        return current_month in [9, 10, 11]
    else:
        return False

def fe_date_ok(fs_date, fe_date, backup_fe_date):
    """
    Validates the analysis end date.
    
    Checks that fe_date is a valid date,
    that it is later than or equal to fs_date,
    and that the period does not exceed 150 years.
    
    Parameters:
        fs_date (datetime.date): Analysis start date.
        fe_date (datetime.date): Analysis end date.
        backup_fe_date (datetime.date): Backup end date to use on error.
    
    Returns:
        tuple: (is_valid, corrected_fe_date, no_of_days)
               - is_valid (bool): True if fe_date passes validation; otherwise False.
               - corrected_fe_date (datetime.date): Either fe_date if valid or backup_fe_date if invalid.
               - no_of_days (int or None): Number of days between fs_date and fe_date (inclusive) if valid; otherwise None.
    """
    try:
        # Validate that fe_date is a datetime.date instance.
        if not isinstance(fe_date, datetime.date):
            print("Analysis end date is invalid. Not a datetime.date instance.")
            return False, backup_fe_date, None
        
        # Ensure fe_date is later than or equal to fs_date.
        if (fe_date - fs_date).days < 0:
            print("Analysis end date must be later than analysis start date.")
            return False, backup_fe_date, None
        
        # Check that the period does not exceed 150 years.
        # First, compute a simple difference in years.
        years_diff = fe_date.year - fs_date.year
        # Adjust the years difference if the month/day of fe_date is earlier than that of fs_date.
        if (fe_date.month, fe_date.day) < (fs_date.month, fs_date.day):
            years_diff -= 1
        if years_diff > 150:
            print("Analysis period must be less than 150 years.")
            return False, backup_fe_date, None
        
        # Calculate the number of days (inclusive).
        no_of_days = (fe_date - fs_date).days + 1
        return True, fe_date, no_of_days

    except Exception as e:
        print("Error in fe_date_ok:", e)
        return False, backup_fe_date, None

def fs_date_ok(fs_date, fe_date, backup_fs_date):
    """
    Validates the analysis start date.
    
    Checks that fs_date is a valid date,
    that it is earlier than or equal to fe_date,
    and that the period does not exceed 150 years.
    
    Parameters:
        fs_date (datetime.date): Analysis start date.
        fe_date (datetime.date): Analysis end date.
        backup_fs_date (datetime.date): Backup start date to use on error.
    
    Returns:
        tuple: (is_valid, corrected_fs_date, no_of_days)
               - is_valid (bool): True if fs_date passes validation; otherwise False.
               - corrected_fs_date (datetime.date): Either fs_date if valid or backup_fs_date if invalid.
               - no_of_days (int or None): Number of days between fs_date and fe_date (inclusive) if valid; otherwise None.
    """
    try:
        # Validate that fs_date is a datetime.date instance.
        if not isinstance(fs_date, datetime.date):
            print("Analysis start date is invalid. Not a datetime.date instance.")
            return False, backup_fs_date, None
        
        # Ensure fs_date is earlier than or equal to fe_date.
        if (fe_date - fs_date).days < 0:
            print("Analysis start date must be earlier than analysis end date.")
            return False, backup_fs_date, None
        
        # Check that the period does not exceed 150 years.
        years_diff = fe_date.year - fs_date.year
        # Adjust if the anniversary hasn't been reached in fe_date.
        if (fe_date.month, fe_date.day) < (fs_date.month, fs_date.day):
            years_diff -= 1
        if years_diff > 150:
            print("Analysis period must be less than 150 years.")
            return False, backup_fs_date, None
        
        # Calculate the number of days (inclusive).
        no_of_days = (fe_date - fs_date).days + 1
        return True, fs_date, no_of_days
    except Exception as e:
        print("Error in fs_date_ok:", e)
        return False, backup_fs_date, None
    
def ensemble_number_ok(ensemble_option_selected, ensemble_number_text, ensemble_wanted):
    """
    Validates the ensemble member input.
    
    If the ensemble option is selected, checks that ensemble_number_text
    is numeric and between 1 and 100. If invalid, resets the value to ensemble_wanted.
    
    Parameters:
        ensemble_option_selected (bool): True if the ensemble option is active.
        ensemble_number_text (str): The entered ensemble member value.
        ensemble_wanted (str): The backup value to use if the entered value is invalid.
    
    Returns:
        tuple: (is_valid, corrected_ensemble_text, updated_ensemble_wanted)
               - is_valid (bool): True if the ensemble value is valid or ensemble not selected.
               - corrected_ensemble_text (str): The validated ensemble member text.
               - updated_ensemble_wanted (str): Updated ensemble wanted value.
    """
    # If ensemble option is not selected, nothing to validate.
    if not ensemble_option_selected:
        return True, ensemble_number_text, ensemble_wanted
    
    try:
        # Check if the input is numeric.
        value = float(ensemble_number_text)
    except (ValueError, TypeError):
        print("Ensemble member value is invalid.")
        return False, ensemble_wanted, ensemble_wanted

    if value < 1 or value > 100:
        print("Ensemble member must be between 1 and 100 (cannot be zero or greater than 100).")
        return False, ensemble_wanted, ensemble_wanted
    # Convert to an integer string.
    value_int = int(value)
    corrected_value = str(value_int)
    return True, corrected_value, corrected_value

def strip_missing(FreqAnalData, ObsYearsAvailable, ModYearsAvailable, NoOfXCols):
    """
    Strips missing data from the FreqAnalData array when observed and modelled data
    are of different lengths. This routine creates a working matrix, sorts the data,
    combines duplicate return periods, and then re-dimensions the FreqAnalData array.

    Parameters:
        FreqAnalData: 2D list representing the frequency analysis data.
                      For observed data, each row should have (at least) columns:
                          [return period, observed, ...]
                      For modelled data, each row should have (at least) columns:
                          [return period (at col 3), modelled (at col 4), ...]
                      (VB references columns 1,2,3,4,6,8 which we map to 0-indexed positions.)
        ObsYearsAvailable: int – number of observed years (rows) in FreqAnalData.
        ModYearsAvailable: int – number of modelled years.
        NoOfXCols: int – if 8 then percentile data (lower% and upper%) are used.
        
    Returns:
        A tuple (new_FreqAnalData, NoOfXDataPoints) where new_FreqAnalData is the
        re-dimensioned frequency analysis array (a list of lists) and NoOfXDataPoints
        is the number of valid data points after stripping.
    """
    try:
        # Maximum number of rows is the sum of observed and modelled rows.
        maxRows = ModYearsAvailable + ObsYearsAvailable

        # Create the first working matrix (maxRows x 5)
        # Columns: [0]=return period, [1]=observed, [2]=modelled, [3]=lower%, [4]=upper%
        workingMatrix = [[None] * 5 for _ in range(maxRows)]

        # Populate workingMatrix from observed data (first ObsYearsAvailable rows)
        # VB loop: For i = 1 To ObsYearsAvailable
        for i in range(1, ObsYearsAvailable + 1):
            idx = i - 1  # 0-indexed row
            # In VB: workingMatrix(i-1, 0) = FreqAnalData(i,1)
            workingMatrix[idx][0] = FreqAnalData[idx][0]
            # VB: workingMatrix(i-1, 1) = FreqAnalData(i,2)
            workingMatrix[idx][1] = FreqAnalData[idx][1]
            # No modelled value available for observed data.
            workingMatrix[idx][2] = GLOBAL_MISSING_CODE
            if NoOfXCols == 8:
                # Set percentiles to missing.
                workingMatrix[idx][3] = GLOBAL_MISSING_CODE
                workingMatrix[idx][4] = GLOBAL_MISSING_CODE

        # Populate workingMatrix from modelled data (next ModYearsAvailable rows)
        # VB loop: For i = 1 To ModYearsAvailable
        for i in range(1, ModYearsAvailable + 1):
            idx = (i - 1) + ObsYearsAvailable
            # VB: workingMatrix(i-1+ObsYearsAvailable, 0) = FreqAnalData(i,3)
            workingMatrix[idx][0] = FreqAnalData[i - 1][2]
            # VB: workingMatrix(i-1+ObsYearsAvailable, 2) = FreqAnalData(i,4)
            workingMatrix[idx][2] = FreqAnalData[i - 1][3]
            # No observed value available for modelled data.
            workingMatrix[idx][1] = GLOBAL_MISSING_CODE
            if NoOfXCols == 8:
                # VB: workingMatrix(i-1+ObsYearsAvailable, 3) = FreqAnalData(i,6)
                # and workingMatrix(i-1+ObsYearsAvailable, 4) = FreqAnalData(i,8)
                workingMatrix[idx][3] = FreqAnalData[i - 1][5]
                workingMatrix[idx][4] = FreqAnalData[i - 1][7]

        # Sort workingMatrix by column 0 (return period) in descending order.
        workingMatrix.sort(key=lambda row: row[0], reverse=True)

        # Create second working matrix (same dimensions initially).
        workingMatrix2 = [[None] * 5 for _ in range(maxRows)]

        # Strip out duplicate lines (combine rows with the same return period).
        TotalCount = 1
        prevRetPeriod = workingMatrix[0][0]
        # Initialize the first row.
        workingMatrix2[0] = workingMatrix[0][:]  # copy row 0

        # Loop through remaining rows.
        # VB: For i = 2 To maxRows  (i from 2 to maxRows; in Python, index 1 to maxRows-1)
        for i in range(1, maxRows):
            if workingMatrix[i][0] == prevRetPeriod:
                # Duplicate return period – decide which field to update.
                if workingMatrix[i][1] == GLOBAL_MISSING_CODE:
                    # If observed is missing, update modelled.
                    workingMatrix2[TotalCount - 1][2] = workingMatrix[i][2]
                    if NoOfXCols == 8:
                        workingMatrix2[TotalCount - 1][3] = workingMatrix[i][3]
                        workingMatrix2[TotalCount - 1][4] = workingMatrix[i][4]
                else:
                    # Otherwise update the observed value.
                    workingMatrix2[TotalCount - 1][1] = workingMatrix[i][1]
            else:
                # New return period found – add a new row.
                TotalCount += 1
                workingMatrix2[TotalCount - 1] = workingMatrix[i][:]
                if NoOfXCols == 8:
                    # (If percentiles are used, the entire row is copied.)
                    pass
                prevRetPeriod = workingMatrix[i][0]

        # Trim workingMatrix2 to only TotalCount rows.
        workingMatrix2 = workingMatrix2[:TotalCount]

        # Build the new FreqAnalData array with the appropriate dimensions.
        if NoOfXCols == 8:
            new_FreqAnalData = [[None] * 8 for _ in range(TotalCount)]
        else:
            new_FreqAnalData = [[None] * 4 for _ in range(TotalCount)]

        # Fill in new_FreqAnalData according to VB mapping.
        # VB loop: For i = 1 To TotalCount
        for i in range(1, TotalCount + 1):
            idx = i - 1
            # VB: FreqAnalData(i,1) = workingMatrix2(i-1,0)
            new_FreqAnalData[idx][0] = workingMatrix2[idx][0]
            # VB: FreqAnalData(i,2) = workingMatrix2(i-1,1)
            new_FreqAnalData[idx][1] = workingMatrix2[idx][1]
            # VB: FreqAnalData(i,3) = workingMatrix2(i-1,0)
            new_FreqAnalData[idx][2] = workingMatrix2[idx][0]
            # VB: FreqAnalData(i,4) = workingMatrix2(i-1,2)
            new_FreqAnalData[idx][3] = workingMatrix2[idx][2]
            if NoOfXCols == 8:
                # VB: FreqAnalData(i,5) = workingMatrix2(i-1,0)
                new_FreqAnalData[idx][4] = workingMatrix2[idx][0]
                # VB: FreqAnalData(i,6) = workingMatrix2(i-1,3)
                new_FreqAnalData[idx][5] = workingMatrix2[idx][3]
                # VB: FreqAnalData(i,7) = workingMatrix2(i-1,0)
                new_FreqAnalData[idx][6] = workingMatrix2[idx][0]
                # VB: FreqAnalData(i,8) = workingMatrix2(i-1,4)
                new_FreqAnalData[idx][7] = workingMatrix2[idx][4]

        NoOfXDataPoints = TotalCount

        return new_FreqAnalData, NoOfXDataPoints

    except Exception as e:
        mini_reset()
        # You might choose to return an error indicator or re-raise the exception.
        return None, 0
    
def empirical_analysis(
    ObservedData,           # list of observed data values (0-indexed)
    ModelledData,           # list of lists; each inner list represents an ensemble's modelled data
    NoOfObserved,           # integer: total number of observed data items available
    NoOfEnsembles,          # integer: number of ensembles
    NoOfModelled_list,      # list of integers: for each ensemble j, the number of modelled data items available
    TotalObsYears,          # integer: total number of observed years expected
    TotalModYears,          # integer: total number of modelled years expected (for each ensemble)
    EndOfSection,           # special marker value indicating end-of-year in the data (e.g. a specific number or object)
    UseThresh,              # integer flag: 1 means use threshold, 0 means do not apply threshold
    Thresh,                 # numeric threshold value
    File1Used,              # boolean: whether observed data is used
    File2Used,              # boolean: whether modelled data is used
    DefaultDir,             # string: default directory (e.g. "C:\\Data")
    NoOfXCols,              # integer: number of columns to produce in FreqAnalData (typically 2, 4, 6, or 8)
    File2ColStart,          # integer: the starting column (1-indexed in VB) where modelled data is placed in FreqAnalData
    PercentileWanted       # numeric: if > 0 then percentile limits are calculated
):
    """
    Performs the empirical analysis by processing the observed and modelled data.
    
    This routine follows these main steps:
      1. Calculate annual maximum series for the observed data (ObsMaxSeries) and,
         for each ensemble, for the modelled data (ModMaxSeries).
      2. Check that there are at least 10 years of data available.
      3. For modelled data, also check that all ensembles have the same number of years.
      4. Determine the maximum available years (MaxYearsAvailable).
      5. Create a sorting matrix and re-dimension the FreqAnalData array.
      6. For observed data, compute the return period and store the annual maximums.
      7. For modelled data, compute (and save to file) the annual maximums for each ensemble;
         then calculate the median (using CalcPercentile) and return period.
      8. If the observed and modelled series have different lengths, “pack” the shorter series
         by repeating the last acceptable value.
    
    Parameters are provided from the calling code (e.g. from your UI or data‐loading routines).
    
    Returns:
        (success, FreqAnalData, NoOfXDataPoints)
          success         : Boolean indicating whether the analysis was successful.
          FreqAnalData    : 2D list (matrix) of empirical results.
          NoOfXDataPoints : Number of data points (rows) available in FreqAnalData.
    """
    try:
        # ---------------------------
        # (A) Prepare arrays for annual maximum series.
        ObsMaxSeries = []  # will store one maximum per observed year
        # Create a 2D list for modelled series (dimensions: NoOfEnsembles x TotalModYears)
        ModMaxSeries = [[None for _ in range(TotalModYears)] for _ in range(NoOfEnsembles)]
        
        # Initialize counters and trackers.
        ObsYearsAvailable = 0
        ModYearsAvailable = 0
        minModYearsAvailable = 9999
        maxModYearsAvailable = 0
        MaxYearsAvailable = 0

        # ---------------------------
        # (B) Process observed data if File1Used.
        if File1Used:
            YearCounter = 0
            YearMax = -12344  # special initial value indicating no maximum found yet
            # Loop over observed data items (VB loop from 1 to NoOfObserved becomes 0-indexed in Python)
            for i in range(NoOfObserved):
                value = ObservedData[i]
                if value == EndOfSection:
                    # End of a year-section reached.
                    if YearMax != -12344:  # we found a valid maximum in this year
                        YearCounter += 1
                        ObsMaxSeries.append(YearMax)
                    # Reset YearMax for the next year.
                    YearMax = -12344
                else:
                    # Check the threshold criteria.
                    if ((UseThresh == 1 and value > Thresh) or (UseThresh == 0)):
                        if (value > YearMax) and (value != GLOBAL_MISSING_CODE):
                            YearMax = value
            ObsYearsAvailable = YearCounter
            if ObsYearsAvailable < 10:
                print("Error: Insufficient observed data (need at least 10 years).")
                mini_reset()
                return False, None, 0

        # ---------------------------
        # (C) Process modelled data if File2Used.
        if File2Used:
            # For each ensemble:
            for j in range(NoOfEnsembles):
                YearCounter = 0
                YearMax = -12344
                # Loop over data items for ensemble j
                for i in range(NoOfModelled_list[j]):
                    value = ModelledData[j][i]
                    if value == EndOfSection:
                        if YearMax != -12344:
                            YearCounter += 1
                            # Store in ModMaxSeries (0-indexed row)
                            ModMaxSeries[j][YearCounter - 1] = YearMax
                        YearMax = -12344
                    else:
                        if ((UseThresh == 1 and value > Thresh) or (UseThresh == 0)):
                            if (value > YearMax) and (value != GLOBAL_MISSING_CODE):
                                YearMax = value
                if YearCounter > maxModYearsAvailable:
                    maxModYearsAvailable = YearCounter
                if YearCounter < minModYearsAvailable:
                    minModYearsAvailable = YearCounter
            ModYearsAvailable = maxModYearsAvailable
            if ModYearsAvailable < 10:
                print("Error: Insufficient modelled data (need at least 10 years).")
                mini_reset()
                return False, None, 0
            if maxModYearsAvailable != minModYearsAvailable:
                print("Error: Modelled ensembles are of different lengths.")
                mini_reset()
                return False, None, 0

        # ---------------------------
        # (D) Determine overall maximum available years.
        MaxYearsAvailable = max(ObsYearsAvailable, ModYearsAvailable)

        # Create sortingMatrix (a list of lists with one element each) and FreqAnalData.
        sortingMatrix = [[None] for _ in range(MaxYearsAvailable)]
        FreqAnalData = [[None] * NoOfXCols for _ in range(MaxYearsAvailable)]
        NoOfXDataPoints = MaxYearsAvailable

        # ---------------------------
        # (E) Process observed annual maximums into FreqAnalData.
        if File1Used:
            # Copy ObsMaxSeries into sortingMatrix (only for the available years)
            for i in range(ObsYearsAvailable):
                sortingMatrix[i][0] = ObsMaxSeries[i]
            # Sort sortingMatrix in descending order by the first (and only) element.
            sortingMatrix[:ObsYearsAvailable] = sorted(sortingMatrix[:ObsYearsAvailable],
                                                         key=lambda row: row[0],
                                                         reverse=True)
            # For each observed year, assign:
            #   Return period = (ObsYearsAvailable) divided by (year index + 1)
            #   Annual maximum = sorted maximum value.
            for i in range(ObsYearsAvailable):
                FreqAnalData[i][0] = float(ObsYearsAvailable) / (i + 1)  # return period
                FreqAnalData[i][1] = sortingMatrix[i][0]                # observed annual max

        # ---------------------------
        # (F) Process modelled annual maximums.
        if File2Used:
            # Determine a temporary filename in the main drive of DefaultDir.
            drive = os.path.splitdrive(DefaultDir)[0]  # e.g., "C:"
            tempFileName = os.path.join(drive + os.sep, "SDSMEmpResults.txt")
            # Open the file for writing empirical results.
            with open(tempFileName, "w") as fout:
                fout.write("Empirical Results\n")
                fout.write("\t\t\t\tReturn Period\n")
                fout.write("Ensemble\t")
                # Write return period values for each year in descending order.
                for i in range(ModYearsAvailable, 0, -1):
                    rp = round(float(ModYearsAvailable) / i, 1)
                    fout.write(f"{rp}\t")
                fout.write("\n")

                # Create PercentileMatrix (list of lists: one column, for each ensemble row)
                PercentileMatrix = [[None] for _ in range(NoOfEnsembles)]
                # Allocate ModYearsData: 2D list of dimensions NoOfEnsembles x ModYearsAvailable.
                ModYearsData = [[None for _ in range(ModYearsAvailable)] for _ in range(NoOfEnsembles)]

                # For each ensemble, compute the annual maximum series.
                for j in range(NoOfEnsembles):
                    # For current ensemble, copy its ModMaxSeries into sortingMatrix.
                    for i in range(ModYearsAvailable):
                        sortingMatrix[i][0] = ModMaxSeries[j][i]
                    # Sort the series in descending order.
                    sortingMatrix[:ModYearsAvailable] = sorted(sortingMatrix[:ModYearsAvailable],
                                                                 key=lambda row: row[0],
                                                                 reverse=True)
                    # Save the sorted annual maximums into ModYearsData.
                    for i in range(ModYearsAvailable):
                        ModYearsData[j][i] = sortingMatrix[i][0]
                    # Write out the results for this ensemble.
                    fout.write(f"{j+1}\t")
                    for i in range(ModYearsAvailable, 0, -1):
                        fout.write(f"{round(ModYearsData[j][i-1], 4)}\t")
                    fout.write("\n")
            
            # Now work out the ensemble median (using CalcPercentile) and return periods.
            # For j from 0 to ModYearsAvailable-1 (VB loop: j = 1 To ModYearsAvailable)
            for j in range(ModYearsAvailable):
                EnsembleSum = 0.0
                # For each ensemble (i from 0 to NoOfEnsembles-1)
                for i in range(NoOfEnsembles):
                    EnsembleSum += ModYearsData[i][j]
                    PercentileMatrix[i][0] = ModYearsData[i][j]
                # Instead of mean, use median via CalcPercentile.
                # In VB:
                #   FreqAnalData(j, File2ColStart) = CalcPercentile(50)
                #   FreqAnalData(j, File2ColStart - 1) = (ModYearsAvailable / j)
                # In Python, adjust indices (we assume caller supplies File2ColStart as 1-indexed).
                col_return = File2ColStart - 2  # return period column (0-indexed)
                col_empirical = File2ColStart - 1  # empirical value column
                FreqAnalData[j][col_empirical] = calc_percentile(50)
                FreqAnalData[j][col_return] = float(ModYearsAvailable) / (j + 1)
                
                # If there are multiple ensembles and percentiles are desired, calculate limits.
                if (NoOfEnsembles > 1) and (PercentileWanted > 0):
                    temp1 = calc_percentile(100 - (PercentileWanted / 2))
                    temp2 = calc_percentile(PercentileWanted / 2)
                    if (temp1 != GLOBAL_MISSING_CODE) and (temp2 != GLOBAL_MISSING_CODE):
                        # VB assigns these values to columns offset relative to File2ColStart.
                        # Here we assume:
                        #   FreqAnalData[j][(File2ColStart + 1) - 1] = return period (again),
                        #   FreqAnalData[j][(File2ColStart + 2) - 1] = upper limit,
                        #   FreqAnalData[j][(File2ColStart + 3) - 1] = return period (again),
                        #   FreqAnalData[j][(File2ColStart + 4) - 1] = lower limit.
                        FreqAnalData[j][File2ColStart + 1 - 1] = float(ModYearsAvailable) / (j + 1)
                        FreqAnalData[j][File2ColStart + 2 - 1] = temp1
                        FreqAnalData[j][File2ColStart + 3 - 1] = float(ModYearsAvailable) / (j + 1)
                        FreqAnalData[j][File2ColStart + 4 - 1] = temp2

        # ---------------------------
        # (G) “Pack” the shorter array if observed and modelled series differ.
        if File1Used and File2Used:
            if ModYearsAvailable > ObsYearsAvailable:
                # For extra rows beyond ObsYearsAvailable, copy the last observed values.
                for i in range(ModYearsAvailable - ObsYearsAvailable):
                    FreqAnalData[ObsYearsAvailable + i][1] = FreqAnalData[ObsYearsAvailable - 1][1]
                    FreqAnalData[ObsYearsAvailable + i][0] = FreqAnalData[ObsYearsAvailable - 1][0]
            elif ModYearsAvailable < ObsYearsAvailable:
                for i in range(ObsYearsAvailable - ModYearsAvailable):
                    FreqAnalData[ModYearsAvailable + i][1] = FreqAnalData[ModYearsAvailable - 1][1]
                    FreqAnalData[ModYearsAvailable + i][0] = FreqAnalData[ModYearsAvailable - 1][0]

        # If we reach here, the empirical analysis is successful.
        return True, FreqAnalData, NoOfXDataPoints

    except Exception as e:
        mini_reset()
        return False, None, 0
    
def gev_analysis(
    ObservedData,           # list (0-indexed) of observed data values; values and section markers
    ModelledData,           # list of lists; each inner list is one ensemble’s modelled data (0-indexed)
    NoOfObserved,           # total number of observed data items in ObservedData
    NoOfEnsembles,          # number of ensembles in ModelledData
    NoOfModelled_list,      # list of integers: for each ensemble, the count of data items available
    TotalObsYears,          # expected number of observed years (for sizing ObsMaxSeries)
    TotalModYears,          # expected number of modelled years (for sizing ModMaxSeries per ensemble)
    EndOfSection,           # marker value (e.g. a special number) that indicates the end of a year’s data
    UseThresh,              # flag (integer): 1 means threshold is used, 0 means not used
    Thresh,                 # threshold value (only applied if UseThresh == 1)
    File1Used,              # Boolean: True if observed data are used
    File2Used,              # Boolean: True if modelled data are used
    DefaultDir,             # string: a directory (e.g. "C:\\Data")—used here to form a temp file path
    NoOfXCols,              # integer: number of columns to create in FreqAnalData (typically 2, 4, 6, or 8)
    File2ColStart,          # integer (1-indexed in VB) indicating the starting column for modelled data in FreqAnalData
    PercentileWanted        # numeric: if > 0 then percentile limits are calculated for ensembles
):
    """
    Performs the GEV analysis on observed and modelled data and propagates the results into the
    FreqAnalData array. Returns a tuple (success, FreqAnalData, NoOfXDataPoints).
    
    The routine follows these major steps:
      1. Compute the annual maximum series for observed data (ObsMaxSeries)
         and for each ensemble’s modelled data (ModMaxSeries).
      2. Validate that at least 3 years of data are available (for each file).
      3. Set NoOfXDataPoints to 10 (or 12 if there is abundant modelled data).
      4. Create FreqAnalData and preset the first column with predetermined return period values.
      5. For the observed data:
             • Sort the annual maximums (ascending order),
             • Compute the L‐moments LMoment(1), LMoment(2), LMoment(3),
             • Compute an intermediate value Zed and then Kay (using the Kysely relationships),
             • Depending on whether |Kay| is larger than a minimum (KayMinimum), use either the 3‑
               parameter model (with CalcGEVValue) or the 2‑parameter model (with CalcGEVSmallKay)
             • Populate the second column of FreqAnalData with the calculated values for a range
               of return periods.
      6. If File2Used is True, write temporary results to a file and then compute ensemble averages
         and percentiles to update FreqAnalData.
      7. Finally, if NoOfXCols > 2, fill in additional columns (with return period values).
      8. Display the Beta, Eta, and Kay values.
    
    Returns:
       (success, FreqAnalData, NoOfXDataPoints)
    """
    try:
        # ----- (A) Initialize arrays for annual maximum series
        ObsMaxSeries = []  # observed annual maximum values
        # For modelled data, create a 2D array: one row per ensemble, preallocate TotalModYears columns.
        ModMaxSeries = [[None] * TotalModYears for _ in range(NoOfEnsembles)]
        # We also create a list to store, for each ensemble, the number of years found.
        ModYearsAvailable = [0] * NoOfEnsembles

        # Other local variables
        YearCounter = 0
        YearMax = None
        EnsembleSum = 0.0
        temp1 = 0.0
        temp2 = 0.0
        # ModYearsData: will be allocated later as a 2D list with dimensions [NoOfEnsembles x NoOfXDataPoints]
        ModYearsData = None  
        ObsYearsAvailable = 0
        minModAvailable = 9999
        absoluteMinimum = -22222  # smallest possible value for AMS calculations
        KayString = ""  # will indicate via a string if a 2-parameter model was used
        KayMinimum = 0.005  # smallest allowed absolute value for Kay before using 2-parameter Gumbel
        tempFileName = ""  # for saving temporary file results

        # ----- (B) Process observed data (if File1Used)
        if File1Used:
            YearCounter = 0
            YearMax = absoluteMinimum
            # Loop over each observed data point (assume ObservedData is 0-indexed)
            for i in range(NoOfObserved):
                value = ObservedData[i]
                if value == EndOfSection:
                    if YearMax != absoluteMinimum:
                        YearCounter += 1
                        ObsMaxSeries.append(YearMax)
                    YearMax = absoluteMinimum
                else:
                    if (value > YearMax) and (value != GLOBAL_MISSING_CODE):
                        if ((UseThresh == 1 and value >= Thresh) or (UseThresh == 0)):
                            YearMax = value
            ObsYearsAvailable = YearCounter
            if ObsYearsAvailable < 3:
                print("Error: Insufficient observed data to plot (need at least 3 years).")
                mini_reset()
                return False, None, 0

        # ----- (C) Process modelled data (if File2Used)
        if File2Used:
            minModAvailable = 9999
            # For each ensemble:
            for j in range(NoOfEnsembles):
                YearCounter = 0
                YearMax = absoluteMinimum
                # Loop over data points for ensemble j.
                for i in range(NoOfModelled_list[j]):
                    value = ModelledData[j][i]
                    if value == EndOfSection:
                        if YearMax != absoluteMinimum:
                            YearCounter += 1
                            # Store the annual maximum in ModMaxSeries for ensemble j.
                            ModMaxSeries[j][YearCounter - 1] = YearMax
                        YearMax = absoluteMinimum
                    else:
                        if (value > YearMax) and (value != GLOBAL_MISSING_CODE):
                            if ((UseThresh == 1 and value >= Thresh) or (UseThresh == 0)):
                                YearMax = value
                ModYearsAvailable[j] = YearCounter
                if YearCounter < minModAvailable:
                    minModAvailable = YearCounter
            if minModAvailable < 3:
                print("Error: Insufficient modelled data to plot (need at least 3 years).")
                mini_reset()
                return False, None, 0

        # ----- (D) Set number of X-data points (return period rows)
        NoOfXDataPoints = 10
        if minModAvailable > 100:
            NoOfXDataPoints = 12
        # Create FreqAnalData as a matrix (list of lists) with NoOfXDataPoints rows and NoOfXCols columns.
        FreqAnalData = [[None] * NoOfXCols for _ in range(NoOfXDataPoints)]

        # Set predetermined return period values in the first column.
        # VB indices 1–10 (or 12) become Python indices 0–(N-1):
        return_periods = [2, 3, 4, 5, 10, 15, 20, 30, 50, 100]
        if minModAvailable > 100:
            return_periods += [500, 1000]
        for i, rp in enumerate(return_periods):
            FreqAnalData[i][0] = rp

        # ----- (E) Prepare a working (sorting) matrix and auxiliary variables
        # We will use the variable "sortingMatrix" as a list of single-element lists.
        sortingMatrix = [[None] for _ in range(ObsYearsAvailable if File1Used else 0)]
        # Local variables for GEV parameter estimation
        Beta = None
        Eta = None
        Kay = None
        Zed = None
        LMoment1 = l_moment(1)  # expected to be provided externally
        LMoment2 = l_moment(2)
        LMoment3 = l_moment(3)
        GammaResult = None

        # ----- (F) Process observed annual maximums for parameter estimation (if File1Used)
        if File1Used:
            # Fill sortingMatrix with observed annual maximums.
            for i in range(ObsYearsAvailable):
                sortingMatrix[i][0] = ObsMaxSeries[i]
            # Sort in ascending order (smallest first)
            sortingMatrix[:ObsYearsAvailable] = sorted(sortingMatrix[:ObsYearsAvailable],
                                                         key=lambda row: row[0])
            # Check that the L‐moments are valid.
            if (LMoment1 == GLOBAL_MISSING_CODE) or (LMoment2 == GLOBAL_MISSING_CODE) or (LMoment3 == GLOBAL_MISSING_CODE) or (LMoment2 == 0):
                print("Error: L‐moment calculation failed.")
                mini_reset()
                return False, None, 0
            # Calculate Zed using the Kysely relationship.
            Zed = 3 + (LMoment3 / LMoment2)
            Zed = 2 / Zed
            Zed = Zed - (math.log(2) / math.log(3))
            # Calculate Kay.
            Kay = (7.859 * Zed) + (2.9554 * (Zed ** 2))
            # ----- (F1) Depending on the magnitude of Kay, use 3‑ or 2‑parameter models.
            if abs(Kay) > KayMinimum:
                # 3‐parameter GEV model.
                Beta = (1 - (2 ** (-Kay)))
                GammaResult = gamma_func(1 + Kay)
                if (GammaResult == GLOBAL_MISSING_CODE) or (GammaResult == 0):
                    print("Error: Gamma function returned an invalid value.")
                    mini_reset()
                    return False, None, 0
                Beta = Beta * GammaResult
                Beta = (LMoment2 * Kay) / Beta
                Eta = (Beta * (gamma_func(1 + Kay) - 1)) / Kay
                Eta = Eta + LMoment1
                # For each predetermined return period, calculate the empirical value using CalcGEVValue.
                for idx, rp in enumerate(return_periods):
                    FreqAnalData[idx][1] = calc_gev_value(Beta, Eta, Kay, rp)
            else:
                # 2‐parameter Gumbel model.
                Beta = LMoment2 / math.log(2)
                Eta = LMoment1 - (0.557215665 * LMoment2 / math.log(2))
                for idx, rp in enumerate(return_periods):
                    FreqAnalData[idx][1] = calc_gev_small_kay(Beta, Eta, rp)

        # ----- (G) Process modelled data results if File2Used.
        if File2Used:
            # Determine a temporary file name; in VB this uses Mid$(DefaultDir,1,2) to extract the drive.
            drive = os.path.splitdrive(DefaultDir)[0]
            tempFileName = os.path.join(drive + os.sep, "SDSMGEVResults.txt")
            # Open the file for output.
            with open(tempFileName, "w") as f_out:
                f_out.write("GEV Results - * indicates Kay is less than " + str(KayMinimum) + "\n")
                f_out.write("Beta:\t" + "\t" + str(Beta) + "\n")
                f_out.write("Eta:\t" + "\t" + str(Eta) + "\n")
                f_out.write("Kay:\t" + "\t" + str(Kay) + "\n")
                f_out.write("\t\t\tReturn Period\n")
                f_out.write("Ensemble\t2\t3\t4\t5\t10\t15\t20\t30\t50\t100")
                if minModAvailable > 100:
                    f_out.write("\t500\t1000")
                f_out.write("\n")
                
                # Allocate ModYearsData: list of lists with dimensions [NoOfEnsembles x NoOfXDataPoints]
                ModYearsData = [[None] * NoOfXDataPoints for _ in range(NoOfEnsembles)]
                # Also create a PercentileMatrix as a list of one-element lists (for use in CalcPercentile).
                PercentileMatrix = [[None] for _ in range(NoOfEnsembles)]
                
                # For each ensemble, process its modelled annual maximums.
                for j in range(NoOfEnsembles):
                    # Set sortingMatrix size for this ensemble: use the number of years available for ensemble j.
                    current_years = ModYearsAvailable[j]
                    sortingMatrix = [[None] for _ in range(current_years)]
                    for i in range(current_years):
                        sortingMatrix[i][0] = ModMaxSeries[j][i]
                    sortingMatrix[:current_years] = sorted(sortingMatrix[:current_years],
                                                             key=lambda row: row[0])
                    # Save sorted values into ModYearsData for ensemble j.
                    for i in range(current_years):
                        ModYearsData[j][i] = sortingMatrix[i][0]
                    # Write out the sorted maximums for this ensemble.
                    f_out.write(str(j+1) + "\t")
                    for i in range(current_years-1, -1, -1):
                        f_out.write(str(round(ModYearsData[j][i], 4)) + "\t")
                    f_out.write("\n")
                
            # Now compute averages and percentiles.
            # For each return period row (i.e. for each index in 0..NoOfXDataPoints-1)
            # we “aggregate” values from all ensembles.
            # Also, populate PercentileMatrix with these values.
            for i in range(NoOfXDataPoints):
                # Reset sum for this return period.
                sum_val = 0.0
                for j in range(NoOfEnsembles):
                    sum_val += ModYearsData[j][i]
                    PercentileMatrix[j][0] = ModYearsData[j][i]
                # Instead of averaging, use the median (via CalcPercentile) for robustness.
                if (PercentileWanted > 0) and (NoOfEnsembles > 1):
                    temp1 = calc_percentile(100 - (PercentileWanted / 2))
                    temp2 = calc_percentile(PercentileWanted / 2)
                    if (temp1 == GLOBAL_MISSING_CODE) or (temp2 == GLOBAL_MISSING_CODE):
                        mini_reset()
                        return False, None, 0
                    # Place the limits into columns (offset as in VB).
                    # Assume that File2ColStart is 1-indexed in VB; here we adjust to 0-indexed.
                    FreqAnalData[i][File2ColStart + 1] = temp1
                    FreqAnalData[i][File2ColStart + 3] = temp2
                # Set the median in the designated column (using CalcPercentile(50)).
                FreqAnalData[i][File2ColStart - 1] = calc_percentile(50)

        # ----- (H) For additional columns beyond 2 (if NoOfXCols > 2) fill in return period values.
        if NoOfXCols > 2:
            # VB: for i = 3 to NoOfXCols step 2, fill these columns with the same predetermined return periods.
            # In Python, columns index 2, 4, 6, ... (0-indexed) are to be filled.
            for col in range(2, NoOfXCols, 2):
                for i, rp in enumerate(return_periods):
                    FreqAnalData[i][col] = rp

        # ----- (I) Display final parameter values.
        BetaString = format(Beta, "#0.000")
        EtaString = format(Eta, "#0.000")
        KayString_final = format(Kay, "#0.000")
        msgString = "Beta:  " + BetaString + "\n" + "Eta:  " + EtaString + "\n" + "Kay:  " + KayString_final
        # In VB a message box is shown; here we simply print.
        print(msgString)

        # Analysis was successful.
        return True, FreqAnalData, NoOfXDataPoints

    except Exception as e:
        mini_reset()
        return False, None, 0
    
def gumbel_analysis(
    ObservedData,           # list of observed data values (0-indexed)
    ModelledData,           # list of lists; each inner list holds one ensemble’s modelled data (0-indexed)
    NoOfObserved,           # integer: total count of items in ObservedData
    NoOfEnsembles,          # integer: number of ensembles in ModelledData
    NoOfModelled_list,      # list of integers: for ensemble j, the count of modelled data items
    TotalObsYears,          # integer: expected number of observed years (for sizing ObsMaxSeries)
    TotalModYears,          # integer: expected number of modelled years per ensemble
    EndOfSection,           # marker value indicating the end of a year’s data (e.g. -99999)
    UseThresh,              # integer flag: 1 means threshold is applied, 0 means not
    Thresh,                 # numeric threshold value (only used if UseThresh==1)
    File1Used,              # Boolean: True if observed data should be processed
    File2Used,              # Boolean: True if modelled data should be processed
    DefaultDir,             # string: default directory (e.g. "C:\\Data") used here to form a temp file path
    NoOfXCols,              # integer: number of columns in FreqAnalData (typically 2, 4, 6, or 8)
    PercentileWanted        # numeric: if > 0 then ensemble percentiles are calculated
):
    """
    Performs Gumbel analysis on observed and modelled data and populates the FreqAnalData matrix.
    
    The routine follows these steps:
    
      (A) Compute the annual maximum series for observed data (ObsMaxSeries).
          – For each observed datum, when the EndOfSection marker is encountered,
            the maximum value for that year is stored.
          – If fewer than 3 years are found, the routine fails.
      
      (B) For modelled data, for each ensemble compute its annual maximum series
          (ModMaxSeries) using similar logic. Also determine the minimum number of years
          (minModAvailable) available across ensembles; if fewer than 3, fail.
      
      (C) Using the observed annual maximums, compute the mean and standard deviation.
      
      (D) Create the output matrix FreqAnalData with 10 rows (or 10–12 if abundant data)
          and NoOfXCols columns. The first column will be preset with fixed return period
          values.
      
      (E) If File2Used is True, then for each ensemble:
            – Build a temporary working matrix for that ensemble,
            – Compute the mean and SD of the annual maximums,
            – Calculate “flood events” using preset multipliers,
            – Write the results to a temporary file,
            – Then compute, for each return period, the median (using CalcPercentile)
              across ensembles (and optionally percentile limits).
      
      (F) Finally, if File1Used is True, populate the observed flood event estimates
          (using ObsMeanAnnualMax and ObsSDAnnualMax) into FreqAnalData.
      
      (G) For columns beyond 2 (if NoOfXCols > 2) fill with the predetermined return period values.
    
    Returns:
       (success, FreqAnalData, NoOfXDataPoints)
         success         : Boolean indicating whether calculations were successful.
         FreqAnalData    : 2D list with analysis results.
         NoOfXDataPoints : Number of rows (fixed to 10 here).
    """
    try:
        # ---------------------------
        # (A) Process observed data: calculate ObsMaxSeries.
        ObsMaxSeries = []  # will hold one maximum per observed year
        if File1Used:
            YearCounter = 0
            YearMax = -12344
            for i in range(NoOfObserved):
                value = ObservedData[i]
                if value == EndOfSection:
                    if YearMax != -12344:
                        YearCounter += 1
                        ObsMaxSeries.append(YearMax)
                    YearMax = -12344
                else:
                    if ((UseThresh == 1 and value >= Thresh) or (UseThresh == 0)):
                        if (value > YearMax) and (value != GLOBAL_MISSING_CODE):
                            YearMax = value
            ObsYearsAvailable = YearCounter
            if ObsYearsAvailable < 3:
                print("Error: Insufficient observed data to plot.")
                mini_reset()
                return False, None, 0
        else:
            ObsYearsAvailable = 0

        # ---------------------------
        # (B) Process modelled data: calculate ModMaxSeries for each ensemble.
        if File2Used:
            minModAvailable = 9999  # track minimum available years across ensembles
            # Prepare a ModMaxSeries matrix: list of lists (one per ensemble)
            ModMaxSeries = [ [None] * TotalModYears for _ in range(NoOfEnsembles) ]
            ModYearsAvailable = [0] * NoOfEnsembles
            for j in range(NoOfEnsembles):
                YearCounter = 0
                YearMax = -12344
                # Loop over data for ensemble j.
                for i in range(NoOfModelled_list[j]):
                    value = ModelledData[j][i]
                    if value == EndOfSection:
                        if YearMax != -12344:
                            YearCounter += 1
                            ModMaxSeries[j][YearCounter - 1] = YearMax
                        YearMax = -12344
                    else:
                        if ((UseThresh == 1 and value > Thresh) or (UseThresh == 0)):
                            if (value > YearMax) and (value != GLOBAL_MISSING_CODE):
                                YearMax = value
                ModYearsAvailable[j] = YearCounter
                if YearCounter < minModAvailable:
                    minModAvailable = YearCounter
            if minModAvailable < 3:
                print("Error: Insufficient modelled data to plot.")
                mini_reset()
                return False, None, 0
        else:
            ModMaxSeries = None

        # ---------------------------
        # (C) Compute observed mean and standard deviation.
        if File1Used:
            # Build workingMatrix (list of lists with one element per row)
            workingMatrix = [[x] for x in ObsMaxSeries]
            ObsMeanAnnualMax = sum(row[0] for row in workingMatrix) / len(workingMatrix)
            ObsSDAnnualMax = math.sqrt(sum((row[0] - ObsMeanAnnualMax) ** 2 for row in workingMatrix) / (len(workingMatrix) - 1)) \
                             if len(workingMatrix) > 1 else 0
        else:
            ObsMeanAnnualMax = None
            ObsSDAnnualMax = None

        # ---------------------------
        # (D) Set up output FreqAnalData matrix.
        NoOfXDataPoints = 10  # fixed to 10 return period rows
        # FreqAnalData will have dimensions [10 x NoOfXCols]
        FreqAnalData = [[None] * NoOfXCols for _ in range(NoOfXDataPoints)]
        # Preset fixed return period values in column 0 (convert VB 1-indexed values to Python indices)
        fixed_return_periods = [2, 3, 4, 5, 10, 15, 20, 30, 50, 100]
        for i, rp in enumerate(fixed_return_periods):
            FreqAnalData[i][0] = rp

        # ---------------------------
        # (E) Process modelled data results (if File2Used)
        if File2Used:
            # Build a temporary filename using the drive from DefaultDir.
            drive = os.path.splitdrive(DefaultDir)[0]
            tempFileName = os.path.join(drive + os.sep, "SDSMGumbelResults.txt")
            # Open the file for writing temporary results.
            with open(tempFileName, "w") as f_out:
                f_out.write("Gumbel Results\n")
                f_out.write("\t\t\t\tReturn Period\n")
                f_out.write("Ensemble\t2\t3\t4\t5\t10\t15\t20\t30\t50\t100\n")
                TotalEnsemblesCalculated = 0
                # Prepare to store each ensemble's flood event calculations.
                ModFloodEvents_all = []  # will be a list of 10-number lists, one per ensemble
                for j in range(NoOfEnsembles):
                    n_years = ModYearsAvailable[j]
                    workingMatrix = [[None] for _ in range(n_years)]
                    for i in range(n_years):
                        workingMatrix[i][0] = ModMaxSeries[j][i]
                    # Sort workingMatrix in ascending order
                    workingMatrix = sorted(workingMatrix, key=lambda row: row[0])
                    TotalEnsemblesCalculated += 1
                    # Calculate mean and SD for ensemble j.
                    ModMeanAnnualMax = sum(row[0] for row in workingMatrix) / len(workingMatrix)
                    ModSDAnnualMax = math.sqrt(sum((row[0] - ModMeanAnnualMax) ** 2 for row in workingMatrix) / (len(workingMatrix) - 1)) \
                                     if len(workingMatrix) > 1 else 0
                    # Compute flood events using given multipliers.
                    ModFloodEvents_row = [
                        ModMeanAnnualMax - (ModSDAnnualMax * 0.16427),
                        ModMeanAnnualMax + (ModSDAnnualMax * 0.25381),
                        ModMeanAnnualMax + (ModSDAnnualMax * 0.52138),
                        ModMeanAnnualMax + (ModSDAnnualMax * 0.71946),
                        ModMeanAnnualMax + (ModSDAnnualMax * 1.30456),
                        ModMeanAnnualMax + (ModSDAnnualMax * 1.63467),
                        ModMeanAnnualMax + (ModSDAnnualMax * 1.86581),
                        ModMeanAnnualMax + (ModSDAnnualMax * 2.18868),
                        ModMeanAnnualMax + (ModSDAnnualMax * 2.59229),
                        ModMeanAnnualMax + (ModSDAnnualMax * 3.13668)
                    ]
                    ModFloodEvents_all.append(ModFloodEvents_row)
                    # Write ensemble results to file.
                    f_out.write(str(j+1) + "\t")
                    for val in ModFloodEvents_row:
                        f_out.write(str(round(val, 4)) + "\t")
                    f_out.write("\n")
            # Now, for each return period (rows 0..9), compute the median flood event
            for i in range(NoOfXDataPoints):
                # Extract the i-th flood event value from each ensemble.
                values = [ensemble[i] for ensemble in ModFloodEvents_all]
                sorted_vals = sorted(values)
                # Compute median
                if len(sorted_vals) % 2 == 1:
                    median_val = sorted_vals[len(sorted_vals)//2]
                else:
                    median_val = (sorted_vals[len(sorted_vals)//2 - 1] + sorted_vals[len(sorted_vals)//2]) / 2.0
                # Instead of averaging, the VB code uses CalcPercentile(50)
                # Here we simply set the median.
                FreqAnalData[i][File2ColStart - 1] = median_val
                # If multiple ensembles and a percentile is requested, attempt to compute limits.
                if TotalEnsemblesCalculated > 1 and PercentileWanted > 0:
                    temp1 = calc_percentile(100 - (PercentileWanted / 2))
                    temp2 = calc_percentile(PercentileWanted / 2)
                    if temp1 != GLOBAL_MISSING_CODE and temp2 != GLOBAL_MISSING_CODE:
                        FreqAnalData[i][File2ColStart + 1 - 1] = temp1
                        FreqAnalData[i][File2ColStart + 3 - 1] = temp2

        # ---------------------------
        # (F) For additional columns beyond the first two, fill in predetermined return period values.
        if NoOfXCols > 2:
            # For columns 2, 4, 6, ... (0-indexed: col 2, 4, 6, etc.) fill with fixed return periods.
            for col in range(2, NoOfXCols, 2):
                for i, rp in enumerate(fixed_return_periods):
                    FreqAnalData[i][col] = rp

        # ---------------------------
        # (G) For observed data, calculate flood event estimates based on the mean and SD.
        if File1Used:
            # Fill FreqAnalData’s second column (index 1) with values computed using ObsMeanAnnualMax and ObsSDAnnualMax.
            FreqAnalData[0][1] = ObsMeanAnnualMax - (ObsSDAnnualMax * 0.16427)
            FreqAnalData[1][1] = ObsMeanAnnualMax + (ObsSDAnnualMax * 0.25381)
            FreqAnalData[2][1] = ObsMeanAnnualMax + (ObsSDAnnualMax * 0.52138)
            FreqAnalData[3][1] = ObsMeanAnnualMax + (ObsSDAnnualMax * 0.71946)
            FreqAnalData[4][1] = ObsMeanAnnualMax + (ObsSDAnnualMax * 1.30456)
            FreqAnalData[5][1] = ObsMeanAnnualMax + (ObsSDAnnualMax * 1.63467)
            FreqAnalData[6][1] = ObsMeanAnnualMax + (ObsSDAnnualMax * 1.86581)
            FreqAnalData[7][1] = ObsMeanAnnualMax + (ObsSDAnnualMax * 2.18868)
            FreqAnalData[8][1] = ObsMeanAnnualMax + (ObsSDAnnualMax * 2.59229)
            FreqAnalData[9][1] = ObsMeanAnnualMax + (ObsSDAnnualMax * 3.13668)
        # (If File2Used, the modelled data results have already been set up above.)

        # Successful processing.
        return True, FreqAnalData, NoOfXDataPoints

    except Exception as e:
        mini_reset()
        return False, None, 0
    
def stretched_analysis(
    ObservedData,           # List of observed data values (0-indexed)
    ModelledData,           # List of lists; each inner list holds one ensemble’s modelled data (0-indexed)
    NoOfObserved,           # Integer; total number of items in ObservedData
    NoOfEnsembles,          # Integer; number of ensembles in ModelledData
    NoOfModelled_list,      # List of integers; for ensemble j, the number of data items available
    FSDate,                 # Analysis start date as a string (e.g., "2025-01-01")
    FEdate,                 # Analysis end date as a string (e.g., "2025-12-31")
    FreqThresh,             # Numeric; threshold used to filter values for frequency analysis
    Thresh,                 # Numeric; user-entered threshold for data selection
    UseThresh,              # Integer flag (1 or 0) that indicates whether to apply Thresh
    File1Used,              # Boolean; True if observed data is used
    File2Used,              # Boolean; True if modelled data is used
    NoOfXCols,              # Integer; number of columns in the FreqAnalData output
    PercentileWanted,       # Numeric; if > 0, percentiles will be computed from ensemble results
    DefaultDir              # String; default directory (e.g., "C:\\Data") used for temporary file output
):
    """
    Performs a Stretched Exponential analysis based on observed and modelled data and
    populates the FreqAnalData matrix with results for predetermined return periods.
    
    The routine proceeds as follows:
    
      1. Compute TotalToReadIn as the number of days between FSDate and FEdate.
      2. For each file (observed and modelled), “strip out” EndOfSection markers and any missing values.
      3. Check that at least 10 valid values remain for observed data and for the longest modelled ensemble.
      4. For observed data:
         • Build ObservedMatrix (a list of lists) from valid ObservedData values.
         • Compute TotObsWet (the total count of “wet” days) and R0 (the mean of those values).
         • Compute PrObsWet as the fraction of wet days.
         • Build a workingMatrix from ObservedMatrix that contains only values above FreqThresh.
         • Verify that at least 10 values are over threshold.
         • Resize workingMatrix (if desired) and sort it ascending.
         • Build WorkingXMatrix and WorkingYMatrix for a regression.
           For each row:
              – Set X[0] = 1.
              – Let N = (number of rows – current index) and assign it to column 1.
              – Compute column 2 as N/(TotObsWet + 1).
              – Set Y = log( -log( N/(TotObsWet + 1) ) ) and X[1] = log( observed_value / R0 ).
         • Perform linear regression (using NumPy) to calculate the regression coefficient, which is the “c” value.
         • For each fixed return period (2, 3, 4, 5, 10, 15, 20, 30, 50, 100), calculate the flood event
           using CalcStretchedValue(c_value, rp, R0, PrObsWet) and store it in FreqAnalData.
         
      5. For modelled data:
         • For each ensemble, similarly build ModelledMatrix from valid data.
         • Resize ModelledMatrix to the maximum valid length across ensembles.
         • (Optionally) write temporary ensemble results to a file.
         • For each ensemble, compute TotModWet, R0, and PrModWet.
         • For each ensemble, build a working matrix and regress (as above) to determine c.
         • Compute flood event estimates for each ensemble and store them in ModFloodEvents.
         • Aggregate across ensembles (using CalcPercentile to compute the median and, if requested, percentile limits)
           and fill the appropriate column(s) in FreqAnalData.
         
      6. If NoOfXCols > 2, fill additional columns with the fixed return period values.
      
      7. Return True along with FreqAnalData and the fixed number of data points (10).
    
    Returns:
       (success, FreqAnalData, NoOfXDataPoints)
    """
    try:
        # -------------------------
        # (1) Compute TotalToReadIn (number of days between FSDate and FEdate plus one)
        fmt = "%Y-%m-%d"
        start_date = datetime.strptime(FSDate, fmt)
        end_date = datetime.strptime(FEdate, fmt)
        TotalToReadIn = (end_date - start_date).days + 1

        # -------------------------
        # (2) Prepare matrices for observed and modelled data.
        # For observed data, create ObservedMatrix with a maximum of TotalToReadIn rows and 1 column.
        if File1Used:
            ObservedMatrix = [[None] for _ in range(TotalToReadIn)]
        else:
            ObservedMatrix = None

        # For modelled data, create ModelledMatrix with TotalToReadIn rows and NoOfEnsembles columns.
        if File2Used:
            ModelledMatrix = [[None for _ in range(NoOfEnsembles)] for _ in range(TotalToReadIn)]
            TempNoOfModelled = [0] * NoOfEnsembles  # list to store count for each ensemble
            MaxModelledData = 0
        else:
            ModelledMatrix = None

        # -------------------------
        # (3) Strip out EndOfSection markers and missing values.
        # It is assumed that EndOfSection is defined globally (you must supply it).
        # For observed data:
        if File1Used:
            TempNoOfObserved = 0
            for i in range(NoOfObserved):
                value = ObservedData[i]
                # Only keep values that are not EndOfSection and not missing,
                # and satisfy the threshold condition.
                if value != EndOfSection and value != GLOBAL_MISSING_CODE:
                    if ((UseThresh == 1 and value >= Thresh) or (UseThresh == 0)):
                        ObservedMatrix[TempNoOfObserved][0] = value
                        TempNoOfObserved += 1
            # Resize ObservedMatrix to only include valid rows.
            ObservedMatrix = ObservedMatrix[:TempNoOfObserved]
        else:
            TempNoOfObserved = 0

        # For modelled data:
        if File2Used:
            # Loop over each ensemble (VB: For j = 1 To NoOfEnsembles)
            for j in range(NoOfEnsembles):
                count = 0
                # Loop over each data point for ensemble j (0-indexed)
                for i in range(NoOfModelled_list[j]):
                    value = ModelledData[j][i]
                    if value != EndOfSection and value != GLOBAL_MISSING_CODE:
                        if ((UseThresh == 1 and value >= Thresh) or (UseThresh == 0)):
                            # Store in ModelledMatrix at row index count, column j.
                            ModelledMatrix[count][j] = value
                            count += 1
                TempNoOfModelled[j] = count
                if count > MaxModelledData:
                    MaxModelledData = count
            # Resize ModelledMatrix to only include valid rows.
            ModelledMatrix = ModelledMatrix[:MaxModelledData]
        else:
            MaxModelledData = 0

        # -------------------------
        # (4) Check that there is sufficient data.
        if (File1Used and TempNoOfObserved < 10) or (File2Used and MaxModelledData < 10):
            print("Error: Unable to determine sufficient data to plot.")
            mini_reset()
            return False, None, 0

        # -------------------------
        # (5) Prepare output matrix: FreqAnalData with 10 rows (Return Period Years)
        NoOfXDataPoints = 10
        FreqAnalData = [[None] * NoOfXCols for _ in range(NoOfXDataPoints)]
        fixed_return_periods = [2, 3, 4, 5, 10, 15, 20, 30, 50, 100]
        for i, rp in enumerate(fixed_return_periods):
            FreqAnalData[i][0] = rp  # first column holds return periods

        # -------------------------
        # (6) Process observed data for regression if File1Used.
        if File1Used:
            TotObsWet = 0   # total number of wet days (observed values > Thresh)
            R0 = 0.0        # sum of wet day amounts
            for row in ObservedMatrix:
                if row[0] > Thresh:
                    TotObsWet += 1
                    R0 += row[0]
            if TotObsWet > 0:
                R0 = R0 / TotObsWet  # mean of wet days
            PrObsWet = TotObsWet / TempNoOfObserved if TempNoOfObserved > 0 else 0

            # Build workingMatrix from ObservedMatrix: keep only values above FreqThresh.
            workingMatrix = []
            for row in ObservedMatrix:
                if row[0] > FreqThresh:
                    workingMatrix.append([row[0]])
            ObsOverThresh = len(workingMatrix)
            if ObsOverThresh < 10:
                print("Error: Insufficient observed data over threshold to plot.")
                mini_reset()
                return False, None, 0

            # Expand workingMatrix to allow additional columns.
            # We will later populate columns 1 and 2.
            for i in range(ObsOverThresh):
                # Ensure each row has at least 3 columns.
                workingMatrix[i] = workingMatrix[i] + [None, None]
            # Sort workingMatrix by the first column (rainfall) in ascending order.
            workingMatrix.sort(key=lambda row: row[0])

            # Build regression matrices: WorkingXMatrix and WorkingYMatrix.
            # Let n = number of rows in workingMatrix.
            n = ObsOverThresh
            WorkingXMatrix = []
            WorkingYMatrix = []
            # For each row (i = 0 to n-1):
            for i in range(n):
                # Set N = n - i (equivalent to VB: workingMatrix.Rows - i + 1)
                N_val = n - i
                # Store N_val in workingMatrix column 1.
                workingMatrix[i][1] = N_val
                # Compute column 2 as N_val / (TotObsWet + 1)
                workingMatrix[i][2] = N_val / (TotObsWet + 1) if (TotObsWet + 1) != 0 else 0
                # WorkingYMatrix: log( -log( N_val/(TotObsWet +1) ) )
                try:
                    y_val = math.log(-math.log(workingMatrix[i][2]))
                except Exception as e:
                    y_val = GLOBAL_MISSING_CODE
                WorkingYMatrix.append([y_val])
                # WorkingXMatrix: first column is 1; second column: log( observed_value / R0 )
                try:
                    x_val = math.log(workingMatrix[i][0] / R0) if R0 > 0 else 0
                except Exception as e:
                    x_val = GLOBAL_MISSING_CODE
                WorkingXMatrix.append([1.0, x_val])
            # Convert WorkingXMatrix and WorkingYMatrix to numpy arrays and perform regression.
            X = np.array(WorkingXMatrix)  # shape (n,2)
            Y = np.array(WorkingYMatrix)  # shape (n,1)
            try:
                beta = np.linalg.inv(X.T @ X) @ (X.T @ Y)
            except Exception as e:
                mini_reset()
                return False, None, 0
            # In VB, CValue = BeesMatrix(1,0) i.e. second element.
            CValue = beta[1, 0]

            # For each predetermined return period, compute the flood event using CalcStretchedValue.
            for idx, rp in enumerate(fixed_return_periods):
                # Note: we assume CalcStretchedValue is a function that returns a numeric value.
                FreqAnalData[idx][1] = calc_stretched_value(CValue, rp, R0, PrObsWet)

        # -------------------------
        # (7) Process modelled data (if File2Used).
        if File2Used:
            # Build ModelledMatrix (already filled when stripping EndOfSection); now resize its rows.
            # ModelledMatrix already has been resized to MaxModelledData rows (each row is a list of length NoOfEnsembles).
            # For each ensemble, we have TempNoOfModelled[j] valid data points.
            # Open a temporary file for writing ensemble results.
            drive = os.path.splitdrive(DefaultDir)[0]
            tempFileName = os.path.join(drive + os.sep, "SDSMSEResults.txt")
            with open(tempFileName, "w") as f_out:
                f_out.write("Stretched Exponential Results\n")
                f_out.write("\t\t\t\tReturn Period\n")
                f_out.write("Ensemble\t2\t3\t4\t5\t10\t15\t20\t30\t50\t100\n")
                # Create an array to hold flood event estimates for each ensemble.
                # We'll use a list of lists: one list per ensemble with 10 values.
                ModFloodEvents = []
                # For each ensemble:
                for j in range(NoOfEnsembles):
                    # For ensemble j, the valid data are in ModelledMatrix[0:TempNoOfModelled[j]][j]
                    current_count = TempNoOfModelled[j]
                    # Skip ensemble if no data (should not happen due to earlier checks)
                    if current_count < 10:
                        continue
                    # Extract column j from ModelledMatrix for the valid rows.
                    ensemble_data = [ ModelledMatrix[i][j] for i in range(current_count) ]
                    # Compute TotModWet and R0 for ensemble j: consider all values > Thresh.
                    TotModWet = 0
                    R0_mod = 0.0
                    for val in ensemble_data:
                        if val > Thresh:
                            TotModWet += 1
                            R0_mod += val
                    if TotModWet > 0:
                        R0_mod = R0_mod / TotModWet
                    else:
                        R0_mod = 0
                    PrModWet = TotModWet / current_count if current_count > 0 else 0
                    # Build workingMatrix for this ensemble: keep only values above FreqThresh.
                    workingMatrix = []
                    for val in ensemble_data:
                        if val > FreqThresh:
                            workingMatrix.append([val])
                    ModOverThresh = len(workingMatrix)
                    if ModOverThresh < 10:
                        print("Error: Insufficient modelled data over threshold to plot for ensemble", j+1)
                        mini_reset()
                        return False, None, 0
                    # Expand workingMatrix rows to have 3 columns (we will fill columns 1 and 2)
                    for i in range(ModOverThresh):
                        workingMatrix[i] = workingMatrix[i] + [None, None]
                    # Sort workingMatrix ascending by the first column.
                    workingMatrix.sort(key=lambda row: row[0])
                    # Build regression matrices for this ensemble.
                    n = ModOverThresh
                    WorkingXMatrix = []
                    WorkingYMatrix = []
                    for i in range(n):
                        N_val = n - i
                        workingMatrix[i][1] = N_val
                        workingMatrix[i][2] = N_val / (TotModWet + 1) if (TotModWet + 1) != 0 else 0
                        try:
                            y_val = math.log(-math.log(workingMatrix[i][2]))
                        except Exception as e:
                            y_val = GLOBAL_MISSING_CODE
                        WorkingYMatrix.append([y_val])
                        try:
                            x_val = math.log(workingMatrix[i][0] / R0_mod) if R0_mod > 0 else 0
                        except Exception as e:
                            x_val = GLOBAL_MISSING_CODE
                        WorkingXMatrix.append([1.0, x_val])
                    # Convert to NumPy arrays and compute regression coefficient:
                    X = np.array(WorkingXMatrix)
                    Y = np.array(WorkingYMatrix)
                    try:
                        beta = np.linalg.inv(X.T @ X) @ (X.T @ Y)
                    except Exception as e:
                        mini_reset()
                        return False, None, 0
                    CValue = beta[1, 0]
                    # For this ensemble, compute flood events for each fixed return period.
                    ensemble_events = []
                    for rp in fixed_return_periods:
                        event = calc_stretched_value(CValue, rp, R0_mod, PrModWet)
                        ensemble_events.append(event)
                    ModFloodEvents.append(ensemble_events)
                    # Write ensemble results to file.
                    f_out.write(str(j+1) + "\t")
                    for ev in ensemble_events:
                        f_out.write(str(round(ev, 4)) + "\t")
                    f_out.write("\n")
            # End of ensemble file output.
            # Now aggregate across ensembles for each return period:
            # Create a PercentileMatrix as a list of one-element lists (one per ensemble) for each return period.
            PercentileMatrix = []  # list of lists; each inner list collects values from all ensembles for a given return period.
            for i in range(NoOfXDataPoints):
                values = [ ensemble_events[i] for ensemble_events in ModFloodEvents ]
                PercentileMatrix.append(values)
                # Instead of averaging, we set the median via CalcPercentile.
                med_val = calc_percentile(50)  # In a real app, CalcPercentile would use the PercentileMatrix data.
                # For this example, we simply choose the median of the sorted values.
                sorted_vals = sorted(values)
                if len(sorted_vals) % 2 == 1:
                    med_val = sorted_vals[len(sorted_vals) // 2]
                else:
                    med_val = (sorted_vals[len(sorted_vals)//2 - 1] + sorted_vals[len(sorted_vals)//2]) / 2.0
                FreqAnalData[i][File2ColStart - 1] = med_val
                # Optionally, compute upper and lower percentile limits if requested.
                if PercentileWanted > 0 and NoOfEnsembles > 1:
                    upper = calc_percentile(100 - (PercentileWanted/2))
                    lower = calc_percentile(PercentileWanted/2)
                    if upper != GLOBAL_MISSING_CODE and lower != GLOBAL_MISSING_CODE:
                        FreqAnalData[i][File2ColStart + 1] = upper
                        FreqAnalData[i][File2ColStart + 3] = lower
                    else:
                        mini_reset()
                        return False, None, 0
        # -------------------------
        # (8) For additional columns (if NoOfXCols > 2), fill in fixed return period values.
        if NoOfXCols > 2:
            for col in range(2, NoOfXCols, 2):
                for i, rp in enumerate(fixed_return_periods):
                    FreqAnalData[i][col] = rp

        # Analysis is successful.
        return True, FreqAnalData, NoOfXDataPoints

    except Exception as e:
        mini_reset()
        return False, None, 0  

def frequency_analysis(presentation,
                        observedFilePath,
                        modelledFilePath,
                        fsDate,
                        feDate,
                        dataPeriodChoice,
                        applyThreshold,
                        thresholdValue,
                        durations,
                        ensembleIndex,
                        freqModel):
    """
    Performs frequency analysis on observed and modelled data.
    
    Parameters:
      presentation        : "Graphical" or "Tabular"
      observedFilePath    : Path to observed data file (.txt)
      modelledFilePath    : Path to modelled data file (.OUT)
      fsDate              : Analysis start date (e.g., "2025-01-01")
      feDate              : Analysis end date (e.g., "2025-12-31")
      dataPeriodChoice    : Data period selection (0 for Annual or a month index)
      applyThreshold      : 1 or 0: whether to apply threshold filtering
      thresholdValue      : Numeric threshold value
      durations           : Duration settings (passed from UI)
      ensembleIndex       : Desired ensemble index (0‑indexed)
      freqModel           : Frequency model string; one of "Empirical", "GEV", "Gumbel", "Stretched"
    
    This function opens the observed (.txt) file and the modelled (.OUT) file,
    performs validation of dates and ensemble settings, skips unwanted header data,
    reads in the required data (one value per line for observed data; fixed‑width
    fields for modelled data if multiple ensembles are present), and then calls the
    appropriate analysis function. Finally, it computes a MAE (if both files are used)
    and prints a graphical or tabular presentation to the console.
    
    UI–actions are indicated in comments.
    """
    try:
        print("=== Starting Frequency Analysis ===")
        
        # --- Preliminary checks -----------------------------------
        # (UI) Set focus to file selection control.
        print("[UI] Set focus to file selection control (e.g., SelectFile1)")
        
        # Ensure at least one file is specified.
        if (observedFilePath == "" or len(observedFilePath) < 5) and \
           (modelledFilePath == "" or len(modelledFilePath) < 5):
            print("ERROR: You must select at least one file before proceeding.")
            return
        
        # Validate dates.
        if not fe_date_ok(fsDate, feDate, feDate):
            print("ERROR: End date is invalid.")
            return
        if not fs_date_ok(fsDate, feDate, fsDate):
            print("ERROR: Start date is invalid.")
            return
        if date_diff_years(fsDate, feDate) < 3:
            print("ERROR: At least three years of data must be selected.")
            return
        
        # Check ensemble settings.
        if not ensemble_number_ok(True, str(ensembleIndex), ensembleIndex):
            print("ERROR: Invalid ensemble selection.")
            return
        
        # Determine which files will be used.
        File1Used = (observedFilePath != "")
        File2Used = (modelledFilePath != "")
        File1Name = observedFilePath
        File2Name = modelledFilePath
        
        # --- Open files ------------------------------------------------
        if File1Used:
            print(f"[FILE] Opening observed file: {File1Name}")
            f1 = open(observedFilePath, 'r')
        if File2Used:
            print(f"[FILE] Opening modelled file: {File2Name}")
            f2 = open(modelledFilePath, 'r')
        
        # (UI) Set mouse pointer to hourglass and show progress bar.
        print("[UI] Mouse pointer set to Hourglass")
        print("[UI] Progress bar displayed")
        
        # --- Determine ensemble details for File2 ---------------------
        EnsemblePresent = False
        NoOfEnsembles = 1
        if File2Used:
            first_line = f2.readline()
            f2.seek(0)
            if len(first_line) > 15:
                EnsemblePresent = True
                NoOfEnsembles = len(first_line) // 14
            else:
                EnsemblePresent = False
                NoOfEnsembles = 1
            print("Determined number of ensembles:", NoOfEnsembles)
            if EnsemblePresent and (NoOfEnsembles < ensembleIndex + 1):
                print(f"ERROR: Selected ensemble does not exist. Only {NoOfEnsembles} available.")
                mini_reset()
                return
        
        # --- Skip unwanted header data ---------------------------------
        # (UI) Update progress bar as needed.
        if File1Used:
            print("Skipping unwanted observed data...")
            # For example, skip the first 5 lines.
            lines_to_skip = 5
            for _ in range(lines_to_skip):
                f1.readline()
                increase_obs_date()  # advance date
                print(f"Observed data skipping progress: {(_+1)*20}%")
            print("Finished skipping observed data.")
        
        if File2Used:
            print("Skipping unwanted modelled data...")
            lines_to_skip = 5
            for _ in range(lines_to_skip):
                f2.readline()
                increase_date()  # advance date
                print(f"Modelled data skipping progress: {(_+1)*20}%")
            print("Finished skipping modelled data.")
        
        # --- Read required data -----------------------------------------
        # Read observed data (each line should hold a single numeric value).
        ObservedData_array = []
        if File1Used:
            for line in f1:
                try:
                    val = float(line.strip())
                    ObservedData_array.append(val)
                except Exception:
                    continue
            f1.close()
            print(f"Read {len(ObservedData_array)} observed data points.")
        else:
            ObservedData_array = []
        
        # Read modelled data.
        ModelledData_array = []
        if File2Used:
            if EnsemblePresent:
                for line in f2:
                    line = line.rstrip("\n")
                    # Assume fixed-width fields of 14 characters.
                    fields = [line[i:i+14].strip() for i in range(0, len(line), 14)]
                    try:
                        row = [float(x) for x in fields if x != ""]
                    except Exception:
                        row = []
                    if row:
                        ModelledData_array.append(row)
                f2.close()
                if ModelledData_array:
                    # Transpose so that each ensemble becomes a list.
                    num_fields = len(ModelledData_array[0])
                    ModelledData_transposed = [[] for _ in range(num_fields)]
                    for row in ModelledData_array:
                        for j in range(min(len(row), num_fields)):
                            ModelledData_transposed[j].append(row[j])
                    ModelledData_array = ModelledData_transposed
            else:
                for line in f2:
                    try:
                        val = float(line.strip())
                        ModelledData_array.append(val)
                    except Exception:
                        continue
                f2.close()
                ModelledData_array = [ModelledData_array]
            print(f"Read modelled data for {len(ModelledData_array)} ensemble(s).")
        
        NoOfObserved_val = len(ObservedData_array)
        NoOfModelled_list = [len(ens) for ens in ModelledData_array]
        TotalObsYears = 3  # (Example value; set appropriately.)
        TotalModYears = 3  # (Example value; set appropriately.)
        
        print("[FILE] Files closed.")
        
        # --- Ensemble reduction if needed --------------------------------
        if File2Used and EnsemblePresent and (NoOfEnsembles > 1):
            print(f"Reducing ensembles: selecting ensemble {ensembleIndex + 1}.")
            ModelledData_array[0] = ModelledData_array[ensembleIndex]
            NoOfModelled_list[0] = NoOfModelled_list[ensembleIndex]
            NoOfEnsembles = 1
        
        # --- Determine FreqAnalData dimensions -----------------------------
        if File1Used and File2Used:
            File2ColStart = 4
            if (NoOfEnsembles > 1) and (applyThreshold and (thresholdValue > 0)):
                NoOfXCols = 8
            else:
                NoOfXCols = 4
        elif File2Used:
            File2ColStart = 2
            if (NoOfEnsembles > 1) and (applyThreshold and (thresholdValue > 0)):
                NoOfXCols = 6
            else:
                NoOfXCols = 2
        else:
            NoOfXCols = 2
        NoOfXDataPoints = 10  # Fixed number of return period rows.
        
        print("Progress: Performing Analysis: 50%")
        
        # --- Call the appropriate analysis function ------------------------
        if freqModel.lower() == "empirical":
            AllOk, FreqAnalData, _ = empirical_analysis(
                ObservedData_array,
                ModelledData_array,
                NoOfObserved_val,
                NoOfEnsembles,
                NoOfModelled_list,
                TotalObsYears,
                TotalModYears,
                EndOfSection,
                int(applyThreshold),
                thresholdValue,
                File1Used,
                File2Used,
                os.path.dirname(observedFilePath) if observedFilePath else "",
                NoOfXCols,
                File2ColStart,
                10  # Assuming PercentileWanted = 10
            )
        elif freqModel.lower() == "gev":
            AllOk, FreqAnalData, _ = gev_analysis(
                ObservedData_array,
                ModelledData_array,
                NoOfObserved_val,
                NoOfEnsembles,
                NoOfModelled_list,
                TotalObsYears,
                TotalModYears,
                EndOfSection,
                int(applyThreshold),
                thresholdValue,
                File1Used,
                File2Used,
                os.path.dirname(observedFilePath) if observedFilePath else "",
                NoOfXCols,
                File2ColStart,
                10
            )
        elif freqModel.lower() == "gumbel":
            AllOk, FreqAnalData, _ = gumbel_analysis(
                ObservedData_array,
                ModelledData_array,
                NoOfObserved_val,
                NoOfEnsembles,
                NoOfModelled_list,
                TotalObsYears,
                TotalModYears,
                EndOfSection,
                int(applyThreshold),
                thresholdValue,
                File1Used,
                File2Used,
                os.path.dirname(observedFilePath) if observedFilePath else "",
                NoOfXCols,
                10
            )
        elif freqModel.lower() == "stretched":
            AllOk, FreqAnalData, _ = stretched_analysis(
                ObservedData_array,
                ModelledData_array,
                NoOfObserved_val,
                NoOfEnsembles,
                NoOfModelled_list,
                fsDate,
                feDate,
                thresholdValue,  # Use thresholdValue as FreqThresh
                thresholdValue,
                int(applyThreshold),
                File1Used,
                File2Used,
                NoOfXCols,
                10,
                os.path.dirname(observedFilePath) if observedFilePath else ""
            )
        else:
            print("ERROR: Unknown frequency model selected.")
            return
        
        print("Progress: Performing Analysis: 75%")
        
        # --- Calculate MAE if both observed and modelled data are used.
        if AllOk and File1Used and File2Used and FreqAnalData is not None:
            MAE = 0.0
            for row in FreqAnalData:
                if row[1] is not None and row[3] is not None:
                    MAE += abs(row[1] - row[3])
            MAE /= NoOfXDataPoints
            print(f"MAE (Mean Absolute Error): {MAE:.3f}")
        
        # --- Presentation stage --------------------------------------------
        if AllOk and FreqAnalData is not None:
            if presentation.lower() == "graphical":
                # (UI) Load and display a chart form.
                print("\n--- Graphical Presentation ---")
                print("X-axis Title: Return period (years)")
                print("Y-axis Title: Value")
                if File1Used and File2Used:
                    ChartMax = FreqAnalData[0][0] if FreqAnalData[0][0] > FreqAnalData[0][2] else FreqAnalData[0][2]
                else:
                    ChartMax = FreqAnalData[0][0]
                print("X-axis Maximum:", ChartMax)
                ChartTitle = "Period: "
                if dataPeriodChoice == 0:
                    ChartTitle += "Annual"
                else:
                    ChartTitle += f"Label({dataPeriodChoice})"
                if freqModel.lower() == "empirical":
                    ChartTitle += ";  Fit: Empirical"
                elif freqModel.lower() == "gev":
                    ChartTitle += ";  Fit: Generalised Extreme Value"
                elif freqModel.lower() == "gumbel":
                    ChartTitle += ";  Fit: Gumbel"
                elif freqModel.lower() == "stretched":
                    ChartTitle += ";  Fit: Stretched Exponential"
                print("Chart Title:", ChartTitle)
                print("FreqAnalData:")
                for row in FreqAnalData:
                    print(row)
            else:
                # Tabular presentation.
                print("\n--- Tabular Presentation ---")
                if File1Used and not File2Used:
                    print("Observed data:", File1Name)
                    print("Return Period\tObs")
                    for row in reversed(FreqAnalData):
                        print(f"{row[0]:10.1f}\t{row[1]:10.3f}")
                elif File2Used and not File1Used:
                    print("Modelled data:", File2Name)
                    if NoOfXCols in [6, 8]:
                        print("Return Period\tMod\tLower\tUpper")
                    else:
                        print("Return Period\tMod")
                    for row in reversed(FreqAnalData):
                        if NoOfXCols in [6, 8]:
                            print(f"{row[File2ColStart-1]:10.1f}\t{row[File2ColStart]:10.3f}\t{row[File2ColStart+4]:10.3f}\t{row[File2ColStart+2]:10.3f}")
                        else:
                            print(f"{row[File2ColStart-1]:10.1f}\t{row[File2ColStart]:10.3f}")
                elif File1Used and File2Used:
                    print("Observed data:", File1Name)
                    print("Modelled data:", File2Name)
                    if NoOfXCols in [6, 8]:
                        print("Return Period\tObs\tMod\tLower\tUpper")
                    else:
                        print("Return Period\tObs\tMod")
                    for row in reversed(FreqAnalData):
                        if NoOfXCols in [6, 8]:
                            print(f"{row[0]:10.1f}\t{row[1]:10.3f}\t{row[File2ColStart]:10.3f}\t{row[File2ColStart+4]:10.3f}\t{row[File2ColStart+2]:10.3f}")
                        else:
                            print(f"{row[0]:10.1f}\t{row[1]:10.3f}\t{row[File2ColStart]:10.3f}")
                else:
                    print("No data available for tabular display.")
        
        # --- Cleanup -------------------------------------------------------
        mini_reset()
        print("=== Frequency Analysis Completed ===")
        
    except Exception as e:
        mini_reset()
#EOF