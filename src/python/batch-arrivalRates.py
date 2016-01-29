import sys
import numpy as np
sys.path.append("~/projects/net-queue/src/python")
from qnet import *

step = float(0.01)
rates = 3


paramsInst = parameters("/home/chase/projects/net-queue/data/params/QNet3params.txt")

utilizationStats = np.zeros((rates,paramsInst.adjacency.shape[0]))
averageWaitTime = np.zeros((rates,2))

for jj in range(rates):
    paramsInst.lambd = paramsInst.lambd + step
    QNet = blockfaceNet(paramsInst, ["utilization"])
    while QNet.timer < QNet.params.simulation_time:
        #find block numbers of blocks with <=0.0 time till next arrival
        #can use itertools.compress on new arrivals list comprehension
        currently_arriving_blocks = [ j for j, x in enumerate(list(QNet.new_arrivals)) if x < QNet.params.time_resolution ]
        if len(currently_arriving_blocks) > 0:
           #give arriving blocks new arrivals
            #prioritize exogenous arrivals
            for i in currently_arriving_blocks:
	            blockindex = QNet.injection_map[i]
	            next_arrival_time = np.random.exponential(QNet.bface[blockindex].arrival_rate)
	            QNet.new_arrivals[i] = next_arrival_time 
	            QNet.bface[blockindex].exogenous += 1
	            QNet.carIndex += 1
	            QNet.cars[QNet.carIndex] = car(QNet.carIndex)
	            #try to park, otherwise, drive somewhere else
	            QNet.park(blockindex, QNet.carIndex)
    
        for origin in QNet.bface.keys():
            #Checking for any drivers arriving at other blocks based on travel time in street buffer
            #have to loop through every block? Yes, if I care about street direction
            for dest in range(len(QNet.streets[origin])):
	            #for each possible destination index, get the block index, neighbors is list of block indexs connected to origin
	            #but dest is local index of street connected to origin to save space, 
	            #e.g. block 2 to block 3 is connected by block 2's street 1
	            destblock = QNet.bface[origin].neighbors[dest]
	            #at least first driver needs to be arriving
	            if len(QNet.streets[origin][dest]) > 0 and QNet.streets[origin][dest][0][1] < QNet.params.time_resolution:
	                #first driver in list will always be closest to 0
	                for driver in QNet.streets[origin][dest]:
		                #could be more than one arriving
		                while QNet.streets[origin][dest][0][1] < QNet.params.time_resolution:
		                    carIndex = QNet.streets[origin][dest][0][0]
		                    QNet.park(destblock, carIndex)
		                    #Get rid of first driver, go back up and check if next driver is also arriving
		                    QNet.streets[origin][dest].pop(0)
		                    if len(QNet.streets[origin][dest]) == 0:
			                    break
    
        #step simulation forward and collect any flagged global stats
        QNet.step_time(supress=False)

    for i in QNet.bface.keys():
        utilizationStats[jj, i+1] = float(sum(QNet.bface[i].utilization))/float(len(QNet.bface[i].utilization))
    #calculate average wait time
    total = 0.0
    numCars = float(len(QNet.cars.keys()))
    for carInd in QNet.cars.keys():
        total += QNet.cars[carInd].totalDriveTime
        averageWait = total/numCars
    averageWaitTime[jj,1] = averageWait
    utilizationStats[jj,0] = QNet.params.lambd
    averageWaitTime[jj,0] = QNet.params.lambd

avgOut = ("~/projects/net-queue/data/scratch/averageWait" + str(np.random.randint(1,100000)) + ".txt")
avgFile = open(avgOut, 'w')
utilizationOut = ("~/projects/net-queue/data/scratch/utilization" + str(np.random.randint(1,100000)) + ".txt")
utilFile = open(utilizationOut, 'w')

np.savetxt(avgFile, averageWaitTime, delimiter=",")
np.savetxt(utilFile, utilizationStats, delimiter=",")
