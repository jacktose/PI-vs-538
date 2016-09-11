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


############  State objects  ############
# Create the main data structure: a list of objects, each representing a state.

class State:
	def __init__(self, abbr, name):
		self.abbr = abbr
		self.name = name

stateNames = {
	'AZ': "Arizona",
	'CO': "Colorado",
	'FL': "Florida",
	'GA': "Georgia",
	'IA': "Iowa",
	'MI': "Mississippi",
	'MN': "Minnesota",
	'NV': "Nevada",
	'NH': "New Hampshire",
	'NC': "North Carolina",
	'OH': "Ohio",
	'PA': "Pennsylvania",
	'VA': "Virginia",
	'WI': "Wisconsin",
}

states = []	# main data structure: list of state objects
for abbr in sorted(stateNames):	# they'll be printed in this order, so make alphabetical now
	name = stateNames[abbr]
	states.append(State(abbr, name))	# create the object and tack it onto the list

############  FiveThirtyEight data  ############
# It would be very nice to find a way to scrape this, but for now it has to be
# entered manually.
# Format: 

fteChances = {
	'AZ': {'dem': 33.2, 'rep': 66.8},
	'CO': {'dem': 75.9, 'rep': 23.9},
	'FL': {'dem': 61.4, 'rep': 38.6},
	'GA': {'dem': 29.7, 'rep': 70.2},
	'IA': {'dem': 47.5, 'rep': 52.5},
	'MI': {'dem': 74.4, 'rep': 25.5},
	'MN': {'dem': 79.5, 'rep': 20.2},
	'NV': {'dem': 66.4, 'rep': 33.5},
	'NH': {'dem': 68.0, 'rep': 31.8},
	'NC': {'dem': 56.0, 'rep': 43.9},
	'OH': {'dem': 55.1, 'rep': 44.8},
	'PA': {'dem': 74.8, 'rep': 25.2},
	'VA': {'dem': 81.7, 'rep': 18.2},
	'WI': {'dem': 70.8, 'rep': 29.1},
}

for state in states:
	# add the FTE chances to each state object
	state.fteDemChance = fteChances[state.abbr]['dem']
	state.fteRepChance = fteChances[state.abbr]['rep']

############  Get PredictIt data  ############

tries = 5	# Times to retry each request if it fails.
urlBase = "https://www.predictit.org/api/marketdata/ticker/"	# all urlBase belongs to us
suffix = "USPREZ16"

def getContentDict(url, tries=5, delay=1):
	# gets data from the API and starts parsing it
	for i in range(tries):
		r = requests.get(url)
		if r.status_code == 200 and r.content != b'null':	# PI gives a 200 for nonexistent markets, just with null contents.
			return(r.json()['Contracts'])	# Extracts the good bits: a list of the (two) contracts.
		sleep(delay)	# wait before retrying
	raise	# if all tries fail

for state in states:
	print("Get prices for " + state.abbr + "... ", end="", flush=True)	# Let the user know we're trying
	
	url = urlBase + state.abbr + "." + suffix	# e.g. "https://www.predictit.org/api/marketdata/ticker/AZ.USPREZ16"
	
	try:
		contracts = getContentDict(url, 5)
	except:
		print("fail!")
	else:
		print("good!")
		for contract in contracts:	# contracts should be a list of the two contracts for the state
			if contract['Name'] == "Democratic":
				state.piDemPrice = contract['BestBuyYesCost']	# put the Y cost in the state object
				state.piDemChance = state.piDemPrice * 100	# prices are /1, chances /100
			elif contract['Name'] == "Republican":
				state.piRepPrice = contract['BestBuyYesCost']	# put the Y cost in the state object
				state.piRepChance = state.piRepPrice * 100	# prices are /1, chances /100
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

for state in states:
	fteDemPercent = format(state.fteDemChance, '0.0f') + "%"	# formatted for printing with percent sign
	piDemPercent  = format(state.piDemChance , '0.0f') + "\u00A2"	# formatted for printing with cent sign
	demDiff = addSign(state.piDemChance - state.fteDemChance)	# difference, formatted for printing with +/- sign
	
	fteRepPercent = format(state.fteRepChance, '0.0f') + "%"
	piRepPercent  = format(state.piRepChance , '0.0f') + "\u00A2"
	repDiff = addSign(state.piRepChance - state.fteRepChance)
	
	print(
		state.abbr.rjust(   colWidths[0]),
		"|",
		fteDemPercent.rjust(colWidths[1]),
		piDemPercent.rjust( colWidths[2]),
		demDiff.rjust(      colWidths[3]),
		"|",
		fteRepPercent.rjust(colWidths[1]),
		piRepPercent.rjust( colWidths[2]),
		repDiff.rjust(      colWidths[3]),
	)	# the goods!
# Happy trading!
