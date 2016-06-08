before installation

apt-get update
apt-get upgrade
apt-get install openjdk7-jdk (this command might be wrong; you need to google it)
apt-get install maven




1. copy ycsb.zip to your linux (ubuntu) directory, e.g., /home/cheng for my case, and unzip it.

2. in the direcotry ycsb/YCSB-master, sudo vi ./pom.xml

- configure "chengPath" to your home directory, e.g., /home/cheng for my case. This folder points to the path of spymemcached-2.7.3.jar

3. copy ycsb/YCSB-master/spy-memcached-2.7.3.jar to the parent directory of "ycsb"

//3. in the directory ycsb/YCSB-master/memcached/, sudo vi ./pom.xml

//- configure "systemPath" to the path of your spymemcached. You might not need to modify it if step 2 is set up appropriately.

4. in workloads/workloada (there are five workloads by default, I'm taking workloada as an example)

set the following params according to your setup:

recordcount=1000
operationcount=1000
requestdistribution=zipfian
memcached.server=10.4.128.2:11211   (change the IP to your memcached server IP)
fieldcount=1
fieldlength=20


You can find the meaning from ./core/workloads/CoreWorkload.java

//5. go to ./core and run mvn clean package

6. go to ycsb/YCSB-master and run mvn clean package

---------

ready to run: just one example

1. warm up:

./bin/ycsb load memcached -P workloads/workloada  -s  -threads 50 > stats.dat

2. run test:

./bin/ycsb run memcached -P workloads/workloadc  -s  -threads 20 > stats.dat