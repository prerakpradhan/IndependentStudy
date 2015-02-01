USPTO Data Pull
================
This repository contains the python code to pull down claim of Patents from 2014 uptil 2002 from the USPTO database currently on Google's Servers. The code was originally from [here](http://abel.lis.illinois.edu/UPDC/Tutorial.html). It has been modified to pull the claims from the USPTO database instead of the citation network. 

Run GrantsParser.py to start the download, parsing and uploading onto the mysql database. 

Use the schema.sql file provided to setup your mysql database first. 

Use a machine that has significant amount of RAM to do this. We noted that the process can consume upto 8GB of RAM. This is due to the use of ElementTree, which makes it easy to parse but is harsh on the memory. 

The process will take a long long time to complete, Have patience :)

