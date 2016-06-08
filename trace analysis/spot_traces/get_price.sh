#!/bin/bash

ec2_type="m3.medium
          m3.large
          m3.xlarge
          m3.2xlarge
          c3.large
          c3.xlarge
          c3.2xlarge
          c3.4xlarge
          c3.8xlarge
          r3.large
          r3.xlarge
          r3.2xlarge
          r3.4xlarge
          r3.8xlarge"

ec2_zone="us-east-1b
          us-east-1c
          us-east-1d
          us-east-1e"

for zone in $ec2_zone
do
  mkdir $zone
  for inst_type in $ec2_type
  do
    ec2dsph -a $zone -d Linux/UNIX -t $inst_type -s 2015-06-27T00:00:00 > $zone/$inst_type.txt
  done
done
