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

def plotMultiple(fieldGroup, statGroup, fieldIds, line):
    if line:
        plt.title("SDSM Line Chart")
    else:
        plt.title("SDSM Bar Chart")

    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    width = 0.4

    for i in range(len(fieldIds)):
        data = []
        
        fields = fieldGroup[i]
        stats = statGroup[i]
        fieldId = fieldIds[i]

        for month in range(12):
            data.append(float(stats[month][fieldId]))

        if line:
            plt.plot(data, label = "File " + str(i + 1) + ": " + fields[fieldId])
        else:
            plt.bar(np.arange(12) + (width * i), data, 0.4, label = "File " + str(i + 1) + ": " +  fields[fieldId])
    
    plt.xticks(np.arange(12), months)
    plt.legend()
    plt.show()

if __name__ == "__main__":
    fields1, stats1 = readSumStatsFile(r"C:\Users\ajs25\Downloads\precOut.dat")
    fields2, stats2 = readSumStatsFile(r"C:\Users\ajs25\Downloads\tempOut.dat")

    plotMultiple([fields1, fields2], [stats1, stats2], [0, 0], False)