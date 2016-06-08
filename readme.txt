
This repository contains code and data for "Identification and Empirical Analysis of 
Amazon EC2 Spot Instance Features for Cost-Effective Tenant Procurement" (http://www.cse.psu.edu/~bhuvan/CSE-TR-16-006.pdf).

|--- trace analysis
MATLab code and data for prediction of the key features for modeling spot prices. "Lb" denotes the lifetime of a spot instance under bid b and "ES" (or "es") denotes the expected average spot price during Lb.

|--- data store
MATLab code and data for the trace-driven simulation of the in-memory data store case study; python code and input data for the 24-hour real-world experiments on Amazon EC2 using Memcacahed as a case study.

|--- batch processing
MATLab code and code for the trace-driven simulation of the batch processing case study; python code and input data for the 24-hour real-world experiments on Amazon EC2 with synthetic batch jobs (the ami used for batch jobs can be replaced by customized batch jobs).

License

The code and data are released under the Apache 2.0 license. 
Copyright (C) 2016 Cheng Wang, Qianlin Liang
