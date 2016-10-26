"""
Compare FiveThirtyEight's odds for each state with PredictIt prices for each.

PI prices are grabbed from their API.
FTE odds are from their "polls-only" forecast, grabbed from their API.

Jack Enneking
2016-10-20
"""

import sys
import os
import time
import requests


############  State objects  ############
# Create the main data structure: a list of objects, each representing a state.

class State:
    """Represent a state and its election probabilities."""
    def __init__(self, abbr, name=''):
        self.abbr = abbr
        self.name = name
        self.chances = {}

stateNames = {
    'AA': 'Alaska',
    'AK': 'Alaska',
    'AL': 'Alabama',
    'AR': 'Arkansas',
    'AZ': 'Arizona',
    'CA': 'California',
    'CO': 'Colorado',
    'CT': 'Connecticut',
    'DC': 'District of Columbia',
    'DE': 'Delaware',
    'FL': 'Florida',
    'GA': 'Georgia',
    'HI': 'Hawaii',
    'IA': 'Iowa',
    'ID': 'Idaho',
    'IL': 'Illinois',
    'IN': 'Indiana',
    'KS': 'Kansas',
    'KY': 'Kentucky',
    'LA': 'Louisiana',
    'MA': 'Massachusetts',
    'MD': 'Maryland',
    'ME': 'Maine',
    'MI': 'Michigan',
    'MN': 'Minnesota',
    'MO': 'Missouri',
    'MS': 'Mississippi',
    'MT': 'Montana',
    'NC': 'North Carolina',
    'ND': 'North Dakota',
    'NE': 'Nebraska',
    'NH': 'New Hampshire',
    'NJ': 'New Jersey',
    'NM': 'New Mexico',
    'NV': 'Nevada',
    'NY': 'New York',
    'OH': 'Ohio',
    'OK': 'Oklahoma',
    'OR': 'Oregon',
    'PA': 'Pennsylvania',
    'RI': 'Rhode Island',
    'SC': 'South Carolina',
    'SD': 'South Dakota',
    'TN': 'Tennessee',
    'TX': 'Texas',
    'UT': 'Utah',
    'VA': 'Virginia',
    'VT': 'Vermont',
    'WA': 'Washington',
    'WI': 'Wisconsin',
    'WV': 'West Virginia',
    'WY': 'Wyoming',
}

# The main data structure, a list of state objects:
states = []
# Sort them into the list because they'll be printed in this order:
for abbr in sorted(stateNames):
    name = stateNames[abbr]
    states.append(State(abbr, name))


############  Site objects  ############

class Site:
    """Represent a site and how to scrape it."""
    def __init__(self, abbr='', urlBase='', urlSuffix='', headers={}):
        self.abbr = abbr
        self.urlBase = urlBase
        self.urlSuffix = urlSuffix
        self.headers = headers
    
sites = []
sites.append(Site(abbr = 'FTE',
                  urlBase = 'https://projects.fivethirtyeight.com/2016-election-forecast/',
                  urlSuffix = '.json',
                  headers = {},
                  #keys = ['forecasts', 'latest'],
                  ))

sites.append(Site(abbr = 'PI',
                  urlBase = 'https://www.predictit.org/api/marketdata/ticker/',
                  urlSuffix = '.USPREZ16',    # markets are e.g. AZ.USPREZ16, CO.USPREZ16
                  headers = {'Accept': 'application/json'},
                  #keys = ['Contracts'],
                  ))


############  API requests  ############

def scrape(site, state, tries=5, delay=0.1):
    """Get data from an API and return it as a dict."""

    # Construct request URL, e.g.
    # "https://projects.fivethirtyeight.com/2016-election-forecast/AZ.json"
    # "https://www.predictit.org/api/marketdata/ticker/AZ.USPREZ16"
    url = site.urlBase + state.abbr + site.urlSuffix

    for i in range(tries):
        # dots count tries for user:
        print('.', end='', flush=True)
        try:
            r = requests.get(url, headers=site.headers)
        except Exception as error:
            if i >= tries - 1:   # if it's the last try
                raise
            else:
                pass
        except KeyboardInterrupt:
            print(' cancelled.')
            sys.exit(1)
        else:
            # Check for bad results
            # FTE gives a 404 for nonexistent states.
            # PI gives a 200 for nonexistent markets, but with null contents.
            if r.status_code == 200 and r.content != b'null':
                # Return the contents as a dict:
                return(r.json())
        time.sleep(delay)
    raise Exception(r.status_code)

def drill(response, site):
    if site.abbr == 'FTE':
        return(fteDrill(response))
    elif site.abbr == 'PI':
        return(piDrill(response))
    else:
        raise Exception(site)

def fteDrill(response):
    """Extract D and R chances from FTE response dict."""
    chances = {}
    chances['dem'] = response['forecasts']['latest']['D']['models']['polls']['winprob']
    chances['rep'] = response['forecasts']['latest']['R']['models']['polls']['winprob']
    return(chances)

def piDrill(response):
    """Extract D and R chances from PI response dict."""
    chances = {}
    contracts = response['Contracts']
    for contract in contracts:
    # contracts is a list of the two contracts for the state
        #print(contract)
        if contract['Name'] == 'Democratic':
            chances['dem'] = contract['BestBuyYesCost'] * 100   # prices are /1, chances /100
        elif contract['Name'] == 'Republican':
            chances['rep'] = contract['BestBuyYesCost'] * 100   # prices are /1, chances /100
        else:
            # not Democratic or Republican
            print('  Something fishy, though.', end='')
    return(chances)


############  Get data  ############

for state in states:
    # Let the user know we're trying:
    print(' ' + state.abbr + ':', end='', flush=True)

    for site in sites:
        print('  ' + site.abbr + '..', end='', flush=True)
        try:
            response = scrape(site, state)
            state.chances[site.abbr.lower()] = drill(response, site)
        except Exception:
            print('fail!', end='')
        else:
            print('good!', end='')
    print()


#############  Get FiveThirtyEight data  ############
#
#print('Get FTE odds:')
#for state in states:
#    # Let the user know we're trying:
#    print('  ' + state.abbr + '..', end='', flush=True)
#    
#    # Construct request URL, e.g.
#    # "https://projects.fivethirtyeight.com/2016-election-forecast/AZ.json"
#    url = urlBase + state.abbr + suffix
#    
#    try:
#        forecast = scrape(url, headers, tries)['forecasts']['latest']
#    except Exception:
#        print(' fail!')
#    else:
#        print(' good!')
#        state.fteDemChance = forecast['D']['models']['polls']['winprob']
#        state.fteRepChance = forecast['R']['models']['polls']['winprob']
#
#
#############  Get PredictIt data  ############
#
#print('Get PI prices:')
#for state in states:
#    # Let the user know we're trying:
#    print('  ' + state.abbr + '..', end='', flush=True)
#    
#    # Construct request URL, e.g.
#    # "https://www.predictit.org/api/marketdata/ticker/AZ.USPREZ16"
#    url = urlBase + state.abbr + '.' + suffix
#    
#    try:
#        contracts = scrape(url, headers, tries)['Contracts']
#    except Exception:
#        print(' fail!')
#    else:
#        print(' good!')
#        for contract in contracts:
#        # contracts is a list of the two contracts for the state
#            if contract['Name'] == 'Democratic':
#                state.piDemPrice = contract['BestBuyYesCost']
#                state.piDemChance = state.piDemPrice * 100
#                # prices are /1, chances /100
#            elif contract['Name'] == 'Republican':
#                state.piRepPrice = contract['BestBuyYesCost']
#                state.piRepChance = state.piRepPrice * 100
#                # prices are /1, chances /100
#            else:
#                # not Democratic or Republican
#                print('Something fishy, though.')


############  Printing  ############

# Adjust table spacing here:
colWidth = [4,4,4,3]

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
        #state.fteDemChance, state.fteRepChance, state.piDemChance, state.piRepChance
        state.chances['fte']['dem']
        state.chances['fte']['rep']
        state.chances['pi']['dem']
        state.chances['pi']['rep']
    except AttributeError:
        badData.append(state.abbr)
    else:
        fteDemPercent = format(state.chances['fte']['dem'], '0.0f') + '%'
        piDemPercent  = format(state.chances['pi']['dem'] , '0.0f') + '\u00A2'    # cent sign
        demDiff = addSign(state.chances['pi']['dem'] - state.chances['fte']['dem'])
        
        fteRepPercent = format(state.chances['fte']['rep'], '0.0f') + '%'
        piRepPercent  = format(state.chances['pi']['rep'] , '0.0f') + '\u00A2'
        repDiff = addSign(state.chances['pi']['rep'] - state.chances['fte']['rep'])
        
        # The goods!
        print(
            state.abbr.rjust(colWidth[0]),
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
    # At least one state messed up
    print('\nInsufficient data:', ', '.join(badData))
print()

# Happy trading!
