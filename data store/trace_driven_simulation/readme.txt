|--- trace
This folder contains code and data used to estimate Lb and ES in different scenarios.
	 ./get_actual_LB_ES.m
	 Obtain the actual Lb and ES from the spot price trace based on the bid 
	 ./get_LB_ES_new.m
	 Obtain the predicted Lb and ES from the spot price trace using the proposed approach
	 ./get_LB_ES_CDF.m
	 Obtain the predicted Lb and ES from the spot price trace using the CDF-based approach
	 ./get_LB_ES_max.m
	 Obtain the predicted Lb and ES from the spot price trace under the maximum allowed bid price.
	 ./plot_dataloss.m
	 Plot the histogram of data loss based on results of the trace-driven simulation.
	
|--- cost_statistics.xslx
This file contains the cost split from the three-month trace-driven simulation under different strategies.

|--- opt.m
MATLab code that computes the optimal solution for the trace-driven simulation.

|--- Ct.mat, Mt.mat
Inputs of opt.m. Ct and Mt are the number of cores and the amount of RAM needed, respectively, generated based on the predicted arrival rates and working set size (from offline performance profiling).

	 