To run:
1. Launch a VM and install Docker container
2. deploy your batch job in the container (one job per container) and make a container image; then each batch job would be one instance of the container image.
We assume that one batch job only needs one full vCPU to achieve the expected execution time.
3. Create an AMI image for the above VM.
4. Launch an instance as the global controller for this experiment and copy all files from this directory to the controller.
5. Based on estimation of maximum number of spot and on-demand instances, modify the main() function in controller.py and set "spots, backups=get_vm(num_spot=10, num_backup=3)" accordingly.
6. In controller.py, change "EC2_AMI = 'ami-75636f1f'" to your AMI in step 3.
7. On the controller node, run "python controller.py"


|--- daemon/daemon.py
A python script that is waiting for the commands from the controller. It will be automatically started when launching a new instance. 
It can start a new job from a container image and collect statistics (execution time) of that job.  
It can also adjust the CPU shares of each job on the VM using Cgroups.

|--- controller/controller.py
A python script that automates the whole experiment: initializing instances, checking spot prices, adjusting CPU shares of jobs with failed primary copies, etc.
Note that you need to install Boto and paramiko for running certain AWS services/APIs on the controller. Here are the commands:
sudo apt-get update
sudo apt-get install python-pip -y
sudo pip install -U boto
sudo apt-get install python-paramiko
