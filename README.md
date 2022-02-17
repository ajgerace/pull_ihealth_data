# Pull Qkview data from iHealth

pull_ihealth_data.py is a python script that will pull data from a qkview previously uploaded to iHealth.f5.com.  
It output a markdown file <device name>_output.md that includes output from various commands (ie. show /sys cpu) and links to images of 30 Day graphs (ie. System CPU).
You'll be prompted for your iHealth credentials and the qkview ID number. The qkview ID number is the 8 digit number after '/qv/' in the URL. 
This script was written for python3 and has been tested with python 3.6.8

Prerequisites:
Install the following pip modules:  requests and xmltodicts
`sudo pip3 install requests xmltodicts`


To run pull_ihealth_data:
`python3 pull_ihealth_data.py`

You will be prompted for your iHealth UserID and password, qkview ID  (multiple qkviews ID can be processed at the same time by separating them by a space ) and customer.
It will create subfolder for qkview_output and a subfolder for the provided customer name if they do not already exist.


Sample run:
```$ python3 pull_ihealth_data.py
Enter your iHealth User ID: a.user@example.com
Enter your iHealth password: 
Enter qkview id: 12345678
Enter customer name: internal

Gatherig command output for bigip.example.com qkview number 12345678
```

