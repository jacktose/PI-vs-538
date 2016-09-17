"""
Compare FiveThirtyEight's odds for their "states to watch" with PredictIt
prices for each.

PI prices are grabbed from their API.
538 doesn't seem to have an API, but it would be nice to find a way to scrape
their data.
In the meantime, 538 odds for a democratic or republican win in each state are
manually entered in a CSV.
The CSV format is:
    state,dem,rep
    AZ,33.2,66.8
    CO,76.3,23.5
    ...

Jack Enneking
2016-09-08
"""

import sys
import os
import time
#import csv
import requests


############  State objects  ############
# Create the main data structure: a list of objects, each representing a state.

class State:
    """Represent a state and its election probabilities."""
    def __init__(self, abbr, name=''):
        self.abbr = abbr
        self.name = name

stateNames = {
    'AZ': 'Arizona',
    'CO': 'Colorado',
    #'FL': 'Florida',
    #'GA': 'Georgia',
    #'IA': 'Iowa',
    #'MI': 'Mississippi',
    #'MN': 'Minnesota',
    #'NC': 'North Carolina',
    #'NH': 'New Hampshire',
    #'NV': 'Nevada',
    #'OH': 'Ohio',
    #'PA': 'Pennsylvania',
    #'VA': 'Virginia',
    #'WI': 'Wisconsin',
    'WX': 'Wxsconsin',
}

# The main data structure, a list of state objects:
states = []
# Sort them into the list because they'll be printed in this order:
for abbr in sorted(stateNames):
    name = stateNames[abbr]
    states.append(State(abbr, name))


############  Get JSON from API as dict  ############

def scrape(url, headers={}, tries=5, delay=1):
    """Get data from an API and return it as a dict."""
    for i in range(tries):
        # dots count tries:
        print('.', end='', flush=True)
        try:
            r = requests.get(url, headers=headers)
        except Exception as error:
            if i >= tries - 1:   # if it's the last try
                raise
            else:
                pass
        except KeyboardInterrupt:
            print(' cancelled.')
            sys.exit(1)
        else:
            # PI gives a 200 for nonexistent markets, just with null contents.:
            if r.status_code == 200 and r.content != b'null':
                ## Extract the good bits: a list of the (two) contracts.:
                #return(r.json()['Contracts'])
                return(r.json())
        time.sleep(delay)
    #print(r.status_code)
    raise Exception(r.status_code)


############  Get FiveThirtyEight data  ############

# times to retry each request if it fails:
#tries = 5
tries = 1   # testing
urlBase = 'https://projects.fivethirtyeight.com/2016-election-forecast/'    # all urlBase are belong to us
suffix = '.json'
headers = {}

def getForecasts(r):
    return(r['forecasts']['latest'])

print('Get FTE chances:')
for state in states:
    # Let the user know we're trying:
    print('  ' + state.abbr + '..', end='', flush=True)

    # Construct request URL e.g. "https://projects.fivethirtyeight.com/2016-election-forecast/AZ.json":
    url = urlBase + state.abbr + suffix
    try:
        forecasts = getForecasts(scrape(url, headers, tries))
    except Exception:
        print(' fail!')
    else:
        print(' good!')
        state.fteDemChance = forecasts['D']['models']['polls']['winprob']
        state.fteRepChance = forecasts['R']['models']['polls']['winprob']


############  Get PredictIt data  ############

# times to retry each request if it fails:
#tries = 5
tries = 1   # testing
urlBase = 'https://www.predictit.org/api/marketdata/ticker/'    # all urlBase are belong to us
suffix = 'USPREZ16'    # markets are e.g. AZ.USPREZ16, CO.USPREZ16
headers = {'Accept': 'application/json'}

def getContracts(r):
    return(r['Contracts'])

print('Get PI prices:')
for state in states:
    # Let the user know we're trying:
    print('  ' + state.abbr + '..', end='', flush=True)
    
    # Construct request URL e.g. "https://www.predictit.org/api/marketdata/ticker/AZ.USPREZ16":
    url = urlBase + state.abbr + '.' + suffix
    try:
        contracts = getContracts(scrape(url, headers, tries))
    except Exception:
        print(' fail!')
    else:
        print(' good!')
        for contract in contracts:    # contracts is a list of the two contracts for the state
            if contract['Name'] == 'Democratic':
                state.piDemPrice = contract['BestBuyYesCost']
                state.piDemChance = state.piDemPrice * 100    # prices are /1, chances /100
            elif contract['Name'] == 'Republican':
                state.piRepPrice = contract['BestBuyYesCost']
                state.piRepChance = state.piRepPrice * 100    # prices are /1, chances /100
            else:
                print('Something fishy, though.')    # not Democratic or Republican


############  Printing  ############

# Adjust table spacing here:
colWidth = [4,3,4,3]

def addSign(n):
    """Format diffs for printing"""
    if int(n) > 0:
        s = '+' + format(n, '0.0f')
    else:
        s = format(n, '0.0f')
    return s

header1 = ' '.join((
    '│'.rjust(6),
    'Democrat'.center(sum(colWidth[1:]) + 2),
    '│',
    'Republican'.center(sum(colWidth[1:]) + 2),
))

header2 = ' '.join((
    'State│'.rjust(6),
    '538'.rjust(colWidth[1]),
    'PI'.center(colWidth[2]),
    'dif'.rjust(colWidth[3]),
    '│',
    '538'.rjust(colWidth[1]),
    'PI'.center(colWidth[2]),
    'dif'.rjust(colWidth[3]),
))

headerBar = '┼'.join((
    '─' * (colWidth[0] + 1),
    '─' * (sum(colWidth[1:]) + 4),
    '─' * (sum(colWidth[1:]) + 4),
))

print('')
print(header1)
print(header2)
print(headerBar)

# List for abbr.s of states that don't have all four values:
badData=[]
for state in states:
    try:
        state.fteDemChance, state.fteRepChance, state.piDemPrice, state.piRepPrice
    except AttributeError:
        badData.append(state.abbr)
    else:
        fteDemPercent = format(state.fteDemChance, '0.0f') + '%'
        piDemPercent  = format(state.piDemChance , '0.0f') + '\u00A2'    # cent sign
        demDiff = addSign(state.piDemChance - state.fteDemChance)
        
        fteRepPercent = format(state.fteRepChance, '0.0f') + '%'
        piRepPercent  = format(state.piRepChance , '0.0f') + '\u00A2'
        repDiff = addSign(state.piRepChance - state.fteRepChance)
        
        # The goods!
        print(
            state.abbr.rjust(   colWidth[0]),
            '│',
            fteDemPercent.rjust(colWidth[1]),
            piDemPercent.rjust(colWidth[2]),
            demDiff.rjust(colWidth[3]),
            '│',
            fteRepPercent.rjust(colWidth[1]),
            piRepPercent.rjust(colWidth[2]),
            repDiff.rjust(colWidth[3]),
        )

if len(badData):
    print('\nInsufficient data:', ', '.join(badData))
print()

# Happy trading!
