import numpy as np
from bs4 import BeautifulSoup
import requests
import urllib.request
import json
import sched
import time
from datetime import datetime
import helper_functions


# set and request url; extract source code for exchange limits
url = "https://oldschool.runescape.wiki/w/Grand_Exchange/Buying_limits"
html = requests.get(url)

#parse raw html => soup object
#soup = BeautifulSoup(html.text, 'html.parser')
soup = BeautifulSoup(html.text, 'xml')

# extract exchange limits for all items
print('Extracting exchange limits for all items...')
table = soup.find('table', attrs={'class':'wikitable align-right-2 sortable'})
table_body = table.find('tbody')

limit_data = np.empty((2,))
rows = table_body.find_all('tr')
for row in rows:
    cols = row.find_all('td')
    cols = [item.text.strip() for item in cols]
    if cols:
        limit_data = np.column_stack((limit_data, np.array([item for item in cols if item])))
limit_data = np.delete(limit_data, 0, axis=1)
print('Done.')

# delete extra string tags
extra_strings = [' (tablet)', ' (flatpack)', ' (beige)', ' (blue)', ' (brown)', ' (red)', ' (white)', ' (pointed)', ' (round)',
                ' (bottom)', ' (top)', ' (bagged)', ' (item)']
pos = 0
for item_name in limit_data[0]:
    for extra_string in extra_strings:
        if extra_string in item_name:
            limit_data[0][pos] = limit_data[0][pos].replace(extra_string, '')
    pos = pos + 1

limits = dict((limit_data[0][i], limit_data[1][i]) for i in range(len(limit_data[0])))


def get_data():
    # set and request url; extract GE data (15 mins)
    with urllib.request.urlopen("http://rsbuddy.com/exchange/summary.json") as url:
        ge_data = json.loads(url.read().decode())

    # add buy_limit to GE info
    valid_items = 0
    invalid_items = 0
    for key in ge_data:
        item = ge_data[key]
        name = item['name']
        if name in limits:
            valid_items = valid_items + 1
            limit = limits[name]
            item['buy_limit'] = limit
        else:
            invalid_items = invalid_items + 1
            item['buy_limit'] = 0
    print('Call time: ' + str(datetime.now()))
    print('Valid items: ' + str(valid_items))
    print('Invalid items: ' + str(invalid_items))

    print('Writing to file... ')
    with open('/home/pi/Desktop/py_scripts/data3.txt', 'a') as write_file:
        write_file.write(json.dumps(ge_data))
        write_file.write('\n')
    print('Done.')

s = sched.scheduler(time.time, time.sleep)
num_points = 5000 # total number of calls
inc = 15*60 # time between calls in minutes
now = time.time()
for x in range(num_points):
    s.enterabs(now + (inc * x), 1, get_data)
s.run()