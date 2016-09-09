#
# PIvs538.py
# 
# Compares FiveThirtyEight's odds for their "states to watch" with PredictIt
# prices for each.
# PI prices are grabbed from their API, but 538 odds are manually entered below.
# 538 doesn't seem to have an API, but it would be nice to find a way to scrape
# their data.
# 
# Jack Enneking
# 2016-09-08
# 


import requests
from time import sleep


############  FiveThirtyEight data  ############
# It would be very nice to find a way to scrape this, but for now it has to be
# entered manually.
# Format: Democrat chance on the left, Republican on the right.

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

tries = 5	# Times to retry each request if it fails.

def getContentDict(url, tries=5, delay=1):
	# gets data from the API and starts parsing it
	for i in range(tries):
		r = requests.get(url)
		if r.status_code == 200 and r.content != b'null':	# PI gives a 200 for nonexistent markets, just with null contents.
			return(r.json()['Contracts'])	# Extracts the good bits: a list of the (two) contracts.
		sleep(delay)	# wait before retrying
	raise	# if all tries fail

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
}	# the main dict

for state in sorted(piStates):
	print("Get prices for " + state + "... ", end="", flush=True)	# Let the user know we're trying
	
	url = urlBase + state + "." + suffix	# e.g. "https://www.predictit.org/api/marketdata/ticker/AZ.USPREZ16"
	
	try:
		contracts = getContentDict(url, 5)
	except:
		print("fail!")
	else:
		print("good!")
		for contract in contracts:	# contracts should be a list of the two contracts for the state
			if contract['Name'] == "Democratic":
				piStates[state]['dem'] = contract['BestBuyYesCost']	# put the Y cost in the main dict
			elif contract['Name'] == "Republican":
				piStates[state]['gop'] = contract['BestBuyYesCost']	# put the Y cost in the main dict
			else:
				print("Something fishy, though.")	# not Democratic or Republican

print("")


############  Printing  ############

colWidths = [4,3,4,4]	# adjust table spacing here

def addSign(n):
	# formats diffs for printing
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
print('-' * len(header2))	# bar under headers

for state in sorted(piStates):	# sort to print alphabetically
	fteDemNormal = fteStates[state][0] / 100	# 538's prediction normalized to 0-1 scale
	fteDemPercent = format(fteDemNormal * 100, '0.0f') + "%"	# back up to percent scale and formatted for printing
	piDemNormal = piStates[state]['dem']	# PI price from main dict
	piDemPercent = format(piDemNormal * 100, '0.0f') + "\u00A2"	# formatted for printing with cent sign
	demDiff = addSign((piDemNormal - fteDemNormal) * 100)	# maybe I should just work in percent scale to begin with
	
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
	)	# the goods!
# Happy trading!