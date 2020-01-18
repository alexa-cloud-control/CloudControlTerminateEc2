#! /bin/bash

mkdir ../package 
cd ../../py/
pwd && ls -al
zip -g ../artifacts/package/CloudControlTerminateEc2.zip cloud_control_terminate_ec2.py