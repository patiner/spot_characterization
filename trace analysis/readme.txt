|--- spot_traces
This folder contains spot price traces used in evaluation.
      |--- get_price.sh
	  A sample shell script that retrieves spot price history data from Amazon EC2
	  |--- extractprice.py
	  Python code that extracts spot prices from the raw output of get_price.sh
	  |--- price_time.py
	  Python code that convert the output of extractprice.py to a time-series of spot price (per minute).
	  
|--- COEF_window.m
MATLab code that computes the under-estimation rate of simultaneous revocations given two spot price traces, with different history window sizes

|--- Lb_window2.m
MATLab code that computes Lb and ES under different history window sizes.

|--- get_LB_overestimate_new.m
MATLab function that computes the over-estimation rate of Lb and relative deviation of ES