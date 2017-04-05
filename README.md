# NASA Fansite Analytics Challenge
## Getting Started
This repository contains a solution to the NASA fansite analytics challenge (described below by the original challenge text). The input log data is not included
in this repository. To run the script input ./run.sh into a unix shell. 

Two optional arguments: -n and -t. The option -n finds the 10 busiest windows in time (60-minutes by default) that do not overlap one another. The option 
-t prints to console the time elapsed to: complete total processing of the log data, complete feature computations, and write feature data to file.

## Prerequisites
Download and Install Python 2.7: https://www.python.org/download/releases/2.7/

Download and Install Pandas: http://pandas.pydata.org/pandas-docs/stable/install.html

## Challenge Summary

Picture yourself as a backend engineer for a NASA fan website that generates a large amount of Internet traffic data. Your challenge is to perform basic analytics on the server log file, provide useful metrics, and implement basic security measures. 

The desired features are described below: 

### Feature 1: 
List the top 10 most active host/IP addresses that have accessed the site.

Write to a file, named hosts.txt, the 10 most active hosts/IP addresses in descending order and how many times they have accessed any part of the site. 
There should be at most 10 lines in the file, and each line should include the host (or IP address) followed by a comma and then the number of times it accessed the site.

### Feature 2: 
Identify the 10 resources that consume the most bandwidth on the site

These most bandwidth-intensive resources, sorted in descending order and separated by a new line, should be written to a file called resources.txt

### Feature 3:
List the top 10 busiest (or most frequently visited) 60-minute periods 

Write to a file named hours.txt, the start of each 60-minute window followed by the number of times the site was accessed during that time period. The file should contain at most 10 lines with each line containing the start of each 60-minute window, 
followed by a comma and then the number of times the site was accessed during those 60 minutes. The 10 lines should be listed in descending order with the busiest 60-minute window shown first

### Feature 4: 
Detect patterns of three failed login attempts from the same IP address over 20 seconds so that all further attempts to the site can be blocked for 5 minutes. Log those possible security breaches (blocked.txt).

## Description of Data

Assume you receive as input, a file, `log.txt`, in ASCII format with one line per request, containing the following columns:

* **host** making the request. A hostname when possible, otherwise the Internet address if the name could not be looked up.

* **timestamp** in the format `[DD/MON/YYYY:HH:MM:SS -0400]`, where DD is the day of the month, MON is the abbreviated name of the month, YYYY is the year, HH:MM:SS is the time of day using a 24-hour clock. The timezone is -0400.

* **request** given in quotes.

* **HTTP reply code**

* **bytes** in the reply. Some lines in the log file will list `-` in the bytes field. For the purposes of this challenge, that should be interpreted as 0 bytes.


e.g., `log.txt`

    in24.inetnebr.com - - [01/Aug/1995:00:00:01 -0400] "GET /shuttle/missions/sts-68/news/sts-68-mcc-05.txt HTTP/1.0" 200 1839
    208.271.69.50 - - [01/Aug/1995:00:00:02 -400] "POST /login HTTP/1.0" 401 1420
    208.271.69.50 - - [01/Aug/1995:00:00:04 -400] "POST /login HTTP/1.0" 200 1420
    uplherc.upl.com - - [01/Aug/1995:00:00:07 -0400] "GET / HTTP/1.0" 304 0
    uplherc.upl.com - - [01/Aug/1995:00:00:08 -0400] "GET /images/ksclogo-medium.gif HTTP/1.0" 304 0
    ...

## Author
* **Louis Jacome** - [luissson](https://github.com/luissson/)