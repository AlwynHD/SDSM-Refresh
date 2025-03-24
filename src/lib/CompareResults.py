import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
try:
    from src.lib.utils import loadFilesIntoMemory, selectFile
except ModuleNotFoundError:
    from utils import loadFilesIntoMemory, selectFile

globalSDate = dt.date(1948, 1, 1)
globalEDate = dt.date(2015, 12, 31)
globalMissingCode = -999
thresh = 0

def readSumStatsFile(path):
    """ Reads in a file produced by the the summary statistics screen.
        File is read using the same method as the original SDSM."""
    fields = []
    stats = []

    populateFields = False
    populateStats = False

    file = open(path, "r")
    for line in file:
        line = line[:-1]

        if populateFields:
            fields = line.split(",")[1:]
            populateFields = False

        if populateStats:
            #List comprehension just removes whitespace from line
            stats.append([newStat[:-1] for newStat in line.split(", ")[1:]])

        if line == "-":
            if len(fields) == 0:
                populateFields = True
            else:
                populateStats = True
    return fields, stats

def plotLine(fields, stats, fieldId):
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    data = []

    for i in range(12):
        data.append(float(stats[i][fieldId]))

    print(data)
    plt.title("SDSM Line Chart")
    plt.plot(months, data)
    plt.show()

fields, stats = readSumStatsFile(r"C:\Users\ajs25\Downloads\precOut.dat")
plotLine(fields, stats, 0)