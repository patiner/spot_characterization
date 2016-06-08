This folder contains python codes and inputs for setting up and running the prototype system on Amaozn EC2.

The system has four basic components:
--- A controller node that runs controller.py and make resource scaling decisions as well as controlling the experiment flow in a global fashion.
--- YCSB nodes (one or more) that run the modified ycsb code in ycsb.zip as workload generator
--- Mcrouter nodes (one or more) that run the Facebook Mcrouter as load balancer. Mcrouter and YCSB can be co-located on the same node to reduce latency.
--- Memcached nodes (one or more) that run the modified Memcached code in memcached-1.4.24-modified.zip as cache nodes.

To run:

1. Configure YCSB and Mcrouter
1.1 Launch an EC2 instance.
1.2 Install the modified ycsb on the instance using ycsb.zip (instructions in YCSB-readme.txt)
1.3 Install mcrouter (https://github.com/facebook/mcrouter).
1.4 Copy "mcrouter_daemon.py" to the new instance and then create an AMI Image for this instance.
1.5 Start YCSB-Mcrouter nodes with the maximum anticipated number of instances using the above AMI image
1.6 put the private IPs of these nodes into "mcrouter_list.txt"
1.7 Run "Python mcrouter_daemon.py" on each instance

2. Configure Memcached
2.1 Launch an EC2 instance and install Docker container on it.
1.2 Create a Docker container and install the modified memcached (memcached-1.4.24.zip) in the container.
1.3 Create a container images with the name of "memcached_img"
1.4 Copy "memcached_daemon.py" to the new instance and then create an AMI image for this instance.
1.5 Start Memcached nodes with the maximum anticipated number of spot and on-demand instances, respectively, using the above AMI image
1.6 put the private IPs of these nodes into "memcached_od_list.txt" and "memcached_spot_list.txt", respectively.
1.7 Run "Python memcached_daemon.py" on each instance.

3. Start experiment
3.1 Launch an EC2 instance as the controller node.
3.2 Copy all text files (in particular mcrouter_list.txt, memcached_od_list.txt and memcached_spot_list.txt) and python codes in this directory "prototype_implementation" to the new instance
3.3 create a folder "results" in the new instance
3.4 Run "Python controller.py"
3.5 The realtime monitoring results can be collected under the folder "results"







|--- cdf_based
This folder contains inputs for the CDF-based approach. By default, we use m3.large in us-east-1c and us-east-1d 
with bid equal to OD and 5*OD wherein OD is the on-demand price.
	 ./on_demand.txt ... ./us_east_1d_5OD.txt
	 Inputs for the CDF-based approach. In on_demand.txt, the columns denote "num of cores", "RAM in GB", "hot weight" and "cold weight", respectively.
     In other files, the columns denote "num of instances", "hot weight" and "cold weight", respectively.

|--- only_od 
|--- prop
These folders contain inputs for BL-OD and PROP, respectively.

|--- price_1.txt, price_2.txt
24-hour spot prices (per minute) used in our experiments

|--- workingset_actual.txt, arrival_actual.txt
Normalized dynamic workingset and arrival rates (per hour)

|--- random_seed.txt
Random seeds used by YCSB to generate key requests in each hour following the scramble-zipfian distribution.
	 