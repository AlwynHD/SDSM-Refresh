import numpy as np
months = [[],[],[],[],[],[],[],[],[],[],[],[]]
lastMonth = 0
currentMonth = 0
nVariables = 2
missingCode = -999
totalFalseMissingCode = 0

for i in range(1,12):
    if lastMonth != currentMonth:
        other = np.full((1,2), missingCode, dtype=int)
        months[lastMonth] = np.concatenate((months[lastMonth], other))
        totalFalseMissingCode += 1
        lastMonth = currentMonth
    
    
    other = np.empty((1,2), dtype=int)
    if len(months[currentMonth]) == 0:
        print("HERE")
        print(months[currentMonth], other)
        months[currentMonth] = other
    else:
        months[currentMonth] = np.concatenate((months[currentMonth], other))
    
    if i == 7:
        currentMonth = 7
    if i == 4:
        currentMonth = 4

#The data comes in and then if the lastmonth and currentmonth are different then you add missing code to the last month, 
# move on the next month after that and past the data in, 
print("FINISHED")

for array in months:
    print(array, 'i')