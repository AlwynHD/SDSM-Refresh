from PyQt5.QtWidgets import QApplication, QFileDialog
import datetime
import os 
import re
import calendar
import numpy as np

class thirtyDate:
    """
    SDSM allows a date option where all months have 30 days
    Python's native datetime.date does not support this
    Especially noticable with Feb 30
    --> This date should support all the functionality needed
    --> Use in place of datetime.date when needed
    """
    def __init__(self, year, month, day):
        self.year = year
        self.month = month
        self.day = day

    def __sub__(self, other):
        return (
            ((self.year - other.year) * 30 * 12) +
            ((self.month - other.month) * 30) +
            (self.day - other.day)
        )
    
    def __eq__(self, other):
        #equal to
        if ((self.year == other.year) 
        and (self.month == other.month) 
        and (self.day == other.day)):
            return True
        else:
            return False
    
    def __gt__(self, other):
        #greater than
        if self.year == other.year:
            if self.month == other.month:
                if self.day == other.day:
                    return False
                else:
                    return self.day > other.day
            else:
                return self.month > other.day
        else:
            return self.year > other.year
        
    def __ge__(self, other):
        #greater than or equal to
        return (self > other) | (self == other)

    def __lt__(self, other):
        #less than
        return not (self >= other)

    def __le__(self, other):
        #less than or equal to
        return not (self > other)

    def __ne__(self, other):
        #not equal to
        return not (self == other)

    def __add__(self, other):
        # increase date by timedelta or int
        if isinstance(other, datetime.timedelta):
            toIncrease = other.days
        elif isinstance(other, int):  # If it's an integer, assume it's days to add.
            toIncrease = other
        else:
            raise TypeError("Unsupported type for addition with ThirtyDate.")

        nextDay = self.day - 1 + toIncrease # mod get numbers between 0-29 we want 1-30. 1's to make it right
        self.day = nextDay % 30 + 1 
        nextMonth = nextDay // 30 + self.month - 1
        self.month = nextMonth % 12 + 1
        nextYear = nextMonth // 12 + self.year
        self.year = nextYear

        return self
    
    def __str__(self):
        # convert to string to print
        """A user-friendly string representation of the date."""
        # Format the date as "YYYY-MM-DD"
        return f"{self.year:04d}-{self.month:02d}-{self.day:02d}"
        #return str(self.year) + '-' + ('0' + str(self.month) if self.month < 10 else str(self.month)) + '-' + ('0' + str(self.day) if self.day < 10 else str(self.day))

def displayFiles(selected_files):
    """
    takes files strips paths and prints that to user
    takes entire path into filesSelected array returns array
    """
    fileSelected = []
    if selected_files:
        for file in selected_files:
            fileName = os.path.basename(file)
            fileSelected.append(fileName)
    else:
        print("No file selected.")
    return fileSelected

def selectFile():
    """
    pulls up the windows file explorer for user to select any file that ends in .Dat
    returns file path
    """
    app = QApplication([])
    file_dialog = QFileDialog()
    file_dialog.setFileMode(QFileDialog.ExistingFiles)
    file_dialog.setNameFilter("DAT files (*.DAT)")
    if file_dialog.exec_():
        files = file_dialog.selectedFiles()
        return files

def filesNames(fileName):
    """
    each of the predictor files represent different things this finds what they mean and return it
    """
    # file name is the (i,0) and description is (i,1)

    fileDescriptionList = [["temp", "Mean temperature at 2m"], ["mslp", "Mean sea level pressure"], ["p500", "500 hPa geopotential height"], ["p850", "850 hPa geopotential height"],
                       ["rhum", "Near surface relative humidity"], ["r500", "Relative humidity at 500 hPa"], ["r850", "Relative humidity at 850 hPa"], ["sphu", "Near surface specific humidity"],
                       ["p__f", "Surface airflow strength"], ["p__z", "Surface vorticity"], ["p__v", "Surface meridional velocity"], ["p__u", "Surface zonal velocity"],
                       ["p_th", "Surface wind direction"], ["p_zh", "Surface divergence"], ["p5_f", "500 hPa airflow strength"], ["p5_z", "500 hPa vorticity"],
                       ["p5_v", "500 hPa meridional velocity"], ["p5_u", "500 hPa zonal velocity"], ["p5th", "500 hPa wind direction"], ["p5zh", "500 hPa divergence"],
                       ["p8_f", "850 hPa airflow strength"], ["p8_z", "850 hPa vorticity"], ["p8_v", "850 hPa meridional velocity"], ["p8_u", "850 hPa zonal velocity"],
                       ["p8th", "850 hPa wind direction"], ["p8zh", "850 hPa divergence"], ["shum", "Surface specific humidity"], ["s850", "Specific humidity at 850 hPa"],
                       ["s500", "Specific humidity at 500 hPa"], ["dswr", "Solar radiation"], ["lftx", "Surface lifted index"], ["pottmp", "Potential temperature"],
                       ["pr_wtr", "Precipitable water"],["prec", "Precipitable total"]]

    # will return file description e.g. Mean temperature at 2m if the fileName is found in the list file Description will be empty if it's not there
    fileDescription = [record[1] for record in fileDescriptionList if re.search(re.compile(record[0]),fileName) != None] # regex

    return fileDescription

def resetFiles(predictorSelected):
    """
    useless function does .clear()
    """
    return predictorSelected.clear()

def loadFilesIntoMemory(filesToLoad):
    """
    create an array with shape (amount of files, length of files) return that
    """
    loadedFiles = []
    for fileLocation in filesToLoad:
        loadedFiles.append(np.loadtxt(fileLocation))
    return loadedFiles

def increaseDate(startDate, noDays): #todo check if the leap year thing was important
    """increases datatime object by noDays"""
    # this might have to change back to orginal vb code as not sure why it was done the way it was
    finalDate = startDate + datetime.timedelta(days=noDays)

    if calendar.isleap(startDate.year):
        feb = datetime.datetime(startDate.year, 2, 29)
        if startDate <= feb <= finalDate:
            finalDate += datetime.timedelta(days=1)
    elif calendar.isleap(finalDate.year):
        feb = datetime.datetime(finalDate.year, 2, 29)
        if startDate <= feb <= finalDate:
            finalDate += datetime.timedelta(days=1)

    return finalDate

def sigLevelOK(sigLevelInput):
    """checks if sigLevel is good returns default diglevel if not"""
    correctSigValue = False
    sigLevel = 0.05
    if sigLevelInput == "" or not type(sigLevelInput) is int:              #SigLevelText is the input from the user
        #todo error message to user orgianl: MsgBox "Significance level must be a value.", 0 + vbCritical, "Error Message" 
        print("Significance level must be a value.")
    else:
        if sigLevelInput > 0.999 or sigLevelInput < 0:
            #todo error message to user orginal: MsgBox "Significance level must be positive and less than 1.", 0 + vbCritical, "Error Message"
            print("Significance level must be positive and less than 1.")
        else:
            if sigLevelInput == 0.1111:
                print("BlankFrm.Show") #todo figure out why this is here in the first place and what BlankFrm.Show does in vb
            else:
                sigLevel = sigLevelInput
                correctSigValue = True
    return correctSigValue, sigLevel

def fsDateOK(fSDate, feDate, globalSDate):
    """if date is okay return true if not return false"""

    output = False
    if not isinstance(fSDate, datetime.datetime):
        #todo error message to user about correct date orginal MsgBox "Start date is invalid - it must be in the format dd/mm/yyyy.", 0 + vbCritical, "Error Message"
        fSDate = globalSDate
        print("Start date is invalid - it must be in the format dd/mm/yyyy")
    elif (fSDate - feDate).days > 1:
        #todo error message to user about correct date orginal MsgBox "End date must be later than start date.", 0 + vbCritical, "Error Message"
        fSDate = globalSDate
        print("End date must be later than start date.")
        print(fSDate - feDate)
    elif (fSDate - globalSDate).days < 0:
        #todo error message to user about correct date orginal MsgBox "Fit start date must be later than record start date.", 0 + vbCritical, "Error Message"
        fSDate = globalSDate
        print("Fit start date must be later than record start date.")
    else:
        output = True 
    return output

def feDateOK(fsDate, feDate, globalEDate):
    """if date is okay return true if not return false"""

    output = False
    if not isinstance(feDate, datetime.datetime):
        #todo error message to user about correct date orginal MsgBox "End date is invalid - it must be in the format dd/mm/yyyy.", 0 + vbCritical, "Error Message"
        fsDate = globalEDate 
        print("End date is invalid - it must be in the format dd/mm/yyyy.")
    elif (fsDate - feDate).days > 1:
        #todo error message to user about correct date orginal MsgBox "End date must be later than start date.", 0 + vbCritical, "Error Message"
        feDate = globalEDate
        print("End date must be later than start date.")
    elif (feDate - globalEDate).days > 0:
        #todo error message to user about correct date orginal MsgBox "Fit end date must be earlier than record end date.", 0 + vbCritical, "Error Message"
        feDate = globalEDate
        print("Fit end date must be earlier than record end date.")
        print((feDate - globalEDate).days >= 0)
    else:
        output = True 
    return output
   
def findDataStart(predictandFile): # gets predictand numpy array then gets the position of the first data position
    """ this gets the first data index where the predictand is not a -999"""
    firstData = predictandFile[predictandFile != -999] #todo change to missing code
    if firstData.size == 0:
        return None  # All values are errors
    return np.where(predictandFile == firstData[0])[0][0]

def dateWanted(date, analysisPeriodChosen):
    """returns true  if analysis period chosen and date match otherwise false"""
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

def checkForFile(file, errorMessage):
    if file is None:
        print(errorMessage)
        return False
    else:
        return True
    
def checkIfFileFormatted(file):
    #Only checks the first line, not ideal but this is how it's done in the original
    with open(file) as f:
        firstLine = f.readline()
        if len(firstLine) > 15:
            print("File may contain multiple columns or non-Windows line breaks / carriage returns. This may cause problems in SDSM later.")
    
    f.close()
    return


if __name__ == '__main__':
    #Module tests go here
    date1 = thirtyDate(2025, 4, 1)  # March 30, 2025 (in this system, all months have 30 days)
    print(date1)
    date2 = thirtyDate(2025, 5, 1)
    print(date2)
    date3 = datetime.date(2025, 4, 1)  # March 30, 2025 (in this system, all months have 30 days)
    print(date3)
    date4 = datetime.date(2025, 5, 1)
    print(date4)
    print(date1 - date2)
    print((date3 - date4).days)