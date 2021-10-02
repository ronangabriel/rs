import numpy as np
from bs4 import BeautifulSoup
import requests
import urllib.request
import json
import sched
import time
from datetime import datetime


# set and request url; extract source code for exchange limits
url = "https://oldschool.runescape.wiki/w/Grand_Exchange/Buying_limits"
html = requests.get(url)

#parse raw html => soup object
#soup = BeautifulSoup(html.text, 'html.parser')
soup = BeautifulSoup(html.text, 'xml')

# extract exchange limits for all items
print('Extracting exchange limits for all items...')
table = soup.find('table', attrs={'class':'wikitable align-right-2 sortable'})
tableBody = table.find('tbody')

limitData = np.empty((2,))
rows = tableBody.find_all('tr')
for row in rows:
    cols = row.find_all('td')
    cols = [item.text.strip() for item in cols]
    if cols:
        limitData = np.column_stack((limitData, np.array([item for item in cols if item])))
limitData = np.delete(limitData, 0, axis=1)
print('Done.')

# delete extra string tags
extraStrings = [' (tablet)', ' (flatpack)', ' (beige)', ' (blue)', ' (brown)', ' (red)', ' (white)', ' (pointed)', ' (round)',
                ' (bottom)', ' (top)', ' (bagged)', ' (item)']
pos = 0
for itemName in limitData[0]:
    for extraString in extraStrings:
        if extraString in itemName:
            limitData[0][pos] = limitData[0][pos].replace(extraString, '')
    pos = pos + 1

limits = dict((limitData[0][i], limitData[1][i]) for i in range(len(limitData[0])))


def getData():
    # set and request url; extract GE data (15 mins)
    with urllib.request.urlopen("http://rsbuddy.com/exchange/summary.json") as url:
        geData = json.loads(url.read().decode())

    # add buy_limit to GE info
    validItems = 0
    invalidItems = 0
    for key in geData:
        item = geData[key]
        name = item['name']
        if name in limits:
            validItems = validItems + 1
            limit = limits[name]
            item['buy_limit'] = limit
        else:
            invalidItems = invalidItems + 1
            item['buy_limit'] = 0
    print('Call time: ' + str(datetime.now()))
    print('Valid items: ' + str(validItems))
    print('Invalid items: ' + str(invalidItems))

    print('Writing to file... ')
    with open('/project1/rs/data3.txt', 'a') as writeFile:
        writeFile.write(json.dumps(geData))
        writeFile.write('\n')
    print('Done.')

s = sched.scheduler(time.time, time.sleep)
numNoints = 10000 # total number of calls
inc = 15*60 # time between calls in minutes
now = time.time()
for x in range(numPoints):
    s.enterabs(now + (inc * x), 1, getData)
s.run()
