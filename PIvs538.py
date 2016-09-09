'''
PIvs538.py

Compares FiveThirtyEight's odds for their "states to watch" with PredictIt
prices for each.
PI prices are grabbed from their API, but 538 odds are manually entered below.
538 doesn't seem to have an API, but it would be nice to find a way to scrape
their data.

Jack Enneking
2016-09-08

'''

import requests
import pprint
from time import sleep


############  FiveThirtyEight data  ############

fteStates = {
	'AZ': (33.2, 66.8),
	'CO': (75.9, 23.9),
	'FL': (61.4, 38.6),
	'GA': (29.7, 70.2),
	'IA': (47.5, 52.5),
	'MI': (74.4, 25.5),
	'MN': (79.5, 20.2),
	'NV': (66.4, 33.5),
	'NH': (68.0, 31.8),
	'NC': (56.0, 43.9),
	'OH': (55.1, 44.8),
	'PA': (74.8, 25.2),
	'VA': (81.7, 18.2),
	'WI': (70.8, 29.1),
}


############  Get PredictIt data  ############

tries = 5

def getContentDict(url, tries=5, delay=1):
	for i in range(tries):
		r = requests.get(url)
		if r.status_code == 200 and r.content != b'null':
			return(r.json()['Contracts'])
		sleep(delay)
	raise

urlBase = "https://www.predictit.org/api/marketdata/ticker/"	# all urlBase belongs to us
suffix = "USPREZ16"
piStates = {
	'AZ': {'dem': None,'gop': None},
	'CO': {'dem': None,'gop': None},
	'FL': {'dem': None,'gop': None},
	'GA': {'dem': None,'gop': None},
	'IA': {'dem': None,'gop': None},
	'MI': {'dem': None,'gop': None},
	'MN': {'dem': None,'gop': None},
	'NV': {'dem': None,'gop': None},
	'NH': {'dem': None,'gop': None},
	'NC': {'dem': None,'gop': None},
	'OH': {'dem': None,'gop': None},
	'PA': {'dem': None,'gop': None},
	'VA': {'dem': None,'gop': None},
	'WI': {'dem': None,'gop': None},
}

for state in sorted(piStates):
	print("Get prices for " + state + " ... ", end="", flush=True)
	
	url = urlBase + state + "." + suffix
	
	try:
		contracts = getContentDict(url, 5)
	except:
		print("fail!")
	else:
		print("good!")
		for contract in contracts:
			if contract['Name'] == "Democratic":
				piStates[state]['dem'] = contract['BestBuyYesCost']
			elif contract['Name'] == "Republican":
				piStates[state]['gop'] = contract['BestBuyYesCost']
			else:
				print("Something fishy, though.")

print("")


############  Printing  ############

colWidths = [4,3,4,4]

def addSign(n):
	if int(n) > 0:
		s = "+" + format(n, '0.0f')
	else:
		s = format(n, '0.0f')
	return s

header1 = " ".join((
	"|".rjust(6),
	"Democrat".center(sum(colWidths[1:3]) + 6),
	"|",
	"Republican".center(sum(colWidths[1:3]) + 6)
))

header2 = " ".join((
	"State|".rjust(6),
	"538".rjust(colWidths[1]),
	"PI".rjust( colWidths[2]),
	"dif".rjust(colWidths[3]),
	"|",
	"538".rjust(colWidths[1]),
	"PI".rjust( colWidths[2]),
	"dif".rjust(colWidths[3]),
))

print(header1)
print(header2)
print('-' * len(header2))

for state in sorted(piStates):
	fteDemNormal = fteStates[state][0] / 100
	fteDemPercent = format(fteDemNormal * 100, '0.0f') + "%"
	piDemNormal = piStates[state]['dem']
	piDemPercent = format(piDemNormal * 100, '0.0f') + "\u00A2"
	demDiff = addSign((piDemNormal - fteDemNormal) * 100)
	
	fteGopNormal = fteStates[state][1] / 100
	fteGopPercent = format(fteGopNormal * 100, '0.0f') + "%"
	piGopNormal = piStates[state]['gop']
	piGopPercent = format(piGopNormal * 100, '0.0f') + "\u00A2"
	gopDiff = addSign((piGopNormal - fteGopNormal) * 100)
	
	print(
		state.rjust(        colWidths[0]),
		"|",
		fteDemPercent.rjust(colWidths[1]),
		piDemPercent.rjust( colWidths[2]),
		demDiff.rjust(      colWidths[3]),
		"|",
		fteGopPercent.rjust(colWidths[1]),
		piGopPercent.rjust( colWidths[2]),
		gopDiff.rjust(      colWidths[3]),
	)
