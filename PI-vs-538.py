"""
Compare FiveThirtyEight's odds for each state with PredictIt prices for each.

PI prices are grabbed from their API.
FTE odds are from their "polls-only" forecast, grabbed from their API.

Jack Enneking
2016-10-31
"""

import sys
import getopt
import time
import requests


############  Parse options  ############

def usage():
    print('usage: PI-vs-538.py [-a|d] [-b] [-v] [AK AL ...]')

def deDupe(dupes):
    """Removes duplicates from a list."""
    clean = []
    [clean.append(i) for i in dupes if i not in clean]
    return(clean)

try:
    opts, args = getopt.getopt(sys.argv[1:], 'abhdv', ['alphabetical', 'best', 'help', 'difference', 'verbose'])
except getopt.GetoptError:
    usage()
    sys.exit(2)

sort = 'diff'
best = False
verbose = False
args = [a.upper() for a in args]
args = deDupe(args)

for opt, arg in opts:
    if opt in ('-h', '--help'):
        usage()
        sys.exit()
    elif opt in ('-a', '--alphabetical'):
        sort = 'alpha'
    elif opt in ('-d', '--difference'):
        sort = 'diff'
    elif opt in ('-b', '--best'):
        best = True
    elif opt in ('-v', '--verbose'):
        verbose = True


############  State objects  ############
# Create the main data structure: a list of objects, each representing a state.

class State:
    """Represent a state and its election probabilities."""
    def __init__(self, abbr, name=''):
        self.abbr = abbr
        self.name = name
        self.chances = {}
        self.difs = {}
    
    def calcDifs(self):
        """Calculate the differences between predictions for this state."""
        self.difs = {}
        self.difs['dem'] = self.chances['pi']['dem'] - self.chances['fte']['dem']
        self.difs['rep'] = self.chances['pi']['rep'] - self.chances['fte']['rep']
        self.difs['max'] = abs(max(self.difs.values(), key=lambda d: abs(d)))

stateNames = {
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
# Take user's states if given:
if len(args):
    for abbr in args:
        try:
            name = stateNames[abbr]
        except Exception:
            print('Invalid state: ' + abbr)
            continue
        states.append(State(abbr, name))
else:
    for abbr in stateNames:
        name = stateNames[abbr]
        states.append(State(abbr, name))

if verbose:
    # For alphabetical printing while scraping
    states.sort(key=lambda state: state.abbr)

############  Site objects  ############
# Create a structure representing all the sites we want to scrape from.

class Site:
    """Represent a site and how to scrape it."""
    def __init__(self, abbr='', urlBase='', urlSuffix='', headers={}):
        self.abbr = abbr
        self.urlBase = urlBase
        self.urlSuffix = urlSuffix
        self.headers = headers

    ############  API requests  ############

    def scrape(self, state, tries=5, delay=0.1):
        """Get data from an API and return it as a dict."""

        # Construct request URL, e.g.
        # "https://projects.fivethirtyeight.com/2016-election-forecast/AZ.json"
        # "https://www.predictit.org/api/marketdata/ticker/AZ.USPREZ16"
        url = self.urlBase + state.abbr + self.urlSuffix

        for i in range(tries):
            # dots count tries for user:
            print('.', end='', flush=True)
            try:
                r = requests.get(url, headers=self.headers)
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
    
    ############  Data processing  ############
    
    def drill(self, response):
        """Extract D and R chances from response dict. from either site."""
        if self.abbr == 'FTE':
            return(self.fteDrill(response))
        elif self.abbr == 'PI':
            return(self.piDrill(response))
        else:
            raise Exception(self)
    
    def fteDrill(self, response):
        """Extract D and R chances from FTE response dict."""
        chances = {}
        chances['dem'] = response['forecasts']['latest']['D']['models']['polls']['winprob']
        chances['rep'] = response['forecasts']['latest']['R']['models']['polls']['winprob']
        return(chances)
    
    def piDrill(self, response):
        """Extract D and R chances from PI response dict."""
        chances = {}
        contracts = response['Contracts']
        for contract in contracts:
        # contracts is a list of the two contracts for the state
            if contract['Name'] == 'Democratic':
                chances['dem'] = contract['BestBuyYesCost'] * 100   # prices are /1, chances /100
            elif contract['Name'] == 'Republican':
                chances['rep'] = contract['BestBuyYesCost'] * 100   # prices are /1, chances /100
            else:
                # not Democratic or Republican
                if verbose:
                    print('mostly ', end='')
        return(chances)


# Create sites:
sites = []

sites.append(Site(
    abbr = 'FTE',
    urlBase = 'https://projects.fivethirtyeight.com/2016-election-forecast/',
    urlSuffix = '.json',
    headers = {},
))

sites.append(Site(
    abbr = 'PI',
    urlBase = 'https://www.predictit.org/api/marketdata/ticker/',
    urlSuffix = '.USPREZ16',    # markets are e.g. AZ.USPREZ16, CO.USPREZ16
    headers = {'Accept': 'application/json'},
))


############  Get data  ############

if verbose:
    print()

for state in states:
    if verbose:
        # Let the user know we're trying:
        print(' ' + state.abbr + ':', end='', flush=True)
    state.badData = False
    
    for site in sites:
        if verbose:
            print('  ' + site.abbr + '..', end='', flush=True)
        try:
            response = site.scrape(state)
            state.chances[site.abbr.lower()] = site.drill(response)
        except Exception:
            state.badData = True
            if verbose:
                print('fail!', end='')
        else:
            if verbose:
                print('good!', end='')
    
    if state.badData is True:
        # If we don't have sufficient data, set fake value:
        state.difs['max'] = -1
    else:
        try:
            state.calcDifs()
        except Exception:
            raise
    
    if verbose:
        # Finish the line for the state:
        print()

if not verbose:
    # Still need a blank line before table
    print()

# Order states by difference, i.e. investment opportunity:
states.sort(key=lambda state: state.difs['max'], reverse=True)
if best:
    states = states[:10]

if sort == 'alpha':
    # Order states alphabetically (by abbreviation):
    states.sort(key=lambda state: state.abbr)
#elif sort == 'diff':
#    # Order states by difference, i.e. investment opportunity:
#    states.sort(key=lambda state: state.difs['max'], reverse=True)
#else:
#    # Default to diff
#    states.sort(key=lambda state: state.difs['max'], reverse=True)


############  Print  ############

# Adjust table spacing here:
colWidth = [4,4,4,3]

def addSign(n):
    """Format diffs for printing."""
    if round(n) == 0:
        s = '0'
    elif round(n) > 0:
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

print()
print(header1)
print(header2)
print(headerBar)

        
# List for abbr.s of states that don't have all four values:
badStates=[]
for state in states:
    try:
        assert state.badData == False
        state.chances['fte']['dem']
        state.chances['fte']['rep']
        state.chances['pi']['dem']
        state.chances['pi']['rep']
    except (AssertionError, AttributeError):
        badStates.append(state.abbr)
    else:
        fteDemPercent = format(state.chances['fte']['dem'], '0.0f') + '%'
        piDemPercent  = format(state.chances['pi']['dem'] , '0.0f') + '\u00A2'    # cent sign
        demDiff = addSign(state.difs['dem'])
        
        fteRepPercent = format(state.chances['fte']['rep'], '0.0f') + '%'
        piRepPercent  = format(state.chances['pi']['rep'] , '0.0f') + '\u00A2'
        repDiff = addSign(state.difs['rep'])
        
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

if len(badStates):
    # At least one state messed up
    print('\nInsufficient data:', ', '.join(badStates))

print()

# Happy trading!
