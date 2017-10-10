from __future__ import print_function
import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

import csv
import datetime
import json
import pytz

from keys import not_acceptable_calendar_summaries, keywords

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/calendar-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Google Calendar API Python Quickstart'


# calendar rules
CALENDARS = {}
KEYWORDS = {}

output = {
    'Time': {
        'Start': '',
        'End': ''
    },
    'Calendars': CALENDARS,
    'Keywords': KEYWORDS
}


def main():
    """Output the number of hours spent in given categories in calendars.txt
    and output it to a CSV for easy copy and pasting
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)

    # time
    today = datetime.date.today()
    idx = (today.weekday() + 1) % 7
    sunday = datetime.datetime.combine(today - datetime.timedelta(7+idx), datetime.time.min).replace(tzinfo=pytz.timezone('US/Pacific')).isoformat()
    saturday = datetime.datetime.combine(today - datetime.timedelta(7+idx-6), datetime.time(22, 59)).replace(tzinfo=pytz.timezone('US/Pacific')).isoformat()

    output['Time']['Start'] = sunday
    output['Time']['End'] = saturday

    # get all the calendars
    calendar_list = service.calendarList().list(pageToken=None).execute()
    for calendar_list_entry in calendar_list['items']:
        calendar_id = calendar_list_entry['id']
        calendar = calendar_list_entry['summary']

        if calendar not in not_acceptable_calendar_summaries:
            # get all the events in each calendar
            eventsResult = service.events().list(
                calendarId=calendar_id, timeMin=sunday, timeMax=saturday, singleEvents=True,
                orderBy='startTime').execute()
            events = eventsResult.get('items', [])

            # calculate calendar
            CALENDARS[calendar] = calculate_calendar(events)

            # calculate keywords
            for cal, keys in keywords.iteritems():
                if cal == calendar:
                    for category, keyword_array in keys.iteritems():
                        KEYWORDS[category] = calculate_keyword(events, keyword_array)

    with open('output.json', 'w') as fp:
        json.dump(output, fp)


def calculate_calendar(events):
    """Calculate hours by calendar
    """
    total = datetime.timedelta(minutes=0)
    for event in events:
        total += get_duration_of_event(event)

    return total.total_seconds() / 60 / 60


def calculate_keyword(events, keyword_array):
    """Calculate hours by keywords
    """
    total = datetime.timedelta(minutes=0)
    for keyword in keyword_array:
        for event in events:
            try:
                if keyword in event['summary']:
                    total += get_duration_of_event(event)
            except KeyError:
                continue

    return total.total_seconds() / 60 / 60


def get_duration_of_event(event):
    """Get the duration of an event
    """
    start = event['start'].get('dateTime', event['start'].get('date'))[:-6]
    end = event['end'].get('dateTime', event['end'].get('date'))[:-6]
    start_datetime = datetime.datetime.strptime(start, '%Y-%m-%dT%H:%M:%S')
    end_datetime = datetime.datetime.strptime(end, '%Y-%m-%dT%H:%M:%S')

    time_different = (end_datetime - start_datetime)
    return time_different


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'calendar-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:  # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

if __name__ == '__main__':
    main()
