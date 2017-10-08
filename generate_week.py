from __future__ import print_function
import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

import datetime

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

not_acceptable_calendar_summaries = ['tiffany.qi@mixpanel.com', 'andrew.huang.010@gmail.com', 'Goals']


def main():
    """Shows basic usage of the Google Calendar API.

    Creates a Google Calendar API service object and outputs a list of the next
    10 events on the user's calendar.
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)
    now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time

    # get all the calendars
    calendar_list = service.calendarList().list(pageToken=None).execute()
    for calendar_list_entry in calendar_list['items']:
        calendar_id = calendar_list_entry['id']
        calendar = calendar_list_entry['summary']

        if calendar not in not_acceptable_calendar_summaries:
            # get all the events in each calendar
            eventsResult = service.events().list(
                calendarId=calendar_id, timeMin=now, maxResults=10, singleEvents=True,
                orderBy='startTime').execute()
            events = eventsResult.get('items', [])
            print('===' + calendar + '===')

            if not events:
                print('No upcoming events found.')
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                try:
                    print(start, event['summary'])
                except KeyError:
                    print(start, 'No description')


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
