#!/usr/bin/python3
# pull_ihealth_data.py       
# version: 1.0

from datetime import datetime
import requests, sys, os, getpass
import json,xmltodict,base64

t = datetime.now()
timestamp = t.strftime('%d-%b-%Y')

url = "https://api.f5.com/auth/pub/sso/login/ihealth-api"

#check for credentials stored on disk
if os.path.isfile('.credentials'):
  f = open('.credentials', 'r')
  creds_encoded = f.readline()
  f.close()
  creds_payload = base64.b64decode(creds_encoded).decode(encoding='UTF-8')
else:
  uID = input('Enter your iHealth User ID: ')
  userID = uID.strip()
  uPass = getpass.getpass('Enter your iHealth password: ')
  userPass = uPass.strip()
  payload = { "user_id": userID, "user_secret": userPass } 
  creds_payload = json.dumps(payload)

headers = {
  'Content-Type': 'application/json',
}
# dictionary of tmsh commands to retrieve from the qkview
dictCommands = {
  'show /sys hardware': "2072d0f40823cb2c812917008231014eb4afd456", 
  'show /sys host-info global': "27b3a0fad26441d792a9d8b041de2a7e44caccef",
  'show /cm failover-status': "e161b8be18af33223a4f3b345aa6d6ca9645dcdf",
  'show /net interface all-properties': "b8cf79d200280103db9dd185d33534abe7787521",
  'list /net route all-properties': "99836b03669ea8fea198a6b902bbbf3f216fc44c",
  'list /net self all-properties': "f3003fb294ca13c5d8a6ec4f1517d6f0bf7e60ac",
  'list /net trunk all-properties': "fed6f349ee7659d4ca7428439492fbcd2ba84874",
  'list /net tunnels all-properties': "4e044fe405f1a6b1527c2975d82db522c6140603",
  'show /net vlan all-properties': "6ee0d0c49b00a0fac1b798743fe8a0d1090b0782",  
  'list /sys provision all-properties': "c12723edf7dedb01e5430fe6077a12ec07ef4e14",
  'show /sys cluster all-properties': "72baf3c23dc373651b173bb4799ad53a3936199d",
  'show /sys cluster memory': "431a98c34bcac36b23c2c1003d3854834521dfe9",
  'show /sys cpu': "81aab6fd832ed03b46618cc17c5ec6606eda26b5",
  'list /vcmp guest all-properties': 'a1db1d50065f454fb1dcea7b90ce9e5c4f73383d'
}
# dictionary of performance graphs
dictGraphs = {
  'active_connections': 'activecons',
  'by_core_cpu': 'blade0cpucores',
  'system_CPU': 'CPU',
  'cpu_plane': 'detailplanestat',
  'memory_breakdown': 'memorybreakdown',
  'new_connections': 'newcons',
  'throughput': 'throughput'
}

# auth request
response = requests.request("POST", url, headers=headers, data=creds_payload)
cookies = response.cookies
if response.status_code != 200:
  print('Authentication error - ' + response.text )
  sys.exit()
  
# check for list of qkviews to retrieve , else prompt for qkview id
if os.path.isfile('qkviews.txt'):
  f = open('qkviews.txt', 'r')
  qkviewList = f.read().splitlines()
  f.close()
else:
  qk = input('Enter qkview id: ')
  qkviewList = qk.split(' ')
  custName = input('Enter customer name: ') 
  path = 'qkview_output/' + custName 
if not os.path.exists(path):
  os.makedirs(path)


#loop through list of qkviews
for qkviewNum in qkviewList:
  outputStr = ''
  if '\n' in qkviewNum:
    qkviewNum = qkviewNum.strip()

  # retrieve hostname and chassis serial number
  url = "https://ihealth-api.f5.com/qkview-analyzer/api/qkviews/" + str(qkviewNum)
  response = requests.request("GET", url, cookies=cookies, headers=headers)
  dictOut = xmltodict.parse(response.text)
  chassis_serial = dictOut['qkview']['chassis_serial']
  hostName = dictOut['qkview']['hostname']
  gDate = dictOut['qkview']['generation_date'] 
  gDate2 = int(gDate) / 1000.0
  genDate = datetime.fromtimestamp(gDate2).strftime('%d-%b-%Y %H:%M:%S')

  outputStr += '## Device: ' + hostName + '\n'
  outputStr += '## Serial Number: ' + chassis_serial + '\n'
  outputStr += '## Generation Date: ' + genDate + '\n'
#  outputStr += '\n'
  print('Gathering command output for ' + hostName + ' qkview number ' + qkviewNum + '\n' )

# Retrieve running version
  url = "https://ihealth-api.f5.com/qkview-analyzer/api/qkviews/" + str(qkviewNum) + "/commands/3af0d910d98f07b78ac322a07920c1c72b5dfc85"
  response = requests.request("GET", url, cookies=cookies, headers=headers)
  if response.status_code == 200:
    dictOut = xmltodict.parse(response.text)
    encoded = dictOut['commands']['command']['output'] 
    if len(encoded) % 4 == 3:
      encoded += '='
    elif len(encoded) % 4 == 2:
      encoded += '=='
    
    decoded_cmdOut = base64.b64decode(encoded).decode(encoding='UTF-8').split('\n')
    for line in decoded_cmdOut:
      fields = line.split(' ')
      if len(fields) > 1:
        if fields[2] == 'yes':
          version = '## BIG-IP Version: ' + fields[7] + '.' + fields[9] + '\n'
    outputStr += version + '\n'

   # retrieve command output from qkview
  for key in dictCommands:
    cmdName = key 
    cmdId = dictCommands[key]
    url = "https://ihealth-api.f5.com/qkview-analyzer/api/qkviews/" + str(qkviewNum) + "/commands/" + str(cmdId)
    response = requests.request("GET", url, cookies=cookies, headers=headers)
    if response.status_code == 200:
      dictOut = xmltodict.parse(response.text)
      encoded = dictOut['commands']['command']['output'] 
      if len(encoded) % 4 == 3:
        encoded += '='
      elif len(encoded) % 4 == 2:
        encoded += '=='
      outputStr += '\n### ' + cmdName + '\n'
      decoded = base64.b64decode(encoded).decode(encoding='UTF-8')
      outputStr += '```' + decoded + '```\n'

  outputStr += '\n'
  fileName = path + '/' + hostName + '_' + timestamp + '_output_qkview.md'
  f = open(fileName, 'w')
  f.write(outputStr)
  f.close()


  for key in dictGraphs:
    label = key 
    graphName=dictGraphs[key]
    url = "https://ihealth-api.f5.com/qkview-analyzer/api/qkviews/" + str(qkviewNum) + "/graphs/" + graphName + "?timespan=30_days"
    response = requests.request("GET", url, cookies=cookies, headers=headers)
    if response.status_code == 200:
      imgFile = hostName + '_' + label +  '_' + timestamp + '.png' 
      imgFileName = path + '/' + imgFile
      f = open( imgFileName, 'wb')
      f.write(response.content)
      f.close()
      outputStr += "---\n### " + label + "\n![" + label + "](" + imgFile+ ")\n\n"
    else: 
      print('Unable to retrieve graph ' + label + ' ' + str(response.status_code)  + ' ' + response.text )

  f = open(fileName, 'w')
  f.write(outputStr)
  f.close()

