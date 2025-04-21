import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
try:
    from src.lib.utils import getSettings
except ModuleNotFoundError:
    from utils import getSettings

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

        #Get headings (might include: mean, maximum, minimum, etc)
        if populateFields:
            fields = line.split(",")[1:]
            populateFields = False

        #Get values for these headings
        if populateStats:
            newStatLine = line.split(",")[1:]
            newStatLine = [entry.strip() for entry in newStatLine]
            stats.append(newStatLine)

        #Split character
        #First encounter says we need to populate field
        #Second encounter says we need to populate stats
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
    width = 0.8 / len(fieldIds)

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
            plt.bar(np.arange(12) + ((-0.4 + (width * i)) + (width / 2)), data, width, label = "File " + str(i + 1) + ": " +  fields[fieldId])
    
    plt.xticks(np.arange(12), months)
    plt.axhline(color = "black", linewidth = 0.75)

    plt.grid(linewidth = 0.5)
    plt.minorticks_on()
    plt.grid(which="minor", linewidth = 0.25)

    plt.legend()
    plt.show()

if __name__ == "__main__":
    fields1, stats1 = readSumStatsFile(r"C:\Users\ajs25\Downloads\precOut.dat")
    fields2, stats2 = readSumStatsFile(r"C:\Users\ajs25\Downloads\tempOut.dat")

    plotMultiple([fields1, fields2], [stats1, stats2], [0, 2], True)