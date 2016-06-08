|--- spot_simulation.py
A python script that simulates the batch processing over three months.
Inputs are in folders of "zone1" and "zone2" (spot prices, Lb and ES)

|--- evaluation.m
MATLab code that takes the output of spot_simulation.py as input, then computes the monetary costs for the simulation.

|--- workload.txt ... workload_size=4.txt  
These are the workload time-series with different configurations of arrival rates and average execution time (if no failure and given one full core)
The first column is the arrival time (minute) of a job, and the second column is the expected execution time (in minutes) of that job.
